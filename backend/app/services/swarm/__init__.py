"""
Swarmie roast pipeline.

Fast, no-Zep founder-validation flow:

    PitchParser  ->  ArchetypeGenerator  ->  SwarmRunner  ->  RoastReporter

Each stage uses the unified LLM client (`app.utils.llm`) with explicit
tier routing so cost is bounded and predictable.
"""

from .pitch_parser import PitchParser, InvestorPitchParser, LaunchPitchParser, ParsedPitch
from .archetype_generator import ArchetypeGenerator, InvestorArchetypeGenerator, LaunchArchetypeGenerator, Archetype
from .swarm_runner import (
    SwarmRunner,
    InvestorSwarmRunner,
    LaunchSwarmRunner,
    AgentReaction,
    CostCeilingExceeded,
)
from .roast_reporter import RoastReporter, InvestorReporter, LaunchReporter, RoastReport
from .agent_chat import chat_with_agent, SOFT_CAP as CHAT_SOFT_CAP
from .registry import SWARMS, DEFAULT_SWARM, SwarmSpec, get_swarm
from .deck_loader import load_pdf, DeckLoadError
from .deck_extractor import DeckExtractor, DeckRead, SlideRead
from .deck_evaluator import DeckEvaluator, DeckDiagnosis

__all__ = [
    "PitchParser",
    "InvestorPitchParser",
    "LaunchPitchParser",
    "ParsedPitch",
    "ArchetypeGenerator",
    "InvestorArchetypeGenerator",
    "LaunchArchetypeGenerator",
    "Archetype",
    "SwarmRunner",
    "InvestorSwarmRunner",
    "LaunchSwarmRunner",
    "AgentReaction",
    "CostCeilingExceeded",
    "RoastReporter",
    "InvestorReporter",
    "LaunchReporter",
    "RoastReport",
    "chat_with_agent",
    "CHAT_SOFT_CAP",
    "SWARMS",
    "DEFAULT_SWARM",
    "SwarmSpec",
    "get_swarm",
    "load_pdf",
    "DeckLoadError",
    "DeckExtractor",
    "DeckRead",
    "SlideRead",
    "DeckEvaluator",
    "DeckDiagnosis",
]
