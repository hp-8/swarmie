"""Analytics ingest: the browser posts events here; the backend writes them to
Supabase with the service-role key. Browser keys have no table access, so no
one can read other users' pitches or overwrite their rows.

Consent is enforced client-side (nothing is sent without it). Each op maps to
one table and a fixed column allowlist, so callers can't write other columns.
"""

from __future__ import annotations

import logging

import httpx
from flask import Blueprint, jsonify, request

from ..config import Config
from ..extensions import limiter
from ..services.billing import BillingError, _svc_headers

logger = logging.getLogger("swarmie.api.analytics")
analytics_bp = Blueprint("analytics", __name__)

# op -> (table, mode, conflict columns or filter column, allowed columns)
OPS: dict[str, tuple[str, str, str | None, tuple[str, ...]]] = {
    "device": ("devices", "upsert", "fingerprint_id",
               ("fingerprint_id", "user_agent", "platform", "screen_res", "timezone", "last_seen_at")),
    "run_start": ("roast_runs", "insert", None,
                  ("job_id", "fingerprint_id", "status", "pitch_length", "pitch_text",
                   "n_agents_requested", "swarm_type", "source")),
    "run_complete": ("roast_runs", "update", "job_id",
                     ("job_id", "status", "completed_at", "agent_count", "prompt_tokens",
                      "completion_tokens", "total_tokens", "cost_usd", "model", "error")),
    "pitch": ("roast_pitches", "upsert", "job_id",
              ("job_id", "one_liner", "problem", "solution", "target_icp", "pricing",
               "icp_segments", "competitors", "channels", "founder_ask")),
    "report": ("roast_reports", "upsert", "job_id",
               ("job_id", "pmf_score", "headline", "narrative", "sentiment_positive",
                "sentiment_neutral", "sentiment_negative", "action_post", "action_comment",
                "action_upvote", "action_ignore", "top_objections", "messaging_gaps",
                "icp_fit", "quoted_reactions")),
    "reactions": ("roast_reactions", "upsert", "job_id,agent_id",
                  ("job_id", "agent_id", "archetype_id", "segment", "name", "tone", "action",
                   "reaction_text", "sentiment", "objections")),
    "pdf_download": ("pdf_downloads", "insert", None, ("job_id", "fingerprint_id")),
    "objection_feedback": ("objection_feedback", "upsert", "job_id,fingerprint_id,objection_category",
                           ("job_id", "fingerprint_id", "objection_category", "vote")),
    "product_feedback": ("product_feedback", "insert", None,
                         ("job_id", "fingerprint_id", "helpful", "comment", "email", "trigger")),
}

MAX_ROWS = 600  # largest swarm is 500 agents
# Written by the backend itself (roast pipeline), never accepted from browsers.
SERVER_ONLY = {"run_complete"}


def write(op: str, rows: list[dict]) -> None:
    table, mode, key, cols = OPS[op]
    rows = [{c: r[c] for c in cols if c in r} for r in rows]
    url = f"{Config.SUPABASE_URL.rstrip('/')}/rest/v1/{table}"
    headers = {**_svc_headers(), "Prefer": "return=minimal"}
    params: dict[str, str] = {}
    if mode == "upsert":
        headers["Prefer"] += ",resolution=merge-duplicates"
        params["on_conflict"] = key
    try:
        if mode == "update":
            for r in rows:
                val = r.pop(key)
                resp = httpx.patch(url, params={key: f"eq.{val}"}, json=r, headers=headers, timeout=10)
                resp.raise_for_status()
        else:
            resp = httpx.post(url, params=params, json=rows, headers=headers, timeout=10)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise BillingError(f"analytics {op} failed: {exc}") from exc


@analytics_bp.route("/<op>", methods=["POST"])
@limiter.limit("300 per hour")
def ingest(op: str):
    if op not in OPS or op in SERVER_ONLY:
        return jsonify({"error": "unknown event"}), 404
    if not (Config.SUPABASE_URL and Config.SUPABASE_SERVICE_ROLE_KEY):
        return "", 204  # analytics not configured: drop silently
    body = request.get_json(silent=True)
    rows = body if isinstance(body, list) else [body]
    if not rows or len(rows) > MAX_ROWS or not all(isinstance(r, dict) for r in rows):
        return jsonify({"error": "bad payload"}), 400
    key = OPS[op][2]
    if OPS[op][1] == "update" and not all(r.get(key) for r in rows):
        return jsonify({"error": f"{key} required"}), 400
    try:
        write(op, rows)
    except BillingError:
        logger.exception("analytics write failed")
        return jsonify({"error": "analytics unavailable"}), 503
    return "", 204
