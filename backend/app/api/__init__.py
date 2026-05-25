"""API route blueprints."""

import logging

from flask import Blueprint

_log = logging.getLogger("swarmie.api")

graph_bp = Blueprint("graph", __name__)
simulation_bp = Blueprint("simulation", __name__)
report_bp = Blueprint("report", __name__)

# Legacy MiroFish pipeline (Zep + OASIS). Heavy deps not installed in slim
# production builds; wrap so the Swarmie roast path still boots.
LEGACY_AVAILABLE = True
try:
    from . import graph  # noqa: E402, F401
    from . import simulation  # noqa: E402, F401
    from . import report  # noqa: E402, F401
except ImportError as exc:
    LEGACY_AVAILABLE = False
    _log.warning("Legacy blueprints disabled (slim install): %s", exc)

# Swarmie roast pipeline (fast founder validation). Required.
from .roast import roast_bp  # noqa: E402

__all__ = ["graph_bp", "simulation_bp", "report_bp", "roast_bp", "LEGACY_AVAILABLE"]
