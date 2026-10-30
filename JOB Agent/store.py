"""SQLite database of jobs, discovered GCCs and handled Telegram messages.

Job status flow:
    pending → shortlisted (fit ≥ MIN_FIT_TO_NOTIFY) or low_fit
    shortlisted → approved (you said APPLY; kit prepared) → applied (you marked it)
    shortlisted → skipped
"""

import sqlite3
from datetime import date

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    no INTEGER PRIMARY KEY AUTOINCREMENT,   -- the number used in Telegram ("APPLY 12")
    key TEXT UNIQUE, company TEXT, title TEXT, location TEXT, url TEXT, posted TEXT,
    source TEXT, description TEXT, first_seen TEXT,
    status TEXT DEFAULT 'pending', fit INTEGER, match INTEGER, summary TEXT,
    job_profile TEXT, gap TEXT, notified_on TEXT,
    letter TEXT, tips TEXT, warnings TEXT
);
CREATE TABLE IF NOT EXISTS gccs (
    company TEXT PRIMARY KEY, city TEXT, summary TEXT, url TEXT, found_on TEXT, searched INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS handled_messages (sid TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS companies (       -- the company's presence in India, looked up once
    company TEXT PRIMARY KEY, india_since TEXT, india_cities TEXT, india_headcount TEXT, about TEXT
);
"""
# columns added after the first version — added to existing databases on connect
NEW_COLUMNS = {"jobs": ["salary TEXT", "salary_source TEXT", "work_mode TEXT", "experience TEXT"],
               "gccs": ["announced TEXT"]}


def connect():
    config.DATA_DIR.mkdir(exist_ok=True)
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    for table, columns in NEW_COLUMNS.items():
        existing = {r["name"] for r in con.execute(f"PRAGMA table_info({table})")}
        for col in columns:
            if col.split()[0] not in existing:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
    return con


def known_keys(con) -> set[str]:
    return {r["key"] for r in con.execute("SELECT key FROM jobs")}


def add_jobs(con, jobs: list[dict]):
    today = date.today().isoformat()
    con.executemany(
        "INSERT OR IGNORE INTO jobs (key, company, title, location, url, posted, source, description, first_seen) "
        "VALUES (:key, :company, :title, :location, :url, :posted, :source, :description, :first_seen)",
        [{**j, "first_seen": today} for j in jobs],
    )
    con.commit()


def jobs(con, where="1=1", params=(), order="fit DESC, posted DESC") -> list[dict]:
    return [dict(r) for r in con.execute(f"SELECT * FROM jobs WHERE {where} ORDER BY {order}", params)]


def job(con, no: int) -> dict | None:
    row = con.execute("SELECT * FROM jobs WHERE no = ?", (no,)).fetchone()
    return dict(row) if row else None


def update_job(con, no: int, **fields):
    cols = ", ".join(f"{k} = ?" for k in fields)
    con.execute(f"UPDATE jobs SET {cols} WHERE no = ?", (*fields.values(), no))
    con.commit()


def add_gcc(con, company, city, summary, url, announced="") -> bool:
    """True if this company wasn't known before."""
    cur = con.execute("INSERT OR IGNORE INTO gccs (company, city, summary, url, found_on, announced) "
                      "VALUES (?, ?, ?, ?, ?, ?)",
                      (company, city, summary, url, date.today().isoformat(), announced))
    con.commit()
    return cur.rowcount == 1


def company(con, name) -> dict | None:
    row = con.execute("SELECT * FROM companies WHERE company = ?", (name,)).fetchone()
    return dict(row) if row else None


def save_company(con, name, **facts):
    con.execute("INSERT OR REPLACE INTO companies (company, india_since, india_cities, india_headcount, about) "
                "VALUES (?, ?, ?, ?, ?)", (name, facts["india_since"], facts["india_cities"],
                                           facts["india_headcount"], facts["about"]))
    con.commit()


def gccs(con, where="1=1", params=()) -> list[dict]:
    return [dict(r) for r in con.execute(f"SELECT * FROM gccs WHERE {where} ORDER BY found_on DESC", params)]


def message_handled(con, sid) -> bool:
    cur = con.execute("INSERT OR IGNORE INTO handled_messages (sid) VALUES (?)", (sid,))
    con.commit()
    return cur.rowcount == 0
