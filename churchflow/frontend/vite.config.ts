import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
	plugins: [
		react(),
		VitePWA({
			registerType: 'prompt',
			injectRegister: null, // Manual registration in main.tsx
			includeAssets: ['favicon.svg', 'apple-touch-icon.png', 'robots.txt'],
			manifest: {
				name: 'ChurchFlow - Church Management Platform',
				short_name: 'ChurchFlow',
				description: 'Seamless movement. Warm connections. Complete church conference and event management.',
				theme_color: '#9333ea',
				background_color: '#f9fafb',
				display: 'standalone',
				orientation: 'portrait-primary',
				scope: '/',
				start_url: '/',
				icons: [
					{
						src: '/icon-192x192.png',
						sizes: '192x192',
						type: 'image/png',
					},
					{
						src: '/icon-384x384.png',
						sizes: '384x384',
						type: 'image/png',
					},
					{
						src: '/icon-512x512.png',
						sizes: '512x512',
						type: 'image/png',
					},
					{
						src: '/icon-512x512.png',
						sizes: '512x512',
						type: 'image/png',
						purpose: 'maskable',
					},
				],
				categories: ['productivity', 'utilities', 'social'],
			},
			workbox: {
				globPatterns: ['**/*.{js,css,ico,png,svg,woff2}'], // HTML removed - fetched via NetworkFirst
				navigateFallback: '/offline.html',
				navigateFallbackDenylist: [/^\/api/, /^\/manifest\.webmanifest$/],
				skipWaiting: false, // Manual control via message
				clientsClaim: true,
				maximumFileSizeToCacheInBytes: 3 * 1024 * 1024, // 3 MB limit
				runtimeCaching: [
					// HTML files - always check network first for fresh CSP headers
					{
						urlPattern: ({ request }) => request.destination === 'document',
						handler: 'NetworkFirst',
						options: {
							cacheName: 'html-cache',
							expiration: {
								maxEntries: 10,
								maxAgeSeconds: 60 * 60, // 1 hour
							},
							networkTimeoutSeconds: 5,
						},
					},
					// Google Fonts CSS stylesheets
					{
						urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
						handler: 'StaleWhileRevalidate',
						options: {
							cacheName: 'google-fonts-stylesheets',
							expiration: {
								maxEntries: 20,
								maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
							},
						},
					},
					// Google Fonts webfont files
					{
						urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
						handler: 'CacheFirst',
						options: {
							cacheName: 'google-fonts-webfonts',
							expiration: {
								maxEntries: 30,
								maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
							},
							cacheableResponse: {
								statuses: [0, 200],
							},
						},
					},
					// Note: Fonts are excluded from service worker caching to avoid CORS issues
					// They will load directly from Google's CDN without service worker interception
					{
						urlPattern: /^https:\/\/churchflow-api\.ailabsafrica\.com\/api\/.*/i,
						handler: 'NetworkFirst',
						options: {
							cacheName: 'api-cache',
							expiration: {
								maxEntries: 100,
								maxAgeSeconds: 60 * 60 * 24, // 24 hours
							},
							cacheableResponse: {
								statuses: [0, 200],
							},
							networkTimeoutSeconds: 10,
						},
					},
					{
						urlPattern: /^https:\/\/unpkg\.com\/leaflet.*/i,
						handler: 'CacheFirst',
						options: {
							cacheName: 'leaflet-cache',
							expiration: {
								maxEntries: 10,
								maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
							},
							cacheableResponse: {
								statuses: [0, 200],
							},
						},
					},
				],
			},
			devOptions: {
				enabled: true,
			},
		}),
	],
	resolve: {
		alias: {
			'@': path.resolve(__dirname, './src'),
			'@kasaai/shared-frontend': path.resolve(__dirname, '../../shared/frontend'),
		},
		dedupe: ['react', 'react-dom'],
	},
	optimizeDeps: {
		include: ['react', 'react-dom', 'react/jsx-runtime'],
	},
	build: {
		commonjsOptions: {
			include: [/node_modules/, /shared/],
		},
		// Code splitting for better performance
		cssCodeSplit: true,
		rollupOptions: {
			output: {
				manualChunks: {
					// Core vendor libraries (loaded on every page)
					'vendor-react': ['react', 'react-dom', 'react-router-dom'],
					// UI libraries (loaded frequently)
					'vendor-ui': ['lucide-react', 'framer-motion'],
					// Admin-specific libraries (lazy loaded)
					'admin-stripe': ['@stripe/react-stripe-js', '@stripe/stripe-js'],
					// Phone input library (only on registration)
					'vendor-phone': ['react-phone-number-input'],
				},
			},
		},
	},
	server: {
		port: 5173,
		host: true,
	},
})
