"""
Swarmie roast pipeline.

Fast, no-Zep founder-validation flow:

    PitchParser  ->  ArchetypeGenerator  ->  SwarmRunner  ->  RoastReporter

Each stage uses the unified LLM client (`app.utils.llm`) with explicit
tier routing so cost is bounded and predictable.
"""

from .agent_chat import SOFT_CAP as CHAT_SOFT_CAP
from .agent_chat import chat_with_agent
from .archetype_generator import (
    Archetype,
    ArchetypeGenerator,
    InvestorArchetypeGenerator,
    LaunchArchetypeGenerator,
)
from .deck_evaluator import DeckDiagnosis, DeckEvaluator
from .deck_extractor import DeckExtractor, DeckRead, SlideRead
from .deck_loader import DeckLoadError, load_pdf
from .pitch_parser import InvestorPitchParser, LaunchPitchParser, ParsedPitch, PitchParser
from .registry import DEFAULT_SWARM, SWARMS, SwarmSpec, get_swarm
from .roast_reporter import InvestorReporter, LaunchReporter, RoastReport, RoastReporter
from .swarm_runner import (
    AgentReaction,
    CostCeilingExceeded,
    InvestorSwarmRunner,
    LaunchSwarmRunner,
    SwarmRunner,
)

__all__ = [
    "CHAT_SOFT_CAP",
    "DEFAULT_SWARM",
    "SWARMS",
    "AgentReaction",
    "Archetype",
    "ArchetypeGenerator",
    "CostCeilingExceeded",
    "DeckDiagnosis",
    "DeckEvaluator",
    "DeckExtractor",
    "DeckLoadError",
    "DeckRead",
    "InvestorArchetypeGenerator",
    "InvestorPitchParser",
    "InvestorReporter",
    "InvestorSwarmRunner",
    "LaunchArchetypeGenerator",
    "LaunchPitchParser",
    "LaunchReporter",
    "LaunchSwarmRunner",
    "ParsedPitch",
    "PitchParser",
    "RoastReport",
    "RoastReporter",
    "SlideRead",
    "SwarmRunner",
    "SwarmSpec",
    "chat_with_agent",
    "get_swarm",
    "load_pdf",
]
