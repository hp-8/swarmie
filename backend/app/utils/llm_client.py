"""
Backwards-compatibility shim.

The original `LLMClient` lived here. It has been replaced by the unified
multi-tier client in `swarmie.utils.llm`. Existing imports continue to
work via this re-export.

New code should import directly from `.llm`:

    from app.utils.llm import LLM, UsageTracker
"""

from .llm import LLM, LLMClient, Usage, UsageTracker

__all__ = ["LLM", "LLMClient", "Usage", "UsageTracker"]
