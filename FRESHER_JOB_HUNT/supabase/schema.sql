-- Fresher Job Hunt: database schema (paid Telegram channel)
-- Run once in Supabase: Dashboard → SQL Editor → New query → paste → Run.
-- Row Level Security is ON with no public policies: only the server (service role key) can read/write.

-- One row per person who starts a subscription.
create table if not exists public.subscribers (
  id                        uuid primary key default gen_random_uuid(),
  token                     text not null unique,        -- links the payment to the bot: t.me/<bot>?start=<token>
  email                     text,
  phone                     text,
  razorpay_subscription_id  text not null unique,
  status                    text not null default 'created'
                            check (status in ('created', 'active', 'past_due', 'cancelled', 'expired')),
  paid_until                timestamptz,                 -- access ends here unless a renewal arrives
  telegram_user_id          bigint unique,               -- set when they open the bot after paying
  telegram_username         text,
  joined_at                 timestamptz,
  removed_at                timestamptz,                 -- when the daily run removed them from the channel
  created_at                timestamptz not null default now(),
  updated_at                timestamptz not null default now()
);
create index if not exists subscribers_expiry_idx on public.subscribers (paid_until) where removed_at is null;

-- One row per payment attempt. The unique payment ID stops a repeated Razorpay webhook being counted twice.
create table if not exists public.payments (
  id                        uuid primary key default gen_random_uuid(),
  subscriber_id             uuid not null references public.subscribers (id) on delete restrict,
  razorpay_payment_id       text not null unique,
  razorpay_subscription_id  text not null,
  amount_paise              integer not null check (amount_paise >= 0),   -- ₹99 = 9900
  currency                  text not null default 'INR',
  status                    text not null check (status in ('captured', 'failed', 'refunded')),
  method                    text,                        -- upi, card, netbanking, ...
  paid_at                   timestamptz,
  raw                       jsonb,                       -- the full Razorpay event, for audits and disputes
  created_at                timestamptz not null default now()
);
create index if not exists payments_subscriber_idx on public.payments (subscriber_id, created_at desc);

-- Jobs and daily posts live here, not in the public GitHub repo, so the paid list stays private.
create table if not exists public.jobs (
  id          bigserial primary key,
  url         text not null unique,
  title       text not null,
  company     text not null,
  location    text,
  work_mode   text,                                      -- remote | onsite | hybrid
  fields      text[] not null default '{}',
  min_years   int,
  experience  text,                                      -- section: 0-2 | 2-4 | 4-6 | 6+
  source      text,
  posted_at   date,
  found_at    timestamptz not null default now(),
  posted_on   date                                       -- day it went out (null = not yet)
);
create index if not exists jobs_found_at_idx on public.jobs (found_at desc);
create index if not exists jobs_posted_on_idx on public.jobs (posted_on);

create table if not exists public.daily_posts (
  day         date primary key,
  job_ids     bigint[] not null,
  jobs        jsonb not null,                            -- full list, for the paid channel
  teaser      jsonb not null default '[]',               -- the few jobs shown publicly
  created_at  timestamptz not null default now()
);

alter table public.subscribers  enable row level security;
alter table public.payments     enable row level security;
alter table public.jobs         enable row level security;
alter table public.daily_posts  enable row level security;
-- No policies on purpose: the anon/public key can't read or write anything.

-- Only the server's service role gets access. This is needed when "Automatically expose new tables" is off.
grant usage on schema public to service_role;
grant select, insert, update, delete on public.subscribers, public.payments, public.jobs, public.daily_posts to service_role;
grant usage, select on sequence public.jobs_id_seq to service_role;
