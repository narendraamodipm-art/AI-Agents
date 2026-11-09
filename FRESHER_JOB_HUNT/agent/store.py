"""Storage: two JSON files in FRESHER_JOB_HUNT/data/, committed back to the repo by the daily GitHub Action.

    jobs.json         every job seen recently, so nothing is posted twice
    latest_post.json  today's post, which the website's job pages read
"""

import json
from datetime import date, datetime, timedelta, timezone

import config

JOB_COLUMNS = ["url", "title", "company", "location", "work_mode", "fields", "min_years", "experience", "source",
               "posted_at"]


def get_store():
    return FileStore()


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

    def save_daily_post(self, day, jobs):
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
