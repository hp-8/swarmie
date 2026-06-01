# Investor Deck Intelligence — Design

**Date:** 2026-06-01
**Status:** Approved forks; pending full-spec review
**Topic:** PDF deck upload → text extraction → pitch-intelligence diagnosis, as an in-pipeline feature of the existing investor swarm.

---

## Goal

Let a founder **drop a PDF pitch deck** into the investor swarm instead of pasting text. The app reads the deck's text layer per page, then produces an **investor-lens diagnosis** — a slide-by-slide scorecard, a red-flag index, strong/weak zones, a funding-readiness %, and a skeptical-investor simulation — with **every finding cited to its original slide/page number**. The existing investor swarm runs alongside it as supporting signal ("what the room would ask").

## Locked decisions (from brainstorming)

1. **In-pipeline feature** on the existing free investor swarm. No auth, no paywall, no separate product tier.
2. **PDF only** for v1. PPTX deferred (needs LibreOffice headless — out of scope).
3. **Text-layer extraction only** (PyMuPDF) for v1 — **no vision model, no new provider, no extra tokens-per-page.** All LLM work uses the existing `deep`/`synth` tiers. Image-only / scanned PDFs (no extractable text) are rejected with a "paste the text instead" fallback. *Why not vision:* the pitch-intelligence rubric is mostly text (headline clarity, market math, traction credibility, ask) — the text layer covers ~80% of the diagnosis at zero cost/latency. Vision only adds design-quality scoring + chart/table-only numbers, a marginal lift for a heavy dependency. Deferred to a fast-follow.
4. **Diagnosis-led report**: pitch-intelligence diagnosis is the spine; swarm archetype reactions appear as a supporting "the room" section.
5. **Page provenance everywhere**: every slide read, score, red flag, and zone cites its deck page number.
6. The `pitch-intelligence` skill is **saved globally** (reconstructed clean) AND its EVALUATE rubric is **ported into the backend** as the diagnosis prompt.

## Non-goals (YAGNI)

- No new financial-field schema on `ParsedPitch` (no cap-table/dilution math engine). The rubric scores ask/financials/traction qualitatively via slide scores.
- **No vision/OCR in v1** — text layer only. Selective vision is a fast-follow.
- No PPTX (needs LibreOffice).
- No upload→preview→edit-then-run step (a good fast-follow; deferred).
- No persistence of the uploaded file.
- No local compute / Ollama — everything uses the existing hosted LLM tiers.

---

## Architecture & data flow

```
POST /api/roast  (multipart: swarm_type=investor + file=deck.pdf)
  │
  ├─ stage: parsing
  │    deck_loader: PDF bytes → per-page text [{page, text}]  (cap ~25 pages, PyMuPDF)
  │    DeckExtractor: ONE text LLM call (deep tier)
  │        → slide reads: [{page, slide_type, headline, body, signals}]
  │        → consolidated ParsedPitch (one_liner/problem/solution/… so the swarm can run)
  │
  ├─ stage: generating_archetypes   (InvestorArchetypeGenerator — unchanged)
  ├─ stage: running_swarm           (InvestorSwarmRunner — unchanged; reacts to consolidated narrative)
  │
  ├─ stage: evaluating              (NEW)
  │    DeckEvaluator: slide reads → pitch-intelligence EVALUATE (one LLM call, synth tier, investor lens)
  │        → DeckDiagnosis (scorecard, red flags, zones, readiness%, investor sim, next move)
  │
  └─ stage: reporting
       InvestorReporter merges: DeckDiagnosis (spine) + swarm reactions (supporting)
       → RoastReport (with additive `deck_diagnosis` field)
```

No vision model: the deck path adds just **two text LLM calls** (extract + evaluate) on top of the existing swarm — no per-page model fan-out, no new provider.

Pasted-text investor runs are **unchanged** — no file → no `deck_loader`/`DeckExtractor`/`DeckEvaluator`, today's `InvestorPitchParser` path runs, `deck_diagnosis` is null.

---

## Components (each: purpose · interface · deps)

### 1. `deck_loader.py`
- **Purpose:** PDF bytes → ordered per-page text.
- **Interface:** `load_pdf(data: bytes, max_pages=25) -> list[PageText]` where `PageText = {page: int, text: str}`.
- **Deps:** PyMuPDF (`pymupdf`) — pure wheel, no system deps. `page.get_text()` per page.
- **Errors:** encrypted/corrupt PDF → `DeckLoadError`. Truncates beyond `max_pages` (records truncation). **No extractable text on any page** (image-only/scanned) → `DeckLoadError("no text layer")` → UI tells the user to paste text (vision fast-follow handles this case later).

### 2. `DeckExtractor`
- **Purpose:** turn per-page text into structured slide reads + a consolidated `ParsedPitch` (so the swarm has narrative to react to).
- **Interface:** `extract(pages: list[PageText], tracker) -> DeckRead` where `DeckRead = { slides: list[SlideRead], pitch: ParsedPitch }`.
- **Internals:** ONE `deep`-tier text LLM call. Input = page texts with their page numbers. Output = each slide classified into one of the 13 canonical types + headline/body/signals + its `page`, plus a consolidated `ParsedPitch`. (No per-page fan-out — one consolidated call over the whole deck.)
- **Deps:** deck_loader output, existing `deep` LLM, `ParsedPitch`.

### 3. `DeckEvaluator`
- **Purpose:** run the pitch-intelligence EVALUATE rubric over the slide reads.
- **Interface:** `evaluate(slides: list[SlideRead], stage: str, tracker) -> DeckDiagnosis`.
- **Internals:** one synth-tier LLM call using the ported rubric. Investor lens, stage-calibrated, no generic advice. Output validated/clamped (scores 0–10, readiness 0–100).
- **Deps:** the rubric prompt (shared with the global skill), slide reads.

### 4. `DeckDiagnosis` (data model)
```
DeckDiagnosis:
  stage: str                       # idea/pre-seed/seed/series-a/growth
  readiness_pct: float             # 0..100
  overall_score: int               # 0..130
  slides: list[{ slide_type, page, score, verdict, top_issue }]
  red_flags: list[{ severity, slide_type, page, text }]   # severity: CRITICAL|HIGH|MEDIUM|LOW
  strong_zones: list[str]
  weak_zones: list[str]
  investor_simulation: str         # 3-4 sentence skeptical-investor voice
  next_move: str                   # single action before next investor call
```
Added to `RoastReport` as an **optional additive field** `deck_diagnosis` (null on non-deck runs). Existing report rendering unaffected.

### 5. API
- `POST /api/roast` accepts `multipart/form-data` (file) in addition to JSON. When `swarm_type=investor` + file present → deck path. Size cap (~25 MB), PDF mime check.
- Job records `source: 'text' | 'deck'`.

### 6. Frontend
- Investor mode in `PitchInput.vue`: a **dropzone** (drag/drop PDF) alongside the paste box ("paste text, or drop a PDF deck"). Shows page count on load.
- `Result.vue`: when `deck_diagnosis` present → **diagnosis-led layout** — readiness % + verdict hero, slide scorecard (with page tags), red-flag index, strong/weak zones, investor simulation, next move. Swarm sections (reactions/"the room") render below as supporting. Reuses existing tokens/cells.
- PDF export includes the diagnosis + page citations.

### 7. Privacy
- **File never persisted.** Extract text → discard PDF bytes from memory after the run. In-process job store already GCs in 1h.
- **Analytics redaction:** for deck runs, `roast_runs` stores the extracted one-liner/problem summary only, never raw financials/cap-table; `source='deck'` flag set.

### 8. The skill (two homes)
- **Global:** reconstruct the pasted (corrupted) content into a clean `~/.claude/skills/pitch-intelligence/SKILL.md` — all 3 modes (GENERATE/EVALUATE/ITERATE), 13 canonical slides, scorecards, cross-mode rules, stage calibration, output standards.
- **Backend rubric:** the EVALUATE rubric text is ported into `DeckEvaluator`'s prompt. Single source of truth kept readable; the backend copy is the runtime one.

---

## Errors

- Unreadable/encrypted PDF → clear UI error, suggest paste.
- Image-only/scanned PDF (no text layer) → "couldn't read the deck — paste the text instead" (vision fast-follow covers this later).
- Extract/evaluate LLM returns bad JSON → graceful deterministic fallback (partial diagnosis, never a crash).
- Primary LLM down → existing Gemini fallback.
- Cost ceiling → existing watchdog cancels (extract + evaluate tokens count toward it).

## Testing

- `deck_loader`: sample text-layer PDF → expected page count + per-page text; encrypted PDF → error; image-only PDF → "no text layer" error.
- `DeckExtractor`: mocked LLM → slide reads carry correct `page`; consolidation yields populated `ParsedPitch`.
- `DeckEvaluator`: mocked LLM → `DeckDiagnosis` parsed/clamped; bad JSON → graceful fallback.
- API: multipart accept; oversized/non-PDF rejected; `source='deck'` recorded.
- Frontend: dropzone accepts PDF / rejects others; diagnosis-led layout renders when `deck_diagnosis` present; falls back to text layout otherwise.

## Fast-follows (explicitly deferred)

- **Selective vision** — fire a VLM only on image-only/no-text pages (scanned decks, chart/cap-table slides) for design-quality scoring + chart-only numbers.
- Upload → preview/edit extracted fields → run (correction loop).
- PPTX support (LibreOffice).
- Side-by-side deck-version delta (the skill's ITERATE mode).
