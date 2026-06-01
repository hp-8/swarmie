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
    top_objections: list[dict[str, Any]]  # [{category, count, example_quote, real_test, kill_criteria, suggested_fix}]
    icp_fit: dict[str, dict[str, Any]]  # per-segment fit + count
    messaging_gaps: list[str]
    narrative: str  # 2-3 paragraph synthesis
    quoted_reactions: list[dict[str, Any]]  # top 10 most representative
    # --- decision brief fields (additive) ---
    verdict: str = "sharpen_positioning"  # "ship_it" | "sharpen_positioning" | "wrong_audience" | "kill"
    verdict_reason: str = ""  # one blunt line < 120 chars
    next_action: str = ""  # single most important move before writing more code, < 160 chars
    confidence: str = "low"  # "low" | "med" | "high"
    confidence_reason: str = ""  # one line
    # --- silence signal (workstream B): why agents scrolled past ---
    ignore_reasons: list[dict[str, Any]] = field(default_factory=list)
    # [{category, label, sampled_count, share_pct, example, implication}]
    silent_share_pct: float = 0.0  # ignore actions as % of all agents
    # --- deck intelligence (investor deck uploads): pitch-intelligence diagnosis ---
    deck_diagnosis: dict[str, Any] | None = None  # DeckDiagnosis.to_dict() or None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_NARRATIVE_SYSTEM = """You are a startup advisor. Synthesize the swarm of agent reactions into a sharp 2-3 paragraph narrative for the founder, and produce a decision brief.

Be direct. Lead with the strongest signal — positive or negative. Cite specific
objection patterns and ICP fit. Do not pad. Do not soften.

Silence is signal. `silent_share_pct` is the share who scrolled past, and
`why_they_scrolled_past` clusters why. A high silent share or one dominant
ignore reason (e.g. "couldn't tell what it does") should weigh heavily on the
verdict and next_action — not just the loud objections.

Narrative format:
- Paragraph 1: the strongest signal (1-3 sentences).
- Paragraph 2: top concrete objections with a short framing of why they matter.
- Paragraph 3: the messaging fix or experiment you would run next.

Plain prose. No headers, no bullet points. Under 250 words.

Decision brief rules:
- verdict: one of "ship_it" | "sharpen_positioning" | "wrong_audience" | "kill"
  * ship_it: strong signal, clear ICP, low objection rate — go build + distribute
  * sharpen_positioning: decent engagement but objections reveal a framing problem
  * wrong_audience: the swarm engaged but the ICP clearly doesn't match the pitch
  * kill: fundamental demand problem, rethink the problem/solution entirely
- verdict_reason: one blunt line under 120 chars — the single decisive factor
- next_action: the single most important move before writing more code, under 160 chars
- confidence: "low" | "med" | "high" — how much weight to put on this signal
- confidence_reason: one line (e.g. "only 14 agents spoke; sentiment split")
- objections_enriched: for each top objection, provide:
  * category: exact category string from top_objections
  * real_test: exact question to ask 5 real users, under 160 chars
  * kill_criteria: "if N/5 say X, this positioning is dead", under 160 chars
  * suggested_fix: concrete messaging/positioning fix, under 160 chars"""


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
        {
            "category": cat,
            "count": n,
            "example_quote": examples.get(cat, ""),
            "real_test": "",
            "kill_criteria": "",
            "suggested_fix": "",
        }
        for cat, n in top
    ]


# Decision-useful framing for each ignore category — static, not fabricated.
_IGNORE_LABELS = {
    "not_my_problem": "not my problem",
    "unclear_value": "couldn't tell what it does",
    "seen_before": "seen this before",
    "dont_care": "don't care enough",
    "price_or_effort": "not worth a look",
    "wrong_timing": "wrong timing",
}
_IGNORE_IMPLICATIONS = {
    "not_my_problem": "Targeting is off — these people aren't your ICP. Tighten who you're speaking to.",
    "unclear_value": "Clarity gap — they couldn't parse the value. Rewrite the one-liner to lead with the outcome.",
    "seen_before": "Differentiation gap — you read as me-too. Sharpen the wedge that makes you different.",
    "dont_care": "Weak pain — this is a vitamin, not a painkiller. Re-anchor on a sharper, costlier problem.",
    "price_or_effort": "Cost/effort anchor — the perceived price or switch isn't worth a look. Reframe ROI or lower the entry friction.",
    "wrong_timing": "Timing mismatch — relevant later, not now. Find the trigger event that makes it urgent.",
}


def _compute_ignore_reasons(
    reactions: list[AgentReaction],
    labels: dict[str, str] | None = None,
    implications: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], float]:
    """Cluster the SAMPLED ignore reasons into decision-useful categories.

    Counts are from the sampled subset only; `share_pct` is that subset's
    category share extrapolated to the whole ignoring population. Honest:
    we report it as the silent-sample distribution, not a fabricated total.
    """
    labels = labels if labels is not None else _IGNORE_LABELS
    implications = implications if implications is not None else _IGNORE_IMPLICATIONS
    total = len(reactions) or 1
    all_ignores = [r for r in reactions if r.action == "ignore"]
    sampled = [r for r in all_ignores if getattr(r, "ignore_reason_category", "")]
    silent_share_pct = round(len(all_ignores) / total * 100, 1)

    if not sampled:
        return [], silent_share_pct

    counter: Counter[str] = Counter()
    examples: dict[str, str] = {}
    for r in sampled:
        cat = r.ignore_reason_category
        counter[cat] += 1
        if cat not in examples and r.ignore_reason:
            examples[cat] = r.ignore_reason
    n_sampled = len(sampled)
    out: list[dict[str, Any]] = []
    for cat, count in counter.most_common(4):
        out.append({
            "category": cat,
            "label": labels.get(cat, cat),
            "sampled_count": count,
            "share_pct": round(count / n_sampled * 100, 1),
            "example": examples.get(cat, ""),
            "implication": implications.get(cat, ""),
        })
    return out, silent_share_pct


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
    """Compose final report. One synth-tier LLM call for narrative; metrics are deterministic.

    Per-swarm variation lives in the overridable class attrs: NARRATIVE_SYSTEM,
    VALID_VERDICTS, DEFAULT_VERDICT, VERDICT_ENUM_HINT and the ignore-label maps.
    The deterministic metrics are swarm-agnostic and shared.
    """

    NARRATIVE_SYSTEM = _NARRATIVE_SYSTEM
    VALID_VERDICTS = {"ship_it", "sharpen_positioning", "wrong_audience", "kill"}
    DEFAULT_VERDICT = "sharpen_positioning"
    VERDICT_ENUM_HINT = "ship_it | sharpen_positioning | wrong_audience | kill"
    IGNORE_LABELS = _IGNORE_LABELS
    IGNORE_IMPLICATIONS = _IGNORE_IMPLICATIONS

    def __init__(self, tracker: UsageTracker | None = None):
        self.llm = LLM(tier="synth", tracker=tracker)

    def report(self, pitch: ParsedPitch, reactions: list[AgentReaction]) -> RoastReport:
        sentiment_split = _compute_sentiment_split(reactions)
        action_split = _compute_action_split(reactions)
        top_objections = _compute_top_objections(reactions)
        icp_fit = _compute_icp_fit(reactions)
        pmf_score = _compute_pmf_score(sentiment_split, action_split, icp_fit)
        quoted = _pick_quoted_reactions(reactions)
        ignore_reasons, silent_share_pct = _compute_ignore_reasons(
            reactions, self.IGNORE_LABELS, self.IGNORE_IMPLICATIONS
        )

        narrative, headline, gaps, verdict, verdict_reason, next_action, confidence, confidence_reason, top_objections = self._synthesize(
            pitch, sentiment_split, action_split, top_objections, icp_fit, pmf_score, quoted, reactions,
            ignore_reasons, silent_share_pct,
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
            verdict=verdict,
            verdict_reason=verdict_reason,
            next_action=next_action,
            confidence=confidence,
            confidence_reason=confidence_reason,
            ignore_reasons=ignore_reasons,
            silent_share_pct=silent_share_pct,
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
        reactions: list[Any],
        ignore_reasons: list[dict[str, Any]] | None = None,
        silent_share_pct: float = 0.0,
    ) -> tuple[str, str, list[str], str, str, str, str, str, list[dict[str, Any]]]:
        ignore_reasons = ignore_reasons or []
        # Deterministic confidence ceiling
        speaking_count = sum(1 for r in reactions if getattr(r, "action", None) in ("comment", "post"))
        pos_pct = sentiment_split.get("positive", 0.0)
        neg_pct = sentiment_split.get("negative", 0.0)
        if speaking_count < 15:
            confidence_ceiling = "low"
        elif pos_pct > 30.0 and neg_pct > 30.0:
            confidence_ceiling = "med"
        else:
            confidence_ceiling = "high"

        # Strip enrichment fields from the payload sent to LLM (they're empty at this point)
        payload_objections = [
            {"category": o["category"], "count": o["count"], "example_quote": o["example_quote"]}
            for o in top_objections
        ]

        payload = {
            "pitch_one_liner": pitch.one_liner,
            "pitch_problem": pitch.problem,
            "pitch_solution": pitch.solution,
            "target_icp": pitch.target_icp,
            "pmf_score": pmf_score,
            "sentiment_split_pct": sentiment_split,
            "action_split_counts": action_split,
            "top_objections": payload_objections,
            "icp_fit_by_segment": icp_fit,
            "representative_reactions": [
                {"name": q["name"], "tone": q["tone"], "text": q["text"][:280]}
                for q in quoted[:8]
            ],
            "speaking_reaction_count": speaking_count,
            "silent_share_pct": silent_share_pct,
            "why_they_scrolled_past": [
                {"reason": ir["label"], "share_of_sampled_pct": ir["share_pct"], "example": ir["example"]}
                for ir in ignore_reasons
            ],
        }

        messages = [
            {"role": "system", "content": self.NARRATIVE_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"DATA:\n{payload}\n\n"
                    "Return JSON with keys:\n"
                    "  headline          (string, <90 chars, blunt, one-line takeaway)\n"
                    "  narrative         (string, the 2-3 paragraph synthesis)\n"
                    "  messaging_gaps    (array of 2-4 short strings — concrete things to fix)\n"
                    f"  verdict           (string, one of: {self.VERDICT_ENUM_HINT})\n"
                    "  verdict_reason    (string, <120 chars, one blunt line — the decisive factor)\n"
                    "  next_action       (string, <160 chars, single most important move before more code)\n"
                    f"  confidence        (string, one of: low | med | high — MUST NOT exceed ceiling '{confidence_ceiling}')\n"
                    "  confidence_reason (string, one line — e.g. 'only 14 agents spoke; sentiment split')\n"
                    "  objections_enriched (array of objects, one per top objection, with keys:\n"
                    "    category (string, exact match to top_objections category),\n"
                    "    real_test (string, <160 chars, exact question to ask 5 real users),\n"
                    "    kill_criteria (string, <160 chars, e.g. 'if 3/5 say X, this positioning is dead'),\n"
                    "    suggested_fix (string, <160 chars, concrete messaging/positioning fix)\n"
                    "  )\n"
                    "JSON only."
                ),
            },
        ]
        try:
            data = self.llm.chat_json(messages, temperature=0.4, max_tokens=1800)
        except Exception as exc:
            logger.warning(f"narrative synthesis failed: {exc}; using deterministic fallback")
            data = {}

        narrative = str(data.get("narrative", "")).strip() or self._fallback_narrative(
            pmf_score, sentiment_split, top_objections
        )
        headline = str(data.get("headline", "")).strip() or f"PMF score {pmf_score}/10"
        gaps = [str(g).strip() for g in data.get("messaging_gaps", []) if str(g).strip()]

        # Decision brief fields
        verdict = str(data.get("verdict", self.DEFAULT_VERDICT)).strip()
        if verdict not in self.VALID_VERDICTS:
            verdict = self.DEFAULT_VERDICT

        verdict_reason = str(data.get("verdict_reason", "")).strip()
        if not verdict_reason:
            verdict_reason = self._fallback_verdict_reason(pmf_score, sentiment_split)

        next_action = str(data.get("next_action", "")).strip()
        if not next_action:
            next_action = self._fallback_next_action(top_objections)

        # Clamp confidence to ceiling
        valid_confidences = {"low": 0, "med": 1, "high": 2}
        ceiling_rank = valid_confidences.get(confidence_ceiling, 2)
        llm_confidence = str(data.get("confidence", "low")).strip()
        if llm_confidence not in valid_confidences:
            llm_confidence = "low"
        llm_rank = valid_confidences[llm_confidence]
        confidence = llm_confidence if llm_rank <= ceiling_rank else confidence_ceiling

        confidence_reason = str(data.get("confidence_reason", "")).strip()
        if not confidence_reason:
            confidence_reason = f"{speaking_count} agents spoke; pos={pos_pct:.0f}% neg={neg_pct:.0f}%"

        # Merge objections_enriched into top_objections by category
        enriched_map: dict[str, dict[str, str]] = {}
        for item in data.get("objections_enriched", []):
            cat = str(item.get("category", "")).strip()
            if cat:
                enriched_map[cat] = {
                    "real_test": str(item.get("real_test", "")).strip(),
                    "kill_criteria": str(item.get("kill_criteria", "")).strip(),
                    "suggested_fix": str(item.get("suggested_fix", "")).strip(),
                }

        merged_objections = []
        for obj in top_objections:
            cat = obj["category"]
            enrichment = enriched_map.get(cat, {})
            merged_objections.append({
                **obj,
                "real_test": enrichment.get("real_test", ""),
                "kill_criteria": enrichment.get("kill_criteria", ""),
                "suggested_fix": enrichment.get("suggested_fix", ""),
            })

        return narrative, headline, gaps, verdict, verdict_reason, next_action, confidence, confidence_reason, merged_objections

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

    @staticmethod
    def _fallback_verdict_reason(
        pmf_score: float,
        sentiment_split: dict[str, float],
    ) -> str:
        pos = sentiment_split.get("positive", 0.0)
        neg = sentiment_split.get("negative", 0.0)
        return f"PMF {pmf_score}/10; {pos:.0f}% positive, {neg:.0f}% negative — positioning needs work."[:120]

    @staticmethod
    def _fallback_next_action(top_objections: list[dict[str, Any]]) -> str:
        if top_objections:
            top_cat = top_objections[0]["category"]
            return f"Interview 5 target users specifically about '{top_cat}' before writing more code."[:160]
        return "Run 5 customer discovery interviews to validate the core problem before any new features."[:160]


# --- Investor swarm reporter ---

_INVESTOR_NARRATIVE_SYSTEM = """You are a seasoned early-stage investor and ex-founder advising on fundability. Synthesize the swarm of investor reactions into a sharp 2-3 paragraph narrative, and produce a fundability decision brief.

Be direct. This is decision stress-testing against patterns from real investor
behavior — NOT a prediction of whether you'll raise. Lead with the strongest
signal. Cite the specific objections and the pass reasons. Do not soften.

`silent_share_pct` is the share of investors who passed without engaging, and
`why_they_scrolled_past` clusters why they passed. A high pass rate or one
dominant pass reason (e.g. "market too small") should weigh heavily on the
verdict and next_action — not just the questions from those who engaged.

Narrative format:
- Paragraph 1: the strongest fundability signal (1-3 sentences).
- Paragraph 2: the partner-meeting objections + missing proof points that matter most.
- Paragraph 3: the one fix to make before the next investor call.

Plain prose. No headers, no bullet points. Under 250 words.

Decision brief rules:
- verdict: one of "fundable" | "sharpen_story" | "wrong_stage" | "not_fundable"
  * fundable: strong signal — clear thesis fit, proof points, would get meetings
  * sharpen_story: real interest but the narrative/proof has gaps to close first
  * wrong_stage: the substance is there but it's too early/late for this raise framing
  * not_fundable: fundamental gap (market, team, or model) — rethink before raising
- verdict_reason: one blunt line under 120 chars — the single decisive factor
- next_action: the single most important move before the next investor call, under 160 chars
- confidence: "low" | "med" | "high" — how much weight to put on this signal
- confidence_reason: one line (e.g. "only 12 investors engaged; split read")
- objections_enriched: for each top objection, provide:
  * category: exact category string from top_objections
  * real_test: the proof point or data to gather that answers this objection, under 160 chars
  * kill_criteria: "if you can't show X, this raise stalls at this objection", under 160 chars
  * suggested_fix: concrete deck/story fix, under 160 chars"""

# Investor pass-reason categories -> founder-facing label + implication.
_INVESTOR_IGNORE_LABELS = {
    "thesis_mismatch": "not our thesis / stage",
    "market_too_small": "market too small",
    "team_risk": "team risk",
    "no_moat": "no defensibility",
    "crowded": "crowded space",
    "traction_thin": "too early / no proof",
}
_INVESTOR_IGNORE_IMPLICATIONS = {
    "thesis_mismatch": "Targeting mismatch — you're pitching the wrong funds. Build a list that matches your stage and sector.",
    "market_too_small": "TAM gap — investors don't see venture-scale return. Reframe the market or the expansion path.",
    "team_risk": "Team gap — founder-market-fit isn't landing. Lead with why you're the team to win this.",
    "no_moat": "Defensibility gap — you read as easily copied. Make the moat (data, network, distribution) explicit.",
    "crowded": "Differentiation gap — you read as me-too. Sharpen the wedge that makes you inevitable.",
    "traction_thin": "Proof gap — nothing to underwrite yet. Get a sharper traction or pilot signal before raising.",
}


class InvestorReporter(RoastReporter):
    """Fundability brief: partner questions, missing proof, pass reasons, the one fix."""

    NARRATIVE_SYSTEM = _INVESTOR_NARRATIVE_SYSTEM
    VALID_VERDICTS = {"fundable", "sharpen_story", "wrong_stage", "not_fundable"}
    DEFAULT_VERDICT = "sharpen_story"
    VERDICT_ENUM_HINT = "fundable | sharpen_story | wrong_stage | not_fundable"
    IGNORE_LABELS = _INVESTOR_IGNORE_LABELS
    IGNORE_IMPLICATIONS = _INVESTOR_IGNORE_IMPLICATIONS

    @staticmethod
    def _fallback_verdict_reason(
        pmf_score: float,
        sentiment_split: dict[str, float],
    ) -> str:
        pos = sentiment_split.get("positive", 0.0)
        neg = sentiment_split.get("negative", 0.0)
        return f"Fundability {pmf_score}/10; {pos:.0f}% would-meet, {neg:.0f}% hard-pass — story needs work."[:120]

    @staticmethod
    def _fallback_next_action(top_objections: list[dict[str, Any]]) -> str:
        if top_objections:
            top_cat = top_objections[0]["category"]
            return f"Build the proof point that answers '{top_cat}' before your next investor call."[:160]
        return "Tighten the deck around traction and market before the next investor call."[:160]
