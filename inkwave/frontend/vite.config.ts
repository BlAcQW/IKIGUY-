/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@kasaai/shared-frontend': path.resolve(__dirname, '../../shared/frontend'),
      // Allow shared components to resolve dependencies from inkwave's node_modules
      'lucide-react': path.resolve(__dirname, './node_modules/lucide-react'),
      'react-hot-toast': path.resolve(__dirname, './node_modules/react-hot-toast'),
      'axios': path.resolve(__dirname, './node_modules/axios'),
    },
    dedupe: ['react', 'react-dom', 'lucide-react'],
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react/jsx-runtime'],
  },
  build: {
    commonjsOptions: {
      include: [/node_modules/, /shared/],
    },
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['framer-motion', 'lucide-react'],
          'vendor-utils': ['axios', 'zustand', 'clsx'],
          // Feature chunks
          'admin': [
            './src/pages/AdminDashboardPage.tsx',
            './src/pages/ProviderManagementPage.tsx',
            './src/pages/AnalyticsDashboardPage.tsx',
            './src/pages/AuthorUploadPage.tsx',
          ],
        },
      },
    },
  },
  server: {
    port: 5173,
    host: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/test/'],
    },
  },
})
