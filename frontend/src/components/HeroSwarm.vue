<template>
  <canvas
    ref="canvasEl"
    aria-hidden="true"
    style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none;display:block;"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
const props = withDefaults(defineProps<{ density?: number | null }>(), {
  density: null,
})

// ---------------------------------------------------------------------------
// Refs
// ---------------------------------------------------------------------------
const canvasEl = ref<HTMLCanvasElement | null>(null)

// ---------------------------------------------------------------------------
// Color helpers — read CSS custom properties at mount; fall back to literals
// ---------------------------------------------------------------------------
function readToken(prop: string, fallback: string): string {
  const v = getComputedStyle(document.documentElement).getPropertyValue(prop).trim()
  return v || fallback
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface Node {
  x: number
  y: number
  vx: number
  vy: number
  r: number          // base radius
}

interface Pulse {
  nodeIdx: number
  t: number          // elapsed ms
  duration: number   // ~700ms
  color: string
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let ctx: CanvasRenderingContext2D | null = null
let W = 0
let H = 0
let dpr = 1

let nodes: Node[] = []
let pulses: Pulse[] = []

let rafId = 0
let lastTs = 0
let paused = false
let reducedMotion = false

// Colors (set at mount)
let COL_NODE = ''
let COL_EDGE = ''
let COL_CORAL = ''
let COL_GREEN = ''
let COL_RED   = ''

const BASE_NODE_ALPHA = 0.22
const EDGE_ALPHA      = 0.09
const BASE_NODE_R     = 2.2
const CONNECT_DIST    = 130   // px (logical)
const MAX_PULSES      = 4
const PULSE_DUR       = 700   // ms

// ---------------------------------------------------------------------------
// Node count
// ---------------------------------------------------------------------------
function targetCount(): number {
  if (props.density != null) return Math.max(8, props.density)
  if (W <= 480) return 28
  if (W <= 900) return 42
  return 60
}

// ---------------------------------------------------------------------------
// Init / resize nodes
// ---------------------------------------------------------------------------
function initNodes() {
  const n = targetCount()
  // Keep existing nodes where possible; add / trim as needed
  while (nodes.length < n) {
    nodes.push({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.28,
      vy: (Math.random() - 0.5) * 0.28,
      r: BASE_NODE_R + Math.random() * 1.2,
    })
  }
  nodes.length = n
}

// ---------------------------------------------------------------------------
// DPR-aware resize
// ---------------------------------------------------------------------------
function resize() {
  const canvas = canvasEl.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  W = rect.width
  H = rect.height
  dpr = window.devicePixelRatio || 1
  canvas.width  = Math.round(W * dpr)
  canvas.height = Math.round(H * dpr)
  ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.scale(dpr, dpr)
  }
  initNodes()
}

// ---------------------------------------------------------------------------
// Pulse scheduler
// ---------------------------------------------------------------------------
function schedulePulse() {
  const delay = 600 + Math.random() * 2200
  setTimeout(() => {
    if (pulses.length < MAX_PULSES && nodes.length > 0) {
      // Weighted pick: coral ~60%, green ~25%, red ~15%
      const r = Math.random()
      const color = r < 0.60 ? COL_CORAL : r < 0.85 ? COL_GREEN : COL_RED
      const nodeIdx = Math.floor(Math.random() * nodes.length)
      pulses.push({ nodeIdx, t: 0, duration: PULSE_DUR + Math.random() * 200, color })
    }
    schedulePulse()
  }, delay)
}

let pulseTimeoutId: ReturnType<typeof setTimeout> | null = null

function startPulseScheduler() {
  pulseTimeoutId = setTimeout(function loop() {
    if (pulses.length < MAX_PULSES && nodes.length > 0) {
      const r = Math.random()
      const color = r < 0.60 ? COL_CORAL : r < 0.85 ? COL_GREEN : COL_RED
      const nodeIdx = Math.floor(Math.random() * nodes.length)
      pulses.push({ nodeIdx, t: 0, duration: PULSE_DUR + Math.random() * 200, color })
    }
    pulseTimeoutId = setTimeout(loop, 600 + Math.random() * 2200)
  }, 800 + Math.random() * 1200)
}

// ---------------------------------------------------------------------------
// Ease
// ---------------------------------------------------------------------------
function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3)
}
function easeInOutQuad(t: number): number {
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2
}

// ---------------------------------------------------------------------------
// Draw one frame
// ---------------------------------------------------------------------------
function draw(dt: number) {
  if (!ctx) return
  ctx.clearRect(0, 0, W, H)

  // ---- update node positions ----
  for (const nd of nodes) {
    nd.x += nd.vx * dt
    nd.y += nd.vy * dt
    // Wrap at edges
    if (nd.x < -10) nd.x = W + 10
    else if (nd.x > W + 10) nd.x = -10
    if (nd.y < -10) nd.y = H + 10
    else if (nd.y > H + 10) nd.y = -10
  }

  // ---- connecting lines ----
  const distSq = CONNECT_DIST * CONNECT_DIST
  ctx.lineWidth = 0.5
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const dx = nodes[i].x - nodes[j].x
      const dy = nodes[i].y - nodes[j].y
      const d2 = dx * dx + dy * dy
      if (d2 < distSq) {
        // fade out near threshold
        const alpha = EDGE_ALPHA * (1 - d2 / distSq)
        ctx.strokeStyle = `${COL_EDGE} / ${alpha})`
        // COL_EDGE already ends with "oklch(..." — we need full syntax
        // Use globalAlpha instead for simplicity
        ctx.globalAlpha = alpha
        ctx.beginPath()
        ctx.moveTo(nodes[i].x, nodes[i].y)
        ctx.lineTo(nodes[j].x, nodes[j].y)
        ctx.stroke()
      }
    }
  }
  ctx.globalAlpha = 1

  // ---- base nodes ----
  for (let i = 0; i < nodes.length; i++) {
    const nd = nodes[i]
    ctx.globalAlpha = BASE_NODE_ALPHA
    ctx.fillStyle = COL_NODE
    ctx.beginPath()
    ctx.arc(nd.x, nd.y, nd.r, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1

  // ---- pulse overlay ----
  const nextPulses: Pulse[] = []
  for (const pulse of pulses) {
    pulse.t += dt
    const progress = Math.min(pulse.t / pulse.duration, 1)

    // arc: rise fast, hold briefly, fade
    let brightness: number
    let radiusScale: number
    if (progress < 0.25) {
      // attack
      brightness = easeOutCubic(progress / 0.25)
      radiusScale = 1 + 1.4 * easeOutCubic(progress / 0.25)
    } else if (progress < 0.5) {
      // hold
      brightness = 1
      radiusScale = 2.4
    } else {
      // release
      const rel = (progress - 0.5) / 0.5
      brightness = 1 - easeInOutQuad(rel)
      radiusScale = 2.4 - 1.4 * easeInOutQuad(rel)
    }

    const nd = nodes[pulse.nodeIdx]
    if (nd) {
      const alpha = 0.75 * brightness
      const glowAlpha = 0.18 * brightness
      const r = nd.r * radiusScale

      // glow
      const grad = ctx.createRadialGradient(nd.x, nd.y, 0, nd.x, nd.y, r * 3.5)
      grad.addColorStop(0, parseColorWithAlpha(pulse.color, glowAlpha * 1.2))
      grad.addColorStop(1, parseColorWithAlpha(pulse.color, 0))
      ctx.fillStyle = grad
      ctx.beginPath()
      ctx.arc(nd.x, nd.y, r * 3.5, 0, Math.PI * 2)
      ctx.fill()

      // core dot
      ctx.globalAlpha = alpha
      ctx.fillStyle = pulse.color
      ctx.beginPath()
      ctx.arc(nd.x, nd.y, r, 0, Math.PI * 2)
      ctx.fill()
      ctx.globalAlpha = 1
    }

    if (progress < 1) nextPulses.push(pulse)
  }
  pulses = nextPulses
}

// ---------------------------------------------------------------------------
// Color utility — produce rgba-ish string for gradient stops
// Because canvas gradient stops need a string, we use globalAlpha trick
// but for radialGradient stops we need inline alpha.
// We'll parse the oklch string partially and just use globalAlpha via a trick:
// store the raw oklch as-is and use globalAlpha around gradient draws.
// ---------------------------------------------------------------------------
function parseColorWithAlpha(color: string, alpha: number): string {
  // color is like "oklch(74% 0.180 50)" — insert alpha
  // oklch supports "oklch(L C H / A)"
  if (color.endsWith(')')) {
    return color.slice(0, -1) + ` / ${alpha.toFixed(3)})`
  }
  return color
}

// ---------------------------------------------------------------------------
// rAF loop
// ---------------------------------------------------------------------------
function loop(ts: number) {
  if (paused) return
  const dt = lastTs === 0 ? 16 : Math.min(ts - lastTs, 50)
  lastTs = ts
  draw(dt)
  rafId = requestAnimationFrame(loop)
}

// ---------------------------------------------------------------------------
// Static frame for reduced-motion
// ---------------------------------------------------------------------------
function drawStaticFrame() {
  if (!ctx) return
  ctx.clearRect(0, 0, W, H)

  // lines
  const distSq = CONNECT_DIST * CONNECT_DIST
  ctx.lineWidth = 0.5
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const dx = nodes[i].x - nodes[j].x
      const dy = nodes[i].y - nodes[j].y
      const d2 = dx * dx + dy * dy
      if (d2 < distSq) {
        ctx.globalAlpha = EDGE_ALPHA * (1 - d2 / distSq)
        ctx.strokeStyle = COL_EDGE
        ctx.beginPath()
        ctx.moveTo(nodes[i].x, nodes[i].y)
        ctx.lineTo(nodes[j].x, nodes[j].y)
        ctx.stroke()
      }
    }
  }
  ctx.globalAlpha = 1

  // nodes
  for (let i = 0; i < nodes.length; i++) {
    const nd = nodes[i]
    ctx.globalAlpha = BASE_NODE_ALPHA
    ctx.fillStyle = COL_NODE
    ctx.beginPath()
    ctx.arc(nd.x, nd.y, nd.r, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1

  // A couple of static colored nodes to evoke the pulse idea
  const staticColors = [COL_CORAL, COL_GREEN, COL_RED]
  const picks = [
    Math.floor(nodes.length * 0.2),
    Math.floor(nodes.length * 0.55),
    Math.floor(nodes.length * 0.75),
  ]
  picks.forEach((idx, ci) => {
    const nd = nodes[idx]
    if (!nd) return
    ctx!.globalAlpha = 0.55
    ctx!.fillStyle = staticColors[ci % staticColors.length]
    ctx!.beginPath()
    ctx!.arc(nd.x, nd.y, nd.r * 1.8, 0, Math.PI * 2)
    ctx!.fill()
  })
  ctx.globalAlpha = 1
}

// ---------------------------------------------------------------------------
// Visibility API pause / resume
// ---------------------------------------------------------------------------
function onVisibilityChange() {
  if (document.hidden) {
    paused = true
    if (rafId) { cancelAnimationFrame(rafId); rafId = 0 }
  } else {
    if (!reducedMotion && !paused) return  // was already running
    paused = false
    lastTs = 0
    if (!reducedMotion) rafId = requestAnimationFrame(loop)
  }
}

// ---------------------------------------------------------------------------
// ResizeObserver
// ---------------------------------------------------------------------------
let ro: ResizeObserver | null = null
let resizePending = false

function onResizeObserved() {
  if (resizePending) return
  resizePending = true
  requestAnimationFrame(() => {
    resizePending = false
    resize()
    if (reducedMotion) drawStaticFrame()
    else if (!rafId && !paused) {
      lastTs = 0
      rafId = requestAnimationFrame(loop)
    }
  })
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------
onMounted(() => {
  // Check reduced-motion
  reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  // Read tokens
  COL_NODE  = readToken('--ink-4',  'oklch(56% 0.014 270)')
  COL_EDGE  = readToken('--ink-4',  'oklch(56% 0.014 270)')
  COL_CORAL = readToken('--accent', 'oklch(74% 0.180 50)')
  COL_GREEN = readToken('--live',   'oklch(78% 0.200 145)')
  COL_RED   = readToken('--warn',   'oklch(72% 0.215 25)')

  resize()

  if (reducedMotion) {
    drawStaticFrame()
  } else {
    startPulseScheduler()
    document.addEventListener('visibilitychange', onVisibilityChange)
    rafId = requestAnimationFrame(loop)
  }

  ro = new ResizeObserver(onResizeObserved)
  if (canvasEl.value) ro.observe(canvasEl.value)
})

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
  if (pulseTimeoutId) clearTimeout(pulseTimeoutId)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  if (ro) ro.disconnect()
})
</script>
