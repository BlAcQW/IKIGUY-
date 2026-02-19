import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";
import { VitePWA } from 'vite-plugin-pwa';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
	server: {
		host: "::",
		port: 8080,
	},
	plugins: [
		react(),
		mode === "development" && componentTagger(),
		VitePWA({
			registerType: 'prompt',
			includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
			manifest: {
				name: 'FreshManna - Daily Devotionals',
				short_name: 'FreshManna',
				description: 'Empower your faith with daily devotionals and spiritual content',
				version: '1.0.6',  // Increment this to force service worker update
				theme_color: '#FF6B35',  // Orange (North Point style)
				background_color: '#FFFFFF',  // White
				display: 'standalone',
				orientation: 'portrait-primary',
				scope: '/',
				start_url: '/',
				categories: ['lifestyle', 'education', 'spirituality'],
				icons: [
					{ src: '/icons/icon-72x72.png', sizes: '72x72', type: 'image/png' },
					{ src: '/icons/icon-96x96.png', sizes: '96x96', type: 'image/png' },
					{ src: '/icons/icon-128x128.png', sizes: '128x128', type: 'image/png' },
					{ src: '/icons/icon-144x144.png', sizes: '144x144', type: 'image/png' },
					{ src: '/icons/icon-152x152.png', sizes: '152x152', type: 'image/png' },
					{ src: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
					{ src: '/icons/icon-384x384.png', sizes: '384x384', type: 'image/png' },
					{ src: '/icons/icon-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' }
				],
				shortcuts: [
					{
						name: "Today's Devotional",
						short_name: "Today",
						url: "/feed",
						icons: [{ src: '/icons/shortcut-today-96x96.png', sizes: '96x96' }]
					},
					{
						name: "My Bookmarks",
						short_name: "Bookmarks",
						url: "/profile?tab=bookmarks",
						icons: [{ src: '/icons/shortcut-bookmarks-96x96.png', sizes: '96x96' }]
					},
					{
						name: "Compose",
						short_name: "Compose",
						url: "/dashboard/compose",
						icons: [{ src: '/icons/shortcut-compose-96x96.png', sizes: '96x96' }]
					}
				]
			},
			workbox: {
				skipWaiting: true,
				clientsClaim: true,
				cleanupOutdatedCaches: true,
				globPatterns: ['**/*.{js,css,html,ico,png,woff2,woff}'],
				// Exclude shortcut SVG files from precaching (they have restrictive permissions)
				globIgnores: ['**/icons/shortcut-*.svg'],
				// Include push notification handler
				importScripts: ['/sw-push.js'],
				runtimeCaching: [
					{
						urlPattern: /^https:\/\/freshmanna-api\.ailabsafrica\.com\/api\/v1\/devotionals/,
						handler: 'NetworkFirst',
						options: {
							cacheName: 'devotionals-api-cache',
							expiration: { maxEntries: 100, maxAgeSeconds: 86400 },
							cacheableResponse: { statuses: [0, 200] }
						}
					},
					{
						urlPattern: /^https:\/\/freshmanna-api\.ailabsafrica\.com\/api\/v1\/(auth|users)/,
						handler: 'NetworkFirst',
						options: {
							cacheName: 'user-api-cache',
							expiration: { maxEntries: 50, maxAgeSeconds: 3600 }
						}
					},
					{
						urlPattern: /^https:\/\/freshmanna-api\.ailabsafrica\.com\/storage\/audio\//,
						handler: 'CacheFirst',
						options: {
							cacheName: 'audio-cache',
							expiration: { maxEntries: 50, maxAgeSeconds: 2592000 },
							cacheableResponse: { statuses: [0, 200] }
						}
					},
					{
						urlPattern: /\.(png|jpg|jpeg|svg|gif|webp)$/,
						handler: 'CacheFirst',
						options: {
							cacheName: 'images-cache',
							expiration: { maxEntries: 100, maxAgeSeconds: 604800 }
						}
					}
				],
				navigateFallback: '/index.html',
				navigateFallbackDenylist: [/^\/api/]
			},
			devOptions: {
				enabled: true,
				type: 'module'
			}
		})
	].filter(Boolean),
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "./src"),
		},
	},
}));
