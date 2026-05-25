"""
Swarmie roast pipeline.

Fast, no-Zep founder-validation flow:

    PitchParser  ->  ArchetypeGenerator  ->  SwarmRunner  ->  RoastReporter

Each stage uses the unified LLM client (`app.utils.llm`) with explicit
tier routing so cost is bounded and predictable.
"""

from .pitch_parser import PitchParser, ParsedPitch
from .archetype_generator import ArchetypeGenerator, Archetype
from .swarm_runner import SwarmRunner, AgentReaction
from .roast_reporter import RoastReporter, RoastReport
from .agent_chat import chat_with_agent, SOFT_CAP as CHAT_SOFT_CAP

__all__ = [
    "PitchParser",
    "ParsedPitch",
    "ArchetypeGenerator",
    "Archetype",
    "SwarmRunner",
    "AgentReaction",
    "RoastReporter",
    "RoastReport",
    "chat_with_agent",
    "CHAT_SOFT_CAP",
]
