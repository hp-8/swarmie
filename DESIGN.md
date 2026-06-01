# Swarmie — DESIGN.md

The full token system lives in `frontend/src/styles/tokens.css` (OKLCH, locked). This file summarizes it so design work stays on-system. **Never inline raw colors — reference tokens by name.**

## Genre
Atmospheric — late-night AI-tool. Deep-noir paper, warm coral heat, phosphor-green / red / blue as semantic signals. Tactile, not flat.

## Color (OKLCH, see tokens.css)
- **Paper:** `--paper` deep noir `oklch(13% .018 270)` → `--paper-2/3/4` step up.
- **Ink:** `--ink` near-white → `--ink-2/3/4` dimmer.
- **Accent (coral, the heat):** `--accent` / `--accent-bright` / `--accent-soft`. Primary CTA + emphasis. Keep it scarce — it's heat, not wallpaper.
- **Semantic:** `--live` (phosphor green = positive/ship), `--warn` (red = negative/kill), `--info` (blue). Each has a `-soft` tint.
- **Strategy:** Committed-dark. The noir surface IS the brand; coral carries voice in small, deliberate doses.

## Typography
- **Display:** Fraunces italic (`--font-display`, `.h-display`) — committed identity, preserved.
- **Body:** Inter (`--font-body`).
- **Mono:** JetBrains Mono (`--font-mono`, `.h-eyebrow`) — labels/eyebrows/meta only, not body.
- **Scale:** `--text-xs (11) … --text-display (112)`, ≥1.25 steps. Use `clamp()` for fluid headings across web/tablet/mobile.

## Space / radius / motion
- 4pt scale `--space-1..11`. Radii `--radius-sm..pill`.
- Eases: `--ease-out` (default), `--ease-in`, `--ease-in-out`. Durations `--dur-fast/base/slow`. Animate transform/opacity only. `prefers-reduced-motion` already collapses motion globally in tokens.css.

## Responsive (web / tablet / mobile — all three required)
- Breakpoints in use: ≥1024 web · 768–1024 tablet/iPad · <768 mobile (test 320/375/414/768).
- `html, body { overflow-x: clip }` already set. Image-bearing grid tracks use `minmax(0,1fr)`. No two-line buttons/links. Display headers `overflow-wrap: anywhere; min-width:0`.

## Atmosphere primitives (added for the elevated marketing surface)
- Ambient swarm canvas (decorative, perf-light, reduced-motion → static) as hero backdrop.
- Subtle grain + radial coral glow tokens layered over `--paper`, low chroma, never competing with text.

## Hard bans (impeccable + brand)
No gradient text · no glassmorphism-by-default · no side-stripe accent borders · no hero-metric template · no identical card-grid triples · no em dashes · no invented metrics (every number on the page must be real).
