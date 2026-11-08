"""Decide which jobs are really for freshers (0–2 years) and tag their fields.

Cheap rules first; Mistral is asked only about jobs the rules can't decide.
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


def rule_check(job) -> str:
    """'yes', 'no' or 'unsure'. Also sets job['fields'] and job['min_years']."""
    job["fields"] = tag_fields(job["title"])
    if not job["fields"]:
        return "no"
    desc = job.get("description") or ""
    years = min_years(desc)
    job["min_years"] = years
    fresher_text = bool(config.FRESHER_TEXT.search(desc))
    if years is not None and years >= 3 and not fresher_text:
        return "no"
    if config.FRESHER_TITLE.search(job["title"]) or fresher_text or (years is not None and years <= 2):
        if job["min_years"] is None:
            job["min_years"] = 0
        return "yes"
    return "unsure"


def llm_check(jobs, log=print):
    """Ask Mistral about unclear jobs in one batch. Returns the jobs it says are for freshers."""
    key = os.environ.get("MISTRAL_API_KEY")
    if not key or not jobs:
        return []
    jobs = jobs[: config.MAX_LLM_CHECKS]
    items = [{"i": i, "title": j["title"], "company": j["company"],
              "description": re.sub(r"\s+", " ", j.get("description") or "")[:1200]} for i, j in enumerate(jobs)]
    prompt = (
        "For each job below, decide if a fresher (0–2 years of experience, including interns and recent "
        "graduates) is a realistic candidate. Use only the title and description. Answer JSON: "
        '{"results": [{"i": <index>, "fresher": true|false, "min_years": <int or null>}]}\n\n'
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
        i = res.get("i")
        if isinstance(i, int) and 0 <= i < len(jobs) and res.get("fresher") is True:
            jobs[i]["min_years"] = res.get("min_years") if isinstance(res.get("min_years"), int) else 0
            keep.append(jobs[i])
    return keep


def fresher_jobs(candidates, log=print):
    yes, unsure = [], []
    for j in candidates:
        verdict = rule_check(j)
        (yes if verdict == "yes" else unsure if verdict == "unsure" else []).append(j)
    from_llm = llm_check(unsure, log)
    log(f"Fresher filter: {len(yes)} by rules, {len(from_llm)}/{min(len(unsure), config.MAX_LLM_CHECKS)} unclear ones confirmed by Mistral")
    return yes + from_llm
