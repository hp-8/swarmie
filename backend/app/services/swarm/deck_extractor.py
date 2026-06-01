"""
Deck extractor.

One `deep`-tier LLM call turns per-page deck text into:
  - structured per-slide reads (classified into the 13 canonical pitch slides,
    each carrying its source page number), and
  - a consolidated ParsedPitch so the existing investor swarm can react.

No vision/OCR — text layer in, structured signal out.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from ...utils.llm import LLM, UsageTracker
from .pitch_parser import ParsedPitch

logger = logging.getLogger("swarmie.swarm.deck_extractor")

# Canonical slide taxonomy (matches the pitch-intelligence rubric).
SLIDE_TYPES = (
    "title", "problem", "solution", "why_now", "market", "product",
    "business_model", "traction", "gtm", "competition", "team",
    "financials", "ask", "other",
)


@dataclass
class SlideRead:
    """One slide's structured read, anchored to its source page."""
    page: int
    slide_type: str
    headline: str = ""
    body: str = ""
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeckRead:
    slides: list[SlideRead]
    pitch: ParsedPitch


_SYSTEM_PROMPT = """You are a venture analyst reading a startup's pitch deck. You receive the deck as per-page text (each chunk tagged with its 1-based page number). Produce a faithful structured read for a fundability stress-test.

Classify EACH page into exactly one canonical slide type:
  title | problem | solution | why_now | market | product | business_model |
  traction | gtm | competition | team | financials | ask | other

For each slide keep its source `page` number, a short `headline` (the slide's
declarative line), a one-paragraph `body` (what the slide actually says), and
`signals` (0-5 short factual tags pulled from the slide — e.g. "$48K MRR",
"22% MoM", "pre-seed", "$1.2M raise", "12k SOM customers"). Never invent
numbers that aren't in the text.

Also produce a consolidated `pitch` object — an investor-lens summary the swarm
will react to. `icp_segments` here are 4-6 INVESTOR archetypes who'd read this
deck (e.g. "operator angel", "thesis-driven seed VC"), NOT customer segments.

Output strict JSON, no markdown fences:
{
  "slides": [
    {"page": <int>, "slide_type": "<one of the canonical types>",
     "headline": "<string>", "body": "<string>", "signals": ["<string>", ...]}
  ],
  "pitch": {
    "one_liner": "", "problem": "", "solution": "", "target_icp": "",
    "icp_segments": ["<investor archetype>", ...],
    "pricing": "", "competitors": ["", ...], "founder_ask": "",
    "traction": "", "team": "", "market": "", "raise_ask": "", "stage": ""
  }
}

Respond with JSON only."""


class DeckExtractor:
    """Per-page deck text -> slide reads + consolidated ParsedPitch (one deep call)."""

    SYSTEM_PROMPT = _SYSTEM_PROMPT

    def __init__(self, tracker: UsageTracker | None = None):
        self.llm = LLM(tier="deep", tracker=tracker)

    def extract(self, pages: list[dict[str, Any]]) -> DeckRead:
        if not pages:
            raise ValueError("no pages to extract")

        deck_text = "\n\n".join(
            f"--- PAGE {p.get('page')} ---\n{p.get('text', '')}" for p in pages
        )
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"DECK ({len(pages)} pages):\n\n{deck_text}\n\nReturn JSON only."},
        ]

        try:
            data = self.llm.chat_json(messages, temperature=0.2, max_tokens=4096)
        except Exception as exc:
            logger.warning("deck extraction LLM call failed: %s", exc)
            data = {}

        slides = self._coerce_slides(data.get("slides", []), pages)
        pitch = self._coerce_pitch(data.get("pitch", {}) or {})
        return DeckRead(slides=slides, pitch=pitch)

    @staticmethod
    def _coerce_slides(raw: Any, pages: list[dict[str, Any]]) -> list[SlideRead]:
        valid_pages = {int(p.get("page")) for p in pages if p.get("page") is not None}
        out: list[SlideRead] = []
        for item in raw or []:
            if not isinstance(item, dict):
                continue
            try:
                page = int(item.get("page"))
            except (TypeError, ValueError):
                continue
            if valid_pages and page not in valid_pages:
                continue
            stype = str(item.get("slide_type") or "other").strip().lower()
            if stype not in SLIDE_TYPES:
                stype = "other"
            out.append(SlideRead(
                page=page,
                slide_type=stype,
                headline=str(item.get("headline") or "").strip(),
                body=str(item.get("body") or "").strip(),
                signals=[str(s).strip() for s in (item.get("signals") or []) if str(s).strip()][:5],
            ))
        out.sort(key=lambda s: s.page)
        return out

    @staticmethod
    def _coerce_pitch(d: dict[str, Any]) -> ParsedPitch:
        def _s(key: str) -> str:
            return str(d.get(key, "") or "").strip()

        def _l(key: str) -> list[str]:
            return [str(x).strip() for x in (d.get(key) or []) if str(x).strip()]

        return ParsedPitch(
            one_liner=_s("one_liner"),
            problem=_s("problem"),
            solution=_s("solution"),
            target_icp=_s("target_icp"),
            icp_segments=_l("icp_segments"),
            pricing=_s("pricing"),
            channels=_l("channels"),
            competitors=_l("competitors"),
            founder_ask=_s("founder_ask") or "Is this fundable at this stage?",
            traction=_s("traction"),
            team=_s("team"),
            market=_s("market"),
            raise_ask=_s("raise_ask"),
            stage=_s("stage"),
        )
