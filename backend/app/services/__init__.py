"""
业务服务模块.

This package intentionally does NOT re-export submodules. The legacy
MiroFish pipeline (graph_builder, simulation_runner, zep_*, oasis_*)
depends on heavy optional packages (camel-ai, zep-cloud, oasis) that are
not installed in slim production builds for the Swarmie roast pipeline.

Import submodules directly:
    from .services.swarm import SwarmRunner          # always available
    from .services.simulation_runner import ...      # legacy only
"""
