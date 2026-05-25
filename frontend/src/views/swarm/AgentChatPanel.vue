<template>
  <div class="chat">
    <div class="chat-head">
      <span class="h-eyebrow">ask {{ agentName ? '@' + agentName : 'agent' }}</span>
      <span class="chat-turn">{{ turns }}/{{ softCap }}</span>
    </div>

    <div ref="scrollRef" class="chat-log scroll-zone">
      <div v-if="messages.length === 0" class="chat-empty">
        ask a follow-up. they reply in character.
      </div>
      <div
        v-for="(m, i) in messages"
        :key="i"
        class="msg"
        :class="'role-' + m.role"
      >
        <span class="msg-bubble">{{ m.content }}</span>
      </div>
      <div v-if="sending" class="msg role-assistant">
        <span class="msg-bubble typing"><i></i><i></i><i></i></span>
      </div>
    </div>

    <div v-if="overCap" class="paywall">
      <strong>past free limit</strong>
      <p>unlock unlimited chats — $2.55 one-time</p>
      <a class="h-btn is-accent" :href="gumroad" target="_blank" rel="noopener">unlock →</a>
    </div>

    <form class="chat-input" @submit.prevent="send">
      <input
        v-model="draft"
        :disabled="sending || disabled"
        type="text"
        placeholder="what about pricing?"
        maxlength="2000"
      />
      <button class="send-btn" type="submit" :disabled="sending || disabled || !draft.trim()">
        {{ sending ? '...' : 'send' }}
      </button>
    </form>
    <div v-if="error" class="chat-err">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { roastApi } from '../../api/roast'

const props = defineProps({
  jobId: { type: String, required: true },
  agentId: { type: String, required: true },
  agentName: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const messages = ref([])
const draft = ref('')
const sending = ref(false)
const turns = ref(0)
const softCap = ref(10)
const overCap = ref(false)
const error = ref('')
const scrollRef = ref(null)

const gumroad = import.meta.env.VITE_GUMROAD_URL || 'https://hp8.gumroad.com/l/azose'

async function load() {
  error.value = ''
  try {
    const res = await roastApi.getChat(props.jobId, props.agentId)
    const d = res.data || res
    messages.value = d.history || []
    turns.value = d.turns || 0
    softCap.value = d.soft_cap || 10
    overCap.value = !!d.over_cap
    await scrollDown()
  } catch (e) {
    // silent — fresh chat
    messages.value = []
    turns.value = 0
  }
}

async function send() {
  const msg = draft.value.trim()
  if (!msg || sending.value) return
  sending.value = true
  error.value = ''
  messages.value.push({ role: 'user', content: msg })
  draft.value = ''
  await scrollDown()
  try {
    const res = await roastApi.chat(props.jobId, props.agentId, msg)
    const d = res.data || res
    messages.value.push({ role: 'assistant', content: d.reply })
    turns.value = d.turns
    softCap.value = d.soft_cap
    overCap.value = d.over_cap
  } catch (e) {
    error.value = e?.response?.data?.error || e?.message || 'chat failed'
    messages.value.pop() // remove user message we optimistically added
  } finally {
    sending.value = false
    await scrollDown()
  }
}

async function scrollDown() {
  await nextTick()
  if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
}

watch(() => props.agentId, () => { load() })
onMounted(load)
</script>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  border-top: 1px dashed var(--rule);
  padding-top: var(--space-4);
  margin-top: var(--space-2);
  min-height: 0;
}
.chat-head { display: flex; justify-content: space-between; align-items: baseline; }
.chat-turn { font-family: var(--font-mono); font-size: 10px; color: var(--ink-3, rgba(255,255,255,0.5)); }
.chat-log {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-height: 280px;
  overflow-y: auto;
  padding-right: 4px;
}
.chat-empty {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-3, rgba(255,255,255,0.45));
  font-style: italic;
  padding: var(--space-2) 0;
}
.msg { display: flex; }
.msg.role-user { justify-content: flex-end; }
.msg.role-assistant { justify-content: flex-start; }
.msg-bubble {
  display: inline-block;
  max-width: 85%;
  padding: 8px 12px;
  border-radius: 14px;
  font-size: var(--text-sm);
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-word;
}
.role-user .msg-bubble {
  background: var(--accent);
  color: var(--paper);
  border-bottom-right-radius: 4px;
}
.role-assistant .msg-bubble {
  background: color-mix(in oklch, var(--ink) 7%, transparent);
  color: var(--ink);
  border-bottom-left-radius: 4px;
}
.typing { display: inline-flex; gap: 3px; padding: 10px 14px; }
.typing i {
  width: 5px; height: 5px; border-radius: 50%;
  background: currentColor;
  opacity: 0.4;
  animation: typing 1.2s infinite ease-in-out;
}
.typing i:nth-child(2) { animation-delay: 0.15s; }
.typing i:nth-child(3) { animation-delay: 0.3s; }
@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-2px); }
}
.chat-input {
  display: flex;
  gap: 6px;
}
.chat-input input {
  flex: 1;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid var(--rule);
  background: transparent;
  color: var(--ink);
  font-size: var(--text-sm);
  font-family: inherit;
}
.chat-input input:focus { outline: none; border-color: var(--accent); }
.send-btn {
  padding: 8px 14px;
  border-radius: 8px;
  border: 0;
  background: var(--accent);
  color: var(--paper);
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  cursor: pointer;
}
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.chat-err {
  font-size: 11px;
  color: var(--warn, #ff5470);
  font-family: var(--font-mono);
}
.paywall {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: var(--space-3);
  border-radius: 10px;
  background: color-mix(in oklch, var(--accent) 10%, transparent);
  border: 1px dashed var(--accent);
}
.paywall strong { font-family: var(--font-display); font-style: italic; font-size: var(--text-lg); color: var(--ink); }
.paywall p { margin: 0; font-size: var(--text-sm); color: var(--ink); }
</style>
