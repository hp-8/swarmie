"""
Deck loader.

Turn an uploaded PDF pitch deck into ordered per-page text. Text-layer only
(PyMuPDF `get_text`) — no vision/OCR in v1. Image-only / scanned decks (no
extractable text) are rejected so the caller can ask the founder to paste text.

Page numbers are 1-based and preserved through the whole pipeline so every
downstream finding can cite its original slide.
"""

from __future__ import annotations

import logging
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger("swarmie.swarm.deck_loader")

MAX_PAGES_DEFAULT = 25


class DeckLoadError(Exception):
    """Raised when a PDF cannot be read into usable per-page text."""


def load_pdf(data: bytes, max_pages: int = MAX_PAGES_DEFAULT) -> list[dict[str, Any]]:
    """Render a PDF's text layer to ordered per-page text.

    Returns: ``[{"page": <1-based int>, "text": <str>}, ...]`` (only pages with
    non-whitespace text). Raises ``DeckLoadError`` on a corrupt/encrypted PDF or
    when no page has an extractable text layer.
    """
    if not data:
        raise DeckLoadError("empty file")

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # fitz raises a variety of low-level errors
        raise DeckLoadError(f"could not open PDF: {exc}") from exc

    try:
        if getattr(doc, "needs_pass", False):
            raise DeckLoadError("PDF is password-protected")

        pages: list[dict[str, Any]] = []
        n = min(doc.page_count, max(1, int(max_pages)))
        for i in range(n):
            try:
                text = doc.load_page(i).get_text("text") or ""
            except Exception as exc:
                logger.warning("page %d text extract failed: %s", i + 1, exc)
                text = ""
            text = text.strip()
            if text:
                pages.append({"page": i + 1, "text": text})

        if not pages:
            # Every page was image-only / scanned — no text layer to read.
            raise DeckLoadError("no text layer")

        truncated = doc.page_count > n
        if truncated:
            logger.info("deck truncated: %d of %d pages used", n, doc.page_count)
        return pages
    finally:
        doc.close()
