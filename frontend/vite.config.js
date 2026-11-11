import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
// Search engine verification tags, only emitted when the token env var is set.
const verifyTags = {
  name: 'verify-tags',
  transformIndexHtml() {
    return [
      ['google-site-verification', process.env.VITE_GSC_TOKEN || 'vEFqzcjXGmJZVqRD9RlkauTQ65YSH96JvpeH9AckYc8'],
      ['msvalidate.01', process.env.VITE_BING_TOKEN],
    ].filter(([, v]) => v).map(([name, content]) => ({ tag: 'meta', attrs: { name, content }, injectTo: 'head' }))
  },
}

export default defineConfig({
  plugins: [vue(), verifyTags],
  // Dev: frontend on :3000, /api forwarded to the Flask server on :5001.
  server: { port: 3000, open: true, proxy: { '/api': { target: 'http://localhost:5001', changeOrigin: true } } },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Vite's __vitePreload + Rollup CommonJS interop helpers are shared by
          // every lazy route. Pin them to the always-eager `vue` chunk, else
          // Rollup co-locates them inside a big lazy chunk (e.g. pdf) and the
          // entry modulepreloads that whole chunk just to reach the helper.
          if (id.includes('vite/preload-helper') || id.includes('commonjsHelpers')) {
            return 'vue'
          }
          // PDF generation — only needed on the Result page
          if (id.includes('jspdf') || id.includes('html2canvas')) {
            return 'pdf'
          }
          // D3 — only used by BrainGraph (lazy-loaded via Result)
          if (id.includes('node_modules/d3') || id.includes('node_modules/d3-')) {
            return 'd3'
          }
          // Vue core + Vue Router
          if (id.includes('node_modules/vue') || id.includes('node_modules/@vue') || id.includes('node_modules/vue-router')) {
            return 'vue'
          }
          // DOMPurify
          if (id.includes('dompurify')) {
            return 'dompurify'
          }
          // FingerprintJS + Vercel analytics + Axios — small vendor chunk
          if (
            id.includes('@fingerprintjs') ||
            id.includes('@vercel/analytics') ||
            id.includes('@vercel/speed-insights') ||
            id.includes('node_modules/axios')
          ) {
            return 'tracking'
          }
        },
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      include: ['src/components/swarm/**', 'src/lib/swarms.js', 'src/views/swarm/**'],
      exclude: [
        'src/views/swarm/BrainGraph.vue',
        'src/views/swarm/AgentChatPanel.vue',
        'src/views/swarm/Watching.vue',
        // Result.vue can't be unit-mounted (calls the API + needs route params on
        // mount); its pure helpers are covered via ResultHelpers.test.js.
        'src/views/swarm/Result.vue',
      ],
      // Ratchet floors over the unit-tested surface — prevents regression, raise over time.
      thresholds: {
        statements: 65,
        branches: 55,
        functions: 50,
        lines: 68,
      },
    },
  },
})
