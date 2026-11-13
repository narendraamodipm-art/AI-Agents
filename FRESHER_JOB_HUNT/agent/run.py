"""Daily Fresher Job Hunt run.

    python agent/run.py --dry-run        find jobs and print today's posts; sends and saves nothing
    python agent/run.py                  find jobs, save them, post to Telegram
    python agent/run.py --wait           same, but wait for the next SEND_TIMES_IST slot (10:00 or 18:00) before sending
                                         (used by the GitHub Actions schedule, which starts a bit early)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402
import filters  # noqa: E402
import notify  # noqa: E402
import post  # noqa: E402
import sources  # noqa: E402
from store import get_store, public_job, today_ist  # noqa: E402

try:
    from dotenv import load_dotenv
    load_dotenv(config.ROOT / ".env")
except ImportError:
    pass

# Secrets pasted into GitHub often keep a trailing line break, which breaks URLs and headers.
for name, value in list(os.environ.items()):
    os.environ[name] = value.strip()


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def wait_until_send_time(lead=0):
    """Wait until `lead` seconds before the next posting slot, if that's at most 90 minutes away.
    On a late start there's nothing to wait for, so the run carries on straight away."""
    now_ist = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    waits = []
    for slot in config.SEND_TIMES_IST:
        hh, mm = map(int, slot.split(":"))
        wait = (now_ist.replace(hour=hh, minute=mm, second=0, microsecond=0) - now_ist).total_seconds() - lead
        if 0 < wait <= 90 * 60:
            waits.append((wait, slot))
    if waits:
        wait, slot = min(waits)
        log(f"Waiting {int(wait // 60)} min until {slot} IST before sending")
        time.sleep(wait)


def admin(text, html=False):
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if chat and os.environ.get("TELEGRAM_BOT_TOKEN"):
        notify.telegram(chat, text, html=html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print the posts; don't save or send anything")
    ap.add_argument("--wait", action="store_true", help=f"wait for the next of {config.SEND_TIMES_IST} IST before sending")
    args = ap.parse_args()

    store = get_store()
    day = today_ist()
    site = (os.environ.get("SITE_URL") or config.SITE_URL_DEFAULT).rstrip("/")
    max_age = config.FIRST_RUN_AGE_DAYS if store.is_empty() else config.MAX_AGE_DAYS
    log(f"Storage: {store.name} · day {day} · looking back {max_age} days")

    # 1. Find and filter
    known = store.known_urls()
    candidates = [j for j in sources.collect(max_age, log) if j["url"] not in known]
    log(f"{len(candidates)} new candidates (not seen before)")
    found = filters.classify_jobs(candidates, log)
    log(f"{len(found)} jobs placed in experience sections")

    if args.dry_run:
        sections = post.pick_sections(found)
        print("\n" + "=" * 70 + "\nWHATSAPP POST (dry run; Telegram gets one message per section)\n" + "=" * 70)
        print(post.whatsapp_text(sections, day, site))
        # Preview for the local website (the dev server shows this instead of the published post)
        config.LOCAL_STATE.mkdir(exist_ok=True)
        preview = [dict(public_job(j), id=i) for i, j in enumerate(post.teaser_jobs(sections))]
        (config.LOCAL_STATE / "preview_post.json").write_text(
            json.dumps({"day": day, "jobs": preview}, ensure_ascii=False, indent=1), "utf-8")
        print(f"\nAll {len(found)} jobs found:")
        order = list(config.EXPERIENCE)
        newest_first = sorted(found, key=lambda j: j["posted_at"] or "", reverse=True)
        for j in sorted(newest_first, key=lambda j: order.index(j["experience"])):
            print(f" - {config.EXPERIENCE[j['experience']][0]:8} [{','.join(j['fields'])}] {j['title']} | {j['company']} | "
                  f"{j['location']} | {j['work_mode']} | {j['posted_at']} | min_yrs={j.get('min_years')} | {j['source']}")
        return

    paid_channel = os.environ.get("TELEGRAM_PAID_CHANNEL_ID")
    if not paid_channel:
        sys.exit("TELEGRAM_PAID_CHANNEL_ID is required: it's the private channel the jobs are posted to.")

    # Remove members whose subscription has run out
    errors = []
    for member in store.expired_members():
        try:
            notify.remove_member(paid_channel, member["telegram_user_id"])
            store.mark_removed(member["id"])
            log(f"Removed expired subscriber {member['id']}")
        except Exception as e:
            errors.append(str(e))

    # 2. Save, then pick today's post (per section) from everything not yet posted
    store.save_jobs(found)
    # Deleting doesn't shrink the reported size, so delete about what was added rather than "until it's small".
    try:
        size = store.database_bytes()
        if size >= config.DB_CLEANUP_BYTES:
            trimmed = store.trim_history(max(len(found) * 2, 200))
            log(f"Database is {size // 1024 ** 2} MB: deleted {trimmed} old job records")
    except Exception as e:
        errors.append(f"Database cleanup skipped: {e}")
    pool = store.unposted_pool()
    sections = post.pick_sections(pool)
    chosen = [j for jobs in sections.values() for j in jobs]
    log(f"Pool of unposted jobs: {len(pool)} → today's post: "
        + ", ".join(f"{config.EXPERIENCE[k][0]}: {len(v)}" for k, v in sections.items()))
    if not chosen:
        admin(f"Fresher Job Hunt {day}: no new jobs today, nothing posted.")
        return

    tg_posts = post.telegram_posts(sections, day, site)
    wa_text = post.whatsapp_text(sections, day, site)
    store.save_daily_post(day, chosen, post.teaser_jobs(sections))

    if args.wait:
        wait_until_send_time(lead=config.HEADS_UP_SECONDS)

    # 3. Send: a short "get ready" heads-up, then the jobs a minute later
    try:
        notify.telegram(paid_channel, post.heads_up(), html=True)
        log("Sent the heads-up; posting jobs in 1 minute")
        time.sleep(config.HEADS_UP_SECONDS)
    except Exception as e:
        errors.append(f"Heads-up not sent: {e}")
    posted = []                                          # only jobs that really went out count as posted
    for key, tg_text in zip(sections, tg_posts):
        try:
            notify.telegram(paid_channel, tg_text, html=True)
            posted += sections[key]
        except Exception as e:
            errors.append(str(e))
    log(f"Posted {len(posted)} of {len(chosen)} jobs to the private channel")
    store.mark_posted([j["id"] for j in posted], day)

    try:
        admin(f"📋 WhatsApp post for {day}. Copy everything below this line and paste it in your group:")
        admin(wa_text)
    except Exception as e:
        errors.append(str(e))

    summary = f"{'✅' if posted else '❌'} Fresher Job Hunt {day}: {len(posted)} jobs posted"
    if errors:
        summary += f"\n⚠️ {len(errors)} errors:\n" + "\n".join(errors[:5])
    log(summary)
    admin(summary)
    if errors and not posted:
        sys.exit(1)


if __name__ == "__main__":
    main()
