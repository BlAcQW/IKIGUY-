import { describe, it, expect } from 'vitest';
import { registerSchema, loginSchema, createApiKeySchema } from './schemas.js';

describe('registerSchema', () => {
  it('validates a correct registration input', () => {
    const input = {
      email: 'user@example.com',
      password: 'securepass123',
      name: 'John Doe',
      organizationName: 'Acme Corp',
    };
    const result = registerSchema.parse(input);
    expect(result).toEqual(input);
  });

  it('rejects an invalid email', () => {
    const input = {
      email: 'not-an-email',
      password: 'securepass123',
      name: 'John Doe',
      organizationName: 'Acme Corp',
    };
    expect(() => registerSchema.parse(input)).toThrow('Invalid email');
  });

  it('rejects a short password', () => {
    const input = {
      email: 'user@example.com',
      password: 'short',
      name: 'John Doe',
      organizationName: 'Acme Corp',
    };
    expect(() => registerSchema.parse(input)).toThrow('at least 8 characters');
  });

  it('rejects a missing name', () => {
    const input = {
      email: 'user@example.com',
      password: 'securepass123',
      name: '',
      organizationName: 'Acme Corp',
    };
    expect(() => registerSchema.parse(input)).toThrow('Name is required');
  });

  it('rejects a missing organization name', () => {
    const input = {
      email: 'user@example.com',
      password: 'securepass123',
      name: 'John Doe',
      organizationName: '',
    };
    expect(() => registerSchema.parse(input)).toThrow('Organization name is required');
  });
});

describe('loginSchema', () => {
  it('validates a correct login input', () => {
    const input = { email: 'user@example.com', password: 'securepass123' };
    const result = loginSchema.parse(input);
    expect(result).toEqual(input);
  });

  it('rejects an invalid email', () => {
    expect(() => loginSchema.parse({ email: 'bad', password: 'pass' })).toThrow('Invalid email');
  });

  it('rejects an empty password', () => {
    expect(() => loginSchema.parse({ email: 'user@example.com', password: '' })).toThrow('Password is required');
  });
});

describe('createApiKeySchema', () => {
  it('validates a correct input with name only', () => {
    const result = createApiKeySchema.parse({ name: 'My Key' });
    expect(result).toEqual({ name: 'My Key' });
  });

  it('validates input with optional expiresAt', () => {
    const input = { name: 'My Key', expiresAt: '2025-12-31T00:00:00.000Z' };
    const result = createApiKeySchema.parse(input);
    expect(result.expiresAt).toBe('2025-12-31T00:00:00.000Z');
  });

  it('rejects a missing name', () => {
    expect(() => createApiKeySchema.parse({ name: '' })).toThrow('API key name is required');
  });
});
