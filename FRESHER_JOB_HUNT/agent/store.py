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
        """One row per day. A second run that day adds its jobs to the row; the website shows the newest samples."""
        old = (self._req("GET", "daily_posts", {"select": "job_ids,jobs", "day": f"eq.{day}"}) or [{}])[0]
        new_ids = {j["id"] for j in jobs}
        kept = [j for j in old.get("jobs") or [] if j.get("id") not in new_ids]
        row = {"day": day, "job_ids": [i for i in old.get("job_ids") or [] if i not in new_ids] + [j["id"] for j in jobs],
               "jobs": kept + [public_job(j) for j in jobs], "teaser": [public_job(j) for j in teaser]}
        self._req("POST", "daily_posts", {"on_conflict": "day"}, row, "resolution=merge-duplicates,return=minimal")

    def database_bytes(self):
        return self._req("POST", "rpc/database_size_bytes", body={})

    def trim_history(self, limit):
        """Delete up to `limit` of the oldest jobs and two old daily posts. Returns how many jobs went.

        Only job data is touched, never subscribers or payments. Jobs younger than SEEN_DAYS stay,
        because they're what stops a job being posted twice.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=config.SEEN_DAYS)
        rows = self._req("GET", "jobs", {"select": "id", "found_at": f"lt.{cutoff.isoformat()}", "order": "id",
                                         "limit": min(limit, 1000)})
        if rows:
            self._req("DELETE", "jobs", {"id": f"in.({','.join(str(r['id']) for r in rows)})"}, prefer="return=minimal")
        days = self._req("GET", "daily_posts", {"select": "day", "day": f"lt.{cutoff.date().isoformat()}", "order": "day",
                                                "limit": 2})
        if days:
            self._req("DELETE", "daily_posts", {"day": f"in.({','.join(d['day'] for d in days)})"}, prefer="return=minimal")
        return len(rows)

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
    return {**{k: j.get(k) for k in ("id", "title", "company", "location", "work_mode", "fields", "experience", "url",
                                     "posted_at")},
            "mass_recruiter": config.is_mass_recruiter(j.get("company"))}


def today_ist() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).date().isoformat()
