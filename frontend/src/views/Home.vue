<template>
  <div class="page home">
    <SiteNav />

    <main>
      <section class="hero">
        <div class="hero-copy">
          <h1 class="hero-title">Find the problem you can't see yet.</h1>
          <p class="hero-lede">
            A panel of synthetic reviewers reads your pitch the way Reddit, Hacker News and
            Product Hunt would. You get a decision memo: what's working, the risks you missed,
            and what to test this week.
          </p>

          <form class="quick" @submit.prevent="startDraft">
            <label for="quick-pitch" class="quick-label">Your pitch</label>
            <textarea
              id="quick-pitch"
              v-model="draft"
              class="quick-input"
              rows="4"
              data-clarity-mask="true"
              placeholder="Problem, product, audience, pricing, competitors. A few honest sentences is enough."
            ></textarea>
            <div class="quick-row">
              <button type="submit" class="btn">Convene the panel</button>
              <span class="quick-meta">Free, no signup · about a minute</span>
            </div>
          </form>
          <p class="disclose">
            Reviewers are AI agents, not real users.
            <AiDisclosure variant="text" label="How this works" />
          </p>
        </div>

        <figure id="memo" class="sample" aria-label="Sample decision memo">
          <figcaption class="sample-cap">Sample memo. Synthetic panel, illustrative pitch.</figcaption>
          <div class="sample-sheet">
            <dl class="s-fields">
              <div><dt>To</dt><dd>Founder, GradeLoop</dd></div>
              <div><dt>Re</dt><dd>AI grading for handwritten worksheets</dd></div>
              <div><dt>Panel</dt><dd>100 reviewers · 61 spoke</dd></div>
            </dl>
            <p class="s-rec">Sharpen the positioning.</p>
            <p class="s-reason">Real pull from teachers, but the panel never heard from the people who pay.</p>
            <div class="s-finding">
              <p class="s-title"><span class="s-flag">Risk</span>The user is not the buyer.</p>
              <p class="s-line"><strong>Easy to miss because</strong> every positive reaction came from teachers; administrators were 4 of 100 reviewers.</p>
            </div>
            <p class="s-action"><strong>This week.</strong> Rewrite the first line for the buyer (admins, not teachers), name the budget it comes from, and re-run.</p>
          </div>
        </figure>
      </section>

      <section class="note" aria-labelledby="note-title">
        <h2 id="note-title" class="note-title">A note on the reviewers</h2>
        <p class="note-body">
          They are AI agents, not real users. They are sometimes wrong and often too agreeable, and
          they cannot tell you your market size. Use the memo to find the questions worth asking real
          people, before those conversations and your code cost you, not to declare product-market fit.
        </p>
      </section>

      <section class="how" aria-labelledby="how-title">
        <h2 id="how-title" class="sec-title">How a review works</h2>
        <ol class="steps">
          <li>
            <span class="step-num">1</span>
            <h3 class="step-title">Submit the pitch</h3>
            <p class="step-copy">Paste deck text, landing copy or a few sentences. The panel reads the problem, audience, price and competitors.</p>
          </li>
          <li>
            <span class="step-num">2</span>
            <h3 class="step-title">The panel reacts</h3>
            <p class="step-copy">Reviewers in the style of community archetypes, from skeptics to lurkers, comment, upvote or scroll past, and say why.</p>
          </li>
          <li>
            <span class="step-num">3</span>
            <h3 class="step-title">Read the memo</h3>
            <p class="step-copy">A recommendation with its confidence, the hidden risks, each objection with the question to ask five real users, and a path forward.</p>
          </li>
        </ol>
      </section>

      <section class="archive-strip" aria-labelledby="archive-title">
        <div class="strip-head">
          <h2 id="archive-title" class="sec-title">From the memo archive</h2>
          <p class="strip-lede">Famous pitches, as they were told, through the same panel. Unedited output.</p>
          <router-link to="/roasts" class="strip-all">See all {{ archive.length }} memos</router-link>
        </div>
        <div class="strip-row">
          <MemoArchiveCard v-for="r in archive.slice(0, 4)" :key="r.slug" :memo="r" variant="compact" />
        </div>
      </section>

      <section id="pricing" class="pricing" aria-labelledby="pricing-title">
        <div class="pricing-head">
          <h2 id="pricing-title" class="pricing-title">Pay per review.<br />Never per month.</h2>
          <p class="pricing-note">
            Free reviews stay free. When you need a bigger panel, an investor read of your deck or a
            launch rehearsal, buy a pack and use it when it matters.
          </p>
        </div>

        <div class="rate-card">
          <div class="rate-intro">
            <p class="intro-title">Every pack</p>
            <p class="intro-copy">One credit runs one full review, at any panel size. Buy once, no subscription.</p>
          </div>
          <div
            v-for="(plan, i) in PLANS"
            :key="plan.key"
            class="rate"
            :class="{ 'rate-hero': plan.hero }"
            :style="{ gridColumn: i + 2 }"
          >
            <p class="rate-name">{{ plan.name }}</p>
            <p class="rate-qty" :class="{ 'is-word': isNaN(plan.qty) }">{{ plan.qty }}</p>
            <p class="rate-unit">{{ plan.unit }}</p>
            <p class="rate-price">
              {{ plan.price }}
              <span v-if="plan.perReview" class="rate-per">{{ plan.perReview }} per review</span>
            </p>
            <p v-if="plan.regular" class="rate-launch">Launch price for the first {{ LAUNCH_BUYERS }} buyers. {{ plan.regular }} after that, save {{ plan.save }}.</p>
            <span class="rate-spacer" aria-hidden="true"></span>
            <router-link v-if="plan.cta" :to="plan.cta" class="rate-cta">Start a free review</router-link>
            <button v-else-if="BILLING_ENABLED" type="button" class="rate-cta rate-buy" :disabled="buying === plan.key" @click="buy(plan.key)">
              {{ buying === plan.key ? 'Opening checkout…' : `Buy ${plan.qty} reviews` }}
            </button>
            <span v-else class="rate-cta is-soon">Coming soon</span>
          </div>

          <table class="rate-table">
            <caption class="sr-only">What each plan includes</caption>
            <thead>
              <tr><th scope="col">Included</th><th v-for="plan in PLANS" :key="plan.key" scope="col">{{ plan.short }}</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in RATE_ROWS" :key="row.label">
                <th scope="row">{{ row.label }}</th>
                <td v-for="(v, i) in row.cells" :key="i" :class="{ 'is-hero': PLANS[i].hero }">
                  <svg v-if="v === true" class="tick" viewBox="0 0 16 16" aria-label="Included" role="img"><path d="M3 8.5l3 3 7-7" /></svg>
                  <span v-else-if="v === false" class="dash" aria-label="Not included">&ndash;</span>
                  <span v-else>{{ v }}</span>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-if="BILLING_ENABLED" class="rate-legal">By purchasing you confirm you're 18+ and agree to the <router-link to="/terms">Terms</router-link>.</p>
        </div>
      </section>

      <section class="founder" aria-labelledby="founder-title">
        <div class="founder-main">
          <h2 id="founder-title" class="sec-title">Built by Harsh Patadia</h2>
          <p class="founder-bio">
            I build for founders. Swarmie is how I think about early-stage validation: fast, honest,
            focused on the objection you actually need to hear. If you want a human in the loop, to ship
            the MVP, sharpen the pitch or prep the raise, that's the day job.
          </p>
          <a href="https://harshpatadia.com" target="_blank" rel="noopener" class="btn btn-ghost">Work with me</a>
        </div>
        <ul class="founder-links" aria-label="Elsewhere">
          <li><a href="https://github.com/hp-8" target="_blank" rel="noopener">github.com/hp-8</a></li>
          <li><a href="https://x.com/harshpatadia_" target="_blank" rel="noopener">x.com/harshpatadia_</a></li>
          <li><a href="https://www.linkedin.com/in/harsh-patadia" target="_blank" rel="noopener">linkedin.com/in/harsh-patadia</a></li>
          <li><a href="https://harshpatadia.com" target="_blank" rel="noopener">harshpatadia.com</a></li>
        </ul>
      </section>

      <section class="closing">
        <h2 class="closing-title">What would a panel find in your pitch?</h2>
        <router-link to="/new" class="btn">Submit a pitch</router-link>
      </section>
    </main>

    <SiteFooter />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AiDisclosure from '../components/AiDisclosure.vue'
import SiteNav from '../components/marketing/SiteNav.vue'
import SiteFooter from '../components/marketing/SiteFooter.vue'
import MemoArchiveCard from '../components/marketing/MemoArchiveCard.vue'
import { BILLING_ENABLED, session } from '../lib/account'
import { buyPack } from '../api/billing'
import data from '../data/famousRoasts.json'

const router = useRouter()
const draft = ref('')
const buying = ref('')

// Signed in: straight to Stripe. Signed out: sign in first, then continue to checkout.
async function buy(pack) {
  if (!session.value) return router.push({ path: '/signin', query: { pack } })
  buying.value = pack
  try {
    await buyPack(pack)
  } catch {
    buying.value = ''
    router.push({ path: '/account', query: { buy: pack } })
  }
}
const archive = data.roasts

// Plans shown on the rate card. Pack prices are launch prices: `regular` is the
// price they move to after launch (state it only if you will actually charge it).
// Launch prices hold for this many paying buyers; enforce at checkout (count purchases).
const LAUNCH_BUYERS = 100

const PLANS = [
  { key: 'free', name: 'Free', short: 'Free', qty: 'Unlimited', unit: 'small reviews', price: '$0', cta: '/new' },
  { key: 'try', name: 'Try pack', short: 'Try', qty: '5', unit: 'full reviews', price: '$5', perReview: '$1.00' },
  { key: 'starter', name: 'Starter pack', short: 'Starter', qty: '20', unit: 'full reviews', price: '$15', perReview: '$0.75', regular: '$25', save: '40%' },
  { key: 'sprint', name: 'Sprint pack', short: 'Sprint', qty: '100', unit: 'full reviews, for a validation sprint', price: '$49', perReview: '$0.49', regular: '$82', save: '40%', hero: true },
]

// What each plan includes, one cell per plan above. true = included, false = not.
const RATE_ROWS = [
  { label: 'Panel size', cells: ['20 reviewers', 'Up to 500', 'Up to 500', 'Up to 500'] },
  { label: 'Full decision memo', cells: [true, true, true, true] },
  { label: 'Validate reviews', cells: [true, true, true, true] },
  { label: 'Investor reviews and deck upload', cells: [false, true, true, true] },
  { label: 'Launch reviews', cells: [false, true, true, true] },
  { label: 'PDF export and share card', cells: [false, true, true, true] },
]

// Hand the hero draft to the submission form (which owns consent + validation).
function startDraft() {
  try { sessionStorage.setItem('swarmie:draft', draft.value) } catch { /* storage blocked */ }
  router.push('/new')
}
</script>

<style scoped>
.page { min-height: 100vh; color: var(--ink); background: var(--paper); }


.btn {
  display: inline-flex; align-items: center; justify-content: center;
  font: inherit; font-weight: 700; font-size: var(--text-base);
  padding: 13px 20px; border: 1px solid var(--ink); border-radius: var(--radius-sm);
  background: var(--ink); color: var(--paper); cursor: pointer; white-space: nowrap;
  transition: background var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out);
}
.btn:hover { background: var(--ink-2); }
.btn:active { transform: translateY(1px); }
.btn-ghost { background: var(--paper); color: var(--ink); border-color: var(--rule-2); }
.btn-ghost:hover { background: var(--paper-3); border-color: var(--ink-4); }

/* Hero: offer + working form beside a real-shaped memo */
.hero {
  max-width: 1200px; margin: 0 auto;
  padding: var(--space-9) var(--space-6) var(--space-8);
  display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr); gap: var(--space-8);
  align-items: start;
}
.hero-title {
  margin: 0;
  font-family: var(--font-display); font-weight: 600;
  font-size: clamp(42px, 5.4vw, 76px); line-height: 1.02; letter-spacing: -0.025em;
  text-wrap: balance;
}
.hero-lede { margin: var(--space-5) 0 0; font-size: var(--text-md); line-height: 1.6; color: var(--ink-2); max-width: 54ch; }

.quick { margin-top: var(--space-6); display: grid; gap: var(--space-2); max-width: 560px; }
.quick-label { font-size: var(--text-sm); font-weight: 700; }
.quick-input {
  width: 100%; resize: vertical; padding: var(--space-3) var(--space-4);
  font: inherit; line-height: 1.55; color: var(--ink);
  background: var(--paper); border: 1px solid var(--rule-2); border-radius: var(--radius-sm);
}
.quick-input:hover { border-color: var(--ink-4); }
.quick-input:focus { outline: none; border-color: var(--ink); box-shadow: 0 0 0 3px oklch(50% 0.11 250 / 0.15); }
.quick-row { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3) var(--space-4); margin-top: var(--space-1); }
.quick-meta { font-size: var(--text-sm); color: var(--ink-3); }
.disclose { margin: var(--space-4) 0 0; font-size: var(--text-sm); color: var(--ink-3); }

.sample { margin: 0; }
.sample-cap { font-size: var(--text-sm); color: var(--ink-3); margin-bottom: var(--space-2); }
.sample-sheet {
  background: var(--paper);
  border: 1px solid var(--rule);
  box-shadow: 0 30px 60px -40px oklch(20% 0.02 250 / 0.45), 0 2px 6px -4px oklch(20% 0.02 250 / 0.2);
  padding: var(--space-6) var(--space-6) var(--space-5);
  transform: rotate(0.6deg);
  animation: lay 700ms var(--ease-out) both;
}
@keyframes lay { from { opacity: 0; transform: rotate(2deg) translateY(14px); } to { opacity: 1; transform: rotate(0.6deg); } }
.s-fields { margin: 0; display: grid; gap: var(--space-1); padding-bottom: var(--space-4); border-bottom: 2px solid var(--ink); }
.s-fields > div { display: grid; grid-template-columns: 64px minmax(0, 1fr); gap: var(--space-3); font-size: var(--text-sm); }
.s-fields dt { color: var(--ink-3); }
.s-fields dd { margin: 0; font-weight: 600; }
.s-rec { margin: var(--space-5) 0 0; font-family: var(--font-display); font-weight: 600; font-size: clamp(28px, 2.8vw, 38px); line-height: 1.08; letter-spacing: -0.015em; }
.s-reason { margin: var(--space-2) 0 0; font-family: var(--font-display); font-size: var(--text-md); line-height: 1.5; color: var(--ink-2); }
.s-finding { margin-top: var(--space-5); padding-top: var(--space-4); border-top: 1px solid var(--rule); }
.s-title { margin: 0; font-weight: 600; }
.s-flag { margin-right: var(--space-2); font-size: var(--text-xs); font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink); background: var(--warn-hl); padding: 0.1em 0.45em; border-radius: 3px; vertical-align: 0.1em; }
.s-line { margin: var(--space-1) 0 0; font-size: var(--text-sm); line-height: 1.55; color: var(--ink-2); }
.s-action { margin: var(--space-5) 0 0; padding: var(--space-3) var(--space-4); background: var(--paper-2); border-top: 1px solid var(--rule-2); font-size: var(--text-sm); line-height: 1.55; }

/* Sections */
.note, .how, .founder, .closing { max-width: 1200px; margin: 0 auto; padding: var(--space-8) var(--space-6); border-top: 1px solid var(--rule); }
.note { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr); gap: var(--space-6); }
.note-title, .sec-title { margin: 0; font-size: var(--text-xl); font-weight: 700; letter-spacing: -0.015em; }
.note-body { margin: 0; font-family: var(--font-display); font-size: var(--text-lg); line-height: 1.6; color: var(--ink-2); max-width: 64ch; }

.steps { list-style: none; margin: var(--space-6) 0 0; padding: 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 2px solid var(--ink); }
.steps li { padding: var(--space-5) var(--space-5) 0 0; }
.steps li + li { padding-left: var(--space-5); border-left: 1px solid var(--rule); }
.step-num { font-weight: 700; color: var(--ink-3); font-variant-numeric: tabular-nums; }
.step-title { margin: var(--space-2) 0 0; font-size: var(--text-md); font-weight: 700; }
.step-copy { margin: var(--space-2) 0 0; line-height: 1.6; color: var(--ink-2); max-width: 40ch; }


.founder { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: var(--space-7); }
.founder-bio { margin: var(--space-4) 0 var(--space-5); line-height: 1.65; color: var(--ink-2); max-width: 62ch; }
.founder-links { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-3); align-content: start; font-size: var(--text-sm); }
.founder-links a { color: var(--ink-2); text-decoration: underline; text-underline-offset: 3px; }
.founder-links a:hover { color: var(--ink); }

.closing { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: var(--space-5); padding-block: var(--space-9); }
.closing-title { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: clamp(30px, 3.6vw, 48px); line-height: 1.1; letter-spacing: -0.02em; max-width: 20ch; }


@media (max-width: 1024px) {
  .hero { grid-template-columns: minmax(0, 1fr); gap: var(--space-7); padding-top: var(--space-8); }
  .sample { max-width: 620px; }
}
@media (max-width: 767px) {
  .hero { padding: var(--space-7) var(--space-4) var(--space-7); }
  .sample-sheet { transform: none; animation: none; padding: var(--space-5) var(--space-4); }
  .note, .how, .founder, .closing { padding-inline: var(--space-4); }
  .note, .founder { grid-template-columns: minmax(0, 1fr); gap: var(--space-4); }
  .steps { grid-template-columns: minmax(0, 1fr); }
  .steps li, .steps li + li { padding: var(--space-4) 0; border-left: 0; border-bottom: 1px solid var(--rule); }
}
/* Archive strip */
.archive-strip { max-width: 1320px; margin: 0 auto; padding: var(--space-8) var(--space-6); border-top: 1px solid var(--rule); }
.strip-head { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: baseline; gap: var(--space-5); }
.strip-lede { margin: 0; color: var(--ink-3); font-size: var(--text-sm); }
.strip-all { font-size: var(--text-sm); font-weight: 600; text-decoration: underline; text-underline-offset: 3px; white-space: nowrap; }
.strip-row { margin-top: var(--space-6); display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-4); }

/* Pricing: a rate card */
.pricing { max-width: 1320px; margin: 0 auto; padding: var(--space-9) var(--space-6); border-top: 1px solid var(--rule); }
.pricing-head { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: var(--space-8); align-items: end; }
.pricing-title { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: clamp(36px, 4.4vw, 60px); line-height: 1.02; letter-spacing: -0.025em; }
.pricing-note { margin: 0; color: var(--ink-2); line-height: 1.65; max-width: 56ch; }

.rate-card {
  margin-top: var(--space-7);
  display: grid;
  grid-template-columns: minmax(170px, 1fr) repeat(4, minmax(0, 1fr));
  border: 1px solid var(--rule-2);
  background: var(--paper);
  box-shadow: 0 30px 60px -44px oklch(20% 0.02 250 / 0.5);
}
.rate { grid-row: 1; padding: var(--space-6) var(--space-5); display: flex; flex-direction: column; border-left: 1px solid var(--rule); }
.rate-hero { background: var(--ink); color: var(--paper); border-left-color: var(--ink); }
.rate-name { margin: 0; font-size: var(--text-sm); font-weight: 700; }
.rate-qty { overflow-wrap: anywhere; margin: var(--space-4) 0 0; font-family: var(--font-display); font-weight: 600; font-size: clamp(44px, 4.4vw, 64px); line-height: 0.95; letter-spacing: -0.03em; font-variant-numeric: lining-nums; }
/* Words ("Unlimited") at number size overflow the column; keep the same line box so units still align. */
.rate-qty.is-word { font-size: clamp(30px, 2.6vw, 40px); line-height: calc(clamp(44px, 4.4vw, 64px) * 0.95); }
.rate-unit { margin: var(--space-2) 0 0; font-size: var(--text-sm); color: var(--ink-3); min-height: 2.6em; }
.rate-hero .rate-unit { color: oklch(100% 0 0 / 0.68); }
.rate-price { margin: var(--space-5) 0 0; font-size: var(--text-lg); font-weight: 700; font-variant-numeric: tabular-nums; }
.rate-per { display: block; margin-top: 2px; font-size: var(--text-sm); font-weight: 500; color: var(--ink-3); }
.rate-hero .rate-per { color: oklch(100% 0 0 / 0.68); }
.rate-launch { margin: var(--space-2) 0 0; font-size: var(--text-sm); line-height: 1.45; color: var(--ink); font-weight: 600; }
.rate-hero .rate-launch { color: var(--paper); }
.rate-legal { grid-column: 1 / -1; margin: var(--space-3) 0 0; font-size: var(--text-sm); color: var(--ink-3); }
/* Pushes every CTA to the card bottom so buttons line up across columns. */
.rate-spacer { flex: 1 0 var(--space-5); }
.rate-cta {
  align-self: stretch;
  text-align: center;
  font-size: var(--text-sm);
  font-weight: 700;
  padding: 11px 14px;
  border-radius: var(--radius-sm);
  background: var(--ink);
  color: var(--paper);
  transition: background var(--dur-fast) var(--ease-out);
}
a.rate-cta:hover, .rate-buy:hover:not(:disabled) { background: var(--ink-2); }
.rate-buy { font: inherit; font-size: var(--text-sm); font-weight: 700; border: 0; cursor: pointer; }
.rate-hero .rate-buy { background: var(--paper); color: var(--ink); }
.rate-hero .rate-buy:hover:not(:disabled) { background: var(--paper-4); }
.rate-buy:disabled { opacity: 0.7; cursor: wait; }
.rate-cta.is-soon { background: transparent; color: var(--ink-3); border: 1px dashed var(--rule-2); }
.rate-hero .rate-cta.is-soon { color: oklch(100% 0 0 / 0.75); border-color: oklch(100% 0 0 / 0.3); }

.rate-table { grid-column: 1 / -1; grid-row: 2; width: 100%; border-collapse: collapse; font-size: var(--text-sm); table-layout: fixed; }
.rate-table thead { display: none; }
.rate-table th, .rate-table td { padding: var(--space-3) var(--space-5); border-top: 1px solid var(--rule); text-align: left; vertical-align: middle; }
.rate-table tbody th { font-weight: 600; color: var(--ink); width: 20%; }
.rate-table td { border-left: 1px solid var(--rule); color: var(--ink-2); font-variant-numeric: tabular-nums; }
.rate-table td.is-hero { background: oklch(20% 0.008 250 / 0.04); font-weight: 600; color: var(--ink); }
.tick { width: 16px; height: 16px; fill: none; stroke: var(--live); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; vertical-align: -3px; }
.dash { color: var(--ink-4); }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

@media (max-width: 1024px) {
  .strip-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .strip-head { grid-template-columns: minmax(0, 1fr) auto; }
  .strip-lede { grid-column: 1 / -1; grid-row: 2; }
}
@media (max-width: 767px) {
  .archive-strip, .pricing { padding-inline: var(--space-4); }
  .strip-row { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; gap: var(--space-3); margin-inline: calc(var(--space-4) * -1); padding: 0 var(--space-4) var(--space-2); scrollbar-width: none; }
  .strip-row > * { flex: 0 0 82%; scroll-snap-align: start; }
  .pricing-head { grid-template-columns: minmax(0, 1fr); gap: var(--space-4); }
  .rate-card { grid-template-columns: minmax(0, 1fr); }
  .rate { grid-column: 1 !important; grid-row: auto; border-left: 0; border-top: 1px solid var(--rule); }
  .rate-intro + .rate { border-top: 0; }
  .rate-table { grid-row: auto; table-layout: auto; }
  .rate-table thead { display: table-header-group; }
  .rate-table thead th { font-size: var(--text-xs); color: var(--ink-3); font-weight: 600; }
  .rate-table th, .rate-table td { padding: var(--space-3) var(--space-2); }
  .rate-table tbody th { width: auto; }
}
.rate-intro { grid-column: 1; grid-row: 1; padding: var(--space-6) var(--space-5); display: flex; flex-direction: column; justify-content: flex-end; }
.intro-title { margin: 0; font-weight: 700; }
.intro-copy { margin: var(--space-2) 0 0; font-size: var(--text-sm); line-height: 1.55; color: var(--ink-3); max-width: 28ch; }
@media (max-width: 767px) { .rate-intro { display: none; } }
</style>
