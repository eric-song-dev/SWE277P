import react from '@vitejs/plugin-react'
import { configDefaults, defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://localhost:8000' },
  },
  build: {
    rolldownOptions: {
      output: {
        // Keep the shared libraries out of the entry chunk so it stays small.
        codeSplitting: {
          groups: [
            { name: 'vendor-react', test: /node_modules[\\/](react|react-dom|react-router|scheduler)[\\/]/ },
            { name: 'vendor-mui', test: /node_modules[\\/]@(mui[\\/](?!x-)|emotion[\\/])/ },
          ],
        },
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    // Playwright owns e2e/.
    exclude: [...configDefaults.exclude, 'e2e/**'],
  },
})
