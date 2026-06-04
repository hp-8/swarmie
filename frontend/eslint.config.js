import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'

// Pragmatic, error-prevention-first config. Vue "essential" rules catch real
// bugs (undefined components, missing v-for keys, etc.) without the stylistic
// noise of the full "recommended" set.
export default [
  {
    ignores: [
      'dist/**',
      'node_modules/**',
      'coverage/**',
      '.lighthouseci/**',
      // HeroSwarm.vue is the only <script lang="ts"> SFC. Linting it correctly
      // needs typescript-eslint + a tsconfig; out of scope until the app adopts
      // TS more broadly. Tracked in tech_debt.md (P2).
      'src/components/HeroSwarm.vue',
    ],
  },
  js.configs.recommended,
  ...pluginVue.configs['flat/essential'],
  {
    files: ['**/*.{js,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      'no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrors: 'none' }],
      // Single-word view/page component names (Home, Result) are intentional.
      'vue/multi-word-component-names': 'off',
    },
  },
  {
    // Vitest provides these as globals (test.globals: true).
    files: ['src/test/**/*.{js,vue}'],
    languageOptions: {
      globals: {
        vi: 'readonly', vitest: 'readonly',
        describe: 'readonly', it: 'readonly', test: 'readonly', expect: 'readonly',
        beforeEach: 'readonly', afterEach: 'readonly', beforeAll: 'readonly', afterAll: 'readonly',
      },
    },
  },
]
