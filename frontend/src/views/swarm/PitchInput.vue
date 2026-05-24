<template>
  <div class="pitch-input">
    <header class="nav">
      <div class="brand" @click="$router.push('/')">SWARMIE</div>
      <a class="ghost-link" href="https://github.com/hp-8/swarmie" target="_blank">GitHub ↗</a>
    </header>

    <main class="content">
      <h1 class="title">Roast your startup with <span class="accent">{{ agentCount }}</span> AI users.</h1>
      <p class="subtitle">
        Paste your pitch. We'll simulate a swarm of real-looking commenters and surface
        the top objections in about a minute.
      </p>

      <form class="form" @submit.prevent="onSubmit">
        <label class="label" for="pitch-text">Your pitch</label>
        <textarea
          id="pitch-text"
          v-model="pitchText"
          class="textarea"
          rows="14"
          placeholder="Paste your one-pager, deck text, or landing-page copy. Mention the problem, the product, who it's for, and pricing if you have it."
          :disabled="submitting"
          maxlength="20000"
        />
        <div class="meta">
          <span>{{ pitchText.length }} / 20000</span>
        </div>

        <div class="row">
          <label class="label" for="agent-count">Swarm size</label>
          <input
            id="agent-count"
            v-model.number="agentCount"
            class="number-input"
            type="number"
            min="10"
            max="500"
            step="10"
            :disabled="submitting"
          />
          <span class="hint">10–500 agents. Bigger swarm = more signal but more cost.</span>
        </div>

        <div v-if="error" class="error">{{ error }}</div>

        <button class="cta" type="submit" :disabled="!canSubmit || submitting">
          {{ submitting ? 'Starting…' : 'Run the swarm' }}
        </button>
      </form>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { roastApi } from '../../api/roast'

const router = useRouter()

const pitchText = ref('')
const agentCount = ref(100)
const submitting = ref(false)
const error = ref('')

const canSubmit = computed(() => pitchText.value.trim().length >= 40)

async function onSubmit() {
  if (!canSubmit.value || submitting.value) return
  error.value = ''
  submitting.value = true
  try {
    const res = await roastApi.create(pitchText.value.trim(), agentCount.value)
    const jobId = res.job_id || res.data?.job_id
    if (!jobId) throw new Error('No job_id in response')
    router.push({ name: 'Watching', params: { jobId } })
  } catch (e) {
    error.value = e?.response?.data?.error || e?.message || 'Failed to start roast'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.pitch-input {
  min-height: 100vh;
  background: #0b0c10;
  color: #f4f4f5;
  font-family: 'Inter', system-ui, sans-serif;
}

.nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 32px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand {
  font-weight: 800;
  letter-spacing: 0.18em;
  cursor: pointer;
  font-size: 14px;
}

.ghost-link {
  color: rgba(255, 255, 255, 0.55);
  font-size: 13px;
  text-decoration: none;
}
.ghost-link:hover { color: #fff; }

.content {
  max-width: 760px;
  margin: 0 auto;
  padding: 64px 32px 96px;
}

.title {
  font-size: 44px;
  font-weight: 700;
  line-height: 1.15;
  margin: 0 0 16px;
  letter-spacing: -0.02em;
}

.accent {
  background: linear-gradient(90deg, #ff6b35, #f59e0b);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.subtitle {
  color: rgba(255, 255, 255, 0.6);
  font-size: 17px;
  line-height: 1.55;
  margin: 0 0 40px;
  max-width: 580px;
}

.form { display: flex; flex-direction: column; gap: 18px; }

.label {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.5);
}

.textarea {
  width: 100%;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 16px;
  color: inherit;
  font: 15px/1.55 'JetBrains Mono', ui-monospace, monospace;
  resize: vertical;
  min-height: 280px;
}
.textarea:focus {
  outline: none;
  border-color: rgba(245, 158, 11, 0.4);
  background: rgba(255, 255, 255, 0.06);
}

.meta {
  text-align: right;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
}

.row { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }

.number-input {
  width: 100px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 10px 12px;
  color: inherit;
  font-family: inherit;
  font-size: 15px;
}

.hint { color: rgba(255, 255, 255, 0.4); font-size: 13px; }

.error {
  color: #f87171;
  font-size: 14px;
  padding: 10px 14px;
  background: rgba(248, 113, 113, 0.08);
  border: 1px solid rgba(248, 113, 113, 0.2);
  border-radius: 8px;
}

.cta {
  margin-top: 12px;
  align-self: flex-start;
  padding: 14px 28px;
  background: linear-gradient(90deg, #ff6b35, #f59e0b);
  color: #0b0c10;
  font-weight: 700;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 16px;
  letter-spacing: 0.01em;
  transition: transform 0.1s;
}
.cta:hover:not(:disabled) { transform: translateY(-1px); }
.cta:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
