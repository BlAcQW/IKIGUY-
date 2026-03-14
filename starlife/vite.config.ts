import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
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
          rewrite: (p) => p.replace(/^\/api\/vapi/, ''),
          configure: (proxy) => {
            proxy.on('proxyReq', (proxyReq) => {
              if (env.VAPI_PRIVATE_KEY) {
                proxyReq.setHeader('Authorization', `Bearer ${env.VAPI_PRIVATE_KEY}`);
              }
            });
          },
        },
      },
    },
  };
});
