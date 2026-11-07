import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0', // 允许外部访问
    port: 5173,
    allowedHosts: [
      '9396rcmx6970.vicp.fun', // 内网穿透域名
      'dealate-ciera-endodermal.ngrok-free.dev', // ngrok 内网穿透域名
      'localhost',
      '.localhost', // 允许所有 localhost 子域名
      '.ngrok-free.dev', // 允许所有 ngrok-free.dev 子域名
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})

