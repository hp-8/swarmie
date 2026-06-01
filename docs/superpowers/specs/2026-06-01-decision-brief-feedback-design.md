# Decision Brief Reframe + Feedback Layers — Design / Contract

Date: 2026-06-01
Status: approved, in build

## Goal

Flip Swarmie's output from a vanity report card ("PMF 7.4") into an **actionable decision brief**, and add **two feedback layers** that double as calibration data. North star: a real product real founders trust. Ship this version without overbuilding.

## Scope (one version, three workstreams)

- **A — Backend reframe** (`backend/app/services/swarm/roast_reporter.py`)
- **B — Feedback infra** (new Vue components + `frontend/src/lib/analytics.js` + Supabase SQL)
- **C — Result.vue integration** (done by lead after A + B land)

Workstreams A and B touch disjoint files and run in parallel. C consumes both.

---

## A — Backend reframe contract

Extend `RoastReport` (additive only — all existing fields stay, frontend stays backward-compatible).

New top-level fields on the report dict:

```
verdict        : str   # one of: "ship_it" | "sharpen_positioning" | "wrong_audience" | "kill"
verdict_reason : str   # one blunt line, < 120 chars, why this verdict
next_action    : str   # the single most important move before writing more code, < 160 chars
confidence     : str   # "low" | "med" | "high"
confidence_reason : str  # one line, why (e.g. "only 14 agents spoke; sentiment split")
```

`top_objections[]` — each existing item (`category`, `count`, `example_quote`) gains:

```
real_test     : str   # exact question to ask 5 real users, < 160 chars
kill_criteria : str   # "if N/5 say X, this positioning is dead", < 160 chars
suggested_fix : str   # concrete messaging/positioning fix, < 160 chars
```

### How

- Keep all deterministic metrics exactly as-is (`pmf_score`, `sentiment_split`, `action_split`, `icp_fit`, `quoted_reactions`). The "no fabrication" rule stands for metrics.
- The single synth-tier LLM call (`_synthesize`) now also returns: `verdict`, `verdict_reason`, `next_action`, `confidence`, `confidence_reason`, and `objections_enriched: [{category, real_test, kill_criteria, suggested_fix}]`.
- Merge `objections_enriched` back into `top_objections` by matching `category`. If the LLM omits a category, fill the three new fields with `""`.
- `confidence` may be informed by a deterministic floor: if total speaking reactions < 15 → cap at "low"; if sentiment is highly split (pos and neg both > 30%) → cap at "med". LLM picks within that ceiling.
- Update the dataclass, the prompt (extend `_NARRATIVE_SYSTEM` + the JSON key instructions), and `_synthesize`'s return + merge logic.
- Update `_fallback_narrative` path so a failed synth still yields sane defaults: `verdict="sharpen_positioning"`, `verdict_reason` derived, `next_action` derived from top objection, `confidence="low"`, empty enrichment fields.
- Keep total output under control: one LLM call, `max_tokens` may rise to ~1800.

### Tests / verification (A)

- Add/extend a unit test that feeds synthetic `AgentReaction`s and asserts the new keys exist and have correct types, and that enrichment merges by category. Run existing backend tests; nothing red.

---

## B — Feedback infra contract

### Supabase tables (SQL migration file)

Write `backend/sql/feedback_tables.sql` (new dir ok; this is documentation/ops SQL, app uses anon client from frontend). Two tables, mirroring existing analytics style (`roast_runs`, `roast_reports`):

```sql
create table if not exists objection_feedback (
  id              bigint generated always as identity primary key,
  job_id          text not null,
  fingerprint_id  text,
  objection_category text not null,
  vote            smallint not null,        -- +1 or -1
  created_at      timestamptz not null default now(),
  unique (job_id, fingerprint_id, objection_category)
);

create table if not exists product_feedback (
  id              bigint generated always as identity primary key,
  job_id          text,
  fingerprint_id  text,
  helpful         boolean,
  comment         text,
  email           text,
  trigger         text,                     -- 'button' | 'popup'
  created_at      timestamptz not null default now()
);
```

Enable RLS with insert-for-anon policies, matching whatever the existing analytics tables use (check Supabase; if existing tables are open-insert, mirror that). Add upsert conflict target `(job_id, fingerprint_id, objection_category)` for objection votes so a user can change their vote.

### analytics.js — new exported functions (additive, same patterns as file)

```js
// vote: +1 | -1. Upsert so re-vote overwrites.
export async function trackObjectionFeedback(jobId, objectionCategory, vote) { ... }

// { helpful: bool, comment?: string, email?: string, trigger: 'button'|'popup' }
export async function trackProductFeedback(jobId, { helpful, comment, email, trigger }) { ... }
```

Reuse `getFingerprint()`, `if (!supabase) return` guard, `console.warn` on error — identical to existing functions. `objection_feedback` uses `.upsert(..., { onConflict: 'job_id,fingerprint_id,objection_category' })`.

### Component: `frontend/src/components/feedback/ObjectionVote.vue`

Inline 👍/👎 for one objection card.

- **Props:** `jobId: string`, `objectionCategory: string`
- **Behavior:** two small icon buttons, label "match your gut?". On click → call `trackObjectionFeedback(jobId, category, +1|-1)`, set local `voted` state, show a tiny "thanks" / highlight the chosen vote. Persist choice in `localStorage` key `swv:${jobId}:${category}` so it survives reload and disables re-spam (but allow switching vote).
- **Style:** match Hallmark tokens already in Result.vue (`--font-mono`, `--ink-3`, `--accent`, `--live`, `--warn`, `--radius-pill`). Tiny, unobtrusive, lives at the bottom of an objection card. No external deps.
- **Emits:** none required.

### Component: `frontend/src/components/feedback/FeedbackWidget.vue`

Product feedback: persistent corner button + auto-popup after dwell.

- **Props:** `jobId: string`
- **Two entry points, one panel:**
  1. **Persistent corner button** — fixed bottom-right pill "Feedback", always present, `z-index` above content but below the brain drawer (drawer uses `z-index: 80`; use `70`). Clicking opens the panel (`trigger: 'button'`).
  2. **Auto-popup** — appears once per job after **dwell ~15s OR scroll past 60% of page**, whichever first. Only if not already dismissed/submitted. `localStorage` key `swv:fb:${jobId}` guards against re-show. Opens the panel as a gentle card (`trigger: 'popup'`).
- **Panel (progressive):** prompt "Did this help you decide what to test next?" with two buttons 👍 / 👎. Tapping a choice expands an optional `<textarea>` ("what would make it more useful?") + optional email input + Send. On Send → `trackProductFeedback(jobId, { helpful, comment, email, trigger })`, then show "Thanks — this trains the swarm." and auto-close after ~1.5s. A 👍/👎 tap alone (without expanding) still records `helpful` immediately so we capture the signal even if they don't elaborate.
- **Non-blocking:** popup is a corner card/toast, NOT a full-screen modal. Dismissible (×). Dismiss sets the localStorage guard. Respect `prefers-reduced-motion` for entrance.
- **Style:** Hallmark tokens, consistent with `Result.vue` rail/cells. No new deps.

### Verification (B)

- Components mount without errors; with Supabase env absent, calls no-op (do not throw). Manually confirm localStorage guards. Lint/build clean (`npm run build` in `frontend`).

---

## C — Result.vue integration (lead, after A + B)

`frontend/src/views/swarm/Result.vue`. The report-tab `<main v-else-if="report">` block:

- **Hero (ROW 1) flips:** replace the giant PMF score as the headline focus with **verdict chip + `next_action`**. Keep `headline` as supporting subtext. PMF number demotes into the sentiment/supporting cell (smaller). Verdict chip color-coded: ship_it→`--live`, sharpen→`--accent-bright`, wrong_audience→`--warn`, kill→`--warn` (stronger). Show `confidence` as a small mono tag with `confidence_reason` on hover/title.
- **Objections (ROW 2):** each objection row/card now renders `real_test`, `kill_criteria`, `suggested_fix` (copyable interview question), plus mounts `<ObjectionVote :job-id="jobId" :objection-category="obj.category" />` at the card foot. Guard with `v-if` so old reports lacking the fields still render.
- **Language shift:** "PMF score" / "prediction" → "signal" / "hypothesis to test" in eyebrows and the foot strip where natural. Keep AiDisclosure.
- **Mount `<FeedbackWidget :job-id="jobId" />`** once at page root (alongside footer), report tab only.
- Backward compatibility: every new field guarded; a report without `verdict`/enrichment still renders the old way.

## Non-goals (this version)

- Live grounding / real-comment citations (next version; objection cards may later gain `real_signal[]`).
- Backend changes for feedback (frontend writes straight to Supabase, matching current analytics).
- PDF template changes (leave as-is this pass).
