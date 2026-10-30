"""Auto-fill job applications in Microsoft Edge, then stop before Submit so you review and send them.

    python "JOB Agent/apply_bot.py" 8 3              fill the applications for jobs #8 and #3
    python "JOB Agent/apply_bot.py" 8 --test         headless dry run: fill, report, close (no login)

Uses its own Edge profile (data/edge-profile), so logins are remembered and your normal browsing
is untouched.
    Workday     signs in, or creates an account (WORKDAY_PASSWORD in .env), uploads your resume,
                then fills page after page until the Review page
    Greenhouse  fills the one-page form and attaches resume + cover letter
    other sites just opens the page for you
Each form field is matched to your details (applicant.json + resume) by Mistral; anything it can't
answer from them is left blank for you. It NEVER clicks Submit. When it sees the "application
submitted" page after you submit, it marks the job as applied.
"""

import difflib
import json
import os
import re
import sys
import time

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mistralai import ChatMistralAI
from playwright.sync_api import sync_playwright
from pydantic import BaseModel

import agent          # also loads .env
import config
import matching
import store
import telegram_bot

NEXT_BUTTONS = ['[data-automation-id="pageFooterNextButton"]', '[data-automation-id="bottom-navigation-next-button"]']
SUBMITTED = re.compile(r"application (was |has been )?(successfully )?submitted|thank you for (applying|your application)"
                       r"|we('ve| have) received your application", re.I)

# Runs in the page: tags every fillable field with data-ja="<id>" and describes it.
COLLECT_FIELDS_JS = r"""
() => {
  const clean = s => (s || '').replace(/\s+/g, ' ').trim();
  const visible = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const labelOf = el => {
    const parts = [], add = s => { s = clean(s); if (s && !parts.includes(s)) parts.push(s); };
    add(el.getAttribute('aria-label'));
    (el.getAttribute('aria-labelledby') || '').split(/\s+/).forEach(id => {
      const n = id && document.getElementById(id); if (n) add(n.innerText); });
    if (el.id) { const l = document.querySelector('label[for="' + CSS.escape(el.id) + '"]'); if (l) add(l.innerText); }
    const wrap = el.closest('label'); if (wrap) add(wrap.innerText);
    const fs = el.closest('fieldset'); if (fs) { const lg = fs.querySelector('legend'); if (lg) add(lg.innerText); }
    if (!parts.length) { let p = el.parentElement;
      for (let k = 0; k < 4 && p; k++, p = p.parentElement) { const t = clean(p.innerText); if (t) { add(t.slice(0, 200)); break; } } }
    add(el.getAttribute('placeholder'));
    return parts.join(' | ').slice(0, 300);
  };
  const radioText = r => { const l = r.id && document.querySelector('label[for="' + CSS.escape(r.id) + '"]');
    return clean(l ? l.innerText : (r.closest('label') || r.parentElement).innerText) || r.value; };
  const fields = [], groups = {};
  let n = 0;
  document.querySelectorAll('input, textarea, select, button[aria-haspopup="listbox"]').forEach(el => {
    const tag = el.tagName.toLowerCase();
    const type = tag === 'input' ? (el.type || 'text').toLowerCase() : tag === 'button' ? 'listbox' : tag;
    if (['hidden', 'submit', 'button', 'file', 'password', 'checkbox', 'image', 'reset', 'search'].includes(type)) return;
    if (el.disabled || el.readOnly) return;
    if (type === 'radio') {
      const box = el.closest('fieldset, [role="radiogroup"]');
      const key = el.name || (box && box.innerText) || labelOf(el);
      if (!groups[key]) {
        const id = n++;
        el.setAttribute('data-ja', id);
        if (box) box.setAttribute('data-ja-group', id);
        const label = box ? clean((box.querySelector('legend, label') || box).innerText).slice(0, 300) : labelOf(el);
        groups[key] = {id, kind: 'radio', name: el.name || '', label, options: [], value: '', required: el.required};
        fields.push(groups[key]);
      }
      groups[key].options.push(radioText(el));
      if (el.checked) groups[key].value = radioText(el);
      return;
    }
    if (!visible(el)) return;
    const id = n++;
    el.setAttribute('data-ja', id);
    const combo = el.getAttribute('role') === 'combobox' || el.hasAttribute('aria-autocomplete');
    const f = {id, kind: tag === 'select' ? 'select' : type === 'listbox' ? 'listbox' : combo ? 'combobox' : 'text',
               label: labelOf(el), value: '', options: [],
               required: el.required || el.getAttribute('aria-required') === 'true'};
    if (tag === 'select') {
      f.options = [...el.options].map(o => clean(o.text)).filter(Boolean);
      f.value = el.selectedIndex > 0 ? clean(el.options[el.selectedIndex].text) : '';
    } else if (type === 'listbox') {
      const t = clean(el.innerText); f.value = /select one|^select$/i.test(t) ? '' : t;
    } else f.value = el.value || '';
    fields.push(f);
  });
  return fields;
}
"""

CLICK_RADIO_JS = r"""
([id, name, value]) => {
  const box = document.querySelector('[data-ja-group="' + id + '"]');
  const radios = name ? [...document.querySelectorAll('input[type="radio"][name="' + CSS.escape(name) + '"]')]
                      : box ? [...box.querySelectorAll('input[type="radio"]')] : [];
  const text = r => { const l = r.id && document.querySelector('label[for="' + CSS.escape(r.id) + '"]');
    return ((l ? l.innerText : (r.closest('label') || r.parentElement).innerText) || r.value).trim().toLowerCase(); };
  const v = value.trim().toLowerCase();
  const hit = radios.find(r => text(r) === v) || radios.find(r => text(r).startsWith(v)) || radios.find(r => text(r).includes(v));
  if (!hit) return false;
  hit.click();
  return true;
}
"""


class FieldAnswer(BaseModel):
    field_id: int
    value: str


class FieldAnswers(BaseModel):
    answers: list[FieldAnswer]


# ── Matching form fields to your details (Mistral) ───────────────────────────
def candidate_details(row) -> str:
    applicant = json.loads(config.APPLICANT_PATH.read_text(encoding="utf-8"))
    applicant.pop("_help", None)
    resume = matching.resume_profile(matching.resume_text())
    return (f"APPLICANT DETAILS (JSON; empty string = unknown):\n{json.dumps(applicant, indent=1)}\n\n"
            f"SKILLS: {', '.join(resume.skills)}\n\n"
            f"JOB BEING APPLIED FOR: {row['title']} at {row['company']}\n\n"
            f"COVER LETTER:\n{row.get('letter') or ''}")


def answer_fields(fields, details) -> dict[int, str]:
    system = (
        "You fill in a job application form for the candidate. For each form field, decide the value "
        "from the candidate's details.\n"
        "Rules:\n"
        "- Only answer fields you can answer from the details. Leave out any field you can't — never guess, "
        "never invent numbers, dates, IDs or facts. Empty strings in the details mean unknown.\n"
        "- If a field has options, the value must be exactly one of the options.\n"
        "- Leave out demographic / diversity / disability / veteran questions unless the details give a value.\n"
        "- Leave out consent, signature, privacy and 'I certify' fields — the candidate does those.\n"
        "- For free-text questions like 'Why do you want to join us' or 'cover letter', you may use the cover "
        "letter. Keep other text answers short.\n"
        "- Phone numbers without the country code unless the label asks for it. Dates in the format the label shows."
    )
    form = [{k: f[k] for k in ("id", "kind", "label", "options", "required")} for f in fields]
    user = f"{details}\n\nFORM FIELDS (JSON):\n{json.dumps(form, indent=1)}"
    model = ChatMistralAI(model=config.APPLY_MODEL, temperature=0)
    result = matching.call_with_retry(model.with_structured_output(FieldAnswers).invoke,
                                      [SystemMessage(system), HumanMessage(user)])
    valid = {f["id"] for f in fields}
    return {a.field_id: a.value.strip() for a in result.answers if a.field_id in valid and a.value.strip()}


def best_option(options, value):
    low = {o.lower(): o for o in options}
    v = value.lower()
    for test in (lambda o: o == v, lambda o: o.startswith(v), lambda o: v in o, lambda o: o in v):
        hit = next((orig for o, orig in low.items() if o and test(o)), None)
        if hit:
            return hit
    close = difflib.get_close_matches(v, list(low), n=1, cutoff=0.6)
    return low[close[0]] if close else None


# ── Filling one page ─────────────────────────────────────────────────────────
def set_field(page, f, value):
    el = page.locator(f'[data-ja="{f["id"]}"]').first
    if f["kind"] == "text":
        el.fill(value)
    elif f["kind"] == "select":
        option = best_option(f["options"], value)
        if option:
            el.select_option(label=option)
    elif f["kind"] == "radio":
        page.evaluate(CLICK_RADIO_JS, [f["id"], f["name"], value])
    elif f["kind"] == "listbox":                      # Workday dropdown button
        el.click()
        page.wait_for_timeout(700)
        pick_option(page, value)
    elif f["kind"] == "combobox":                     # type-ahead (Workday prompts, react-select)
        el.click()
        el.fill(value)
        page.wait_for_timeout(1200)
        if not pick_option(page, value):
            el.press("Enter")
            page.wait_for_timeout(1200)
            pick_option(page, value)


def pick_option(page, value) -> bool:
    options = page.locator('[role="option"]:visible, [data-automation-id="promptOption"]:visible')
    texts = [t.strip() for t in options.all_inner_texts()]
    choice = best_option([t for t in texts if t], value)
    if choice is None:
        page.keyboard.press("Escape")
        return False
    options.nth(texts.index(choice)).click()
    page.wait_for_timeout(500)
    return True


def fill_page(page, details, log) -> int:
    fields = [f for f in page.evaluate(COLLECT_FIELDS_JS) if not f["value"]]
    if not fields:
        return 0
    answers = answer_fields(fields, details)
    done = 0
    for f in fields:
        if f["id"] in answers:
            try:
                set_field(page, f, answers[f["id"]])
                done += 1
            except Exception as e:
                log(f"    couldn't fill '{f['label'][:50]}': {type(e).__name__}")
    log(f"    filled {done} of {len(fields)} empty fields")
    return done


def upload_files(page, row, log):
    """Attach resume (and cover letter where asked) to any file inputs on the page."""
    letter_file = config.DATA_DIR / "letters" / f"Cover_Letter_{row['company']}_{row['no']}.txt".replace(" ", "_")
    letter_file.parent.mkdir(parents=True, exist_ok=True)
    letter_file.write_text(row.get("letter") or "", encoding="utf-8")
    inputs = page.locator('input[type="file"]')
    for i in range(inputs.count()):
        label = inputs.nth(i).evaluate(
            "el => (el.closest('[class*=field], [data-automation-id], fieldset, div') || el).innerText || ''").lower()
        if "cover" in label:
            if row.get("letter"):
                inputs.nth(i).set_input_files(str(letter_file))
                log("    attached cover letter")
        elif config.RESUME_PATH.name not in page.content():
            inputs.nth(i).set_input_files(str(config.RESUME_PATH))
            log("    uploaded resume")
            page.wait_for_timeout(4000)


# ── Workday ──────────────────────────────────────────────────────────────────
def click(page, selector, timeout=4000) -> bool:
    try:
        page.locator(selector).first.click(timeout=timeout, force=True)
        page.wait_for_timeout(2500)
        return True
    except Exception:
        return False


def visible(page, selector) -> bool:
    try:
        return page.locator(selector).first.is_visible()
    except Exception:
        return False


def workday_login(page, log) -> bool:
    """Sign in, or create an account. False if you need to step in (e.g. verify your email)."""
    email = json.loads(config.APPLICANT_PATH.read_text(encoding="utf-8"))["email"]
    password = os.getenv("WORKDAY_PASSWORD", "")
    if not password:
        log("    WORKDAY_PASSWORD is not set in JOB Agent/.env")
        return False
    if visible(page, '[data-automation-id="signInSubmitButton"]') or click(page, '[data-automation-id="signInLink"]'):
        page.locator('[data-automation-id="email"]').fill(email)
        page.locator('[data-automation-id="password"]').fill(password)
        click(page, '[data-automation-id="signInSubmitButton"]')
        page.wait_for_timeout(3000)
        if not visible(page, '[data-automation-id="signInSubmitButton"]'):
            log("    signed in")
            return True
    log("    no account yet — creating one")
    if click(page, '[data-automation-id="createAccountLink"]') or visible(page, '[data-automation-id="verifyPassword"]'):
        page.locator('[data-automation-id="email"]').fill(email)
        page.locator('[data-automation-id="password"]').fill(password)
        page.locator('[data-automation-id="verifyPassword"]').fill(password)
        if visible(page, '[data-automation-id="createAccountCheckbox"]'):
            page.locator('[data-automation-id="createAccountCheckbox"]').check(force=True)
        click(page, '[data-automation-id="createAccountSubmitButton"]')
        page.wait_for_timeout(4000)
        if not visible(page, '[data-automation-id="createAccountSubmitButton"]'):
            log("    account created")
            return True
    return False


def next_button(page):
    for sel in NEXT_BUTTONS:
        if visible(page, sel):
            return page.locator(sel).first
    return None


def workday(page, row, details, log, test=False) -> str:
    click(page, '[data-automation-id="adventureButton"]')                 # "Apply"
    if not (click(page, '[data-automation-id="autofillWithResume"]')
            or click(page, '[data-automation-id="applyManually"]')):
        click(page, '[data-automation-id="useMyLastApplication"]')
    if test:
        return "reached sign-in" if visible(page, '[data-automation-id="email"]') else f"at: {page.url}"
    if visible(page, '[data-automation-id="email"]') and not workday_login(page, log):
        return "needs you to sign in / verify your email in the Edge window"

    for step in range(15):
        page.wait_for_timeout(2500)
        heading = page.locator("h2").first.inner_text() if page.locator("h2").count() else f"page {step + 1}"
        log(f"  page: {heading}")
        upload_files(page, row, log)
        nxt = next_button(page)
        if nxt is None:
            return f"stopped at '{heading}' — no Next button found"
        if "submit" in nxt.inner_text().lower():
            return "ready for review — check it and click Submit"
        fill_page(page, details, log)
        nxt.click(force=True)
        page.wait_for_timeout(3500)
        new_heading = page.locator("h2").first.inner_text() if page.locator("h2").count() else ""
        if new_heading == heading:
            return f"needs you on '{heading}' — some required fields I couldn't answer"
    return "stopped after 15 pages"


# ── Greenhouse ───────────────────────────────────────────────────────────────
def greenhouse(page, row, details, log) -> str:
    frame = page.locator('iframe[src*="greenhouse"]')
    if frame.count():                                   # company page embedding the Greenhouse form
        page.goto(frame.first.get_attribute("src"))
        page.wait_for_timeout(3000)
    click(page, 'button:has-text("Apply"), a:has-text("Apply for this job")', timeout=2000)
    upload_files(page, row, log)
    fill_page(page, details, log)
    return "ready for review — check it and click Submit"


# ── Running it ───────────────────────────────────────────────────────────────
def fill_application(context, row, log, test=False) -> tuple:
    page = context.new_page()
    page.goto(row["url"], timeout=60000)
    page.wait_for_timeout(4000)
    details = candidate_details(row)
    url = page.url.lower()
    try:
        if "myworkday" in url:
            result = workday(page, row, details, log, test)
        elif "greenhouse" in url or page.locator('iframe[src*="greenhouse"]').count():
            result = greenhouse(page, row, details, log)
        else:
            result = "opened the job page — this site needs you to apply by hand"
    except Exception as e:
        result = f"stopped with an error ({type(e).__name__}) — please finish by hand"
        log(f"  {type(e).__name__}: {e}")
    return page, result


def main(numbers, test=False):
    log = print
    con = store.connect()
    rows = [r for r in (store.job(con, n) for n in numbers) if r]
    with sync_playwright() as p:
        if test:
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context()
        else:
            config.BROWSER_PROFILE.mkdir(parents=True, exist_ok=True)
            context = p.chromium.launch_persistent_context(str(config.BROWSER_PROFILE), channel="msedge",
                                                           headless=False, no_viewport=True,
                                                           args=["--start-maximized"])
        open_pages = {}
        for row in rows:
            log(f"#{row['no']} {row['title']} — {row['company']}")
            page, result = fill_application(context, row, log, test)
            log(f"  → {result}")
            open_pages[row["no"]] = page
            if test:
                page.screenshot(path=str(config.DATA_DIR / f"apply_test_{row['no']}.png"), full_page=True)
            else:
                telegram_bot.send(f"🤖 <b>#{row['no']} · {agent.esc(row['title'])}</b> at {agent.esc(row['company'])}\n"
                                  f"{agent.esc(result)}\n\n<i>The form is open in Edge on your PC.</i>")
        if test:
            context.close()
            return

        # keep the browser open until you close it; spot the "application submitted" page
        while True:
            try:
                for no, page in list(open_pages.items()):
                    if page.is_closed():
                        open_pages.pop(no)
                    elif SUBMITTED.search(page.inner_text("body")):
                        store.update_job(con, no, status="applied")
                        telegram_bot.send(f"🎉 Submitted <b>#{no}</b> — marked as applied. Good luck! 🤞")
                        open_pages.pop(no)
                if not context.pages:
                    break
                time.sleep(5)
            except Exception:
                break


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    main([int(a) for a in args if a.isdigit()], test="--test" in args)
