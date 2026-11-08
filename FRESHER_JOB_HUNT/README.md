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

- posts them to a **Telegram channel** automatically (one message per section)
- sends **you** a ready-made **WhatsApp** post to paste into your group (free)
- emails each subscriber the jobs for their own fields and experience levels (optional, needs Resend)
- shows them on the website's **Today** page

```
FRESHER_JOB_HUNT/
├── web/        Next.js website (signup, today's jobs, unsubscribe, privacy) → Vercel
├── agent/      Python daily agent → GitHub Actions (.github/workflows/fresher-job-alerts.yml)
├── supabase/   schema.sql: database tables
└── PLAN.md     design decisions
```

## Setup

### 1. Supabase (database, free)
1. Create a project at https://supabase.com.
2. Go to **SQL Editor → New query**, paste [`supabase/schema.sql`](supabase/schema.sql) and click **Run**.
3. Go to **Project Settings → API** and copy the **Project URL** and the **service_role** key (keep it secret).

### 2. Telegram channel (free, automatic posting)
1. Create a public channel. Ours is **Tech Jobs India: Daily**, [`@techjobsdaily_in`](https://t.me/techjobsdaily_in).
2. Add your bot (the one in `TELEGRAM_BOT_TOKEN`) as an **admin** with "Post messages" permission.
3. The channel ID is `@techjobsdaily_in`.

### 3. WhatsApp group (free, you paste once a day)
Create the group and set **Group settings → Send messages → Only admins**. Copy the invite link for the website. Every morning the agent sends you the post on Telegram: copy it and paste it into the group.

### 4. Website on Vercel
1. Go to https://vercel.com → **Add New → Project** → import this GitHub repo.
2. Set **Root Directory** to `FRESHER_JOB_HUNT/web`. The framework is detected as Next.js.
3. Add these **Environment Variables**:

| Name | Value |
|---|---|
| `SUPABASE_URL` | from step 1 |
| `SUPABASE_SERVICE_ROLE_KEY` | from step 1 |
| `NEXT_PUBLIC_TELEGRAM_URL` | `https://t.me/techjobsdaily_in` |
| `NEXT_PUBLIC_WHATSAPP_GROUP_URL` | your group invite link |
| `NEXT_PUBLIC_TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY` | optional: Cloudflare Turnstile spam protection |

4. Click **Deploy**. `NEXT_PUBLIC_*` values are built into the page, so **redeploy after changing them**.

### 5. Daily agent on GitHub Actions
In the GitHub repo go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Required | Value |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | ✅ | from step 1 |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | ✅ | your bot, and your own chat ID (receives the WhatsApp post and run summaries) |
| `TELEGRAM_CHANNEL_ID` | ✅ | `@techjobsdaily_in` |
| `FRESHER_SITE_URL` | ✅ | your Vercel URL, e.g. `https://fresher-job-hunt.vercel.app` |
| `MISTRAL_API_KEY`, `TAVILY_API_KEY` | ✅ | your keys |
| `RESEND_API_KEY`, `EMAIL_FROM` | optional | personal emails (`EMAIL_FROM` like `Fresher Jobs <jobs@yourdomain.com>`; needs a verified domain) |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `RAPIDAPI_KEY` | optional | more job sources (Adzuna India, JSearch) |

The workflow starts at 9:30 AM IST, finds jobs, then **waits until 10:00 AM** to post. To test it, go to **Actions → Fresher job alerts → Run workflow**, which posts right away.

## Run locally

```powershell
# agent: dry run finds jobs and prints the post; nothing is sent. It writes agent/state/preview_post.json,
# which the local website shows when Supabase isn't configured.
.\.venv\Scripts\python.exe -m pip install -r FRESHER_JOB_HUNT/agent/requirements.txt
.\.venv\Scripts\python.exe FRESHER_JOB_HUNT/agent/run.py --dry-run

# website
cd FRESHER_JOB_HUNT/web
copy .env.example .env.local     # fill in values
npm install
npm run dev                       # http://localhost:3000
```

The agent reads keys from `FRESHER_JOB_HUNT/.env`. Without Supabase keys it uses a local test file (`agent/state/`). On GitHub Actions it refuses to run without Supabase, so it never re-posts old jobs.

## Tuning
Everything is in [`agent/config.py`](agent/config.py): jobs per section, the experience sections (`EXPERIENCE`), fields and their keywords, title rules for each section, locations, and the company career sites to scan. Add a company by adding its Greenhouse / Lever / Ashby board name or Workday site.
