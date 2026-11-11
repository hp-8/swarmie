"""Review credits: packs bought through Stripe Checkout, spent one per paid review.

The ledger lives in Supabase (see supabase/migrations/*_billing_credits.sql) and
is only reached with the service-role key, server side. Every mutation carries
a unique ref, so retries are safe.

Free reviews (Validate, panel <= FREE_MAX_AGENTS) need no account. Anything
larger, or a pack-only review type, costs one credit.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx

from ..config import Config

logger = logging.getLogger("swarmie.billing")

# Prices in USD cents. `launch` applies to the first LAUNCH_BUYERS paying buyers;
# keep in sync with the rate card in frontend/src/views/Home.vue (PLANS).
PACKS: dict[str, dict] = {
    "try": {"name": "Try pack", "credits": 5, "price": 500},
    "starter": {"name": "Starter pack", "credits": 20, "price": 2500, "launch": 1500},
    "sprint": {"name": "Sprint pack", "credits": 100, "price": 8200, "launch": 4900},
}

_TIMEOUT = httpx.Timeout(10.0)


class BillingError(Exception):
    """A billing backend call failed (Supabase or Stripe unreachable/misconfigured)."""


@dataclass
class User:
    id: str
    email: str | None


def enabled() -> bool:
    return bool(Config.BILLING_ENABLED)


def needs_credit(swarm_type: str, n_agents: int) -> bool:
    return swarm_type in Config.PAID_SWARMS or n_agents > Config.FREE_MAX_AGENTS


# ---------------------------------------------------------------- Supabase

def _svc_headers() -> dict[str, str]:
    key = Config.SUPABASE_SERVICE_ROLE_KEY
    if not (Config.SUPABASE_URL and key):
        raise BillingError("Supabase is not configured")
    headers = {"apikey": key, "Content-Type": "application/json"}
    # New secret keys (sb_secret_...) are not JWTs and go on `apikey` only;
    # legacy service_role JWTs also need Authorization: Bearer.
    if not key.startswith("sb_"):
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _rpc(fn: str, args: dict) -> object:
    url = f"{Config.SUPABASE_URL.rstrip('/')}/rest/v1/rpc/{fn}"
    try:
        resp = httpx.post(url, json=args, headers=_svc_headers(), timeout=_TIMEOUT)
    except httpx.HTTPError as exc:
        raise BillingError(f"supabase rpc {fn} failed: {exc}") from exc
    if resp.status_code >= 300:
        raise BillingError(f"supabase rpc {fn} returned {resp.status_code}: {resp.text[:200]}")
    return resp.json()


def user_from_token(token: str | None) -> User | None:
    """Resolve a Supabase access token to its user; None if missing/invalid/expired."""
    if not token:
        return None
    url = f"{Config.SUPABASE_URL.rstrip('/')}/auth/v1/user"
    try:
        resp = httpx.get(
            url,
            headers={"apikey": Config.SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {token}"},
            timeout=_TIMEOUT,
        )
    except httpx.HTTPError as exc:
        raise BillingError(f"supabase auth lookup failed: {exc}") from exc
    if resp.status_code != 200:
        return None
    data = resp.json()
    return User(id=data["id"], email=data.get("email"))


def balance(user_id: str) -> int:
    return int(_rpc("credit_balance", {"p_user": user_id}) or 0)


def consume(user_id: str, ref: str) -> bool:
    return bool(_rpc("consume_credit", {"p_user": user_id, "p_ref": ref}))


def refund(user_id: str, ref: str) -> bool:
    try:
        return bool(_rpc("refund_credit", {"p_user": user_id, "p_ref": ref}))
    except BillingError:
        # Never lose a refund silently: the ledger ref makes a manual replay safe.
        logger.exception("credit refund failed for %s %s", user_id, ref)
        return False


def diagnose() -> dict:
    """Billing configuration health for operators. Never returns secret values."""
    key = Config.SUPABASE_SERVICE_ROLE_KEY or ""
    if not key:
        key_kind = "missing"
    elif key.startswith("sb_secret_"):
        key_kind = "secret"
    elif key.startswith("sb_publishable_"):
        key_kind = "publishable (wrong: needs the secret key)"
    elif key.startswith("eyJ"):
        key_kind = "legacy jwt"
    else:
        key_kind = "unrecognised"
    url = Config.SUPABASE_URL or ""
    out = {
        "billing_enabled": enabled(),
        "supabase_url_set": bool(url),
        "supabase_url_shape_ok": url.startswith("https://") and url.rstrip("/").endswith(".supabase.co"),
        "supabase_key": key_kind,
        "stripe_secret_key": "test" if Config.STRIPE_SECRET_KEY.startswith("sk_test_") else
                             "live" if Config.STRIPE_SECRET_KEY.startswith("sk_live_") else
                             "missing" if not Config.STRIPE_SECRET_KEY else "unrecognised",
        "stripe_webhook_secret_set": Config.STRIPE_WEBHOOK_SECRET.startswith("whsec_"),
    }
    try:
        _rpc("launch_buyers_count", {})
        out["ledger"] = "ok"
    except BillingError as exc:
        # Status code and Postgres/PostgREST error code only; no payload echo.
        msg = str(exc)
        out["ledger"] = msg.split(":")[0][:120]
        for code in ("42501", "PGRST202", "PGRST301", "401", "403", "404"):
            if code in msg:
                out["ledger_error_code"] = code
                break
    return out


def launch_remaining() -> int:
    used = int(_rpc("launch_buyers_count", {}) or 0)
    return max(0, Config.LAUNCH_BUYERS - used)


def pack_offer(pack_key: str, launch_left: int) -> dict:
    """Current price for a pack: launch price while launch spots remain."""
    p = PACKS[pack_key]
    launch = "launch" in p and launch_left > 0
    return {
        "key": pack_key,
        "name": p["name"],
        "credits": p["credits"],
        "price_cents": p["launch"] if launch else p["price"],
        "regular_cents": p["price"],
        "launch_price": launch,
    }


# ---------------------------------------------------------------- Stripe

def create_checkout(user: User, pack_key: str) -> str:
    """Create a hosted Checkout session for a pack; returns its URL."""
    import stripe

    if not Config.STRIPE_SECRET_KEY:
        raise BillingError("Stripe is not configured")
    offer = pack_offer(pack_key, launch_remaining())
    base = Config.APP_BASE_URL.rstrip("/")
    try:
        session = stripe.checkout.Session.create(
            api_key=Config.STRIPE_SECRET_KEY,
            mode="payment",
            line_items=[{
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "unit_amount": offer["price_cents"],
                    "product_data": {"name": f"Swarmie {offer['name']} ({offer['credits']} reviews)"},
                },
            }],
            client_reference_id=user.id,
            customer_email=user.email or None,
            metadata={
                "user_id": user.id,
                "pack": pack_key,
                "credits": str(offer["credits"]),
                "launch_price": "1" if offer["launch_price"] else "0",
            },
            success_url=f"{base}/account?purchase=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base}/#pricing",
        )
    except stripe.StripeError as exc:
        raise BillingError(f"stripe checkout failed: {exc}") from exc
    return session.url


def handle_webhook(payload: bytes, signature: str | None) -> str:
    """Verify a Stripe webhook and grant credits for paid Checkout sessions.

    Returns a short outcome string for logging. Raises ValueError on a bad
    signature/payload (caller answers 400 so Stripe does not retry forever).
    """
    import stripe

    if not Config.STRIPE_WEBHOOK_SECRET:
        raise BillingError("Stripe webhook secret is not configured")
    try:
        stripe.Webhook.construct_event(payload, signature or "", Config.STRIPE_WEBHOOK_SECRET)
    except (stripe.SignatureVerificationError, ValueError) as exc:
        raise ValueError(f"invalid webhook: {exc}") from exc
    # Signature verified; read plain JSON rather than SDK objects, whose
    # dict-like interface changes across stripe-python majors.
    event = json.loads(payload)

    if event["type"] not in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        return f"ignored {event['type']}"
    session = event["data"]["object"]
    if session.get("payment_status") != "paid":
        return "not paid yet"

    meta = session.get("metadata") or {}
    pack_key = meta.get("pack")
    user_id = meta.get("user_id") or session.get("client_reference_id")
    if pack_key not in PACKS or not user_id:
        logger.error("webhook session %s missing pack/user metadata", session.get("id"))
        return "missing metadata"

    granted = _rpc("grant_purchase", {
        "p_user": user_id,
        "p_pack": pack_key,
        "p_credits": PACKS[pack_key]["credits"],
        "p_amount_cents": int(session.get("amount_total") or 0),
        "p_currency": session.get("currency") or "usd",
        "p_launch": meta.get("launch_price") == "1",
        "p_session": session["id"],
    })
    return "granted" if granted else "already granted"
