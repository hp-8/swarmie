# Launch Swarm — Design (synthetic-first)

**Date:** 2026-06-01
**Status:** Approved (forks settled); building
**Topic:** Launch Swarm — stress-test a launch by simulating how startup communities are likely to react. Synthetic-first; real-signal grounding is a deferred separate layer.

---

## Positioning

Not "predict your launch." **Surface the objections, questions, confusion points, risks, and discussion themes likely to emerge during launch** across Product Hunt / Hacker News / Reddit / Indie Hackers / X — then a clear verdict (**Go · Sharpen · Hold**), a response playbook, and recommended next actions. Decision stress-testing, not roleplay. Aligned with Swarmie's core philosophy.

## Scope

- **In:** a third swarm (`launch`) built on the existing subclass-per-swarm pipeline, exactly like `investor`. Synthetic archetypes drawn from community-behavior patterns. New additive `launch_brief` report field. Picker + Result rendering.
- **Out (deferred):** the realism/signal layer — scrapling, source adapters, ingest pipeline, pgvector, RAG conditioning, side-by-side real-vs-synthetic. That becomes a later layer to improve accuracy/calibration. No new deps.

## Components (mirror Investor)

All reuse the pipeline (cost routing, SSE, cost ceiling, agent chat, storage) untouched.

- **`LaunchPitchParser`** (subclass of `PitchParser`) — `icp_segments` = **community archetypes** (e.g. "PH maker hunting launches", "HN Show-HN skeptic", "subreddit lurker", "Indie Hackers founder", "X reply-guy"), not customer segments. `founder_ask` defaults to a launch framing.
- **`LaunchArchetypeGenerator`** (subclass of `ArchetypeGenerator`) — archetypes from real community behavior patterns across PH/HN/Reddit/IH/X. `segment` = the community/persona. `objection_bias` = launch concerns: `unclear_value`, `me_too`, `pricing`, `show_hn_rigor`, `hype_fatigue`, `trust`, `timing`. Distribution realistic (skeptics, lurkers, enthusiasts, indifferent).
- **`LaunchSwarmRunner`** (subclass of `SwarmRunner`) — reaction system prompt = roleplay one member of an online community reacting to a **launch post**; voice per community. Ignore-reason categories = why a launch gets scrolled past (`unclear_value`, `seen_before`, `not_my_community`, `dont_care`, `launch_fatigue`, `wrong_timing`).
- **`LaunchReporter`** (subclass of `RoastReporter`) — verdict vocab **go · sharpen · hold**. Deterministic metrics reused (sentiment, action split, per-community icp_fit, silence). Produces the additive `launch_brief`.

## `launch_brief` (additive report field)

Added to `RoastReport` as optional `launch_brief: dict | None` (null on non-launch runs), same pattern as `deck_diagnosis`:

```
launch_brief:
  questions:    [str]                          # likely questions communities will ask
  confusion:    [str]                          # what reads as unclear / will be misread
  risks:        [str]                          # launch risks (timing, framing, defensibility)
  themes:       [str]                          # discussion themes likely to dominate the thread
  playbook:     [{ trigger: str, response: str }]   # prepared response per likely objection
  next_actions: [str]                          # concrete moves before going live
```

Top objections + per-community fit ride the existing `top_objections` / `icp_fit` fields (relabeled per-swarm in the UI, as Investor already does). `launch_brief` carries the buckets that don't map to objections.

Verdict chip mapping: `go → is-ship` (live/green), `sharpen → is-sharpen` (accent), `hold → is-wrong` (warn).

## Registry + API

- Add `launch` `SwarmSpec` bundling the four classes; `agent_noun = "commenter"`, label "Launch".
- `swarm_type=launch` already threads through (registry-driven). No API changes beyond registering.

## Frontend

- `PitchInput.vue` — enable Launch in the picker (drop the `enabled:false`/"soon"); add launch per-swarm copy (title, sub, placeholder, checklist: problem / audience / channel / differentiation / timing).
- `Result.vue` — when `report.launch_brief` present, render launch sections (questions · confusion · risks · themes · playbook · next actions) alongside the verdict-led report + per-community fit. Reuse tokens/cells. Verdict labels go/sharpen/hold.
- `api/roast.js` `create` already takes `swarmType` — pass `'launch'`. Analytics `swarm_type` already recorded.

## Testing

- Registry resolves `launch` → Launch* classes.
- `LaunchReporter` parses/validates `launch_brief`; bad JSON → graceful fallback (empty brief, never raises).
- Verdict clamped to {go, sharpen, hold}.
- Frontend build clean; launch layout renders when `launch_brief` present, falls back otherwise.

## Deferred (the signal layer — separate spec later)

Source adapters (free API else scrapling), offline ingest + tagging + hosted embeddings, Supabase pgvector corpus, live targeted search, RAG-conditioned archetypes, side-by-side real-vs-synthetic. Improves accuracy/calibration; not required for v1 decision value.
