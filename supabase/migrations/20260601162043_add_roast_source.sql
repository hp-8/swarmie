-- Phase 2 deck intelligence: tag each run by input source (text | deck).
-- Additive + nullable, so existing rows and old clients keep working.

alter table public.roast_runs
  add column if not exists source text;
