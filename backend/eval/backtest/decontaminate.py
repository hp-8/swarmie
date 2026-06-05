"""Decontaminate YC company text for backtest use.

Removes:
- Company name + every former_names entry (whole-word, case-insensitive).
- Outcome-leak phrases and the sentence/clause containing them.
- Trailing exit-date clauses (e.g. "Exited October 2014").
- Hiring/boilerplate phrases and careers URLs.
- Collapses whitespace. Returns "" if scrubbed result is < 15 chars.
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Outcome-leak patterns
# Each pattern matches a sentence or clause that contains a leak phrase.
# Strategy: first nuke whole sentences containing any outcome marker, then
# clean up residual fragments.
# ---------------------------------------------------------------------------

# Sentence-level splitter: split on period / exclamation / question mark
# followed by whitespace or end-of-string, preserving the delimiter.
_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')

# Patterns that mark a sentence/clause as outcome-contaminated.
# If any matches, the whole sentence is dropped.
_OUTCOME_SENTENCE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r'\bacquired\b', re.IGNORECASE),
    re.compile(r'\bexit(?:ed)?\b', re.IGNORECASE),
    re.compile(r'\bshut\s+down\b', re.IGNORECASE),
    re.compile(r'\bshutdown\b', re.IGNORECASE),
    re.compile(r'\bnow\s+part\s+of\b', re.IGNORECASE),
    re.compile(r'\bwound\s+down\b', re.IGNORECASE),
    re.compile(r'\bclosed(?:\s+down)?\b', re.IGNORECASE),
    # Markdown/asterisk form: *Acquired by ...
    re.compile(r'\*\s*acquired\b', re.IGNORECASE),
]

# Trailing exit-date clause: "Exited Month Year" or "Exited YYYY" at end of text/sentence
_TRAILING_EXIT_DATE = re.compile(
    r'\bExited\s+\w+(?:\s+\d{4})?\b[.\s]*',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Hiring / boilerplate patterns (phrase-level, not whole-sentence)
# ---------------------------------------------------------------------------

_HIRING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"we'?re\s+hiring\b[^.!?]*[.!?]?", re.IGNORECASE),
    re.compile(r"\bjoin\s+us\b[^.!?]*[.!?]?", re.IGNORECASE),
    re.compile(r"\bapply\s+today\b[^.!?]*[.!?]?", re.IGNORECASE),
    re.compile(r"\bopen\s+positions\b[^.!?]*[.!?]?", re.IGNORECASE),
    re.compile(r"\bcheck\s+out\s+our\b[^.!?]*careers[^.!?]*[.!?]?", re.IGNORECASE),
    # Careers/jobs URLs: any URL containing /careers or /jobs
    re.compile(r'https?://\S+/(?:careers|jobs)\S*', re.IGNORECASE),
    # Bare domain-style careers mention
    re.compile(r'\S+\.com/(?:careers|jobs)\S*', re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def decontaminate(record: dict) -> str:  # noqa: C901 — acceptable complexity here
    """Strip name, outcome phrases, and hiring boilerplate from a YC record.

    Args:
        record: dict with keys:
            name (str): company name.
            former_names (list[str]): previous names.
            long_description (str | None): full description text.
            one_liner (str | None): short pitch.

    Returns:
        Scrubbed pitch text, or "" if result is unusably short (< 15 chars).
    """
    name: str = record.get("name") or ""
    former_names: list[str] = record.get("former_names") or []
    long_desc: str | None = record.get("long_description")
    one_liner: str | None = record.get("one_liner")

    # 1. Pick base text
    text = ""
    if long_desc and long_desc.strip():
        text = long_desc
    elif one_liner and one_liner.strip():
        text = one_liner

    if not text.strip():
        return ""

    # 2. Normalise line endings → spaces (preserves sentence structure)
    text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")

    # 3. Strip outcome-contaminated sentences
    text = _strip_outcome_sentences(text)

    # 4. Strip trailing exit-date clauses that survived sentence-level removal
    text = _TRAILING_EXIT_DATE.sub(" ", text)

    # 5. Strip hiring/boilerplate phrases
    for pat in _HIRING_PATTERNS:
        text = pat.sub(" ", text)

    # 6. Strip company name and former names (whole-word, case-insensitive)
    for entity in [name] + list(former_names):
        if entity and entity.strip():
            text = _strip_entity_name(text, entity.strip())

    # 7. Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Strip leading/trailing punctuation artifacts
    text = re.sub(r'^[,\s;:\-]+', '', text)
    text = re.sub(r'[,\s;:\-]+$', '', text)
    text = text.strip()

    # 8. Minimum usable length
    if len(text) < 15:
        return ""

    return text


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_outcome_sentences(text: str) -> str:
    """Split text into sentences; drop any that contain an outcome phrase."""
    # Split on sentence boundaries but keep delimiters attached to the preceding sentence.
    # We use a simple regex-based split that keeps the terminator with the sentence.
    sentences = re.split(r'(?<=[.!?])\s+', text)
    clean: list[str] = []
    for sentence in sentences:
        if not _is_outcome_sentence(sentence):
            clean.append(sentence)
    return " ".join(clean)


def _is_outcome_sentence(sentence: str) -> bool:
    """Return True if the sentence contains any outcome-leak phrase."""
    return any(pat.search(sentence) for pat in _OUTCOME_SENTENCE_PATTERNS)


def _strip_entity_name(text: str, name: str) -> str:
    """Remove a company name as a whole word, case-insensitively.

    Handles names that may contain regex special characters (e.g. "42Floors").
    """
    escaped = re.escape(name)
    # Try whole-word match first; if name contains digits/special chars at boundaries
    # \b may not anchor cleanly — use lookahead/lookbehind for non-word chars too.
    pattern = re.compile(
        r'(?<![A-Za-z0-9])' + escaped + r'(?![A-Za-z0-9])',
        re.IGNORECASE,
    )
    return pattern.sub('', text)
