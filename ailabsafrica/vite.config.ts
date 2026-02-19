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
		},
	},
	build: {
		// Enable source maps for debugging
		sourcemap: mode === 'development',

		// Optimize chunk splitting for better caching
		rollupOptions: {
			output: {
				manualChunks: {
					// Vendor chunks for better caching
					'react-vendor': ['react', 'react-dom'],
					'router-vendor': ['react-router-dom'],
					'ui-vendor': [
						'@radix-ui/react-dialog',
						'@radix-ui/react-dropdown-menu',
						'@radix-ui/react-tabs',
						'@radix-ui/react-toast',
						'@radix-ui/react-tooltip',
						'lucide-react'
					],
					'form-vendor': ['react-hook-form', '@hookform/resolvers', 'zod'],
					'supabase-vendor': ['@supabase/supabase-js'],
					'query-vendor': ['@tanstack/react-query'],
					'charts-vendor': ['recharts'],
					'utils-vendor': ['date-fns', 'clsx', 'tailwind-merge'],
				},
				// Optimize chunk naming for better caching
				chunkFileNames: (chunkInfo) => {
					const facadeModuleId = chunkInfo.facadeModuleId ? chunkInfo.facadeModuleId.split('/').pop() : 'chunk';
					return `js/[name]-[hash].js`;
				},
				entryFileNames: 'js/[name]-[hash].js',
				assetFileNames: (assetInfo) => {
					const info = assetInfo.name.split('.');
					const ext = info[info.length - 1];
					if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
						return `images/[name]-[hash][extname]`;
					}
					if (/css/i.test(ext)) {
						return `css/[name]-[hash][extname]`;
					}
					return `assets/[name]-[hash][extname]`;
				},
			},
		},

		// Optimize chunk size warnings
		chunkSizeWarningLimit: 1000,

		// Enable minification
		minify: 'terser',
		terserOptions: {
			compress: {
				drop_console: mode === 'production',
				drop_debugger: mode === 'production',
			},
		},
	},

	// Optimize dependencies
	optimizeDeps: {
		include: [
			'react',
			'react-dom',
			'react-router-dom',
			'@supabase/supabase-js',
			'@tanstack/react-query',
			'lucide-react',
			'date-fns',
			'clsx',
			'tailwind-merge',
		],
	},

	// Enable CSS code splitting
	css: {
		devSourcemap: mode === 'development',
	},
}));
