"""
Canned reactions for --mode synth.

These are hand-crafted AgentReaction-compatible dicts that let roast_reporter
run deterministically without any LLM calls. One reaction set per golden case.

Each reaction matches the AgentReaction dataclass signature:
  agent_id, archetype_id, segment, name, tone, action,
  text, objections, sentiment, ignore_reason, ignore_reason_category
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Minimal AgentReaction stub (mirrors the real dataclass without requiring
# env vars / LLM setup at import time).
# ---------------------------------------------------------------------------

@dataclass
class _CannedReaction:
    agent_id: str
    archetype_id: str
    segment: str
    name: str
    tone: str
    action: str
    text: str = ""
    objections: list = field(default_factory=list)
    sentiment: float = 0.0
    ignore_reason: str = ""
    ignore_reason_category: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "archetype_id": self.archetype_id,
            "segment": self.segment,
            "name": self.name,
            "tone": self.tone,
            "action": self.action,
            "text": self.text,
            "objections": self.objections,
            "sentiment": self.sentiment,
            "ignore_reason": self.ignore_reason,
            "ignore_reason_category": self.ignore_reason_category,
        }


def _r(i, seg, tone, action, text="", objections=None, sentiment=0.0,
        ig_reason="", ig_cat=""):
    return _CannedReaction(
        agent_id=f"canned_{i:04d}",
        archetype_id=f"arch_{seg[:4]}",
        segment=seg, name=f"Agent{i}", tone=tone, action=action,
        text=text, objections=objections or [],
        sentiment=sentiment, ignore_reason=ig_reason,
        ignore_reason_category=ig_cat,
    )


# ---------------------------------------------------------------------------
# tally_validate — strong pitch, positive tilt with expected objections
# ---------------------------------------------------------------------------
TALLY_VALIDATE = [
    _r(0,  "freelance_designer", "enthusiastic", "post",
       "finally an invoicing tool that doesn't make me recreate my week from scratch. "
       "i lose maybe $200/month to forgotten invoices and this is exactly what i need.",
       ["price"], 0.8),
    _r(1,  "freelance_dev", "curious", "comment",
       "does it handle partial invoices mid-project or just end-of-cycle? "
       "also privacy concern — giving it full gmail access feels risky.",
       ["privacy", "trust"], 0.3),
    _r(2,  "freelance_dev", "skeptical", "comment",
       "freshbooks already does time tracking, why would i pay $9 more? "
       "what's the real diff from bonsai?",
       ["competitor", "price"], -0.3),
    _r(3,  "studio_owner", "neutral", "comment",
       "interesting, though i already have my own system. the calendar parsing "
       "sounds brittle if you have non-billable personal events mixed in.",
       ["trust", "ux"], 0.1),
    _r(4,  "freelance_designer", "enthusiastic", "upvote",
       "", [], 0.5),
    _r(5,  "freelance_dev", "curious", "comment",
       "pricing is fine but i want to see how accurate the calendar parsing is "
       "before i trust it to generate a real invoice.",
       ["trust"], 0.2),
    _r(6,  "studio_owner", "skeptical", "comment",
       "the biggest issue is calendar noise. half my calendar is meetings that aren't billable. "
       "this needs to be very smart about categorization.",
       ["ux", "trust"], -0.1),
    _r(7,  "freelance_designer", "enthusiastic", "post",
       "this is the app that will actually get me to stop losing money. "
       "the 30-day free trial seals it.",
       [], 0.9),
    _r(8,  "freelance_dev", "indifferent", "ignore",
       ig_reason="i just use wave, it's free", ig_cat="price_or_effort"),
    _r(9,  "freelance_consultant", "enthusiastic", "comment",
       "i've tried freshbooks and bonsai. the key problem they all have is i still "
       "have to touch the invoice. if this truly auto-generates from calendar it's "
       "a different product.",
       ["competitor"], 0.7),
    _r(10, "freelance_consultant", "skeptical", "comment",
       "what happens when the llm extracts a meeting wrong and bills a client for "
       "a 3h meeting that was 30 min? liability issues.",
       ["trust", "accuracy"], -0.4),
    _r(11, "studio_owner", "neutral", "upvote", "", [], 0.3),
    _r(12, "freelance_designer", "curious", "comment",
       "does it support multiple currencies? i bill USD and EUR clients.",
       ["ux"], 0.2),
    _r(13, "freelance_dev", "skeptical", "ignore",
       ig_reason="i don't want any app touching my email", ig_cat="unclear_value"),
    _r(14, "freelance_consultant", "enthusiastic", "comment",
       "priced right, pain is real, just needs to nail the accuracy. "
       "will try the free trial.",
       [], 0.7),
    _r(15, "studio_owner", "neutral", "comment",
       "who's the target — solo freelancer or small studio? those are very different "
       "workflows and i'm not sure one product nails both.",
       ["icp_fit"], 0.0),
    _r(16, "freelance_designer", "enthusiastic", "upvote", "", [], 0.6),
    _r(17, "freelance_dev", "neutral", "comment",
       "oauth scopes concern me. what data exactly does it read from gmail?",
       ["privacy", "trust"], 0.1),
    _r(18, "freelance_consultant", "skeptical", "comment",
       "$9/mo on top of all my other subscriptions is a tough sell for slow months.",
       ["price", "cost"], -0.2),
    _r(19, "studio_owner", "indifferent", "ignore",
       ig_cat="not_my_problem"),
]


# ---------------------------------------------------------------------------
# onetap_investor — strong traction, moat + market size questions expected
# ---------------------------------------------------------------------------
ONETAP_INVESTOR = [
    _r(0,  "seed_vc", "skeptical", "comment",
       "what stops shopify from shipping one-tap checkout natively in the next 18 months "
       "and killing this? the platform risk is the whole story.",
       ["moat", "competition"], -0.2),
    _r(1,  "operator_angel", "enthusiastic", "post",
       "ex-stripe engineers, real traction, solving a problem i saw at scale. "
       "the nrr 112 is the signal. would take a meeting.",
       [], 0.8),
    _r(2,  "thesis_seed_vc", "curious", "comment",
       "the $750k pre-seed to $30k mrr math works only if cac stays low. "
       "what's current cac? the zero-paid-marketing claim needs explanation.",
       ["traction", "business_model"], 0.3),
    _r(3,  "multistage_partner", "skeptical", "comment",
       "150k store beachhead at $20-99/mo is $36-180M arr ceiling. "
       "that's not venture scale on its own. what's the land-and-expand story?",
       ["market_size", "valuation"], -0.3),
    _r(4,  "generalist_pre_seed", "neutral", "upvote", "", [], 0.4),
    _r(5,  "seed_vc", "curious", "comment",
       "payment tokenization is a regulated space. how are you handling pci compliance "
       "for stores that aren't on shopify?",
       ["team", "defensibility"], 0.1),
    _r(6,  "operator_angel", "enthusiastic", "comment",
       "the 5-minute install claim is the killer feature for smb adoption. "
       "what's the p50 time-to-first-checkout actually look like?",
       [], 0.6),
    _r(7,  "thesis_seed_vc", "skeptical", "ignore",
       ig_reason="payments is brutally competitive, stripe and shopify own distribution", ig_cat="crowded"),
    _r(8,  "multistage_partner", "neutral", "comment",
       "the 20% mom growth is real but 5 months isn't enough data. need to see "
       "retention curve at month 6+.",
       ["traction"], 0.0),
    _r(9,  "generalist_pre_seed", "enthusiastic", "comment",
       "stripe background is founder-market fit unlocked. "
       "checkout friction is a real unsolved problem for smb.",
       [], 0.7),
    _r(10, "seed_vc", "skeptical", "ignore",
       ig_reason="too early, nothing to underwrite", ig_cat="traction_thin"),
    _r(11, "operator_angel", "curious", "comment",
       "what's the churn rate? nrr 112 is great but absolute numbers at 400 stores "
       "make me want the logo list.",
       ["traction"], 0.4),
    _r(12, "thesis_seed_vc", "enthusiastic", "post",
       "payments infrastructure with real traction and zero paid cac is the profile "
       "i look for. sending to a partner.",
       [], 0.85),
    _r(13, "multistage_partner", "skeptical", "comment",
       "woocommerce integration complexity is real. i'd focus the raise on shopify only "
       "until you have 2k stores.",
       ["competition", "business_model"], -0.1),
    _r(14, "generalist_pre_seed", "neutral", "upvote", "", [], 0.3),
    _r(15, "seed_vc", "curious", "comment",
       "what's the defensibility once bolt or stripe checkout expands? "
       "the moat has to be data or switching cost, not the feature.",
       ["moat", "competition"], 0.1),
    _r(16, "operator_angel", "enthusiastic", "upvote", "", [], 0.7),
    _r(17, "thesis_seed_vc", "neutral", "comment",
       "$750k on just two hires and app-store growth is lean but achievable. "
       "how do you allocate across eng vs gtm?",
       ["business_model"], 0.2),
    _r(18, "multistage_partner", "skeptical", "ignore",
       ig_reason="market too small for our fund size", ig_cat="market_too_small"),
    _r(19, "generalist_pre_seed", "curious", "comment",
       "is this b2b saas or payments infra? the pricing model at $20-99/mo feels "
       "like saas but the product is payments.",
       ["business_model"], 0.2),
]


# ---------------------------------------------------------------------------
# clarity_launch — free notes tool; ChatGPT-wrapper + monetization objections
# ---------------------------------------------------------------------------
CLARITY_LAUNCH = [
    _r(0,  "product_hunt_maker", "enthusiastic", "post",
       "love the zero-friction angle. paste and go is the right ux. "
       "would upvote on ph if the output quality is actually good.",
       [], 0.75),
    _r(1,  "hn_skeptic", "aggressive", "comment",
       "this is a chatgpt prompt wrapper with a landing page. "
       "what stops me from doing this in 3 lines of python?",
       ["me_too", "unclear_value"], -0.7),
    _r(2,  "reddit_productivity", "curious", "comment",
       "does it work on code/technical docs or just prose? "
       "also — free forever is nice but what's the business model?",
       ["pricing", "unclear_value"], 0.2),
    _r(3,  "indie_hackers", "neutral", "comment",
       "the no-account angle is smart for initial distribution but you're "
       "leaving all retention on the table. how do returning users save their summaries?",
       ["differentiation", "pricing"], 0.0),
    _r(4,  "product_hunt_maker", "enthusiastic", "upvote", "", [], 0.6),
    _r(5,  "hn_skeptic", "skeptical", "comment",
       "notion ai already does this and you have the whole workspace context. "
       "why would i use a standalone tool?",
       ["me_too", "differentiation"], -0.4),
    _r(6,  "reddit_productivity", "enthusiastic", "comment",
       "honestly i just need this to work for meeting notes. "
       "if the output is clean i don't care about features.",
       [], 0.6),
    _r(7,  "indie_hackers", "curious", "comment",
       "interesting wedge but 'free forever' is a death sentence for saas. "
       "have you thought through the pricing path?",
       ["pricing"], 0.1),
    _r(8,  "hn_skeptic", "aggressive", "ignore",
       ig_reason="another ai wrapper launch, numb to these", ig_cat="launch_fatigue"),
    _r(9,  "product_hunt_maker", "enthusiastic", "comment",
       "the student audience is real — i used to spend 30 min cleaning notes "
       "after every lecture. this is the right problem.",
       [], 0.7),
    _r(10, "reddit_productivity", "neutral", "ignore",
       ig_reason="looks like every other ai summarizer", ig_cat="seen_before"),
    _r(11, "indie_hackers", "skeptical", "comment",
       "show hn will ask 'what model' and 'why not just use claude.ai'. "
       "you need a better answer than 'simpler ux'.",
       ["unclear_value", "me_too"], -0.3),
    _r(12, "product_hunt_maker", "neutral", "upvote", "", [], 0.3),
    _r(13, "hn_skeptic", "curious", "comment",
       "is the summary deterministic across runs? i'd want to know if i get the "
       "same output for the same input.",
       ["trust"], 0.1),
    _r(14, "reddit_productivity", "enthusiastic", "comment",
       "tried it — output is clean. would share this with my study group.",
       [], 0.8),
    _r(15, "indie_hackers", "neutral", "ignore",
       ig_reason="can't tell if it does anything different from summarize.tech", ig_cat="unclear_value"),
    _r(16, "product_hunt_maker", "skeptical", "comment",
       "the 'top-5 ph day' goal is ambitious for a free tool with no account. "
       "how do you drive votes without a user base?",
       ["differentiation"], -0.1),
    _r(17, "hn_skeptic", "aggressive", "comment",
       "gpt wrapper #437 of 2025. the show hn title had better be exceptionally good "
       "or this dies at 3 points.",
       ["hype_fatigue", "me_too"], -0.6),
    _r(18, "reddit_productivity", "curious", "comment",
       "does it handle voice memo transcripts or just text? "
       "that's the main use case for me.",
       ["ux"], 0.3),
    _r(19, "indie_hackers", "enthusiastic", "upvote", "", [], 0.5),
]


# ---------------------------------------------------------------------------
# weak_b2b_saas — deliberately vague, low-signal pitch
# ---------------------------------------------------------------------------
WEAK_B2B_SAAS = [
    _r(0,  "smb_ops", "skeptical", "comment",
       "what does this actually do? 'improve operations with ai' tells me nothing.",
       ["unclear_value"], -0.6),
    _r(1,  "enterprise_it", "indifferent", "ignore",
       ig_reason="too vague to evaluate", ig_cat="unclear_value"),
    _r(2,  "startup_founder", "skeptical", "comment",
       "every saas company says they use ml to make businesses efficient. "
       "what problem specifically?",
       ["unclear_value", "competitor"], -0.5),
    _r(3,  "smb_ops", "neutral", "ignore",
       ig_reason="not for me", ig_cat="not_my_problem"),
    _r(4,  "enterprise_it", "skeptical", "comment",
       "pricing tbd on an enterprise product means no one on my team can evaluate it.",
       ["price"], -0.4),
    _r(5,  "startup_founder", "aggressive", "comment",
       "the market is huge — all businesses need to be efficient. "
       "that's not a market thesis, that's a horoscope.",
       ["unclear_value"], -0.7),
    _r(6,  "smb_ops", "neutral", "upvote", "", [], 0.1),
    _r(7,  "enterprise_it", "indifferent", "ignore",
       ig_reason="what's the actual product", ig_cat="unclear_value"),
    _r(8,  "startup_founder", "skeptical", "ignore",
       ig_reason="seen a hundred ai efficiency platforms", ig_cat="seen_before"),
    _r(9,  "smb_ops", "skeptical", "comment",
       "better than competition because latest ai — that's what every vendor says. "
       "not a differentiator.",
       ["unclear_value", "competitor"], -0.5),
    _r(10, "enterprise_it", "neutral", "comment",
       "what integrations does this have? no stack mentioned, no use case, nothing.",
       ["unclear_value"], -0.3),
    _r(11, "startup_founder", "indifferent", "ignore",
       ig_cat="unclear_value"),
    _r(12, "smb_ops", "neutral", "ignore",
       ig_reason="too generic to know if relevant", ig_cat="not_my_problem"),
    _r(13, "enterprise_it", "skeptical", "comment",
       "enterprise and smb are completely different products. "
       "you can't nail both at once.",
       ["icp_fit"], -0.4),
    _r(14, "startup_founder", "neutral", "ignore",
       ig_cat="dont_care"),
    _r(15, "smb_ops", "skeptical", "comment",
       "what does success look like in 90 days for a customer?",
       ["unclear_value"], -0.2),
]


# ---------------------------------------------------------------------------
# strong_dev_tool — FixBot, clear niche dev tool
# ---------------------------------------------------------------------------
STRONG_DEV_TOOL = [
    _r(0,  "backend_engineer", "enthusiastic", "post",
       "this is exactly the workflow i need. sentry triage is the most annoying part "
       "of being on-call. if it can actually draft a pr from an error, i'm in.",
       [], 0.9),
    _r(1,  "engineering_lead", "curious", "comment",
       "how does it handle errors that span multiple services? "
       "microservices make cross-context reconstruction hard.",
       ["trust", "ux"], 0.4),
    _r(2,  "backend_engineer", "skeptical", "comment",
       "$49/seat/month is expensive for a small team. "
       "that's $500/yr for just one person — add team of 5 and it's real money.",
       ["price"], -0.2),
    _r(3,  "sre", "enthusiastic", "comment",
       "the 'cross-reference past errors' feature is the killer. we have the same "
       "class of bug reopened 3-4 times and nobody connects the dots.",
       [], 0.8),
    _r(4,  "engineering_lead", "skeptical", "comment",
       "giving a bot write access to our repo to auto-open prs is a hard no "
       "for most security-conscious teams. how's the access model?",
       ["trust", "security"], -0.4),
    _r(5,  "backend_engineer", "enthusiastic", "upvote", "", [], 0.7),
    _r(6,  "sre", "curious", "comment",
       "does it work with gitlab or just github? we're on gitlab.",
       ["ux"], 0.2),
    _r(7,  "engineering_lead", "neutral", "comment",
       "the roi calc at 1.5h saved per week is the right framing. "
       "that's how we sell tools to finance.",
       [], 0.5),
    _r(8,  "backend_engineer", "skeptical", "ignore",
       ig_reason="copilot already does this kind of thing", ig_cat="seen_before"),
    _r(9,  "sre", "enthusiastic", "post",
       "this solves a very specific pain that every on-call rotation has. "
       "the icp is tight and the product is scoped correctly.",
       [], 0.85),
    _r(10, "engineering_lead", "curious", "comment",
       "what's the false positive rate on the auto-generated fix? "
       "a bad pr is worse than no pr.",
       ["trust"], 0.1),
    _r(11, "backend_engineer", "enthusiastic", "comment",
       "i'd pay this out of my own pocket if my employer won't. "
       "the problem is that real.",
       [], 0.9),
    _r(12, "sre", "neutral", "upvote", "", [], 0.4),
    _r(13, "engineering_lead", "skeptical", "comment",
       "how does it handle languages other than python/js? "
       "our stack is go + rust.",
       ["ux"], -0.1),
    _r(14, "backend_engineer", "curious", "comment",
       "is the sentry context chunked or full events? sentry events can be enormous.",
       ["ux"], 0.2),
    _r(15, "sre", "enthusiastic", "upvote", "", [], 0.6),
    _r(16, "engineering_lead", "neutral", "comment",
       "the 60% claim on pattern errors needs proof. what dataset is that from?",
       ["trust"], 0.1),
    _r(17, "backend_engineer", "enthusiastic", "comment",
       "launched into my team slack. three people immediately asked for the trial link.",
       [], 0.95),
    _r(18, "sre", "skeptical", "ignore",
       ig_reason="we built something similar internally, unlikely to buy", ig_cat="seen_before"),
    _r(19, "engineering_lead", "curious", "upvote", "", [], 0.3),
]


# ---------------------------------------------------------------------------
# wrong_audience_b2c — RecallMate pitched to enterprise (audience mismatch)
# ---------------------------------------------------------------------------
WRONG_AUDIENCE_B2C = [
    _r(0,  "cto_enterprise", "skeptical", "comment",
       "$299/yr for kindle highlights is not an enterprise procurement conversation. "
       "our engineering docs don't live in kindle.",
       ["icp_fit", "price"], -0.6),
    _r(1,  "vp_engineering", "indifferent", "ignore",
       ig_reason="this is a consumer app, not a b2b tool", ig_cat="not_my_problem"),
    _r(2,  "cto_enterprise", "aggressive", "comment",
       "you're pitching a readwise clone to enterprise buyers. "
       "readwise is $7/mo b2c. this makes no sense.",
       ["competitor", "icp_fit"], -0.8),
    _r(3,  "vp_engineering", "skeptical", "comment",
       "kindle highlights and instapaper are personal tools. "
       "enterprise knowledge management is a different market entirely.",
       ["icp_fit"], -0.5),
    _r(4,  "cto_enterprise", "indifferent", "ignore",
       ig_cat="not_my_problem"),
    _r(5,  "vp_engineering", "skeptical", "comment",
       "the audience mismatch is the whole problem. "
       "individual engineers choosing their own tools is different from an enterprise purchase.",
       ["icp_fit"], -0.4),
    _r(6,  "cto_enterprise", "skeptical", "ignore",
       ig_reason="not a b2b problem as described", ig_cat="not_my_problem"),
    _r(7,  "vp_engineering", "neutral", "comment",
       "the problem statement is real for individuals but $299/seat is wrong "
       "for a consumer behavior app.",
       ["price", "icp_fit"], -0.3),
    _r(8,  "cto_enterprise", "skeptical", "comment",
       "anki is free. what's the marginal value over anki + readwise that "
       "justifies $299 enterprise procurement?",
       ["price", "competitor"], -0.5),
    _r(9,  "vp_engineering", "indifferent", "ignore",
       ig_reason="not what enterprise buyers are looking for", ig_cat="not_my_problem"),
    _r(10, "cto_enterprise", "neutral", "comment",
       "the spaced repetition idea for technical docs is actually interesting "
       "but the execution is b2c, not enterprise.",
       ["icp_fit"], 0.1),
    _r(11, "vp_engineering", "aggressive", "comment",
       "targeting ctOs with a kindle app is the most confused icp i've seen this year.",
       ["icp_fit"], -0.7),
    _r(12, "cto_enterprise", "indifferent", "ignore",
       ig_cat="not_my_problem"),
    _r(13, "vp_engineering", "neutral", "upvote", "", [], 0.1),
    _r(14, "cto_enterprise", "skeptical", "comment",
       "no procurement team will expense $299/yr per engineer for a reading app. "
       "this has to be a consumer play.",
       ["price", "icp_fit"], -0.5),
]


# ---------------------------------------------------------------------------
# Registry: map golden case id -> canned reactions
# ---------------------------------------------------------------------------
CANNED: dict[str, list] = {
    "tally_validate": TALLY_VALIDATE,
    "onetap_investor": ONETAP_INVESTOR,
    "clarity_launch": CLARITY_LAUNCH,
    "weak_b2b_saas": WEAK_B2B_SAAS,
    "strong_dev_tool": STRONG_DEV_TOOL,
    "wrong_audience_b2c": WRONG_AUDIENCE_B2C,
}
