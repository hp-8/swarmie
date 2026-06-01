-- Phase 2: tag each run with which swarm produced it (validate | investor | …).
-- Additive + nullable-with-default, so existing rows and old clients keep working.

alter table public.roast_runs
  add column if not exists swarm_type text not null default 'validate';

create index if not exists idx_roast_runs_swarm_type on public.roast_runs(swarm_type);
