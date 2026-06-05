"""
LLM Client v2 — Swarmie.

Provider-agnostic, tiered, async-capable, token-tracked.

Design goals:
- Single source of truth for all LLM calls
- Tier routing: cheap (high-volume agent reactions) / deep (influencer agents) / synth (final report)
- Provider-agnostic via OpenAI-compatible interface (works with OpenAI, Anthropic-via-OpenRouter,
  Groq, Together, Fireworks, Ollama, DeepSeek, Qwen, etc.)
- Async-first for parallel agent generation; sync wrapper provided
- Built-in retry with exponential backoff
- Token + cost tracking per call
- Optional prompt-cache hints for Anthropic-family models

Backwards compatibility:
- LLMClient (old name) re-exported as alias so existing services keep working.
- chat() / chat_json() preserved.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any

from openai import APIError, APITimeoutError, AsyncOpenAI, OpenAI, RateLimitError

from ..config import Config

logger = logging.getLogger("swarmie.llm")


# --- model pricing table (USD per 1M tokens, input/output) ---
# Source: provider pricing pages as of 2026-Q1. Update as needed.
# Used only for cost estimation; missing entries fall back to zero.
_PRICING: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    # Anthropic
    "claude-opus-4-7": (15.00, 75.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (0.80, 4.00),
    # Groq / open weights
    "llama-3.3-70b-versatile": (0.59, 0.79),
    "llama-3.1-8b-instant": (0.05, 0.08),
    "mixtral-8x7b-32768": (0.24, 0.24),
    # Qwen / Alibaba
    "qwen-plus": (0.40, 1.20),
    "qwen-turbo": (0.05, 0.20),
    # DeepSeek
    "deepseek-chat": (0.27, 1.10),
    # Local — free
    "ollama": (0.0, 0.0),
}


def _lookup_price(model: str) -> tuple[float, float]:
    """Best-effort price lookup. Matches by prefix if exact not found."""
    if model in _PRICING:
        return _PRICING[model]
    for key, price in _PRICING.items():
        if model.startswith(key) or key in model:
            return price
    return (0.0, 0.0)


@dataclass
class Usage:
    """Token + cost stats for a single call."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    model: str = ""
    tier: str = ""
    cached: bool = False

    @classmethod
    def from_response(cls, resp: Any, model: str, tier: str) -> "Usage":
        u = getattr(resp, "usage", None)
        if u is None:
            return cls(model=model, tier=tier)
        pt = getattr(u, "prompt_tokens", 0) or 0
        ct = getattr(u, "completion_tokens", 0) or 0
        in_price, out_price = _lookup_price(model)
        cost = (pt * in_price + ct * out_price) / 1_000_000
        return cls(
            prompt_tokens=pt,
            completion_tokens=ct,
            total_tokens=getattr(u, "total_tokens", pt + ct) or (pt + ct),
            cost_usd=round(cost, 6),
            model=model,
            tier=tier,
        )


@dataclass
class UsageTracker:
    """Aggregate usage across many calls (e.g. one sim run)."""
    calls: list[Usage] = field(default_factory=list)

    def add(self, u: Usage) -> None:
        self.calls.append(u)

    @property
    def total_cost_usd(self) -> float:
        return round(sum(c.cost_usd for c in self.calls), 6)

    @property
    def total_tokens(self) -> int:
        return sum(c.total_tokens for c in self.calls)

    def summary(self) -> dict[str, Any]:
        by_tier: dict[str, dict[str, float]] = {}
        for c in self.calls:
            t = by_tier.setdefault(c.tier or "default", {"calls": 0, "tokens": 0, "cost": 0.0})
            t["calls"] += 1
            t["tokens"] += c.total_tokens
            t["cost"] += c.cost_usd
        return {
            "total_cost_usd": self.total_cost_usd,
            "total_tokens": self.total_tokens,
            "total_calls": len(self.calls),
            "by_tier": by_tier,
        }


# --- tier resolution ---

def _resolve_fallback() -> tuple[str, str, str] | None:
    """Resolve fallback provider creds, if configured.

    Env: LLM_FALLBACK_API_KEY, LLM_FALLBACK_BASE_URL, LLM_FALLBACK_MODEL_NAME.
    Returns None if no fallback configured. Designed for Gemini's
    OpenAI-compatible endpoint but works for any OpenAI-compatible API.
    """
    api_key = os.environ.get("LLM_FALLBACK_API_KEY")
    if not api_key:
        return None
    base_url = os.environ.get(
        "LLM_FALLBACK_BASE_URL",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    model = os.environ.get("LLM_FALLBACK_MODEL_NAME", "gemini-2.0-flash")
    return api_key, base_url, model


def _resolve_model(tier: str) -> tuple[str, str, str]:
    """Resolve tier -> (api_key, base_url, model).

    Tiers and their env mapping:
      cheap  -> LLM_CHEAP_*  (defaults to LLM_* base, model fallback)
      deep   -> LLM_DEEP_*   (defaults to LLM_*)
      synth  -> LLM_SYNTH_*  (defaults to LLM_*)
      default-> LLM_*        (the legacy / primary model)
    """
    tier = (tier or "default").lower()
    prefix_map = {
        "cheap": "LLM_CHEAP_",
        "deep": "LLM_DEEP_",
        "synth": "LLM_SYNTH_",
        "default": "LLM_",
    }
    prefix = prefix_map.get(tier, "LLM_")

    api_key = os.environ.get(prefix + "API_KEY") or Config.LLM_API_KEY
    base_url = os.environ.get(prefix + "BASE_URL") or Config.LLM_BASE_URL
    model = os.environ.get(prefix + "MODEL_NAME") or Config.LLM_MODEL_NAME

    if not api_key:
        raise ValueError(f"No API key configured for tier '{tier}' (set {prefix}API_KEY or LLM_API_KEY)")

    return api_key, base_url, model


def _strip_think_tags(text: str) -> str:
    """Reasoning models (MiniMax, GLM, DeepSeek-R1) leak <think> blocks. Strip them."""
    if not text:
        return text
    return re.sub(r"<think>[\s\S]*?</think>", "", text).strip()


def _strip_json_fences(text: str) -> str:
    """Strip markdown ```json fences that some models wrap JSON in."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


# --- client ---

class LLM:
    """Unified LLM client. One instance per tier; reuse across calls.

    Usage:
        llm = LLM(tier="cheap")
        text = llm.chat([{"role": "user", "content": "hi"}])

        # async, parallel
        results = await asyncio.gather(*[llm.achat(msgs) for msgs in batch])
    """

    def __init__(
        self,
        tier: str = "default",
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        tracker: UsageTracker | None = None,
        max_retries: int = 3,
        timeout: float | None = None,
    ):
        self.tier = tier
        if api_key and base_url and model:
            self.api_key, self.base_url, self.model = api_key, base_url, model
        else:
            self.api_key, self.base_url, self.model = _resolve_model(tier)
        self.tracker = tracker
        self.max_retries = max_retries
        # Env-overridable so slow local backends (Ollama 7B) don't abort the
        # longer deep-tier generations. Default 30s for hosted providers.
        self.timeout = timeout if timeout is not None else float(os.environ.get("LLM_TIMEOUT", "30"))

        self._sync = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
        self._async: AsyncOpenAI | None = None  # lazy

        # Fallback provider (e.g. Gemini). Used after primary exhausts retries.
        self._fallback = _resolve_fallback()
        self._fallback_sync: OpenAI | None = None
        self._fallback_async: AsyncOpenAI | None = None

    @property
    def aclient(self) -> AsyncOpenAI:
        if self._async is None:
            self._async = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
        return self._async

    def _fb_sync_client(self) -> OpenAI | None:
        if not self._fallback:
            return None
        if self._fallback_sync is None:
            k, b, _ = self._fallback
            self._fallback_sync = OpenAI(api_key=k, base_url=b, timeout=self.timeout)
        return self._fallback_sync

    def _fb_async_client(self) -> AsyncOpenAI | None:
        if not self._fallback:
            return None
        if self._fallback_async is None:
            k, b, _ = self._fallback
            self._fallback_async = AsyncOpenAI(api_key=k, base_url=b, timeout=self.timeout)
        return self._fallback_async

    # --- core sync API ---

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict | None = None,
        model: str | None = None,
    ) -> str:
        """Single chat completion. Returns plain text."""
        resp = self._call_with_retry(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            model=model or self.model,
        )
        text = resp.choices[0].message.content or ""
        return _strip_think_tags(text)

    def chat_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Chat → parse JSON. Tolerant of markdown fences and stray think-tags."""
        text = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            model=model,
        )
        cleaned = _strip_json_fences(text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM did not return valid JSON: {cleaned[:200]}...") from exc

    # --- core async API ---

    async def achat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict | None = None,
        model: str | None = None,
    ) -> str:
        """Async chat completion."""
        resp = await self._acall_with_retry(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            model=model or self.model,
        )
        text = resp.choices[0].message.content or ""
        return _strip_think_tags(text)

    async def achat_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> dict[str, Any]:
        text = await self.achat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            model=model,
        )
        cleaned = _strip_json_fences(text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM did not return valid JSON: {cleaned[:200]}...") from exc

    # --- retry wrappers ---

    def _call_with_retry(self, **kwargs):
        last_exc: Exception | None = None
        payload = {k: v for k, v in kwargs.items() if v is not None}
        model = payload.get("model", self.model)
        max_tok = payload.get("max_tokens", "?")
        # Coarse prompt size for logging — sum of message content lengths.
        prompt_chars = sum(len((m.get("content") or "")) for m in payload.get("messages", []))
        for attempt in range(self.max_retries):
            print(
                f"[llm.{self.tier}] -> {model} max_tokens={max_tok} prompt_chars={prompt_chars} attempt={attempt + 1}",
                flush=True,
            )
            try:
                started = time.time()
                resp = self._sync.chat.completions.create(**payload)
                dur = time.time() - started
                if self.tracker:
                    self.tracker.add(Usage.from_response(resp, model=model, tier=self.tier))
                pt = getattr(getattr(resp, "usage", None), "prompt_tokens", 0)
                ct = getattr(getattr(resp, "usage", None), "completion_tokens", 0)
                print(
                    f"[llm.{self.tier}] <- {model} in={pt} out={ct} took={dur:.1f}s",
                    flush=True,
                )
                return resp
            except APITimeoutError as exc:
                last_exc = exc
                print(f"[llm.{self.tier}] TIMEOUT after {self.timeout}s (attempt {attempt + 1})", flush=True)
            except (RateLimitError, APIError) as exc:
                last_exc = exc
                wait = min(2 ** attempt, 30)
                print(f"[llm.{self.tier}] attempt {attempt + 1} failed: {exc}; retrying in {wait}s", flush=True)
                time.sleep(wait)
        # Primary exhausted — try fallback provider once
        fb = self._fb_sync_client()
        if fb is not None:
            fb_model = self._fallback[2]  # type: ignore[index]
            fb_payload = {**payload, "model": fb_model}
            print(f"[llm.{self.tier}] FALLBACK -> {fb_model}", flush=True)
            try:
                resp = fb.chat.completions.create(**fb_payload)
                if self.tracker:
                    self.tracker.add(Usage.from_response(resp, model=fb_model, tier=f"{self.tier}/fallback"))
                return resp
            except Exception as exc:
                last_exc = exc
                print(f"[llm.{self.tier}] fallback failed: {exc}", flush=True)
        raise RuntimeError(f"LLM call failed after {self.max_retries} retries: {last_exc}")

    async def _acall_with_retry(self, **kwargs):
        last_exc: Exception | None = None
        payload = {k: v for k, v in kwargs.items() if v is not None}
        model = payload.get("model", self.model)
        for attempt in range(self.max_retries):
            try:
                started = time.time()
                resp = await self.aclient.chat.completions.create(**payload)
                dur = time.time() - started
                if self.tracker:
                    self.tracker.add(Usage.from_response(resp, model=model, tier=self.tier))
                if dur > 5.0:
                    print(f"[llm.{self.tier}/async] slow call took={dur:.1f}s", flush=True)
                return resp
            except APITimeoutError as exc:
                last_exc = exc
                print(f"[llm.{self.tier}/async] TIMEOUT after {self.timeout}s", flush=True)
            except (RateLimitError, APIError) as exc:
                last_exc = exc
                wait = min(2 ** attempt, 30)
                print(f"[llm.{self.tier}/async] attempt {attempt + 1} failed: {exc}; retrying in {wait}s", flush=True)
                await asyncio.sleep(wait)
        # Primary exhausted — try fallback provider once (async)
        fb = self._fb_async_client()
        if fb is not None:
            fb_model = self._fallback[2]  # type: ignore[index]
            fb_payload = {**payload, "model": fb_model}
            print(f"[llm.{self.tier}/async] FALLBACK -> {fb_model}", flush=True)
            try:
                resp = await fb.chat.completions.create(**fb_payload)
                if self.tracker:
                    self.tracker.add(Usage.from_response(resp, model=fb_model, tier=f"{self.tier}/fallback"))
                return resp
            except Exception as exc:
                last_exc = exc
                print(f"[llm.{self.tier}/async] fallback failed: {exc}", flush=True)
        raise RuntimeError(f"Async LLM call failed after {self.max_retries} retries: {last_exc}")

    # --- batch helper ---

    async def abatch_chat(
        self,
        message_batches: list[list[dict[str, str]]],
        concurrency: int = 20,
        **kwargs,
    ) -> list[str]:
        """Run many chat() calls in parallel with bounded concurrency.

        Use this for the cheap-tier agent-reaction fan-out. Concurrency cap
        prevents hammering rate limits.
        """
        sem = asyncio.Semaphore(concurrency)

        async def _one(msgs):
            async with sem:
                return await self.achat(msgs, **kwargs)

        return await asyncio.gather(*[_one(m) for m in message_batches])


# --- legacy compatibility shim ---
# Existing services import `LLMClient` from utils.llm_client. Keep that import
# path working so the old pipeline doesn't break during the refactor.

class LLMClient(LLM):
    """Backwards-compatible alias. Defaults to the 'default' tier."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        super().__init__(tier="default", api_key=api_key, base_url=base_url, model=model)
