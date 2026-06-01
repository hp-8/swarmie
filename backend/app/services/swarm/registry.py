"""
Swarm registry.

Each swarm is one founder decision answered by a verdict + next action. A swarm
is a bundle of the four pipeline stage classes plus light display config. The
API resolves a `swarm_type` to a SwarmSpec and instantiates that swarm's stages;
all cost, concurrency, streaming and storage plumbing is shared.

Adding a swarm = subclass the stages (see InvestorPitchParser et al.) and
register the bundle here. No changes to the pipeline runner required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Type

from .archetype_generator import ArchetypeGenerator, InvestorArchetypeGenerator, LaunchArchetypeGenerator
from .pitch_parser import InvestorPitchParser, LaunchPitchParser, PitchParser
from .roast_reporter import InvestorReporter, LaunchReporter, RoastReporter
from .swarm_runner import InvestorSwarmRunner, LaunchSwarmRunner, SwarmRunner


@dataclass(frozen=True)
class SwarmSpec:
    """One swarm: its four pipeline stages + display metadata for the UI."""
    key: str
    label: str            # short display name ("Validate", "Investor")
    blurb: str            # one-line description of the decision it answers
    agent_noun: str       # what one agent is called ("commenter", "investor")
    parser_cls: Type[PitchParser]
    archgen_cls: Type[ArchetypeGenerator]
    runner_cls: Type[SwarmRunner]
    reporter_cls: Type[RoastReporter]
    n_archetypes: int = 12

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "blurb": self.blurb,
            "agent_noun": self.agent_noun,
        }


SWARMS: dict[str, SwarmSpec] = {
    "validate": SwarmSpec(
        key="validate",
        label="Validate",
        blurb="Stress-test positioning against a swarm reacting like a Reddit/HN/PH thread.",
        agent_noun="commenter",
        parser_cls=PitchParser,
        archgen_cls=ArchetypeGenerator,
        runner_cls=SwarmRunner,
        reporter_cls=RoastReporter,
    ),
    "investor": SwarmSpec(
        key="investor",
        label="Investor",
        blurb="Stress-test fundability against patterns from real investor behavior.",
        agent_noun="investor",
        parser_cls=InvestorPitchParser,
        archgen_cls=InvestorArchetypeGenerator,
        runner_cls=InvestorSwarmRunner,
        reporter_cls=InvestorReporter,
    ),
    "launch": SwarmSpec(
        key="launch",
        label="Launch",
        blurb="Stress-test how startup communities will react to your launch.",
        agent_noun="commenter",
        parser_cls=LaunchPitchParser,
        archgen_cls=LaunchArchetypeGenerator,
        runner_cls=LaunchSwarmRunner,
        reporter_cls=LaunchReporter,
    ),
}

DEFAULT_SWARM = "validate"


def get_swarm(swarm_type: str | None) -> SwarmSpec:
    """Resolve a swarm_type to its spec, falling back to the default."""
    return SWARMS.get((swarm_type or DEFAULT_SWARM).strip().lower(), SWARMS[DEFAULT_SWARM])
