# GCC Job Agent

Every morning it finds **new data-engineering jobs at Global Capability Centres (GCCs) in India**,
scores each one against your resume, and sends you a Telegram shortlist. Reply `APPLY 8 15` and it
writes a tailored cover letter + resume tips for those jobs and sends you the apply links. You do the
final submit, so nothing is ever sent in your name without you seeing it.

```
            ┌─ Tavily news ──► Mistral picks out newly announced GCCs ──► Tavily: jobs at them ─┐
 daily ─────┤                                                                                   ├─► SQLite
            └─ 26 Workday + 9 Greenhouse GCC career feeds (title / India / last-3-days filter) ─┘
                                             │
             score each new job (Mistral: JD → skills → gap, embeddings similarity, Python score)
                                             │
             fit ≥ 50 → Telegram: "#8 Data Engineer — PayPal, Fit 98/100 … Reply APPLY 8"
                                             │
 you reply ──► APPLY 8 → cover letter + resume tips (dashboard) + apply link on Telegram
               SKIP 3 · APPLIED 8 · LIST
```

## Files

| File | What it does |
|---|---|
| `config.py` | Everything you might tune: search terms, title filters, GCC career sites, thresholds |
| `sources.py` | Fetches jobs from Workday / Greenhouse feeds and Tavily search |
| `matching.py` | Mistral steps: resume profile, job scoring, cover letter, new-GCC extraction |
| `store.py` | SQLite database in `data/jobs.db` |
| `telegram_bot.py` | Telegram bot: send messages + read your replies |
| `agent.py` | `run` (daily pipeline), `replies` / `listen` (act on your replies), `chat-id` (setup) |
| `dashboard.py` | Streamlit UI: browse matches, approve, read cover letters, mark applied |
| `run_agent.bat` | Launcher for Windows Task Scheduler; logs to `data/agent.log` |
| `schedule_tasks.ps1` | Registers the daily 9:00 run + 15-minute reply check in Task Scheduler |

## Run it

```powershell
.\.venv\Scripts\python.exe -m pip install -r "JOB Agent/requirements.txt"
.\.venv\Scripts\python.exe "JOB Agent/agent.py" run        # find + score + Telegram
.\.venv\Scripts\python.exe "JOB Agent/agent.py" replies    # act on your replies once
.\.venv\Scripts\python.exe "JOB Agent/agent.py" listen     # answer replies instantly (Ctrl+C stops)
.\.venv\Scripts\streamlit.exe run "JOB Agent/dashboard.py"
```

Keys live in `JOB Agent/.env` (used instead of the repo-root `.env`): `MISTRAL_API_KEY`,
`TAVILY_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

## Telegram setup (free, ~2 minutes)

1. In Telegram, open **@BotFather**, send `/newbot`, pick a name and a username ending in `bot`.
2. Copy the token it gives you into `TELEGRAM_BOT_TOKEN`.
3. Open your new bot and press **Start** (sends `/start`).
4. Run `agent.py chat-id` and copy the printed `TELEGRAM_CHAT_ID=…` line into `.env`.

The agent only acts on messages from that chat id, so other people messaging your bot are ignored.
Telegram keeps unread replies for 24 hours, so the 15-minute reply check never misses one.

## Notes

- Jobs are scored with `ministral-8b`; it occasionally lists a skill as missing that is on your resume.
  Check the matched/missing chips before trusting a score.
- Web-search jobs (from newly announced GCCs) without a readable job description are dropped.
- The first run looks back 7 days; later runs only pick up jobs posted in the last 3 days that aren't
  already in the database.
- Add more GCCs to `WORKDAY` / `GREENHOUSE` in `config.py` (the URL pattern is in the comments).
