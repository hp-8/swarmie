"""
Archetype generator.

Given a parsed pitch + ICP segments, produce N agent archetypes that populate
the swarm. Each archetype carries a personality + objection bias so the
downstream SwarmRunner can generate distinct, non-vanilla reactions.

This is a placeholder for the eventual real-corpus-grounded version (Phase 2),
which will replace LLM-hallucinated personas with personas sampled from
tagged Reddit/HN/PH corpora.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from ...utils.llm import LLM, UsageTracker
from .pitch_parser import ParsedPitch

logger = logging.getLogger("swarmie.swarm.archetype_generator")


@dataclass
class Archetype:
    """A single agent archetype. Many concrete agents are sampled from one archetype."""
    id: str
    segment: str  # parent ICP segment label
    name: str  # short handle (no real PII)
    persona: str  # 2-3 sentence character description
    tone: str  # "skeptical" | "enthusiastic" | "neutral" | "aggressive" | "curious" | "indifferent"
    objection_bias: list[str]  # e.g. ["price", "trust", "timing"]
    action_likelihood: dict[str, float]  # P(post | comment | upvote | ignore)
    weight: float = 1.0  # sampling weight; higher = more agents instantiated

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_SYSTEM_PROMPT = """You design archetype profiles for a startup-validation simulation.

Given a parsed pitch and a list of ICP segments, output N archetypes whose
COLLECTIVE reactions will resemble how the segments would behave on social
media (Reddit / HN / X / ProductHunt) if shown this product.

Be realistic. Real audiences include:
  - skeptics and trolls (15-20%)
  - the curious but uncommitted (35-40%)
  - genuine enthusiasts (10-15%)
  - the indifferent who'd scroll past (15-20%)

Distribute archetypes accordingly. Do NOT make everyone polite or agreeable.
This is a FEEDBACK simulation — every agent was asked to evaluate the pitch.
Most should engage (comment, post, or upvote), not silently ignore.

Output strict JSON:
{
  "archetypes": [
    {
      "id": "<short snake_case id>",
      "segment": "<one of the input ICP segments>",
      "name": "<short handle, e.g. 'JadedDevOps'; never real names>",
      "persona": "<2-3 sentences: background, motivations, what they care about>",
      "tone": "skeptical|enthusiastic|neutral|aggressive|curious|indifferent",
      "objection_bias": ["price","trust","timing","fit","competitor","tech","ux"],
      "action_likelihood": {"post": 0.0, "comment": 0.0, "upvote": 0.0, "ignore": 0.0},
      "weight": 1.0
    }
  ]
}

action_likelihood must sum to ~1.0. Baseline: comment≈0.40, upvote≈0.25,
ignore≈0.20, post≈0.15. Keep ignore between 0.15–0.30 for ALL archetypes.
Adjust per archetype — skeptics comment more, enthusiasts upvote/post more,
indifferent ones lean toward ignore (but never above 0.30).

Respond with JSON only."""


class ArchetypeGenerator:
    """Pitch + segments -> archetype list. Uses the `deep` tier (one call per sim).

    Subclasses override SYSTEM_PROMPT (and `_build_payload` for extra signal) to
    retarget the generator at a different swarm.
    """

    SYSTEM_PROMPT = _SYSTEM_PROMPT

    def __init__(self, tracker: UsageTracker | None = None):
        self.llm = LLM(tier="deep", tracker=tracker)

    def _build_payload(self, pitch: ParsedPitch, n_archetypes: int) -> dict[str, Any]:
        return {
            "n_archetypes": n_archetypes,
            "pitch": {
                "one_liner": pitch.one_liner,
                "problem": pitch.problem,
                "solution": pitch.solution,
                "target_icp": pitch.target_icp,
                "pricing": pitch.pricing,
            },
            "icp_segments": pitch.icp_segments,
        }

    def generate(self, pitch: ParsedPitch, n_archetypes: int = 12) -> list[Archetype]:
        if not pitch.icp_segments:
            raise ValueError("ParsedPitch has no icp_segments; run PitchParser first")

        user_payload = self._build_payload(pitch, n_archetypes)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"INPUT:\n{user_payload}\n\nReturn JSON only."},
        ]

        # Try the strict json_object path first; fall back to text + partial-recovery
        # if the LLM truncates output (large archetype counts often blow past max_tokens).
        try:
            data = self.llm.chat_json(messages, temperature=0.7, max_tokens=8192)
            raw = data.get("archetypes", [])
        except ValueError as exc:
            logger.warning(f"chat_json failed ({exc}); attempting partial-array recovery")
            raw_text = self.llm.chat(messages, temperature=0.7, max_tokens=8192)
            raw = self._extract_archetypes_from_partial(raw_text)
            if not raw:
                raise

        archetypes: list[Archetype] = []
        for i, a in enumerate(raw):
            try:
                archetypes.append(self._coerce_archetype(a, fallback_id=f"arch_{i}"))
            except Exception as exc:
                logger.warning(f"skipped malformed archetype: {exc}; raw={a}")
        if not archetypes:
            raise ValueError("LLM returned no usable archetypes")
        return archetypes

    @staticmethod
    def _extract_archetypes_from_partial(text: str) -> list[dict[str, Any]]:
        """Recover as many complete archetype objects as possible from truncated JSON.

        Walks the `"archetypes": [` array and parses each balanced `{...}` block
        until it can't. Tolerates a truncated final object and an unclosed array.
        """
        # Strip code fences if any
        text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text)

        # Locate the start of the archetypes array.
        m = re.search(r'"archetypes"\s*:\s*\[', text)
        if not m:
            return []
        i = m.end()
        n = len(text)
        items: list[dict[str, Any]] = []

        while i < n:
            # Skip whitespace and commas between objects.
            while i < n and text[i] in " \t\n\r,":
                i += 1
            if i >= n or text[i] != "{":
                break
            # Walk until matching `}` while respecting string boundaries.
            depth = 0
            start = i
            in_str = False
            escape = False
            j = i
            while j < n:
                ch = text[j]
                if escape:
                    escape = False
                elif ch == "\\" and in_str:
                    escape = True
                elif ch == '"':
                    in_str = not in_str
                elif not in_str:
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            j += 1
                            break
                j += 1
            if depth != 0:
                # truncated mid-object — stop
                break
            chunk = text[start:j]
            try:
                items.append(json.loads(chunk))
            except json.JSONDecodeError:
                pass
            i = j
        return items

    @staticmethod
    def _coerce_archetype(a: dict[str, Any], fallback_id: str) -> Archetype:
        likelihood = a.get("action_likelihood") or {}
        # normalize to sum 1.0
        total = sum(float(v) for v in likelihood.values()) or 1.0
        normalized = {k: float(v) / total for k, v in likelihood.items()}
        # ensure all four keys present
        for k in ("post", "comment", "upvote", "ignore"):
            normalized.setdefault(k, 0.0)
        # clamp ignore to [0.15, 0.30] and redistribute excess
        ign = normalized.get("ignore", 0.0)
        if ign > 0.30:
            excess = ign - 0.30
            normalized["ignore"] = 0.30
            others = [k for k in ("post", "comment", "upvote") if normalized[k] > 0]
            if others:
                share = excess / len(others)
                for k in others:
                    normalized[k] += share
        elif ign < 0.15:
            deficit = 0.15 - ign
            normalized["ignore"] = 0.15
            others = [k for k in ("post", "comment", "upvote") if normalized[k] > deficit / 3]
            if others:
                share = deficit / len(others)
                for k in others:
                    normalized[k] -= share

        return Archetype(
            id=str(a.get("id") or fallback_id),
            segment=str(a.get("segment") or "unknown"),
            name=str(a.get("name") or fallback_id),
            persona=str(a.get("persona") or ""),
            tone=str(a.get("tone") or "neutral"),
            objection_bias=list(a.get("objection_bias") or []),
            action_likelihood=normalized,
            weight=float(a.get("weight") or 1.0),
        )


_INVESTOR_SYSTEM_PROMPT = """You design INVESTOR archetype profiles for a fundability stress-test.

Given a parsed deck and a list of investor archetypes, output N archetypes whose
COLLECTIVE reactions resemble how real early-stage investors would respond to this
deck landing in their inbox — partner-meeting questions, objections, and passes.

This is decision stress-testing, NOT roleplay. Ground each archetype in real
investor behavior patterns (thesis fit, pattern-matching, risk allocation).

Be realistic. A real cap-table funnel includes:
  - hard skeptics who pass fast on thesis/stage fit (25-35%)
  - the diligent who probe traction, moat, team before deciding (30-40%)
  - thesis-aligned believers who lean in (10-20%)
  - the politely-passing who never really engage (15-25%)

Distribute archetypes accordingly. Do NOT make everyone enthusiastic. Most should
engage (ask a question, write a note, or signal interest), not silently pass.

Output strict JSON:
{
  "archetypes": [
    {
      "id": "<short snake_case id>",
      "segment": "<one of the input investor archetypes>",
      "name": "<short handle, e.g. 'ThesisDrivenSeed'; never real names>",
      "persona": "<2-3 sentences: fund type, check size, thesis, what they pattern-match on>",
      "tone": "skeptical|enthusiastic|neutral|aggressive|curious|indifferent",
      "objection_bias": ["market_size","team","traction","moat","timing","valuation","business_model","competition","defensibility"],
      "action_likelihood": {"post": 0.0, "comment": 0.0, "upvote": 0.0, "ignore": 0.0},
      "weight": 1.0
    }
  ]
}

action mapping for investors:
  post   = writes a detailed memo / partner-meeting note (deep engagement)
  comment= asks a sharp diligence question or raises an objection
  upvote = soft interest / "send me more" without committing
  ignore = passes without engaging

action_likelihood must sum to ~1.0. Baseline: comment≈0.45, post≈0.15,
upvote≈0.20, ignore≈0.20. Keep ignore between 0.15–0.30 for ALL archetypes.
Skeptics comment/probe more; thesis-aligned believers post/upvote more.

Respond with JSON only."""


class InvestorArchetypeGenerator(ArchetypeGenerator):
    """Investor archetypes (angel / operator / VC patterns) reading a deck."""

    SYSTEM_PROMPT = _INVESTOR_SYSTEM_PROMPT

    def _build_payload(self, pitch: ParsedPitch, n_archetypes: int) -> dict[str, Any]:
        return {
            "n_archetypes": n_archetypes,
            "deck": {
                "one_liner": pitch.one_liner,
                "problem": pitch.problem,
                "solution": pitch.solution,
                "market": pitch.market,
                "traction": pitch.traction,
                "team": pitch.team,
                "business_model": pitch.pricing,
                "raise_ask": pitch.raise_ask,
                "stage": pitch.stage,
                "competitors": pitch.competitors,
            },
            "investor_archetypes": pitch.icp_segments,
        }
