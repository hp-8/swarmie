"""
Swarmie roast pipeline.

Fast, no-Zep founder-validation flow:

    PitchParser  ->  ArchetypeGenerator  ->  SwarmRunner  ->  RoastReporter

Each stage uses the unified LLM client (`app.utils.llm`) with explicit
tier routing so cost is bounded and predictable.
"""

from .pitch_parser import PitchParser, InvestorPitchParser, ParsedPitch
from .archetype_generator import ArchetypeGenerator, InvestorArchetypeGenerator, Archetype
from .swarm_runner import SwarmRunner, InvestorSwarmRunner, AgentReaction
from .roast_reporter import RoastReporter, InvestorReporter, RoastReport
from .agent_chat import chat_with_agent, SOFT_CAP as CHAT_SOFT_CAP
from .registry import SWARMS, DEFAULT_SWARM, SwarmSpec, get_swarm
from .deck_loader import load_pdf, DeckLoadError
from .deck_extractor import DeckExtractor, DeckRead, SlideRead
from .deck_evaluator import DeckEvaluator, DeckDiagnosis

__all__ = [
    "PitchParser",
    "InvestorPitchParser",
    "ParsedPitch",
    "ArchetypeGenerator",
    "InvestorArchetypeGenerator",
    "Archetype",
    "SwarmRunner",
    "InvestorSwarmRunner",
    "AgentReaction",
    "RoastReporter",
    "InvestorReporter",
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
