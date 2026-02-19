import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    alias: {
      '@/lib/supabase': '/src/lib/__mocks__/supabase.ts'
    },
  },
  server: {
    host: "::",
    port: 8080,
    allowedHosts: [
      "language-community.ailabsafrica.com",
      "localhost",
      "127.0.0.1",
      "::"
    ]
  },
  preview: {
    host: "::",
    port: 8080,
    strictPort: true
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    // Increase chunk size warning limit
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks: {
          // Vendor libraries
          vendor: [
            'react',
            'react-dom',
            'react-router-dom',
          ],
          // UI components
          ui: [
            '@radix-ui/react-dialog',
            '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-tabs',
            '@radix-ui/react-avatar',
            '@radix-ui/react-checkbox',
            '@radix-ui/react-label',
            '@radix-ui/react-progress',
            '@radix-ui/react-scroll-area',
            '@radix-ui/react-select',
            '@radix-ui/react-separator',
            '@radix-ui/react-switch',
            '@radix-ui/react-toast',
            '@radix-ui/react-tooltip',
          ],
          // Form and data libraries
          forms: [
            'react-hook-form',
            '@hookform/resolvers',
            'zod',
          ],
          // Data fetching and state
          data: [
            '@tanstack/react-query',
            '@supabase/supabase-js',
          ],
          // Icons and utilities
          icons: ['lucide-react'],
          utils: [
            'clsx',
            'tailwind-merge',
            'class-variance-authority',
            'date-fns',
          ],
          // Export functionality
          export: [
            'file-saver',
          ],
          // Real-time functionality
          realtime: [
            'socket.io-client',
          ],
          // Charts and visualization
          charts: [
            'recharts',
          ],
          // Notifications
          notifications: [
            'sonner',
          ],
        },
      },
    },
    // Enable compression
    minify: 'esbuild',
    target: 'es2015',
    // Optimize CSS
    cssMinify: true,
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'socket.io-client',
      'file-saver',
      'sonner',
    ],
  },
}));
