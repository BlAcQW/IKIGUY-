import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [
    react(),
    mode === 'development' &&
    componentTagger(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@kasaai/shared-frontend": path.resolve(__dirname, "../shared/frontend"),
    },
    dedupe: ['react', 'react-dom', 'lucide-react', 'react-hot-toast', 'axios'],
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react/jsx-runtime'],
  },
  build: {
    commonjsOptions: {
      include: [/node_modules/, /shared/],
    },
  },
}));
