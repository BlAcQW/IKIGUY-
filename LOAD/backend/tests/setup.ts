import { afterEach, vi } from 'vitest';

// Set required env vars before any module imports
process.env.NODE_ENV = 'test';
process.env.DATABASE_URL = 'postgresql://test:test@localhost:5432/test_db';
process.env.JWT_SECRET = 'test-secret-key-minimum-16-chars';
process.env.JWT_EXPIRES_IN = '15m';
process.env.REDIS_URL = 'redis://localhost:6379';
process.env.FRONTEND_URL = 'http://localhost:5173';
process.env.API_URL = 'http://localhost:3000';
process.env.WEBHOOK_SECRET = 'test-webhook-secret';

afterEach(() => {
  vi.clearAllMocks();
});
