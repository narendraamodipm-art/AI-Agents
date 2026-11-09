# Fresher Job Hunt

Free daily tech job alerts in AI, ML, Data Engineering, Data Analytics, Full Stack and Software Engineering, covering remote and office roles in India, in four experience sections:

| Section | Who it's for |
|---|---|
| 🎓 0–2 yrs | Freshers & interns |
| 🚀 2–4 yrs | Early career |
| ⭐ 4–6 yrs | Mid-level |
| 🏆 6+ yrs | Senior & lead |

A job goes in the section that contains the minimum years it asks for. A Senior / Lead / Principal / Manager title sets the lowest section it can go in. Jobs that state no years are placed by title, or by Mistral when the title doesn't say.

Every day at **10:00 AM IST** an agent finds new jobs on company career pages and job boards, picks **10–12 per section**, and:

- posts them to the **Telegram channel** [`@techjobsdaily_in`](https://t.me/techjobsdaily_in) (one message per section)
- sends **you** a ready-made **WhatsApp** post to paste into a group if you run one (free)
- shows them on the website

There are no accounts, signup forms or database. People join the Telegram channel.

```
FRESHER_JOB_HUNT/
├── web/        Next.js website (Telegram link, today's jobs, privacy) → Vercel
├── agent/      Python daily agent → GitHub Actions (.github/workflows/fresher-job-alerts.yml)
├── data/       jobs.json + latest_post.json, committed by the daily run
└── PLAN.md     original design notes (written before signup and Supabase were removed)
```

`data/jobs.json` remembers every job seen in the last 30 days so nothing is posted twice. `data/latest_post.json` is today's post; the website reads it from GitHub, so new jobs appear without a redeploy.

## Setup

### 1. Telegram channel (free, automatic posting)
1. Create a public channel. Ours is **Tech Jobs India: Daily**, [`@techjobsdaily_in`](https://t.me/techjobsdaily_in).
2. Add your bot (the one in `TELEGRAM_BOT_TOKEN`) as an **admin** with "Post messages" permission.

### 2. Website on Vercel
1. Go to https://vercel.com → **Add New → Project** → import this GitHub repo.
2. Set **Root Directory** to `FRESHER_JOB_HUNT/web`. The framework is detected as Next.js.
3. Click **Deploy**. No environment variables are needed.

### 3. Daily agent on GitHub Actions
In the GitHub repo go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Required | Value |
|---|---|---|
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | ✅ | your bot, and your own chat ID (receives the WhatsApp post and run summaries) |
| `TELEGRAM_CHANNEL_ID` | ✅ | `@techjobsdaily_in` |
| `FRESHER_SITE_URL` | ✅ | your Vercel URL, e.g. `https://fresher-job-hunt.vercel.app` |
| `MISTRAL_API_KEY`, `TAVILY_API_KEY` | ✅ | your keys |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `RAPIDAPI_KEY` | optional | more job sources (Adzuna India, JSearch) |

The workflow starts at 9:30 AM IST, finds jobs, then **waits until 10:00 AM** to post. To test it, go to **Actions → Fresher job alerts → Run workflow**, which posts right away.

## Run locally

```powershell
# agent: dry run finds jobs and prints the post; nothing is sent. It writes agent/state/preview_post.json,
# which the local website shows instead of the published post.
.\.venv\Scripts\python.exe -m pip install -r FRESHER_JOB_HUNT/agent/requirements.txt
.\.venv\Scripts\python.exe FRESHER_JOB_HUNT/agent/run.py --dry-run

# website
cd FRESHER_JOB_HUNT/web
npm install
npm run dev                       # http://localhost:3000
```

The agent reads keys from `FRESHER_JOB_HUNT/.env`.

## Tuning
Everything is in [`agent/config.py`](agent/config.py): jobs per section, the experience sections (`EXPERIENCE`), fields and their keywords, title rules for each section, locations, and the company career sites to scan. Add a company by adding its Greenhouse / Lever / Ashby board name or Workday site.
