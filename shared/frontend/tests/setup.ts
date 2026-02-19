/**
 * Test Setup
 * Global test configuration and polyfills
 */

import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock fetch API for tests
global.fetch = vi.fn();

// Mock import.meta.env
Object.defineProperty(global, 'import', {
  value: {
    meta: {
      env: {
        VITE_API_URL: 'http://localhost:30027',
      },
    },
  },
  writable: true,
});
