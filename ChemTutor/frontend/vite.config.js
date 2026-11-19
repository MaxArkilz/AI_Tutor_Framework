import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/': 'http://localhost:8000',
      '/api-auth/': 'http://localhost:8000',
      '/byu/': 'http://localhost:8000',
      '/admin/': 'http://localhost:8000',
      '/static/': 'http://localhost:8000',
    },
  },
})
