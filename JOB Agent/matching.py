"""The LLM steps: read the resume, score each job against it, write application kits.

Scoring follows the Resume Matcher workflow (AI WORKFLOW/resume_matcher):
    JD → Mistral extracts JobProfile → Mistral embeddings similarity
       → Mistral skill-gap analysis → score + interview-chance (plain Python)
"""

import json
import re
import time

import numpy as np
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from pydantic import BaseModel, Field
from pypdf import PdfReader

import config

EMBED_CHARS = 16000          # keep each text well under mistral-embed's 8k-token limit


def llm(temperature=0.2):
    return ChatMistralAI(model=config.MODEL, temperature=temperature)


def call_with_retry(fn, *args, retries=6, **kwargs):
    """Retry on Mistral rate limits (HTTP 429) with exponential backoff."""
    delay = 2
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            msg = str(e).lower()
            if ("429" in msg or "rate limit" in msg) and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise


# ── Structured output schemas (Mistral fills these in) ───────────────────────
class ResumeProfile(BaseModel):
    name: str = Field(description="candidate's full name, or 'Unknown'")
    job_titles: list[str] = Field(description="job titles held, most recent first")
    years_of_experience: float = Field(description="total professional experience in years, 0 if unclear")
    skills: list[str] = Field(description="technical skills, tools, languages, frameworks and soft skills")
    projects: list[str] = Field(description="personal or professional project names with their tech stack")
    achievements: list[str] = Field(description="key accomplishments, ideally with numbers")
    experience_bullets: list[str] = Field(description="the experience bullet points, copied exactly as written")


class JobProfile(BaseModel):
    job_title: str
    company: str = Field(description="company name, or 'Unknown'")
    required_skills: list[str]
    nice_to_have_skills: list[str]
    min_years_experience: float = Field(description="minimum years of experience required, 0 if not stated")
    responsibilities: list[str]


class SkillGap(BaseModel):
    matched_required: list[str]
    missing_required: list[str]
    matched_nice_to_have: list[str]
    missing_nice_to_have: list[str]
    summary: str = Field(description="2-3 sentence honest assessment of the fit")


class BulletRewrite(BaseModel):
    original: str
    improved: str
    reason: str


class ResumeSuggestions(BaseModel):
    rewrites: list[BulletRewrite]
    skills_to_highlight: list[str] = Field(description="skills the candidate HAS that this job values most")
    tips: list[str] = Field(description="other short, practical tips for this application")


class NewGCC(BaseModel):
    company: str = Field(description="the company opening or expanding the centre, e.g. 'Lowe's'")
    city: str = Field(description="Indian city of the centre, or 'India' if not stated")
    summary: str = Field(description="one line: what was announced, e.g. 'new 1,000-seat tech centre, hiring engineers'")
    article_number: int = Field(description="number of the article this came from")


class GCCList(BaseModel):
    gccs: list[NewGCC]


class JobFacts(BaseModel):
    salary_range: str = Field(description="yearly salary in India like '₹18–28 LPA', or 'Unknown'")
    salary_source: str = Field(description="'job posting' if the JD states it, else the site the estimate "
                                           "comes from, e.g. 'AmbitionBox estimate'; 'Unknown' if none")
    work_mode: str = Field(description="'Hybrid', 'Onsite', 'Remote' or 'Not stated'")
    experience: str = Field(description="experience required as written, e.g. '3+ yrs' or '5–8 yrs'; 'Not stated'")


class CompanyFacts(BaseModel):
    india_since: str = Field(description="year the company started operating in India, e.g. '2004', or 'Unknown'")
    india_cities: list[str] = Field(description="Indian cities where it has offices/centres, max 4")
    india_headcount: str = Field(description="approx. employees in India, ONLY a short number like '~10,000' "
                                             "(no explanation), or 'Unknown'")
    about: str = Field(description="one short line: what its India centre does")


# ── Resume ───────────────────────────────────────────────────────────────────
def resume_text() -> str:
    reader = PdfReader(config.RESUME_PATH)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return re.sub(r"\s+", " ", text).strip()        # this PDF puts a newline between every word


def resume_profile(text: str) -> ResumeProfile:
    """Extract once and cache; re-extract only when the resume file changes."""
    cache = config.DATA_DIR / "resume_profile.json"
    stamp = config.RESUME_PATH.stat().st_mtime
    if cache.exists():
        saved = json.loads(cache.read_text(encoding="utf-8"))
        if saved.get("mtime") == stamp:
            return ResumeProfile.model_validate(saved["profile"])
    system = ("Extract the candidate's details from this resume. Copy facts exactly; "
              "do not guess or invent anything that is not written.")
    profile = call_with_retry(llm().with_structured_output(ResumeProfile).invoke,
                              [SystemMessage(system), HumanMessage(text)])
    config.DATA_DIR.mkdir(exist_ok=True)
    cache.write_text(json.dumps({"mtime": stamp, "profile": profile.model_dump()}, indent=2), encoding="utf-8")
    return profile


# ── Scoring one job ──────────────────────────────────────────────────────────
def extract_job(model, jd_text) -> JobProfile:
    system = ("Extract the job requirements from this job description. Split skills into "
              "required (must-have) and nice-to-have. Keep skill names short, e.g. 'Python', 'SQL'.")
    return call_with_retry(model.with_structured_output(JobProfile).invoke,
                           [SystemMessage(system), HumanMessage(jd_text)])


def semantic_similarity(text_a, text_b) -> float:
    emb = MistralAIEmbeddings(model="mistral-embed")
    a, b = call_with_retry(emb.embed_documents, [text_a[:EMBED_CHARS], text_b[:EMBED_CHARS]])
    a, b = np.array(a), np.array(b)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))     # cosine similarity


def analyse_gap(model, resume: ResumeProfile, job: JobProfile) -> SkillGap:
    system = (
        "Compare the candidate's skills and projects with the job's skills.\n"
        "Rules:\n"
        "- Put EVERY required skill in exactly one of matched_required / missing_required, "
        "and EVERY nice-to-have skill in exactly one of matched_nice_to_have / missing_nice_to_have.\n"
        "- Use the job's skill names exactly as written.\n"
        "- Count a skill as matched if the resume shows it, an equivalent, or a clearly "
        "related tool (e.g. 'PostgreSQL' matches 'SQL', 'PyTorch' matches 'deep learning').\n"
        "- Be honest; do not mark a skill as matched without evidence."
    )
    user = f"CANDIDATE:\n{resume.model_dump_json(indent=2)}\n\nJOB:\n{job.model_dump_json(indent=2)}"
    return call_with_retry(model.with_structured_output(SkillGap).invoke,
                           [SystemMessage(system), HumanMessage(user)])


def ratio(matched, missing):
    total = len(matched) + len(missing)
    return len(matched) / total if total else None


def fit_scores(gap: SkillGap, similarity: float, resume: ResumeProfile, job: JobProfile) -> dict:
    """Overall match % and interview-chance estimate (0–100), plain Python — see AI WORKFLOW/readme.txt."""
    required = ratio(gap.matched_required, gap.missing_required) or 0.0
    nice = ratio(gap.matched_nice_to_have, gap.missing_nice_to_have)
    # mistral-embed cosine is ~0.6 for unrelated text and ~0.9 for very close text
    semantic = float(np.clip((similarity - 0.60) / 0.30, 0, 1))
    overall = (0.6 * required + 0.4 * semantic if nice is None
               else 0.5 * required + 0.2 * nice + 0.3 * semantic)

    experience = (1.0 if job.min_years_experience <= 0
                  else min(resume.years_of_experience / job.min_years_experience, 1.0))
    nice_or_req = nice if nice is not None else required
    chance = 100 * (0.45 * required + 0.10 * nice_or_req + 0.20 * semantic + 0.25 * experience)
    if experience < 0.5:
        chance = min(chance, 40)
    if required < 0.5:
        chance = min(chance, 45)
    return {"match": round(overall * 100), "fit": round(chance)}


def score_job(resume_txt: str, resume: ResumeProfile, job: dict) -> dict:
    """Run the scoring workflow on one job dict; returns the fields to store."""
    model = llm()
    jd = f"{job['title']} at {job['company']} ({job['location']})\n\n{job['description']}"
    job_p = extract_job(model, jd)
    similarity = semantic_similarity(resume_txt, jd)
    gap = analyse_gap(model, resume, job_p)
    return {**fit_scores(gap, similarity, resume, job_p), "summary": gap.summary,
            "job_profile": job_p.model_dump_json(), "gap": gap.model_dump_json()}


# ── Application kit (only for jobs you approve) ──────────────────────────────
def suggest_improvements(model, resume, job, gap) -> ResumeSuggestions:
    system = (
        "You are a professional resume coach. Rewrite up to 5 of the candidate's experience "
        "bullets so they better match the job: strong action verbs, measurable impact, and the "
        "job's keywords where TRUE. Never invent skills, tools, numbers or experience the "
        "candidate does not have — if a number is missing, use a placeholder like [X]%."
    )
    user = (f"CANDIDATE:\n{resume.model_dump_json(indent=2)}\n\nJOB:\n{job.model_dump_json(indent=2)}\n\n"
            f"SKILL GAP:\n{gap.model_dump_json(indent=2)}")
    return call_with_retry(model.with_structured_output(ResumeSuggestions).invoke,
                           [SystemMessage(system), HumanMessage(user)])


def write_cover_letter(model, resume, job, gap) -> str:
    system = (
        "Write a professional cover letter of 250-320 words for this candidate and job.\n"
        "- Address it to the hiring manager at the company (use 'Hiring Manager' if no name).\n"
        "- Open with the specific role and genuine interest.\n"
        "- Connect 2-3 of the candidate's real achievements or projects to the job's responsibilities.\n"
        "- Mention matched skills naturally; do NOT claim missing skills — you may say the "
        "candidate is keen to grow in one of them.\n"
        "- Use ONLY facts from the candidate's profile. Never invent experience.\n"
        "- Do NOT write any number or percentage unless it appears in the candidate's profile.\n"
        "- End with a call to action and sign off with the candidate's name.\n"
        "Return only the letter as plain text — no Markdown, no ** bold."
    )
    user = (f"CANDIDATE:\n{resume.model_dump_json(indent=2)}\n\nJOB:\n{job.model_dump_json(indent=2)}\n\n"
            f"MATCHED SKILLS: {gap.matched_required + gap.matched_nice_to_have}\n"
            f"MISSING SKILLS: {gap.missing_required}")
    return call_with_retry(model.invoke, [SystemMessage(system), HumanMessage(user)]).content.replace("**", "").strip()


def invented_numbers(letter: str, *sources: str) -> list[str]:
    """Numbers in the letter that appear in neither the resume nor the JD (LLMs sometimes make up metrics)."""
    source_text = " ".join(sources)
    found = re.findall(r"\d[\d,.]*%?", letter)
    return sorted({n.rstrip(".,") for n in found if n.rstrip(".,%") not in source_text})


def application_kit(resume_txt: str, resume: ResumeProfile, row: dict) -> dict:
    job_p = JobProfile.model_validate_json(row["job_profile"])
    gap = SkillGap.model_validate_json(row["gap"])
    letter = write_cover_letter(llm(0.4), resume, job_p, gap)
    tips = suggest_improvements(llm(), resume, job_p, gap)
    return {"letter": letter, "tips": tips.model_dump_json(),
            "warnings": json.dumps(invented_numbers(letter, resume_txt, row["description"]))}


# ── Extra facts for the Telegram cards (grounded in search results) ──────────
def snippets_text(results) -> str:
    return "\n\n".join(f"[{r['url']}]\n{r.get('content', '')[:1200]}" for r in results)


def job_facts(job: dict, salary_results: list[dict]) -> JobFacts:
    system = (
        "Fill in facts about this job in India.\n"
        "- salary_range: if the JOB DESCRIPTION states a salary, use it with source 'job posting'. Otherwise "
        "use the SALARY PAGES, but ONLY a figure given in Indian rupees (₹, INR, lakhs, LPA) for this company "
        "and the same role and seniority. NEVER convert from USD or any other currency. Copy the numbers "
        "exactly as written, formatted like '₹18–28 LPA' with no explanation. Source = site name + ' estimate'. "
        "If there is no such rupee figure, write 'Unknown'.\n"
        "- work_mode and experience: only from the job description."
    )
    user = (f"JOB: {job['title']} at {job['company']} ({job['location']})\n\n"
            f"JOB DESCRIPTION:\n{job['description'][:8000]}\n\nSALARY PAGES:\n{snippets_text(salary_results)}")
    facts = call_with_retry(llm(0).with_structured_output(JobFacts).invoke,
                            [SystemMessage(system), HumanMessage(user)])
    # guardrail: every number in the salary must appear in the JD or salary pages, and it must be in rupees
    sources_text = job["description"] + snippets_text(salary_results)
    numbers = re.findall(r"\d+(?:\.\d+)?", facts.salary_range)
    if (not numbers or "₹" not in facts.salary_range and "LPA" not in facts.salary_range
            or any(n not in sources_text for n in numbers) or len(facts.salary_range) > 30):
        facts.salary_range, facts.salary_source = "Unknown", "Unknown"
    return facts


def company_facts(company: str, results: list[dict]) -> CompanyFacts:
    system = (f"From these search results, give facts about {company}'s presence in INDIA only. "
              "Use only what the results say; write 'Unknown' instead of guessing.")
    return call_with_retry(llm(0).with_structured_output(CompanyFacts).invoke,
                           [SystemMessage(system), HumanMessage(snippets_text(results))])


# ── New GCCs from news ───────────────────────────────────────────────────────
def extract_gccs(articles: list[dict]) -> list[NewGCC]:
    if not articles:
        return []
    system = (
        "From these news articles, list companies that are OPENING a new Global Capability Centre (GCC) "
        "or significantly EXPANDING one in India. Skip consulting/research firms that only write about "
        "GCCs, staffing firms, and articles about the GCC industry in general. One entry per company. "
        "Use the company's common name. Return an empty list if none qualify."
    )
    text = "\n\n".join(f"[{i}] {a['title']}\n{a.get('content', '')[:1500]}" for i, a in enumerate(articles))
    return call_with_retry(llm(0).with_structured_output(GCCList).invoke,
                           [SystemMessage(system), HumanMessage(text)]).gccs
