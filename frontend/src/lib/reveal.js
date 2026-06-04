// Scroll-reveal directive: `v-reveal` fades + lifts an element into view the
// first time it enters the viewport. Pure IntersectionObserver + CSS — no
// animation library. The visual transition lives in tokens.css (.reveal).
//
// Optional delay (ms) for stagger:  v-reveal="120"
//
// Accessibility: under `prefers-reduced-motion: reduce` nothing is hidden —
// the element renders in its final state, no transition.
const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

export const reveal = {
  mounted(el, binding) {
    // Reduced motion (or no IO support): leave the element fully visible.
    if (prefersReducedMotion() || typeof IntersectionObserver === 'undefined') return

    el.classList.add('reveal')
    if (binding.value) el.style.transitionDelay = `${binding.value}ms`

    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            el.classList.add('reveal--in')
            io.unobserve(el)
          }
        }
      },
      { threshold: 0.15, rootMargin: '0px 0px -10% 0px' },
    )
    io.observe(el)
    el.__revealIO = io
  },
  unmounted(el) {
    el.__revealIO?.disconnect()
  },
}

export default {
  install(app) {
    app.directive('reveal', reveal)
  },
}
