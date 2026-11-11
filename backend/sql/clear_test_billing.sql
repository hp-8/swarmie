-- clear_test_billing.sql
-- Run ONCE in the Supabase SQL editor, right after switching STRIPE_MODE=live
-- and before the first real sale. Not a migration: it deletes data.
--
-- Removes everything bought, spent or refunded with test-mode credits.
-- Manual 'grant' rows (credits you gave out by hand) are kept.
-- Aborts without touching anything if a live purchase already exists.

begin;

do $$
begin
  if exists (select 1 from public.purchases where stripe_session_id like 'cs_live_%') then
    raise exception 'Live purchases exist. Aborting so no real data is deleted.';
  end if;
end $$;

-- Preview: what is about to go.
select reason, count(*) as rows, sum(delta) as credits
from public.credit_ledger
where reason <> 'grant'
group by reason;

delete from public.credit_ledger where reason <> 'grant';
delete from public.purchases;  -- all test-mode: guarded above

commit;
