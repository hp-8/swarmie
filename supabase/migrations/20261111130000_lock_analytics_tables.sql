-- Analytics now flows through the backend (/api/analytics, service-role key).
-- Remove every browser (anon/authenticated) policy and privilege on these
-- tables, so the public key can't read pitches or overwrite rows.
-- Apply AFTER the backend + frontend with /api/analytics are deployed.
-- service_role bypasses RLS and is unaffected.

do $$
declare
  t text;
  pol record;
begin
  foreach t in array array[
    'devices', 'roast_runs', 'pdf_downloads', 'roast_pitches',
    'roast_reports', 'roast_reactions', 'objection_feedback', 'product_feedback'
  ] loop
    for pol in select policyname from pg_policies where schemaname = 'public' and tablename = t loop
      execute format('drop policy %I on public.%I', pol.policyname, t);
    end loop;
    execute format('alter table public.%I enable row level security', t);
    execute format('revoke all on public.%I from anon, authenticated', t);
  end loop;
end $$;
