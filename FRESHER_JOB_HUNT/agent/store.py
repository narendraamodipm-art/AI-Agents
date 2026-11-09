"""Storage. Paid mode (TELEGRAM_PAID_CHANNEL_ID set) uses Supabase, so the paid list stays out of the public repo.

Free mode uses two JSON files in FRESHER_JOB_HUNT/data/, committed back to the repo by the daily GitHub Action:

    jobs.json         every job seen recently, so nothing is posted twice
    latest_post.json  today's post, which the website's job pages read
"""

import json
import os
from datetime import datetime, timedelta, timezone

import requests

import config

JOB_COLUMNS = ["url", "title", "company", "location", "work_mode", "fields", "min_years", "experience", "source",
               "posted_at"]


def get_store():
    if not os.environ.get("TELEGRAM_PAID_CHANNEL_ID"):
        return FileStore()
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and key):
        raise SystemExit("Paid mode needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
    return SupabaseStore(url, key)


class SupabaseStore:
    name = "Supabase"

    def __init__(self, url, key):
        self.base = url.rstrip("/") + "/rest/v1"
        self.h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def _req(self, method, path, params=None, body=None, prefer=None):
        headers = dict(self.h, **({"Prefer": prefer} if prefer else {}))
        r = requests.request(method, f"{self.base}/{path}", params=params, json=body, headers=headers, timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase {method} {path}: {r.status_code} {r.text[:300]}")
        return r.json() if r.text else None

    def is_empty(self):
        return not self._req("GET", "jobs", {"select": "id", "limit": 1})

    def known_urls(self):
        since = (datetime.now(timezone.utc) - timedelta(days=config.SEEN_DAYS)).isoformat()
        urls, page = set(), 1000                     # Supabase returns at most 1,000 rows per request
        while True:
            rows = self._req("GET", "jobs", {"select": "url", "found_at": f"gte.{since}", "order": "id",
                                             "limit": page, "offset": len(urls)})
            urls |= {r["url"] for r in rows}
            if len(rows) < page:
                return urls

    def save_jobs(self, jobs):
        if jobs:
            rows = [{c: j.get(c) for c in JOB_COLUMNS} for j in jobs]
            self._req("POST", "jobs", {"on_conflict": "url"}, rows, "resolution=ignore-duplicates,return=minimal")

    def unposted_pool(self):
        since = (datetime.now(timezone.utc) - timedelta(days=config.POOL_DAYS)).isoformat()
        return self._req("GET", "jobs", {"select": "*", "posted_on": "is.null", "found_at": f"gte.{since}",
                                         "order": "posted_at.desc", "limit": 1000})

    def mark_posted(self, ids, day):
        if ids:
            self._req("PATCH", "jobs", {"id": f"in.({','.join(map(str, ids))})"}, {"posted_on": day}, "return=minimal")

    def save_daily_post(self, day, jobs, teaser=None):
        row = {"day": day, "job_ids": [j["id"] for j in jobs], "jobs": [public_job(j) for j in jobs],
               "teaser": [public_job(j) for j in teaser or []]}
        self._req("POST", "daily_posts", {"on_conflict": "day"}, row, "resolution=merge-duplicates,return=minimal")

    def expired_members(self):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=config.GRACE_DAYS)).isoformat()
        return self._req("GET", "subscribers", {"select": "id,telegram_user_id", "paid_until": f"lt.{cutoff}",
                                                "telegram_user_id": "not.is.null", "removed_at": "is.null"})

    def mark_removed(self, subscriber_id):
        now = datetime.now(timezone.utc).isoformat()
        self._req("PATCH", "subscribers", {"id": f"eq.{subscriber_id}"},
                  {"status": "expired", "removed_at": now, "updated_at": now}, "return=minimal")


class FileStore:
    name = "JSON files"

    def __init__(self):
        self.path = config.DATA_DIR / "jobs.json"
        self.jobs = json.loads(self.path.read_text("utf-8"))["jobs"] if self.path.exists() else []

    def _save(self):
        now = datetime.now(timezone.utc)
        keep_after = (now - timedelta(days=config.SEEN_DAYS)).isoformat()
        pool_after = (now - timedelta(days=config.POOL_DAYS)).isoformat()
        kept = []
        for j in self.jobs:
            if j["found_at"] < keep_after:
                continue
            if j["posted_on"] or j["found_at"] < pool_after:      # can't be posted again: only the URL still matters
                j = {k: j[k] for k in ("id", "url", "found_at", "posted_on")}
            kept.append(j)
        self.jobs = kept
        config.DATA_DIR.mkdir(exist_ok=True)
        rows = ",\n".join(json.dumps(j, ensure_ascii=False) for j in self.jobs)    # one job per line: small git diffs
        self.path.write_text('{"jobs": [\n' + rows + "\n]}\n", "utf-8", newline="\n")

    def is_empty(self):
        return not self.jobs

    def known_urls(self):
        return {j["url"] for j in self.jobs}

    def save_jobs(self, jobs):
        known = self.known_urls()
        next_id = max((j["id"] for j in self.jobs), default=0) + 1
        now = datetime.now(timezone.utc).isoformat()
        for j in jobs:
            if j["url"] not in known:
                self.jobs.append(dict({c: j.get(c) for c in JOB_COLUMNS}, id=next_id, found_at=now, posted_on=None))
                known.add(j["url"])
                next_id += 1
        self._save()

    def unposted_pool(self):
        since = (datetime.now(timezone.utc) - timedelta(days=config.POOL_DAYS)).isoformat()
        pool = [j for j in self.jobs if not j["posted_on"] and j["found_at"] >= since]
        return sorted(pool, key=lambda j: j.get("posted_at") or "", reverse=True)

    def mark_posted(self, ids, day):
        ids = set(ids)
        for j in self.jobs:
            if j["id"] in ids:
                j["posted_on"] = day
        self._save()

    def expired_members(self):
        return []

    def mark_removed(self, subscriber_id):
        pass

    def save_daily_post(self, day, jobs, teaser=None):
        config.DATA_DIR.mkdir(exist_ok=True)
        (config.DATA_DIR / "latest_post.json").write_text(
            json.dumps({"day": day, "jobs": [public_job(j) for j in jobs]}, ensure_ascii=False, indent=1) + "\n",
            "utf-8", newline="\n")


def public_job(j):
    """What the website shows for a job."""
    return {k: j.get(k) for k in ("id", "title", "company", "location", "work_mode", "fields", "experience", "url",
                                  "posted_at")}


def today_ist() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).date().isoformat()
