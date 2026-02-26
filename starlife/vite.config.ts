import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3001,
    proxy: {
      '/api/vapi': {
        target: 'https://api.vapi.ai',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/vapi/, ''),
      },
    },
  },
});
