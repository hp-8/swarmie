"""
corpus.py — YC ground-truth corpus loader for the PMF Readiness Index backtest.

Emits raw (un-decontaminated) text. Decontamination is handled in a separate module.
Stdlib only: json, re, pathlib.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "yc_all.json"

_YEAR_RE = re.compile(r"\b(\d{4})\b")

_HIT_STATUSES = {"Acquired", "Public"}
_FLOP_STATUS = "Inactive"


def load_raw() -> list[dict]:
    """Load and JSON-parse the cached YC dataset."""
    with DATA_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def batch_year(batch: str | None) -> int | None:
    """Parse the 4-digit year from a batch string like 'Winter 2012'.

    Returns None if batch is None or no year found.
    """
    if not batch:
        return None
    m = _YEAR_RE.search(batch)
    return int(m.group(1)) if m else None


def label_of(status: str | None) -> int | None:
    """Map company status to a binary label.

    Acquired / Public -> 1 (hit)
    Inactive          -> 0 (flop)
    Active            -> None (excluded / censored)
    """
    if status in _HIT_STATUSES:
        return 1
    if status == _FLOP_STATUS:
        return 0
    return None


def load_tier1(max_batch_year: int = 2018) -> list[dict]:
    """Return labeled cases from matured batches (batch_year <= max_batch_year).

    Excludes Active companies (label is None).

    Each returned dict contains:
        id, name, former_names, raw_text, label, status, batch
    """
    cases: list[dict] = []
    for company in load_raw():
        batch = company.get("batch")
        year = batch_year(batch)
        if year is None or year > max_batch_year:
            continue

        status = company.get("status")
        label = label_of(status)
        if label is None:
            continue

        long_desc = company.get("long_description") or ""
        one_liner = company.get("one_liner") or ""
        raw_text = long_desc if long_desc.strip() else one_liner

        cases.append(
            {
                "id": company.get("id"),
                "name": company.get("name"),
                "former_names": company.get("former_names", []),
                "raw_text": raw_text,
                "label": label,
                "status": status,
                "batch": batch,
            }
        )
    return cases
