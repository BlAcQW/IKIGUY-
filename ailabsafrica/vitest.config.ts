import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

export default defineConfig({
	plugins: [react()],
	test: {
		globals: true,
		environment: 'jsdom',
		setupFiles: ['./src/test-setup.ts'],
		css: true,
		// Add test timeout and retry settings
		testTimeout: 15000,
		hookTimeout: 15000,
		// Disable console output during tests to reduce noise
		silent: false,
		// Add coverage settings
		coverage: {
			provider: 'v8',
			reporter: ['text', 'json', 'html'],
			exclude: [
				'node_modules/',
				'src/test-setup.ts',
				'**/*.d.ts',
				'**/*.config.*',
			],
		},
		// Add test isolation and environment settings
		isolate: true,
		pool: 'forks',
		poolOptions: {
			forks: {
				singleFork: true,
			},
		},
		// Environment setup for React 18 compatibility
		environmentOptions: {
			jsdom: {
				resources: 'usable',
				runScripts: 'dangerously',
			},
		},
	},
	resolve: {
		alias: {
			'@': path.resolve(__dirname, './src'),
		},
	},
});

