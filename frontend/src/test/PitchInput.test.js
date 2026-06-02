import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'

// --- Module mocks (must be before component imports) ---
vi.mock('../api/roast.js', () => ({
  roastApi: {
    create: vi.fn().mockResolvedValue({ job_id: 'job_test_123' }),
    createDeck: vi.fn().mockResolvedValue({ job_id: 'job_test_456' }),
  },
}))

vi.mock('../lib/analytics.js', () => ({
  trackRoastStart: vi.fn().mockResolvedValue(undefined),
  trackRoastComplete: vi.fn().mockResolvedValue(undefined),
  trackParsedPitch: vi.fn().mockResolvedValue(undefined),
  trackReport: vi.fn().mockResolvedValue(undefined),
  trackReactions: vi.fn().mockResolvedValue(undefined),
  trackPdfDownload: vi.fn().mockResolvedValue(undefined),
  trackObjectionFeedback: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('../lib/supabase.js', () => ({ supabase: null }))

// --- Helpers to build router ---
function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'Home', component: { template: '<div />' } },
      { path: '/new', name: 'PitchInput', component: { template: '<div />' } },
      { path: '/run/:jobId', name: 'Watching', component: { template: '<div />' } },
      { path: '/terms', name: 'Terms', component: { template: '<div />' } },
      { path: '/privacy', name: 'Privacy', component: { template: '<div />' } },
    ],
  })
}

// Lazy import after mocks are registered
let PitchInput
beforeEach(async () => {
  PitchInput = (await import('../views/swarm/PitchInput.vue')).default
})

describe('PitchInput — costEst computed', () => {
  async function mountComp(router) {
    await router.push('/new')
    return mount(PitchInput, {
      global: { plugins: [router] },
    })
  }

  it('shows "<0.01" for small agent counts (20 agents)', async () => {
    const router = makeRouter()
    const wrapper = await mountComp(router)
    // Default agentCount is 100; change to 20
    const slider = wrapper.find('input[type="range"]')
    await slider.setValue(20)
    // costEst with 20 agents: speaking=4, tokens=10000, usd=0.006 → '<0.01'
    // The size field meta shows "N agents · est. $X" — find the one in .field-size
    const sizeFieldMeta = wrapper.find('.field-size .field-meta')
    expect(sizeFieldMeta.text()).toContain('<0.01')
  })

  it('shows numeric cost for 500 agents', async () => {
    const router = makeRouter()
    const wrapper = await mountComp(router)
    const slider = wrapper.find('input[type="range"]')
    await slider.setValue(500)
    // 500 agents: speaking=100, tokens=106000, usd~0.0636 → '0.06'
    const sizeFieldMeta = wrapper.find('.field-size .field-meta')
    expect(sizeFieldMeta.text()).toMatch(/\$0\.\d\d/)
  })
})

describe('PitchInput — canSubmit gating', () => {
  async function mountComp(router) {
    await router.push('/new')
    return mount(PitchInput, {
      global: { plugins: [router] },
    })
  }

  it('run button is disabled when pitch is empty (no consent)', async () => {
    const router = makeRouter()
    const wrapper = await mountComp(router)
    const btn = wrapper.find('button[type="submit"]')
    expect(btn.attributes('disabled')).toBeDefined()
  })

  it('run button remains disabled when pitch < 40 chars even with consent checked', async () => {
    const router = makeRouter()
    const wrapper = await mountComp(router)
    // Type a short pitch
    await wrapper.find('textarea').setValue('Short pitch')
    // Check the consent checkbox if it's visible
    const checkbox = wrapper.find('input[type="checkbox"]')
    if (checkbox.exists()) await checkbox.setValue(true)
    const btn = wrapper.find('button[type="submit"]')
    expect(btn.attributes('disabled')).toBeDefined()
  })

  it('run button is enabled when pitch >= 40 chars and consent is checked', async () => {
    const router = makeRouter()
    const wrapper = await mountComp(router)
    const longPitch = 'PROBLEM: We solve the enterprise data silo problem for mid-market SaaS companies.'
    await wrapper.find('textarea').setValue(longPitch)
    const checkbox = wrapper.find('input[type="checkbox"]')
    if (checkbox.exists()) await checkbox.setValue(true)
    const btn = wrapper.find('button[type="submit"]')
    expect(btn.attributes('disabled')).toBeUndefined()
  })
})

describe('PitchInput — runHint', () => {
  async function mountComp(router) {
    await router.push('/new')
    return mount(PitchInput, {
      global: { plugins: [router] },
    })
  }

  it('shows "agree to the terms first" when no content and no consent', async () => {
    const router = makeRouter()
    const wrapper = await mountComp(router)
    expect(wrapper.find('.actions-hint').text()).toBe('agree to the terms first')
  })

  it('shows "fill the pitch first" when consent checked but pitch too short', async () => {
    const router = makeRouter()
    const wrapper = await mountComp(router)
    await wrapper.find('textarea').setValue('Short')
    const checkbox = wrapper.find('input[type="checkbox"]')
    if (checkbox.exists()) await checkbox.setValue(true)
    expect(wrapper.find('.actions-hint').text()).toBe('fill the pitch first')
  })

  it('shows agent count hint when canSubmit is true', async () => {
    const router = makeRouter()
    const wrapper = await mountComp(router)
    const longPitch = 'PROBLEM: We solve the enterprise data silo problem for mid-market SaaS companies in 2024.'
    await wrapper.find('textarea').setValue(longPitch)
    const checkbox = wrapper.find('input[type="checkbox"]')
    if (checkbox.exists()) await checkbox.setValue(true)
    const hint = wrapper.find('.actions-hint').text()
    expect(hint).toContain('agents')
    expect(hint).toContain('60s')
  })
})

describe('PitchInput — hasSection checklist', () => {
  async function mountComp(router) {
    await router.push('/new')
    return mount(PitchInput, {
      global: { plugins: [router] },
    })
  }

  it('check-item gets "done" class when its pattern matches the pitch', async () => {
    const router = makeRouter()
    const wrapper = await mountComp(router)
    const pitch = 'PROBLEM: solving data silos\nPRODUCT: a unified API\nAUDIENCE: B2B SaaS\nPRICING: $49/seat\nCOMPETITORS: vs. Salesforce'
    await wrapper.find('textarea').setValue(pitch)
    const doneItems = wrapper.findAll('.check-item.done')
    expect(doneItems.length).toBeGreaterThan(0)
  })

  it('no check-item is done when pitch is empty', async () => {
    const router = makeRouter()
    const wrapper = await mountComp(router)
    const doneItems = wrapper.findAll('.check-item.done')
    expect(doneItems).toHaveLength(0)
  })
})
