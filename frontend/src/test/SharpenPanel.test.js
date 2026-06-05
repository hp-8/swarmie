import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SharpenPanel from '../components/swarm/SharpenPanel.vue'

// AiDisclosure pulls in analytics/UI we don't care about here — stub it.
vi.mock('../components/AiDisclosure.vue', () => ({
  default: { name: 'AiDisclosure', template: '<span />' },
}))

const stubs = {
  AiDisclosure: true,
  // router-link -> plain anchor so the re-roast CTA renders without a router.
  'router-link': { props: ['to'], template: '<a><slot /></a>' },
}

const REPORT = {
  top_objections: [{ text: 'Too expensive for SMBs.' }],
  messaging_gaps: ['Value prop is vague', 'No proof of ROI'],
  next_action: 'Talk to 5 SMB owners about price.',
}

const mountPanel = (report = REPORT, parsedPitch = { one_liner: 'CRM for plumbers' }) =>
  mount(SharpenPanel, { props: { report, parsedPitch }, global: { stubs } })

describe('SharpenPanel', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('renders the Sharpen trigger and hides the panel initially', () => {
    const w = mountPanel()
    expect(w.find('.sharpen-trigger').exists()).toBe(true)
    expect(w.find('.sharpen-overlay').exists()).toBe(false)
  })

  it('first sharpen is free: opens the plan, not the gate', async () => {
    const w = mountPanel()
    await w.find('.sharpen-trigger').trigger('click')

    expect(w.find('.sharpen-plan').exists()).toBe(true)
    expect(w.find('.sharpen-gate').exists()).toBe(false)
    expect(localStorage.getItem('swarmie_sharpen_used')).toBe('1')
  })

  it('seeds the plan from the top objection and gaps', async () => {
    const w = mountPanel()
    await w.find('.sharpen-trigger').trigger('click')

    expect(w.find('.sharpen-positioning').text()).toContain('Too expensive for SMBs.')
    const fixes = w.findAll('.sharpen-fix-text').map((n) => n.text())
    expect(fixes).toHaveLength(3)
    expect(fixes.some((f) => f.includes('Value prop is vague'))).toBe(true)
  })

  it('falls back gracefully when the report has no objections', async () => {
    const w = mountPanel({}, { one_liner: 'CRM for plumbers' })
    await w.find('.sharpen-trigger').trigger('click')

    expect(w.find('.sharpen-positioning').text()).toContain('CRM for plumbers')
    expect(w.findAll('.sharpen-fix-text')).toHaveLength(3)
  })

  it('gates the second sharpen behind email when not signed up', async () => {
    localStorage.setItem('swarmie_sharpen_used', '1')
    const w = mountPanel()
    await w.find('.sharpen-trigger').trigger('click')

    expect(w.find('.sharpen-gate').exists()).toBe(true)
    expect(w.find('.sharpen-plan').exists()).toBe(false)
  })

  it('unlocking with an email reveals the plan and persists the user', async () => {
    localStorage.setItem('swarmie_sharpen_used', '1')
    const w = mountPanel()
    await w.find('.sharpen-trigger').trigger('click')

    await w.find('.sharpen-input').setValue('founder@startup.com')
    await w.find('.sharpen-gate-form').trigger('submit')

    expect(w.find('.sharpen-plan').exists()).toBe(true)
    expect(localStorage.getItem('swarmie_user_email')).toBe('founder@startup.com')
  })

  it('signed-up users skip the gate on every sharpen', async () => {
    localStorage.setItem('swarmie_sharpen_used', '1')
    localStorage.setItem('swarmie_user_email', 'founder@startup.com')
    const w = mountPanel()
    await w.find('.sharpen-trigger').trigger('click')

    expect(w.find('.sharpen-plan').exists()).toBe(true)
    expect(w.find('.sharpen-gate').exists()).toBe(false)
  })

  it('closes the overlay on the close button', async () => {
    const w = mountPanel()
    await w.find('.sharpen-trigger').trigger('click')
    expect(w.find('.sharpen-overlay').exists()).toBe(true)

    await w.find('.sharpen-close').trigger('click')
    expect(w.find('.sharpen-overlay').exists()).toBe(false)
  })
})
