"""Billing: credit gating on review creation, pack pricing, and the Stripe webhook.

Supabase is faked in-process (a tiny ledger), so these run with no network.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import threading
import time

import pytest

from app import create_app
from app.api import roast as roast_api
from app.config import Config
from app.services import billing


class FakeLedger:
    """In-memory stand-in for the Supabase RPCs, with the same semantics."""

    def __init__(self):
        self.rows: dict[str, tuple[str, int]] = {}  # ref -> (user, delta)
        self.purchases: dict[str, tuple[str, bool]] = {}  # session -> (user, launch)

    def balance(self, user):
        return sum(d for u, d in self.rows.values() if u == user)

    def rpc(self, fn, args):
        if fn == "credit_balance":
            return self.balance(args["p_user"])
        if fn == "consume_credit":
            if args["p_ref"] in self.rows:
                return True
            if self.balance(args["p_user"]) < 1:
                return False
            self.rows[args["p_ref"]] = (args["p_user"], -1)
            return True
        if fn == "refund_credit":
            charge = self.rows.get(args["p_ref"])
            key = "refund:" + args["p_ref"]
            if not charge or key in self.rows:
                return False
            self.rows[key] = (args["p_user"], 1)
            return True
        if fn == "grant_purchase":
            if args["p_session"] in self.purchases:
                return False
            self.purchases[args["p_session"]] = (args["p_user"], args["p_launch"])
            self.rows["purchase:" + args["p_session"]] = (args["p_user"], args["p_credits"])
            return True
        if fn == "launch_buyers_count":
            return len({u for u, launch in self.purchases.values() if launch})
        raise AssertionError(fn)


@pytest.fixture
def ledger(monkeypatch):
    fake = FakeLedger()
    monkeypatch.setattr(billing, "_rpc", fake.rpc)
    monkeypatch.setattr(billing, "user_from_token",
                        lambda tok: billing.User(id=tok, email=f"{tok}@x.test") if tok else None)
    monkeypatch.setattr(Config, "BILLING_ENABLED", True)
    return fake


def _client():
    class _C(Config):
        TESTING = True
    return create_app(_C).test_client()


def _no_pipeline(monkeypatch, result="completed"):
    """Swap the pipeline for an instant stub that ends in `result`."""
    done = threading.Event()

    def fake(job):
        job.status = result
        done.set()

    monkeypatch.setattr(roast_api, "_roast_slots", threading.BoundedSemaphore(4))
    monkeypatch.setattr(roast_api, "_run_pipeline", fake)
    return done


def post(client, user=None, **body):
    headers = {"Authorization": f"Bearer {user}"} if user else {}
    payload = {"pitch": "a" * 60, "swarm_type": "validate", "n_agents": 20, **body}
    return client.post("/api/roast", json=payload, headers=headers)


# ---------------------------------------------------------------- gating

def test_free_review_needs_no_account(ledger, monkeypatch):
    _no_pipeline(monkeypatch)
    assert post(_client()).status_code == 202


@pytest.mark.parametrize("body", [{"n_agents": 100}, {"swarm_type": "investor"}, {"swarm_type": "launch"}])
def test_paid_review_requires_sign_in(ledger, monkeypatch, body):
    _no_pipeline(monkeypatch)
    resp = post(_client(), **body)
    assert resp.status_code == 401
    assert resp.get_json()["code"] == "sign_in_required"


def test_paid_review_without_credits_is_402(ledger, monkeypatch):
    _no_pipeline(monkeypatch)
    resp = post(_client(), user="u1", n_agents=100)
    assert resp.status_code == 402
    assert resp.get_json()["code"] == "no_credits"


def test_paid_review_spends_exactly_one_credit(ledger, monkeypatch):
    ledger.rows["grant:u1"] = ("u1", 3)
    done = _no_pipeline(monkeypatch)
    assert post(_client(), user="u1", n_agents=500).status_code == 202
    assert done.wait(2)
    time.sleep(0.05)  # let the wrapper's finally run
    assert ledger.balance("u1") == 2


def test_failed_review_refunds_its_credit(ledger, monkeypatch):
    ledger.rows["grant:u1"] = ("u1", 1)
    done = _no_pipeline(monkeypatch, result="failed")
    assert post(_client(), user="u1", swarm_type="investor").status_code == 202
    assert done.wait(2)
    for _ in range(40):  # refund happens in the worker thread's finally
        if ledger.balance("u1") == 1:
            break
        time.sleep(0.05)
    assert ledger.balance("u1") == 1


def test_busy_server_never_charges(ledger, monkeypatch):
    ledger.rows["grant:u1"] = ("u1", 1)
    monkeypatch.setattr(roast_api, "_roast_slots", threading.BoundedSemaphore(1))
    roast_api._roast_slots.acquire()  # server full
    resp = post(_client(), user="u1", n_agents=100)
    assert resp.status_code == 503
    assert ledger.balance("u1") == 1


def test_billing_off_keeps_pack_lock(monkeypatch):
    monkeypatch.setattr(Config, "BILLING_ENABLED", False)
    monkeypatch.setattr(Config, "PAID_SWARMS_ENABLED", False)
    _no_pipeline(monkeypatch)
    resp = post(_client(), swarm_type="launch")
    assert resp.status_code == 402
    assert resp.get_json()["code"] == "pack_required"


# ---------------------------------------------------------------- pricing

def test_launch_price_for_first_buyers_then_regular(ledger, monkeypatch):
    monkeypatch.setattr(Config, "LAUNCH_BUYERS", 2)
    client = _client()
    prices = {p["key"]: p for p in client.get("/api/billing/packs").get_json()["packs"]}
    assert prices["starter"]["price_cents"] == 1500 and prices["starter"]["launch_price"]
    assert prices["sprint"]["price_cents"] == 4900
    assert prices["try"]["price_cents"] == 500 and not prices["try"]["launch_price"]

    for i in range(2):
        ledger.purchases[f"cs_{i}"] = (f"buyer{i}", True)
    body = client.get("/api/billing/packs").get_json()
    prices = {p["key"]: p for p in body["packs"]}
    assert body["launch_remaining"] == 0
    assert prices["starter"]["price_cents"] == 2500 and not prices["starter"]["launch_price"]
    assert prices["sprint"]["price_cents"] == 8200


def test_endpoints_hidden_while_billing_off(monkeypatch):
    monkeypatch.setattr(Config, "BILLING_ENABLED", False)
    assert _client().get("/api/billing/packs").status_code == 404


def test_me_reports_balance(ledger):
    ledger.rows["grant:u9"] = ("u9", 7)
    resp = _client().get("/api/billing/me", headers={"Authorization": "Bearer u9"})
    assert resp.get_json() == {"email": "u9@x.test", "credits": 7}


# ---------------------------------------------------------------- webhook

SECRET = "whsec_test_secret"


def _signed(event: dict):
    payload = json.dumps(event).encode()
    ts = str(int(time.time()))
    sig = hmac.new(SECRET.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return payload, f"t={ts},v1={sig}"


def _paid_session(session_id="cs_1", pack="starter", user="u5", launch="1"):
    return {
        "id": "evt_1", "object": "event", "type": "checkout.session.completed",
        "data": {"object": {
            "id": session_id, "object": "checkout.session", "payment_status": "paid",
            "amount_total": 1500, "currency": "usd", "client_reference_id": user,
            "metadata": {"user_id": user, "pack": pack, "launch_price": launch},
        }},
    }


def test_webhook_grants_credits_once(ledger, monkeypatch):
    monkeypatch.setattr(Config, "STRIPE_WEBHOOK_SECRET", SECRET)
    client = _client()
    payload, sig = _signed(_paid_session())
    for _ in range(2):  # Stripe retries must not double-grant
        resp = client.post("/api/billing/webhook", data=payload, headers={"Stripe-Signature": sig})
        assert resp.status_code == 200
    assert ledger.balance("u5") == 20


def test_webhook_rejects_bad_signature(ledger, monkeypatch):
    monkeypatch.setattr(Config, "STRIPE_WEBHOOK_SECRET", SECRET)
    payload, _ = _signed(_paid_session())
    resp = _client().post("/api/billing/webhook", data=payload, headers={"Stripe-Signature": "t=1,v1=bad"})
    assert resp.status_code == 400
    assert ledger.balance("u5") == 0


def test_checkout_sends_launch_price_and_metadata(ledger, monkeypatch):
    import stripe

    seen = {}

    class _Session:
        url = "https://checkout.stripe.test/cs_1"

    def fake_create(**kwargs):
        seen.update(kwargs)
        return _Session()

    monkeypatch.setattr(Config, "STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setattr(Config, "APP_BASE_URL", "https://swarmie.test")
    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(fake_create))
    resp = _client().post("/api/billing/checkout", json={"pack": "sprint"}, headers={"Authorization": "Bearer u7"})
    assert resp.status_code == 200 and resp.get_json()["url"].startswith("https://checkout.stripe.test")
    item = seen["line_items"][0]["price_data"]
    assert item["unit_amount"] == 4900 and item["currency"] == "usd"
    assert seen["metadata"] == {"user_id": "u7", "pack": "sprint", "credits": "100", "launch_price": "1"}
    assert seen["success_url"].startswith("https://swarmie.test/account")


def test_checkout_requires_sign_in_and_known_pack(ledger):
    client = _client()
    assert client.post("/api/billing/checkout", json={"pack": "sprint"}).status_code == 401
    assert client.post("/api/billing/checkout", json={"pack": "gold"}, headers={"Authorization": "Bearer u7"}).status_code == 400


@pytest.mark.parametrize("key,bearer", [("sb_secret_abc", False), ("eyJhbGciOi.legacy.jwt", True)])
def test_service_headers_support_new_and_legacy_keys(monkeypatch, key, bearer):
    monkeypatch.setattr(Config, "SUPABASE_URL", "https://p.supabase.co")
    monkeypatch.setattr(Config, "SUPABASE_SERVICE_ROLE_KEY", key)
    h = billing._svc_headers()
    assert h["apikey"] == key
    assert ("Authorization" in h) is bearer


def test_status_reports_config_without_secrets(monkeypatch):
    monkeypatch.setattr(Config, "SUPABASE_URL", "https://abc.supabase.co")
    monkeypatch.setattr(Config, "SUPABASE_SERVICE_ROLE_KEY", "sb_secret_TOPSECRET")
    monkeypatch.setattr(Config, "STRIPE_SECRET_KEY", "sk_test_TOPSECRET")

    def boom(fn, args):
        raise billing.BillingError("supabase rpc launch_buyers_count returned 401: Invalid API key")

    monkeypatch.setattr(billing, "_rpc", boom)
    resp = _client().get("/api/billing/status")
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["supabase_key"] == "secret" and body["stripe_secret_key"] == "test"
    assert body["ledger_error_code"] == "401"
    assert "TOPSECRET" not in resp.get_data(as_text=True)
