"""Put each job in an experience section (0–2, 2–4, 4–6, 6+ years) and tag its fields.

Cheap rules first; Mistral is asked only about jobs the rules can't place.
"""

import json
import os
import re

import requests

import config


def tag_fields(title: str) -> list[str]:
    return [k for k, p in config.FIELD_PATTERNS.items() if p.search(title)]


def min_years(description: str):
    """Smallest 'N years' experience requirement in the description, or None if it doesn't say."""
    found = []
    for m in config.YEARS.finditer(description or ""):
        after = description[m.end(): m.end() + 60].lower()
        before = description[max(0, m.start() - 40): m.start()].lower()
        if "experience" in after or "exp" in after or "experience" in before:
            n = int(m.group(1))
            if n <= 15:
                found.append(n)
    return min(found) if found else None


def band_for_years(years: int) -> str:
    for key, (_, _, _, lo, hi) in config.EXPERIENCE.items():
        if lo <= years <= hi:
            return key
    return "6+"


def band_from_title(title: str):
    """Experience section implied by the title alone, or None."""
    if config.TITLE_6_PLUS.search(title):
        return "6+"
    if config.TITLE_4_6.search(title):
        return "4-6"
    if config.TITLE_2_4.search(title):
        return "2-4"
    if config.FRESHER_TITLE.search(title):
        return "0-2"
    return None


def rule_check(job) -> str:
    """'yes', 'no' or 'unsure'. Sets job['fields'], job['min_years'] and job['experience']."""
    job["fields"] = tag_fields(job["title"])
    if not job["fields"]:
        return "no"
    desc = job.get("description") or ""
    years = min_years(desc)
    if years is None and config.FRESHER_TEXT.search(desc):
        years = 0
    job["min_years"] = years
    title_band = band_from_title(job["title"])
    if years is not None:
        job["experience"] = at_least_title(band_for_years(years), title_band)
        return "yes"
    if title_band:
        job["experience"] = title_band
        return "yes"
    return "unsure"


ORDER = list(config.EXPERIENCE)


def at_least_title(band, title_band):
    """Descriptions often mention a small number ('2+ years of Python') on senior roles, so a Senior / Lead /
    Principal / Manager title sets the lowest section the job can go in. Fresher titles never pull a job down."""
    if title_band and title_band != "0-2" and ORDER.index(title_band) > ORDER.index(band):
        return title_band
    return band


def llm_check(jobs, log=print):
    """Ask Mistral for the minimum years of unclear jobs in one batch. Returns the jobs it could place."""
    key = os.environ.get("MISTRAL_API_KEY")
    if not key or not jobs:
        return []
    jobs = jobs[: config.MAX_LLM_CHECKS]
    items = [{"i": i, "title": j["title"], "company": j["company"],
              "description": re.sub(r"\s+", " ", j.get("description") or "")[:1200]} for i, j in enumerate(jobs)]
    prompt = (
        "For each job below, estimate the MINIMUM years of professional experience a realistic candidate needs "
        "(0 for interns, trainees and new graduates). Use only the title and description. If you really can't "
        'tell, use null. Answer JSON: {"results": [{"i": <index>, "min_years": <int or null>}]}\n\n'
        + json.dumps(items, ensure_ascii=False))
    try:
        r = requests.post("https://api.mistral.ai/v1/chat/completions", timeout=120,
                          headers={"Authorization": f"Bearer {key}"},
                          json={"model": config.MODEL, "temperature": 0, "response_format": {"type": "json_object"},
                                "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status()
        data = json.loads(r.json()["choices"][0]["message"]["content"])
        results = data if isinstance(data, list) else data.get("results", [])   # small models sometimes skip the wrapper
    except Exception as e:
        log(f"Mistral check skipped: {e}")
        return []
    keep = []
    for res in results:
        if not isinstance(res, dict):
            continue
        i, years = res.get("i"), res.get("min_years")
        if isinstance(i, int) and 0 <= i < len(jobs) and isinstance(years, int) and 0 <= years <= 30:
            jobs[i]["min_years"] = years
            jobs[i]["experience"] = at_least_title(band_for_years(years), band_from_title(jobs[i]["title"]))
            keep.append(jobs[i])
    return keep


def classify_jobs(candidates, log=print):
    """All candidates that fit one of our fields, each with job['experience'] set."""
    placed, unsure = [], []
    for j in candidates:
        verdict = rule_check(j)
        (placed if verdict == "yes" else unsure if verdict == "unsure" else []).append(j)
    from_llm = llm_check(unsure, log)
    jobs = placed + from_llm
    counts = {k: sum(1 for j in jobs if j["experience"] == k) for k in config.EXPERIENCE}
    log(f"Experience filter: {len(placed)} by rules, {len(from_llm)}/{min(len(unsure), config.MAX_LLM_CHECKS)} "
        f"unclear ones placed by Mistral · " + ", ".join(f"{config.EXPERIENCE[k][0]}: {n}" for k, n in counts.items()))
    return jobs
