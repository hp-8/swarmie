import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'

const sendMagicLink = vi.fn().mockResolvedValue(undefined)
vi.mock('../lib/account', () => ({
  sendMagicLink: (...a) => sendMagicLink(...a),
  BILLING_ENABLED: true,
  session: { value: null },
}))

const SignIn = (await import('../views/SignIn.vue')).default

async function mountPage() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/signin', component: SignIn }] })
  await router.push('/signin?pack=starter')
  const w = mount(SignIn, { global: { plugins: [router], stubs: { SiteNav: true, SiteFooter: true } } })
  await w.find('#email').setValue('a@b.test')
  await w.find('form').trigger('submit')
  await flushPromises()
  return w
}

describe('SignIn resend', () => {
  beforeEach(() => { vi.useFakeTimers(); sendMagicLink.mockClear() })
  afterEach(() => vi.useRealTimers())

  it('sends once, carrying the pack to buy after sign-in', async () => {
    await mountPage()
    expect(sendMagicLink).toHaveBeenCalledWith('a@b.test', '/account?buy=starter')
  })

  it('locks resend for 60s, then resends', async () => {
    const w = await mountPage()
    const btn = () => w.find('.sent-actions .btn-ghost')
    expect(btn().attributes('disabled')).toBeDefined()
    expect(btn().text()).toContain('60s')

    vi.advanceTimersByTime(60_000)
    await w.vm.$nextTick()
    expect(btn().attributes('disabled')).toBeUndefined()

    await btn().trigger('click')
    await flushPromises()
    expect(sendMagicLink).toHaveBeenCalledTimes(2)
    expect(w.find('.note').text()).toContain('Sent again')
  })
})
