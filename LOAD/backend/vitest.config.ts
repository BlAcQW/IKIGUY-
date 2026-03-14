import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    include: ['src/**/*.test.ts', 'tests/e2e/**/*.test.ts'],
    setupFiles: ['tests/setup.ts'],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.ts'],
      exclude: [
        'src/telephony/**',
        'src/websocket/**',
        'src/webrtc/**',
        'src/index.ts',
        'src/config/**',
        'src/database/**',
        'src/modules/voices/**',
        'src/providers/stt/types.ts',
        'src/providers/llm/types.ts',
        'src/providers/tts/types.ts',
        'src/providers/tts/cartesia.ts',
        'src/providers/tts/deepgram.ts',
        'src/providers/tts/elevenlabs.ts',
        'src/providers/stt/deepgram.ts',
        'src/types/**',
        'src/**/index.ts',
        'src/**/*.test.ts',
      ],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 75,
        lines: 80,
      },
    },
  },
});
