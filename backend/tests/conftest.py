"""Pytest bootstrap — make the suite hermetic.

`app/config.py` raises at import time if SECRET_KEY is unset. Tests must not
depend on the developer's ambient shell / .env (CI has neither), so set a
test default BEFORE any `from app...` import runs. `setdefault` means a real
env value (local dev) still wins.
"""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")
# Intentionally leave LLM_API_KEY unset: the suite must be offline-safe.
# Anything needing the LLM should mock it or skip without a key.
