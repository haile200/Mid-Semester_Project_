import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  // Python virtual environments ship their own JavaScript; it is not ours to lint.
  globalIgnores(['dist', 'coverage', 'backend/venv', '.venv']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
  },
  {
    // Cypress runs specs with Mocha and Chai and provides cy and Cypress.
    files: ['cypress/**/*.{js,jsx}'],
    languageOptions: {
      globals: { ...globals.mocha, cy: 'readonly', Cypress: 'readonly', expect: 'readonly' },
    },
  },
  {
    files: ['cypress.config.js'],
    languageOptions: { globals: globals.node },
  },
])
