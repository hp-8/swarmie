"""Local dev server: `uv run python run.py`. Production runs wsgi.py under gunicorn."""

import os
import sys

# Show prints/logs immediately in `npm run dev` instead of when a buffer fills.
os.environ.setdefault("PYTHONUNBUFFERED", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from app import create_app  # noqa: E402  (after the stream setup above)
from app.config import Config  # noqa: E402


def main() -> None:
    problems = Config.validate()
    if problems:
        sys.exit("Fix your .env first:\n" + "\n".join(f"  - {p}" for p in problems))

    port = int(os.environ.get("PORT") or os.environ.get("FLASK_PORT") or 5001)
    create_app().run(
        host=os.environ.get("FLASK_HOST", "0.0.0.0"),
        port=port,
        debug=Config.DEBUG,
        threaded=True,
    )


if __name__ == "__main__":
    main()
