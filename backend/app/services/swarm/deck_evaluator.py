"""
Deck evaluator.

Run the pitch-intelligence EVALUATE rubric (investor lens) over the structured
slide reads to produce a DeckDiagnosis: a slide scorecard, a red-flag index,
strong/weak zones, a funding-readiness %, a skeptical-investor simulation, and
a single next move — every finding cited to its source slide/page.

One `synth`-tier LLM call. Bad JSON or LLM failure degrades to a deterministic
fallback; it never raises.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from ...utils.llm import LLM, UsageTracker
from .deck_extractor import SlideRead

logger = logging.getLogger("swarmie.swarm.deck_evaluator")

_SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")


@dataclass
class DeckDiagnosis:
    """Investor-lens diagnosis of a deck. Page-cited throughout."""
    stage: str = ""
    readiness_pct: float = 0.0          # 0..100
    overall_score: int = 0              # 0..130
    slides: list[dict[str, Any]] = field(default_factory=list)
    # each: {slide_type, page, score(0-10), verdict, top_issue}
    red_flags: list[dict[str, Any]] = field(default_factory=list)
    # each: {severity, slide_type, page, text}
    strong_zones: list[str] = field(default_factory=list)
    weak_zones: list[str] = field(default_factory=list)
    investor_simulation: str = ""
    next_move: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Ported from the pitch-intelligence skill, MODE 2: EVALUATE.
_SYSTEM_PROMPT = """You are a skeptical seed-stage investor evaluating a startup pitch deck. You operate from the investor's perspective at all times. Generic advice is prohibited — every observation must reference the specific company, slide, and page.

You receive the deck as structured per-slide reads (each with its source `page`,
`slide_type`, headline, body, and signal tags). Diagnose fundability.

RULES (non-negotiable):
- Specificity: never say anything that could apply to any startup. Cite the slide and page.
- Investor lens: frame as "this signals to the investor that…", not "you should…".
- Market sizing: reject top-down TAM ("1% of $40B"). Demand bottoms-up SOM with a customer count.
- Traction credibility order: Revenue > Signed Contracts > LOIs > Paid Pilots > Beta+retention > Waitlist. Never let a lower tier pass as a higher one. Signups/pageviews/followers are vanity.
- The ask must be specific and milestone-tied ("raising X to hit Y by Z"). Vague ranges are a red flag.
- Design/clarity is a proxy for execution.
- Calibrate to stage: do not hold a pre-seed deck to a Series A bar, but flag when a deck presents below its stage baseline.

Output strict JSON, no markdown fences:
{
  "stage": "<idea|pre-seed|seed|series-a|growth — infer if unstated>",
  "readiness_pct": <0-100, funding readiness>,
  "overall_score": <0-130, sum of the slide scores you assign>,
  "slides": [
    {"slide_type": "<canonical type>", "page": <int from the input>,
     "score": <0-10>, "verdict": "<<=6 words>", "top_issue": "<one specific line>"}
  ],
  "red_flags": [
    {"severity": "CRITICAL|HIGH|MEDIUM|LOW", "slide_type": "<type>", "page": <int>,
     "text": "<specific, blunt — what an investor will think>"}
  ],
  "strong_zones": ["<short phrase>", ...],
  "weak_zones": ["<short phrase>", ...],
  "investor_simulation": "<3-4 sentences in a skeptical seed investor's voice; do not be gentle>",
  "next_move": "<the single most important thing to fix before the next investor conversation>"
}

Score every slide present in the input, carrying its exact `page`. Respond with JSON only."""


class DeckEvaluator:
    """Slide reads -> DeckDiagnosis via the pitch-intelligence rubric (one synth call)."""

    SYSTEM_PROMPT = _SYSTEM_PROMPT

    def __init__(self, tracker: UsageTracker | None = None):
        self.llm = LLM(tier="synth", tracker=tracker)

    def evaluate(self, slides: list[SlideRead], stage: str = "") -> DeckDiagnosis:
        slide_payload = [
            {
                "page": s.page,
                "slide_type": s.slide_type,
                "headline": s.headline,
                "body": s.body[:600],
                "signals": s.signals,
            }
            for s in slides
        ]
        valid_pages = {s.page for s in slides}

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"DECK SLIDES (stage hint: {stage or 'unspecified'}):\n"
                    f"{slide_payload}\n\nReturn JSON only."
                ),
            },
        ]

        try:
            data = self.llm.chat_json(messages, temperature=0.3, max_tokens=2200)
        except Exception as exc:
            logger.warning("deck evaluation failed: %s; using deterministic fallback", exc)
            return self._fallback(slides, stage)

        try:
            return self._coerce(data, valid_pages, stage)
        except Exception as exc:
            logger.warning("deck diagnosis coercion failed: %s; using fallback", exc)
            return self._fallback(slides, stage)

    @staticmethod
    def _clamp(v: Any, lo: float, hi: float, default: float) -> float:
        try:
            return max(lo, min(hi, float(v)))
        except (TypeError, ValueError):
            return default

    def _coerce(self, data: dict[str, Any], valid_pages: set[int], stage: str) -> DeckDiagnosis:
        slides_out: list[dict[str, Any]] = []
        for s in data.get("slides", []) or []:
            if not isinstance(s, dict):
                continue
            try:
                page = int(s.get("page"))
            except (TypeError, ValueError):
                continue
            if valid_pages and page not in valid_pages:
                continue
            slides_out.append({
                "slide_type": str(s.get("slide_type") or "other").strip().lower(),
                "page": page,
                "score": int(self._clamp(s.get("score"), 0, 10, 0)),
                "verdict": str(s.get("verdict") or "").strip(),
                "top_issue": str(s.get("top_issue") or "").strip(),
            })

        red_flags: list[dict[str, Any]] = []
        for rf in data.get("red_flags", []) or []:
            if not isinstance(rf, dict):
                continue
            sev = str(rf.get("severity") or "MEDIUM").strip().upper()
            if sev not in _SEVERITIES:
                sev = "MEDIUM"
            page_raw = rf.get("page")
            try:
                page = int(page_raw)
            except (TypeError, ValueError):
                page = 0
            red_flags.append({
                "severity": sev,
                "slide_type": str(rf.get("slide_type") or "").strip().lower(),
                "page": page,
                "text": str(rf.get("text") or "").strip(),
            })

        return DeckDiagnosis(
            stage=str(data.get("stage") or stage or "").strip(),
            readiness_pct=round(self._clamp(data.get("readiness_pct"), 0, 100, 0.0), 1),
            overall_score=int(self._clamp(data.get("overall_score"), 0, 130, sum(s["score"] for s in slides_out))),
            slides=slides_out,
            red_flags=red_flags,
            strong_zones=[str(z).strip() for z in (data.get("strong_zones") or []) if str(z).strip()],
            weak_zones=[str(z).strip() for z in (data.get("weak_zones") or []) if str(z).strip()],
            investor_simulation=str(data.get("investor_simulation") or "").strip(),
            next_move=str(data.get("next_move") or "").strip(),
        )

    @staticmethod
    def _fallback(slides: list[SlideRead], stage: str) -> DeckDiagnosis:
        present = {s.slide_type for s in slides}
        canonical = {"problem", "solution", "market", "traction", "team", "ask"}
        missing = sorted(canonical - present)
        weak = [f"missing or weak: {m}" for m in missing]
        return DeckDiagnosis(
            stage=stage or "unspecified",
            readiness_pct=0.0,
            overall_score=0,
            slides=[{"slide_type": s.slide_type, "page": s.page, "score": 0,
                     "verdict": "not scored", "top_issue": "automated diagnosis unavailable"} for s in slides],
            red_flags=[],
            strong_zones=[],
            weak_zones=weak,
            investor_simulation="The automated diagnosis could not be generated for this deck. Review the slide scorecard manually.",
            next_move="Re-run the diagnosis, or paste the deck text directly.",
        )
