-- The billing migration revoked EXECUTE from public/anon/authenticated to keep
-- browser keys out. In projects where service_role only had EXECUTE through
-- PUBLIC, that also locked out the backend ("permission denied for function",
-- 42501). Grant the backend role explicitly; browser roles stay revoked.

grant execute on function public.credit_balance(uuid) to service_role;
grant execute on function public.consume_credit(uuid, text) to service_role;
grant execute on function public.refund_credit(uuid, text) to service_role;
grant execute on function public.grant_purchase(uuid, text, integer, integer, text, boolean, text) to service_role;
grant execute on function public.launch_buyers_count() to service_role;
