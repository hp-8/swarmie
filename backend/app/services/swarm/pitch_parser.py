"""
Pitch parser.

Take raw pitch text (deck excerpt, landing-page copy, problem statement)
and extract a structured ParsedPitch the rest of the pipeline can reason about.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from ...utils.llm import LLM, UsageTracker

logger = logging.getLogger("swarmie.swarm.pitch_parser")


@dataclass
class ParsedPitch:
    """Structured representation of a founder pitch."""
    # One-line summary of what the product does.
    one_liner: str = ""
    # Free-text description of the problem the product solves.
    problem: str = ""
    # Free-text description of the proposed solution.
    solution: str = ""
    # Implied ICP (e.g. "B2B SaaS founders, pre-seed, technical").
    target_icp: str = ""
    # 3-5 ICP segments to populate the swarm with.
    icp_segments: list[str] = field(default_factory=list)
    # Pricing model if mentioned (free, freemium, subscription, one-time, etc).
    pricing: str = ""
    # Channels the founder wants to validate through (PH launch, HN, LinkedIn, ads…).
    channels: list[str] = field(default_factory=list)
    # Closest competitors / alternatives, if mentioned.
    competitors: list[str] = field(default_factory=list)
    # What the founder is asking the simulation to evaluate.
    founder_ask: str = ""

    # --- investor-swarm fields (filled only by InvestorPitchParser; empty otherwise) ---
    traction: str = ""   # revenue, users, growth, retention signals if any
    team: str = ""       # founder/team background, why-them
    market: str = ""     # market size / TAM framing
    raise_ask: str = ""  # round + amount being raised, if stated
    stage: str = ""      # pre-seed | seed | series-a | … (inferred ok)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_SYSTEM_PROMPT = """You are a startup analyst. You read a founder's pitch and extract the structured signal a product validation swarm needs.

Output strict JSON with these keys (no extras):
  one_liner       : string  — single sentence, founder's own framing if present
  problem         : string  — pain being solved, plain language
  solution        : string  — how the product solves it
  target_icp      : string  — implied ICP in one short phrase
  icp_segments    : array of 3-5 strings — distinct user segments to simulate
                    (be specific: "indie hackers building SaaS", not "developers")
  pricing         : string  — pricing model if mentioned, else ""
  channels        : array   — distribution channels if mentioned, else []
  competitors     : array   — competitors / alternatives if mentioned, else []
  founder_ask     : string  — what the founder is asking the swarm to evaluate
                    (default: "Will this resonate with the target ICP?")

If the pitch is vague, infer reasonably but mark inferred fields with "[inferred]" prefix.
Never invent competitors that weren't mentioned.

Respond with JSON only. No prose, no markdown fences."""


class PitchParser:
    """Single-shot pitch -> ParsedPitch extractor.

    Uses the `deep` tier because pitch extraction quality cascades into every
    downstream stage. Cost is bounded — one call per sim run.

    Subclasses override SYSTEM_PROMPT (and `_build` if they populate extra
    ParsedPitch fields) to retarget the parser at a different swarm.
    """

    SYSTEM_PROMPT = _SYSTEM_PROMPT

    def __init__(self, tracker: UsageTracker | None = None):
        self.llm = LLM(tier="deep", tracker=tracker)

    def parse(self, pitch_text: str) -> ParsedPitch:
        if not pitch_text or not pitch_text.strip():
            raise ValueError("pitch_text is empty")

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"PITCH:\n\n{pitch_text.strip()}"},
        ]
        data = self.llm.chat_json(messages, temperature=0.2, max_tokens=2500)
        return self._build(data)

    def _build(self, data: dict[str, Any]) -> ParsedPitch:
        return ParsedPitch(
            one_liner=data.get("one_liner", "").strip(),
            problem=data.get("problem", "").strip(),
            solution=data.get("solution", "").strip(),
            target_icp=data.get("target_icp", "").strip(),
            icp_segments=[s.strip() for s in data.get("icp_segments", []) if s.strip()],
            pricing=data.get("pricing", "").strip(),
            channels=[c.strip() for c in data.get("channels", []) if c.strip()],
            competitors=[c.strip() for c in data.get("competitors", []) if c.strip()],
            founder_ask=data.get("founder_ask", "").strip()
                or "Will this resonate with the target ICP?",
        )


_INVESTOR_SYSTEM_PROMPT = """You are a venture analyst. You read a founder's pitch/deck and extract the structured signal an investor swarm needs to pressure-test fundability.

Output strict JSON with these keys (no extras):
  one_liner       : string  — single sentence, founder's own framing if present
  problem         : string  — pain being solved, plain language
  solution        : string  — how the product solves it, the wedge
  target_icp      : string  — the customer ICP in one short phrase
  icp_segments    : array of 4-6 strings — INVESTOR archetypes who'd see this deck
                    (e.g. "operator angel who scaled a SaaS", "thesis-driven seed VC",
                    "generalist pre-seed fund associate", "skeptical multistage partner")
  pricing         : string  — business/revenue model if mentioned, else ""
  channels        : array   — go-to-market channels if mentioned, else []
  competitors     : array   — competitors / alternatives if mentioned, else []
  founder_ask     : string  — the raise framing (default: "Is this fundable at this stage?")
  traction        : string  — revenue / users / growth / retention signals, else ""
  team            : string  — founder & team background, why-them, else ""
  market          : string  — market size / TAM framing if stated, else ""
  raise_ask       : string  — round + amount being raised if stated, else ""
  stage           : string  — pre-seed | seed | series-a | … (infer if unstated)

icp_segments here are INVESTOR personas, NOT customer segments. If the pitch is
vague, infer reasonably but mark inferred fields with "[inferred]" prefix.
Never invent traction or competitors that weren't mentioned.

Respond with JSON only. No prose, no markdown fences."""


class InvestorPitchParser(PitchParser):
    """Parse a deck for the investor swarm: investor archetypes + fundability signal."""

    SYSTEM_PROMPT = _INVESTOR_SYSTEM_PROMPT

    def _build(self, data: dict[str, Any]) -> ParsedPitch:
        pitch = super()._build(data)
        pitch.founder_ask = data.get("founder_ask", "").strip() or "Is this fundable at this stage?"
        pitch.traction = data.get("traction", "").strip()
        pitch.team = data.get("team", "").strip()
        pitch.market = data.get("market", "").strip()
        pitch.raise_ask = data.get("raise_ask", "").strip()
        pitch.stage = data.get("stage", "").strip()
        return pitch


# --- Launch swarm parser ---

_LAUNCH_SYSTEM_PROMPT = """You are a launch strategist. You read a founder's pitch or launch copy and extract the structured signal a community-launch simulation needs.

Output strict JSON with these keys (no extras):
  one_liner       : string  — single sentence, founder's own framing if present
  problem         : string  — pain being solved, plain language
  solution        : string  — how the product solves it
  target_icp      : string  — primary user in one short phrase
  icp_segments    : array of 5-6 strings — COMMUNITY ARCHETYPES who will react to this launch
                    (e.g. "Product Hunt maker hunting new tools",
                    "HN Show-HN skeptic demanding rigor",
                    "subreddit lurker in r/SaaS or r/startups",
                    "Indie Hackers founder comparing to their own tool",
                    "X reply-guy with hot takes",
                    "Reddit power user who's seen every launch")
                    These are community personas, NOT customer segments.
  pricing         : string  — pricing model if mentioned, else ""
  channels        : array   — launch channels if mentioned (e.g. ["Product Hunt","HN Show-HN","Reddit"]), else []
  competitors     : array   — alternatives if mentioned, else []
  founder_ask     : string  — what the founder wants to learn from this launch simulation
                    (default: "What will communities say when this launches?")

If the pitch is vague, infer reasonably but mark inferred fields with "[inferred]" prefix.
Never invent competitors that weren't mentioned.

Respond with JSON only. No prose, no markdown fences."""


class LaunchPitchParser(PitchParser):
    """Parse a pitch for the launch swarm: community archetypes + launch signal."""

    SYSTEM_PROMPT = _LAUNCH_SYSTEM_PROMPT

    def _build(self, data: dict[str, Any]) -> ParsedPitch:
        pitch = super()._build(data)
        pitch.founder_ask = (
            data.get("founder_ask", "").strip()
            or "What will communities say when this launches?"
        )
        return pitch
