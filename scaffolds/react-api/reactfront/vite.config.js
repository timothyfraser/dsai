import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' makes every asset path relative, so the built dist/ works at any
// URL, including a Posit Connect content path like /content/<guid>/.
export default defineConfig({
  plugins: [react()],
  base: './',
  server: {
    // Local development without CORS: the page calls "/api/health" on its own
    // address and Vite forwards it to the API on your machine, so the browser
    // never sees a second origin. Use 127.0.0.1, not "localhost": on Windows,
    // "localhost" can resolve to ::1 and miss an API listening on IPv4.
    // FastAPI runs on 8000. For plumber, change the target to port 5762.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.js'],
  },
})
