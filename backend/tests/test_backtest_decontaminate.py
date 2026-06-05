"""Tests for decontaminate.py — TDD-first, known real leak cases from YC dataset."""

import pytest
from eval.backtest.decontaminate import decontaminate


# ---------------------------------------------------------------------------
# Fixtures: real known-leak cases from the spec
# ---------------------------------------------------------------------------

FORTY_TWO_FLOORS_RECORD = {
    "name": "42Floors",
    "former_names": [],
    "long_description": (
        "*Acquired by Knotel in 2018\r\n\r\n"
        "42Floors was founded in November of 2011 with the vision of making it easy "
        "to discover and create your dream office space. We help companies find the "
        "perfect office for their team. Browse thousands of listings nationwide."
    ),
    "one_liner": "Find office space for your company.",
}

SLIDE_PAY_RECORD = {
    "name": "SlidePay",
    "former_names": ["Cube"],
    "long_description": (
        "SlidePay, formerly Cube, is an API that makes it easy for any app to accept "
        "credit cards that are processed in person. Integration takes hours, not weeks, "
        "and works on any platform or device."
    ),
    "one_liner": "Banking and Payment Platform APIs. Exited October 2014.",
}

OUTCOME_ONLY_RECORD = {
    "name": "DeadCo",
    "former_names": [],
    "long_description": "Acquired by BigCorp in 2015. Now part of BigCorp.",
    "one_liner": "Acquired.",
}

CLEAN_RECORD = {
    "name": "CleanStartup",
    "former_names": [],
    "long_description": (
        "CleanStartup makes it easy for small businesses to manage invoices and "
        "payments online. Our platform saves accountants hours every week."
    ),
    "one_liner": "Invoice management for small businesses.",
}

HIRING_RECORD = {
    "name": "HiringCo",
    "former_names": [],
    "long_description": (
        "HiringCo builds developer tools for continuous integration. "
        "We're hiring! Join us and apply today at https://hiringco.com/jobs."
    ),
    "one_liner": "CI tools for developers.",
}


# ---------------------------------------------------------------------------
# Tests: 42Floors
# ---------------------------------------------------------------------------

class TestFortyTwoFloors:
    def test_acquired_phrase_removed(self):
        result = decontaminate(FORTY_TWO_FLOORS_RECORD)
        assert "Acquired by Knotel" not in result
        assert "acquired" not in result.lower()

    def test_company_name_removed(self):
        result = decontaminate(FORTY_TWO_FLOORS_RECORD)
        assert "42Floors" not in result

    def test_core_pitch_retained(self):
        result = decontaminate(FORTY_TWO_FLOORS_RECORD)
        # The retained pitch text should reference finding office space for companies
        assert "office" in result.lower()

    def test_result_is_non_empty(self):
        result = decontaminate(FORTY_TWO_FLOORS_RECORD)
        assert len(result) >= 15


# ---------------------------------------------------------------------------
# Tests: SlidePay
# ---------------------------------------------------------------------------

class TestSlidePay:
    def test_exited_clause_removed(self):
        result = decontaminate(SLIDE_PAY_RECORD)
        assert "Exited October 2014" not in result
        assert "exited" not in result.lower()

    def test_company_name_removed(self):
        result = decontaminate(SLIDE_PAY_RECORD)
        assert "SlidePay" not in result

    def test_former_name_removed(self):
        # "Cube" as whole word — should not appear as a standalone name token
        result = decontaminate(SLIDE_PAY_RECORD)
        # The former name "Cube" should be stripped
        import re
        assert not re.search(r'\bCube\b', result, re.IGNORECASE)

    def test_credit_cards_pitch_retained(self):
        result = decontaminate(SLIDE_PAY_RECORD)
        assert "credit cards" in result.lower()

    def test_result_is_non_empty(self):
        result = decontaminate(SLIDE_PAY_RECORD)
        assert len(result) >= 15


# ---------------------------------------------------------------------------
# Tests: Outcome-only record → returns ""
# ---------------------------------------------------------------------------

class TestOutcomeOnly:
    def test_returns_empty_for_outcome_only(self):
        result = decontaminate(OUTCOME_ONLY_RECORD)
        assert result == ""


# ---------------------------------------------------------------------------
# Tests: Clean record → retained roughly intact
# ---------------------------------------------------------------------------

class TestCleanRecord:
    def test_clean_record_retained(self):
        result = decontaminate(CLEAN_RECORD)
        assert "invoice" in result.lower() or "invoices" in result.lower()
        assert "payments" in result.lower()

    def test_name_stripped_from_clean_record(self):
        result = decontaminate(CLEAN_RECORD)
        assert "CleanStartup" not in result

    def test_clean_record_non_empty(self):
        result = decontaminate(CLEAN_RECORD)
        assert len(result) >= 15


# ---------------------------------------------------------------------------
# Tests: Hiring/boilerplate stripped
# ---------------------------------------------------------------------------

class TestHiringBoilerplate:
    def test_hiring_phrase_removed(self):
        result = decontaminate(HIRING_RECORD)
        assert "we're hiring" not in result.lower()
        assert "join us" not in result.lower()
        assert "apply today" not in result.lower()

    def test_careers_url_removed(self):
        result = decontaminate(HIRING_RECORD)
        assert "hiringco.com/jobs" not in result

    def test_core_pitch_retained_after_hiring_strip(self):
        result = decontaminate(HIRING_RECORD)
        assert "developer tools" in result.lower() or "continuous integration" in result.lower()


# ---------------------------------------------------------------------------
# Tests: Additional outcome phrase variants
# ---------------------------------------------------------------------------

class TestOutcomePhraseVariants:
    @pytest.mark.parametrize("phrase,description", [
        ("shut down last year.", "shut down"),
        ("The company shutdown in 2020.", "shutdown"),
        ("wound down operations.", "wound down"),
        ("closed down in 2019.", "closed down"),
        ("closed its doors.", "closed"),
        ("Now part of Google.", "now part of"),
        ("Exited June 2016.", "exit date clause"),
        ("The startup exited via acquisition.", "exited"),
    ])
    def test_outcome_phrase_variant_removed(self, phrase, description):
        record = {
            "name": "TestCo",
            "former_names": [],
            "long_description": None,
            "one_liner": phrase,
        }
        result = decontaminate(record)
        assert result == "", f"Expected empty string for outcome phrase: {description!r}"

    def test_acquired_variant_removed(self):
        record = {
            "name": "TestCo",
            "former_names": [],
            "long_description": "TestCo was acquired by BigCorp.",
            "one_liner": None,
        }
        result = decontaminate(record)
        assert "acquired" not in result.lower()


# ---------------------------------------------------------------------------
# Tests: Fallback hierarchy (long_description → one_liner → "")
# ---------------------------------------------------------------------------

class TestTextFallback:
    def test_uses_long_description_when_present(self):
        record = {
            "name": "Foo",
            "former_names": [],
            "long_description": "Foo builds amazing widgets for factories.",
            "one_liner": "Widget builder.",
        }
        result = decontaminate(record)
        assert "factories" in result.lower()

    def test_falls_back_to_one_liner_when_no_long_description(self):
        record = {
            "name": "Foo",
            "former_names": [],
            "long_description": None,
            "one_liner": "Foo makes widgets for factories.",
        }
        result = decontaminate(record)
        assert "factories" in result.lower()

    def test_empty_long_description_triggers_fallback(self):
        record = {
            "name": "Foo",
            "former_names": [],
            "long_description": "",
            "one_liner": "Foo makes widgets for factories.",
        }
        result = decontaminate(record)
        assert "factories" in result.lower()

    def test_no_text_returns_empty(self):
        record = {
            "name": "Foo",
            "former_names": [],
            "long_description": None,
            "one_liner": None,
        }
        result = decontaminate(record)
        assert result == ""

    def test_short_result_returns_empty(self):
        record = {
            "name": "Foo",
            "former_names": [],
            "long_description": None,
            "one_liner": "Foo builds.",  # after stripping "Foo" → "builds." which is < 15 chars
        }
        result = decontaminate(record)
        assert result == ""
