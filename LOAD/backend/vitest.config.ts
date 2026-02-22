import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
    setupFiles: ['tests/setup.ts'],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.ts'],
      exclude: [
        'src/telephony/**',
        'src/websocket/**',
        'src/index.ts',
        'src/config/**',
        'src/database/**',
        'src/modules/campaigns/**',
        'src/modules/phone-numbers/**',
        'src/modules/squads/**',
        'src/modules/tools/**',
        'src/modules/webhooks/**',
        'src/**/*.test.ts',
      ],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
    },
  },
});
