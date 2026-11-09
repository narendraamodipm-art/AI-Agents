"""Pick the day's jobs (10–12 per experience section) and write the Telegram and WhatsApp versions."""

import html
from collections import defaultdict
from datetime import date

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


def telegram_posts(sections, day, site_url):
    """One Telegram message per experience section."""
    e = html.escape
    posts = []
    for key, jobs in sections.items():
        emoji, label, heading = section_title(key)
        lines = [f"{emoji} <b>{e(label)} · {e(heading)}</b>: {nice_day(day)}", ""]
        n = 0
        for f, items in grouped(jobs):
            flabel, femoji, _ = config.FIELDS[f]
            lines.append(f"{femoji} <b>{e(flabel)}</b>")
            for j in items:
                n += 1
                lines.append(f"{n}. <b>{e(j['title'])}</b>: {e(j['company'])} · {e(short_loc(j))} · {mode_label(j)}")
                lines.append(f'   👉 <a href="{e(j["url"], quote=True)}">Apply</a>')
            lines.append("")
        lines.append(f'🔔 All of today\'s jobs: <a href="{e(site_url)}">{e(site_url.replace("https://", ""))}</a>')
        posts.append("\n".join(lines))
    return posts


def teaser_jobs(sections):
    return [j for jobs in sections.values() for j in jobs[:config.TEASER_PER_SECTION]]


def teaser_post(sections, day, site_url):
    """One message for the free channel: a sample from each section and a link to subscribe."""
    e = html.escape
    lines = [f"🎯 <b>Today's free picks: {nice_day(day)}</b>", ""]
    for key, jobs in sections.items():
        emoji, label, _ = section_title(key)
        lines.append(f"{emoji} <b>{e(label)}</b>")
        for j in jobs[:config.TEASER_PER_SECTION]:
            lines.append(f"• <b>{e(j['title'])}</b>: {e(j['company'])} · {e(short_loc(j))} · {mode_label(j)}")
            lines.append(f'   👉 <a href="{e(j["url"], quote=True)}">Apply</a>')
        lines.append("")
    lines.append(f'🔒 Get the full list every day for ₹99/month: <a href="{e(site_url)}">{e(site_url.replace("https://", ""))}</a>')
    return "\n".join(lines)


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
    lines.append(f"🔔 All of today's jobs: {site_url}")
    return "\n".join(lines)


def short_loc(j):
    loc = (j.get("location") or "India").split(" / ")[0]
    return loc if len(loc) <= 40 else loc[:37] + "…"
