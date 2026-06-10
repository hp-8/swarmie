<template>
  <div class="dbp-panel">
    <!-- Eyebrow -->
    <span class="dbp-eyebrow">sample output</span>

    <!-- Verdict row -->
    <div class="dbp-verdict-block">
      <div class="dbp-verdict-chip">sharpen</div>
      <div class="dbp-verdict-meta">
        <span class="dbp-conf">confidence · med</span>
        <span class="dbp-signal">signal 6.4<span class="dbp-signal-denom">/10</span></span>
      </div>
    </div>

    <!-- Do this next -->
    <div class="dbp-next-block">
      <span class="dbp-next-label">do this next</span>
      <p class="dbp-next-action">Interview 5 AEs on price before building the integrations.</p>
    </div>

    <div class="dbp-rule"></div>

    <!-- Objection block -->
    <div class="dbp-objection-block">
      <div class="dbp-obj-head-row">
        <span class="dbp-obj-cat">PRICE</span>
        <span class="dbp-obj-count">14x</span>
      </div>

      <!-- Ask 5 users row -->
      <div class="dbp-obj-ask-row">
        <span class="dbp-obj-tag">ask 5 users</span>
        <span class="dbp-obj-ask-text">At what monthly price would you stop evaluating this tool entirely?</span>
      </div>

      <!-- Kill signal row -->
      <p class="dbp-obj-kill">
        <span class="dbp-obj-tag is-warn">kill signal</span>
        More than 3 of 5 AEs say the price exceeds their discretionary budget.
      </p>

      <!-- Fix row -->
      <p class="dbp-obj-fix">
        <span class="dbp-obj-tag is-accent">fix</span>
        Lead with ROI framing and add a usage-based entry tier before the enterprise gate.
      </p>
    </div>

    <div class="dbp-rule"></div>

    <!-- Silence block -->
    <div class="dbp-silence-block">
      <span class="dbp-silence-eyebrow">why 38% scrolled past</span>
      <div class="dbp-silence-row">
        <span class="dbp-silence-label">couldn't tell what it does</span>
        <p class="dbp-silence-imp">Rewrite the headline to name the outcome, not the mechanism.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
// No props required. Self-contained static presentational component.
// Optional: accept a title override for A/B testing page sections.
defineProps({
  nextAction: {
    type: String,
    default: null,
  },
})
</script>

<style scoped>
/* DecisionBriefPreview — static product visual for the marketing homepage.
 * Mirrors Result.vue visual language: verdict chip, objection cards, silence block.
 * Tokens only. No raw oklch/hex. No gradient text. No glassmorphism.
 * No side-stripe borders. No em dashes.
 * Responsive: 320px min width, single column.
 */

.dbp-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 560px;
  box-sizing: border-box;
}

/* Eyebrow */
.dbp-eyebrow {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-4);
  line-height: 1;
}

/* Verdict block */
.dbp-verdict-block {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
  row-gap: var(--space-2);
}

.dbp-verdict-chip {
  font-family: var(--font-display);
  font-style: normal;
  font-weight: 600;
  font-variation-settings: 'opsz' 144, 'wght' 600;
  font-size: clamp(28px, 6vw, 44px);
  line-height: 0.95;
  letter-spacing: -0.02em;
  text-transform: uppercase;
  color: var(--accent-bright);
  text-shadow: 0 0 40px var(--accent-bright);
}

.dbp-verdict-meta {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.dbp-conf {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-3);
}

.dbp-signal {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--ink-3);
}

.dbp-signal-denom {
  opacity: 0.55;
}

/* Do this next */
.dbp-next-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.dbp-next-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-3);
}

.dbp-next-action {
  font-family: var(--font-display);
  font-style: normal;
  font-weight: 500;
  font-variation-settings: 'opsz' 72, 'wght' 500;
  font-size: clamp(var(--text-base), 3vw, var(--text-md));
  line-height: 1.25;
  color: var(--ink);
  margin: 0;
}

/* Divider */
.dbp-rule {
  height: 1px;
  background: var(--rule);
  border: 0;
  flex-shrink: 0;
}

/* Objection block */
.dbp-objection-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.dbp-obj-head-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-3);
}

.dbp-obj-cat {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink);
}

.dbp-obj-count {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--ink-3);
}

/* Ask 5 users row -- full bordered sub-row, no side-stripe */
.dbp-obj-ask-row {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  background: var(--paper-3);
  border: 1px solid var(--rule);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  flex-wrap: wrap;
  row-gap: var(--space-1);
}

.dbp-obj-ask-text {
  flex: 1;
  font-size: var(--text-sm);
  color: var(--ink);
  line-height: 1.4;
  min-width: 0;
}

/* Shared obj-tag */
.dbp-obj-tag {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-3);
  padding: 1px 5px;
  border: 1px solid var(--rule);
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}

.dbp-obj-tag.is-warn {
  color: var(--warn);
  border-color: color-mix(in oklch, var(--warn) 35%, transparent);
  background: var(--warn-soft);
}

.dbp-obj-tag.is-accent {
  color: var(--accent-bright);
  border-color: color-mix(in oklch, var(--accent) 35%, transparent);
  background: var(--accent-soft);
}

/* Kill signal line */
.dbp-obj-kill {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
  color: var(--ink-2);
  line-height: 1.5;
  flex-wrap: wrap;
  row-gap: var(--space-1);
}

/* Fix line */
.dbp-obj-fix {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
  color: var(--ink-2);
  line-height: 1.5;
  flex-wrap: wrap;
  row-gap: var(--space-1);
}

/* Silence block */
.dbp-silence-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.dbp-silence-eyebrow {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-3);
}

.dbp-silence-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dbp-silence-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-2);
}

.dbp-silence-imp {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.5;
  color: var(--ink);
}

/* Responsive adjustments */
@media (max-width: 360px) {
  .dbp-panel {
    padding: var(--space-4);
    gap: var(--space-3);
  }

  .dbp-obj-ask-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .dbp-obj-kill,
  .dbp-obj-fix {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
