"""Where jobs come from. Every source returns a list of job dicts:

    {url, title, company, location, work_mode, posted_at (YYYY-MM-DD), source, description}

Only public job APIs are used (no scraping of sites whose terms forbid it).
"""

import html
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse

import requests

import config

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "FresherJobHunt/1.0 (+job alerts for freshers)", "Accept": "application/json"})


# ── Helpers ──────────────────────────────────────────────────────────────────
def get_json(url, **kw):
    r = SESSION.get(url, timeout=30, **kw)
    r.raise_for_status()
    return r.json()


def post_json(url, body, **kw):
    r = SESSION.post(url, json=body, timeout=30, **kw)
    r.raise_for_status()
    return r.json()


def html_to_text(text: str) -> str:
    text = re.sub(r"<(br|/p|/li|/h\d|/div)[^>]*>", "\n", text or "", flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n\n", text)).strip()


def clean_title(title: str) -> str:
    """'IN_Associate_Data Science' → 'IN Associate Data Science'; trims stray punctuation."""
    t = re.sub(r"[_\s]+", " ", title or "").strip()
    return re.sub(r"^[\s,;:|–-]+|[\s,;:|–(-]+$", "", t)


def company_name(slug: str) -> str:
    """Board slug → display name ('ag' → 'AG', 'tiger-analytics' → 'Tiger Analytics')."""
    s = slug.replace("-", " ").replace("_", " ").strip()
    return s.upper() if len(s) <= 3 else s.title()


def title_prefilter(title: str) -> bool:
    """Tech role in one of our fields, not senior, not a non-tech job."""
    title = clean_title(title)
    return (any(p.search(title) for p in config.FIELD_PATTERNS.values())
            and not config.SENIOR_TITLE.search(title) and not config.NON_TECH.search(title))


def work_mode_of(location: str, remote_flag: bool = False, workplace: str = "") -> str:
    w = (workplace or "").lower()
    if remote_flag or w == "remote" or config.REMOTE.search(location or ""):
        return "remote"
    if w == "hybrid" or "hybrid" in (location or "").lower():
        return "hybrid"
    return "onsite"


def location_ok(location: str, mode: str) -> bool:
    loc = location or ""
    if config.INDIA.search(loc):
        return True
    return mode == "remote" and bool(config.REMOTE_OK_REGION.search(loc))


def iso_day(value) -> str:
    """Many date formats → 'YYYY-MM-DD' (today if unknown)."""
    if not value:
        return date.today().isoformat()
    if isinstance(value, (int, float)):                       # epoch milliseconds (Lever)
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date().isoformat()
    return str(value)[:10]


def recent(day: str, max_age: int) -> bool:
    return day >= (date.today() - timedelta(days=max_age)).isoformat()


def _safe(fn, *args):
    try:
        return fn(*args)
    except Exception:
        return []


# ── Greenhouse ───────────────────────────────────────────────────────────────
def greenhouse_detail(slug, job_id, company):
    j = get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}")
    loc = (j.get("location") or {}).get("name", "")
    return {"url": j["absolute_url"], "title": j["title"].strip(), "company": company, "location": loc,
            "work_mode": work_mode_of(loc), "posted_at": iso_day(j.get("first_published") or j.get("updated_at")),
            "source": "Greenhouse", "description": html_to_text(html.unescape(j.get("content", "")))}


def greenhouse(slug, company, max_age):
    jobs = get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")["jobs"]
    picks = []
    for j in jobs:
        loc = (j.get("location") or {}).get("name", "")
        posted = iso_day(j.get("first_published") or j.get("updated_at"))
        if title_prefilter(j["title"]) and location_ok(loc, work_mode_of(loc)) and recent(posted, max_age):
            picks.append(j["id"])
    return [d for d in (_safe_one(greenhouse_detail, slug, i, company) for i in picks[:25]) if d]


def _safe_one(fn, *args):
    try:
        return fn(*args)
    except Exception:
        return None


# ── Lever ────────────────────────────────────────────────────────────────────
def lever_job(j, company):
    cats = j.get("categories") or {}
    loc = cats.get("location") or ", ".join(cats.get("allLocations") or [])
    lists = "\n".join(f"{x.get('text', '')}\n{html_to_text(x.get('content', ''))}" for x in j.get("lists") or [])
    return {"url": j["hostedUrl"], "title": j["text"].strip(), "company": company, "location": loc,
            "work_mode": work_mode_of(loc, workplace=j.get("workplaceType", "")),
            "posted_at": iso_day(j.get("createdAt")), "source": "Lever",
            "description": f"{j.get('descriptionPlain', '')}\n{lists}\n{j.get('additionalPlain', '')}"}


def lever(slug, company, max_age):
    out = []
    for j in get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json"):
        job = lever_job(j, company)
        if title_prefilter(job["title"]) and location_ok(job["location"], job["work_mode"]) and recent(job["posted_at"], max_age):
            out.append(job)
    return out


# ── Ashby ────────────────────────────────────────────────────────────────────
def ashby_job(j, company):
    locs = [j.get("location") or ""] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
    loc = " / ".join(x for x in locs if x)
    return {"url": j.get("jobUrl") or j.get("applyUrl"), "title": j["title"].strip(), "company": company,
            "location": loc, "work_mode": work_mode_of(loc, j.get("isRemote", False), j.get("workplaceType", "")),
            "posted_at": iso_day(j.get("publishedAt")), "source": "Ashby",
            "description": j.get("descriptionPlain") or html_to_text(j.get("descriptionHtml", ""))}


def ashby(slug, company, max_age):
    out = []
    for j in get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")["jobs"]:
        job = ashby_job(j, company)
        if title_prefilter(job["title"]) and location_ok(job["location"], job["work_mode"]) and recent(job["posted_at"], max_age):
            out.append(job)
    return out


# ── Workday (big tech centres in India) ─────────────────────────────────────
def workday_age(posted_on: str) -> int:
    t = (posted_on or "").lower()
    if "today" in t:
        return 0
    if "yesterday" in t:
        return 1
    n = re.search(r"\d+", t)
    return int(n.group()) if n else 30


def workday_detail(company, base, path, public_base):
    info = get_json(f"{base}{path}")["jobPostingInfo"]
    country = (info.get("country") or {}).get("descriptor", "")
    loc = info.get("location", "")
    if country and country != "India" and not config.INDIA.search(loc):
        return None
    loc = loc if config.INDIA.search(loc) else f"{loc}, India".strip(", ")
    return {"url": info.get("externalUrl") or f"{public_base}{path}", "title": info["title"].strip(),
            "company": company, "location": loc, "work_mode": work_mode_of(loc, workplace=info.get("remoteType", "")),
            "posted_at": iso_day(info.get("startDate")), "source": "Workday",
            "description": html_to_text(info.get("jobDescription", ""))}


def workday(entry, max_age):
    company, host, tenant, site = entry
    base = f"https://{host}/wday/cxs/{tenant}/{site}"
    paths = {}
    for term in config.WORKDAY_TERMS:
        try:
            data = post_json(f"{base}/jobs", {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": f"{term} India"})
        except Exception:
            continue
        for p in data.get("jobPostings", []):
            loc = p.get("locationsText", "")
            if (title_prefilter(p.get("title", "")) and workday_age(p.get("postedOn", "")) <= max_age
                    and (config.INDIA.search(loc) or "locations" in loc.lower())):
                paths[p["externalPath"]] = True
    jobs = [_safe_one(workday_detail, company, base, path, f"https://{host}/{site}") for path in list(paths)[:15]]
    return [j for j in jobs if j]


# ── Tavily web search (job-board sites only) ────────────────────────────────
def tavily_search(query):
    r = SESSION.post("https://api.tavily.com/search", timeout=60,
                     headers={"Authorization": f"Bearer {os.environ['TAVILY_API_KEY']}"},
                     json={"query": query, "time_range": "week", "max_results": 10,
                           "include_domains": config.TAVILY_DOMAINS})
    r.raise_for_status()
    return r.json().get("results", [])


def job_from_url(url, title_hint="", content_hint=""):
    """Turn a job-board URL into a structured job using that board's API where possible."""
    u = urlparse(url)
    parts = [p for p in u.path.split("/") if p]
    host = u.netloc.lower()
    if "greenhouse.io" in host and "jobs" in parts:
        slug, job_id = parts[0], parts[parts.index("jobs") + 1]
        return greenhouse_detail(slug, job_id, config.GREENHOUSE.get(slug, company_name(slug)))
    if host == "jobs.lever.co" and len(parts) >= 2:
        slug = parts[0]
        j = get_json(f"https://api.lever.co/v0/postings/{slug}/{parts[1]}")
        return lever_job(j, config.LEVER.get(slug, company_name(slug)))
    if host == "jobs.ashbyhq.com" and len(parts) >= 2:
        slug = parts[0]
        for j in get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")["jobs"]:
            if j.get("id") == parts[1]:
                return ashby_job(j, config.ASHBY.get(slug, company_name(slug)))
        return None
    if "myworkdayjobs.com" in host and "job" in parts:
        tenant, i = host.split(".")[0], parts.index("job")
        site = parts[i - 1]
        path = "/" + "/".join(parts[i:])
        return workday_detail(company_name(tenant), f"https://{host}/wday/cxs/{tenant}/{site}", path, f"https://{host}/{site}")
    return parse_web_result(url, host, title_hint, content_hint)


def parse_web_result(url, host, title_hint, content_hint):
    """Other boards (Wellfound, Cutshort, …): parse the search result's title. Keep only clear India jobs."""
    hint = re.sub(r"\s+", " ", title_hint).strip()
    title, company, location = hint, "", ""
    m = re.match(r"(.+?) is hiring (?:for )?(.+?) job in (.+)", hint, re.I)            # Cutshort style
    if m:
        company, title, location = m.group(1), m.group(2), m.group(3)
    elif " at " in hint:                                                                # Wellfound style
        title, rest = hint.split(" at ", 1)
        bits = [b.strip() for b in re.split(r"[•|]", rest)
                if b.strip() and b.strip().lower() not in {"wellfound", "cutshort", "instahyre"}]
        company, location = bits[0], ", ".join(bits[1:])
    else:
        title = re.split(r"\s[|–-]\s", hint)[0]
    location = re.sub(r"\s*[|–-]\s*(wellfound|cutshort|instahyre).*$", "", location, flags=re.I).strip()
    if not config.INDIA.search(f"{location} {content_hint}"):
        return None
    if not company or company.lower() in {"wellfound", "cutshort", "instahyre"}:
        return None                                                                     # can't tell who is hiring
    return {"url": url, "title": clean_title(title), "company": re.sub(r"\s+(pvt\.?\s*ltd\.?|private limited)$", "", company, flags=re.I).strip(),
            "location": location or "India", "work_mode": work_mode_of(location or content_hint),
            "posted_at": date.today().isoformat(), "source": "Web", "description": content_hint}


def tavily_jobs(max_age):
    if not os.environ.get("TAVILY_API_KEY"):
        return []
    results = {}
    for q in config.TAVILY_QUERIES:
        for r in _safe(tavily_search, q):
            results[r["url"]] = r
    jobs = [_safe_one(job_from_url, url, r.get("title", ""), r.get("content", "")) for url, r in list(results.items())[:40]]
    return [j for j in jobs if j and title_prefilter(j["title"]) and location_ok(j["location"], j["work_mode"])
            and recent(j["posted_at"], max_age + 4)]


# ── Optional aggregators (only if keys are set) ─────────────────────────────
def adzuna_jobs(max_age):
    app_id, app_key = os.environ.get("ADZUNA_APP_ID"), os.environ.get("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        return []
    out = {}
    for q in config.ADZUNA_QUERIES:
        try:
            data = get_json("https://api.adzuna.com/v1/api/jobs/in/search/1", params={
                "app_id": app_id, "app_key": app_key, "what": q, "category": "it-jobs",
                "max_days_old": max_age, "results_per_page": 50, "content-type": "application/json"})
        except Exception:
            continue
        for j in data.get("results", []):
            loc = (j.get("location") or {}).get("display_name", "India")
            job = {"url": j["redirect_url"], "title": html_to_text(j["title"]), "company": (j.get("company") or {}).get("display_name", ""),
                   "location": loc if config.INDIA.search(loc) else f"{loc}, India", "work_mode": work_mode_of(j.get("description", "")),
                   "posted_at": iso_day(j.get("created")), "source": "Adzuna", "description": html_to_text(j.get("description", ""))}
            if title_prefilter(job["title"]):
                out[job["url"]] = job
    return list(out.values())


def jsearch_jobs(max_age):
    key = os.environ.get("RAPIDAPI_KEY")
    if not key:
        return []
    out = {}
    for q in config.JSEARCH_QUERIES:
        try:
            data = get_json("https://jsearch.p.rapidapi.com/search", params={
                "query": q, "country": "in", "date_posted": "3days" if max_age <= 3 else "week", "num_pages": 1,
                "job_requirements": "under_3_years_experience,no_experience"},
                headers={"X-RapidAPI-Key": key, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"})
        except Exception:
            continue
        for j in data.get("data", []):
            loc = ", ".join(x for x in [j.get("job_city"), j.get("job_state"), "India"] if x)
            job = {"url": j.get("job_apply_link") or j.get("job_google_link"), "title": j.get("job_title", ""),
                   "company": j.get("employer_name", ""), "location": loc,
                   "work_mode": "remote" if j.get("job_is_remote") else "onsite",
                   "posted_at": iso_day(j.get("job_posted_at_datetime_utc")), "source": "JSearch",
                   "description": j.get("job_description", "")}
            if job["url"] and title_prefilter(job["title"]):
                out[job["url"]] = job
    return list(out.values())


# ── All sources ──────────────────────────────────────────────────────────────
def collect(max_age, log=print):
    tasks = ([("Greenhouse", greenhouse, (s, c, max_age)) for s, c in config.GREENHOUSE.items()]
             + [("Lever", lever, (s, c, max_age)) for s, c in config.LEVER.items()]
             + [("Ashby", ashby, (s, c, max_age)) for s, c in config.ASHBY.items()]
             + [("Workday", workday, (w, max_age)) for w in config.WORKDAY]
             + [("Web (Tavily)", tavily_jobs, (max_age,)), ("Adzuna", adzuna_jobs, (max_age,)),
                ("JSearch", jsearch_jobs, (max_age,))])
    with ThreadPoolExecutor(12) as pool:
        results = list(pool.map(lambda t: (t[0], _safe(t[1], *t[2])), tasks))
    counts, jobs = {}, {}
    for name, found in results:
        counts[name] = counts.get(name, 0) + len(found)
        for j in found:
            j["title"] = clean_title(j["title"])
            if title_prefilter(j["title"]):
                jobs.setdefault(j["url"], j)
    log("Candidates by source: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    return list(jobs.values())
