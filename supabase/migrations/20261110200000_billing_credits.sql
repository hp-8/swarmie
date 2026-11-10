-- Billing: review credits bought in packs via Stripe Checkout.
--
-- Balance is the sum of an append-only ledger. Every mutation carries a unique
-- `ref`, so webhook retries, double clicks and refund races are idempotent.
-- Only the backend (service role) touches these tables; RLS is on with no
-- policies, so browser (anon/authenticated) keys get no access at all.

create table if not exists public.purchases (
  id                bigserial primary key,
  user_id           uuid not null references auth.users(id) on delete cascade,
  pack              text not null,
  credits           integer not null check (credits > 0),
  amount_cents      integer not null check (amount_cents >= 0),
  currency          text not null default 'usd',
  launch_price      boolean not null default false,
  stripe_session_id text not null unique,
  created_at        timestamptz not null default now()
);

create table if not exists public.credit_ledger (
  id         bigserial primary key,
  user_id    uuid not null references auth.users(id) on delete cascade,
  delta      integer not null check (delta <> 0),
  reason     text not null check (reason in ('purchase', 'review', 'refund', 'grant')),
  ref        text not null unique,
  created_at timestamptz not null default now()
);

create index if not exists credit_ledger_user_idx on public.credit_ledger (user_id);
create index if not exists purchases_user_idx on public.purchases (user_id);

alter table public.purchases enable row level security;
alter table public.credit_ledger enable row level security;

create or replace function public.credit_balance(p_user uuid)
returns integer
language sql stable security definer set search_path = public
as $$
  select coalesce(sum(delta), 0)::integer from public.credit_ledger where user_id = p_user;
$$;

-- Spend one credit for a review. Serialized per user (advisory lock) so two
-- concurrent reviews can never both spend the last credit. Returns false when
-- the balance is zero; true when charged or already charged for this ref.
create or replace function public.consume_credit(p_user uuid, p_ref text)
returns boolean
language plpgsql security definer set search_path = public
as $$
begin
  perform pg_advisory_xact_lock(hashtext(p_user::text));
  if exists (select 1 from public.credit_ledger where ref = p_ref) then
    return true;
  end if;
  if public.credit_balance(p_user) < 1 then
    return false;
  end if;
  insert into public.credit_ledger (user_id, delta, reason, ref) values (p_user, -1, 'review', p_ref);
  return true;
end;
$$;

-- Return a credit for a review that failed or was cancelled. Only refunds a
-- charge that exists, and only once.
create or replace function public.refund_credit(p_user uuid, p_ref text)
returns boolean
language plpgsql security definer set search_path = public
as $$
begin
  if not exists (select 1 from public.credit_ledger where ref = p_ref and delta < 0 and user_id = p_user) then
    return false;
  end if;
  insert into public.credit_ledger (user_id, delta, reason, ref)
  values (p_user, 1, 'refund', 'refund:' || p_ref)
  on conflict (ref) do nothing;
  return found;
end;
$$;

-- Record a paid Checkout session and add its credits, exactly once per session.
create or replace function public.grant_purchase(
  p_user uuid, p_pack text, p_credits integer, p_amount_cents integer,
  p_currency text, p_launch boolean, p_session text
)
returns boolean
language plpgsql security definer set search_path = public
as $$
begin
  insert into public.purchases (user_id, pack, credits, amount_cents, currency, launch_price, stripe_session_id)
  values (p_user, p_pack, p_credits, p_amount_cents, p_currency, p_launch, p_session)
  on conflict (stripe_session_id) do nothing;
  if not found then
    return false;  -- webhook retry: already granted
  end if;
  insert into public.credit_ledger (user_id, delta, reason, ref)
  values (p_user, p_credits, 'purchase', 'purchase:' || p_session);
  return true;
end;
$$;

-- Paying buyers who got a launch price (the "first 100 buyers" offer).
create or replace function public.launch_buyers_count()
returns integer
language sql stable security definer set search_path = public
as $$
  select count(distinct user_id)::integer from public.purchases where launch_price;
$$;

revoke all on function public.credit_balance(uuid) from public, anon, authenticated;
revoke all on function public.consume_credit(uuid, text) from public, anon, authenticated;
revoke all on function public.refund_credit(uuid, text) from public, anon, authenticated;
revoke all on function public.grant_purchase(uuid, text, integer, integer, text, boolean, text) from public, anon, authenticated;
revoke all on function public.launch_buyers_count() from public, anon, authenticated;
