import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // In dev, forward /api to the local Flask server - mirrors what nginx does in production
    proxy: {
      '/api': 'http://localhost:5000',
    },
  },
})
