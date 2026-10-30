"""GCC Job Agent — finds new data-engineering jobs at GCCs in India, scores them against
your resume, and asks you on Telegram which ones to apply for.

    python "JOB Agent/agent.py" run        daily: new GCCs + new jobs → score → Telegram shortlist
    python "JOB Agent/agent.py" replies    act on your Telegram replies (APPLY 12 15 / SKIP 13 / LIST)
    python "JOB Agent/agent.py" listen     keep answering replies instantly until you press Ctrl+C
    python "JOB Agent/agent.py" chat-id    show the chat id to put in TELEGRAM_CHAT_ID

The agent never submits an application itself: for jobs you approve it writes a cover letter
and resume tips, then sends you the apply link.
"""

import html
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

import config
import matching
import sources
import store
import telegram_bot


def load_env():
    """Load the nearest .env file above this script."""
    for folder in Path(__file__).resolve().parents:
        if (folder / ".env").exists():
            load_dotenv(folder / ".env")
            return


load_env()

HELP = ("💬 <b>Reply with</b>\n"
        "<code>APPLY 8 3</code>  →  cover letter + apply link\n"
        "<code>SKIP 5</code>  →  drop a job\n"
        "<code>APPLIED 8</code>  →  mark as applied\n"
        "<code>LIST</code>  →  show your shortlist")
DIVIDER = "━━━━━━━━━━━━━━━"


# ── Daily run ────────────────────────────────────────────────────────────────
def find_new_gccs(con, log) -> list[dict]:
    try:
        articles = sources.gcc_news()
        found = matching.extract_gccs(articles)
    except Exception as e:
        log(f"New-GCC search failed: {type(e).__name__}: {e}")
        return []
    new = []
    for g in found:
        article = articles[g.article_number] if 0 <= g.article_number < len(articles) else {}
        url, announced = article.get("url", ""), announced_date(article.get("published_date", ""))
        if sources.company_ok(g.company) and store.add_gcc(con, g.company, g.city, g.summary, url, announced):
            new.append({"company": g.company, "city": g.city, "summary": g.summary, "url": url,
                        "announced": announced})
    log(f"News: {len(articles)} articles → {len(new)} newly announced GCCs")
    return new


def collect_jobs(con, log) -> int:
    first_run = not store.known_keys(con)
    max_age = config.FIRST_RUN_AGE_DAYS if first_run else config.MAX_AGE_DAYS
    known = store.known_keys(con)
    jobs = sources.collect_feed_jobs(max_age, known, log)

    # GCCs found in the news aren't in the career-feed list, so search the web for their jobs
    for g in store.gccs(con, "searched = 0")[:config.MAX_NEW_GCC_SEARCHES]:
        try:
            web = sources.web_jobs_at(g["company"], known | {j["key"] for j in jobs})
            log(f"Web search: {len(web)} job postings at {g['company']}")
            jobs += web
        except Exception as e:
            log(f"Web search for {g['company']} failed: {type(e).__name__}: {e}")
        con.execute("UPDATE gccs SET searched = 1 WHERE company = ?", (g["company"],))
        con.commit()

    store.add_jobs(con, jobs)
    return len(jobs)


def score_pending(con, resume_txt, resume, log):
    pending = store.jobs(con, "status = 'pending'", order="posted DESC")[:config.MAX_JOBS_TO_SCORE]
    log(f"Scoring {len(pending)} jobs against your resume with {config.MODEL} …")

    def score(row):
        try:
            return row, matching.score_job(resume_txt, resume, row), None
        except Exception as e:
            return row, None, e

    with ThreadPoolExecutor(4) as pool:
        for row, result, err in pool.map(score, pending):
            if err:
                log(f"  ✗ #{row['no']} {row['title']} — {type(err).__name__}: {err}")
                continue
            status = "shortlisted" if result["fit"] >= config.MIN_FIT_TO_NOTIFY else "low_fit"
            store.update_job(con, row["no"], status=status, **result)
            log(f"  {result['fit']:>3}/100  #{row['no']} {row['title']} — {row['company']}")


def run(log=print, notify=True):
    con = store.connect()
    resume_txt = matching.resume_text()
    resume = matching.resume_profile(resume_txt)
    log(f"Resume: {resume.name} · {resume.years_of_experience:g} yrs · {len(resume.skills)} skills")

    new_gccs = find_new_gccs(con, log)
    log(f"Added {collect_jobs(con, log)} new jobs to the database")
    score_pending(con, resume_txt, resume, log)
    if notify:
        notify_shortlist(con, new_gccs, log)


# ── Telegram messages ────────────────────────────────────────────────────────
def job_line(j) -> str:
    """One job as a small Telegram card (HTML)."""
    gap = matching.SkillGap.model_validate_json(j["gap"]) if j.get("gap") else None
    lines = [f"{fit_dot(j['fit'])} <b>#{j['no']} · {esc(j['title'])}</b>",
             f"🏢 <b>{esc(j['company'])}</b>{company_line(j.get('co') or {})}",
             f"📍 {esc(short_place(j['location']))}" + "".join(
                 f"  ·  {icon} {esc(j[k])}" for icon, k in (("🏠", "work_mode"), ("🧑‍💻", "experience"))
                 if j.get(k) and j[k] != "Not stated")]
    if j.get("salary") and j["salary"] != "Unknown":
        lines.append(f"💰 {esc(j['salary'])}  <i>({esc(j['salary_source'])})</i>")
    else:
        lines.append("💰 <i>Salary not disclosed</i>")
    lines.append(f"⭐ Fit <b>{j['fit']}</b>/100  ·  📅 Posted {posted_ago(j['posted'])}")
    if gap and gap.missing_required:
        lines.append(f"⚠️ <i>Missing: {esc(', '.join(gap.missing_required[:3]))}</i>")
    lines.append(f'🔗 <a href="{esc(j["url"])}">View job</a>')
    return "\n".join(lines)


def company_line(co: dict) -> str:
    """'  ·  🇮🇳 in India since 2003 · ~9,000 people' — whatever is known."""
    bits = []
    if co.get("india_since", "Unknown") != "Unknown":
        bits.append(f"in India since {esc(co['india_since'])}")
    if co.get("india_headcount", "Unknown") != "Unknown" and len(co["india_headcount"]) <= 12:
        bits.append(f"{esc(co['india_headcount'])} people")
    return f"\n🇮🇳 <i>{' · '.join(bits)}</i>" if bits else ""


def esc(text) -> str:
    return html.escape(str(text))


def fit_dot(fit) -> str:
    return "🟢" if fit >= 75 else "🟡" if fit >= config.MIN_FIT_TO_NOTIFY else "🔴"


def short_place(location: str) -> str:
    """'Chennai, Tamil Nadu, India' → 'Chennai'; 'Pune Maharashtra India' → 'Pune'."""
    loc = location.lower()
    city = next((c for c in config.INDIA_CITIES if c in loc), None)
    return city.title() if city else re.split(r"[,\-]", location)[0].strip() or location


def posted_ago(posted: str) -> str:
    days = (date.today() - date.fromisoformat(posted)).days
    return "today" if days <= 0 else "yesterday" if days == 1 else f"{days} days ago"


def digest(new_gccs, rows) -> str:
    """The daily message. Blocks are separated by blank lines so long messages split cleanly."""
    blocks = [f"🧭 <b>GCC Job Agent</b>  ·  {date.today():%a, %d %b}\n"
              f"<i>{len(rows)} new match{'es' if len(rows) != 1 else ''} · "
              f"{len(new_gccs)} new GCC{'s' if len(new_gccs) != 1 else ''}</i>"]
    if new_gccs:
        blocks.append(f"{DIVIDER}\n🆕 <b>NEW GCCs IN INDIA</b>")
        blocks += [f"🏢 <b>{esc(g['company'])}</b>  ·  📍 {esc(g['city'])}"
                   + (f"\n📰 Announced {esc(g['announced'])}" if g.get("announced") else "")
                   + f"\n<i>{esc(g['summary'])}</i>"
                   + (f'\n🔗 <a href="{esc(g["url"])}">Read the news</a>' if g.get("url") else "")
                   for g in new_gccs]
    blocks.append(f"{DIVIDER}\n🎯 <b>TOP MATCHES FOR YOU</b>")
    blocks += [job_line(j) for j in rows] or ["No new jobs above your fit cutoff today. 🌱"]
    blocks.append(f"{DIVIDER}\n{HELP}")
    return "\n\n".join(blocks)


def kit_message(row, kit) -> str:
    """Reply to APPLY: job card, apply link, cover letter (collapsible) and next steps."""
    tips = matching.ResumeSuggestions.model_validate_json(kit["tips"])
    warnings = json.loads(kit["warnings"])
    card = job_line(row).rsplit("\n🔗", 1)[0]                 # the card without its "View job" link
    parts = [f"✅ <b>Application kit ready</b>\n\n{card}"]
    if row["fit"] < config.MIN_FIT_TO_NOTIFY:
        parts.append(f"⚠️ <i>Heads-up: this job scored below your {config.MIN_FIT_TO_NOTIFY}/100 cutoff.</i>")
    parts.append(f'👉 <a href="{esc(row["url"])}"><b>Open the application page</b></a>')
    parts.append(f"💌 <b>Cover letter</b>  <i>(tap to expand · long-press to copy)</i>\n"
                 f"<blockquote expandable>{esc(kit['letter'])}</blockquote>")
    if warnings:
        parts.append(f"⚠️ <b>Check these numbers before sending:</b> {esc(', '.join(warnings))}")
    if tips.skills_to_highlight:
        parts.append(f"📝 <b>Put these front and centre</b>\n{esc(', '.join(tips.skills_to_highlight[:6]))}")
    parts.append("🪜 <b>Next steps</b>\n"
                 "1. Open the link and sign in\n"
                 "2. Upload your resume, paste the letter\n"
                 "3. Answer the questions and submit\n"
                 f"4. Reply <code>APPLIED {row['no']}</code> here")
    return "\n\n".join(parts)


def announced_date(published: str) -> str:
    """Tavily news date 'Wed, 28 Oct 2026 10:00:00 GMT' → '28 Oct 2026'."""
    m = re.search(r"\d{1,2} \w{3} \d{4}", published)
    return m.group() if m else ""


def enrich(con, row, log=print) -> dict:
    """Add salary, work mode, experience and the company's India facts to a job (looked up once)."""
    try:
        if row.get("salary") is None:
            facts = matching.job_facts(row, sources.salary_snippets(row["company"], row["title"]))
            store.update_job(con, row["no"], salary=facts.salary_range, salary_source=facts.salary_source,
                             work_mode=facts.work_mode, experience=facts.experience)
        if not store.company(con, row["company"]):
            c = matching.company_facts(row["company"], sources.company_snippets(row["company"]))
            store.save_company(con, row["company"], india_since=c.india_since,
                               india_cities=", ".join(c.india_cities[:4]),
                               india_headcount=c.india_headcount, about=c.about)
    except Exception as e:
        log(f"  couldn't look up details for #{row['no']}: {type(e).__name__}: {e}")
    return {**store.job(con, row["no"]), "co": store.company(con, row["company"]) or {}}


def notify_shortlist(con, new_gccs, log):
    rows = [enrich(con, j, log) for j in store.jobs(con, "status = 'shortlisted' AND notified_on IS NULL")]
    if telegram_bot.send(digest(new_gccs, rows), log):
        for j in rows:
            store.update_job(con, j["no"], notified_on=date.today().isoformat())
        log(f"Telegram: sent {len(rows)} matches and {len(new_gccs)} new GCCs")


# ── Acting on your choices ───────────────────────────────────────────────────
def approve(con, no, resume_txt=None, resume=None) -> dict:
    """Write the cover letter + resume tips for job #no and mark it approved."""
    row = store.job(con, no)
    resume_txt = resume_txt or matching.resume_text()
    resume = resume or matching.resume_profile(resume_txt)
    kit = matching.application_kit(resume_txt, resume, row)
    store.update_job(con, no, status="approved", **kit)
    return {**row, **kit}


def start_auto_fill(numbers):
    """Open Edge and fill the applications in the background (apply_bot.py); you click Submit."""
    log_file = open(config.DATA_DIR / "apply_bot.log", "a", encoding="utf-8")
    subprocess.Popen([sys.executable, str(Path(__file__).with_name("apply_bot.py")), *map(str, numbers)],
                     stdout=log_file, stderr=subprocess.STDOUT,
                     creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)


def parse_command(text):
    m = re.match(r"\s*/?(apply|applied|skip|list|help)\b(.*)", text, re.I | re.S)
    if not m:
        return None, []
    return m.group(1).lower(), [int(n) for n in re.findall(r"\d+", m.group(2))]


def handle_replies(log=print, wait=0):
    con = store.connect()
    if not telegram_bot.configured():
        log("Telegram not configured — add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to JOB Agent/.env")
        return
    for sid, text in telegram_bot.recent_replies(wait):
        if store.message_handled(con, sid):
            continue
        command, numbers = parse_command(text)
        log(f"Reply: {text!r}")
        for message in answer(con, command, numbers):
            telegram_bot.send(message, log)


def answer(con, command, numbers) -> list[str]:
    """The Telegram messages to send back for one reply (each one sent separately)."""
    if command == "list":
        rows = [enrich(con, j) for j in store.jobs(con, "status = 'shortlisted'")]
        if not rows:
            return ["📋 Your shortlist is empty — new matches arrive every morning. 🌅"]
        return ["\n\n".join([f"📋 <b>YOUR SHORTLIST</b>  ·  {len(rows)} jobs"] + [job_line(j) for j in rows]
                            + [f"{DIVIDER}\n{HELP}"])]
    if command not in ("apply", "skip", "applied") or not numbers:
        return [f"👋 <b>Hi! I'm your GCC Job Agent.</b>\n"
                f"Every morning I send new data-engineering jobs at GCCs in India that fit your resume.\n\n{HELP}"]

    out, approved = [], []
    for no in numbers:
        row = store.job(con, no)
        if not row:
            out.append(f"❓ There's no job <b>#{no}</b>. Send <code>LIST</code> to see your shortlist.")
        elif command == "skip":
            store.update_job(con, no, status="skipped")
            out.append(f"🗑 Skipped <b>#{no} · {esc(row['title'])}</b> at {esc(row['company'])}.")
        elif command == "applied":
            store.update_job(con, no, status="applied")
            out.append(f"🎉 <b>Nice!</b> Marked <b>#{no} · {esc(row['title'])}</b> at {esc(row['company'])} "
                       f"as applied. Good luck! 🤞")
        else:
            try:
                kit = approve(con, no)
                out.append(kit_message(enrich(con, row), kit))
                approved.append(no)
            except Exception as e:
                out.append(f"⚠️ Couldn't prepare the kit for <b>#{no}</b> ({type(e).__name__}). Try again in a minute.")
    if approved and config.AUTO_FILL:
        start_auto_fill(approved)
        out.append(f"🤖 <b>Auto-fill started</b> for {', '.join(f'#{n}' for n in approved)}\n"
                   "Edge is opening on your PC and filling the form(s). I'll message you when each one is "
                   "ready for your review. <b>I never click Submit</b> — you do.")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")        # emoji in logs on the Windows console
    action = sys.argv[1] if len(sys.argv) > 1 else "run"
    if action == "run":
        run()
    elif action == "replies":
        handle_replies()
    elif action == "listen":
        print("Listening for Telegram replies — Ctrl+C to stop")
        while True:
            handle_replies(wait=50)
    elif action == "chat-id":
        chats = telegram_bot.find_chat_ids()
        print("\n".join(f"TELEGRAM_CHAT_ID={cid}   ({name})" for cid, name in chats)
              or "No messages yet — send /start to your bot in Telegram, then run this again.")
    else:
        print(__doc__)
