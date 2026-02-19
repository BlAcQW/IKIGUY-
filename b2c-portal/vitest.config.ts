import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

export default defineConfig({
	plugins: [react()],
	test: {
		environment: 'jsdom',
		setupFiles: ['./src/test/setup.ts'],
		globals: true,
		coverage: {
			provider: 'v8',
			reporter: ['text', 'json', 'html', 'lcov'],
			exclude: [
				'node_modules/',
				'src/test/',
				'**/*.d.ts',
				'**/*.config.*',
				'**/coverage/**',
				'**/dist/**',
				'**/build/**',
				'**/*.test.*',
				'**/*.spec.*',
				'**/__tests__/**',
				'**/__mocks__/**',
			],
			thresholds: {
				global: {
					branches: 80,
					functions: 80,
					lines: 80,
					statements: 80,
				},
			},
		},
		include: [
			'src/**/*.{test,spec}.{js,jsx,ts,tsx}',
			'src/**/__tests__/**/*.{js,jsx,ts,tsx}',
		],
                exclude: [
                        'node_modules/',
                        'dist/',
                        'build/',
                        'coverage/',
                        'src/test/**',
                        'src/hooks/__tests__/useIndustryModules.test.ts',
                        'src/test/hooks/useCoreApi.test.ts',
                        'src/test/pages/Assistants.test.tsx',
                        'src/test/pages/Campaigns.test.tsx',
                ],
		testTimeout: 10000,
		hookTimeout: 10000,
	},
	resolve: {
		alias: {
			'@': path.resolve(__dirname, './src'),
		},
	},
}) 