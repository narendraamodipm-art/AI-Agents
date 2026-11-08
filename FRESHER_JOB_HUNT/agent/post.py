"""Pick the day's 10–12 jobs and write the Telegram, WhatsApp and email versions."""

import html
from collections import defaultdict
from datetime import date

import config


def main_field(job):
    return (job.get("fields") or ["software_engineer"])[0]


def pick(pool, n=config.JOBS_PER_POST, fields=None, work_modes=None):
    """Newest first, spread across fields (round-robin), at most MAX_PER_COMPANY per company."""
    pool = [j for j in pool
            if (not fields or set(j.get("fields") or []) & set(fields))
            and (not work_modes or (j.get("work_mode") or "onsite") in work_modes
                 or ("onsite" in work_modes and j.get("work_mode") == "hybrid"))]
    pool = sorted(pool, key=lambda j: j.get("posted_at") or "", reverse=True)
    by_field, seen = defaultdict(list), set()
    for j in pool:
        same = (j["title"].lower().strip(), j["company"].lower().strip())     # same role re-posted under a new ID
        if same not in seen:
            seen.add(same)
            by_field[main_field(j)].append(j)
    chosen, per_company = [], defaultdict(int)
    while len(chosen) < n and any(by_field.values()):
        for f in config.FIELDS:
            while by_field[f]:
                j = by_field[f].pop(0)
                if per_company[j["company"].lower()] < config.MAX_PER_COMPANY:
                    chosen.append(j)
                    per_company[j["company"].lower()] += 1
                    break
            if len(chosen) >= n:
                break
    return chosen


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


def telegram_text(jobs, day, site_url):
    e = html.escape
    lines = [f"🎯 <b>Fresher Jobs: {nice_day(day)}</b> (0–2 yrs)", ""]
    n = 0
    for f, items in grouped(jobs):
        label, emoji, _ = config.FIELDS[f]
        lines.append(f"{emoji} <b>{e(label)}</b>")
        for j in items:
            n += 1
            lines.append(f"{n}. <b>{e(j['title'])}</b>: {e(j['company'])} · {e(short_loc(j))} · {mode_label(j)}")
            lines.append(f'   👉 <a href="{e(j["url"], quote=True)}">Apply</a>')
        lines.append("")
    lines.append(f'🔔 All jobs + email alerts for your field: <a href="{e(site_url)}">{e(site_url.replace("https://", ""))}</a>')
    return "\n".join(lines)


def whatsapp_text(jobs, day, site_url):
    lines = [f"🎯 *Fresher Jobs: {nice_day(day)}* (0–2 yrs)", ""]
    n = 0
    for f, items in grouped(jobs):
        label, emoji, _ = config.FIELDS[f]
        lines.append(f"{emoji} *{label}*")
        for j in items:
            n += 1
            lines.append(f"{n}. {j['title']}: {j['company']} · {short_loc(j)} · {mode_label(j)}")
            lines.append(f"   👉 {j['url']}")
        lines.append("")
    lines.append(f"🔔 Email alerts for your field: {site_url}")
    return "\n".join(lines)


def email_html(user, jobs, day, site_url):
    e = html.escape
    rows = "".join(
        f'<tr><td style="padding:10px 0;border-bottom:1px solid #eee">'
        f'<div style="font-weight:600;color:#111">{e(j["title"])}</div>'
        f'<div style="color:#555;font-size:14px">{e(j["company"])} · {e(short_loc(j))} · {mode_label(j)}</div>'
        f'<a href="{e(j["url"], quote=True)}" style="color:#0d9488;font-size:14px">Apply →</a></td></tr>'
        for j in jobs)
    unsub = f"{site_url}/unsubscribe/{user['token']}"
    return (f'<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto">'
            f'<h2 style="color:#111">🎯 {len(jobs)} new fresher jobs for you</h2>'
            f'<p style="color:#555">Hi {e(user["name"])}, here are today\'s openings ({nice_day(day)}).</p>'
            f'<table style="width:100%;border-collapse:collapse">{rows}</table>'
            f'<p style="color:#888;font-size:12px;margin-top:24px">You get this because you signed up at '
            f'<a href="{e(site_url)}">{e(site_url)}</a>. <a href="{e(unsub)}">Unsubscribe</a></p></div>')


def short_loc(j):
    loc = (j.get("location") or "India").split(" / ")[0]
    return loc if len(loc) <= 40 else loc[:37] + "…"
