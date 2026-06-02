"""
Swarmie eval harness.

Usage (from backend/ with venv active):
  python -m eval.run                     # synth mode (default, no LLM needed)
  python -m eval.run --mode synth        # explicit synth
  python -m eval.run --mode full         # full pipeline (needs LLM_API_KEY)
  python -m eval.run --mode full --runs 3  # consistency check (3 runs per case)
  python -m eval.run --cases tally_validate,strong_dev_tool  # subset
  python -m eval.run --judge             # add LLM-as-judge rubric (needs key)

Exit codes:
  0 = all cases pass the deterministic bar
  1 = one or more cases failed
  2 = env/import error
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from typing import Any

# ---------------------------------------------------------------------------
# Allow running from backend/ as  python -m eval.run
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# ---------------------------------------------------------------------------
# Lazy imports — keep env-sensitive things behind a guard so the module can
# be imported without triggering Config.validate() (which requires SECRET_KEY)
# ---------------------------------------------------------------------------

def _has_api_key() -> bool:
    return bool(
        os.environ.get("LLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )


# ---------------------------------------------------------------------------
# Scorecard helpers
# ---------------------------------------------------------------------------

PASS_BAR = 0.70  # 70% of deterministic checks must pass per case


def _pct(n: int, total: int) -> str:
    if total == 0:
        return "  0%"
    return f"{100*n//total:3d}%"


def _print_separator(width: int = 72) -> None:
    print("─" * width)


def _print_case_header(case_id: str, swarm_type: str, run_idx: int | None = None) -> None:
    suffix = f" (run {run_idx})" if run_idx is not None else ""
    print(f"\n{'━'*72}")
    print(f"  CASE: {case_id}  [{swarm_type}]{suffix}")
    print("━" * 72)


def _format_check_row(result: dict) -> str:
    icon = "PASS" if result["passed"] else "FAIL"
    return f"  [{icon}] {result['check']:<28}  {result['detail']}"


def _case_score(check_results: list[dict]) -> float:
    if not check_results:
        return 0.0
    return sum(1 for r in check_results if r["passed"]) / len(check_results)


# ---------------------------------------------------------------------------
# Synth mode: drive roast_reporter with canned reactions (no LLM calls for
# the swarm, but roast_reporter still calls LLM for narrative synthesis).
# We stub the LLM call so synth mode is 100% offline.
# ---------------------------------------------------------------------------

def _build_parsed_pitch(case: dict) -> Any:
    """Build a minimal ParsedPitch from the pitch_text in the golden case."""
    from app.services.swarm.pitch_parser import ParsedPitch

    text = case["pitch_text"]
    # Quick heuristic extraction for synth mode — good enough for reporter
    lines = text.lower()
    return ParsedPitch(
        one_liner=text.split(".")[0][:120].strip(),
        problem=_extract_section(text, ["problem", "PROBLEM"]) or "Unspecified problem.",
        solution=_extract_section(text, ["solution", "SOLUTION", "product", "PRODUCT"]) or "Unspecified solution.",
        target_icp=_extract_section(text, ["audience", "AUDIENCE", "target", "icp"]) or "General B2B",
        icp_segments=["early_adopters", "skeptics", "domain_experts"],
        pricing=_extract_section(text, ["pricing", "PRICING"]) or "",
        channels=[],
        competitors=[],
        founder_ask="Will this resonate with the target ICP?",
    )


def _extract_section(text: str, markers: list[str]) -> str:
    """Extract the first sentence after a marker keyword."""
    for marker in markers:
        idx = text.find(marker + ":")
        if idx == -1:
            idx = text.find(marker.upper() + ":")
        if idx != -1:
            start = idx + len(marker) + 1
            snippet = text[start:start + 400].strip()
            return snippet.split("\n")[0][:300].strip()
    return ""


def _make_llm_stub(return_value: dict) -> Any:
    """Return a minimal object with a chat_json method that returns canned data."""
    class _Stub:
        def chat_json(self, messages, temperature=0.3, max_tokens=4096, model=None):
            return return_value
    return _Stub()


def _synth_fallback_llm_response(case: dict) -> dict:
    """
    Build a plausible LLM response for synth mode based on case metadata.
    This is the 'narrative' synthesis call only — all metric computation is
    fully deterministic.
    """
    swarm_type = case.get("swarm_type", "validate")
    expected_v = list(case["expected_verdicts"])
    # Pick a verdict from expected set
    verdict = expected_v[0]

    verdict_enum_map = {
        "validate": "sharpen_positioning",
        "investor": "sharpen_story",
        "launch": "sharpen",
    }
    default_v = verdict_enum_map.get(swarm_type, "sharpen_positioning")

    # Pick valid objection categories from the case's required themes
    themes = case.get("required_objection_themes", [])
    obj_cats = [t[0] for t in themes[:3]] if themes else ["unclear_value"]

    return {
        "headline": f"[synth] {case['id']} — narrative stub.",
        "narrative": (
            f"Paragraph 1: signal summary for {case['id']}. "
            f"Paragraph 2: top objections include {', '.join(obj_cats)}. "
            f"Paragraph 3: recommended fix for positioning."
        ),
        "messaging_gaps": [f"Improve {t[0]} messaging" for t in themes[:2]],
        "verdict": verdict,
        "verdict_reason": f"Synth stub for {case['id']}: {verdict}.",
        "next_action": f"Interview 5 users about {obj_cats[0]}.",
        "confidence": "low",
        "confidence_reason": "synth mode — canned reactions, stub LLM",
        "objections_enriched": [
            {
                "category": cat,
                "real_test": f"How does {cat} affect your decision?",
                "kill_criteria": f"If 3/5 cite {cat}, reframe.",
                "suggested_fix": f"Address {cat} in the one-liner.",
            }
            for cat in obj_cats
        ],
        # launch brief stub
        "questions": ["What does this cost?", "How does it compare to X?"],
        "confusion": ["Unclear differentiation"],
        "risks": ["Crowded market"],
        "themes": ["Differentiation debate"],
        "playbook": [{"trigger": "ChatGPT wrapper?", "response": "We integrate with your existing context."}],
        "next_actions": ["Fix one-liner to lead with outcome."],
    }


def run_synth_case(case: dict, verbose: bool = True) -> dict[str, Any]:
    """
    Run a single golden case in synth mode.
    - Uses canned reactions (no swarm LLM calls).
    - Stubs the roast_reporter LLM call with plausible canned output.
    - Runs all deterministic checks.
    """
    from eval.canned_reactions import CANNED
    from eval.checks import run_all_checks

    case_id = case["id"]
    swarm_type = case.get("swarm_type", "validate")

    # Choose the right reporter class
    reporter_class = _reporter_class_for(swarm_type)

    # Build parsed pitch (quick heuristic, no LLM)
    pitch = _build_parsed_pitch(case)

    # Get canned reactions
    canned = CANNED.get(case_id, [])
    if not canned:
        return {
            "case_id": case_id,
            "error": f"No canned reactions for case '{case_id}'",
            "check_results": [],
            "score": 0.0,
            "passed": False,
        }

    # Build reporter with stubbed LLM
    reporter = reporter_class.__new__(reporter_class)
    reporter.llm = _make_llm_stub(_synth_fallback_llm_response(case))

    # Run report
    t0 = time.monotonic()
    try:
        report = reporter.report(pitch, canned)
    except Exception as exc:
        return {
            "case_id": case_id,
            "error": f"report() raised: {exc}",
            "check_results": [],
            "score": 0.0,
            "passed": False,
        }
    elapsed = time.monotonic() - t0

    report_dict = report.to_dict()

    # Run checks
    check_results = run_all_checks(report_dict, case)
    score = _case_score(check_results)
    passed = score >= PASS_BAR

    if verbose:
        _print_case_header(case_id, swarm_type)
        for r in check_results:
            print(_format_check_row(r))
        _print_separator()
        print(f"  verdict={report.verdict}  pmf={report.pmf_score:.1f}/10  "
              f"confidence={report.confidence}  silent={report.silent_share_pct:.0f}%")
        print(f"  score: {score:.0%} ({sum(r['passed'] for r in check_results)}/{len(check_results)} checks)  "
              f"elapsed={elapsed:.2f}s  {'PASS' if passed else 'FAIL'}")

    return {
        "case_id": case_id,
        "swarm_type": swarm_type,
        "check_results": check_results,
        "score": score,
        "passed": passed,
        "elapsed": elapsed,
        "report_summary": {
            "verdict": report.verdict,
            "pmf_score": report.pmf_score,
            "confidence": report.confidence,
            "silent_share_pct": report.silent_share_pct,
            "headline": report.headline,
        },
    }


def _reporter_class_for(swarm_type: str):
    from app.services.swarm.roast_reporter import RoastReporter, InvestorReporter, LaunchReporter
    return {
        "validate": RoastReporter,
        "investor": InvestorReporter,
        "launch": LaunchReporter,
    }.get(swarm_type, RoastReporter)


# ---------------------------------------------------------------------------
# Full mode: run the complete pipeline (parse → archetypes → swarm → report)
# ---------------------------------------------------------------------------

def run_full_case(case: dict, verbose: bool = True) -> dict[str, Any]:
    """Run the full pipeline. Requires an API key."""
    import asyncio
    from app.services.swarm.pitch_parser import PitchParser, InvestorPitchParser, LaunchPitchParser
    from app.services.swarm.archetype_generator import ArchetypeGenerator, InvestorArchetypeGenerator, LaunchArchetypeGenerator
    from app.services.swarm.swarm_runner import SwarmRunner, InvestorSwarmRunner, LaunchSwarmRunner
    from app.services.swarm.roast_reporter import RoastReporter, InvestorReporter, LaunchReporter
    from app.utils.llm import UsageTracker
    from eval.checks import run_all_checks

    case_id = case["id"]
    swarm_type = case.get("swarm_type", "validate")

    parser_map = {
        "validate": PitchParser,
        "investor": InvestorPitchParser,
        "launch": LaunchPitchParser,
    }
    arch_map = {
        "validate": ArchetypeGenerator,
        "investor": InvestorArchetypeGenerator,
        "launch": LaunchArchetypeGenerator,
    }
    runner_map = {
        "validate": SwarmRunner,
        "investor": InvestorSwarmRunner,
        "launch": LaunchSwarmRunner,
    }
    reporter_map = {
        "validate": RoastReporter,
        "investor": InvestorReporter,
        "launch": LaunchReporter,
    }

    tracker = UsageTracker()
    t0 = time.monotonic()

    try:
        # 1. Parse pitch
        parser = parser_map[swarm_type](tracker=tracker)
        pitch = parser.parse(case["pitch_text"])

        # 2. Generate archetypes (small count for eval speed)
        gen = arch_map[swarm_type](tracker=tracker)
        archetypes = gen.generate(pitch, n_archetypes=6)

        # 3. Run swarm (small agent count)
        runner = runner_map[swarm_type](tracker=tracker)
        reactions = asyncio.run(runner.run(pitch, archetypes, n_agents=20, concurrency=5))

        # 4. Generate report
        reporter = reporter_map[swarm_type](tracker=tracker)
        report = reporter.report(pitch, reactions)

    except Exception as exc:
        return {
            "case_id": case_id,
            "error": str(exc),
            "check_results": [],
            "score": 0.0,
            "passed": False,
        }

    elapsed = time.monotonic() - t0
    report_dict = report.to_dict()
    from eval.checks import run_all_checks
    check_results = run_all_checks(report_dict, case)
    score = _case_score(check_results)
    passed = score >= PASS_BAR

    if verbose:
        _print_case_header(case_id, swarm_type)
        for r in check_results:
            print(_format_check_row(r))
        _print_separator()
        cost = tracker.total_cost_usd
        print(f"  verdict={report.verdict}  pmf={report.pmf_score:.1f}/10  "
              f"confidence={report.confidence}  silent={report.silent_share_pct:.0f}%")
        print(f"  score: {score:.0%} ({sum(r['passed'] for r in check_results)}/{len(check_results)} checks)  "
              f"elapsed={elapsed:.1f}s  cost=${cost:.4f}  {'PASS' if passed else 'FAIL'}")

    return {
        "case_id": case_id,
        "swarm_type": swarm_type,
        "check_results": check_results,
        "score": score,
        "passed": passed,
        "elapsed": elapsed,
        "report_summary": {
            "verdict": report.verdict,
            "pmf_score": report.pmf_score,
            "confidence": report.confidence,
            "silent_share_pct": report.silent_share_pct,
            "headline": report.headline,
        },
        "cost_usd": tracker.total_cost_usd,
    }


# ---------------------------------------------------------------------------
# Consistency check: run N times and measure verdict stability
# ---------------------------------------------------------------------------

def run_consistency(case: dict, n_runs: int = 3, mode: str = "synth",
                    verbose: bool = True) -> dict[str, Any]:
    """Run case N times; report verdict stability."""
    verdicts = []
    scores = []
    for i in range(n_runs):
        if mode == "full":
            result = run_full_case(case, verbose=False)
        else:
            result = run_synth_case(case, verbose=False)
        v = result.get("report_summary", {}).get("verdict", "N/A")
        verdicts.append(v)
        scores.append(result.get("score", 0.0))

    verdict_counts = Counter(verdicts)
    dominant = verdict_counts.most_common(1)[0][0]
    stability = verdict_counts[dominant] / n_runs  # fraction agreeing with dominant

    if verbose:
        print(f"\n  Consistency ({n_runs} runs): {dict(verdict_counts)}  "
              f"stability={stability:.0%}  avg_score={sum(scores)/len(scores):.0%}")

    return {
        "verdicts": verdicts,
        "stability": stability,
        "dominant_verdict": dominant,
        "avg_score": sum(scores) / len(scores),
    }


# ---------------------------------------------------------------------------
# LLM-as-judge (optional)
# ---------------------------------------------------------------------------

_JUDGE_RUBRIC_SYSTEM = """You are a quality evaluator for LLM-generated startup validation reports.
Given a report and the original pitch, score each dimension 1-5 (5=best):
  clarity      — is the narrative clear, jargon-free, easy to act on?
  specificity  — does it cite specific aspects of THIS pitch, not generic advice?
  actionability — does the next_action give one concrete, specific step?

Return strict JSON:
{"clarity": <int>, "specificity": <int>, "actionability": <int>, "rationale": "<1-2 sentences>"}
JSON only."""


def run_judge(case: dict, report_dict: dict) -> dict[str, Any]:
    """Run LLM-as-judge rubric. Returns score dict or error."""
    if not _has_api_key():
        return {"skipped": True, "reason": "no API key configured"}

    try:
        from app.utils.llm import LLM
        llm = LLM(tier="synth")
        payload = {
            "pitch_excerpt": case["pitch_text"][:600],
            "headline": report_dict.get("headline", ""),
            "verdict": report_dict.get("verdict", ""),
            "next_action": report_dict.get("next_action", ""),
            "narrative": str(report_dict.get("narrative", ""))[:400],
        }
        messages = [
            {"role": "system", "content": _JUDGE_RUBRIC_SYSTEM},
            {"role": "user", "content": f"REPORT DATA:\n{json.dumps(payload, indent=2)}\n\nReturn JSON only."},
        ]
        data = llm.chat_json(messages, temperature=0.2, max_tokens=300)
        scores = {k: int(data.get(k, 0)) for k in ("clarity", "specificity", "actionability")}
        scores["rationale"] = str(data.get("rationale", ""))
        scores["avg"] = round(sum(scores[k] for k in ("clarity", "specificity", "actionability")) / 3, 2)
        return scores
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Aggregate scorecard
# ---------------------------------------------------------------------------

def print_scorecard(results: list[dict], consistency_results: dict | None = None,
                    judge_results: dict | None = None) -> None:
    print(f"\n{'═'*72}")
    print("  AGGREGATE SCORECARD")
    print("═" * 72)

    total = len(results)
    n_passed = sum(1 for r in results if r.get("passed", False))
    avg_score = sum(r.get("score", 0.0) for r in results) / max(total, 1)

    print(f"  Cases: {total}   Passed: {n_passed}/{total}   Avg score: {avg_score:.0%}")
    print()
    print(f"  {'Case':<28} {'Swarm':<10} {'Score':>6} {'Verdict':<24} {'PMF':>5}  Status")
    _print_separator()

    for r in results:
        if "error" in r:
            print(f"  {r['case_id']:<28} {'?':<10} {'N/A':>6} ERROR: {r['error']}")
            continue
        rs = r.get("report_summary", {})
        verdict = rs.get("verdict", "?")
        pmf = rs.get("pmf_score", 0.0)
        score = r.get("score", 0.0)
        status = "PASS" if r.get("passed") else "FAIL"
        print(f"  {r['case_id']:<28} {r.get('swarm_type','?'):<10} {score:>5.0%}  {verdict:<24} {pmf:>4.1f}  {status}")

    if consistency_results:
        print()
        print("  CONSISTENCY CHECK")
        _print_separator()
        for case_id, cr in consistency_results.items():
            print(f"  {case_id:<28} stability={cr['stability']:.0%}  "
                  f"dominant='{cr['dominant_verdict']}'  runs={len(cr['verdicts'])}")

    if judge_results:
        print()
        print("  LLM-AS-JUDGE (1-5 rubric)")
        _print_separator()
        for case_id, jr in judge_results.items():
            if jr.get("skipped"):
                print(f"  {case_id:<28} SKIPPED ({jr.get('reason', '')})")
            elif "error" in jr:
                print(f"  {case_id:<28} ERROR: {jr['error']}")
            else:
                print(f"  {case_id:<28} clarity={jr.get('clarity','?')}  "
                      f"specific={jr.get('specificity','?')}  "
                      f"action={jr.get('actionability','?')}  "
                      f"avg={jr.get('avg','?')}")

    print()
    overall = n_passed == total
    print(f"  OVERALL: {'ALL PASS' if overall else f'{total-n_passed} CASE(S) FAILED'}  "
          f"(bar={PASS_BAR:.0%} of deterministic checks per case)")
    print("═" * 72)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Swarmie eval harness")
    parser.add_argument("--mode", choices=["synth", "full"], default="synth",
                        help="synth = canned reactions + stub LLM (offline); "
                             "full = real pipeline (needs API key)")
    parser.add_argument("--cases", type=str, default="",
                        help="comma-separated case IDs to run (default: all)")
    parser.add_argument("--runs", type=int, default=1,
                        help="number of runs per case for consistency check (default: 1)")
    parser.add_argument("--judge", action="store_true",
                        help="add LLM-as-judge rubric scoring (needs API key)")
    parser.add_argument("--json-out", type=str, default="",
                        help="path to write JSON results (optional)")
    args = parser.parse_args()

    from eval.golden_set import GOLDEN_CASES, all_case_ids

    # Determine which cases to run
    if args.cases:
        requested = [c.strip() for c in args.cases.split(",") if c.strip()]
        cases = [c for c in GOLDEN_CASES if c["id"] in requested]
        if not cases:
            print(f"ERROR: none of {requested} found in golden set (available: {all_case_ids()})")
            return 2
    else:
        cases = GOLDEN_CASES

    # Mode check
    if args.mode == "full" and not _has_api_key():
        print("ERROR: --mode full requires LLM_API_KEY or OPENAI_API_KEY in env.")
        print("       Run with --mode synth for offline evaluation.")
        return 2

    print(f"\nSwarmie Eval Harness  mode={args.mode}  cases={len(cases)}  runs={args.runs}")
    print("=" * 72)

    results = []
    consistency_results = {}
    judge_results = {}

    for case in cases:
        case_id = case["id"]

        if args.mode == "full":
            result = run_full_case(case, verbose=True)
        else:
            result = run_synth_case(case, verbose=True)

        results.append(result)

        # Consistency check (only meaningful for full mode; synth is deterministic)
        if args.runs > 1:
            cr = run_consistency(case, n_runs=args.runs, mode=args.mode, verbose=True)
            consistency_results[case_id] = cr

        # Judge
        if args.judge:
            report_dict = {}
            if "report_summary" in result:
                # For judge we need the full report dict — only available if we stored it
                # In synth mode we store a summary; for judge we re-run briefly
                if args.mode == "synth":
                    # Re-run synth silently to get full dict
                    jr_case_result = run_synth_case(case, verbose=False)
                    # We don't have full dict here; use summary as approximation
                    report_dict = jr_case_result.get("report_summary", {})
                else:
                    report_dict = result.get("report_summary", {})
            jr = run_judge(case, report_dict)
            judge_results[case_id] = jr
            if not jr.get("skipped"):
                print(f"  judge: clarity={jr.get('clarity','?')} "
                      f"specificity={jr.get('specificity','?')} "
                      f"actionability={jr.get('actionability','?')}")
        elif not _has_api_key():
            # Silently skip judge if no key
            pass

    print_scorecard(
        results,
        consistency_results=consistency_results if args.runs > 1 else None,
        judge_results=judge_results if args.judge else None,
    )

    if args.json_out:
        out = {
            "mode": args.mode,
            "cases": results,
            "consistency": consistency_results,
            "judge": judge_results,
        }
        with open(args.json_out, "w") as f:
            json.dump(out, f, indent=2, default=str)
        print(f"\nJSON results written to: {args.json_out}")

    overall_pass = all(r.get("passed", False) for r in results)
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
