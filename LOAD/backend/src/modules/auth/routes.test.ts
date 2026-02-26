import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildUser, buildOrganization, buildApiKey } from '../../../tests/helpers/factories.js';
import type { FastifyInstance } from 'fastify';

let prismaMock: PrismaMock;

vi.mock('../../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
  connectDatabase: vi.fn(),
  disconnectDatabase: vi.fn(),
}));

vi.mock('bcryptjs', () => ({
  default: {
    hash: vi.fn().mockResolvedValue('$2b$12$hashed'),
    compare: vi.fn(),
  },
}));

import bcrypt from 'bcryptjs';

let app: FastifyInstance;

beforeEach(async () => {
  prismaMock = createPrismaMock();
  // Lazy import to ensure mocks are in place
  if (!app) {
    const { createTestApp } = await import('../../../tests/helpers/app.js');
    app = await createTestApp();
  }
});

afterAll(async () => {
  if (app) await app.close();
});

function generateToken(payload?: { userId?: string; organizationId?: string; role?: string }) {
  return app.jwt.sign({
    userId: payload?.userId ?? 'test-user-id',
    organizationId: payload?.organizationId ?? 'test-org-id',
    role: payload?.role ?? 'OWNER',
  });
}

describe('POST /api/auth/register', () => {
  const validBody = {
    email: 'new@example.com',
    password: 'securepass123',
    name: 'New User',
    organizationName: 'New Org',
  };

  it('returns 201 with token on success', async () => {
    const org = buildOrganization({ name: 'New Org' });
    const user = buildUser({ email: 'new@example.com', name: 'New User', organizationId: org.id });

    prismaMock.user.findUnique.mockResolvedValue(null);
    prismaMock.organization.create.mockResolvedValue(org);
    prismaMock.user.create.mockResolvedValue(user);
    prismaMock.refreshToken.create.mockResolvedValue({ id: 'rt-1', tokenHash: 'hashed', userId: user.id, organizationId: org.id, expiresAt: new Date(), revokedAt: null, createdAt: new Date() });

    const res = await app.inject({
      method: 'POST',
      url: '/api/auth/register',
      payload: validBody,
    });

    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.token).toBeDefined();
    expect(body.data.refreshToken).toBeDefined();
    expect(body.data.user.email).toBe('new@example.com');
  });

  it('returns 400 for invalid email', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/auth/register',
      payload: { ...validBody, email: 'bad-email' },
    });

    expect(res.statusCode).toBe(400);
    expect(res.json().error.code).toBe('VALIDATION_ERROR');
  });

  it('returns 400 for short password', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/auth/register',
      payload: { ...validBody, password: 'short' },
    });

    expect(res.statusCode).toBe(400);
  });

  it('returns 400 for missing fields', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/auth/register',
      payload: { email: 'a@b.com' },
    });

    expect(res.statusCode).toBe(400);
  });

  it('returns 409 for duplicate email', async () => {
    prismaMock.user.findUnique.mockResolvedValue(buildUser());

    const res = await app.inject({
      method: 'POST',
      url: '/api/auth/register',
      payload: validBody,
    });

    expect(res.statusCode).toBe(409);
  });
});

describe('POST /api/auth/login', () => {
  it('returns 200 with token on valid credentials', async () => {
    const org = buildOrganization();
    const user = { ...buildUser({ organizationId: org.id }), organization: org };

    prismaMock.user.findUnique.mockResolvedValue(user);
    vi.mocked(bcrypt.compare).mockResolvedValue(true as never);
    prismaMock.refreshToken.create.mockResolvedValue({ id: 'rt-1', tokenHash: 'hashed', userId: user.id, organizationId: org.id, expiresAt: new Date(), revokedAt: null, createdAt: new Date() });

    const res = await app.inject({
      method: 'POST',
      url: '/api/auth/login',
      payload: { email: 'user@example.com', password: 'securepass123' },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.token).toBeDefined();
    expect(body.data.refreshToken).toBeDefined();
  });

  it('returns 400 for missing email', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/auth/login',
      payload: { password: 'securepass123' },
    });

    expect(res.statusCode).toBe(400);
  });

  it('returns 401 for invalid credentials', async () => {
    prismaMock.user.findUnique.mockResolvedValue(null);

    const res = await app.inject({
      method: 'POST',
      url: '/api/auth/login',
      payload: { email: 'user@example.com', password: 'wrong' },
    });

    expect(res.statusCode).toBe(401);
  });
});

describe('GET /api/auth/me', () => {
  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/auth/me',
    });

    expect(res.statusCode).toBe(401);
  });

  it('returns 200 with valid JWT', async () => {
    const token = generateToken({ userId: 'u1', organizationId: 'o1', role: 'OWNER' });

    const res = await app.inject({
      method: 'GET',
      url: '/api/auth/me',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.userId).toBe('u1');
    expect(body.data.organizationId).toBe('o1');
  });
});

describe('POST /api/api-keys', () => {
  it('returns 201 with auth', async () => {
    prismaMock.apiKey.create.mockResolvedValue(buildApiKey());
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/api-keys',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'My API Key' },
    });

    expect(res.statusCode).toBe(201);
    expect(res.json().success).toBe(true);
  });

  it('returns 401 without auth', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/api-keys',
      payload: { name: 'My API Key' },
    });

    expect(res.statusCode).toBe(401);
  });
});

describe('GET /api/api-keys', () => {
  it('returns 200 with auth', async () => {
    prismaMock.apiKey.findMany.mockResolvedValue([buildApiKey()]);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/api-keys',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().success).toBe(true);
    expect(res.json().data).toHaveLength(1);
  });

  it('returns 401 without auth', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/api-keys',
    });

    expect(res.statusCode).toBe(401);
  });
});

describe('DELETE /api/api-keys/:id', () => {
  it('returns 204 with auth', async () => {
    prismaMock.apiKey.findFirst.mockResolvedValue(buildApiKey({ id: 'key-1' }));
    prismaMock.apiKey.delete.mockResolvedValue(buildApiKey({ id: 'key-1' }));
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/api-keys/key-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(204);
  });

  it('returns 401 without auth', async () => {
    const res = await app.inject({
      method: 'DELETE',
      url: '/api/api-keys/key-1',
    });

    expect(res.statusCode).toBe(401);
  });

  it('returns 404 when key not found', async () => {
    prismaMock.apiKey.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/api-keys/nonexistent',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
  });
});
