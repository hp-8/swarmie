import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DecisionMemo from '../components/swarm/DecisionMemo.vue'

const STUBS = { ObjectionList: true, QuotesList: true, SharpenPanel: true, AiDisclosure: true }
const COPY = { objections: 'top objections', voices: 'loudest voices', segments: 'segments', silence: (p) => `why ${p}% scrolled past` }

function makeReport(overrides = {}) {
  return {
    verdict: 'sharpen_positioning',
    verdict_reason: 'Real pull, wrong buyer.',
    next_action: 'Interview 5 administrators.',
    confidence: 'med',
    confidence_reason: '61 spoke',
    headline: 'Teachers want it',
    sentiment_split: { positive: 41, neutral: 23, negative: 36 },
    action_split: { post: 6, comment: 55, upvote: 12, ignore: 27 },
    silent_share_pct: 27,
    top_objections: [],
    icp_fit: { teachers: { count: 72 } },
    narrative: 'Summary text.',
    messaging_gaps: [],
    ignore_reasons: [],
    quoted_reactions: [],
    ...overrides,
  }
}

const mountMemo = (report, props = {}) =>
  mount(DecisionMemo, {
    props: { report, copy: COPY, jobId: 'job_1', reactionCount: 100, ...props },
    global: { stubs: STUBS },
  })

describe('DecisionMemo', () => {
  it('leads with the memo phrasing of the verdict and the reason', () => {
    const w = mountMemo(makeReport())
    expect(w.find('.rec-verdict').text()).toBe('Sharpen the positioning.')
    expect(w.find('.rec-reason').text()).toBe('Real pull, wrong buyer.')
    expect(w.find('.rec-action').text()).toContain('Interview 5 administrators.')
  })

  it('falls back to the headline when there is no verdict', () => {
    const w = mountMemo(makeReport({ verdict: '' }))
    expect(w.find('.rec-verdict').text()).toBe('Teachers want it')
  })

  it('summarises the panel from real counts', () => {
    const w = mountMemo(makeReport())
    expect(w.text()).toContain('100 reviewers · 61 spoke · 27% scrolled past')
    expect(w.find('.conf').text()).toBe('Medium')
  })

  it('renders numbered hidden risks with deep-linkable ids', () => {
    const w = mountMemo(makeReport({
      hidden_risks: [{ risk: 'Buyer is not the user.', why_non_obvious: 'Only teachers spoke.', cheap_test: 'Ask 5 admins.' }],
    }))
    const f = w.find('#risk-1')
    expect(f.exists()).toBe(true)
    expect(f.text()).toContain('Buyer is not the user.')
    expect(f.text()).toContain('only teachers spoke.')
    expect(f.text()).toContain('Ask 5 admins.')
  })

  it('copies a link to a single finding', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { clipboard: { writeText } })
    const w = mountMemo(makeReport({ hidden_risks: [{ risk: 'R' }] }))
    await w.find('.f-link').trigger('click')
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining('#risk-1'))
  })

  it('omits advisor sections on old reports that lack them', () => {
    const w = mountMemo(makeReport())
    expect(w.find('#working').exists()).toBe(false)
    expect(w.find('#risks').exists()).toBe(false)
    expect(w.find('#path').exists()).toBe(false)
  })

  it('hides the path forward when it only repeats this week', () => {
    const w = mountMemo(makeReport({ path_forward: { this_week: 'x' } }))
    expect(w.find('#path').exists()).toBe(false)
    const w2 = mountMemo(makeReport({ path_forward: { this_week: 'x', if_not: 'y' } }))
    expect(w2.find('#path').text()).toContain('If not')
  })

  it('letters exhibits by which ones actually render', () => {
    const w = mountMemo(makeReport(), { usage: { total_cost_usd: 0.0213, total_tokens: 1000, total_calls: 4 } })
    const ids = w.findAll('.ex-id').map((e) => e.text())
    // sentiment, segments, cost (no silence, no voices)
    expect(ids).toEqual(['A', 'B', 'C'])
  })

  it('shows real cost, and says so when it is negligible instead of inventing one', () => {
    const w = mountMemo(makeReport(), { usage: { total_cost_usd: 0.0213, total_tokens: 1, total_calls: 1 } })
    expect(w.text()).toContain('$0.0213')
    const w2 = mountMemo(makeReport(), { usage: { total_cost_usd: 0.0001, total_tokens: 1, total_calls: 1 } })
    expect(w2.text()).toContain('under $0.001')
  })

  it('colours low confidence as a warning', () => {
    const w = mountMemo(makeReport({ confidence: 'low' }))
    expect(w.find('.conf').classes()).toContain('is-low')
  })
})
