"""
chatgpt_proxy.py — No-API swarm proxy via a chat UI (copy-paste workflow).

Replaces the live swarm pipeline for tier-1 feature extraction when no API key
or local GPU is available. A human pastes generated prompt batches into any
chat LLM UI (ChatGPT, Claude, etc.), saves each reply to a file, and this
module ingests the replies into the same features JSON the backtest runner
would have produced — ready for eval.backtest.calibrate.

HONESTY LABEL: this is a *proxy* calibration. One chat-LLM call approximates
the aggregate output of the real multi-agent swarm. Weights fit on proxy
features may not transfer perfectly to the live pipeline's distribution.
Anything calibrated this way must carry a "proxy-calibrated" status in
RUBRIC.md / calibration_status — never plain "calibrated".

Workflow
--------
1. Generate prompt batches (20 files of 10 cases each, sample matches the
   Colab notebook: build_sample seed 42, 100 hits + 100 flops):

     .venv/bin/python -m eval.backtest.chatgpt_proxy make-prompts

2. Paste each eval/backtest/data/chatgpt/prompts/batch_NN.txt into the chat
   UI. Save each full reply as eval/backtest/data/chatgpt/replies/<anything>.txt
   (one file per reply; filenames don't matter).

3. Ingest replies → features:

     .venv/bin/python -m eval.backtest.chatgpt_proxy ingest

   Prints progress and missing case ids. Re-run after adding more replies.
   To regenerate prompts for only the still-missing cases:

     .venv/bin/python -m eval.backtest.chatgpt_proxy make-prompts \\
         --missing-from eval/backtest/data/chatgpt/features_tier1_proxy.json

4. Calibrate (writes proxy weights — keep the filename distinct from the
   live-run weights until promoted deliberately):

     .venv/bin/python -m eval.backtest.calibrate \\
         --features eval/backtest/data/chatgpt/features_tier1_proxy.json \\
         --out eval/backtest/data/chatgpt/index_weights_v1_proxy.json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

from eval.backtest.runner import build_sample, extract_dims

logger = logging.getLogger("swarmie.eval.backtest.chatgpt_proxy")

BASE_DIR = Path(__file__).parent / "data" / "chatgpt"
PROMPTS_DIR = BASE_DIR / "prompts"
REPLIES_DIR = BASE_DIR / "replies"
MANIFEST_PATH = BASE_DIR / "sample_manifest.json"
FEATURES_PATH = BASE_DIR / "features_tier1_proxy.json"

BATCH_SIZE = 10
N_AGENTS = 20
MAX_TEXT_CHARS = 1200

# Must stay aligned with roast_reporter._OBJECTION_SEVERITY_TIERS keywords so
# compute_objection_severity maps the proxy categories onto the right tiers.
OBJECTION_CATEGORIES = (
    "no demand, won't pay, pricing too high, no problem worth solving, "
    "market size too small, positioning unclear, messaging unclear, "
    "differentiation weak, who is this for, ui concerns, naming, "
    "onboarding friction, minor nitpicks"
)

PROMPT_HEADER = f"""\
You are simulating an audience swarm for startup pitch validation.

For EACH pitch below, simulate {N_AGENTS} distinct, realistic audience members
(mix of skeptical potential customers, industry insiders, and casual browsers
appropriate to that pitch's market). Judge each pitch AS IF AT LAUNCH TIME —
you have no knowledge of what happened to the company later. Do NOT try to
identify the company. React only to the text as written. Be harsh and
realistic: most pitches bore most people. Vary your judgments across pitches —
do not give every pitch similar numbers.

For each pitch output ONE JSON object:

{{
  "id": <the case id, copied exactly>,
  "sentiment_split": {{"positive": P, "neutral": N, "negative": G}},
  "action_split": {{"post": a, "comment": b, "upvote": c, "ignore": d}},
  "icp_fit": {{"<segment name>": {{"count": k, "avg_sentiment": s}}, ...}},
  "top_objections": [{{"category": "<category>", "count": m}}, ...]
}}

Rules:
- sentiment_split: integer percentages, must sum to exactly 100.
- action_split: integer counts of what each of the {N_AGENTS} members would do,
  must sum to exactly {N_AGENTS}. "ignore" = scrolled past, said nothing.
- icp_fit: 3-5 audience segments you simulated; counts sum to {N_AGENTS};
  avg_sentiment is that segment's mean sentiment in [-1.0, 1.0].
- top_objections: the 1-3 most common objections, count = how many of the
  {N_AGENTS} members raised it. Pick each category ONLY from this list:
  {OBJECTION_CATEGORIES}.
- Output ONLY a JSON array containing one object per pitch, in the same order.
  No commentary, no markdown, no code fences.

PITCHES:
"""


# ---------------------------------------------------------------------------
# make-prompts
# ---------------------------------------------------------------------------

def make_prompts(missing_from: str | None = None) -> None:
    sample = build_sample(n_per_class=100, seed=42)

    manifest = {str(c["id"]): {"label": c["label"], "name": c["name"]}
                for c in sample}
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if missing_from:
        have = {str(r["id"]) for r in json.loads(Path(missing_from).read_text())}
        sample = [c for c in sample if str(c["id"]) not in have]
        logger.info("missing-from filter: %d cases still needed", len(sample))

    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    for old in PROMPTS_DIR.glob("batch_*.txt"):
        old.unlink()

    batches = [sample[i:i + BATCH_SIZE] for i in range(0, len(sample), BATCH_SIZE)]
    for bi, batch in enumerate(batches, start=1):
        parts = [PROMPT_HEADER]
        for case in batch:
            text = case["text"][:MAX_TEXT_CHARS]
            parts.append(f'--- case id: {case["id"]} ---\n{text}\n')
        path = PROMPTS_DIR / f"batch_{bi:02d}.txt"
        path.write_text("\n".join(parts), encoding="utf-8")

    REPLIES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Wrote {len(batches)} prompt files to {PROMPTS_DIR}")
    print(f"Paste each into the chat UI; save each reply as a file in {REPLIES_DIR}")


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)

# Chat UIs / clipboards replace straight quotes with typographic ones, which
# breaks json.loads and severity-table keyword matching ("won't pay").
_QUOTE_MAP = str.maketrans({
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
    "‘": "'", "’": "'", "‚": "'",
})


def _extract_json_objects(raw: str) -> list[dict]:
    """Pull case objects out of a chat reply: tolerate fences, prose, arrays."""
    raw = raw.translate(_QUOTE_MAP)
    candidates: list[str] = []
    fenced = _FENCE_RE.findall(raw)
    candidates.extend(fenced)
    candidates.append(raw)
    start, end = raw.find("["), raw.rfind("]")
    if start != -1 and end > start:
        candidates.append(raw[start:end + 1])

    for cand in candidates:
        try:
            parsed = json.loads(cand.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, list):
            return [o for o in parsed if isinstance(o, dict)]
    return []


def _to_report(obj: dict) -> dict:
    """Coerce one chat-reply object into the report shape extract_dims needs."""
    action = {k: int(obj.get("action_split", {}).get(k, 0))
              for k in ("post", "comment", "upvote", "ignore")}
    total = sum(action.values())
    silent_share_pct = (action["ignore"] / total * 100.0) if total else 0.0

    sentiment = {k: float(obj.get("sentiment_split", {}).get(k, 0))
                 for k in ("positive", "neutral", "negative")}

    icp_fit = {}
    for seg, v in (obj.get("icp_fit") or {}).items():
        if isinstance(v, dict):
            icp_fit[str(seg)] = {
                "count": int(v.get("count", 0)),
                "avg_sentiment": max(-1.0, min(1.0, float(v.get("avg_sentiment", 0.0)))),
            }

    objections = []
    for o in (obj.get("top_objections") or []):
        if isinstance(o, dict) and o.get("category"):
            objections.append({"category": str(o["category"]),
                               "count": int(o.get("count", 0))})

    return {
        "sentiment_split": sentiment,
        "action_split": action,
        "icp_fit": icp_fit,
        "top_objections": objections,
        "silent_share_pct": silent_share_pct,
    }


def ingest() -> None:
    manifest: dict = json.loads(MANIFEST_PATH.read_text())

    reply_files = sorted(p for p in REPLIES_DIR.iterdir()
                         if p.is_file() and not p.name.startswith("."))
    if not reply_files:
        print(f"No reply files in {REPLIES_DIR} — nothing to ingest.")
        return

    by_id: dict[str, dict] = {}
    bad = 0
    for path in reply_files:
        objs = _extract_json_objects(path.read_text(encoding="utf-8", errors="replace"))
        if not objs:
            logger.warning("ingest: no JSON found in %s", path.name)
            continue
        for obj in objs:
            cid = str(obj.get("id", "")).strip()
            if cid not in manifest:
                logger.warning("ingest: unknown id %r in %s — skipped", cid, path.name)
                bad += 1
                continue
            try:
                by_id[cid] = extract_dims(_to_report(obj))
            except Exception as exc:  # noqa: BLE001 — skip malformed, keep batch
                logger.warning("ingest: id %s failed (%s: %s)", cid,
                               type(exc).__name__, exc)
                bad += 1

    rows = [{"id": cid, "label": manifest[cid]["label"], "run_idx": 0, **dims}
            for cid, dims in by_id.items()]
    FEATURES_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    missing = [cid for cid in manifest if cid not in by_id]
    hits = sum(r["label"] == 1 for r in rows)
    print(f"Ingested {len(rows)}/{len(manifest)} cases "
          f"({hits} hits / {len(rows) - hits} flops) from {len(reply_files)} reply files"
          f"{f' — {bad} malformed entries skipped' if bad else ''}")
    print(f"Features written to {FEATURES_PATH}")
    if missing:
        print(f"Missing {len(missing)} case ids: {', '.join(missing[:20])}"
              f"{' …' if len(missing) > 20 else ''}")
        print("Regenerate prompts for just these with:\n"
              f"  python -m eval.backtest.chatgpt_proxy make-prompts "
              f"--missing-from {FEATURES_PATH}")
    else:
        print("All cases ingested. Calibrate with:\n"
              f"  python -m eval.backtest.calibrate --features {FEATURES_PATH} "
              f"--out eval/backtest/data/chatgpt/index_weights_v1_proxy.json")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv: list[str] | None = None) -> None:
    import os
    os.environ.setdefault("SECRET_KEY", "chatgpt-proxy")
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s — %(message)s",
                        stream=sys.stderr)

    p = argparse.ArgumentParser(
        description="No-API copy-paste proxy for tier-1 feature extraction.",
        prog="python -m eval.backtest.chatgpt_proxy",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    mk = sub.add_parser("make-prompts", help="Write prompt batch files.")
    mk.add_argument("--missing-from", default=None,
                    help="Existing features JSON; only emit prompts for cases "
                         "not present in it.")

    sub.add_parser("ingest", help="Parse saved replies into features JSON.")

    args = p.parse_args(argv)
    if args.cmd == "make-prompts":
        make_prompts(missing_from=args.missing_from)
    else:
        ingest()


if __name__ == "__main__":
    _main()
