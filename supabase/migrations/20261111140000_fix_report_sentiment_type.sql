-- Sentiment split is a percentage with one decimal (e.g. 33.3), but the
-- columns were smallint, so every roast_reports write failed and the table
-- stayed empty. Widen to numeric(4,1) (0.0 – 100.0).

-- roast_overview reads these columns, so drop it first and recreate it after.
drop view if exists public.roast_overview;

alter table public.roast_reports
  alter column sentiment_positive type numeric(4,1),
  alter column sentiment_neutral  type numeric(4,1),
  alter column sentiment_negative type numeric(4,1);

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
