import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    include: ['tests/integration/**/*.integration.test.ts'],
    setupFiles: ['tests/setup-integration.ts'],
    testTimeout: 30_000,
    hookTimeout: 15_000,
    pool: 'forks',
    fileParallelism: false,
  },
});
