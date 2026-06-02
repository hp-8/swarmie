import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ObjectionList from '../components/swarm/ObjectionList.vue'

// ObjectionVote uses analytics (Supabase) — stub the whole module so tests are pure
vi.mock('../lib/analytics.js', () => ({
  trackObjectionFeedback: vi.fn().mockResolvedValue(undefined),
  trackRoastStart: vi.fn().mockResolvedValue(undefined),
  trackRoastComplete: vi.fn().mockResolvedValue(undefined),
  trackParsedPitch: vi.fn().mockResolvedValue(undefined),
  trackReport: vi.fn().mockResolvedValue(undefined),
  trackReactions: vi.fn().mockResolvedValue(undefined),
  trackPdfDownload: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('../lib/supabase.js', () => ({ supabase: null }))

const COPY = { askTag: 'ask 5 users', killTag: 'kill signal' }

const makeObjection = (overrides = {}) => ({
  category: 'Pricing',
  count: 3,
  example_quote: 'Too expensive for SMBs.',
  real_test: 'Would you pay $49/mo for this?',
  kill_criteria: 'If > 80% say no.',
  suggested_fix: 'Add a free tier.',
  ...overrides,
})

describe('ObjectionList', () => {
  it('renders empty state when objections prop is []', () => {
    const wrapper = mount(ObjectionList, {
      props: { objections: [], copy: COPY, jobId: 'job_001' },
    })
    expect(wrapper.find('.muted').text()).toBe('No clear clusters.')
    expect(wrapper.find('ol').exists()).toBe(false)
  })

  it('renders N objection rows', () => {
    const objections = [
      makeObjection({ category: 'Pricing' }),
      makeObjection({ category: 'Trust', count: 2, real_test: null }),
    ]
    const wrapper = mount(ObjectionList, {
      props: { objections, copy: COPY, jobId: 'job_001' },
    })
    expect(wrapper.findAll('.obj-row')).toHaveLength(2)
  })

  it('shows rank numbers with zero-padding', () => {
    const objections = [makeObjection({ category: 'A' }), makeObjection({ category: 'B', count: 1 })]
    const wrapper = mount(ObjectionList, {
      props: { objections, copy: COPY, jobId: 'job_001' },
    })
    const ranks = wrapper.findAll('.obj-rank').map(el => el.text())
    expect(ranks).toEqual(['01', '02'])
  })

  it('displays category and count', () => {
    const wrapper = mount(ObjectionList, {
      props: { objections: [makeObjection()], copy: COPY, jobId: 'job_001' },
    })
    expect(wrapper.find('.obj-cat').text()).toBe('Pricing')
    expect(wrapper.find('.obj-count').text()).toBe('3×')
  })

  it('shows copy button when real_test is present', () => {
    const wrapper = mount(ObjectionList, {
      props: { objections: [makeObjection()], copy: COPY, jobId: 'job_001' },
    })
    expect(wrapper.find('.obj-test-q').exists()).toBe(true)
    expect(wrapper.find('.obj-tag').text()).toBe('ask 5 users')
  })

  it('does NOT show copy button when real_test is absent', () => {
    const wrapper = mount(ObjectionList, {
      props: {
        objections: [makeObjection({ real_test: null })],
        copy: COPY,
        jobId: 'job_001',
      },
    })
    expect(wrapper.find('.obj-test-q').exists()).toBe(false)
  })

  it('clicking copy button calls clipboard.writeText', async () => {
    const obj = makeObjection()
    const wrapper = mount(ObjectionList, {
      props: { objections: [obj], copy: COPY, jobId: 'job_001' },
    })
    await wrapper.find('.obj-test-q').trigger('click')
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(obj.real_test)
  })

  it('shows kill_criteria tag when present', () => {
    const wrapper = mount(ObjectionList, {
      props: { objections: [makeObjection()], copy: COPY, jobId: 'job_001' },
    })
    const killTag = wrapper.find('.obj-tag.warn')
    expect(killTag.exists()).toBe(true)
    expect(killTag.text()).toBe('kill signal')
  })

  it('does not render kill criteria section when absent', () => {
    const wrapper = mount(ObjectionList, {
      props: {
        objections: [makeObjection({ kill_criteria: null })],
        copy: COPY,
        jobId: 'job_001',
      },
    })
    expect(wrapper.find('.obj-kill').exists()).toBe(false)
  })

  it('renders example_quote when present', () => {
    const wrapper = mount(ObjectionList, {
      props: { objections: [makeObjection()], copy: COPY, jobId: 'job_001' },
    })
    expect(wrapper.find('.obj-quote').text()).toContain('Too expensive for SMBs.')
  })
})
