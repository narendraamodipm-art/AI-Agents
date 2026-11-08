# Fresher Job Hunt: Project Plan

A website where freshers (0–2 years of experience) sign up with their name, email and WhatsApp number and pick the fields they want: AI, Software Engineering, Data Engineering, Full Stack, ML Engineering or Data Analyst. Every day at **10:00 AM IST** an agent finds new fresher jobs and internships (**remote and on-site in India**) and sends each user **10–12 matching openings** with links to apply, by **WhatsApp and email**.

## Decisions (2026-11-08)

| Topic | Decision |
|---|---|
| Frontend | Next.js on Vercel (free Hobby plan) |
| Database | **Supabase** (free plan, Postgres) |
| Channels | **Telegram channel** (automatic, free) + **WhatsApp group** (agent sends the admin a ready-made post to paste, free) + **email** (personal, optional via Resend) |
| Status | ✅ Built (2026-11-08): see [README.md](README.md) for setup |
| Jobs per user per day | **10–12** |
| Locations | **Remote + on-site/office** (India on-site, plus remote roles open to India) |
| Send time | 10:00 AM IST daily |

---

## 0. WhatsApp delivery: free group post (decided 2026-11-08)

Personal WhatsApp messages through the API cost money per recipient (≈ ₹0.86 marketing / ≈ ₹0.13 utility through Meta, more through Twilio). To keep the project **free**, WhatsApp delivery is **one daily post in a WhatsApp group** instead.

- **Group setup:** an admin-only group ("Only admins can send messages"). People join through an **invite link** on the website, never by being added. When it's full (≈ 1,024 members), start a new group; the site shows the current group's link.
- **Daily flow:** at 10:00 IST the agent builds one post with **10–15 jobs grouped by field** (bold headings and apply links; WhatsApp allows long messages) and sends it **to the admin** on Telegram or email. The admin pastes it into the group (about 30 seconds).
- **Not automated on purpose:** there's no official API for posting into normal groups, and automating a personal WhatsApp account (whatsapp-web.js, Baileys, bulk senders) breaks WhatsApp's terms and risks a ban.
- **Privacy:** group members can see each other's numbers. Say so next to the join button, or use a WhatsApp **Community** announcement group, where numbers are hidden, if needed.
- **Effect on the rest of this plan:** the website **doesn't collect WhatsApp numbers**. Meta / WhatsApp Cloud API setup, the webhook and template approval are **not needed**. Sections below that mention WhatsApp API sending are kept only as a future paid upgrade.

**Example daily post:**
```
🎯 *Fresher Jobs — 8 Nov 2026* (0–2 yrs)

🤖 *AI / ML Engineer*
1. ML Engineer Intern — <Company> · Bengaluru
   👉 <apply link>

🛠 *Data Engineer*
2. Data Engineer I — <Company> · Remote
   👉 <apply link>
...
🔔 Get jobs for your field by email: <site>
```

---

## 1. Architecture

```
┌──────────────────────── Vercel (Next.js) ────────────────────────┐
│  /                         Landing page + signup form            │
│  /api/signup               validate → insert into Supabase       │
│  /jobs/[token]             "Your jobs today": all 10–12 links    │◄── WhatsApp link
│  /unsubscribe/[token]      one-click opt-out                     │
│  /api/whatsapp/webhook     receives "STOP" replies from Meta     │
│  /privacy                  what we store and why                 │
└──────────────────────────────────────────────────────────────────┘
                 │ insert / read (server-side keys only)
                 ▼
        ┌──────────────── Supabase (Postgres) ────────────────┐
        │ users · jobs · daily_digests · deliveries            │
        └──────────────────────────────────────────────────────┘
                 ▲ read users, write jobs + deliveries
┌──── GitHub Actions: daily cron (≈04:00 UTC → done by 10:00 IST) ────┐
│  agent/run.py                                                       │
│   1. Load active users from Supabase                                │
│   2. Fetch jobs: Greenhouse / Lever / Ashby / Workday / Adzuna /    │
│      JSearch + Tavily search                                        │
│   3. Keep fresher roles only (rules + Mistral check)                │
│   4. Tag fields (AI, DE, ML, Full Stack, DA, SWE) + remote/on-site  │
│   5. Save new jobs to `jobs` (dedupe by URL)                        │
│   6. Per user: pick 10–12 best matches not sent before              │
│   7. Save the day's list → `daily_digests` (powers /jobs/[token])   │
│   8. Send email (full list) + WhatsApp (summary + link)             │
│   9. Log each send in `deliveries`; alert admin on failures         │
└─────────────────────────────────────────────────────────────────────┘
```

**Why the agent runs on GitHub Actions, not Vercel:** fetching many job feeds and LLM-checking jobs takes minutes. Vercel Hobby functions have short time limits, and Vercel Hobby cron jobs only run at an imprecise time within the hour. GitHub Actions is free, allows long runs and can reuse `JOB Agent/` code. Its cron can start late, so it starts at about 04:00 UTC (9:30 IST) and **sends at 10:00 IST**: the job waits until 10:00 before sending.

**Supabase free plan note:** free projects are **paused after about 1 week with no activity**. The daily agent reads the database every day, which keeps it active.

---

## 2. How each channel delivers 10–12 jobs

**Email:** the full list in one HTML email.
> **🎯 12 new fresher jobs for you: Data Engineer · Data Analyst**
> 1. **Data Engineer Intern**: Databricks · Bengaluru (On-site) · [Apply →](#)
> 2. **Junior Data Analyst**: Razorpay · Remote (India) · [Apply →](#)
> … 12 jobs
> *[Unsubscribe](#)*

**WhatsApp:** a short template message plus a link. WhatsApp template variables **can't contain line breaks**, and the body is capped at **1,024 characters**, so 10–12 links don't fit. The message links to the user's personal page:
> Hi {{1}} 👋 {{2}} new fresher jobs for you today in {{3}}.
> See all and apply: {{4}}
> Reply STOP to unsubscribe.

`{{4}}` = `https://<site>/jobs/<user_token>`, a page listing all of today's jobs with Apply buttons. One message per user per day keeps WhatsApp costs low.

---

## 3. APIs and keys needed

### Required (free WhatsApp-group design: total cost ₹0/month)

| # | Service | What it's for | Free tier | What you need to get |
|---|---|---|---|---|
| 1 | **Supabase** | Database for users, jobs and the daily post | Free plan (≈500 MB DB; pauses after ~1 week of inactivity, but the daily run keeps it active) | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (server and agent only, never in the browser) |
| 2 | **Telegram Bot API** | Sends the ready-made WhatsApp group post **to you** at 10 AM, plus failure alerts | Free (you already have a bot) | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| 3 | **Mistral AI** | Fresher check, field tagging, short job summaries | Free tier (you already have a key) | `MISTRAL_API_KEY` |
| 4 | **Tavily** | Web search for fresher openings at companies without a public job board | ~1,000 credits/month free (you already have a key) | `TAVILY_API_KEY` |
| 5 | **Cloudflare Turnstile** | Stops bots and spam signups on the website | Free | `NEXT_PUBLIC_TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY` |

### Optional

| Service | What it's for | Key |
|---|---|---|
| **Resend** (or Brevo) | Personal daily emails with each user's 10–12 jobs. Free ≈100/day (Brevo ≈300/day), but **needs a domain you own** | `RESEND_API_KEY` |

### Not needed (free group design)
- **Meta WhatsApp Cloud API, Twilio:** only for paid, automatic personal WhatsApp messages. Kept as a future upgrade (section 0).

### Job sources: no key needed

| Source | Endpoint | Notes |
|---|---|---|
| Greenhouse | `boards-api.greenhouse.io/v1/boards/<company>/jobs` | Public JSON, reused from JOB Agent |
| Lever | `api.lever.co/v0/postings/<company>` | Public JSON |
| Ashby | `api.ashbyhq.com/posting-api/job-board/<company>` | Public JSON |
| Workday | `<company>.wd*.myworkdayjobs.com/wday/cxs/...` | Public JSON, reused from JOB Agent |

### Recommended extra job sources (free keys, much better fresher coverage)

| # | Service | What it's for | Free tier | Key |
|---|---|---|---|---|
| 7 | **Adzuna API** | Job search API with **India** listings, filterable by keyword and location | Free developer key (rate-limited) | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` |
| 8 | **JSearch (RapidAPI)** | Aggregates postings from Google for Jobs (LinkedIn, Indeed, Naukri listings and more) through an official API | Small free monthly request quota | `RAPIDAPI_KEY` |

### Optional extra

| Service | What it's for | Cost |
|---|---|---|
| Custom domain | Needed only if you send emails with Resend; also nicer than `*.vercel.app` | ~₹100–900/year, depending on the domain ending |

**Where the keys go:**
- **Vercel environment variables** (the website): Supabase, Turnstile.
- **GitHub repo Secrets** (the daily agent): Supabase, Telegram, Mistral, Tavily, Adzuna, RapidAPI, and Resend if you use email.
- **Local `.env`** for testing (already gitignored).
- Never in code or the repo.

---

## 4. Database (Supabase)

```sql
create table users (
  id               uuid primary key default gen_random_uuid(),
  name             text not null,
  email            text not null unique,
  whatsapp         text unique,                 -- E.164, e.g. +919876543210
  fields           text[] not null,             -- {'data_engineer','data_analyst'}
  work_mode        text[] default '{remote,onsite}',
  channels         text[] default '{email,whatsapp}',
  consent_at       timestamptz not null,
  status           text default 'active',       -- active | unsubscribed
  token            text unique not null,        -- for /jobs/[token] and /unsubscribe/[token]
  created_at       timestamptz default now()
);

create table jobs (
  id          bigserial primary key,
  url         text unique not null,
  title       text, company text, location text,
  work_mode   text,                             -- remote | onsite | hybrid
  fields      text[],
  min_years   int,
  source      text,
  posted_at   timestamptz,
  found_at    timestamptz default now()
);

create table daily_digests (                    -- what each user got each day
  user_id  uuid references users(id) on delete cascade,
  day      date,
  job_ids  bigint[],
  primary key (user_id, day)
);

create table deliveries (                       -- send log, for retries and debugging
  id        bigserial primary key,
  user_id   uuid references users(id) on delete cascade,
  day       date, channel text, status text, error text,
  sent_at   timestamptz default now()
);
```

**Security:** turn on **Row Level Security** for every table with **no public policies**. The website's API routes and the agent use the **service role key on the server only**, so nobody can read the user list from the browser.

**Fields:** `ai_engineer`, `software_engineer`, `data_engineer`, `full_stack`, `ml_engineer`, `data_analyst`.

---

## 5. Job sources and the fresher filter

**Only public job APIs.** No LinkedIn, Naukri or Indeed scraping: it breaks their terms and gets blocked. JSearch reaches those listings legally through its API.

**Fresher filter** (cheap rules first, then the LLM only for unclear cases):
1. Title **includes** one of: intern, internship, trainee, graduate, fresher, junior, associate, entry level, "engineer I", "analyst I", "SDE 1".
2. Title **excludes** one of: senior, sr, lead, principal, staff, manager, architect, II, III.
3. JD experience: regex for `0-1 / 0-2 / 1-2 years`, "no experience". **Reject** if it asks for 3+ years.
4. **Location:** on-site/hybrid in India, **or** remote roles that are open to candidates in India.
5. Unclear cases → Mistral (`ministral-8b`) structured output: `{is_fresher, fields[], work_mode, min_years}`.

**Choosing 10–12 per user:** jobs in the user's fields, not sent to them before, newest first. Mix remote and on-site, and allow at most 2 jobs from the same company. If there are fewer than 10 new matches, send what's available. If there are none, send nothing that day.

---

## 6. Privacy, consent and safety (required)

- **Consent checkbox**, unticked by default: "I agree to receive daily job alerts on WhatsApp and email." Save `consent_at`. Required by WhatsApp's opt-in rules and India's **DPDP Act 2023**.
- **Unsubscribe:** a link in every email, `STOP` on WhatsApp (handled by the webhook), and on the `/jobs/[token]` page.
- **Privacy page:** what's stored, why, and how to delete it.
- **Spam protection:** Turnstile, rate limiting on `/api/signup`, email format and phone (E.164) validation.
- **WhatsApp sending limits:** new WhatsApp business numbers can only message a limited number of unique users per day. The limit rises as your quality rating and business verification improve, so plan gradual growth.

---

## 7. Tech stack

| Part | Choice |
|---|---|
| Frontend | Next.js (App Router) + Tailwind CSS on Vercel |
| Validation | `zod` |
| Database | Supabase (`@supabase/supabase-js` in Next.js, `supabase` Python client in the agent) |
| Agent | Python 3.12 on GitHub Actions |
| LLM / search | Mistral `ministral-8b-latest`, Tavily |
| Job APIs | Greenhouse, Lever, Ashby, Workday, Adzuna, JSearch |
| Messaging | Meta WhatsApp Cloud API, Resend |

---

## 8. Folder structure

```
FRESHER_JOB_HUNT/
├── PLAN.md
├── supabase/schema.sql          tables + RLS (run once in the Supabase SQL editor)
├── web/                         Next.js (Vercel root directory = FRESHER_JOB_HUNT/web)
│   ├── app/
│   │   ├── page.tsx                     landing + signup
│   │   ├── api/signup/route.ts
│   │   ├── api/whatsapp/webhook/route.ts
│   │   ├── jobs/[token]/page.tsx        today's jobs for one user
│   │   ├── unsubscribe/[token]/page.tsx
│   │   └── privacy/page.tsx
│   ├── lib/ (supabase.ts, schema.ts)
│   └── package.json
├── agent/
│   ├── run.py                   entry point (dry-run flag for testing)
│   ├── sources/                 greenhouse.py, lever.py, ashby.py, workday.py, adzuna.py, jsearch.py, tavily.py
│   ├── filters.py               fresher rules + Mistral check + field/work-mode tagging
│   ├── matcher.py               pick 10–12 per user
│   ├── db.py                    Supabase reads/writes
│   ├── notify_email.py
│   ├── notify_whatsapp.py
│   ├── config.py
│   └── requirements.txt
└── scripts/export_csv.py        users → users.csv (local only)

.github/workflows/fresher-job-alerts.yml
```

---

## 9. Build phases

| Phase | Deliverable | Done when |
|---|---|---|
| **1. Database + signup site** | Supabase schema + RLS, landing page, signup form, `/api/signup`, privacy page, Turnstile | A test signup appears in Supabase, duplicates are rejected, and the user list can't be read from the browser |
| **2. Job finder** | `agent/` sources, fresher filter, tagging, saved to `jobs`; dry run | One run finds ≥ 30 real fresher jobs across all 6 fields, with few false positives |
| **3. Email** | Matcher (10–12 per user), Resend email, `/jobs/[token]` page, unsubscribe | Test users get correct emails, and a second run sends no repeats |
| **4. WhatsApp** | Meta setup, template approval, `notify_whatsapp.py`, STOP webhook | A test number receives the daily message with a working link |
| **5. Schedule** | GitHub Actions cron, send at 10:00 IST, failure alert to you | Runs on its own for 3 days in a row |
| **6. Polish** | Email verification, stats on the landing page, CSV export, link from your portfolio | — |

---

## 10. Costs (≈100–300 users)

| Item | Cost |
|---|---|
| Vercel Hobby, Supabase free, GitHub Actions | Free (Vercel Hobby is non-commercial; move to Pro if you monetise) |
| Mistral, Tavily, Adzuna, JSearch | Free tiers |
| Resend | Free up to ~100 emails/day. Above ~100 users, use Brevo (~300/day) or a paid plan |
| Domain | ~₹100–900/year (needed to send email) |
| **WhatsApp Cloud API** | **Paid per message.** 1 message × users × 30 days, so check Meta's current India price and multiply. This is the main running cost. |

---

## 11. Still to decide

1. **Domain name** for the site and email sender. Have one, or buy one?
2. **WhatsApp number:** a spare SIM/number to register with the WhatsApp Cloud API. It can't be your personal WhatsApp number.
3. **Message category:** Meta decides whether the template counts as *utility* or *marketing*, which affects the price. Draft the template text and submit it early.
