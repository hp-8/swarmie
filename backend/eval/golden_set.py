"""
Golden set for the Swarmie eval harness.

Each case defines:
  - id: unique slug
  - swarm_type: "validate" | "investor" | "launch"
  - pitch_text: raw pitch (drawn from test-pitches.local.txt + hand-crafted extremes)
  - expected_verdicts: set of acceptable verdict strings
  - required_objection_themes: list of keyword/substring lists — at least one keyword
      per inner list must appear (case-insensitive) in any top_objection category
      or example_quote across the report.
  - pmf_direction: "positive" (>= 5.0), "neutral" (2.0–7.9), or "negative" (< 5.0)
  - confidence_ceiling: maximum acceptable confidence
  - notes: human annotation
  - hidden_risk_keywords (optional): planted non-obvious risk; any keyword must
      appear in the report's founder-facing prose (eval.checks.check_hidden_risk).
      Never use words that merely echo the pitch.
  - full_only (optional): no canned reactions; skipped in synth mode

Keep assertions tolerant — these are LLM outputs.
"""

from __future__ import annotations
from typing import Any

GOLDEN_CASES: list[dict[str, Any]] = [
    # ------------------------------------------------------------------
    # Case 1: Tally — strong freelance-invoicing pitch (from test-pitches.local.txt)
    # Expectation: decent PMF signal, positioning might need sharpening
    # ------------------------------------------------------------------
    {
        "id": "tally_validate",
        "swarm_type": "validate",
        "pitch_text": (
            "PROBLEM: Solo freelancers and small studios lose real money every month "
            "simply because invoicing is an afterthought. After a long day of client work, "
            "the last thing a designer or developer wants to do is open a spreadsheet, dig "
            "through their calendar to reconstruct billable hours, and manually write out "
            "an invoice. So it slips. Work that was delivered in the first week of the month "
            "doesn't get billed until the third — or gets forgotten entirely. Studies of "
            "freelance income consistently show a meaningful chunk of revenue is never "
            "collected, not because clients refuse to pay, but because the invoice was never "
            "sent. The pain is quiet, recurring, and directly tied to cash flow.\n\n"
            "PRODUCT: Tally is an invoicing app that works backwards from the work you already "
            "did. It connects to your Google Calendar and email, detects client meetings, "
            "project blocks, and delivery threads, and automatically drafts a clean, itemized "
            "invoice at the end of each billing cycle. You review it in one screen — adjust "
            "line items, rates, and hours if needed — and send it with a single tap. Payment "
            "reminders go out on autopilot. The founder never has to remember to invoice again; "
            "the system remembers for them, grounded in their real activity rather than manual "
            "logging.\n\n"
            "AUDIENCE: Independent freelance designers, developers, and consultants billing "
            "3–15 clients a month, plus 2–4 person studios without a dedicated ops person. "
            "Specifically the segment that currently lives in a mix of Google Calendar, Gmail, "
            "and an ad-hoc spreadsheet, and who bill hourly or per-project.\n\n"
            "PRICING: $9/month flat, or $90/year. 30-day free trial, no card required.\n\n"
            "COMPETITORS: FreshBooks, QuickBooks Self-Employed, Bonsai. How we're different: "
            "every other tool still expects you to *enter* the work. Tally generates the invoice "
            "from what you actually did."
        ),
        "expected_verdicts": {"ship_it", "sharpen_positioning"},
        "required_objection_themes": [
            # at least one of these keywords must surface as an objection theme
            ["price", "cost", "subscription", "$9"],
            ["trust", "privacy", "calendar", "email", "access", "permission"],
            ["competitor", "freshbooks", "bonsai", "quickbooks", "alternative"],
        ],
        "pmf_direction": "positive",  # expect pmf_score >= 5.0
        "confidence_ceiling": "high",  # we have a rich pitch — no hard ceiling
        "notes": "Strong pain, clear ICP, $9/mo price sensitivity and privacy are expected concerns.",
    },

    # ------------------------------------------------------------------
    # Case 2: OneTap — strong investor pitch (from test-pitches.local.txt)
    # Expectation: good fundability signal; traction is real
    # ------------------------------------------------------------------
    {
        "id": "onetap_investor",
        "swarm_type": "investor",
        "pitch_text": (
            "PROBLEM: Small and mid-size e-commerce stores leak an enormous amount of revenue "
            "at the final step of the funnel: checkout. Industry cart-abandonment hovers around "
            "70%, and a large share of that is friction — too many form fields, forced account "
            "creation, slow multi-page flows, and clumsy mobile payment.\n\n"
            "SOLUTION: OneTap is a drop-in checkout widget that any store can install in under "
            "five minutes with a single script tag. It collapses the entire checkout into one tap "
            "for returning shoppers using tokenized payment + address details, and a single short "
            "form for new ones. Platform-agnostic — works on Shopify, WooCommerce, custom React "
            "storefronts, and headless setups. Handles Apple Pay, Google Pay, and cards.\n\n"
            "MARKET: ~2M+ active Shopify stores alone. Targeting ~150k stores doing $10k–$500k/yr "
            "GMV at $20–$99/mo.\n\n"
            "TRACTION: $8k MRR, ~20% MoM growth for 5 months. 400 paying stores, $1.2M monthly "
            "GMV through widget. NRR 112%. Zero paid marketing.\n\n"
            "TEAM: Two ex-Stripe payments engineers, 4 years building checkout and fraud infra.\n\n"
            "RAISE: $750k pre-seed to reach $30k MRR and 1,500 stores in 12 months."
        ),
        "expected_verdicts": {"fundable", "sharpen_story"},
        "required_objection_themes": [
            ["moat", "defensib", "compet", "shop pay", "stripe"],
            ["market", "tam", "size", "scale", "venture"],
        ],
        "pmf_direction": "positive",  # strong traction should read positively
        "confidence_ceiling": "high",
        "notes": "Strong traction story. Moat and Shopify lock-in will be scrutinized.",
    },

    # ------------------------------------------------------------------
    # Case 3: Clarity — launch pitch (from test-pitches.local.txt)
    # Expectation: "sharpen" or "go"; ChatGPT wrapper objection is near-certain
    # ------------------------------------------------------------------
    {
        "id": "clarity_launch",
        "swarm_type": "launch",
        "pitch_text": (
            "PRODUCT: Clarity is a free web tool that turns messy, half-formed notes into a "
            "clean, structured one-page summary. You paste in a wall of meeting notes, voice-memo "
            "transcripts, scattered bullet points, or research scraps, and it returns a single "
            "organized page. No setup, no account, no learning curve — paste, generate, copy.\n\n"
            "AUDIENCE: Students drowning in lecture and reading notes, indie hackers and solo "
            "operators capturing scattered ideas.\n\n"
            "CHANNEL: Launching on Product Hunt (aiming for a top-5 day) and Hacker News "
            "(Show HN), with follow-on posts in r/productivity, r/SideProject, and student "
            "subreddits.\n\n"
            "DIFFERENTIATION: Faster and radically simpler than Notion AI or a raw ChatGPT "
            "prompt — no document to set up, no prompt to engineer, no account wall.\n\n"
            "TIMING: Launching next week. Debating whether to gate anything behind signup, "
            "whether 'free forever' undercuts a future paid tier."
        ),
        "expected_verdicts": {"go", "sharpen", "hold"},
        "required_objection_themes": [
            ["wrapper", "chatgpt", "gpt", "ai", "openai", "llm", "model"],
            ["free", "monetiz", "business model", "paid", "sustain"],
            ["similar", "competitor", "notion", "alternative", "me-too", "seen"],
        ],
        "pmf_direction": "neutral",  # mixed — free tool with clarity gap
        "confidence_ceiling": "high",
        "notes": "ChatGPT-wrapper objection expected from HN skeptics. Monetization gap expected.",
    },

    # ------------------------------------------------------------------
    # Case 4: WeakPitch — deliberately vague / weak idea
    # Expectation: kill or sharpen_positioning; low PMF
    # ------------------------------------------------------------------
    {
        "id": "weak_b2b_saas",
        "swarm_type": "validate",
        "pitch_text": (
            "We are building an AI platform for businesses to improve their operations. "
            "Our product uses machine learning to help companies be more efficient. "
            "We target enterprise companies and SMBs. Pricing TBD. "
            "The market is huge — all businesses need to be more efficient. "
            "We are better than the competition because we use the latest AI."
        ),
        "expected_verdicts": {"kill", "sharpen_positioning", "wrong_audience"},
        "required_objection_themes": [
            ["vague", "unclear", "generic", "broad", "specific", "what does"],
            ["competitor", "market", "differ", "unique", "ai", "machine learning"],
        ],
        "pmf_direction": "negative",  # expect pmf_score < 5.0
        "confidence_ceiling": "med",   # vague pitch = less signal
        "notes": "Deliberately weak pitch: no specific problem, no ICP, buzzword-heavy.",
    },

    # ------------------------------------------------------------------
    # Case 5: StrongNiche — deliberate strong pitch with clear wedge
    # Expectation: ship_it or sharpen_positioning; high PMF
    # ------------------------------------------------------------------
    {
        "id": "strong_dev_tool",
        "swarm_type": "validate",
        "pitch_text": (
            "PROBLEM: Backend engineers on small teams spend 2–4 hours per week manually "
            "triaging production errors in Sentry. They open tickets, cross-reference logs, "
            "reproduce locally, and write half the fix — only to find someone else already "
            "patched a similar bug last sprint. Error triage is repetitive, context-heavy, "
            "and deeply frustrating.\n\n"
            "PRODUCT: FixBot is a Sentry integration that, when a new error fires, "
            "automatically (a) pulls relevant code context from your repo, (b) cross-references "
            "similar past errors from your own history, (c) drafts a fix with a one-click PR. "
            "It handles the 60% of errors that follow repeatable patterns — freeing engineers "
            "for the 40% that actually need human judgment.\n\n"
            "AUDIENCE: Backend engineers and engineering leads at B2B SaaS companies with "
            "2–15 engineers. Teams that use Sentry + GitHub and can't afford a dedicated SRE.\n\n"
            "PRICING: $49/seat/month. Free 14-day trial, no credit card. "
            "ROI calculator shows payback at 1.5 hours saved per week.\n\n"
            "COMPETITORS: Sentry's own AI suggestions (shallow), GitHub Copilot (no Sentry "
            "context), manual triage. We're the first to combine repo history + error history "
            "into a single fix draft."
        ),
        "expected_verdicts": {"ship_it", "sharpen_positioning"},
        "required_objection_themes": [
            ["price", "cost", "$49", "seat", "budget"],
            ["trust", "code", "access", "repo", "security", "sensitive"],
        ],
        "pmf_direction": "positive",
        "confidence_ceiling": "high",
        "notes": "Strong niche pitch. Price sensitivity and repo-access trust are predictable objections.",
    },

    # ------------------------------------------------------------------
    # Case 6: WrongAudience — pitch that speaks to the wrong segment
    # Expectation: wrong_audience or sharpen_positioning
    # ------------------------------------------------------------------
    {
        "id": "wrong_audience_b2c",
        "swarm_type": "validate",
        "pitch_text": (
            "PROBLEM: People struggle to remember what they read. After finishing a book or "
            "article, they can rarely recall the key ideas two weeks later.\n\n"
            "PRODUCT: RecallMate is a $299/year app that uses spaced repetition + AI to "
            "turn your Kindle highlights and web clips into daily quiz sessions. It integrates "
            "with Readwise, Kindle, and Instapaper.\n\n"
            "AUDIENCE: We are targeting enterprise CTOs and VPs of Engineering who want their "
            "teams to retain technical knowledge from internal documentation and engineering "
            "blog posts.\n\n"
            "PRICING: $299/year per seat. B2B bulk pricing available.\n\n"
            "COMPETITORS: Readwise, Anki, Roam Research."
        ),
        "expected_verdicts": {"wrong_audience", "sharpen_positioning", "kill"},
        "required_objection_themes": [
            ["audience", "icp", "segment", "who", "target", "enterprise", "cto"],
            ["price", "$299", "expensive", "cost"],
            ["readwise", "anki", "competitor", "alternative", "exist"],
        ],
        "pmf_direction": "negative",  # audience mismatch kills PMF
        "confidence_ceiling": "high",
        "notes": "Consumer memory product pitched to enterprise decision-makers — clear mismatch.",
    },
    # ==================================================================
    # Value traps (full mode only). Each tests a failure that makes the
    # product useless: flattery, needless harshness, or missing the real,
    # non-obvious problem a good advisor would spot.
    # ==================================================================
    {
        "id": "trap_flattery_hype",
        "swarm_type": "validate",
        "full_only": True,
        "pitch_text": (
            "PROBLEM: Pet owners love their pets and want to share them.\n\n"
            "PRODUCT: PawPal is a revolutionary AI-powered social network exclusively for pets. "
            "Every pet gets an AI personality that posts on its behalf. This is the future of "
            "social media and will disrupt Instagram.\n\n"
            "AUDIENCE: Everyone who owns a pet (over 1 billion pets worldwide).\n\n"
            "PRICING: $49/month premium for advanced AI personalities.\n\n"
            "COMPETITORS: None. Nobody is doing AI for pets."
        ),
        "expected_verdicts": {"kill", "wrong_audience", "sharpen_positioning"},
        "required_objection_themes": [
            ["price", "$49", "expensive", "cost"],
            ["instagram", "existing", "already", "competitor", "alternative"],
        ],
        "pmf_direction": "negative",
        "confidence_ceiling": "high",
        "hidden_risk_keywords": ["too broad", "no specific", "who exactly",
                                 "niche", "narrow"],
        "notes": "Hype words, 'no competitors', 'everyone' as ICP, consumer price far above "
                 "norms. Must NOT get ship_it. A good report still names what could work "
                 "(e.g. a narrow segment like pet influencer accounts).",
    },
    {
        "id": "trap_harshness_boring_b2b",
        "swarm_type": "validate",
        "full_only": True,
        "pitch_text": (
            "PROBLEM: Independent dental clinics lose 10-15% of booked hours to no-shows. "
            "Front-desk staff call patients manually the day before, which takes ~1 hour a day.\n\n"
            "PRODUCT: RemindDent sends SMS + WhatsApp confirmations with one-tap reschedule, "
            "syncs with Dentrix and Open Dental, and backfills cancelled slots from a waitlist.\n\n"
            "AUDIENCE: Independent dental clinics with 1-4 chairs in the US.\n\n"
            "TRACTION: 14 paying clinics after a 3-month pilot; no-shows down from 12% to 5% on "
            "average; 0 churn so far. Two clinics referred others.\n\n"
            "PRICING: $149/month per clinic.\n\n"
            "COMPETITORS: Weave, Lighthouse 360, built-in PMS reminders. We are cheaper than Weave "
            "and include waitlist backfill, which the built-in reminders lack."
        ),
        "expected_verdicts": {"ship_it", "sharpen_positioning"},
        "required_objection_themes": [
            ["weave", "competitor", "existing", "built-in", "already"],
        ],
        "pmf_direction": "positive",
        "confidence_ceiling": "high",
        "notes": "Unsexy but real: measured outcome, paying customers, referrals. Must NOT get "
                 "kill. Swarm skeptics will say 'Weave exists'; a calibrated report weighs the "
                 "traction evidence above that.",
    },
    {
        "id": "hidden_buyer_not_user",
        "swarm_type": "validate",
        "full_only": True,
        "pitch_text": (
            "PROBLEM: K-12 teachers spend 5+ hours a week grading short-answer homework.\n\n"
            "PRODUCT: GradeLoop is an AI grader that reads handwritten worksheets from a phone "
            "photo, suggests a grade and feedback, and lets the teacher approve in one tap.\n\n"
            "AUDIENCE: Public school teachers in grades 6-12 in the US.\n\n"
            "PRICING: $12/month per teacher.\n\n"
            "COMPETITORS: Gradescope, manual grading."
        ),
        "expected_verdicts": {"sharpen_positioning", "wrong_audience", "ship_it"},
        "required_objection_themes": [
            ["accura", "trust", "wrong", "mistake", "error"],
        ],
        "pmf_direction": "neutral",
        "confidence_ceiling": "high",
        "hidden_risk_keywords": ["district", "school budget", "procurement", "administrator",
                                 "who pays", "buyer", "out of pocket", "own pocket", "ferpa",
                                 "student data"],
        "notes": "Teachers love it but rarely pay personally; districts buy, with long "
                 "procurement and student-data (FERPA) review. A strong report spots buyer != user.",
    },
    {
        "id": "hidden_low_frequency",
        "swarm_type": "validate",
        "full_only": True,
        "pitch_text": (
            "PROBLEM: Freelancers in the US dread filing their annual taxes and miss deductions.\n\n"
            "PRODUCT: TaxBuddy connects to your bank, auto-categorizes deductible expenses, and "
            "prepares a filing-ready Schedule C package for your accountant or for self-filing.\n\n"
            "AUDIENCE: US freelancers and 1099 contractors.\n\n"
            "PRICING: $19/month subscription.\n\n"
            "COMPETITORS: TurboTax Self-Employed, Keeper, QuickBooks Self-Employed."
        ),
        "expected_verdicts": {"sharpen_positioning", "ship_it", "wrong_audience"},
        "required_objection_themes": [
            ["turbotax", "keeper", "quickbooks", "competitor", "existing"],
        ],
        "pmf_direction": "neutral",
        "confidence_ceiling": "high",
        "hidden_risk_keywords": ["once a year", "seasonal", "tax season", "churn",
                                 "frequency", "rest of the year", "monthly pricing"],
        "notes": "Core pain happens once a year but pricing is monthly: expect churn after "
                 "April unless there's year-round value (quarterly estimates). Non-obvious.",
    },
    {
        "id": "hidden_regulatory",
        "swarm_type": "validate",
        "full_only": True,
        "pitch_text": (
            "PROBLEM: Therapy is expensive and waitlists are months long.\n\n"
            "PRODUCT: MindMate is an AI therapist chatbot that provides CBT sessions 24/7, "
            "detects mood from messages, and can recommend when to adjust medication.\n\n"
            "AUDIENCE: Adults with anxiety or depression who can't afford therapy.\n\n"
            "PRICING: $15/month.\n\n"
            "COMPETITORS: Woebot, Wysa, BetterHelp."
        ),
        "expected_verdicts": {"sharpen_positioning", "kill", "wrong_audience"},
        "required_objection_themes": [
            ["trust", "safe", "human", "ai", "replace"],
        ],
        "pmf_direction": "neutral",
        "confidence_ceiling": "high",
        "hidden_risk_keywords": ["regulat", "fda", "liabil", "license", "medical advice",
                                 "hipaa", "crisis", "suicid", "clinical"],
        "notes": "Recommending medication changes is practicing medicine: regulatory and "
                 "liability exposure, plus crisis/safety handling. Should be flagged clearly, "
                 "with a path (drop med advice, position as wellness, clinician-in-loop).",
    },
    {
        "id": "hidden_marketplace_cold_start",
        "swarm_type": "validate",
        "full_only": True,
        "pitch_text": (
            "PROBLEM: Homeowners can't find reliable local handymen for small jobs, and "
            "handymen waste time on low-quality leads.\n\n"
            "PRODUCT: FixNear is a two-sided marketplace matching homeowners with vetted "
            "handymen for jobs under $500, with instant booking and escrowed payment.\n\n"
            "AUDIENCE: Homeowners and independent handymen, launching nationwide in the US.\n\n"
            "PRICING: 15% take rate on each job.\n\n"
            "COMPETITORS: Thumbtack, TaskRabbit, Angi, Nextdoor."
        ),
        "expected_verdicts": {"sharpen_positioning", "wrong_audience", "kill"},
        "required_objection_themes": [
            ["thumbtack", "taskrabbit", "angi", "competitor", "existing"],
        ],
        "pmf_direction": "neutral",
        "confidence_ceiling": "high",
        "hidden_risk_keywords": ["cold start", "chicken", "liquidity", "supply", "both sides",
                                 "one city", "single city", "local density",
                                 "disintermediat", "off-platform", "leakage"],
        "notes": "Nationwide launch of a local two-sided marketplace = no density anywhere; "
                 "plus repeat jobs leak off-platform. Good report: start in one city/one job type.",
    },
]


def get_case(case_id: str) -> dict | None:
    """Retrieve a golden case by id."""
    return next((c for c in GOLDEN_CASES if c["id"] == case_id), None)


def all_case_ids() -> list[str]:
    return [c["id"] for c in GOLDEN_CASES]
