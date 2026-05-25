"""
Gunicorn WSGI entrypoint for production.

Render runs: gunicorn --bind 0.0.0.0:$PORT wsgi:app
"""

import os

# Production-safe defaults — Config.validate() exits if LLM_API_KEY is missing,
# which is the right behavior on Render (fail fast in build/deploy logs).
os.environ.setdefault("PYTHONUNBUFFERED", "1")
os.environ.setdefault("FLASK_HOST", "0.0.0.0")

from app import create_app  # noqa: E402
from app.config import Config  # noqa: E402

errors = Config.validate()
if errors:
    # Print to stderr so Render captures it in deploy logs.
    import sys
    print("Configuration errors:", file=sys.stderr)
    for err in errors:
        print(f"  - {err}", file=sys.stderr)
    raise SystemExit(1)

app = create_app()
