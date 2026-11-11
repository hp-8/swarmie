-- archive_analytics.sql
-- Run ONCE in the Supabase SQL editor before launching the new version.
-- Copies every analytics table into the `archive` schema (suffix _v1), checks
-- the copies are complete, then empties the live tables. Billing tables
-- (purchases, credit_ledger) are not touched.
--
-- `archive` is not exposed through the Supabase API, so browser keys can't
-- reach it. Read it from the SQL editor: select * from archive.roast_runs_v1;
-- Undo: insert the rows back from archive.*_v1 into public.*.

begin;

create schema if not exists archive;
revoke all on schema archive from anon, authenticated;

do $$
declare
  t text;
  live bigint;
  copied bigint;
begin
  foreach t in array array[
    'devices', 'roast_runs', 'roast_pitches', 'roast_reports',
    'roast_reactions', 'pdf_downloads', 'objection_feedback', 'product_feedback'
  ] loop
    execute format('create table archive.%I as table public.%I', t || '_v1', t);
    execute format('select count(*) from public.%I', t) into live;
    execute format('select count(*) from archive.%I', t || '_v1') into copied;
    if live <> copied then
      raise exception 'Copy of % incomplete (% of % rows). Nothing changed.', t, copied, live;
    end if;
    raise notice 'archived %: % rows', t, copied;
  end loop;
end $$;

-- One statement so foreign keys between these tables don't block it.
truncate public.pdf_downloads, public.roast_reactions, public.roast_reports,
         public.roast_pitches, public.roast_runs, public.devices,
         public.objection_feedback, public.product_feedback;

commit;

-- Row counts in the archive:
select 'devices' as t, count(*) from archive.devices_v1
union all select 'roast_runs', count(*) from archive.roast_runs_v1
union all select 'roast_pitches', count(*) from archive.roast_pitches_v1
union all select 'roast_reports', count(*) from archive.roast_reports_v1
union all select 'roast_reactions', count(*) from archive.roast_reactions_v1
union all select 'pdf_downloads', count(*) from archive.pdf_downloads_v1
union all select 'objection_feedback', count(*) from archive.objection_feedback_v1
union all select 'product_feedback', count(*) from archive.product_feedback_v1;
