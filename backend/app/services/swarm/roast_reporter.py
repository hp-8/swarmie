"""
Roast reporter.

Synthesize all agent reactions into a single PMF scorecard for the founder.
Output is JSON-structured so the frontend can render a clean card; the LLM
synthesizes a short narrative summary, but the headline metrics are computed
deterministically from the reactions (no fabrication).
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

from ...utils.llm import LLM, UsageTracker
from .pitch_parser import ParsedPitch
from .swarm_runner import AgentReaction

logger = logging.getLogger("swarmie.swarm.roast_reporter")


@dataclass
class RoastReport:
    """The founder-facing report."""
    pmf_score: float  # 0-10
    headline: str
    sentiment_split: dict[str, float]  # {positive, neutral, negative} percentages
    action_split: dict[str, int]  # {post, comment, upvote, ignore} counts
    top_objections: list[dict[str, Any]]  # [{category, count, example_quote}]
    icp_fit: dict[str, dict[str, Any]]  # per-segment fit + count
    messaging_gaps: list[str]
    narrative: str  # 2-3 paragraph synthesis
    quoted_reactions: list[dict[str, Any]]  # top 10 most representative

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_NARRATIVE_SYSTEM = """You are a startup advisor. Synthesize the swarm of agent reactions into a sharp 2-3 paragraph narrative for the founder.

Be direct. Lead with the strongest signal — positive or negative. Cite specific
objection patterns and ICP fit. Do not pad. Do not soften.

Format:
- Paragraph 1: the strongest signal (1-3 sentences).
- Paragraph 2: top concrete objections with a short framing of why they matter.
- Paragraph 3: the messaging fix or experiment you would run next.

Plain prose. No headers, no bullet points. Under 250 words."""


def _compute_sentiment_split(reactions: list[AgentReaction]) -> dict[str, float]:
    """Bucket reactions by sentiment into positive / neutral / negative."""
    speaking = [r for r in reactions if r.action in ("comment", "post")]
    if not speaking:
        return {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
    pos = sum(1 for r in speaking if r.sentiment > 0.2)
    neg = sum(1 for r in speaking if r.sentiment < -0.2)
    neu = len(speaking) - pos - neg
    n = len(speaking)
    return {
        "positive": round(pos / n * 100, 1),
        "neutral": round(neu / n * 100, 1),
        "negative": round(neg / n * 100, 1),
    }


def _compute_action_split(reactions: list[AgentReaction]) -> dict[str, int]:
    c = Counter(r.action for r in reactions)
    return {k: c.get(k, 0) for k in ("post", "comment", "upvote", "ignore")}


def _compute_top_objections(reactions: list[AgentReaction], top_k: int = 5) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    examples: dict[str, str] = {}
    for r in reactions:
        for obj in r.objections:
            counter[obj] += 1
            if obj not in examples and r.text:
                examples[obj] = r.text
    top = counter.most_common(top_k)
    return [
        {"category": cat, "count": n, "example_quote": examples.get(cat, "")}
        for cat, n in top
    ]


def _compute_icp_fit(reactions: list[AgentReaction]) -> dict[str, dict[str, Any]]:
    """Per-segment: count, avg sentiment, dominant action."""
    by_segment: dict[str, list[AgentReaction]] = {}
    for r in reactions:
        by_segment.setdefault(r.segment, []).append(r)
    out: dict[str, dict[str, Any]] = {}
    for seg, items in by_segment.items():
        speaking = [r for r in items if r.action in ("comment", "post")]
        avg_sent = (
            sum(r.sentiment for r in speaking) / len(speaking) if speaking else 0.0
        )
        actions = Counter(r.action for r in items)
        dominant = actions.most_common(1)[0][0] if actions else "ignore"
        out[seg] = {
            "count": len(items),
            "avg_sentiment": round(avg_sent, 3),
            "dominant_action": dominant,
            "speaking_count": len(speaking),
        }
    return out


def _compute_pmf_score(
    sentiment_split: dict[str, float],
    action_split: dict[str, int],
    icp_fit: dict[str, dict[str, Any]],
) -> float:
    """Heuristic 0-10 PMF score. Not predictive truth — directional signal."""
    total_actions = sum(action_split.values()) or 1
    engagement_rate = (
        action_split["comment"] + action_split["post"] + 0.5 * action_split["upvote"]
    ) / total_actions
    sentiment_score = (
        sentiment_split["positive"] - sentiment_split["negative"]
    ) / 100.0  # -1..1
    segment_fit = (
        sum(1 for v in icp_fit.values() if v["avg_sentiment"] > 0.1)
        / max(len(icp_fit), 1)
    )
    raw = (engagement_rate * 4) + ((sentiment_score + 1) * 2) + (segment_fit * 4)
    return round(min(max(raw, 0.0), 10.0), 1)


def _pick_quoted_reactions(reactions: list[AgentReaction], k: int = 10) -> list[dict[str, Any]]:
    """Pick the most informative reactions: top by extremity of sentiment + has text."""
    with_text = [r for r in reactions if r.text]
    with_text.sort(key=lambda r: abs(r.sentiment), reverse=True)
    return [r.to_dict() for r in with_text[:k]]


class RoastReporter:
    """Compose final report. One synth-tier LLM call for narrative; metrics are deterministic."""

    def __init__(self, tracker: UsageTracker | None = None):
        self.llm = LLM(tier="synth", tracker=tracker)

    def report(self, pitch: ParsedPitch, reactions: list[AgentReaction]) -> RoastReport:
        sentiment_split = _compute_sentiment_split(reactions)
        action_split = _compute_action_split(reactions)
        top_objections = _compute_top_objections(reactions)
        icp_fit = _compute_icp_fit(reactions)
        pmf_score = _compute_pmf_score(sentiment_split, action_split, icp_fit)
        quoted = _pick_quoted_reactions(reactions)

        narrative, headline, gaps = self._synthesize(
            pitch, sentiment_split, action_split, top_objections, icp_fit, pmf_score, quoted
        )

        return RoastReport(
            pmf_score=pmf_score,
            headline=headline,
            sentiment_split=sentiment_split,
            action_split=action_split,
            top_objections=top_objections,
            icp_fit=icp_fit,
            messaging_gaps=gaps,
            narrative=narrative,
            quoted_reactions=quoted,
        )

    def _synthesize(
        self,
        pitch: ParsedPitch,
        sentiment_split: dict[str, float],
        action_split: dict[str, int],
        top_objections: list[dict[str, Any]],
        icp_fit: dict[str, dict[str, Any]],
        pmf_score: float,
        quoted: list[dict[str, Any]],
    ) -> tuple[str, str, list[str]]:
        payload = {
            "pitch_one_liner": pitch.one_liner,
            "pitch_problem": pitch.problem,
            "pitch_solution": pitch.solution,
            "target_icp": pitch.target_icp,
            "pmf_score": pmf_score,
            "sentiment_split_pct": sentiment_split,
            "action_split_counts": action_split,
            "top_objections": top_objections,
            "icp_fit_by_segment": icp_fit,
            "representative_reactions": [
                {"name": q["name"], "tone": q["tone"], "text": q["text"][:280]}
                for q in quoted[:8]
            ],
        }

        messages = [
            {"role": "system", "content": _NARRATIVE_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"DATA:\n{payload}\n\n"
                    "Return JSON with keys:\n"
                    "  headline       (string, <90 chars, blunt, one-line takeaway)\n"
                    "  narrative      (string, the 2-3 paragraph synthesis)\n"
                    "  messaging_gaps (array of 2-4 short strings — concrete things to fix)\n"
                    "JSON only."
                ),
            },
        ]
        try:
            data = self.llm.chat_json(messages, temperature=0.4, max_tokens=1200)
        except Exception as exc:
            logger.warning(f"narrative synthesis failed: {exc}; using deterministic fallback")
            data = {}

        narrative = str(data.get("narrative", "")).strip() or self._fallback_narrative(
            pmf_score, sentiment_split, top_objections
        )
        headline = str(data.get("headline", "")).strip() or f"PMF score {pmf_score}/10"
        gaps = [str(g).strip() for g in data.get("messaging_gaps", []) if str(g).strip()]

        return narrative, headline, gaps

    @staticmethod
    def _fallback_narrative(
        pmf_score: float,
        sentiment_split: dict[str, float],
        top_objections: list[dict[str, Any]],
    ) -> str:
        obj_str = (
            ", ".join(o["category"] for o in top_objections[:3]) or "no clear objections"
        )
        return (
            f"PMF score: {pmf_score}/10. Sentiment is "
            f"{sentiment_split['positive']:.0f}% positive, "
            f"{sentiment_split['negative']:.0f}% negative. "
            f"Top concerns from the swarm: {obj_str}."
        )
