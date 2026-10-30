"""Where jobs come from: GCC career feeds (Workday, Greenhouse) and Tavily web search.

Every job is a plain dict:
    {key, company, title, location, url, posted (YYYY-MM-DD), source, description}
"""

import html
import json
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import config


# ── Helpers ──────────────────────────────────────────────────────────────────
def http_json(url, body=None, headers=None, timeout=30):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "Mozilla/5.0", **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def html_to_text(text: str) -> str:
    text = re.sub(r"<(br|/p|/li|/h\d|/div)[^>]*>", "\n", text or "", flags=re.I)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def title_ok(title: str) -> bool:
    t = title.lower()
    wanted = any(k in t for k in config.TITLE_KEYWORDS)
    excluded = any(re.search(rf"\b{re.escape(x)}\b", t) for x in config.TITLE_EXCLUDE)
    return wanted and not excluded


def in_india(location: str) -> bool:
    loc = location.lower()
    return "india" in loc or any(city in loc for city in config.INDIA_CITIES)


def company_ok(company: str) -> bool:
    return company.lower() not in {c.lower() for c in config.EXCLUDE_COMPANIES}


# ── Workday (most big GCCs: Target, Wells Fargo, Lowe's, PayPal, …) ─────────
def workday_age(posted_on: str) -> int:
    """'Posted Today' → 0, 'Posted Yesterday' → 1, 'Posted 5 Days Ago' → 5, '30+' → 30."""
    text = posted_on.lower()
    if "today" in text:
        return 0
    if "yesterday" in text:
        return 1
    n = re.search(r"\d+", text)
    return int(n.group()) if n else 30


def workday_search(entry, max_age):
    """Job stubs (title, path) from one Workday site that pass the title/age/location filters."""
    company, host, tenant, site = entry
    base = f"https://{host}/wday/cxs/{tenant}/{site}"
    stubs = {}
    for term in config.SEARCH_TERMS:
        try:
            data = http_json(f"{base}/jobs", {"appliedFacets": {}, "limit": 20, "offset": 0,
                                              "searchText": f"{term} India"})
        except Exception:
            continue
        for p in data.get("jobPostings", []):
            loc = p.get("locationsText") or ""
            if (title_ok(p.get("title", "")) and workday_age(p.get("postedOn", "")) <= max_age
                    and (in_india(loc) or "locations" in loc.lower())):   # "2 Locations" → check detail
                req_id = p["externalPath"].rsplit("_", 1)[-1]
                stubs[f"wd:{tenant}:{req_id}"] = (company, base, p["externalPath"])
    return stubs


def workday_detail(key, company, base, path):
    info = http_json(f"{base}{path}")["jobPostingInfo"]
    country = (info.get("country") or {}).get("descriptor", "")
    if country and country != "India":
        return None
    return {
        "key": key, "company": company, "title": info["title"], "location": info.get("location", "India"),
        "url": info.get("externalUrl") or f"{base}{path}", "posted": info.get("startDate") or date.today().isoformat(),
        "source": "Workday", "description": html_to_text(info.get("jobDescription", "")),
    }


# ── Greenhouse (Databricks, Stripe, Okta, MongoDB, …) ───────────────────────
def greenhouse_jobs(token, max_age):
    company = config.GREENHOUSE[token]
    try:
        jobs = http_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true")["jobs"]
    except Exception:
        return []
    cutoff = (date.today() - timedelta(days=max_age)).isoformat()
    found = []
    for j in jobs:
        posted = (j.get("first_published") or j.get("updated_at") or "")[:10]
        loc = j.get("location", {}).get("name", "")
        if title_ok(j["title"]) and in_india(loc) and posted >= cutoff:
            found.append({
                "key": f"gh:{token}:{j['id']}", "company": company, "title": j["title"], "location": loc,
                "url": j["absolute_url"], "posted": posted, "source": "Greenhouse",
                "description": html_to_text(html.unescape(j.get("content", ""))),
            })
    return found


def collect_feed_jobs(max_age, known_keys, log=print):
    """New jobs from all configured career feeds, skipping keys already in the database."""
    companies = [w for w in config.WORKDAY if company_ok(w[0])]
    with ThreadPoolExecutor(8) as pool:
        stub_maps = list(pool.map(lambda w: workday_search(w, max_age), companies))
        stubs = {k: v for m in stub_maps for k, v in m.items() if k not in known_keys}
        log(f"Workday: {len(stubs)} new matching postings across {len(companies)} GCCs")
        details = list(pool.map(lambda kv: _safe(workday_detail, kv[0], *kv[1]), stubs.items()))
        gh = [j for jobs in pool.map(lambda t: greenhouse_jobs(t, max_age), config.GREENHOUSE) for j in jobs]
    gh = [j for j in gh if j["key"] not in known_keys]
    log(f"Greenhouse: {len(gh)} new matching postings across {len(config.GREENHOUSE)} companies")
    return [j for j in details if j] + gh


def _safe(fn, *args):
    try:
        return fn(*args)
    except Exception:
        return None


# ── Tavily: newly announced GCCs, and jobs at them ───────────────────────────
def tavily(endpoint, payload):
    return http_json(f"https://api.tavily.com/{endpoint}", payload,
                     {"Authorization": f"Bearer {os.environ['TAVILY_API_KEY']}"}, timeout=60)


def gcc_news(days=7):
    """Recent news articles about GCCs opening or expanding in India."""
    articles = {}
    for q in config.GCC_NEWS_QUERIES:
        for r in tavily("search", {"query": q, "topic": "news", "days": days, "max_results": 8})["results"]:
            articles[r["url"]] = r
    return list(articles.values())


def salary_snippets(company, title) -> list[dict]:
    """Salary pages (AmbitionBox, Glassdoor, …) for this role at this company in India."""
    role = re.sub(r"[-–,(].*$", "", title).strip()          # 'Senior Data Engineer-4' → 'Senior Data Engineer'
    return tavily("search", {"query": f"{company} {role} salary in India", "max_results": 6,
                             "include_domains": ["ambitionbox.com", "glassdoor.co.in", "6figr.com",
                                                 "levels.fyi", "naukri.com"]})["results"]


def company_snippets(company) -> list[dict]:
    """Pages about the company's presence in India (when it started, cities, headcount)."""
    query = f"{company} India technology centre GCC established year cities employees"
    return tavily("search", {"query": query, "max_results": 5})["results"]


def web_jobs_at(company, known_keys):
    """Search the web for data jobs at one company in India; keep only single-posting URLs."""
    query = f'"{company}" India careers {config.SEARCH_TERMS[0]} job'
    results = tavily("search", {"query": query, "time_range": "month", "max_results": 8})["results"]
    hits = [r for r in results
            if any(p in r["url"].lower() for p in config.JOB_URL_PATTERNS)
            and f"web:{r['url']}" not in known_keys and title_ok(r["title"])]
    if not hits:
        return []
    pages = {p["url"]: p.get("raw_content") or "" for p in
             tavily("extract", {"urls": [h["url"] for h in hits[:5]]}).get("results", [])}
    jobs = [{
        "key": f"web:{h['url']}", "company": company, "title": h["title"].split("|")[0].strip(),
        "location": "India", "url": h["url"], "posted": date.today().isoformat(), "source": "Web (Tavily)",
        "description": (pages.get(h["url"]) or h.get("content", ""))[:15000],
    } for h in hits[:5]]
    return [j for j in jobs if len(j["description"]) >= 500]   # too little text to score fairly
