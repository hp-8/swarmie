"""
Unit tests for the deck-intelligence module (loader, extractor, evaluator).

LLM calls are stubbed via patching the module-level LLM symbol so tests are
deterministic and offline. PDFs are built in-memory with PyMuPDF — no fixtures.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import fitz  # PyMuPDF
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.swarm.deck_loader import DeckLoadError, load_pdf
from app.services.swarm.deck_extractor import DeckExtractor, SlideRead
from app.services.swarm.deck_evaluator import DeckEvaluator, DeckDiagnosis


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _make_text_pdf(pages_text: list[str]) -> bytes:
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=12)
    data = doc.tobytes()
    doc.close()
    return data


def _make_blank_pdf(n: int = 2) -> bytes:
    doc = fitz.open()
    for _ in range(n):
        doc.new_page()  # no text inserted -> no text layer
    data = doc.tobytes()
    doc.close()
    return data


def _llm_stub(return_value: dict) -> MagicMock:
    instance = MagicMock()
    instance.chat_json.return_value = return_value
    cls = MagicMock(return_value=instance)
    return cls


# --------------------------------------------------------------------------
# deck_loader
# --------------------------------------------------------------------------

def test_load_pdf_extracts_per_page_text():
    data = _make_text_pdf(["Problem: reps waste time", "Traction: $48K MRR"])
    pages = load_pdf(data)
    assert [p["page"] for p in pages] == [1, 2]
    assert "reps waste time" in pages[0]["text"]
    assert "48K MRR" in pages[1]["text"]


def test_load_pdf_truncates_to_max_pages():
    data = _make_text_pdf([f"slide {i}" for i in range(10)])
    pages = load_pdf(data, max_pages=3)
    assert len(pages) == 3
    assert pages[-1]["page"] == 3


def test_load_pdf_empty_bytes_raises():
    with pytest.raises(DeckLoadError):
        load_pdf(b"")


def test_load_pdf_no_text_layer_raises():
    with pytest.raises(DeckLoadError, match="no text layer"):
        load_pdf(_make_blank_pdf(2))


def test_load_pdf_corrupt_raises():
    with pytest.raises(DeckLoadError):
        load_pdf(b"%PDF-1.4 not really a pdf")


# --------------------------------------------------------------------------
# DeckExtractor
# --------------------------------------------------------------------------

def test_extractor_carries_page_numbers_and_builds_pitch():
    canned = {
        "slides": [
            {"page": 1, "slide_type": "problem", "headline": "Big pain",
             "body": "reps waste time", "signals": ["40% admin"]},
            {"page": 2, "slide_type": "traction", "headline": "Growing",
             "body": "MRR up", "signals": ["$48K MRR", "22% MoM"]},
        ],
        "pitch": {
            "one_liner": "AI CRM autopilot", "problem": "admin overload",
            "solution": "auto-fill", "target_icp": "B2B AEs",
            "icp_segments": ["operator angel", "seed VC"],
            "traction": "$48K MRR", "stage": "seed",
        },
    }
    pages = [{"page": 1, "text": "x"}, {"page": 2, "text": "y"}]
    with patch("app.services.swarm.deck_extractor.LLM", _llm_stub(canned)):
        deck = DeckExtractor().extract(pages)
    assert [s.page for s in deck.slides] == [1, 2]
    assert deck.slides[0].slide_type == "problem"
    assert deck.slides[1].signals == ["$48K MRR", "22% MoM"]
    assert deck.pitch.one_liner == "AI CRM autopilot"
    assert deck.pitch.stage == "seed"
    assert deck.pitch.icp_segments == ["operator angel", "seed VC"]


def test_extractor_drops_unknown_slide_type_and_bad_pages():
    canned = {
        "slides": [
            {"page": 1, "slide_type": "wormhole", "headline": "?", "body": "", "signals": []},
            {"page": 99, "slide_type": "ask", "headline": "raise", "body": "", "signals": []},
        ],
        "pitch": {},
    }
    pages = [{"page": 1, "text": "x"}]
    with patch("app.services.swarm.deck_extractor.LLM", _llm_stub(canned)):
        deck = DeckExtractor().extract(pages)
    # unknown type coerced to 'other'; page 99 (not in input) dropped
    assert len(deck.slides) == 1
    assert deck.slides[0].slide_type == "other"


# --------------------------------------------------------------------------
# DeckEvaluator
# --------------------------------------------------------------------------

_SLIDES = [
    SlideRead(page=1, slide_type="problem", headline="Pain", body="b", signals=[]),
    SlideRead(page=2, slide_type="ask", headline="Raise", body="b", signals=[]),
]


def test_evaluator_parses_and_clamps():
    canned = {
        "stage": "seed",
        "readiness_pct": 142,      # over 100 -> clamp
        "overall_score": 999,      # over 130 -> clamp
        "slides": [
            {"slide_type": "problem", "page": 1, "score": 13, "verdict": "ok", "top_issue": "weak"},
            {"slide_type": "ask", "page": 2, "score": 7, "verdict": "fine", "top_issue": ""},
        ],
        "red_flags": [
            {"severity": "nuclear", "slide_type": "ask", "page": 2, "text": "vague ask"},
        ],
        "strong_zones": ["team"],
        "weak_zones": ["market"],
        "investor_simulation": "I'd pass.",
        "next_move": "Tighten the ask.",
    }
    with patch("app.services.swarm.deck_evaluator.LLM", _llm_stub(canned)):
        diag = DeckEvaluator().evaluate(_SLIDES, stage="seed")
    assert isinstance(diag, DeckDiagnosis)
    assert diag.readiness_pct == 100.0
    assert diag.overall_score == 130
    assert diag.slides[0]["score"] == 10        # 13 clamped to 10
    assert diag.red_flags[0]["severity"] == "MEDIUM"  # invalid -> default
    assert diag.red_flags[0]["page"] == 2
    assert diag.next_move == "Tighten the ask."


def test_evaluator_bad_json_falls_back_without_raising():
    instance = MagicMock()
    instance.chat_json.side_effect = ValueError("not json")
    cls = MagicMock(return_value=instance)
    with patch("app.services.swarm.deck_evaluator.LLM", cls):
        diag = DeckEvaluator().evaluate(_SLIDES, stage="seed")
    assert isinstance(diag, DeckDiagnosis)
    assert diag.stage == "seed"
    # fallback still lists the slides it was given (page-cited)
    assert {s["page"] for s in diag.slides} == {1, 2}
    assert diag.next_move  # non-empty guidance
