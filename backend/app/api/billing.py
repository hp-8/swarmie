"""Billing API: account balance, pack offers, Stripe Checkout, Stripe webhook."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from ..extensions import limiter
from ..services import billing

logger = logging.getLogger("swarmie.api.billing")
billing_bp = Blueprint("billing", __name__)


def bearer_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    return header[7:].strip() or None


def current_user():
    """(user, error_response). Error is a ready Flask response when auth fails."""
    try:
        user = billing.user_from_token(bearer_token())
    except billing.BillingError:
        logger.exception("auth lookup failed")
        return None, (jsonify({"error": "Sign-in is temporarily unavailable.", "code": "billing_unavailable"}), 503)
    if user is None:
        return None, (jsonify({"error": "Sign in to continue.", "code": "sign_in_required"}), 401)
    return user, None


def _disabled():
    return jsonify({"error": "Review packs are not on sale yet.", "code": "billing_disabled"}), 404


@billing_bp.route("/packs", methods=["GET"])
def packs():
    if not billing.enabled():
        return _disabled()
    try:
        left = billing.launch_remaining()
    except billing.BillingError:
        logger.exception("launch count failed")
        return jsonify({"error": "Pricing is temporarily unavailable."}), 503
    return jsonify({
        "packs": [billing.pack_offer(k, left) for k in billing.PACKS],
        "launch_remaining": left,
        "mode": billing.Config.STRIPE_MODE,
    }), 200


@billing_bp.route("/status", methods=["GET"])
@limiter.limit("30 per hour")
def status():
    """Config health: which settings are present and whether the ledger answers."""
    return jsonify(billing.diagnose()), 200


@billing_bp.route("/me", methods=["GET"])
def me():
    if not billing.enabled():
        return _disabled()
    user, err = current_user()
    if err:
        return err
    try:
        bal = billing.balance(user.id)
    except billing.BillingError:
        logger.exception("balance lookup failed")
        return jsonify({"error": "Your balance is temporarily unavailable."}), 503
    return jsonify({"email": user.email, "credits": bal}), 200


@billing_bp.route("/checkout", methods=["POST"])
@limiter.limit("20 per hour")
def checkout():
    if not billing.enabled():
        return _disabled()
    user, err = current_user()
    if err:
        return err
    pack = (request.get_json(silent=True) or {}).get("pack")
    if pack not in billing.PACKS:
        return jsonify({"error": f"unknown pack '{pack}'"}), 400
    try:
        url = billing.create_checkout(user, pack)
    except billing.BillingError:
        logger.exception("checkout creation failed")
        return jsonify({"error": "Checkout is temporarily unavailable. Please try again shortly."}), 503
    return jsonify({"url": url}), 200


@billing_bp.route("/webhook", methods=["POST"])
def webhook():
    # Always reachable when configured, even if sales are paused, so in-flight
    # payments are still granted.
    try:
        outcome = billing.handle_webhook(request.get_data(), request.headers.get("Stripe-Signature"))
    except ValueError as exc:
        logger.warning("rejected stripe webhook: %s", exc)
        return jsonify({"error": "invalid webhook"}), 400
    except billing.BillingError:
        # 500 makes Stripe retry later; grants are idempotent on the session id.
        logger.exception("stripe webhook processing failed")
        return jsonify({"error": "temporarily unavailable"}), 500
    logger.info("stripe webhook: %s", outcome)
    return jsonify({"ok": True, "outcome": outcome}), 200
