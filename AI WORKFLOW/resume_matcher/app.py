"""Resume ↔ Job Description Matcher + Cover Letter Writer.

An AI WORKFLOW (fixed steps, the code decides the order):
    resume + JD → extract text → Mistral extracts structured profiles
        → Mistral embeddings similarity → Mistral skill-gap analysis
        → score (Python) → Mistral improves bullets → Mistral writes cover letter

Run:  streamlit run "AI WORKFLOW/resume_matcher/app.py"
"""

import html
import os
import re
import time
from pathlib import Path

import numpy as np
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from pydantic import BaseModel, Field
from pypdf import PdfReader


# ── Setup ────────────────────────────────────────────────────────────────────
def load_env():
    """Load the nearest .env file above this script (holds MISTRAL_API_KEY)."""
    for folder in Path(__file__).resolve().parents:
        if (folder / ".env").exists():
            load_dotenv(folder / ".env")
            return


load_env()

# models available on the current Mistral subscription (first = default).
# mistral-small/medium/large return 429 / 403 on this plan.
MODELS = ["ministral-8b-latest", "ministral-14b-latest", "ministral-3b-latest"]
EMBED_CHARS = 16000          # keep each text well under mistral-embed's 8k-token limit


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
    education: list[str]
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


# ── Step 1: resume file → text ───────────────────────────────────────────────
def read_resume(uploaded_file) -> str:
    if uploaded_file.name.lower().endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    return uploaded_file.read().decode("utf-8", errors="ignore").strip()


# ── Step 2: text → structured profiles ───────────────────────────────────────
def extract_resume(llm, resume_text) -> ResumeProfile:
    system = ("Extract the candidate's details from this resume. Copy facts exactly; "
              "do not guess or invent anything that is not written.")
    structured = llm.with_structured_output(ResumeProfile)
    return call_with_retry(structured.invoke, [SystemMessage(system), HumanMessage(resume_text)])


def extract_job(llm, jd_text) -> JobProfile:
    system = ("Extract the job requirements from this job description. Split skills into "
              "required (must-have) and nice-to-have. Keep skill names short, e.g. 'Python', 'SQL'.")
    structured = llm.with_structured_output(JobProfile)
    return call_with_retry(structured.invoke, [SystemMessage(system), HumanMessage(jd_text)])


# ── Step 3: semantic similarity with Mistral embeddings ──────────────────────
def semantic_similarity(resume_text, jd_text) -> float:
    emb = MistralAIEmbeddings(model="mistral-embed")
    a, b = call_with_retry(emb.embed_documents, [resume_text[:EMBED_CHARS], jd_text[:EMBED_CHARS]])
    a, b = np.array(a), np.array(b)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))     # cosine similarity


# ── Step 4: skill-gap analysis ───────────────────────────────────────────────
def analyse_gap(llm, resume: ResumeProfile, job: JobProfile) -> SkillGap:
    system = (
        "Compare the candidate's skills with the job's skills.\n"
        "Rules:\n"
        "- Put EVERY required skill in exactly one of matched_required / missing_required, "
        "and EVERY nice-to-have skill in exactly one of matched_nice_to_have / missing_nice_to_have.\n"
        "- Use the job's skill names exactly as written.\n"
        "- Count a skill as matched if the resume shows it, an equivalent, or a clearly "
        "related tool (e.g. 'PostgreSQL' matches 'SQL', 'PyTorch' matches 'deep learning').\n"
        "- Be honest; do not mark a skill as matched without evidence."
    )
    user = (f"CANDIDATE:\n{resume.model_dump_json(indent=2)}\n\n"
            f"JOB:\n{job.model_dump_json(indent=2)}")
    structured = llm.with_structured_output(SkillGap)
    return call_with_retry(structured.invoke, [SystemMessage(system), HumanMessage(user)])


# ── Step 5: score (plain Python, no LLM) ─────────────────────────────────────
def ratio(matched, missing):
    total = len(matched) + len(missing)
    return len(matched) / total if total else None


def compute_scores(gap: SkillGap, similarity: float) -> dict:
    required = ratio(gap.matched_required, gap.missing_required)
    nice = ratio(gap.matched_nice_to_have, gap.missing_nice_to_have)
    # mistral-embed cosine is ~0.6 for unrelated text and ~0.9 for very close text,
    # so stretch that range to 0–1
    semantic = float(np.clip((similarity - 0.60) / 0.30, 0, 1))

    required = 0.0 if required is None else required
    if nice is None:                               # JD lists no nice-to-haves
        overall = 0.6 * required + 0.4 * semantic
    else:
        overall = 0.5 * required + 0.2 * nice + 0.3 * semantic
    return {"overall": overall, "required": required, "nice": nice, "semantic": semantic}


# ── Step 5b: interview chance estimate (plain Python, no LLM) ────────────────
def interview_chance(scores: dict, resume: ResumeProfile, job: JobProfile, gap: SkillGap) -> dict:
    """Estimate (0–100) of how strong the profile looks for an interview.

    A transparent heuristic based on the match analysis — NOT a prediction of how
    the candidate will actually perform in the interview.
    """
    # experience fit: 1.0 if the minimum is met, otherwise the fraction met
    if job.min_years_experience <= 0:
        experience = 1.0
    else:
        experience = min(resume.years_of_experience / job.min_years_experience, 1.0)

    nice = scores["nice"] if scores["nice"] is not None else scores["required"]
    percent = 100 * (0.45 * scores["required"]      # must-have skills matter most
                     + 0.10 * nice                  # nice-to-haves give a small boost
                     + 0.20 * scores["semantic"]    # overall profile closeness
                     + 0.25 * experience)           # years of experience vs. minimum

    # hard caps: big gaps in the basics limit the chance however good the rest is
    caps = []
    if experience < 0.5:
        percent = min(percent, 40)
        caps.append("less than half the required experience (capped at 40%)")
    if scores["required"] < 0.5:
        percent = min(percent, 45)
        caps.append("fewer than half the required skills (capped at 45%)")

    percent = round(percent)
    band = "High" if percent >= 75 else "Moderate" if percent >= 50 else "Low"
    return {
        "percent": percent,
        "band": band,
        "factors": {
            "Required skills (45%)": scores["required"],
            "Nice-to-have skills (10%)": nice,
            "Profile similarity (20%)": scores["semantic"],
            "Experience fit (25%)": experience,
        },
        "caps": caps,
        "prepare": gap.missing_required,
    }


# ── Step 6: improve resume bullets ───────────────────────────────────────────
def suggest_improvements(llm, resume, job, gap) -> ResumeSuggestions:
    system = (
        "You are a professional resume coach. Rewrite up to 5 of the candidate's experience "
        "bullets so they better match the job: strong action verbs, measurable impact, and the "
        "job's keywords where TRUE. Never invent skills, tools, numbers or experience the "
        "candidate does not have — if a number is missing, use a placeholder like [X]%."
    )
    user = (f"CANDIDATE:\n{resume.model_dump_json(indent=2)}\n\n"
            f"JOB:\n{job.model_dump_json(indent=2)}\n\n"
            f"SKILL GAP:\n{gap.model_dump_json(indent=2)}")
    structured = llm.with_structured_output(ResumeSuggestions)
    return call_with_retry(structured.invoke, [SystemMessage(system), HumanMessage(user)])


# ── Step 7: cover letter ─────────────────────────────────────────────────────
LENGTHS = {"Short": "150-200 words", "Medium": "250-320 words", "Long": "350-450 words"}


def write_cover_letter(llm, resume, job, gap, tone, length) -> str:
    system = (
        f"Write a {tone.lower()} cover letter of {LENGTHS[length]} for this candidate and job.\n"
        "- Address it to the hiring manager at the company (use 'Hiring Manager' if no name).\n"
        "- Open with the specific role and genuine interest.\n"
        "- Connect 2-3 of the candidate's real achievements to the job's responsibilities.\n"
        "- Mention matched skills naturally; do NOT claim missing skills — you may say the "
        "candidate is keen to grow in one of them.\n"
        "- Use ONLY facts from the candidate's profile. Never invent experience.\n"
        "- Do NOT write any number or percentage unless it appears in the candidate's profile.\n"
        "- End with a call to action and sign off with the candidate's name.\n"
        "Return only the letter as plain text — no Markdown, no ** bold."
    )
    user = (f"CANDIDATE:\n{resume.model_dump_json(indent=2)}\n\n"
            f"JOB:\n{job.model_dump_json(indent=2)}\n\n"
            f"MATCHED SKILLS: {gap.matched_required + gap.matched_nice_to_have}\n"
            f"MISSING SKILLS: {gap.missing_required}")
    reply = call_with_retry(llm.invoke, [SystemMessage(system), HumanMessage(user)])
    return reply.content.replace("**", "").strip()


def invented_numbers(letter: str, *sources: str) -> list[str]:
    """Numbers in the letter that appear in neither the resume nor the JD.

    A cheap guardrail: LLMs sometimes make up metrics like "reduced costs by 30%".
    """
    source_text = " ".join(sources)
    found = re.findall(r"\d[\d,.]*%?", letter)
    return sorted({n.rstrip(".,") for n in found if n.rstrip(".,%") not in source_text})


# ── The workflow ─────────────────────────────────────────────────────────────
def run_workflow(resume_text, jd_text, model, tone, length):
    """The fixed AI workflow. Each step always runs in the same order."""
    llm = ChatMistralAI(model=model, temperature=0.2)
    with st.status("Analysing…", expanded=True) as status:
        try:
            st.write("1️⃣ Extracting your resume details")
            resume = extract_resume(llm, resume_text)
            st.write("2️⃣ Extracting the job requirements")
            job = extract_job(llm, jd_text)
            st.write("3️⃣ Measuring semantic similarity (Mistral embeddings)")
            similarity = semantic_similarity(resume_text, jd_text)
            st.write("4️⃣ Finding matched and missing skills")
            gap = analyse_gap(llm, resume, job)
            st.write("5️⃣ Calculating the match score and interview chance")
            scores = compute_scores(gap, similarity)
            chance = interview_chance(scores, resume, job, gap)
            st.write("6️⃣ Suggesting resume improvements")
            suggestions = suggest_improvements(llm, resume, job, gap)
            st.write("7️⃣ Writing the cover letter")
            letter = write_cover_letter(llm, resume, job, gap, tone, length)
        except Exception as e:
            status.update(label="Mistral API error", state="error")
            st.error(f"{type(e).__name__}: {e}\n\nIf this is a 429 / 403 error, pick a "
                     "different model in the sidebar or wait a minute and try again.")
            st.stop()
        status.update(label="Done!", state="complete", expanded=False)

    return {"resume": resume, "job": job, "similarity": similarity, "gap": gap,
            "scores": scores, "chance": chance, "suggestions": suggestions, "letter": letter,
            "resume_text": resume_text, "jd_text": jd_text}


# ── UI helpers ───────────────────────────────────────────────────────────────
def chips(items, color):
    if not items:
        return "<i>none</i>"
    return " ".join(
        f"<span style='background:{color};color:white;padding:3px 10px;border-radius:12px;"
        f"margin:2px;display:inline-block;font-size:0.85rem'>{html.escape(s)}</span>"
        for s in items
    )


def build_report(r) -> str:
    s, g, job = r["scores"], r["gap"], r["job"]
    lines = [
        f"# Match report — {job.job_title} at {job.company}",
        f"Interview chance (estimate): {r['chance']['percent']}/100 ({r['chance']['band']})",
        f"Overall match: {s['overall'] * 100:.0f}%",
        f"Required skills: {len(g.matched_required)}/{len(g.matched_required) + len(g.missing_required)}",
        f"Semantic similarity: {r['similarity']:.3f}",
        "", "## Assessment", g.summary,
        "", "## Missing required skills", *[f"- {x}" for x in g.missing_required],
        "", "## Improved bullets",
    ]
    for b in r["suggestions"].rewrites:
        lines += [f"- Before: {b.original}", f"  After:  {b.improved}", f"  Why:    {b.reason}"]
    lines += ["", "## Cover letter", r["letter"]]
    return "\n".join(lines)


# ── UI ───────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Resume Matcher", page_icon="📄", layout="wide")
    st.title("📄 Resume ↔ Job Matcher + Cover Letter Writer")
    st.caption("See how well your resume fits a job, what's missing, and get a tailored cover letter. Powered by Mistral.")

    with st.sidebar:
        st.header("Settings")
        model = st.selectbox("Mistral model", MODELS)
        tone = st.selectbox("Cover letter tone", ["Professional", "Enthusiastic", "Concise", "Friendly"])
        length = st.radio("Cover letter length", list(LENGTHS), index=1, horizontal=True)
        st.divider()
        st.markdown(
            "**Workflow steps**\n\n"
            "1. Extract resume\n2. Extract job\n3. Embedding similarity\n"
            "4. Skill gap\n5. Score + interview chance\n6. Improve bullets\n7. Cover letter"
        )
        st.caption("Your resume is sent to the Mistral API for processing.")

    if not os.getenv("MISTRAL_API_KEY"):
        st.error("MISTRAL_API_KEY not found. Add it to your .env file.")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your resume")
        uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])
        pasted_resume = st.text_area("…or paste resume text", height=200)
    with col2:
        st.subheader("Job description")
        jd_text = st.text_area("Paste the job description", height=300)

    resume_text = read_resume(uploaded) if uploaded else pasted_resume.strip()

    if st.button("Analyse match", type="primary", disabled=not (resume_text and jd_text.strip())):
        if len(resume_text) < 100:
            st.error("Couldn't read enough text from the resume. If it's a scanned PDF, paste the text instead.")
            st.stop()
        st.session_state.result = run_workflow(resume_text, jd_text.strip(), model, tone, length)

    r = st.session_state.get("result")
    if not r:
        return

    s, g, resume, job = r["scores"], r["gap"], r["resume"], r["job"]
    st.divider()
    st.subheader(f"{job.job_title} · {job.company}")

    c = r["chance"]
    m0, m1, m2, m3, m4 = st.columns(5)
    m0.metric("Interview chance", f"{c['percent']} / 100", c["band"],
              delta_color="normal" if c["band"] == "High" else "off" if c["band"] == "Moderate" else "inverse",
              help="Estimate of how strong your profile looks for this job — not a prediction "
                   "of how you will perform in the interview itself.")
    m1.metric("Overall match", f"{s['overall'] * 100:.0f}%")
    m2.metric("Required skills",
              f"{len(g.matched_required)} / {len(g.matched_required) + len(g.missing_required)}")
    m3.metric("Semantic similarity", f"{s['semantic'] * 100:.0f}%", help=f"raw cosine = {r['similarity']:.3f}")
    exp_ok = resume.years_of_experience >= job.min_years_experience
    m4.metric("Experience", f"{resume.years_of_experience:g} yrs",
              f"{'meets' if exp_ok else 'below'} {job.min_years_experience:g}+ required",
              delta_color="normal" if exp_ok else "inverse")
    st.progress(s["overall"])
    st.info(g.summary)

    with st.expander(f"🎯 Interview chance: {c['percent']}/100 ({c['band']}) — how it's calculated"):
        for name, value in c["factors"].items():
            st.write(f"{name}: **{value * 100:.0f}%**")
            st.progress(value)
        for cap in c["caps"]:
            st.warning(f"Limited by: {cap}")
        if c["prepare"]:
            st.markdown("**To raise your chance, learn or show evidence of:** " + ", ".join(c["prepare"]))
        st.caption("This estimates how well your profile matches the job on paper. Actually "
                   "clearing the interview also depends on your preparation, communication "
                   "and the interviewers — no tool can predict that.")

    tab_gap, tab_bullets, tab_letter, tab_data = st.tabs(
        ["🧩 Skills gap", "✍️ Improve resume", "💌 Cover letter", "🔍 Extracted data"]
    )

    with tab_gap:
        st.markdown("**✅ Matched required skills**")
        st.markdown(chips(g.matched_required, "#16a34a"), unsafe_allow_html=True)
        st.markdown("**❌ Missing required skills**")
        st.markdown(chips(g.missing_required, "#dc2626"), unsafe_allow_html=True)
        st.markdown("**👍 Matched nice-to-have**")
        st.markdown(chips(g.matched_nice_to_have, "#2563eb"), unsafe_allow_html=True)
        st.markdown("**➕ Missing nice-to-have**")
        st.markdown(chips(g.missing_nice_to_have, "#6b7280"), unsafe_allow_html=True)

    with tab_bullets:
        sug = r["suggestions"]
        for b in sug.rewrites:
            st.markdown(f"**Before:** {b.original}")
            st.success(f"**After:** {b.improved}")
            st.caption(f"Why: {b.reason}")
            st.divider()
        if sug.skills_to_highlight:
            st.markdown("**Skills to put front and centre:** " + ", ".join(sug.skills_to_highlight))
        for tip in sug.tips:
            st.markdown(f"- {tip}")

    with tab_letter:
        new_tone = st.selectbox("Tone", ["Professional", "Enthusiastic", "Concise", "Friendly"], key="re_tone")
        new_length = st.radio("Length", list(LENGTHS), index=1, horizontal=True, key="re_length")
        if st.button("🔄 Rewrite cover letter"):
            with st.spinner("Writing…"):
                llm = ChatMistralAI(model=model, temperature=0.4)
                r["letter"] = write_cover_letter(llm, resume, job, g, new_tone, new_length)
        suspicious = invented_numbers(r["letter"], r["resume_text"], r["jd_text"])
        if suspicious:
            st.warning("⚠️ These numbers are not in your resume or the job description — "
                       f"check or remove them before sending: {', '.join(suspicious)}")
        st.text_area("Cover letter", r["letter"], height=420)
        st.download_button("⬇️ Download cover letter (.txt)", r["letter"], file_name="cover_letter.txt")

    with tab_data:
        c1, c2 = st.columns(2)
        c1.markdown("**Resume (as Mistral read it)**")
        c1.json(resume.model_dump())
        c2.markdown("**Job (as Mistral read it)**")
        c2.json(job.model_dump())

    st.download_button("⬇️ Download full report (.md)", build_report(r), file_name="match_report.md")


if __name__ == "__main__":
    main()
