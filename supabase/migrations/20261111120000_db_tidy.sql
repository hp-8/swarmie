-- Tidy pass: close a data leak, fix a double-counting view, drop indexes no
-- query uses. No table or column is dropped; no row is changed.

-- 1. roast_overview ran with its owner's rights, so the browser (anon) key
--    could read every user's runs through it, bypassing RLS. Run it with the
--    caller's rights instead, and stop exposing it to browser keys.
--    It also joined pdf_downloads directly, so a run downloaded twice showed
--    up as two rows; use EXISTS so each run is one row.
drop view if exists public.roast_overview;  -- column list changes; replace can't
create view public.roast_overview
with (security_invoker = true) as
select
  r.job_id,
  r.fingerprint_id,
  r.status,
  r.swarm_type,
  r.source,
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
  exists (select 1 from public.pdf_downloads d where d.job_id = r.job_id) as pdf_downloaded
from public.roast_runs r
left join public.roast_pitches p on p.job_id = r.job_id
left join public.roast_reports rp on rp.job_id = r.job_id;

revoke all on public.roast_overview from anon, authenticated;

-- 2. pdf_downloads is insert-only from the browser; nothing reads it back.
drop policy if exists "anon_read_downloads" on public.pdf_downloads;

-- 3. Indexes nothing queries. Each one slows every insert of up to 500
--    reaction rows per run.
--    idx_reactions_job duplicates the unique (job_id, agent_id) index.
drop index if exists public.idx_reactions_job;
drop index if exists public.idx_reactions_action;
drop index if exists public.idx_reactions_segment;
drop index if exists public.idx_reports_pmf;
drop index if exists public.idx_roast_runs_swarm_type;
