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
import time
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
    """Fan-out agent reactions in parallel with strict cost + concurrency caps."""

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

        # ignores + upvotes => zero LLM calls; build reactions immediately.
        reactions: list[AgentReaction] = []
        for aid, arch, action in ignores:
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
            return await self._generate_reaction(llm, pitch, aid, arch, action, sem, on_reaction)

        # Hard cost ceiling: poll tracker periodically and bail.
        task_objs = [
            asyncio.create_task(_one(i, aid, arch, action))
            for i, (aid, arch, action) in enumerate(speaking)
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
    ) -> AgentReaction:
        async with sem:
            user_prompt = (
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
            try:
                data = await llm.achat_json(
                    [
                        {"role": "system", "content": _REACTION_SYSTEM},
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
