"""
Tests for eval/backtest/tier2.py — all network calls are mocked via injectable http_get.

Run: cd backend && python -m pytest tests/test_backtest_tier2.py -q
"""

from __future__ import annotations

import pytest

from eval.backtest.tier2 import find_show_hn, find_wayback, match_contemporaneous


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_hit(obj_id: str, title: str, created_at_i: int, story_text: str = "") -> dict:
    return {
        "objectID": obj_id,
        "title": title,
        "created_at_i": created_at_i,
        "story_text": story_text,
        "url": f"https://example.com/{obj_id}",
    }


def _algolia_response(hits: list[dict]) -> dict:
    return {"hits": hits, "nbHits": len(hits)}


def _wayback_response(snapshot_url: str | None) -> dict:
    if snapshot_url is None:
        return {"archived_snapshots": {}}
    return {
        "archived_snapshots": {
            "closest": {
                "available": True,
                "url": snapshot_url,
                "timestamp": "20120115120000",
                "status": "200",
            }
        }
    }


# ---------------------------------------------------------------------------
# find_show_hn
# ---------------------------------------------------------------------------

class TestFindShowHn:
    def test_returns_closest_hit_by_launched_at(self):
        """Two title-matching hits; should pick the one closest to launched_at."""
        launched_at = 1_350_000_000  # ~Oct 2012

        hit_near = _make_hit("111", "Show HN: Acme — the best tool", 1_350_100_000, "Great product")
        hit_far  = _make_hit("222", "Show HN: Acme launches today",   1_200_000_000, "Old product")

        def fake_get(url: str) -> dict:
            return _algolia_response([hit_far, hit_near])

        result = find_show_hn("Acme", launched_at, http_get=fake_get)

        assert result is not None
        assert result["source"] == "show_hn"
        assert "111" in result["url"]       # near hit selected
        assert "Show HN: Acme" in result["text"]
        assert "Great product" in result["text"]

    def test_title_must_contain_name(self):
        """Hits whose title does NOT contain the company name are filtered out."""
        launched_at = 1_350_000_000

        unrelated = _make_hit("333", "Show HN: SomeOtherCo launches", 1_350_000_001)

        def fake_get(url: str) -> dict:
            return _algolia_response([unrelated])

        result = find_show_hn("Acme", launched_at, http_get=fake_get)
        assert result is None

    def test_no_hits_returns_none(self):
        """Empty hits list → None."""
        def fake_get(url: str) -> dict:
            return _algolia_response([])

        result = find_show_hn("GhostCo", 1_400_000_000, http_get=fake_get)
        assert result is None

    def test_launched_at_none_picks_first_title_match(self):
        """When launched_at is None, return the first title-matching hit."""
        hit_a = _make_hit("10", "Show HN: Zeta widget", 1_300_000_000)
        hit_b = _make_hit("20", "Show HN: Zeta v2 launch", 1_400_000_000)

        def fake_get(url: str) -> dict:
            return _algolia_response([hit_a, hit_b])

        result = find_show_hn("Zeta", None, http_get=fake_get)
        assert result is not None
        assert "10" in result["url"]   # first match

    def test_url_built_from_object_id(self):
        """Returned url must point to news.ycombinator.com with the objectID."""
        hit = _make_hit("9999", "Show HN: MyApp — fast auth", 1_350_000_000)

        def fake_get(url: str) -> dict:
            return _algolia_response([hit])

        result = find_show_hn("MyApp", 1_350_000_000, http_get=fake_get)
        assert result is not None
        assert result["url"] == "https://news.ycombinator.com/item?id=9999"

    def test_case_insensitive_name_match(self):
        """Name matching is case-insensitive."""
        hit = _make_hit("55", "Show HN: DROPBOX launches", 1_300_000_000)

        def fake_get(url: str) -> dict:
            return _algolia_response([hit])

        result = find_show_hn("Dropbox", 1_300_000_000, http_get=fake_get)
        assert result is not None


# ---------------------------------------------------------------------------
# find_wayback
# ---------------------------------------------------------------------------

class TestFindWayback:
    def test_returns_snapshot_url_when_available(self):
        snapshot = "https://web.archive.org/web/20120115120000/https://example.com/"

        def fake_get(url: str) -> dict:
            return _wayback_response(snapshot)

        result = find_wayback("https://example.com", 2012, http_get=fake_get)

        assert result is not None
        assert result["source"] == "wayback"
        assert result["url"] == snapshot
        assert result["text"] == snapshot

    def test_returns_none_when_no_snapshots(self):
        def fake_get(url: str) -> dict:
            return _wayback_response(None)

        result = find_wayback("https://ghost.io", 2011, http_get=fake_get)
        assert result is None

    def test_returns_none_when_available_false(self):
        def fake_get(url: str) -> dict:
            return {
                "archived_snapshots": {
                    "closest": {
                        "available": False,
                        "url": "https://web.archive.org/web/20110101/https://ghost.io",
                    }
                }
            }

        result = find_wayback("https://ghost.io", 2011, http_get=fake_get)
        assert result is None

    def test_algolia_url_contains_timestamp(self):
        """The request URL must embed <year>0101 as the timestamp."""
        captured: list[str] = []

        def fake_get(url: str) -> dict:
            captured.append(url)
            return _wayback_response(None)

        find_wayback("https://foo.com", 2014, http_get=fake_get)
        assert captured, "http_get was never called"
        assert "20140101" in captured[0]


# ---------------------------------------------------------------------------
# match_contemporaneous
# ---------------------------------------------------------------------------

class TestMatchContemporaneous:
    def _make_company(self, name: str = "Acme", batch: str = "W12",
                      launched_at: int = 1_350_000_000,
                      website: str = "https://acme.com") -> dict:
        return {"name": name, "batch": batch, "launched_at": launched_at, "website": website}

    def test_returns_show_hn_hit_without_calling_wayback(self):
        """If Show HN succeeds, Wayback must never be queried."""
        hn_hit = _make_hit("42", "Show HN: Acme — fast payments", 1_350_000_000)
        wayback_called: list[bool] = []

        def fake_get(url: str) -> dict:
            if "algolia" in url:
                return _algolia_response([hn_hit])
            # Any Wayback call is unexpected
            wayback_called.append(True)
            return _wayback_response(None)

        company = self._make_company()
        result = match_contemporaneous(company, http_get=fake_get)

        assert result is not None
        assert result["source"] == "show_hn"
        assert not wayback_called, "Wayback was queried unnecessarily"

    def test_falls_back_to_wayback_on_show_hn_miss(self):
        """If Show HN returns no title-match, Wayback should be tried."""
        snapshot = "https://web.archive.org/web/20120101120000/https://acme.com/"

        def fake_get(url: str) -> dict:
            if "algolia" in url:
                return _algolia_response([])   # no HN hits
            return _wayback_response(snapshot)

        company = self._make_company()
        result = match_contemporaneous(company, http_get=fake_get)

        assert result is not None
        assert result["source"] == "wayback"

    def test_returns_none_when_both_sources_miss(self):
        def fake_get(url: str) -> dict:
            if "algolia" in url:
                return _algolia_response([])
            return _wayback_response(None)

        company = self._make_company()
        result = match_contemporaneous(company, http_get=fake_get)
        assert result is None

    def test_skips_wayback_when_no_website(self):
        """Company with empty website should not call Wayback at all."""
        wayback_called: list[bool] = []

        def fake_get(url: str) -> dict:
            if "algolia" in url:
                return _algolia_response([])
            wayback_called.append(True)
            return _wayback_response("https://archive.org/snap")

        company = self._make_company(website="")
        result = match_contemporaneous(company, http_get=fake_get)

        assert result is None
        assert not wayback_called


# ---------------------------------------------------------------------------
# Live network smoke test (normally skipped)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="live network — run manually to verify real HN Algolia")
def test_live_show_hn_airbnb():
    """Hit real HN Algolia for Airbnb and assert we get a reasonable result."""
    result = find_show_hn("Airbnb", launched_at=None)
    assert result is not None
    assert result["source"] == "show_hn"
    assert "airbnb" in result["text"].lower() or "airbedandbreakfast" in result["text"].lower()
