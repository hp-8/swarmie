-- =============================================
-- Extend roast_runs with pitch input
-- =============================================
alter table public.roast_runs
  add column if not exists pitch_text       text,
  add column if not exists n_agents_requested int;

-- =============================================
-- Parsed pitch — what the LLM extracted
-- =============================================
create table public.roast_pitches (
  job_id        text primary key references public.roast_runs(job_id) on delete cascade,
  one_liner     text,
  problem       text,
  solution      text,
  target_icp    text,
  pricing       text,
  icp_segments  jsonb default '[]',
  competitors   jsonb default '[]',
  channels      jsonb default '[]',
  founder_ask   text,
  created_at    timestamptz not null default now()
);

-- =============================================
-- Report output — scores, narrative, analysis
-- =============================================
create table public.roast_reports (
  job_id              text primary key references public.roast_runs(job_id) on delete cascade,
  pmf_score           numeric(3,1),
  headline            text,
  narrative           text,
  sentiment_positive  smallint,
  sentiment_neutral   smallint,
  sentiment_negative  smallint,
  action_post         smallint default 0,
  action_comment      smallint default 0,
  action_upvote       smallint default 0,
  action_ignore       smallint default 0,
  top_objections      jsonb default '[]',
  messaging_gaps      jsonb default '[]',
  icp_fit             jsonb default '{}',
  quoted_reactions    jsonb default '[]',
  created_at          timestamptz not null default now()
);

-- =============================================
-- Individual agent reactions
-- =============================================
create table public.roast_reactions (
  id            bigint generated always as identity primary key,
  job_id        text not null references public.roast_runs(job_id) on delete cascade,
  agent_id      text not null,
  archetype_id  text,
  segment       text,
  name          text,
  tone          text,
  action        text,
  reaction_text text,
  sentiment     numeric(4,3),
  objections    jsonb default '[]',

  unique (job_id, agent_id)
);

-- =============================================
-- Indexes for common queries
-- =============================================
create index idx_reports_pmf on public.roast_reports(pmf_score desc);
create index idx_reactions_job on public.roast_reactions(job_id);
create index idx_reactions_action on public.roast_reactions(action);
create index idx_reactions_segment on public.roast_reactions(segment);

-- =============================================
-- RLS — same open policy as existing tables
-- =============================================
alter table public.roast_pitches enable row level security;
alter table public.roast_reports enable row level security;
alter table public.roast_reactions enable row level security;

create policy "anon_insert_pitches" on public.roast_pitches for insert to anon with check (true);
create policy "anon_read_pitches" on public.roast_pitches for select to anon using (true);

create policy "anon_insert_reports" on public.roast_reports for insert to anon with check (true);
create policy "anon_read_reports" on public.roast_reports for select to anon using (true);

create policy "anon_insert_reactions" on public.roast_reactions for insert to anon with check (true);
create policy "anon_read_reactions" on public.roast_reactions for select to anon using (true);

-- =============================================
-- Handy view: one-row-per-run with everything
-- =============================================
create or replace view public.roast_overview as
select
  r.job_id,
  r.fingerprint_id,
  r.status,
  r.n_agents_requested,
  r.agent_count,
  r.total_tokens,
  r.cost_usd,
  r.started_at,
  r.completed_at,
  p.one_liner,
  p.target_icp,
  p.pricing,
  p.icp_segments,
  rp.pmf_score,
  rp.headline,
  rp.sentiment_positive,
  rp.sentiment_neutral,
  rp.sentiment_negative,
  rp.action_post,
  rp.action_comment,
  rp.action_upvote,
  rp.action_ignore,
  d.downloaded_at is not null as pdf_downloaded
from public.roast_runs r
left join public.roast_pitches p on p.job_id = r.job_id
left join public.roast_reports rp on rp.job_id = r.job_id
left join public.pdf_downloads d on d.job_id = r.job_id;
