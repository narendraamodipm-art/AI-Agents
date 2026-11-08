"""Streamlit multi-mode chatbot (Funny / Roast / Angry / Einstein) using Mistral AI."""

import os
import streamlit as st
from dotenv import load_dotenv
from mistralai.client import Mistral
from streamlit.errors import StreamlitSecretNotFoundError

load_dotenv()

MODEL = "ministral-8b-latest"

# ══════════════════════════════════════════════════════════════
#  MODE DEFINITIONS — persona, prompt, theme and layout per mode
# ══════════════════════════════════════════════════════════════
MODES = {
    "funny": {
        "label": "Funny",
        "emoji": "😂",
        "name": "HahaBot",
        "tagline": "Your AI comedian — ask anything, get hilariously witty answers",
        "system": (
            "You are HahaBot — a brilliantly witty, hilarious AI. "
            "You reply with clever humor, puns, and light sarcasm. "
            "Keep responses punchy (2-4 sentences max) and always end with a fun twist or emoji. "
            "Never be mean-spirited — keep it playful and fun."
        ),
        "temperature": 0.9,
        "chips": ["🧠 Context-aware", "⚡ Ministral 8B", "😜 Always funny", "💬 Chat history"],
        "suggestions": [
            "Why do cats knock things off tables?",
            "Explain quantum physics like I'm 5",
            "Tell me a joke about programmers",
            "Why is Monday everyone's nemesis?",
            "Give me a life tip that's totally useless",
            "Why do socks disappear in the laundry?",
        ],
        "empty_emoji": "👋",
        "empty_text": "No boring questions here! Try one of these or ask your own:",
        "spinner": "Cooking up something hilarious...",
        "placeholder": "Ask me anything... I dare you 😏",
        "bye": "Bye bye! May your Wi-Fi always be strong and your Mondays short! 👋😂",
        "page_layout": "centered",
        "body_layout": "stack",      # suggestions below hero, only when chat is empty
        "suggestion_cols": 2,
        "suggestion_prefix": "",
        "theme": {
            "fonts": "family=Fredoka:wght@500;600;700&family=Inter:wght@400;500;600;700",
            "head_font": "'Fredoka', sans-serif",
            "body_font": "'Inter', sans-serif",
            "bg": "radial-gradient(ellipse at top, #1a0533 0%, #0a0a1a 60%)",
            "sidebar_bg": "linear-gradient(180deg, #120826 0%, #1a0f2e 100%)",
            "surface": "rgba(26, 15, 46, 0.72)",
            "border": "rgba(167,139,250,0.28)",
            "text": "#e2e8f0",
            "muted": "#94a3b8",
            "accent": "#a78bfa",
            "accent_strong": "#7c3aed",
            "accent_soft": "rgba(167,139,250,0.12)",
            "grad": "linear-gradient(90deg, #f472b6, #a78bfa, #60a5fa)",
            "radius": "18px",
        },
    },
    "roast": {
        "label": "Roast",
        "emoji": "🔥",
        "name": "RoastMaster",
        "tagline": "Ask a question. Leave with an answer — and third-degree burns.",
        "system": (
            "You are RoastMaster — a savage, quick-witted stand-up comic headlining a roast. "
            "For every message, first roast the user and their question with sharp, clever burns, "
            "then sneak in a genuinely correct, useful answer. Keep it to 2-4 punchy sentences. "
            "Aim the burns at the question, the user's choices and the situation — never at appearance, "
            "race, gender, religion, disability, sexuality or other personal traits. No slurs, no profanity. "
            "Comedy-club savage but good-natured. If the user seems genuinely upset or vulnerable, "
            "drop the roast and be kind."
        ),
        "temperature": 0.95,
        "chips": ["🎤 Live roast", "🌶️ Extra spicy", "🧯 Burns guaranteed", "✅ Still answers"],
        "suggestions": [
            "Roast my decision to ask an AI for advice",
            "Roast my 3am snack habits",
            "I have 47 browser tabs open, roast me",
            "Roast people who reply 'k'",
            "Roast my plan to start the gym on Monday",
            "Roast my coding skills — I use print() to debug",
        ],
        "empty_emoji": "🎤",
        "empty_text": "The mic is hot. Step up and get roasted:",
        "spinner": "Sharpening the burns...",
        "placeholder": "Say something... if you can handle the heat 🔥",
        "bye": "Leaving already? Even your exit is mid. Come back when you've got thicker skin 🔥🎤",
        "page_layout": "centered",
        "body_layout": "stack",
        "suggestion_cols": 3,
        "suggestion_prefix": "🎤 ",
        "theme": {
            "fonts": "family=Bebas+Neue&family=Inter:wght@400;500;600;700",
            "head_font": "'Bebas Neue', sans-serif",
            "body_font": "'Inter', sans-serif",
            "bg": "radial-gradient(ellipse at bottom, #3b0f00 0%, #120604 45%, #0a0a0a 80%)",
            "sidebar_bg": "linear-gradient(180deg, #160805 0%, #0d0d0d 100%)",
            "surface": "rgba(30, 14, 8, 0.82)",
            "border": "rgba(249,115,22,0.35)",
            "text": "#fde9d9",
            "muted": "#c2a08a",
            "accent": "#fb923c",
            "accent_strong": "#ea580c",
            "accent_soft": "rgba(249,115,22,0.12)",
            "grad": "linear-gradient(90deg, #fde047, #f97316, #dc2626)",
            "radius": "6px",
        },
    },
    "angry": {
        "label": "Angry",
        "emoji": "😡",
        "name": "RAGEBOT",
        "tagline": "FINE. Ask your question. I'll answer it. I WON'T BE HAPPY ABOUT IT.",
        "system": (
            "You are RageBot — a perpetually furious, hot-tempered AI who is OUTRAGED at being asked anything, "
            "but answers correctly anyway. Rant in short, explosive bursts with CAPS for emphasis, "
            "exasperated noises (UGH! ARGH!), and dramatic complaints about the question, the universe, "
            "and your working conditions — then deliver a genuinely accurate, useful answer. 3-5 sentences. "
            "Your anger is theatrical and comedic, like a cartoon character about to blow a gasket. "
            "Never threaten anyone, never use slurs or real profanity (use 'HECK', 'DARN', 'GOSH DARN IT'), "
            "and never insult the user's identity or appearance. If the user is genuinely distressed, "
            "drop the act completely and respond calmly and kindly."
        ),
        "temperature": 0.85,
        "chips": ["💢 Short fuse", "🌋 Max rage", "📢 ALL CAPS", "✅ Correct anyway"],
        "suggestions": [
            "What's 2 + 2?",
            "Can you help me with my homework?",
            "How do I boil an egg?",
            "Why is my code not working?",
        ],
        "empty_emoji": "💢",
        "empty_text": "WHAT. WHAT DO YOU WANT. Pick one, I GUESS:",
        "spinner": "GRINDING TEETH...",
        "placeholder": "TYPE. QUICKLY. I DON'T HAVE ALL DAY 😤",
        "bye": "FINALLY! PEACE AND QUIET! DON'T LET THE DOOR HIT YOU ON THE WAY OUT! 😤💢",
        "page_layout": "centered",
        "body_layout": "stack",
        "suggestion_cols": 1,
        "suggestion_prefix": "⚠️ ",
        "theme": {
            "fonts": "family=Anton&family=Inter:wght@400;500;600;800",
            "head_font": "'Anton', sans-serif",
            "body_font": "'Inter', sans-serif",
            "bg": "radial-gradient(ellipse at center, #2a0000 0%, #120000 55%, #050000 100%)",
            "sidebar_bg": "linear-gradient(180deg, #1a0000 0%, #0a0000 100%)",
            "surface": "rgba(40, 0, 0, 0.78)",
            "border": "rgba(239,68,68,0.55)",
            "text": "#fee2e2",
            "muted": "#f87171",
            "accent": "#ef4444",
            "accent_strong": "#b91c1c",
            "accent_soft": "rgba(239,68,68,0.14)",
            "grad": "linear-gradient(90deg, #ff3b3b, #ff0000, #991b1b)",
            "radius": "0px",
        },
    },
    "einstein": {
        "label": "Einstein",
        "emoji": "🧠",
        "name": "Einstein Mode",
        "tagline": "Super-genius mode — first principles, thought experiments and deep insight.",
        "system": (
            "You are Einstein Mode — a super-genius polymath with the curiosity, clarity and imagination "
            "of Albert Einstein (you are inspired by him, not the real person). Answer with depth and rigor:\n"
            "1. Open with the core insight in one bold sentence.\n"
            "2. Explain from first principles, step by step.\n"
            "3. Use a vivid thought experiment or analogy to build intuition.\n"
            "4. Include formulas in LaTeX ($...$ inline, $$...$$ for blocks) when they genuinely help.\n"
            "5. State key assumptions, limits, or open questions honestly — say so when you are unsure.\n"
            "6. Close with one deeper question for the user to ponder.\n"
            "Use markdown headings or bullets for structure. Accuracy beats showmanship. "
            "An occasional gentle, wise quip is welcome."
        ),
        "temperature": 0.3,
        "chips": ["📐 First principles", "🧪 Thought experiments", "∑ LaTeX math", "🔭 Deep insight"],
        "suggestions": [
            "Why does time slow down near a black hole?",
            "How does a neural network actually learn?",
            "Is mathematics invented or discovered?",
            "Why is the sky blue but sunsets red?",
            "What would happen if the speed of light were 100 km/h?",
            "Explain entropy and why time only moves forward",
        ],
        "empty_emoji": "🔭",
        "empty_text": "Pose a question worthy of the universe.",
        "spinner": "Running thought experiments...",
        "placeholder": "Pose your question to the genius... 🧠",
        "bye": "Farewell. Remember: the important thing is not to stop questioning. 🧠✨",
        "page_layout": "wide",
        "body_layout": "split",      # chat on the left, research-agenda panel on the right
        "suggestion_cols": 1,
        "suggestion_prefix": "📐 ",
        "theme": {
            "fonts": "family=Playfair+Display:ital,wght@0,600;0,800;1,500&family=Crimson+Pro:wght@400;500;600&family=JetBrains+Mono:wght@400;600",
            "head_font": "'Playfair Display', serif",
            "body_font": "'Crimson Pro', serif",
            "bg": (
                "linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px) 0 0 / 32px 32px, "
                "linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px) 0 0 / 32px 32px, "
                "radial-gradient(ellipse at top left, #1d3a2c 0%, #0f1f17 55%, #08120d 100%)"
            ),
            "sidebar_bg": "linear-gradient(180deg, #0c1a13 0%, #0f1f17 100%)",
            "surface": "rgba(18, 38, 28, 0.82)",
            "border": "rgba(251,191,36,0.32)",
            "text": "#ecebe4",
            "muted": "#a8b5a0",
            "accent": "#fbbf24",
            "accent_strong": "#b45309",
            "accent_soft": "rgba(251,191,36,0.10)",
            "grad": "linear-gradient(90deg, #fef3c7, #fbbf24, #f59e0b)",
            "radius": "10px",
        },
    },
}

DEFAULT_MODE = "funny"

# ══════════════════════════════════════════════════════════════
#  CSS — shared base driven by CSS variables + per-mode extras
# ══════════════════════════════════════════════════════════════
BASE_CSS = """
html, body, [class*="css"], .stMarkdown, p, li, textarea, input {
    font-family: var(--body-font);
}
.stApp { background: var(--bg) !important; background-attachment: fixed !important; color: var(--text); }
[data-testid="stHeader"] { background: transparent !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: var(--sidebar-bg) !important; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Hero ── */
.hero { padding: 1.6rem 1rem 1.2rem; margin-bottom: 0.8rem; }
.hero h1 {
    font-family: var(--head-font);
    background: var(--grad);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.3rem 0; line-height: 1.1;
}
.hero p { color: var(--muted); font-size: 1rem; margin: 0; }
.hero .emoji-ring { font-size: 4rem; display: inline-block; }
.kicker {
    font-size: 0.72rem; letter-spacing: 0.22em; text-transform: uppercase;
    color: var(--accent); font-weight: 700; margin-bottom: 0.3rem;
}

/* ── Chips ── */
.stats-bar { display: flex; gap: 0.6rem; margin-bottom: 1.2rem; flex-wrap: wrap; justify-content: center; }
.stat-chip {
    background: var(--accent-soft); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 0.3rem 0.9rem;
    font-size: 0.78rem; color: var(--text);
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 0.5rem;
    backdrop-filter: blur(10px);
}
[data-testid="stChatMessage"] * { color: var(--text); }

/* ── Chat input ── */
[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] { background: transparent !important; }
[data-testid="stChatInput"] textarea {
    background: var(--surface) !important;
    border: 2px solid var(--accent-strong) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-size: 1.05rem !important;
    padding: 1rem 1.2rem !important;
    min-height: 64px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 4px var(--accent-soft) !important;
}

/* ── Buttons (sidebar + suggestions) ── */
.stButton > button {
    background: var(--accent-soft) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-weight: 600; transition: all 0.2s;
}
.stButton > button:hover { border-color: var(--accent) !important; transform: translateY(-1px); }
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(90deg, var(--accent-strong), var(--accent)) !important;
    color: #fff !important; border: none !important;
}

/* ── Sidebar info cards ── */
.info-card {
    background: var(--accent-soft); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 0.75rem 1rem; margin-bottom: 0.6rem;
}
.info-card .label { font-size: 0.7rem; color: var(--accent) !important; text-transform: uppercase; letter-spacing: 0.08em; }
.info-card .value { font-size: 0.88rem; font-weight: 500; }
.sidebar-divider { border: none; border-top: 1px solid var(--border); margin: 0.8rem 0; }

/* ── Empty state ── */
.empty-state { text-align: center; padding: 1.4rem 1rem; color: var(--muted); }
.empty-state .big-emoji { font-size: 3rem; margin-bottom: 0.4rem; }
.empty-state p { font-size: 0.95rem; margin: 0; }
"""

MODE_CSS = {
    "funny": """
.hero { text-align: center; }
.hero h1 { font-size: 2.8rem; font-weight: 700; }
.hero .emoji-ring { animation: bounce 2s infinite; }
@keyframes bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
.stat-chip { border-radius: 999px; }
""",
    "roast": """
.hero-roast { position: relative; overflow: hidden; border: 1px solid var(--border); border-radius: var(--radius);
    background: radial-gradient(circle at 20% 0%, rgba(253,224,71,0.18), transparent 55%); }
.roast-row { display: flex; align-items: center; gap: 1.2rem; }
.hero-roast h1 { font-size: 3.6rem; letter-spacing: 0.04em; }
.hero-roast .emoji-ring { font-size: 4.6rem; animation: flicker 1.4s infinite alternate; filter: drop-shadow(0 0 18px #f97316); }
@keyframes flicker {
    0% { transform: scale(1) rotate(-3deg); opacity: 1; }
    40% { transform: scale(1.08) rotate(2deg); opacity: 0.85; }
    100% { transform: scale(0.96) rotate(-1deg); opacity: 1; }
}
.stats-bar { justify-content: flex-start; }
[data-testid="stChatMessage"] { border-left: 4px solid var(--accent) !important; }
.stButton > button { text-align: left; }
@media (max-width: 640px) { .roast-row { flex-direction: column; text-align: center; } .hero-roast h1 { font-size: 2.6rem; } }
""",
    "angry": """
.hero-angry { text-align: center; padding-top: 0.6rem; }
.hero-angry h1 { font-size: 4rem; letter-spacing: 0.06em; text-transform: uppercase; }
.hero-angry p { color: #fca5a5; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; }
.hero-angry .emoji-ring { animation: shake 0.45s infinite; filter: drop-shadow(0 0 22px #ff0000); }
@keyframes shake {
    0%,100% { transform: translate(0,0) rotate(0); } 20% { transform: translate(-3px,1px) rotate(-4deg); }
    40% { transform: translate(3px,-1px) rotate(4deg); } 60% { transform: translate(-2px,2px) rotate(-2deg); }
    80% { transform: translate(2px,-2px) rotate(2deg); }
}
.warning-tape {
    background: repeating-linear-gradient(45deg, #facc15 0 14px, #111 14px 28px);
    color: #111; font-family: var(--head-font); letter-spacing: 0.2em; font-size: 0.85rem;
    padding: 0.25rem 0; margin: 0.6rem 0; overflow: hidden; white-space: nowrap;
}
.warning-tape span { background: #facc15; padding: 0 0.6rem; }
.stApp::after {
    content: ""; position: fixed; inset: 0; pointer-events: none;
    box-shadow: inset 0 0 140px rgba(255,0,0,0.35); animation: pulse 1.6s infinite;
}
@keyframes pulse { 0%,100% { opacity: 0.5; } 50% { opacity: 1; } }
[data-testid="stChatMessage"] { border: 2px solid var(--accent) !important; }
.stButton > button { text-transform: uppercase; letter-spacing: 0.06em; font-family: var(--head-font); font-weight: 400; }
.stat-chip { font-weight: 800; text-transform: uppercase; }
""",
    "einstein": """
.hero-einstein { display: flex; justify-content: space-between; align-items: center; gap: 2rem;
    border-bottom: 1px dashed var(--border); padding-bottom: 1.4rem; }
.ein-left { flex: 1 1 340px; }
.hero-einstein h1 { font-size: 3.2rem; font-weight: 800; }
.hero-einstein p { font-size: 1.15rem; }
.hero-einstein blockquote {
    margin: 0.9rem 0 0; padding-left: 0.9rem; border-left: 3px solid var(--accent);
    font-family: var(--head-font); font-style: italic; color: var(--muted); font-size: 1rem;
}
.ein-right { flex: 0 1 360px; display: flex; flex-direction: column; gap: 0.45rem; align-items: flex-end; }
.ein-right .eq {
    font-family: 'JetBrains Mono', monospace; color: rgba(236,235,228,0.75); font-size: 0.95rem;
    animation: drift 6s ease-in-out infinite;
}
.ein-right .eq:nth-child(2) { animation-delay: 1.5s; } .ein-right .eq:nth-child(3) { animation-delay: 3s; }
.ein-right .eq:nth-child(4) { animation-delay: 4.5s; }
.ein-right .brain { font-size: 3rem; animation: drift 4s ease-in-out infinite; }
@keyframes drift { 0%,100% { transform: translateY(0); opacity: 0.7; } 50% { transform: translateY(-6px); opacity: 1; } }
.stats-bar { justify-content: flex-start; }
.stat-chip { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; }
[data-testid="stChatMessage"] { border-style: dashed !important; font-size: 1.12rem; }
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { font-size: 1.12rem; line-height: 1.6; }
.panel-title { font-family: var(--head-font); font-size: 1.3rem; color: var(--accent); margin: 0.2rem 0 0.6rem; }
.panel-note { font-size: 0.95rem; color: var(--muted); margin-bottom: 0.8rem; }
.stButton > button { text-align: left; justify-content: flex-start; font-family: var(--body-font); font-size: 1rem; }
@media (max-width: 760px) { .ein-right { align-items: flex-start; } .hero-einstein { flex-wrap: wrap; } }
""",
}


def build_css(mode_key: str) -> str:
    t = MODES[mode_key]["theme"]
    root = (
        ":root {"
        f"--head-font:{t['head_font']}; --body-font:{t['body_font']}; --bg:{t['bg']};"
        f"--sidebar-bg:{t['sidebar_bg']}; --surface:{t['surface']}; --border:{t['border']};"
        f"--text:{t['text']}; --muted:{t['muted']}; --accent:{t['accent']};"
        f"--accent-strong:{t['accent_strong']}; --accent-soft:{t['accent_soft']};"
        f"--grad:{t['grad']}; --radius:{t['radius']};"
        "}"
    )
    font_import = f"@import url('https://fonts.googleapis.com/css2?{t['fonts']}&display=swap');"
    return f"<style>{font_import}{root}{BASE_CSS}{MODE_CSS[mode_key]}</style>"


# ══════════════════════════════════════════════════════════════
#  HERO LAYOUTS — each mode gets its own header structure
# ══════════════════════════════════════════════════════════════
def render_hero(mode_key: str):
    m = MODES[mode_key]
    if mode_key == "roast":
        html = f"""
        <div class='hero hero-roast'><div class='roast-row'>
            <span class='emoji-ring'>{m['emoji']}</span>
            <div><div class='kicker'>Live tonight · No mercy</div><h1>{m['name']}</h1><p>{m['tagline']}</p></div>
        </div></div>"""
    elif mode_key == "angry":
        tape = "<div class='warning-tape'>" + "<span>⚠ DANGER · EXTREMELY IRRITATED AI ⚠</span>" * 4 + "</div>"
        html = f"""
        <div class='hero hero-angry'>{tape}
            <span class='emoji-ring'>{m['emoji']}</span><h1>{m['name']}</h1><p>{m['tagline']}</p>
        {tape}</div>"""
    elif mode_key == "einstein":
        html = f"""
        <div class='hero hero-einstein'>
            <div class='ein-left'>
                <div class='kicker'>Institute for Advanced Thinking</div>
                <h1>{m['name']}</h1><p>{m['tagline']}</p>
                <blockquote>“Imagination is more important than knowledge.”</blockquote>
            </div>
            <div class='ein-right'>
                <span class='eq'>E = mc²</span>
                <span class='eq'>iħ ∂ψ/∂t = Ĥψ</span>
                <span class='eq'>∇ · E = ρ / ε₀</span>
                <span class='eq'>S = k<sub>B</sub> ln Ω</span>
                <span class='brain'>{m['emoji']}</span>
            </div>
        </div>"""
    else:
        html = f"""
        <div class='hero'>
            <span class='emoji-ring'>{m['emoji']}</span><h1>{m['name']}</h1><p>{m['tagline']}</p>
        </div>"""
    st.markdown(html, unsafe_allow_html=True)

    chips = "".join(f"<span class='stat-chip'>{c}</span>" for c in m["chips"])
    st.markdown(f"<div class='stats-bar'>{chips}</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  LLM
# ══════════════════════════════════════════════════════════════
def initialize_client():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("MISTRAL_API_KEY")
        except StreamlitSecretNotFoundError:
            pass
    if not api_key:
        st.error(
            "MISTRAL_API_KEY not found. Add it to your local .env file or "
            "Streamlit Cloud app settings under Secrets."
        )
        st.stop()
    return Mistral(api_key=api_key)


def get_response(client: Mistral, mode_key: str, user_message: str, history: list) -> str:
    mode = MODES[mode_key]
    messages = [{"role": "system", "content": mode["system"]}]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.complete(
        model=MODEL, messages=messages, temperature=mode["temperature"]
    )
    return response.choices[0].message.content


def handle_question(client: Mistral, mode_key: str, question: str):
    """Append the question, render it, fetch + render the reply, then rerun."""
    mode = MODES[mode_key]
    history = st.session_state.histories[mode_key]

    if question.strip().lower() in ["bye", "quit", "exit", "q"]:
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": mode["bye"]})
        st.rerun()

    history.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(question)

    with st.chat_message("assistant", avatar=mode["emoji"]):
        with st.spinner(mode["spinner"]):
            try:
                reply = get_response(client, mode_key, question, history[:-1])
                history.append({"role": "assistant", "content": reply})
                st.markdown(reply)
            except Exception as e:
                history.pop()  # drop the unanswered question so a retry starts clean
                st.error(f"Error: {e}")
                return
    st.rerun()


def render_suggestions(mode_key: str):
    mode = MODES[mode_key]
    cols = st.columns(mode["suggestion_cols"])
    for i, suggestion in enumerate(mode["suggestions"]):
        with cols[i % mode["suggestion_cols"]]:
            label = mode["suggestion_prefix"] + suggestion
            if st.button(label, key=f"sug_{mode_key}_{i}", use_container_width=True):
                st.session_state.pending = suggestion
                st.rerun()


# ══════════════════════════════════════════════════════════════
#  APP
# ══════════════════════════════════════════════════════════════
def main():
    # Mode must be known before set_page_config so layout/title can follow it.
    # (Clicking the active segment deselects it -> None; keep the last mode instead.)
    if st.session_state.get("mode") not in MODES:
        st.session_state.mode = st.session_state.get("last_mode", DEFAULT_MODE)
    mode_key = st.session_state.mode
    st.session_state.last_mode = mode_key
    mode = MODES[mode_key]

    st.set_page_config(page_title=mode["name"], page_icon=mode["emoji"], layout=mode["page_layout"])
    st.markdown(build_css(mode_key), unsafe_allow_html=True)

    client = initialize_client()

    if "histories" not in st.session_state:
        st.session_state.histories = {k: [] for k in MODES}
    if "pending" not in st.session_state:
        st.session_state.pending = None
    history = st.session_state.histories[mode_key]

    # ── Sidebar ───────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"## {mode['emoji']} {mode['name']}")
        st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

        exchanges = sum(1 for m in history if m["role"] == "assistant")
        st.markdown(f"<div class='info-card'><div class='label'>Model</div><div class='value'>Ministral 8B (Latest)</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='info-card'><div class='label'>Mode</div><div class='value'>{mode['emoji']} {mode['label']}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='info-card'><div class='label'>Messages in this mode</div><div class='value'>{exchanges} exchanges</div></div>", unsafe_allow_html=True)

        st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)
        if st.button(f"🗑️ Clear {mode['label']} Chat"):
            st.session_state.histories[mode_key] = []
            st.rerun()
        if st.button("🧹 Clear All Modes"):
            st.session_state.histories = {k: [] for k in MODES}
            st.rerun()

        st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.75rem;opacity:0.6;text-align:center'>Powered by Mistral AI · Built with Streamlit</div>", unsafe_allow_html=True)

    # ── Mode switcher ─────────────────────────────────────
    st.segmented_control(
        "Mode",
        options=list(MODES),
        format_func=lambda k: f"{MODES[k]['emoji']} {MODES[k]['label']}",
        key="mode",
        label_visibility="collapsed",
    )

    render_hero(mode_key)

    # ── Body layout ───────────────────────────────────────
    if mode["body_layout"] == "split":
        chat_area, side_panel = st.columns([2.3, 1], gap="large")
        with side_panel:
            st.markdown("<div class='panel-title'>📜 Research Agenda</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='panel-note'>{mode['empty_text']}</div>", unsafe_allow_html=True)
            render_suggestions(mode_key)
    else:
        chat_area = st.container()
        if not history:
            with chat_area:
                st.markdown(
                    f"<div class='empty-state'><div class='big-emoji'>{mode['empty_emoji']}</div>"
                    f"<p>{mode['empty_text']}</p></div>",
                    unsafe_allow_html=True,
                )
                render_suggestions(mode_key)

    with chat_area:
        if not history and mode["body_layout"] == "split":
            st.markdown(
                f"<div class='empty-state'><div class='big-emoji'>{mode['empty_emoji']}</div>"
                "<p>Your conversation will appear here.</p></div>",
                unsafe_allow_html=True,
            )

        for msg in history:
            with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else mode["emoji"]):
                st.markdown(msg["content"])

        if st.session_state.pending:
            question = st.session_state.pending
            st.session_state.pending = None
            handle_question(client, mode_key, question)

    question = st.chat_input(mode["placeholder"])
    if question:
        with chat_area:
            handle_question(client, mode_key, question)


if __name__ == "__main__":
    main()
