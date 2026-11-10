import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AdvisorBrief from '../components/swarm/AdvisorBrief.vue'

const full = {
  what_working: ['Pain is real for agencies'],
  hidden_risks: [{ risk: 'Buyer != user', why_non_obvious: 'all comments from users', cheap_test: 'ask 5 ops leads' }],
  path_forward: { this_week: 'interview 5 ops leads', if_confirmed: 'rewrite landing', if_not: 'per-seat tool' },
}

describe('AdvisorBrief', () => {
  it('renders all three sections', () => {
    const text = mount(AdvisorBrief, { props: { report: full } }).text()
    expect(text).toContain('Pain is real for agencies')
    expect(text).toContain('Buyer != user')
    expect(text).toContain('ask 5 ops leads')
    expect(text).toContain('per-seat tool')
  })

  it('renders nothing for old results without advisor fields', () => {
    const w = mount(AdvisorBrief, { props: { report: { verdict: 'kill' } } })
    expect(w.find('.advisor').exists()).toBe(false)
  })

  it('hides a lone this_week step (it only repeats the hero next_action)', () => {
    const w = mount(AdvisorBrief, { props: { report: { path_forward: { this_week: 'x' } } } })
    expect(w.find('.advisor').exists()).toBe(false)
  })

  it('omits missing optional risk sub-lines', () => {
    const w = mount(AdvisorBrief, { props: { report: { hidden_risks: [{ risk: 'Cold start' }] } } })
    expect(w.text()).toContain('Cold start')
    expect(w.text()).not.toContain('easy to miss')
  })
})
