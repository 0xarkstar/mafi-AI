import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
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
    allowedHosts: ['host.docker.internal', 'localhost'],
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
