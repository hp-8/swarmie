"""
Agent chat — interactive follow-up with a specific swarm agent.

Stateless from LLM's perspective: history is passed in each call. Soft cap on
turns enforced at the route layer.
"""

from __future__ import annotations

from typing import Any

from ...utils.llm import LLM, UsageTracker
from .archetype_generator import Archetype
from .pitch_parser import ParsedPitch

MAX_HISTORY_TURNS = 10
SOFT_CAP = 10  # soft turn cap per agent before paywall prompt

_CHAT_SYSTEM = """You are roleplaying a single online commenter who already reacted to a startup pitch.
The founder is now asking you a follow-up question. Stay in character.

Rules:
- Match the persona's tone exactly (skeptical = push back, aggressive = blunt, indifferent = brief).
- Do NOT break character. Never mention you are an AI or part of a simulation.
- Keep replies short (1-3 sentences). Real commenters don't write essays.
- Reference your prior reaction or biases when relevant.
- Use lowercase / casual punctuation if it fits the persona.
- If founder asks something off-topic or hostile, react how this persona would (not how a polite assistant would).
"""


def build_chat_messages(
    pitch: ParsedPitch | dict,
    archetype: Archetype | dict,
    original_reaction: dict | None,
    history: list[dict[str, str]],
    user_message: str,
) -> list[dict[str, str]]:
    """Build OpenAI-style message list for one chat turn."""
    p = pitch.to_dict() if hasattr(pitch, "to_dict") else (pitch or {})
    a = archetype.to_dict() if hasattr(archetype, "to_dict") else (archetype or {})

    persona_block = (
        f"YOU ARE:\n"
        f"- name: {a.get('name','?')} (segment: {a.get('segment','?')})\n"
        f"- persona: {a.get('persona','')}\n"
        f"- tone: {a.get('tone','neutral')}\n"
        f"- biases: {', '.join(a.get('objection_bias', []) or [])}\n"
    )

    pitch_block = (
        f"\nPITCH UNDER DISCUSSION:\n"
        f"- one_liner: {p.get('one_liner','')}\n"
        f"- problem: {p.get('problem','')}\n"
        f"- solution: {p.get('solution','')}\n"
        f"- pricing: {p.get('pricing') or 'unspecified'}\n"
    )

    reaction_block = ""
    if original_reaction:
        reaction_block = (
            f"\nYOUR ORIGINAL REACTION:\n"
            f"- action: {original_reaction.get('action','')}\n"
            f"- said: \"{original_reaction.get('text','') or '(silent)'}\"\n"
            f"- sentiment: {original_reaction.get('sentiment', 0)}\n"
            f"- objections raised: {', '.join(original_reaction.get('objections') or [])}\n"
        )

    system_content = _CHAT_SYSTEM + "\n\n" + persona_block + pitch_block + reaction_block

    trimmed = (history or [])[-(MAX_HISTORY_TURNS * 2):]
    return [
        {"role": "system", "content": system_content},
        *trimmed,
        {"role": "user", "content": user_message},
    ]


async def chat_with_agent(
    pitch: ParsedPitch | dict,
    archetype: Archetype | dict,
    original_reaction: dict | None,
    history: list[dict[str, str]],
    user_message: str,
    tracker: UsageTracker | None = None,
    llm: LLM | None = None,
) -> str:
    msgs = build_chat_messages(pitch, archetype, original_reaction, history, user_message)
    llm = llm or LLM(tier="cheap", tracker=tracker)
    reply = await llm.achat(msgs, temperature=0.85, max_tokens=300)
    return reply.strip()
