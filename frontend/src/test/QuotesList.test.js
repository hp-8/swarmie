import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import QuotesList from '../components/swarm/QuotesList.vue'

const makeQuote = (overrides = {}) => ({
  agent_id: 'agent_1',
  name: 'VCSkeptic',
  text: 'Where is the moat?',
  tone: 'skeptical',
  segment: 'seed-vc',
  ...overrides,
})

describe('QuotesList', () => {
  it('shows empty state when quotes is []', () => {
    const wrapper = mount(QuotesList, { props: { quotes: [] } })
    expect(wrapper.find('.muted').text()).toBe('No standout reactions.')
    expect(wrapper.findAll('.quote')).toHaveLength(0)
  })

  it('renders a quote card for each quote', () => {
    const quotes = [
      makeQuote({ agent_id: 'a1', tone: 'skeptical' }),
      makeQuote({ agent_id: 'a2', tone: 'enthusiastic', name: 'EarlyAdopter' }),
    ]
    const wrapper = mount(QuotesList, { props: { quotes } })
    expect(wrapper.findAll('.quote')).toHaveLength(2)
  })

  it('applies tone-<tone> class to each card', () => {
    const quotes = [
      makeQuote({ agent_id: 'a1', tone: 'skeptical' }),
      makeQuote({ agent_id: 'a2', tone: 'enthusiastic' }),
      makeQuote({ agent_id: 'a3', tone: 'curious' }),
    ]
    const wrapper = mount(QuotesList, { props: { quotes } })
    const cards = wrapper.findAll('.quote')
    expect(cards[0].classes()).toContain('tone-skeptical')
    expect(cards[1].classes()).toContain('tone-enthusiastic')
    expect(cards[2].classes()).toContain('tone-curious')
  })

  it('renders @name handle for each quote', () => {
    const wrapper = mount(QuotesList, {
      props: { quotes: [makeQuote({ name: 'SeedSkeptic' })] },
    })
    expect(wrapper.find('.q-handle').text()).toBe('@SeedSkeptic')
  })

  it('renders the quote text', () => {
    const wrapper = mount(QuotesList, {
      props: { quotes: [makeQuote({ text: 'Why not just use Excel?' })] },
    })
    expect(wrapper.find('.q-text').text()).toBe('Why not just use Excel?')
  })

  it('renders tone and segment in meta', () => {
    const wrapper = mount(QuotesList, {
      props: { quotes: [makeQuote({ tone: 'aggressive', segment: 'enterprise-it' })] },
    })
    const meta = wrapper.find('.q-meta')
    expect(meta.find('.q-tone').text()).toBe('aggressive')
    expect(meta.find('.q-seg').text()).toBe('enterprise-it')
  })

  it('does not show empty-state p when quotes are provided', () => {
    const wrapper = mount(QuotesList, {
      props: { quotes: [makeQuote()] },
    })
    expect(wrapper.find('.muted').exists()).toBe(false)
  })

  it('handles tone-aggressive class for aggressive tone', () => {
    const wrapper = mount(QuotesList, {
      props: { quotes: [makeQuote({ tone: 'aggressive' })] },
    })
    expect(wrapper.find('.quote').classes()).toContain('tone-aggressive')
  })
})
