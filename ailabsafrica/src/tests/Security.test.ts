import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { RateLimiter, InputSanitizer, CSRFProtection } from '@/utils/security';
import { webcrypto } from 'node:crypto';

// Ensure crypto is available for token generation
if (!globalThis.crypto) {
  // @ts-expect-error: assign webcrypto to globalThis for tests
  globalThis.crypto = webcrypto;
}

describe('RateLimiter', () => {
  const config = { windowMs: 1000, maxRequests: 2, message: 'Too many' };

  beforeEach(() => {
    RateLimiter.resetLimit('test');
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    RateLimiter.resetLimit('test');
  });

  it('allows requests within limit and blocks after exceeding', () => {
    let result = RateLimiter.checkLimit('test', config);
    expect(result.allowed).toBe(true);
    result = RateLimiter.checkLimit('test', config);
    expect(result.allowed).toBe(true);
    result = RateLimiter.checkLimit('test', config);
    expect(result.allowed).toBe(false);
  });

  it('resets count after window expires', () => {
    RateLimiter.checkLimit('test', config);
    vi.advanceTimersByTime(1001);
    const result = RateLimiter.checkLimit('test', config);
    expect(result.allowed).toBe(true);
  });
});

describe('InputSanitizer', () => {
  it('sanitizes strings by removing HTML tags and scripts', () => {
    const input = '<script>alert(1)</script>Hello';
    const sanitized = InputSanitizer.sanitizeString(input);
    expect(sanitized).toBe('scriptalert(1)/scriptHello');
  });

  it('sanitizes HTML by stripping script tags', () => {
    const input = '<div>Test</div><script>alert(1)</script>';
    const sanitized = InputSanitizer.sanitizeHTML(input);
    expect(sanitized).toBe('<div>Test</div>');
  });

  it('sanitizes SQL queries by removing keywords', () => {
    const input = 'SELECT * FROM users; DROP TABLE users;';
    const sanitized = InputSanitizer.sanitizeSQL(input);
    expect(sanitized).not.toMatch(/SELECT|DROP/);
  });
});

describe('CSRFProtection', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('generates and validates a token', () => {
    const token = CSRFProtection.generateToken('session');
    expect(typeof token).toBe('string');
    expect(CSRFProtection.validateToken('session', token)).toBe(true);
  });

  it('rejects invalid tokens', () => {
    CSRFProtection.generateToken('session');
    expect(CSRFProtection.validateToken('session', 'wrong')).toBe(false);
  });

  it('expires tokens after time window', () => {
    const token = CSRFProtection.generateToken('session');
    vi.advanceTimersByTime(30 * 60 * 1000 + 1);
    expect(CSRFProtection.validateToken('session', token)).toBe(false);
  });
});
