"""Configuration. All env-loaded from project-root `.env`."""

import os

from dotenv import load_dotenv

# Load .env from project root (../../.env relative to this file).
_root_env = os.path.join(os.path.dirname(__file__), "../../.env")
if os.path.exists(_root_env):
    load_dotenv(_root_env, override=True)
else:
    load_dotenv(override=True)


def _bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


def _csv(name: str, default: str) -> list[str]:
    """Parse a comma-separated env var into a list (whitespace-trimmed, empties dropped)."""
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


class Config:
    # --- Flask ---
    _secret = os.environ.get("SECRET_KEY")
    if not _secret:
        raise ValueError("SECRET_KEY environment variable must be set")
    SECRET_KEY = _secret
    DEBUG = _bool("FLASK_DEBUG", False)
    JSON_AS_ASCII = False

    # --- LLM (default / primary tier) ---
    LLM_API_KEY = os.environ.get("LLM_API_KEY")
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")

    # --- LLM tiers (resolved at call time inside utils.llm) ---
    # cheap = high-volume agent reactions (Haiku / Qwen-turbo / Llama-3.1-8B)
    # deep  = "influencer" agents that shape the conversation (Sonnet)
    # synth = final report synthesis (Sonnet / Opus)
    # Any tier env var that's unset falls back to the LLM_* primary above.
    LLM_CHEAP_MODEL_NAME = os.environ.get("LLM_CHEAP_MODEL_NAME")
    LLM_DEEP_MODEL_NAME = os.environ.get("LLM_DEEP_MODEL_NAME")
    LLM_SYNTH_MODEL_NAME = os.environ.get("LLM_SYNTH_MODEL_NAME")

    # --- Zep ---
    # Zep is optional. The fast "roast" pipeline runs without it.
    # Deep simulation (legacy MiroFish path) still requires Zep.
    ZEP_API_KEY = os.environ.get("ZEP_API_KEY")
    USE_ZEP = _bool("USE_ZEP", False)  # default OFF for fast pipeline

    # --- Uploads ---
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "../uploads")
    ALLOWED_EXTENSIONS = {"pdf", "md", "txt", "markdown"}

    # --- Text processing ---
    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 50

    # --- OASIS (deep simulation only) ---
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get("OASIS_DEFAULT_MAX_ROUNDS", "10"))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), "../uploads/simulations")
    OASIS_TWITTER_ACTIONS = [
        "CREATE_POST", "LIKE_POST", "REPOST", "FOLLOW", "DO_NOTHING", "QUOTE_POST",
    ]
    OASIS_REDDIT_ACTIONS = [
        "LIKE_POST", "DISLIKE_POST", "CREATE_POST", "CREATE_COMMENT",
        "LIKE_COMMENT", "DISLIKE_COMMENT", "SEARCH_POSTS", "SEARCH_USER",
        "TREND", "REFRESH", "DO_NOTHING", "FOLLOW", "MUTE",
    ]

    # --- Report agent (deep / legacy path) ---
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get("REPORT_AGENT_MAX_TOOL_CALLS", "5"))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get("REPORT_AGENT_MAX_REFLECTION_ROUNDS", "2"))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get("REPORT_AGENT_TEMPERATURE", "0.5"))

    # --- Roast pipeline (fast path) ---
    # Number of agents to spawn in the cheap / fast pipeline.
    ROAST_AGENT_COUNT = int(os.environ.get("ROAST_AGENT_COUNT", "100"))
    # Concurrency cap for parallel agent reactions (prevents rate-limit hammering).
    ROAST_CONCURRENCY = int(os.environ.get("ROAST_CONCURRENCY", "20"))
    # Hard cost ceiling per sim in USD. Aborts mid-run if exceeded.
    ROAST_MAX_COST_USD = float(os.environ.get("ROAST_MAX_COST_USD", "1.00"))

    # --- Roast job store ---
    # When set, roast jobs + the SSE event log live in Redis so they survive a
    # worker restart / redeploy / idle spin-down (the cause of "job not found"
    # 404s on the stream/poll endpoints). Unset → in-process store (dev/test).
    REDIS_URL = os.environ.get("REDIS_URL")
    # How long a job's state lives in Redis after its last write.
    ROAST_JOB_TTL = int(os.environ.get("ROAST_JOB_TTL", "3600"))
    # A non-terminal job with no progress for this long is treated as failed
    # (its pipeline thread died with the worker). Guards against "stuck running".
    ROAST_STALE_SECONDS = int(os.environ.get("ROAST_STALE_SECONDS", "180"))

    # --- API hardening (public launch) ---
    # Browser origins allowed to call /api/* (comma-separated env CORS_ORIGINS).
    CORS_ORIGINS = _csv("CORS_ORIGINS", "https://swarmie.vercel.app,http://localhost:3000")
    # Per-IP rate limits (flask-limiter notation). Roast creation + agent chat
    # both burn LLM tokens; reads and the SSE stream are deliberately unlimited.
    RATE_LIMIT_ROAST = os.environ.get("RATE_LIMIT_ROAST", "5 per hour")
    RATE_LIMIT_CHAT = os.environ.get("RATE_LIMIT_CHAT", "30 per hour")
    # Master switch (flask-limiter reads RATELIMIT_ENABLED from app config).
    # Tests set RATE_LIMIT_ENABLED=false so the suite never trips limits.
    RATELIMIT_ENABLED = _bool("RATE_LIMIT_ENABLED", True)

    @classmethod
    def validate(cls):
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY is not configured")
        if cls.USE_ZEP and not cls.ZEP_API_KEY:
            errors.append("USE_ZEP=true but ZEP_API_KEY is not configured")
        return errors
