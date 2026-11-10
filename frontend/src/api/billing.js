import service from './index'

export const billingApi = {
  packs: () => service.get('/api/billing/packs'),
  me: () => service.get('/api/billing/me'),
  checkout: (pack) => service.post('/api/billing/checkout', { pack }),
}

// Send the buyer to Stripe's hosted checkout for a pack.
export async function buyPack(pack) {
  const res = await billingApi.checkout(pack)
  window.location.assign(res.url)
}
