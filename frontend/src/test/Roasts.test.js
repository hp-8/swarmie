import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Roasts from '../views/Roasts.vue'
import data from '../data/famousRoasts.json'

const mountPage = () =>
  mount(Roasts, {
    global: {
      stubs: {
        'router-link': { props: ['to'], template: '<a :href="to"><slot /></a>' },
      },
    },
  })

describe('Roasts gallery', () => {
  it('renders one card per famous roast', () => {
    const w = mountPage()
    expect(w.findAll('.roast-card')).toHaveLength(data.roasts.length)
  })

  it('shows each name, verdict label and color class', () => {
    const w = mountPage()
    const cards = w.findAll('.roast-card')
    expect(cards[0].text()).toContain('Juicero')
    expect(cards[0].find('.verdict').classes()).toContain('is-kill')
    expect(cards[0].find('.verdict').text()).toBe('kill')
  })

  it('discloses synthetic users on the page', () => {
    const w = mountPage()
    expect(w.text().toLowerCase()).toContain('synthetic')
  })

  it('every card carries a roast-your-own CTA to the pitch input', () => {
    const w = mountPage()
    const ctas = w.findAll('.card-cta')
    expect(ctas).toHaveLength(data.roasts.length)
    for (const cta of ctas) expect(cta.attributes('href')).toBe('/new')
  })

  it('shows the silence stat per card', () => {
    const w = mountPage()
    expect(w.findAll('.roast-card')[0].text()).toMatch(/\d+% scrolled past/)
  })
})
