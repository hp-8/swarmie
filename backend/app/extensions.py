"""
Flask extensions instantiated unbound (bound to the app in create_app).

Lives in its own module so blueprints can import the limiter for route
decorators without circular imports through the app factory.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Per-IP rate limiter. In-memory storage is deliberate: single-instance deploy
# (Render, 1 gunicorn worker). Revisit (Redis storage) if we ever scale out.
# No default_limits — only token-burning routes opt in via @limiter.limit;
# reads and the long-lived SSE stream stay unlimited.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    headers_enabled=True,  # send X-RateLimit-* + Retry-After on responses
)
