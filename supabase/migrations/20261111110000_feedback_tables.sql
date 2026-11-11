-- Bring the feedback tables (previously created by hand from
-- backend/sql/feedback_tables.sql) under migrations. Idempotent: safe on a
-- database where they already exist.

create table if not exists public.objection_feedback (
  id                 bigint generated always as identity primary key,
  job_id             text not null,
  fingerprint_id     text,
  objection_category text not null,
  vote               smallint not null check (vote in (-1, 1)),
  created_at         timestamptz not null default now(),
  unique (job_id, fingerprint_id, objection_category)
);

create table if not exists public.product_feedback (
  id             bigint generated always as identity primary key,
  job_id         text,
  fingerprint_id text,
  helpful        boolean,
  comment        text,
  email          text,
  trigger        text,
  created_at     timestamptz not null default now()
);

alter table public.objection_feedback enable row level security;
alter table public.product_feedback enable row level security;

drop policy if exists "anon insert objection_feedback" on public.objection_feedback;
drop policy if exists "anon update objection_feedback" on public.objection_feedback;
drop policy if exists "anon insert product_feedback" on public.product_feedback;

create policy "anon insert objection_feedback" on public.objection_feedback
  for insert to anon with check (true);
create policy "anon update objection_feedback" on public.objection_feedback
  for update to anon using (true) with check (true);
create policy "anon insert product_feedback" on public.product_feedback
  for insert to anon with check (true);
