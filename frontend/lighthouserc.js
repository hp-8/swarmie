// Lighthouse CI configuration.
//
// Usage:
//   npm run lighthouse
//   (builds, starts vite preview on :4173, runs lhci autorun, kills preview)
//
// Manual one-shot:
//   npm run build
//   npx vite preview --port 4173 &
//   node_modules/.bin/lhci autorun --config=lighthouserc.js
//   kill %1
//
// Scores are directional — the app uses client-side rendering so Lighthouse
// sees the shell. Home is eagerly loaded; all other routes are lazy.
// Run results go to .lighthouseci/ (gitignored).

export default {
  ci: {
    collect: {
      // LHCI auto-detects ./dist and spins up its own server on a random port.
      // To target a running vite preview on :4173 instead, set staticDistDir
      // to false and set url to 'http://localhost:4173/'.
      staticDistDir: './dist',
      numberOfRuns: 3,
      settings: {
        // Desktop preset gives more stable scores for a SPA dashboard.
        preset: 'desktop',
        // Skip PWA audit — app is not a PWA.
        skipAudits: ['installable-manifest', 'service-worker', 'apple-touch-icon'],
        chromeFlags: '--no-sandbox',
      },
    },
    assert: {
      // Use only the explicit assertions we care about.
      // All built-in lhci preset assertions are disabled.
      preset: 'lighthouse:no-pwa',
      assertions: {
        // Score thresholds (warn rather than fail so CI stays green on first run)
        'categories:performance': ['warn', { minScore: 0.7 }],
        'categories:accessibility': ['warn', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.85 }],
        'categories:seo': ['warn', { minScore: 0.8 }],

        // Core Web Vitals
        'first-contentful-paint': ['warn', { maxNumericValue: 4000 }],
        'total-blocking-time': ['warn', { maxNumericValue: 300 }],
        'cumulative-layout-shift': ['warn', { maxNumericValue: 0.1 }],

        // Disable noisy audits that fire on every SPA build
        'bf-cache': 'off',
        'valid-source-maps': 'off',
        'non-composited-animations': 'off',
        'lcp-lazy-loaded': 'off',
        'prioritize-lcp-image': 'off',
        'unused-javascript': 'off',
      },
    },
    upload: {
      // Write results locally — no LHCI server needed.
      target: 'filesystem',
      outputDir: '.lighthouseci',
    },
  },
}
