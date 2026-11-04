import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// O frontend roda em http://localhost:5173 e repassa tudo que começa com /api
// para o backend Flask (http://127.0.0.1:5000). Assim os dois parecem um só site.
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:5000', changeOrigin: false },
    },
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.js'],
  },
})
