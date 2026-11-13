# Fresher Job Hunt

Daily tech job alerts in AI, ML, Data Engineering, Data Analytics, Full Stack and Software Engineering, covering remote and office roles in India, in four experience sections:

| Section | Who it's for |
|---|---|
| 🎓 0–2 yrs | Freshers & interns |
| 🚀 2–4 yrs | Early career |
| ⭐ 4–6 yrs | Mid-level |
| 🏆 6+ yrs | Senior & lead |

A job goes in the section that contains the minimum years it asks for. A Senior / Lead / Principal / Manager title sets the lowest section it can go in. Jobs that state no years are placed by title, or by Mistral when the title doesn't say.

Twice a day, at **10:00 AM and 6:00 PM IST**, an agent finds new jobs on company career pages and job boards, picks **10–12 per section**, posts them to a **private Telegram channel** for paying members (₹99/month through Razorpay), and shows one sample job per section on the website.

```
FRESHER_JOB_HUNT/
├── web/        Next.js website: subscribe, sample jobs, Razorpay and Telegram webhooks → Vercel
├── agent/      Python daily agent → GitHub Actions (.github/workflows/fresher-job-alerts.yml)
├── supabase/   schema.sql: subscribers, payments, jobs, daily_posts
└── PLAN.md     original design notes (some of it is out of date)
```

## How a subscription works

1. The visitor pays on the website. The checkout signature is verified on the server.
2. They open the bot, which links their Telegram account and sends a join-request invite.
3. The bot approves the request only for an account with paid access, so a forwarded invite is useless.
4. Razorpay webhooks extend access each month. The daily run removes members 2 days after their paid date.
5. Sending `/cancel` to the bot stops renewals. Access continues until the end of the paid period.

## Setup

1. **Supabase:** create a project and run [`supabase/schema.sql`](supabase/schema.sql) in the SQL Editor.
2. **Razorpay:** create API keys and a ₹99 monthly plan.
3. **Telegram:** create a private channel and add the bot as an admin with Post Messages, Invite Users and Ban Users.
4. **Vercel:** import this repo, set **Root Directory** to `FRESHER_JOB_HUNT/web`, add the variables in [`web/.env.example`](web/.env.example), and deploy.
5. **Webhooks**, using your live URL:
   - Razorpay → Webhooks: `https://<site>/api/razorpay/webhook`, using `RAZORPAY_WEBHOOK_SECRET`. Events: `subscription.charged`, `subscription.pending`, `subscription.halted`, `subscription.cancelled`, `subscription.completed`.
   - Telegram `setWebhook`: `https://<site>/api/telegram/webhook`, with `secret_token` set to `TELEGRAM_WEBHOOK_SECRET` and `allowed_updates` set to `message` and `chat_join_request`.
6. **GitHub Actions secrets** (Settings → Secrets and variables → Actions):

| Secret | Required | Value |
|---|---|---|
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | ✅ | your bot, and your own chat ID (receives run summaries) |
| `TELEGRAM_PAID_CHANNEL_ID` | ✅ | the private channel's numeric ID |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | ✅ | from Supabase |
| `FRESHER_SITE_URL` | ✅ | your live website URL |
| `MISTRAL_API_KEY`, `TAVILY_API_KEY` | ✅ | your keys |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `RAPIDAPI_KEY` | optional | more job sources |

The workflow runs twice a day, starting at 9:30 AM and 5:30 PM IST. Each run finds jobs, then **waits until 10:00 AM or 6:00 PM** to post. Go to **Actions → Fresher job alerts → Run workflow** to post right away.

## Run locally

```powershell
# agent: dry run finds jobs and prints the post; nothing is sent. It writes agent/state/preview_post.json,
# which the local website shows as its sample jobs.
.\.venv\Scripts\python.exe -m pip install -r FRESHER_JOB_HUNT/agent/requirements.txt
.\.venv\Scripts\python.exe FRESHER_JOB_HUNT/agent/run.py --dry-run

# website
cd FRESHER_JOB_HUNT/web
copy .env.example .env.local     # fill in values
npm install
npm run dev                       # http://localhost:3000
```

The agent reads keys from `FRESHER_JOB_HUNT/.env`.

## Tuning
Everything is in [`agent/config.py`](agent/config.py): jobs per section, sample jobs per section, the grace period, the experience sections (`EXPERIENCE`), fields and their keywords, title rules, locations, and the company career sites to scan.
