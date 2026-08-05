"""
Swarmie Backend - Flask Application Factory
"""

import os
import time
import warnings

# Suppress multiprocessing resource_tracker warnings (from third-party libs like transformers)
# Must be set before all other imports
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from .config import Config
from .extensions import limiter
from .utils.logger import get_logger, setup_logger


def create_app(config_class=Config):
    """Flask application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure JSON encoding: ensure text is rendered directly (not in \uXXXX format)
    # Flask >= 2.3 uses app.json.ensure_ascii, older versions use JSON_AS_ASCII
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # Setup logger
    logger = setup_logger('swarmie')
    
    # Only log startup info in reloader subprocess (avoid duplicate logs in debug mode)
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process
    
    if should_log_startup:
        logger.info("=" * 50)
        logger.info("Swarmie Backend is starting...")
        logger.info("=" * 50)
    
    # Enable CORS — allowlist only (env CORS_ORIGINS, comma-separated)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", [])}})

    # Per-IP rate limiting (in-memory; flask-limiter honors RATELIMIT_ENABLED)
    limiter.init_app(app)

    @app.errorhandler(429)
    def handle_rate_limit(exc):
        """JSON 429 in the API's standard {error: ...} envelope."""
        desc = getattr(exc, "description", None) or "rate limit exceeded"
        retry_hint = "Please try again later."
        try:
            reset_at = limiter.current_limit.reset_at  # epoch seconds of window reset
            minutes = max(1, int(reset_at - time.time()) // 60 + 1)
            plural = "s" if minutes != 1 else ""
            retry_hint = f"Please try again in about {minutes} minute{plural}."
        except Exception:
            logger.debug("rate-limit retry hint failed; header Retry-After still set by flask-limiter", exc_info=True)
        if request.path.endswith("/chat"):
            msg = f"You've hit the agent chat limit ({desc}). {retry_hint}"
        elif request.path.startswith("/api/roast"):
            msg = f"You've hit the roast limit ({desc}). {retry_hint}"
        else:
            msg = f"Too many requests ({desc}). {retry_hint}"
        return jsonify({"error": msg}), 429

    @app.errorhandler(Exception)
    def handle_unhandled_exception(exc):
        """Catch-all: JSON {error} + 500, real traceback only in server logs."""
        if isinstance(exc, HTTPException):
            return exc  # 404/405/413/429... keep their dedicated handling
        get_logger('swarmie.errors').exception(
            "unhandled exception on %s %s", request.method, request.path
        )
        return jsonify({
            "error": "Something went wrong on our end. Please try again in a moment.",
        }), 500

    # Request logging middleware
    @app.before_request
    def log_request():
        logger = get_logger('swarmie.request')
        logger.debug(f"Request: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"Request Body: {request.get_json(silent=True)}")
    
    @app.after_request
    def log_response(response):
        logger = get_logger('swarmie.request')
        logger.debug(f"Response: {response.status_code}")
        return response
    
    # Register blueprints
    from .api import roast_bp
    app.register_blueprint(roast_bp, url_prefix='/api/roast')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'Swarmie Backend'}
    
    if should_log_startup:
        logger.info("Swarmie Backend started successfully")
    
    return app