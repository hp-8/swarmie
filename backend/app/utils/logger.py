"""Logging setup for the backend.

Everything logs under the ``swarmie`` namespace to stdout, which is what
Render (and docker logs) collect. Modules can keep using
``logging.getLogger("swarmie.<area>")`` directly; ``get_logger`` is a
convenience that guarantees the namespace prefix.
"""

from __future__ import annotations

import logging
import os
import sys

ROOT = "swarmie"
_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def setup_logger(name: str = ROOT, level: int | str | None = None) -> logging.Logger:
    """Attach one stdout handler to ``name`` (idempotent) and return it.

    Level comes from the argument, else LOG_LEVEL, else INFO.
    """
    logger = logging.getLogger(name)
    if not any(getattr(h, "_swarmie", False) for h in logger.handlers):
        # Windows consoles default to a legacy codepage; pitches aren't ASCII.
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_FORMAT))
        handler._swarmie = True  # marker so repeated calls don't stack handlers
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(level or os.environ.get("LOG_LEVEL", "INFO").upper())
    return logger


def get_logger(name: str = ROOT) -> logging.Logger:
    """Logger under the swarmie namespace (``"request"`` → ``swarmie.request``)."""
    if name != ROOT and not name.startswith(ROOT + "."):
        name = f"{ROOT}.{name}"
    return logging.getLogger(name)
