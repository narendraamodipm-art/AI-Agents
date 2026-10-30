"""YouTube Video → Study Notes Generator.

An AI WORKFLOW (fixed steps, the code decides the order):
    URL → video id → transcript → chunks → Mistral notes per chunk
        → Mistral combines into study notes → Mistral makes flashcards + quiz

Run:  streamlit run "AI WORKFLOW/youtube_notes/app.py"
"""

import csv
import io
import os
import re
import time
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mistralai import ChatMistralAI
from pydantic import BaseModel, Field
from youtube_transcript_api import NoTranscriptFound, RequestBlocked, YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig


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
CHUNK_CHARS = 12000          # transcript characters sent to Mistral per call


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
class Flashcard(BaseModel):
    question: str
    answer: str


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(description="exactly 4 answer options")
    correct_index: int = Field(description="index (0-3) of the correct option")
    explanation: str = Field(description="one sentence on why the answer is correct")


class StudyMaterial(BaseModel):
    flashcards: list[Flashcard]
    quiz: list[QuizQuestion]


# ── Step 1: URL → video id ───────────────────────────────────────────────────
def extract_video_id(url: str):
    url = url.strip()
    if re.fullmatch(r"[\w-]{11}", url):                     # already an id
        return url
    match = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([\w-]{11})", url)
    return match.group(1) if match else None


# ── Step 2: video id → transcript ────────────────────────────────────────────
def proxy_config():
    """YouTube blocks cloud-server IPs. Set a proxy in .env to get around it:
    WEBSHARE_PROXY_USERNAME + WEBSHARE_PROXY_PASSWORD (rotating residential), or
    PROXY_URL=http://user:pass@host:port (any HTTP proxy)."""
    if os.getenv("WEBSHARE_PROXY_USERNAME"):
        return WebshareProxyConfig(
            proxy_username=os.getenv("WEBSHARE_PROXY_USERNAME"),
            proxy_password=os.getenv("WEBSHARE_PROXY_PASSWORD"),
        )
    if os.getenv("PROXY_URL"):
        return GenericProxyConfig(http_url=os.getenv("PROXY_URL"),
                                  https_url=os.getenv("PROXY_URL"))
    return None


def fetch_via_relay(relay_url: str, video_id: str):
    """Ask relay.py (running on a home PC) for the transcript."""
    try:
        resp = requests.get(f"{relay_url.rstrip('/')}/transcript",
                            params={"video_id": video_id},
                            headers={"X-Relay-Token": os.getenv("RELAY_TOKEN", "")},
                            timeout=60)
    except requests.RequestException as e:
        raise RuntimeError(f"Relay not reachable — is relay.py and the tunnel running? ({e})")
    body = resp.json()
    if resp.status_code != 200:
        raise RuntimeError(f"Relay error: {body.get('error')}")
    return body["snippets"], body["language_code"]


@st.cache_data(show_spinner=False)
def fetch_transcript(video_id: str):
    """Return ([{start, text}, ...], language_code). Prefers English."""
    if os.getenv("TRANSCRIPT_RELAY_URL"):
        return fetch_via_relay(os.getenv("TRANSCRIPT_RELAY_URL"), video_id)
    api = YouTubeTranscriptApi(proxy_config=proxy_config())
    try:
        transcript = api.fetch(video_id, languages=["en", "en-US", "en-GB"])
    except NoTranscriptFound:
        # no English captions → take the first available language
        available = api.list(video_id)
        transcript = next(iter(available)).fetch()
    snippets = [{"start": s.start, "text": s.text} for s in transcript.snippets]
    return snippets, transcript.language_code


def parse_pasted_transcript(text: str):
    """Parse text copied from YouTube's 'Show transcript' panel.
    Timestamp lines (0:05, 1:02:30) mark the start of the text that follows."""
    snippets, start = [], 0.0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r"\d{1,2}(:\d{2}){1,2}", line):
            parts = [int(p) for p in line.split(":")]
            start = sum(p * 60 ** i for i, p in enumerate(reversed(parts)))
            continue
        snippets.append({"start": start, "text": line})
    return snippets


def fmt_time(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


# ── Step 3: transcript → chunks that fit in one LLM call ─────────────────────
def chunk_transcript(snippets, max_chars=CHUNK_CHARS):
    chunks, current, size = [], [], 0
    for s in snippets:
        line = f"[{fmt_time(s['start'])}] {s['text']}"
        if size + len(line) > max_chars and current:
            chunks.append("\n".join(current))
            current, size = [], 0
        current.append(line)
        size += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks


# ── Step 4–6: Mistral calls ──────────────────────────────────────────────────
def notes_for_chunk(llm, chunk, part, total, language):
    system = (
        "You are an expert note-taker. You get one part of a video transcript. "
        "Each line starts with a [mm:ss] timestamp.\n"
        "Write concise bullet-point notes of the key ideas, definitions, examples "
        "and facts. Start every bullet with the timestamp where that idea begins, "
        "like '[03:15]'. Use only information from the transcript. "
        f"Write the notes in {language}."
    )
    user = f"Transcript part {part} of {total}:\n\n{chunk}"
    reply = call_with_retry(llm.invoke, [SystemMessage(system), HumanMessage(user)])
    return reply.content


def combine_notes(llm, partial_notes, language):
    system = (
        "You are a teacher writing study notes for a student. Combine the notes "
        "below into one well-organised Markdown document with these sections:\n"
        "## Summary — 3 to 5 sentences\n"
        "## Key Points — bullets grouped under ### sub-headings by topic; keep the "
        "[mm:ss] timestamps at the start of bullets\n"
        "## Key Terms — **term**: short definition\n"
        "## Takeaways — the 3 to 5 most important things to remember\n"
        "Remove repetition. Do not add facts that are not in the notes. "
        "Return plain Markdown, not wrapped in a code block. "
        f"Write in {language}."
    )
    user = "\n\n---\n\n".join(partial_notes)
    reply = call_with_retry(llm.invoke, [SystemMessage(system), HumanMessage(user)])
    return strip_code_fence(reply.content)


def strip_code_fence(text: str) -> str:
    """Small models sometimes wrap Markdown in ```markdown ... ``` — remove it."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def make_study_material(llm, notes, n_flashcards, n_quiz, language):
    system = (
        f"From the study notes, create {n_flashcards} flashcards and "
        f"{n_quiz} multiple-choice quiz questions that test understanding, not "
        "trivia. Each quiz question has exactly 4 options with one correct answer. "
        f"Write in {language}."
    )
    structured = llm.with_structured_output(StudyMaterial)
    material = call_with_retry(structured.invoke, [SystemMessage(system), HumanMessage(notes)])
    # drop malformed quiz questions instead of crashing the UI
    material.quiz = [
        q for q in material.quiz
        if len(q.options) >= 2 and 0 <= q.correct_index < len(q.options)
    ]
    return material


def run_workflow(url, model, language, n_flashcards, n_quiz, pasted=""):
    """The fixed AI workflow. Each step always runs in the same order."""
    with st.status("Generating study notes…", expanded=True) as status:
        st.write("1️⃣ Reading the video id")
        video_id = extract_video_id(url)
        if not video_id:
            status.update(label="Invalid YouTube URL", state="error")
            st.stop()

        if pasted.strip():
            st.write("2️⃣ Using the pasted transcript")
            snippets, lang_code = parse_pasted_transcript(pasted), "pasted"
        else:
            st.write("2️⃣ Fetching the transcript")
            try:
                snippets, lang_code = fetch_transcript(video_id)
            except RequestBlocked:
                status.update(label="YouTube blocked the request", state="error")
                st.error("YouTube is blocking transcript requests from this server's IP "
                         "(common on cloud hosts like Streamlit Cloud).\n\n"
                         "Free fix: on YouTube open the video → **...more → Show transcript**, "
                         "copy it, and paste it into **Paste transcript instead** above.")
                st.stop()
            except Exception as e:
                status.update(label="Could not get a transcript", state="error")
                st.error(f"This video has no available captions, or YouTube blocked the request.\n\n{type(e).__name__}: {e}")
                st.stop()

        if not snippets:
            status.update(label="Transcript is empty", state="error")
            st.stop()

        if language == "Same as video":
            language = f"the same language as the transcript (code: {lang_code})"

        chunks = chunk_transcript(snippets)
        llm = ChatMistralAI(model=model, temperature=0.2)

        try:
            if len(chunks) == 1:
                # short video: skip the per-chunk step and save an API call
                st.write("3️⃣ Short video — notes from the full transcript")
                partial = [chunks[0]]
            else:
                partial = []
                for i, chunk in enumerate(chunks, 1):
                    st.write(f"3️⃣ Notes for part {i} of {len(chunks)}")
                    partial.append(notes_for_chunk(llm, chunk, i, len(chunks), language))

            st.write("4️⃣ Combining into study notes")
            notes = combine_notes(llm, partial, language)

            st.write("5️⃣ Creating flashcards and quiz")
            material = make_study_material(llm, notes, n_flashcards, n_quiz, language)
        except Exception as e:
            status.update(label="Mistral API error", state="error")
            st.error(f"{type(e).__name__}: {e}\n\nIf this is a 429 / 403 error, pick a "
                     "different model in the sidebar or wait a minute and try again.")
            st.stop()

        status.update(label="Done!", state="complete", expanded=False)

    return {
        "video_id": video_id,
        "language": lang_code,
        "snippets": snippets,
        "chunks": len(chunks),
        "notes": notes,
        "material": material,
    }


# ── Helpers for downloads ────────────────────────────────────────────────────
def flashcards_csv(cards):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["question", "answer"])
    for c in cards:
        writer.writerow([c.question, c.answer])
    return buf.getvalue()


# ── UI ───────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="YouTube Study Notes", page_icon="🎓", layout="wide")
    st.title("🎓 YouTube Video → Study Notes")
    st.caption("Paste a YouTube link and get notes, flashcards and a quiz. Powered by Mistral.")

    with st.sidebar:
        st.header("Settings")
        model = st.selectbox("Mistral model", MODELS)
        language = st.selectbox("Notes language", ["English", "Hindi", "Same as video"])
        n_flashcards = st.slider("Flashcards", 3, 20, 8)
        n_quiz = st.slider("Quiz questions", 3, 15, 5)
        st.divider()
        st.markdown(
            "**Workflow steps**\n\n"
            "1. Video id\n2. Transcript\n3. Notes per chunk\n"
            "4. Combine notes\n5. Flashcards + quiz"
        )

    if not os.getenv("MISTRAL_API_KEY"):
        st.error("MISTRAL_API_KEY not found. Add it to your .env file.")
        st.stop()

    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    with st.expander("Paste transcript instead (if YouTube blocks the request)"):
        st.caption("On YouTube: **...more → Show transcript**, select all of it, copy, paste here.")
        pasted = st.text_area("Transcript", height=200, label_visibility="collapsed")
    if st.button("Generate notes", type="primary", disabled=not url):
        st.session_state.result = run_workflow(url, model, language, n_flashcards, n_quiz, pasted)
        st.session_state.answers_checked = False

    result = st.session_state.get("result")
    if not result:
        return

    left, right = st.columns([2, 1])
    with right:
        st.video(f"https://www.youtube.com/watch?v={result['video_id']}")
        duration = fmt_time(result["snippets"][-1]["start"]) if result["snippets"] else "?"
        st.caption(
            f"Transcript language: {result['language']} · length ≈ {duration} · "
            f"{result['chunks']} chunk(s)"
        )

    with left:
        tab_notes, tab_cards, tab_quiz, tab_transcript = st.tabs(
            ["📝 Notes", "🃏 Flashcards", "❓ Quiz", "📜 Transcript"]
        )

        with tab_notes:
            st.markdown(result["notes"])
            st.download_button("⬇️ Download notes (.md)", result["notes"],
                               file_name=f"notes_{result['video_id']}.md")

        with tab_cards:
            cards = result["material"].flashcards
            for i, card in enumerate(cards, 1):
                with st.expander(f"**{i}. {card.question}**"):
                    st.write(card.answer)
            st.download_button("⬇️ Download flashcards (.csv, Anki-ready)",
                               flashcards_csv(cards),
                               file_name=f"flashcards_{result['video_id']}.csv")

        with tab_quiz:
            quiz = result["material"].quiz
            for i, q in enumerate(quiz):
                st.radio(f"**{i + 1}. {q.question}**", q.options, index=None, key=f"quiz_{i}")
            if st.button("Check answers"):
                st.session_state.answers_checked = True
            if st.session_state.get("answers_checked"):
                score = 0
                for i, q in enumerate(quiz):
                    picked = st.session_state.get(f"quiz_{i}")
                    correct = q.options[q.correct_index]
                    if picked == correct:
                        score += 1
                        st.success(f"{i + 1}. ✅ Correct — {q.explanation}")
                    else:
                        st.error(f"{i + 1}. ❌ Answer: **{correct}** — {q.explanation}")
                st.metric("Score", f"{score} / {len(quiz)}")

        with tab_transcript:
            text = "\n".join(f"[{fmt_time(s['start'])}] {s['text']}" for s in result["snippets"])
            st.text_area("Full transcript", text, height=400)


if __name__ == "__main__":
    main()
