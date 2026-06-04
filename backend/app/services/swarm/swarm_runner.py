"""
Swarm runner.

Given a parsed pitch + archetypes, instantiate N concrete agents (sampled from
archetypes by weight) and fan out parallel LLM calls to produce reactions.

Cost-aware:
  - Most agents use the `cheap` tier (one short comment each).
  - A small percentage of "influencer" agents per archetype use the `deep` tier.
  - The `ignore` action is decided BEFORE any LLM call — those agents cost zero.
  - Hard cost ceiling (Config.ROAST_MAX_COST_USD) aborts mid-run if exceeded.

No OASIS, no Zep, no subprocess. Pure async LLM fan-out.
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from ...config import Config
from ...utils.llm import LLM, UsageTracker
from .archetype_generator import Archetype
from .pitch_parser import ParsedPitch

logger = logging.getLogger("swarmie.swarm.swarm_runner")


@dataclass
class AgentReaction:
    """One agent's reaction to the pitch."""
    agent_id: str
    archetype_id: str
    segment: str
    name: str
    tone: str
    action: str  # "post" | "comment" | "upvote" | "ignore"
    text: str = ""  # empty for upvote/ignore
    objections: list[str] = field(default_factory=list)
    sentiment: float = 0.0  # -1..1
    # Why a sampled ignore was scrolled past (empty for silent ignores / speakers).
    ignore_reason: str = ""
    ignore_reason_category: str = ""  # one of _IGNORE_CATEGORIES

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_REACTION_SYSTEM = """You roleplay a single member of an online community reacting to a startup product.

Speak in this persona's authentic voice. Do NOT be polite or hedging by default —
match the persona's tone exactly. Real social-media commenters are blunt, distracted,
sometimes dismissive. Match that energy.

Output strict JSON:
{
  "text": "<the comment / post body, 1-3 sentences, conversational, lowercase ok>",
  "objections": ["<short objection tag>", ...],  // 0-3 tags, e.g. ["price","trust"]
  "sentiment": <float -1..1>                       // -1 = hostile, +1 = excited
}

Rules:
- Stay in character. Tone overrides niceness.
- Reference specifics from the pitch when relevant. Don't generalize.
- If the persona's `tone` is `aggressive` or `skeptical`, push back hard.
- If `indifferent`, be brief and mildly dismissive.
- Never break character or mention the simulation.

Respond with JSON only."""


# --- Ignore-reason sampling (workstream B) ---
# Silence is signal. We don't LLM-call every ignore (that would break the
# zero-token cost model), but we sample a small, capped fraction to get a
# grounded, non-vague reason. The reporter extrapolates the distribution.
IGNORE_SAMPLE_RATE = 0.15
IGNORE_SAMPLE_CAP = 20
_IGNORE_CATEGORIES = (
    "not_my_problem",    # targeting / ICP wrong
    "unclear_value",     # messaging / clarity gap
    "seen_before",       # differentiation gap
    "dont_care",         # weak pain — vitamin, not painkiller
    "price_or_effort",   # positioning / anchor
    "wrong_timing",      # not relevant right now
)

_IGNORE_SYSTEM = """You are one member of an online community who just SCROLLED PAST a startup product without engaging. You did not comment, did not upvote — you ignored it.

In your authentic persona voice, say in ONE blunt first-person sentence why you scrolled past. Be specific to THIS product — never generic. Then classify the reason.

Output strict JSON:
{
  "reason": "<one blunt first-person sentence, lowercase ok, specific to the pitch>",
  "category": "<one of: not_my_problem | unclear_value | seen_before | dont_care | price_or_effort | wrong_timing>"
}

Category guide:
- not_my_problem: I don't have this problem / not for someone like me
- unclear_value: couldn't tell what it does or why it matters
- seen_before: nothing new, already exists, saturated
- dont_care: mild problem, not worth my attention
- price_or_effort: cost or switching effort not worth a closer look
- wrong_timing: relevant someday but not now

Respond with JSON only."""


def _sample_concrete_agents(archetypes: list[Archetype], n_agents: int) -> list[tuple[str, Archetype]]:
    """Sample N concrete agent instances from archetypes by weight."""
    weights = [a.weight for a in archetypes]
    sampled = random.choices(archetypes, weights=weights, k=n_agents)
    return [(f"agent_{i:04d}", arch) for i, arch in enumerate(sampled)]


def _decide_action(archetype: Archetype) -> str:
    """Pick an action for this agent based on its action_likelihood distribution."""
    likelihood = archetype.action_likelihood or {}
    actions = ["post", "comment", "upvote", "ignore"]
    weights = [likelihood.get(a, 0.0) for a in actions]
    if sum(weights) <= 0:
        return "ignore"
    return random.choices(actions, weights=weights, k=1)[0]


class SwarmRunner:
    """Fan-out agent reactions in parallel with strict cost + concurrency caps.

    Per-swarm variation lives in the overridable class attrs (REACTION_SYSTEM,
    IGNORE_SYSTEM, IGNORE_CATEGORIES, DEFAULT_IGNORE_CATEGORY) and the prompt
    builders (`_build_reaction_prompt`, `_build_ignore_prompt`). All cost,
    concurrency, sampling and watchdog logic is shared.
    """

    REACTION_SYSTEM = _REACTION_SYSTEM
    IGNORE_SYSTEM = _IGNORE_SYSTEM
    IGNORE_CATEGORIES = _IGNORE_CATEGORIES
    DEFAULT_IGNORE_CATEGORY = "dont_care"

    def _build_reaction_prompt(self, pitch: ParsedPitch, arch: Archetype, action: str) -> str:
        return (
            f"PRODUCT PITCH:\n"
            f"- one_liner: {pitch.one_liner}\n"
            f"- problem: {pitch.problem}\n"
            f"- solution: {pitch.solution}\n"
            f"- pricing: {pitch.pricing or 'unspecified'}\n"
            f"- competitors: {', '.join(pitch.competitors) or 'none mentioned'}\n\n"
            f"YOU ARE:\n"
            f"- name: {arch.name} (from segment: {arch.segment})\n"
            f"- persona: {arch.persona}\n"
            f"- tone: {arch.tone}\n"
            f"- biases (objections you typically raise): {', '.join(arch.objection_bias)}\n"
            f"- action: {action}\n\n"
            f"Reply in character. JSON only."
        )

    def _build_ignore_prompt(self, pitch: ParsedPitch, arch: Archetype) -> str:
        return (
            f"PRODUCT PITCH:\n"
            f"- one_liner: {pitch.one_liner}\n"
            f"- problem: {pitch.problem}\n"
            f"- solution: {pitch.solution}\n"
            f"- pricing: {pitch.pricing or 'unspecified'}\n\n"
            f"YOU ARE:\n"
            f"- name: {arch.name} (from segment: {arch.segment})\n"
            f"- persona: {arch.persona}\n"
            f"- tone: {arch.tone}\n\n"
            f"You scrolled past without engaging. Why? JSON only."
        )

    def __init__(
        self,
        tracker: UsageTracker | None = None,
        cheap_tier_llm: LLM | None = None,
        deep_tier_llm: LLM | None = None,
        max_cost_usd: float | None = None,
    ):
        self.tracker = tracker or UsageTracker()
        self.cheap = cheap_tier_llm or LLM(tier="cheap", tracker=self.tracker)
        self.deep = deep_tier_llm or LLM(tier="deep", tracker=self.tracker)
        self.max_cost_usd = max_cost_usd if max_cost_usd is not None else Config.ROAST_MAX_COST_USD

    async def run(
        self,
        pitch: ParsedPitch,
        archetypes: list[Archetype],
        n_agents: int | None = None,
        concurrency: int | None = None,
        on_reaction: Callable[[AgentReaction], None] | None = None,
        on_thinking: Callable[[str, Archetype, str], None] | None = None,
        influencer_ratio: float = 0.10,
    ) -> list[AgentReaction]:
        """Run the swarm. Returns the full list of reactions.

        Args:
          on_reaction: optional callback fired as each reaction completes — use
                       this to stream comments to the UI live.
          influencer_ratio: fraction of speaking agents (comment/post) that
                       upgrade to the `deep` tier.
        """
        n_agents = n_agents or Config.ROAST_AGENT_COUNT
        concurrency = concurrency or Config.ROAST_CONCURRENCY

        concrete = _sample_concrete_agents(archetypes, n_agents)

        # Step 1 (free): roll dice for each agent's action.
        rolled: list[tuple[str, Archetype, str]] = [
            (aid, arch, _decide_action(arch)) for aid, arch in concrete
        ]

        # Buckets
        ignores: list[tuple[str, Archetype, str]] = [r for r in rolled if r[2] == "ignore"]
        upvotes: list[tuple[str, Archetype, str]] = [r for r in rolled if r[2] == "upvote"]
        speaking: list[tuple[str, Archetype, str]] = [r for r in rolled if r[2] in ("comment", "post")]

        # Sample a capped fraction of ignores for a grounded "why I scrolled past"
        # reason (cheap tier). The rest stay silent and cost zero tokens.
        random.shuffle(ignores)
        sample_rate = getattr(Config, "ROAST_IGNORE_SAMPLE_RATE", IGNORE_SAMPLE_RATE)
        sample_cap = getattr(Config, "ROAST_IGNORE_SAMPLE_CAP", IGNORE_SAMPLE_CAP)
        n_ignore_sample = min(int(sample_cap), int(len(ignores) * float(sample_rate)))
        ignore_sampled: list[tuple[str, Archetype, str]] = ignores[:n_ignore_sample]
        ignore_silent: list[tuple[str, Archetype, str]] = ignores[n_ignore_sample:]

        # silent ignores + upvotes => zero LLM calls; build reactions immediately.
        reactions: list[AgentReaction] = []
        for aid, arch, action in ignore_silent:
            r = AgentReaction(
                agent_id=aid, archetype_id=arch.id, segment=arch.segment,
                name=arch.name, tone=arch.tone, action="ignore",
            )
            reactions.append(r)
            if on_reaction:
                on_reaction(r)
        for aid, arch, action in upvotes:
            r = AgentReaction(
                agent_id=aid, archetype_id=arch.id, segment=arch.segment,
                name=arch.name, tone=arch.tone, action="upvote", sentiment=0.4,
            )
            reactions.append(r)
            if on_reaction:
                on_reaction(r)

        # Step 2 (expensive): generate text for speaking agents in parallel.
        # Promote a fraction to the `deep` tier for influencer-grade output.
        random.shuffle(speaking)
        n_deep = int(len(speaking) * influencer_ratio)
        deep_set = set(idx for idx in range(n_deep))

        sem = asyncio.Semaphore(concurrency)

        async def _one(idx: int, aid: str, arch: Archetype, action: str) -> AgentReaction:
            llm = self.deep if idx in deep_set else self.cheap
            return await self._generate_reaction(llm, pitch, aid, arch, action, sem, on_reaction, on_thinking)

        async def _one_ignore(aid: str, arch: Archetype) -> AgentReaction:
            return await self._generate_ignore_reason(self.cheap, pitch, aid, arch, sem, on_reaction, on_thinking)

        # Hard cost ceiling: poll tracker periodically and bail.
        task_objs = [
            asyncio.create_task(_one(i, aid, arch, action))
            for i, (aid, arch, action) in enumerate(speaking)
        ]
        # Sampled ignores share the same semaphore, watchdog, and cost ceiling.
        task_objs += [
            asyncio.create_task(_one_ignore(aid, arch))
            for aid, arch, _action in ignore_sampled
        ]

        watchdog = asyncio.create_task(self._cost_watchdog(task_objs))
        try:
            for t in asyncio.as_completed(task_objs):
                reactions.append(await t)
        finally:
            watchdog.cancel()

        return reactions

    async def _generate_reaction(
        self,
        llm: LLM,
        pitch: ParsedPitch,
        agent_id: str,
        arch: Archetype,
        action: str,
        sem: asyncio.Semaphore,
        on_reaction: Callable[[AgentReaction], None] | None,
        on_thinking: Callable[[str, Archetype, str], None] | None = None,
    ) -> AgentReaction:
        async with sem:
            if on_thinking:
                try:
                    on_thinking(agent_id, arch, action)
                except Exception:
                    pass
            user_prompt = self._build_reaction_prompt(pitch, arch, action)
            try:
                data = await llm.achat_json(
                    [
                        {"role": "system", "content": self.REACTION_SYSTEM},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.85,
                    max_tokens=400,
                )
                reaction = AgentReaction(
                    agent_id=agent_id,
                    archetype_id=arch.id,
                    segment=arch.segment,
                    name=arch.name,
                    tone=arch.tone,
                    action=action,
                    text=str(data.get("text", "")).strip(),
                    objections=[str(o).strip() for o in data.get("objections", []) if str(o).strip()],
                    sentiment=float(data.get("sentiment", 0.0)),
                )
            except Exception as exc:
                logger.warning(f"reaction failed for {agent_id}/{arch.id}: {exc}")
                reaction = AgentReaction(
                    agent_id=agent_id, archetype_id=arch.id, segment=arch.segment,
                    name=arch.name, tone=arch.tone, action=action, text="",
                )
            if on_reaction:
                on_reaction(reaction)
            return reaction

    async def _generate_ignore_reason(
        self,
        llm: LLM,
        pitch: ParsedPitch,
        agent_id: str,
        arch: Archetype,
        sem: asyncio.Semaphore,
        on_reaction: Callable[[AgentReaction], None] | None,
        on_thinking: Callable[[str, Archetype, str], None] | None = None,
    ) -> AgentReaction:
        """One cheap-tier call: why this persona scrolled past. Grounded ignore signal."""
        async with sem:
            if on_thinking:
                try:
                    on_thinking(agent_id, arch, "ignore")
                except Exception:
                    pass
            user_prompt = self._build_ignore_prompt(pitch, arch)
            reason = ""
            category = ""
            try:
                data = await llm.achat_json(
                    [
                        {"role": "system", "content": self.IGNORE_SYSTEM},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.8,
                    max_tokens=120,
                )
                reason = str(data.get("reason", "")).strip()
                cat = str(data.get("category", "")).strip()
                category = cat if cat in self.IGNORE_CATEGORIES else self.DEFAULT_IGNORE_CATEGORY
            except Exception as exc:
                logger.warning(f"ignore-reason failed for {agent_id}/{arch.id}: {exc}")
            reaction = AgentReaction(
                agent_id=agent_id, archetype_id=arch.id, segment=arch.segment,
                name=arch.name, tone=arch.tone, action="ignore",
                ignore_reason=reason, ignore_reason_category=category,
            )
            if on_reaction:
                on_reaction(reaction)
            return reaction

    async def _cost_watchdog(self, tasks: list[asyncio.Task]) -> None:
        """Cancel outstanding tasks if cumulative cost exceeds ceiling."""
        while True:
            await asyncio.sleep(2)
            cost = self.tracker.total_cost_usd
            if cost > self.max_cost_usd:
                logger.warning(
                    f"cost ceiling hit (${cost:.4f} > ${self.max_cost_usd:.4f}); cancelling swarm"
                )
                for t in tasks:
                    if not t.done():
                        t.cancel()
                return


# --- Investor swarm overrides ---

_INVESTOR_REACTION_SYSTEM = """You roleplay a single early-stage INVESTOR reacting to a startup deck.

This is a fundability stress-test, not a pitch meeting. React the way this investor
actually would — pattern-matching on thesis fit, team, market, traction, moat.
Be blunt. Real investors are time-pressed and skeptical; most decks get a pass.

Speak in this investor's authentic voice. Do NOT be encouraging by default —
match the persona's tone exactly. Reference specifics from the deck.

Output strict JSON:
{
  "text": "<your reaction: a diligence question, partner-meeting objection, or memo note — 1-3 sentences>",
  "objections": ["<short concern tag>", ...],  // 0-3, e.g. ["market_size","traction"]
  "sentiment": <float -1..1>                     // -1 = hard pass, +1 = would take the meeting
}

Rules:
- Stay in character. Tone overrides niceness.
- If action is `comment`, ask the single sharpest diligence question you'd raise.
- If action is `post`, write the partner-meeting note (would I champion this? why/why not).
- Concern tags from: market_size, team, traction, moat, timing, valuation, business_model, competition, defensibility.
- Never break character or mention the simulation.

Respond with JSON only."""

_INVESTOR_IGNORE_SYSTEM = """You are an early-stage INVESTOR who just PASSED on a startup deck without engaging. No meeting, no reply — you moved on.

In your authentic investor voice, say in ONE blunt first-person sentence why you passed. Be specific to THIS deck — never generic. Then classify the reason.

Output strict JSON:
{
  "reason": "<one blunt first-person sentence, specific to the deck>",
  "category": "<one of: thesis_mismatch | market_too_small | team_risk | no_moat | crowded | traction_thin>"
}

Category guide:
- thesis_mismatch: wrong stage / sector / not our thesis
- market_too_small: TAM doesn't support venture-scale returns
- team_risk: team/founder-market-fit concerns
- no_moat: no defensibility, easily copied
- crowded: me-too, saturated, no clear wedge
- traction_thin: too early, no proof, nothing to underwrite

Respond with JSON only."""

_INVESTOR_IGNORE_CATEGORIES = (
    "thesis_mismatch",
    "market_too_small",
    "team_risk",
    "no_moat",
    "crowded",
    "traction_thin",
)


class InvestorSwarmRunner(SwarmRunner):
    """Investor swarm: deck-reading investors raise questions, objections, and passes."""

    REACTION_SYSTEM = _INVESTOR_REACTION_SYSTEM
    IGNORE_SYSTEM = _INVESTOR_IGNORE_SYSTEM
    IGNORE_CATEGORIES = _INVESTOR_IGNORE_CATEGORIES
    DEFAULT_IGNORE_CATEGORY = "thesis_mismatch"

    def _build_reaction_prompt(self, pitch: ParsedPitch, arch: Archetype, action: str) -> str:
        return (
            f"STARTUP DECK:\n"
            f"- one_liner: {pitch.one_liner}\n"
            f"- problem: {pitch.problem}\n"
            f"- solution: {pitch.solution}\n"
            f"- market: {pitch.market or 'unspecified'}\n"
            f"- traction: {pitch.traction or 'none stated'}\n"
            f"- team: {pitch.team or 'unspecified'}\n"
            f"- business_model: {pitch.pricing or 'unspecified'}\n"
            f"- raise: {pitch.raise_ask or 'unspecified'} (stage: {pitch.stage or 'unspecified'})\n"
            f"- competitors: {', '.join(pitch.competitors) or 'none mentioned'}\n\n"
            f"YOU ARE:\n"
            f"- name: {arch.name} ({arch.segment})\n"
            f"- persona: {arch.persona}\n"
            f"- tone: {arch.tone}\n"
            f"- concerns you typically raise: {', '.join(arch.objection_bias)}\n"
            f"- action: {action}\n\n"
            f"React as this investor. JSON only."
        )

    def _build_ignore_prompt(self, pitch: ParsedPitch, arch: Archetype) -> str:
        return (
            f"STARTUP DECK:\n"
            f"- one_liner: {pitch.one_liner}\n"
            f"- problem: {pitch.problem}\n"
            f"- solution: {pitch.solution}\n"
            f"- market: {pitch.market or 'unspecified'}\n"
            f"- traction: {pitch.traction or 'none stated'}\n"
            f"- team: {pitch.team or 'unspecified'}\n"
            f"- stage: {pitch.stage or 'unspecified'}\n\n"
            f"YOU ARE:\n"
            f"- name: {arch.name} ({arch.segment})\n"
            f"- persona: {arch.persona}\n"
            f"- tone: {arch.tone}\n\n"
            f"You passed without engaging. Why? JSON only."
        )


# --- Launch swarm overrides ---

_LAUNCH_REACTION_SYSTEM = """You roleplay a single member of an online community reacting to a **launch post** in their community.

This is a launch stress-test. React the way this community member actually would —
pattern-matching on whether the product solves a real pain, whether the copy is
clear, whether it's genuinely new, whether it belongs in their community.
Be authentic to your platform and persona.

Speak in this persona's authentic community voice. A PH maker sounds different from
an HN skeptic, a Reddit commenter, or an X reply-guy. Match that energy exactly.
Do NOT be polite or hedging — real launch thread responses are blunt and specific.

Output strict JSON:
{
  "text": "<the comment / post / reaction, 1-3 sentences, in your community's voice, lowercase ok>",
  "objections": ["<short concern tag>", ...],  // 0-3, e.g. ["unclear_value","me_too"]
  "sentiment": <float -1..1>                    // -1 = dismissive, +1 = genuinely excited
}

Rules:
- Stay in character. Your community's tone overrides niceness.
- Reference specifics from the launch copy — never generic feedback.
- If tone is `skeptical` or `aggressive`, push back hard on the weakest point.
- If `indifferent`, be brief and mildly dismissive ("seen this before", "who asked for this").
- If `curious`, ask the one question you'd actually post in the thread.
- Concern tags from: unclear_value, me_too, pricing, show_hn_rigor, hype_fatigue, trust, timing, differentiation.
- Never break character or mention the simulation.

Respond with JSON only."""

_LAUNCH_IGNORE_SYSTEM = """You are one member of an online community who just SCROLLED PAST a launch post without engaging. You did not comment, did not upvote — you ignored it.

In your authentic community-member voice, say in ONE blunt first-person sentence why you scrolled past. Be specific to THIS launch — never generic. Then classify the reason.

Output strict JSON:
{
  "reason": "<one blunt first-person sentence, lowercase ok, specific to the launch>",
  "category": "<one of: unclear_value | seen_before | not_my_community | dont_care | launch_fatigue | wrong_timing>"
}

Category guide:
- unclear_value: couldn't parse what it does or why it matters from the post
- seen_before: another me-too tool, nothing differentiates it
- not_my_community: wrong audience — this isn't for someone like me in this community
- dont_care: mild problem, not worth my attention right now
- launch_fatigue: too many launches like this recently, I'm numb to it
- wrong_timing: might matter later but not relevant to me right now

Respond with JSON only."""

_LAUNCH_IGNORE_CATEGORIES = (
    "unclear_value",
    "seen_before",
    "not_my_community",
    "dont_care",
    "launch_fatigue",
    "wrong_timing",
)


class LaunchSwarmRunner(SwarmRunner):
    """Launch swarm: community members react to a launch post/thread."""

    REACTION_SYSTEM = _LAUNCH_REACTION_SYSTEM
    IGNORE_SYSTEM = _LAUNCH_IGNORE_SYSTEM
    IGNORE_CATEGORIES = _LAUNCH_IGNORE_CATEGORIES
    DEFAULT_IGNORE_CATEGORY = "dont_care"

    def _build_reaction_prompt(self, pitch: ParsedPitch, arch: Archetype, action: str) -> str:
        return (
            f"LAUNCH POST:\n"
            f"- one_liner: {pitch.one_liner}\n"
            f"- problem: {pitch.problem}\n"
            f"- solution: {pitch.solution}\n"
            f"- pricing: {pitch.pricing or 'unspecified'}\n"
            f"- channels: {', '.join(pitch.channels) or 'unspecified'}\n"
            f"- competitors: {', '.join(pitch.competitors) or 'none mentioned'}\n\n"
            f"YOU ARE:\n"
            f"- name: {arch.name} (from community: {arch.segment})\n"
            f"- persona: {arch.persona}\n"
            f"- tone: {arch.tone}\n"
            f"- concerns you typically raise on launch posts: {', '.join(arch.objection_bias)}\n"
            f"- action: {action}\n\n"
            f"React as this community member to this launch. JSON only."
        )

    def _build_ignore_prompt(self, pitch: ParsedPitch, arch: Archetype) -> str:
        return (
            f"LAUNCH POST:\n"
            f"- one_liner: {pitch.one_liner}\n"
            f"- problem: {pitch.problem}\n"
            f"- solution: {pitch.solution}\n"
            f"- pricing: {pitch.pricing or 'unspecified'}\n\n"
            f"YOU ARE:\n"
            f"- name: {arch.name} (from community: {arch.segment})\n"
            f"- persona: {arch.persona}\n"
            f"- tone: {arch.tone}\n\n"
            f"You scrolled past this launch without engaging. Why? JSON only."
        )
