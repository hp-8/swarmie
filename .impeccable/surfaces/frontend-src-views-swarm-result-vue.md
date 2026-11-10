---
version: 1
slug: "frontend-src-views-swarm-result-vue"
primary_target: "frontend/src/views/swarm/Result.vue"
related_targets: ["frontend/src/styles/tokens.css"]
---

# Surface brief: Result (decision memo)

Scope: Result view (validate, investor, launch layouts) plus the app-wide theme it establishes. Mode: Read (the founder must understand a decision and act on it). Related: PitchInput (submission), Watching (deliberation), Home and Roasts adopt the same world later.

Audience: pre-launch founders making a real build/positioning decision. Job: understand the recommendation, the hidden risks, and the one next step; share a finding. Proof: the swarm evidence as exhibits. Constraint: every number real; disclose synthetic reviewers.

## Direction contract
THESIS: The result is the memo a partner writes before the investment committee: recommendation first, numbered findings, evidence as exhibits. It refuses the dashboard of score tiles and tabs.
OWN-WORLD: White bond ground, near-black ink, slate secondary, a single risk red used only on flags. Serif for the recommendation and summaries, precise grotesk for findings, labels and figures. Hairline rules, numbered findings with margin flags, tabular figures, exhibit tables. No glow, no cards-as-decoration.
STORY: Founder reads the recommendation and why, sees what's working, takes in the hidden risks with their cheap tests, scans objections, and leaves with this week's step; evidence is there when doubted.
FIRST VIEWPORT: Memo header (To, Re, Panel, Confidence) across the top; recommendation as a large serif line with the one-line reason beneath; next step set as the memo's action line; right margin column holds the risk flags and share/PDF actions.
FORM: Investment committee memo, my top-ranked grounded candidate (1 of 7), chosen as IMPECCABLE'S PICK. seed:a18e5fcf706654a3
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

Signature interaction: each finding is addressable (deep link copies a link to that finding). Motion: findings settle in once, top to bottom, on load; nothing loops.
