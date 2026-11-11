"""Swarmie backend: Flask app factory."""

from __future__ import annotations

import time

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .extensions import limiter
from .utils.logger import get_logger, setup_logger


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    log = setup_logger()

    # Render sits in front of us: without ProxyFix every client shares the
    # proxy's IP and therefore one rate-limit bucket. 0 disables it.
    hops = app.config.get("TRUSTED_PROXY_HOPS", 1)
    if hops:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops)

    # Return non-ASCII text (pitches, quotes) as-is instead of \uXXXX escapes.
    app.json.ensure_ascii = False

    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", [])}})
    limiter.init_app(app)

    _register_error_handlers(app)
    _register_routes(app)

    # Method + path + status only: request bodies carry users' pitches.
    @app.after_request
    def _log_request(response):
        get_logger("request").debug("%s %s -> %s", request.method, request.path, response.status_code)
        return response

    log.info("Swarmie backend ready")
    return app


def _register_routes(app: Flask) -> None:
    from .api.analytics import analytics_bp
    from .api.billing import billing_bp
    from .api.roast import roast_bp

    app.register_blueprint(roast_bp, url_prefix="/api/roast")
    app.register_blueprint(billing_bp, url_prefix="/api/billing")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "Swarmie Backend"}


def _retry_hint() -> str:
    try:
        seconds_left = limiter.current_limit.reset_at - time.time()
    except Exception:  # no active limit in this request context
        return "Please try again later."
    minutes = max(1, int(seconds_left) // 60 + 1)
    return f"Please try again in about {minutes} minute{'' if minutes == 1 else 's'}."


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(429)
    def too_many_requests(exc):
        limit = getattr(exc, "description", None) or "rate limit exceeded"
        if request.path.endswith("/chat"):
            what = f"You've hit the agent chat limit ({limit})."
        elif request.path.startswith("/api/roast"):
            what = f"You've hit the roast limit ({limit})."
        else:
            what = f"Too many requests ({limit})."
        return jsonify({"error": f"{what} {_retry_hint()}"}), 429

    @app.errorhandler(Exception)
    def unexpected_error(exc):
        if isinstance(exc, HTTPException):
            return exc  # 404/405/413… keep their own responses
        get_logger("errors").exception("unhandled exception on %s %s", request.method, request.path)
        return jsonify({"error": "Something went wrong on our end. Please try again in a moment."}), 500
