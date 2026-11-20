-- Tag each run by where it was started: 'web' (the site) or 'mcp' (the Claude connector).
-- Distinct from `source`, which is the input type (text | deck).
alter table public.roast_runs
  add column if not exists channel text not null default 'web';
