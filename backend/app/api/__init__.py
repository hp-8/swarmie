"""API route blueprints."""

from flask import Blueprint

graph_bp = Blueprint("graph", __name__)
simulation_bp = Blueprint("simulation", __name__)
report_bp = Blueprint("report", __name__)

# Legacy MiroFish pipeline (deep / Zep-backed simulation).
from . import graph  # noqa: E402, F401
from . import simulation  # noqa: E402, F401
from . import report  # noqa: E402, F401

# Swarmie roast pipeline (fast founder validation).
from .roast import roast_bp  # noqa: E402

__all__ = ["graph_bp", "simulation_bp", "report_bp", "roast_bp"]
