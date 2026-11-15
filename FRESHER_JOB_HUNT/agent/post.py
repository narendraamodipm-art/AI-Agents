"""Pick each run's jobs (10–12 per experience section) and write the Telegram and WhatsApp versions."""

import html
from collections import defaultdict
import unicodedata
from datetime import date, datetime, timedelta, timezone

import config


def main_field(job):
    return (job.get("fields") or ["software_engineer"])[0]


def experience_of(job):
    return job.get("experience") or "0-2"          # jobs saved before sections existed were all 0–2


def pick(pool, n=config.JOBS_PER_POST, experience=None, seen=None):
    """Newest first, spread across fields (round-robin), at most MAX_PER_COMPANY per company.
    `seen` (title, company) pairs are skipped; pass one set across calls to avoid repeats between sections."""
    pool = [j for j in pool if not experience or experience_of(j) in experience]
    pool = sorted(pool, key=lambda j: j.get("posted_at") or "", reverse=True)
    seen = set() if seen is None else seen
    role = lambda j: (j["title"].lower().strip(), j["company"].lower().strip())   # same role re-posted under a new ID
    by_field, queued = defaultdict(list), set()
    for j in pool:
        if role(j) not in seen and role(j) not in queued:
            queued.add(role(j))
            by_field[main_field(j)].append(j)
    chosen, per_company = [], defaultdict(int)
    while len(chosen) < n and any(by_field.values()):
        for f in config.FIELDS:
            while by_field[f]:
                j = by_field[f].pop(0)
                if per_company[j["company"].lower()] < config.MAX_PER_COMPANY:
                    chosen.append(j)
                    seen.add(role(j))
                    per_company[j["company"].lower()] += 1
                    break
            if len(chosen) >= n:
                break
    return chosen


def pick_sections(pool, n=config.JOBS_PER_POST):
    """{experience key: up to n jobs}, only for sections that have jobs, in EXPERIENCE order."""
    seen = set()
    sections = {k: pick(pool, n=n, experience=[k], seen=seen) for k in config.EXPERIENCE}
    return {k: v for k, v in sections.items() if v}


def grouped(jobs):
    groups = defaultdict(list)
    for j in jobs:
        groups[main_field(j)].append(j)
    return [(f, groups[f]) for f in config.FIELDS if groups[f]]


def mode_label(j):
    return {"remote": "Remote", "hybrid": "Hybrid"}.get(j.get("work_mode"), "On-site")


def nice_day(day: str) -> str:
    d = date.fromisoformat(day)
    return f"{d.day} {d.strftime('%b %Y')}"


def section_title(key):
    label, emoji, heading, _, _ = config.EXPERIENCE[key]
    return emoji, label, heading


def cut(text, width):
    text = " ".join((text or "").split())
    return text if len(text) <= width else text[:width - 1] + "…"


def where(j):
    if j.get("work_mode") == "remote":
        return "Remote"
    return short_loc(j).split(",")[0].split(" - ")[0].strip()


MODE_ICON = {"remote": "🏠 Remote", "hybrid": "🔀 Hybrid"}


def heads_up():
    """Short message sent one minute before each run's jobs."""
    return (f"⏰ <b>{slot_label()} jobs drop in 1 minute!</b>\n"
            "Keep your resume ready. Apply early, don't be late. 🚀")


def slot_label():
    """'🌅 Morning' or '🌆 Evening' by the current time in India (posts go out at 10 AM and 6 PM)."""
    hour = (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).hour
    return "🌅 Morning" if hour < 14 else "🌆 Evening"


def plain(text):
    """Drop emoji and other double-width characters, which would break the table's borders."""
    return "".join(ch for ch in " ".join((text or "").split())
                   if unicodedata.east_asian_width(ch) not in ("W", "F") and ord(ch) < 0x2190 or ch in "–—…·")


def box_table(ordered):
    """Fixed-width table with box borders. Each job: number column, then role on one line and
    company · place on the next. Field names are full-width divider rows."""
    num_w, text_w = config.BOX_NUM_WIDTH, config.BOX_TEXT_WIDTH
    inner = num_w + 1 + text_w                                 # width between the outer borders
    mid = f"├{'─' * num_w}┼{'─' * text_w}┤"
    open_ = f"├{'─' * num_w}┬{'─' * text_w}┤"                  # field row → job rows
    close = f"├{'─' * num_w}┴{'─' * text_w}┤"                  # job rows → field row
    bottom = f"└{'─' * num_w}┴{'─' * text_w}┘"
    row = lambda a, b: f"│{a:^{num_w}}│ {b:<{text_w - 1}}│"
    full = lambda t: f"│ {t:<{inner - 1}}│"

    lines = [f"┌{'─' * inner}┐", full("Tap a number below to apply"), f"├{'─' * inner}┤"]
    n = 0
    for gi, (f, items) in enumerate(ordered):
        flabel = config.FIELDS[f][0].upper()
        if gi:
            lines.append(close)
        lines.append(full(cut(flabel, inner - 1)))
        lines.append(open_)
        for ji, j in enumerate(items):
            n += 1
            if ji:
                lines.append(mid)
            star = "★" if config.is_mass_recruiter(j.get("company")) else ""
            lines.append(row(f"{n}{star}", cut(plain(j["title"]), text_w - 1)))
            lines.append(row("", cut(plain(f"{j['company']} · {where(j)}"), text_w - 1)))
    lines.append(bottom)
    return "\n".join(lines)


def telegram_posts(sections, day, site_url):
    """One Telegram message per experience section, in a bulleted alert layout:

        🛠️ Tech Job Alerts — 14 Nov 2026
        🎓 0–2 yrs · Freshers & interns
        📢 Company – Title
        • Experience / Role / Location / Work mode / Apply

    Returns [{"text": html, "buttons": None}]."""
    e = html.escape
    posts = []
    keys = list(sections)
    for key, jobs in sections.items():
        emoji, label, heading = section_title(key)
        lines = [f"🛠️ <b>Tech Job Alerts — {nice_day(day)}</b> · {slot_label()}", "",
                 f"{emoji} <b>{e(label)} · {e(heading)}</b>", ""]
        for f, items in grouped(jobs):
            flabel = config.FIELDS[f][0]
            for j in items:
                lines.append(f"📢 <b>{e(cut(j['company'], 40))} – {e(cut(j['title'], 80))}</b>")
                lines.append(f"• Experience: {e(label)}")
                lines.append(f"• Role: {e(flabel)}")
                lines.append(f"• Location: {e(short_loc(j))}")
                lines.append(f"• Work mode: {mode_label(j)}")
                if config.is_mass_recruiter(j.get("company")):
                    lines.append("• Note: 🏭 Mass recruiter")
                url = e(j["url"], quote=True)
                lines.append(f'• Apply: <a href="{url}">{url}</a>')
                lines.append("")
        if key == keys[-1]:
            lines.append(f'🤝 Know someone job hunting? <a href="{e(config.SHARE_URL, quote=True)}">Share this channel</a>')
        posts.append({"text": "\n".join(lines).rstrip(), "buttons": None})
    return posts


def telegram_table_posts(sections, day, site_url):
    """Alternative layout (not used): a boxed monospace table, then numbered Apply buttons.

    Telegram has no real tables and links inside fixed-width text can't be clicked, so the table is
    monospaced text with box borders and each job's Apply link is a numbered button underneath.
    Returns [{"text": html, "buttons": inline keyboard rows}].
    """
    e = html.escape
    posts = []
    keys = list(sections)
    for key, jobs in sections.items():
        emoji, label, heading = section_title(key)
        ordered = grouped(jobs)
        flat = [j for _, items in ordered for j in items]
        has_mass = any(config.is_mass_recruiter(j.get("company")) for j in flat)
        lines = [f"{emoji} <b>{e(heading.upper())} · {e(label)}</b>",
                 f"📅 {nice_day(day)} · {slot_label()} · 🆕 {len(flat)} jobs",
                 f"<pre>{e(box_table(ordered), quote=False)}</pre>"]
        if has_mass:
            lines.append("★ = 🏭 Mass recruiter")
        lines.append("👇 <b>Tap a number to apply</b>")
        if key == keys[-1]:
            lines.append(f'🤝 Know someone job hunting? <a href="{e(config.SHARE_URL, quote=True)}">Share this channel</a>')
        buttons = [{"text": f"{n}{'★' if config.is_mass_recruiter(j.get('company')) else ''} ↗", "url": j["url"]}
                   for n, j in enumerate(flat, 1)]
        rows = [buttons[i:i + config.BUTTONS_PER_ROW] for i in range(0, len(buttons), config.BUTTONS_PER_ROW)]
        posts.append({"text": "\n".join(lines), "buttons": rows})
    return posts


def teaser_jobs(sections):
    return [j for jobs in sections.values() for j in jobs[:config.TEASER_PER_SECTION]]


def whatsapp_text(sections, day, site_url):
    """One message with every section, to paste into the WhatsApp group."""
    lines = [f"🎯 *Tech Jobs: {nice_day(day)}*", ""]
    for key, jobs in sections.items():
        emoji, label, heading = section_title(key)
        lines += [f"━━━━━━━━━━━━━━", f"{emoji} *{label} · {heading}*", ""]
        n = 0
        for f, items in grouped(jobs):
            flabel, femoji, _ = config.FIELDS[f]
            lines.append(f"{femoji} *{flabel}*")
            for j in items:
                n += 1
                lines.append(f"{n}. {j['title']}: {j['company']} · {short_loc(j)} · {mode_label(j)}")
                lines.append(f"   👉 {j['url']}")
            lines.append("")
    lines.append(f"🔒 Get every job daily for ₹99/month: {site_url}")
    return "\n".join(lines)


def short_loc(j):
    loc = (j.get("location") or "India").split(" / ")[0]
    return loc if len(loc) <= 40 else loc[:37] + "…"
