<template>
  <div class="brain-wrap" ref="wrapRef">
    <canvas ref="canvasRef" class="brain-canvas" @click="onClick" @mousemove="onMove"></canvas>
    <div v-if="hover" class="brain-tip" :style="tipStyle">
      <strong>@{{ hover.name }}</strong>
      <span class="tip-row">{{ hover.segment }} · {{ hover.tone }}</span>
      <span class="tip-row" v-if="hover.state === 'reacted'">{{ hover.action }} · sent {{ (hover.sentiment ?? 0).toFixed(2) }}</span>
      <span class="tip-row" v-else>{{ hover.state }}</span>
    </div>
    <div class="brain-legend">
      <span class="lg"><i class="dot idle"></i> idle</span>
      <span class="lg"><i class="dot thinking"></i> thinking</span>
      <span class="lg"><i class="dot pos"></i> positive</span>
      <span class="lg"><i class="dot neg"></i> negative</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  archetypes: { type: Array, default: () => [] },
  agents: { type: Map, default: () => new Map() }, // agent_id -> {state, ...}
  pitchLabel: { type: String, default: 'pitch' },
})
const emit = defineEmits(['select-agent'])

const wrapRef = ref(null)
const canvasRef = ref(null)
const hover = ref(null)
const tipPos = ref({ x: 0, y: 0 })
const tipStyle = computed(() => ({ left: tipPos.value.x + 14 + 'px', top: tipPos.value.y + 14 + 'px' }))

let sim = null
let ctx = null
let width = 0
let height = 0
let raf = null
let dpr = 1

// node graph
let rootNode = null
let archetypeNodes = []
let agentNodes = []
let nodes = []
let links = []

const SEG_COLORS = d3.scaleOrdinal(d3.schemeTableau10)

function color(node) {
  if (node.kind === 'root') return '#fff'
  if (node.kind === 'archetype') return SEG_COLORS(node.segment)
  // agent
  if (node.state === 'thinking') return '#ffd166'
  if (node.state === 'reacted') {
    const s = node.sentiment ?? 0
    if (s > 0.15) return '#3ddc97'
    if (s < -0.15) return '#ff5470'
    return '#a0a0b8'
  }
  return '#3a3a52'
}

function radius(node) {
  if (node.kind === 'root') return 18
  if (node.kind === 'archetype') return 11
  if (node.state === 'thinking') return 5 + node.pulse * 3
  if (node.state === 'reacted') return 4
  return 2.5
}

function build() {
  if (!props.archetypes.length) return
  rootNode = { id: '__root__', kind: 'root', fx: 0, fy: 0 }
  archetypeNodes = props.archetypes.map((a, i) => {
    const angle = (i / props.archetypes.length) * Math.PI * 2
    const R = Math.min(width, height) * 0.22
    return {
      id: a.id,
      kind: 'archetype',
      segment: a.segment,
      name: a.name,
      tone: a.tone,
      x: Math.cos(angle) * R,
      y: Math.sin(angle) * R,
    }
  })
  const archById = new Map(archetypeNodes.map(a => [a.id, a]))
  agentNodes = []
  for (const [aid, ag] of props.agents.entries()) {
    const parent = archById.get(ag.archetype_id)
    if (!parent) continue
    const jitter = 30 + Math.random() * 50
    const ang = Math.random() * Math.PI * 2
    agentNodes.push({
      id: aid,
      kind: 'agent',
      archetype_id: ag.archetype_id,
      segment: ag.segment,
      name: ag.name,
      tone: ag.tone,
      state: ag.state,
      action: ag.action,
      sentiment: ag.sentiment,
      pulse: 0,
      x: parent.x + Math.cos(ang) * jitter,
      y: parent.y + Math.sin(ang) * jitter,
    })
  }
  nodes = [rootNode, ...archetypeNodes, ...agentNodes]
  links = [
    ...archetypeNodes.map(a => ({ source: rootNode.id, target: a.id, kind: 'spoke' })),
    ...agentNodes.map(a => ({ source: a.archetype_id, target: a.id, kind: 'synapse' })),
  ]

  if (sim) sim.stop()
  sim = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(l => l.kind === 'spoke' ? 130 : 28).strength(0.4))
    .force('charge', d3.forceManyBody().strength(d => d.kind === 'agent' ? -8 : -120))
    .force('collide', d3.forceCollide().radius(d => radius(d) + 1.5))
    .force('center', d3.forceCenter(0, 0).strength(0.05))
    .alpha(0.9)
    .alphaDecay(0.02)
}

function tick() {
  if (!ctx) return
  ctx.save()
  ctx.clearRect(0, 0, width, height)
  ctx.translate(width / 2, height / 2)

  // links
  ctx.lineWidth = 0.6
  for (const l of links) {
    const s = typeof l.source === 'object' ? l.source : nodes.find(n => n.id === l.source)
    const t = typeof l.target === 'object' ? l.target : nodes.find(n => n.id === l.target)
    if (!s || !t) continue
    if (l.kind === 'spoke') {
      ctx.strokeStyle = 'rgba(255,255,255,0.10)'
    } else {
      if (t.state === 'thinking') ctx.strokeStyle = 'rgba(255,209,102,0.55)'
      else if (t.state === 'reacted') ctx.strokeStyle = 'rgba(255,255,255,0.07)'
      else ctx.strokeStyle = 'rgba(255,255,255,0.03)'
    }
    ctx.beginPath()
    ctx.moveTo(s.x, s.y)
    ctx.lineTo(t.x, t.y)
    ctx.stroke()
  }

  // nodes
  for (const n of nodes) {
    const r = radius(n)
    if (n.state === 'thinking') {
      ctx.shadowColor = '#ffd166'
      ctx.shadowBlur = 18
    } else if (n.kind === 'root') {
      ctx.shadowColor = '#ff5470'
      ctx.shadowBlur = 22
    } else {
      ctx.shadowBlur = 0
    }
    ctx.beginPath()
    ctx.arc(n.x, n.y, r, 0, Math.PI * 2)
    ctx.fillStyle = color(n)
    ctx.fill()
    if (n.kind === 'archetype') {
      ctx.lineWidth = 1.5
      ctx.strokeStyle = 'rgba(255,255,255,0.6)'
      ctx.stroke()
    }
  }
  ctx.shadowBlur = 0

  // root label
  ctx.fillStyle = '#0b0b14'
  ctx.font = '600 10px ui-sans-serif, system-ui'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('PITCH', 0, 0)

  ctx.restore()

  // pulse decay
  for (const n of agentNodes) {
    if (n.state === 'thinking') n.pulse = Math.max(0, n.pulse - 0.04)
  }
  raf = requestAnimationFrame(tick)
}

function resize() {
  const wrap = wrapRef.value
  if (!wrap || !canvasRef.value) return
  const rect = wrap.getBoundingClientRect()
  width = rect.width
  height = rect.height
  dpr = window.devicePixelRatio || 1
  canvasRef.value.width = width * dpr
  canvasRef.value.height = height * dpr
  canvasRef.value.style.width = width + 'px'
  canvasRef.value.style.height = height + 'px'
  ctx = canvasRef.value.getContext('2d')
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function pickAt(clientX, clientY) {
  const rect = canvasRef.value.getBoundingClientRect()
  const x = clientX - rect.left - width / 2
  const y = clientY - rect.top - height / 2
  let best = null
  let bestD = Infinity
  for (const n of nodes) {
    const dx = n.x - x, dy = n.y - y
    const d2 = dx * dx + dy * dy
    const r = radius(n) + 3
    if (d2 < r * r && d2 < bestD) {
      best = n
      bestD = d2
    }
  }
  return best
}

function onMove(e) {
  const n = pickAt(e.clientX, e.clientY)
  if (n && n.kind === 'agent') {
    hover.value = n
    const rect = wrapRef.value.getBoundingClientRect()
    tipPos.value = { x: e.clientX - rect.left, y: e.clientY - rect.top }
    canvasRef.value.style.cursor = 'pointer'
  } else if (n && n.kind === 'archetype') {
    hover.value = { name: n.name, segment: n.segment, tone: n.tone, state: 'archetype' }
    const rect = wrapRef.value.getBoundingClientRect()
    tipPos.value = { x: e.clientX - rect.left, y: e.clientY - rect.top }
    canvasRef.value.style.cursor = 'pointer'
  } else {
    hover.value = null
    canvasRef.value.style.cursor = 'default'
  }
}

function onClick(e) {
  const n = pickAt(e.clientX, e.clientY)
  if (n && n.kind === 'agent') emit('select-agent', n.id)
}

// patch in-place updates without rebuilding sim (for state changes)
function patchAgents() {
  const map = new Map(agentNodes.map(n => [n.id, n]))
  let added = false
  for (const [aid, ag] of props.agents.entries()) {
    const ex = map.get(aid)
    if (ex) {
      const wasThinking = ex.state === 'thinking'
      ex.state = ag.state
      ex.action = ag.action
      ex.sentiment = ag.sentiment
      if (ex.state === 'thinking' && !wasThinking) ex.pulse = 1
    } else {
      added = true
    }
  }
  if (added) {
    build()
  }
}

watch(() => props.archetypes.length, () => { build() })
watch(() => props.agents.size, () => { patchAgents() }, { flush: 'post' })

// also watch agents content shallowly via a counter externally (parent triggers via .size)

onMounted(() => {
  resize()
  window.addEventListener('resize', resize)
  build()
  tick()
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  if (raf) cancelAnimationFrame(raf)
  if (sim) sim.stop()
})

defineExpose({ patchAgents })
</script>

<style scoped>
.brain-wrap {
  position: relative;
  width: 100%;
  height: 100%;
  background: radial-gradient(ellipse at center, #14142a 0%, #07070f 75%);
  border-radius: 12px;
  overflow: hidden;
}
.brain-canvas { display: block; width: 100%; height: 100%; }
.brain-tip {
  position: absolute;
  pointer-events: none;
  background: rgba(11, 11, 20, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #f0f0fa;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 11px;
  font-family: var(--font-mono, ui-monospace);
  display: flex;
  flex-direction: column;
  gap: 2px;
  z-index: 10;
  max-width: 220px;
}
.tip-row { color: rgba(240, 240, 250, 0.7); }
.brain-legend {
  position: absolute;
  bottom: 10px;
  left: 12px;
  display: flex;
  gap: 12px;
  font-size: 10px;
  font-family: var(--font-mono, ui-monospace);
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 0.08em;
}
.lg { display: inline-flex; align-items: center; gap: 5px; }
.lg .dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.dot.idle { background: #3a3a52; }
.dot.thinking { background: #ffd166; box-shadow: 0 0 6px #ffd166; }
.dot.pos { background: #3ddc97; }
.dot.neg { background: #ff5470; }
</style>
