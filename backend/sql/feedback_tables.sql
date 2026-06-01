-- feedback_tables.sql
-- Run manually in the Supabase SQL editor (Dashboard → SQL Editor → New query).
-- Creates the two feedback tables used by the Swarmie frontend feedback layer.
-- Mirrors the RLS style of existing analytics tables (anon insert enabled).

-- ---------------------------------------------------------------------------
-- objection_feedback
-- Stores per-user thumbs up/down votes on individual objection categories.
-- Unique constraint allows a user to change their vote (upsert on conflict).
-- ---------------------------------------------------------------------------
create table if not exists objection_feedback (
  id              bigint generated always as identity primary key,
  job_id          text not null,
  fingerprint_id  text,
  objection_category text not null,
  vote            smallint not null,        -- +1 or -1
  created_at      timestamptz not null default now(),
  unique (job_id, fingerprint_id, objection_category)
);

alter table objection_feedback enable row level security;

-- Allow anonymous clients to insert AND upsert (update on conflict)
create policy "anon insert objection_feedback"
  on objection_feedback for insert
  to anon
  with check (true);

create policy "anon update objection_feedback"
  on objection_feedback for update
  to anon
  using (true)
  with check (true);

-- ---------------------------------------------------------------------------
-- product_feedback
-- Stores product-level helpful/comment/email feedback from the FeedbackWidget.
-- No unique constraint — each submission is its own row.
-- ---------------------------------------------------------------------------
create table if not exists product_feedback (
  id              bigint generated always as identity primary key,
  job_id          text,
  fingerprint_id  text,
  helpful         boolean,
  comment         text,
  email           text,
  trigger         text,                     -- 'button' | 'popup'
  created_at      timestamptz not null default now()
);

alter table product_feedback enable row level security;

create policy "anon insert product_feedback"
  on product_feedback for insert
  to anon
  with check (true);
