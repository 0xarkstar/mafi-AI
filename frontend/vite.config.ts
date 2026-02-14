import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: '../static',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          ethers: ['ethers'],
          'framer-motion': ['framer-motion'],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/ws': {
        target: 'http://localhost:8080',
        ws: true,
      },
      '/api': {
        target: 'http://localhost:8080',
      },
    },
  },
})
