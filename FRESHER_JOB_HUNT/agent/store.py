"""Storage: Supabase (REST API) when SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY are set,
otherwise a local JSON file (for testing on your laptop)."""

import json
import os
from datetime import date, datetime, timedelta, timezone

import requests

import config

JOB_COLUMNS = ["url", "title", "company", "location", "work_mode", "fields", "min_years", "source", "posted_at"]


def get_store():
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    return SupabaseStore(url, key) if url and key else LocalStore()


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
        since = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        rows = self._req("GET", "jobs", {"select": "url", "found_at": f"gte.{since}", "limit": 20000})
        return {r["url"] for r in rows}

    def save_jobs(self, jobs):
        if jobs:
            rows = [{c: j.get(c) for c in JOB_COLUMNS} for j in jobs]
            self._req("POST", "jobs", {"on_conflict": "url"}, rows, "resolution=ignore-duplicates,return=minimal")

    def unposted_pool(self, days):
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        return self._req("GET", "jobs", {"select": "*", "posted_on": "is.null", "found_at": f"gte.{since}",
                                         "order": "posted_at.desc", "limit": 500})

    def mark_posted(self, ids, day):
        if ids:
            self._req("PATCH", "jobs", {"id": f"in.({','.join(map(str, ids))})"}, {"posted_on": day}, "return=minimal")

    def save_daily_post(self, day, jobs, telegram_text, whatsapp_text):
        row = {"day": day, "job_ids": [j["id"] for j in jobs], "jobs": [public_job(j) for j in jobs],
               "telegram_text": telegram_text, "whatsapp_text": whatsapp_text}
        self._req("POST", "daily_posts", {"on_conflict": "day"}, row, "resolution=merge-duplicates,return=minimal")

    def email_subscribers(self):
        return self._req("GET", "users", {"select": "name,email,fields,work_modes,token",
                                          "status": "eq.active", "email_alerts": "is.true"})


class LocalStore:
    """Same interface, kept in agent/state/local_db.json (gitignored)."""
    name = "local file"

    def __init__(self):
        config.LOCAL_STATE.mkdir(exist_ok=True)
        self.path = config.LOCAL_STATE / "local_db.json"
        self.db = json.loads(self.path.read_text("utf-8")) if self.path.exists() else {"jobs": [], "daily_posts": {}}

    def _save(self):
        self.path.write_text(json.dumps(self.db, indent=1, ensure_ascii=False), "utf-8")

    def is_empty(self):
        return not self.db["jobs"]

    def known_urls(self):
        return {j["url"] for j in self.db["jobs"]}

    def save_jobs(self, jobs):
        known, next_id = self.known_urls(), len(self.db["jobs"]) + 1
        now = datetime.now(timezone.utc).isoformat()
        for j in jobs:
            if j["url"] not in known:
                self.db["jobs"].append(dict({c: j.get(c) for c in JOB_COLUMNS}, id=next_id, found_at=now, posted_on=None))
                known.add(j["url"])
                next_id += 1
        self._save()

    def unposted_pool(self, days):
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        pool = [j for j in self.db["jobs"] if not j["posted_on"] and j["found_at"] >= since]
        return sorted(pool, key=lambda j: j.get("posted_at") or "", reverse=True)

    def mark_posted(self, ids, day):
        for j in self.db["jobs"]:
            if j["id"] in ids:
                j["posted_on"] = day
        self._save()

    def save_daily_post(self, day, jobs, telegram_text, whatsapp_text):
        self.db["daily_posts"][day] = {"jobs": [public_job(j) for j in jobs], "whatsapp_text": whatsapp_text}
        self._save()

    def email_subscribers(self):
        return []


def public_job(j):
    """What the website's 'Today' page shows for a job."""
    return {k: j.get(k) for k in ("id", "title", "company", "location", "work_mode", "fields", "url", "posted_at")}


def today_ist() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).date().isoformat()
