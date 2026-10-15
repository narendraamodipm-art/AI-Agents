"""Streamlit Web Interface for Funny Chatbot using Mistral AI."""

import os
import streamlit as st
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

PAGE_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Background ── */
[data-testid="stAppViewContainer"] > .main {
    background: radial-gradient(ellipse at top, #1a0533 0%, #0a0a1a 60%);
    min-height: 100vh;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #120826 0%, #1a0f2e 100%);
    border-right: 1px solid #2d1f4e;
}
[data-testid="stSidebar"] * { color: #d4b8ff !important; }

/* ── Hero banner ── */
.hero {
    text-align: center;
    padding: 2.2rem 1rem 1.5rem;
    margin-bottom: 1rem;
}
.hero .emoji-ring {
    font-size: 4rem;
    display: block;
    margin-bottom: 0.4rem;
    animation: bounce 2s infinite;
}
@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-8px); }
}
.hero h1 {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(90deg, #f472b6, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.3rem 0;
    line-height: 1.2;
}
.hero p {
    color: #94a3b8;
    font-size: 1rem;
    margin: 0;
}

/* ── Stats bar ── */
.stats-bar {
    display: flex;
    justify-content: center;
    gap: 1.5rem;
    margin-bottom: 1.4rem;
    flex-wrap: wrap;
}
.stat-chip {
    background: rgba(167,139,250,0.1);
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: 20px;
    padding: 0.3rem 0.9rem;
    font-size: 0.78rem;
    color: #c4b5fd;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: rgba(26, 15, 46, 0.7) !important;
    border: 1px solid rgba(167,139,250,0.15);
    border-radius: 14px;
    margin-bottom: 0.5rem;
    backdrop-filter: blur(10px);
}

/* ── Chat input ── */
[data-testid="stChatInput"] textarea {
    background: rgba(26,15,46,0.95) !important;
    border: 2px solid #7c3aed !important;
    border-radius: 18px !important;
    color: #e2e8f0 !important;
    font-size: 1.05rem !important;
    padding: 1rem 1.2rem !important;
    min-height: 64px !important;
    line-height: 1.5 !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #a78bfa !important;
    box-shadow: 0 0 0 4px rgba(167,139,250,0.25), 0 8px 32px rgba(124,58,237,0.3) !important;
}

/* ── Sidebar buttons ── */
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: linear-gradient(90deg, #7c3aed, #6d28d9);
    color: white !important;
    border: none;
    border-radius: 10px;
    padding: 0.55rem 1rem;
    font-weight: 600;
    font-size: 0.88rem;
    transition: all 0.2s;
    margin-bottom: 0.4rem;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(90deg, #8b5cf6, #7c3aed);
    transform: translateY(-1px);
}

/* ── Sidebar info cards ── */
.info-card {
    background: rgba(124,58,237,0.12);
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.7rem;
}
.info-card .label {
    font-size: 0.7rem;
    color: #9d7fea;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.25rem;
}
.info-card .value {
    font-size: 0.88rem;
    color: #d4b8ff;
    font-weight: 500;
}

/* ── Prompt suggestions ── */
.suggestion-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    margin-bottom: 1rem;
}
.suggestion-pill {
    background: rgba(124,58,237,0.12);
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 10px;
    padding: 0.6rem 0.8rem;
    font-size: 0.78rem;
    color: #c4b5fd;
    cursor: pointer;
    text-align: center;
    line-height: 1.3;
}
.suggestion-pill:hover {
    background: rgba(124,58,237,0.25);
    border-color: #a78bfa;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 2.5rem 1rem;
    color: #64748b;
}
.empty-state .big-emoji { font-size: 3.5rem; margin-bottom: 0.5rem; }
.empty-state p { font-size: 0.95rem; margin: 0; }

/* ── Divider ── */
.sidebar-divider {
    border: none;
    border-top: 1px solid #2d1f4e;
    margin: 0.8rem 0;
}
</style>
"""

SUGGESTIONS = [
    "Why do cats knock things off tables?",
    "Explain quantum physics like I'm 5",
    "Tell me a joke about programmers",
    "Why is Monday everyone's nemesis?",
    "Give me a life tip that's totally useless",
    "Roast my decision to ask an AI for advice",
]


def initialize_client():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        st.error("MISTRAL_API_KEY not found. Add it to your .env file.")
        st.stop()
    return Mistral(api_key=api_key)


def get_funny_response(client: Mistral, user_message: str, history: list) -> str:
    system = (
        "You are HahaBot — a brilliantly witty, hilarious AI. "
        "You reply with clever humor, puns, and light sarcasm. "
        "Keep responses punchy (2-4 sentences max) and always end with a fun twist or emoji. "
        "Never be mean-spirited — keep it playful and fun."
    )
    messages = [{"role": "system", "content": system}]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.complete(model="ministral-8b-latest", messages=messages)
    return response.choices[0].message.content


def main():
    st.set_page_config(page_title="HahaBot", page_icon="😂", layout="centered")
    st.markdown(PAGE_STYLE, unsafe_allow_html=True)

    client = initialize_client()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "msg_count" not in st.session_state:
        st.session_state.msg_count = 0
    if "pending" not in st.session_state:
        st.session_state.pending = None

    # ── Sidebar ───────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 😂 HahaBot")
        st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

        st.markdown("<div class='info-card'><div class='label'>Model</div><div class='value'>Ministral 8B (Latest)</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='info-card'><div class='label'>Messages this session</div><div class='value'>" + str(st.session_state.msg_count) + " exchanges</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='info-card'><div class='label'>Mode</div><div class='value'>Funny · Context-aware · Witty</div></div>", unsafe_allow_html=True)

        st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.msg_count = 0
            st.rerun()

        st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.75rem;color:#6b5ea8;text-align:center'>Powered by Mistral AI · Built with Streamlit</div>", unsafe_allow_html=True)

    # ── Hero ──────────────────────────────────────────────
    st.markdown("""
    <div class='hero'>
        <span class='emoji-ring'>😂</span>
        <h1>HahaBot</h1>
        <p>Your AI comedian — ask anything, get hilariously witty answers</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class='stats-bar'>
        <span class='stat-chip'>🧠 Context-aware</span>
        <span class='stat-chip'>⚡ Ministral 8B</span>
        <span class='stat-chip'>😜 Always funny</span>
        <span class='stat-chip'>💬 Chat history</span>
    </div>""", unsafe_allow_html=True)

    # ── Suggestion pills (shown only when chat is empty) ──
    if not st.session_state.messages:
        st.markdown("""
        <div class='empty-state'>
            <div class='big-emoji'>👋</div>
            <p>No boring questions here! Try one of these or ask your own:</p>
        </div>""", unsafe_allow_html=True)

        cols = st.columns(2)
        for i, suggestion in enumerate(SUGGESTIONS):
            with cols[i % 2]:
                if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                    st.session_state.pending = suggestion
                    st.rerun()

    # ── Chat history ──────────────────────────────────────
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "😂"):
            st.markdown(msg["content"])

    # ── Process pending suggestion click ──────────────────
    if st.session_state.pending:
        question = st.session_state.pending
        st.session_state.pending = None

        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(question)

        with st.chat_message("assistant", avatar="😂"):
            with st.spinner("Cooking up something hilarious..."):
                try:
                    reply = get_funny_response(client, question, st.session_state.messages[:-1])
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    st.session_state.msg_count += 1
                    st.markdown(reply)
                except Exception as e:
                    st.error(f"Error: {e}")
        st.rerun()

    # ── Chat input ────────────────────────────────────────
    question = st.chat_input("Ask me anything... I dare you 😏")

    if question:
        if question.lower() in ["bye", "quit", "exit", "q"]:
            st.session_state.messages.append({"role": "user", "content": question})
            st.session_state.messages.append({"role": "assistant", "content": "Bye bye! May your Wi-Fi always be strong and your Mondays short! 👋😂"})
            st.rerun()
            return

        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(question)

        with st.chat_message("assistant", avatar="😂"):
            with st.spinner("Cooking up something hilarious..."):
                try:
                    reply = get_funny_response(client, question, st.session_state.messages[:-1])
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    st.session_state.msg_count += 1
                    st.markdown(reply)
                except Exception as e:
                    st.error(f"Error: {e}")
        st.rerun()


if __name__ == "__main__":
    main()
