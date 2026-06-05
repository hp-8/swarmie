"""
Tier-2 contemporaneous launch text finder for the PMF Readiness Index backtest.

Resolves a YC company to its launch-era pitch text so the backtest uses
pre-success, minimal-hindsight input rather than YC directory copy.

Two sources, tried in order:
  1. HN Algolia — Show HN / Launch HN post near ``launched_at``.
  2. Wayback Machine — archived homepage snapshot from the launch year.

Every network call is routed through an injectable ``http_get`` callable so
unit tests can pass canned responses without any real I/O.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Callable

# ---------------------------------------------------------------------------
# Default HTTP helper (stdlib only; requests is not a project dependency)
# ---------------------------------------------------------------------------

def _default_http_get(url: str) -> dict:
    """Fetch *url* and return the parsed JSON body as a dict."""
    with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
        return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def find_show_hn(
    name: str,
    launched_at: int | None,
    *,
    http_get: Callable[[str], dict] = _default_http_get,
) -> dict | None:
    """Query HN Algolia for a Show HN post near *launched_at*.

    Strategy
    --------
    - Search ``https://hn.algolia.com/api/v1/search`` with ``tags=show_hn``.
    - Keep only hits whose title contains *name* (case-insensitive, partial).
    - Among those, pick the hit whose ``created_at_i`` (unix ts) is closest
      to *launched_at*.  If *launched_at* is None, pick the first title-match.

    Returns
    -------
    ``{"source": "show_hn", "text": <title + story_text>, "url": <HN link>}``
    or ``None`` if no suitable hit is found.
    """
    query = urllib.parse.quote(name)
    url = (
        f"https://hn.algolia.com/api/v1/search"
        f"?query={query}&tags=show_hn&hitsPerPage=20"
    )
    data = http_get(url)
    hits = data.get("hits", [])

    name_lower = name.lower()
    candidates = [h for h in hits if name_lower in (h.get("title") or "").lower()]

    if not candidates:
        return None

    if launched_at is None:
        best = candidates[0]
    else:
        best = min(
            candidates,
            key=lambda h: abs((h.get("created_at_i") or 0) - launched_at),
        )

    title = best.get("title") or ""
    story = best.get("story_text") or best.get("url") or ""
    text = f"{title}\n{story}".strip()
    obj_id = best.get("objectID", "")
    hn_url = f"https://news.ycombinator.com/item?id={obj_id}" if obj_id else ""

    return {"source": "show_hn", "text": text, "url": hn_url}


def find_wayback(
    website: str,
    year: int,
    *,
    http_get: Callable[[str], dict] = _default_http_get,
) -> dict | None:
    """Query the Wayback Machine availability API for a snapshot of *website*.

    Requests a snapshot closest to ``<year>0101``.

    Returns
    -------
    ``{"source": "wayback", "text": <snapshot url>, "url": <snapshot url>}``
    or ``None`` if no snapshot is available.
    """
    encoded = urllib.parse.quote(website, safe="")
    timestamp = f"{year}0101"
    url = f"http://archive.org/wayback/available?url={encoded}&timestamp={timestamp}"
    data = http_get(url)

    snapshots = data.get("archived_snapshots", {})
    closest = snapshots.get("closest", {})
    if not closest.get("available"):
        return None

    snapshot_url = closest.get("url", "")
    if not snapshot_url:
        return None

    return {"source": "wayback", "text": snapshot_url, "url": snapshot_url}


def match_contemporaneous(
    company: dict,
    *,
    http_get: Callable[[str], dict] = _default_http_get,
) -> dict | None:
    """Find the best contemporaneous launch text for *company*.

    ``company`` is a YC API record with at least:
      - ``name`` (str)
      - ``launched_at`` (int unix ts, optional)
      - ``batch`` (str like "S12", "W18") — used to derive the year fallback
      - ``website`` (str, optional)

    Strategy: try Show HN first; if no match, fall back to Wayback Machine.
    Returns the first successful hit, or ``None``.
    """
    name: str = company.get("name", "")
    launched_at: int | None = company.get("launched_at")
    batch: str = company.get("batch", "")
    website: str = company.get("website", "")

    # --- Show HN ----------------------------------------------------------
    if name:
        hit = find_show_hn(name, launched_at, http_get=http_get)
        if hit:
            return hit

    # --- Wayback Machine fallback -----------------------------------------
    if website:
        year = _batch_year(batch, launched_at)
        if year:
            hit = find_wayback(website, year, http_get=http_get)
            if hit:
                return hit

    return None


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------

def _batch_year(batch: str, launched_at: int | None) -> int | None:
    """Derive a calendar year from the YC batch string or ``launched_at``."""
    # batch looks like "S12", "W18", "S2023", "W2024"
    if batch and len(batch) >= 2:
        suffix = batch[1:]  # drop S/W prefix
        if suffix.isdigit():
            raw = int(suffix)
            # Two-digit year: 05 → 2005, 24 → 2024
            year = (2000 + raw) if raw < 100 else raw  # noqa: PLR2004
            return year

    if launched_at:
        import datetime
        return datetime.datetime.utcfromtimestamp(launched_at).year

    return None
