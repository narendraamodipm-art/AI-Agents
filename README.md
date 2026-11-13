# AI-Agents

AI agents, LLM workflows and RAG apps built by **Nikhil Kumar**, a Data Engineer and Cloud Engineer in Bengaluru. This repo also hosts my portfolio website.

**🌐 Portfolio:** https://narendraamodipm-art.github.io/AI-Agents/
**📄 Resume:** [Nikhil_Kumar_Resume.pdf](Nikhil_Kumar_Resume.pdf)
**✉️ Contact:** [Nikhil.nk0101@gmail.com](mailto:Nikhil.nk0101@gmail.com)

---

## Live demos

All of these run on free hosting. A GitHub Actions workflow keeps the Streamlit apps awake, but if one is asleep it can take a minute to start.

| Project | What it does | Stack | Live demo | Code |
|---|---|---|---|---|
| **Resume Matcher + Cover Letter Writer** | Scores how well a resume fits a job description, shows the skill gaps, rewrites bullets and writes a cover letter. A guardrail flags any invented numbers. | Python, LangChain, Mistral, Pydantic, Streamlit | [Open app](https://ai-resume-validator.streamlit.app/) | [`AI WORKFLOW/resume_matcher`](AI%20WORKFLOW/resume_matcher) |
| **YouTube → Study Notes** | Turns a YouTube video into timestamped notes, Anki flashcards and a quiz, using map-reduce summarisation. | Python, LangChain, Mistral, Streamlit | [Open app](https://ai-smart-notes-maker.streamlit.app/) | [`AI WORKFLOW/youtube_notes`](AI%20WORKFLOW/youtube_notes) |
| **DocChat AI (RAG)** | Answers questions about any PDF or web page, grounded in the top-4 chunks retrieved from Pinecone. | Python, LangChain, Mistral, Pinecone, Streamlit | [Open app](https://rag-for-study-and-reser.streamlit.app/) | [`RAG`](RAG) |
| **Travel Planner AI Agent** | A ReAct agent that chooses between web search, weather forecasts and a budget calculator to build day-by-day trip plans. | Python, Mistral, Tavily, OpenWeather, Streamlit | [Open app](https://ai-agents-plan-my-trip.streamlit.app/) | [`travel_planner`](travel_planner) |
| **GRAPHIFY** | Turns source code (Python, JS/TS, Java, HTML, Rust) into an interactive knowledge graph, with AI explanations. | Next.js, React Flow, Tailwind, Claude / Mistral | [Open app](https://ai-agents-sage-ten.vercel.app/) | [`GRAPHIFY`](GRAPHIFY) |
| **JOB HUNTER** | A daily agent that finds tech jobs on company career pages, sorts them into 0–2, 2–4, 4–6 and 6+ years, and posts them to a Telegram channel. Includes a website and a Razorpay subscription flow (currently free to join). | Python, Mistral, Supabase, GitHub Actions, Telegram Bot API, Next.js, Vercel | [Open site](https://job-hunter-kappa-mocha.vercel.app/) | [`FRESHER_JOB_HUNT`](FRESHER_JOB_HUNT) |
| **HahaBot** | A Mistral chatbot with four modes (Funny, Roast, Angry, Einstein). Each mode has its own system prompt and its own UI theme and layout. | Python, Mistral, Streamlit | [Open app](https://haha-funny-bot-h.streamlit.app/) | [`CHATBOT`](CHATBOT) |

## Repository layout

```
AI-Agents/
├── AI WORKFLOW/          Resume Matcher and YouTube Notes (fixed-step LLM workflows); see readme.txt
├── CHATBOT/              HahaBot 4-mode chatbot (Funny / Roast / Angry / Einstein)
├── RAG/                  DocChat AI RAG app
├── travel_planner/       Travel Planner ReAct agent
├── GRAPHIFY/             Code → knowledge graph web app (Next.js); see its README
├── FRESHER_JOB_HUNT/     JOB HUNTER: daily job agent + Telegram channel + website; see its README
├── JOB Agent/            Daily job-search agent with Telegram alerts; see its README
├── MY_PORTFOLIO/         Portfolio website (static HTML/CSS/JS, deployed to GitHub Pages)
├── .github/              Workflows: deploy the portfolio, keep the Streamlit apps awake
├── Nikhil_Kumar_Resume.pdf
└── requirements.txt      Dependencies for HahaBot and DocChat AI
```

## Running the apps locally

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt  # HahaBot + DocChat AI
streamlit run CHATBOT/CHATBOT_APP.py
```

Some apps have their own requirements file:

| App | Install | Run |
|---|---|---|
| Resume Matcher / YouTube Notes | `pip install -r "AI WORKFLOW/requirements.txt"` | `streamlit run "AI WORKFLOW/resume_matcher/app.py"` |
| Travel Planner | `pip install -r travel_planner/requirements.txt` | `streamlit run travel_planner/app.py` |
| GRAPHIFY | `cd GRAPHIFY && npm install` | `npm run dev` |

Put API keys in a `.env` file. `.env` and local Streamlit secrets files are ignored by Git, so keys never go into the repo.

## Deploying on Streamlit Community Cloud

Create a separate app for each one in [Streamlit Community Cloud](https://share.streamlit.io/). Select this repository and the `main` branch, then choose its main file:

| App | Main file | Secrets |
|---|---|---|
| HahaBot | `CHATBOT/CHATBOT_APP.py` | `MISTRAL_API_KEY` |
| DocChat AI | `RAG/RAG.py` | `MISTRAL_API_KEY`, `PINECONE_API_KEY` |
| Resume Matcher | `AI WORKFLOW/resume_matcher/app.py` | `MISTRAL_API_KEY` |
| YouTube Notes | `AI WORKFLOW/youtube_notes/app.py` | `MISTRAL_API_KEY` |
| Travel Planner | `travel_planner/app.py` | `MISTRAL_API_KEY`, `TAVILY_API_KEY`, `OPENWEATHER_API_KEY` |

After creating each app, open **Settings → Secrets** and add its keys in TOML format, for example:

```toml
MISTRAL_API_KEY = "your-mistral-api-key"
PINECONE_API_KEY = "your-pinecone-api-key"
```

DocChat AI connects to the Pinecone index configured in `RAG/RAG.py`. Processing a new document replaces everything in the app's `RAG` namespace, so content indexed earlier is removed.

## Keeping the demos awake

Streamlit Community Cloud puts free apps to sleep when nobody visits them. The [keep-awake workflow](.github/workflows/keep-streamlit-awake.yml) runs every 4 hours. It opens each app in a headless browser and clicks the wake-up button if the app is asleep. To run it by hand, go to **Actions → Keep Streamlit apps awake → Run workflow**. To add a new app, add its URL to `APPS` in [`.github/scripts/keep_awake.py`](.github/scripts/keep_awake.py).

## Portfolio website

The portfolio in [`MY_PORTFOLIO/`](MY_PORTFOLIO) is a single page built with plain HTML, CSS and JavaScript. It needs no build step. The [deploy workflow](.github/workflows/deploy-portfolio.yml) publishes it to GitHub Pages whenever anything in `MY_PORTFOLIO/` changes on `main`. For this to work, the repo's **Settings → Pages → Source** must be set to **GitHub Actions**. To update the resume on the site, replace `MY_PORTFOLIO/Nikhil_Kumar_Resume.pdf` and keep the same filename.
