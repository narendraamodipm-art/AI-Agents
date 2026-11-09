"""Storage: Supabase (REST API). Kept out of the public GitHub repo so the paid job list stays private."""

import os
from datetime import datetime, timedelta, timezone

import requests

import config

JOB_COLUMNS = ["url", "title", "company", "location", "work_mode", "fields", "min_years", "experience", "source",
               "posted_at"]


def get_store():
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and key):
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required.")
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

    def save_daily_post(self, day, jobs, teaser):
        row = {"day": day, "job_ids": [j["id"] for j in jobs], "jobs": [public_job(j) for j in jobs],
               "teaser": [public_job(j) for j in teaser]}
        self._req("POST", "daily_posts", {"on_conflict": "day"}, row, "resolution=merge-duplicates,return=minimal")

    def expired_members(self):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=config.GRACE_DAYS)).isoformat()
        return self._req("GET", "subscribers", {"select": "id,telegram_user_id", "paid_until": f"lt.{cutoff}",
                                                "telegram_user_id": "not.is.null", "removed_at": "is.null"})

    def mark_removed(self, subscriber_id):
        now = datetime.now(timezone.utc).isoformat()
        self._req("PATCH", "subscribers", {"id": f"eq.{subscriber_id}"},
                  {"status": "expired", "removed_at": now, "updated_at": now}, "return=minimal")


def public_job(j):
    """What the website shows for a job."""
    return {k: j.get(k) for k in ("id", "title", "company", "location", "work_mode", "fields", "experience", "url",
                                  "posted_at")}


def today_ist() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).date().isoformat()
