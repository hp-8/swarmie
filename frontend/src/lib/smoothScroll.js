// Smooth scroll (Lenis). Buttery wheel/trackpad scrolling for the chic feel.
//
// Accessibility: fully disabled under `prefers-reduced-motion: reduce` — those
// users get native scroll, no hijack. Touch is left native too (better on
// mobile, avoids scroll-jacking).
import Lenis from 'lenis'

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

let lenis = null
let rafId = null

export function getLenis() {
  return lenis
}

export function startSmoothScroll() {
  if (lenis || prefersReducedMotion()) return null

  lenis = new Lenis({
    lerp: 0.1,          // glide factor — lower = silkier, higher = snappier
    wheelMultiplier: 1,
    smoothWheel: true,
    syncTouch: false,   // native momentum on touch devices
  })

  const raf = (time) => {
    lenis.raf(time)
    rafId = requestAnimationFrame(raf)
  }
  rafId = requestAnimationFrame(raf)

  return lenis
}

export function stopSmoothScroll() {
  if (rafId != null) cancelAnimationFrame(rafId)
  rafId = null
  lenis?.destroy()
  lenis = null
}

// Jump to top with no animation — used on route change.
export function resetScroll() {
  if (lenis) lenis.scrollTo(0, { immediate: true })
  else window.scrollTo(0, 0)
}

// Smooth-scroll to an element or selector (e.g. in-page anchors).
export function scrollToTarget(target, options = {}) {
  if (lenis) lenis.scrollTo(target, options)
}
