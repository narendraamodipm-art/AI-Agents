-- Fresher Job Hunt: database schema
-- Run once in Supabase: Dashboard → SQL Editor → New query → paste → Run.
-- Row Level Security is ON with no public policies: only the server (service role key) can read/write.

create table if not exists public.users (
  id           uuid primary key default gen_random_uuid(),
  name         text not null check (char_length(name) between 2 and 80),
  email        text not null unique,
  phone        text check (phone ~ '^\+[1-9][0-9]{7,14}$'),   -- optional, E.164 (e.g. +919876543210)
  fields       text[] not null,
  work_modes   text[] not null default '{remote,onsite}',
  experience   text[] not null default '{0-2}',  -- sections they want: 0-2 | 2-4 | 4-6 | 6+
  email_alerts boolean not null default true,
  consent_at   timestamptz not null,
  status       text not null default 'active' check (status in ('active', 'unsubscribed')),
  token        text not null unique,            -- for /unsubscribe/<token>
  created_at   timestamptz not null default now()
);

-- Upgrades for databases created before these columns existed (safe to re-run).
alter table public.users add column if not exists phone text;
alter table public.users add column if not exists experience text[] not null default '{0-2}';

create table if not exists public.jobs (
  id          bigserial primary key,
  url         text not null unique,
  title       text not null,
  company     text not null,
  location    text,
  work_mode   text,                             -- remote | onsite | hybrid
  fields      text[] not null default '{}',
  min_years   int,
  experience  text,                             -- section: 0-2 | 2-4 | 4-6 | 6+
  source      text,
  posted_at   date,
  found_at    timestamptz not null default now(),
  posted_on   date                              -- day it went out in the daily post (null = not yet)
);
alter table public.jobs add column if not exists experience text;
create index if not exists jobs_found_at_idx on public.jobs (found_at desc);
create index if not exists jobs_posted_on_idx on public.jobs (posted_on);

create table if not exists public.daily_posts (
  day            date primary key,
  job_ids        bigint[] not null,
  jobs           jsonb not null,                -- snapshot shown on the website's "Today" page
  telegram_text  text,
  whatsapp_text  text,
  created_at     timestamptz not null default now()
);

alter table public.users        enable row level security;
alter table public.jobs         enable row level security;
alter table public.daily_posts  enable row level security;
-- No policies on purpose: the anon/public key can't read or write anything.
