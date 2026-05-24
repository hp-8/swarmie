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

import logging
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
  - the indifferent who'd scroll past (30-40%)

Distribute archetypes accordingly. Do NOT make everyone polite or agreeable.

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

action_likelihood must sum to ~1.0. Realistic baseline: ignore≈0.7, upvote≈0.15,
comment≈0.12, post≈0.03. Adjust per archetype but keep the population realistic.

Respond with JSON only."""


class ArchetypeGenerator:
    """Pitch + segments -> archetype list. Uses the `deep` tier (one call per sim)."""

    def __init__(self, tracker: UsageTracker | None = None):
        self.llm = LLM(tier="deep", tracker=tracker)

    def generate(self, pitch: ParsedPitch, n_archetypes: int = 20) -> list[Archetype]:
        if not pitch.icp_segments:
            raise ValueError("ParsedPitch has no icp_segments; run PitchParser first")

        user_payload = {
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

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"INPUT:\n{user_payload}\n\nReturn JSON only."},
        ]
        data = self.llm.chat_json(messages, temperature=0.7, max_tokens=4096)

        raw = data.get("archetypes", [])
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
    def _coerce_archetype(a: dict[str, Any], fallback_id: str) -> Archetype:
        likelihood = a.get("action_likelihood") or {}
        # normalize to sum 1.0
        total = sum(float(v) for v in likelihood.values()) or 1.0
        normalized = {k: float(v) / total for k, v in likelihood.items()}
        # ensure all four keys present
        for k in ("post", "comment", "upvote", "ignore"):
            normalized.setdefault(k, 0.0)

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
