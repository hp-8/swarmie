import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // PDF generation — only needed on the Result page
          if (id.includes('jspdf') || id.includes('html2canvas')) {
            return 'pdf'
          }
          // D3 — only used by BrainGraph (lazy-loaded via Result)
          if (id.includes('node_modules/d3') || id.includes('node_modules/d3-')) {
            return 'd3'
          }
          // Supabase SDK
          if (id.includes('@supabase')) {
            return 'supabase'
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
