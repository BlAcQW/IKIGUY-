/**
 * E2E: Auth flow — Register → Login → Refresh → Logout
 *
 * These tests use the Fastify app with mocked Prisma (no real DB),
 * verifying the full route → service → response chain.
 */
import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../helpers/prisma-mock.js';
import { buildUser, buildOrganization, buildRefreshToken } from '../helpers/factories.js';
import type { FastifyInstance } from 'fastify';

let prismaMock: PrismaMock;

vi.mock('../../src/database/client.js', () => ({
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
  if (!app) {
    const { createTestApp } = await import('../helpers/app.js');
    app = await createTestApp();
  }
});

afterAll(async () => {
  if (app) await app.close();
});

describe('Auth E2E Flow', () => {
  it('register → returns token + refreshToken', async () => {
    const org = buildOrganization({ name: 'New Org' });
    const user = buildUser({ email: 'new@test.com', name: 'New', organizationId: org.id });

    prismaMock.user.findUnique.mockResolvedValue(null);
    prismaMock.organization.create.mockResolvedValue(org);
    prismaMock.user.create.mockResolvedValue(user);
    prismaMock.refreshToken.create.mockResolvedValue(buildRefreshToken({ userId: user.id, organizationId: org.id }));

    const res = await app.inject({
      method: 'POST',
      url: '/api/auth/register',
      payload: { email: 'new@test.com', password: 'password123', name: 'New', organizationName: 'New Org' },
    });

    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.data.token).toBeDefined();
    expect(body.data.refreshToken).toBeDefined();
    expect(body.data.user.email).toBe('new@test.com');
  });

  it('login → returns token + refreshToken', async () => {
    const org = buildOrganization();
    const user = { ...buildUser({ organizationId: org.id }), organization: org };

    prismaMock.user.findUnique.mockResolvedValue(user);
    vi.mocked(bcrypt.compare).mockResolvedValue(true as never);
    prismaMock.refreshToken.create.mockResolvedValue(buildRefreshToken());

    const res = await app.inject({
      method: 'POST',
      url: '/api/auth/login',
      payload: { email: user.email, password: 'password123' },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.data.token).toBeDefined();
    expect(body.data.refreshToken).toBeDefined();
  });

  it('refresh → rotates token pair', async () => {
    const user = buildUser({ id: 'u-1' });
    const org = buildOrganization({ id: 'o-1' });
    const rt = buildRefreshToken({ userId: user.id, organizationId: org.id });

    prismaMock.refreshToken.findMany.mockResolvedValue([
      {
        ...rt,
        user: { id: user.id, email: user.email, name: user.name, role: user.role },
        organization: { id: org.id, name: org.name, slug: org.slug },
      },
    ]);
    vi.mocked(bcrypt.compare).mockResolvedValue(true as never);
    prismaMock.refreshToken.update.mockResolvedValue({ ...rt, revokedAt: new Date() });
    prismaMock.refreshToken.create.mockResolvedValue(buildRefreshToken());

    const res = await app.inject({
      method: 'POST',
      url: '/api/auth/refresh',
      payload: { refreshToken: 'raw-token' },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.data.token).toBeDefined();
    expect(body.data.refreshToken).toBeDefined();
  });

  it('logout → revokes all refresh tokens', async () => {
    const token = app.jwt.sign({ userId: 'u-1', organizationId: 'o-1', role: 'OWNER' });
    prismaMock.refreshToken.updateMany.mockResolvedValue({ count: 2 });

    const res = await app.inject({
      method: 'POST',
      url: '/api/auth/logout',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    expect(prismaMock.refreshToken.updateMany).toHaveBeenCalledWith({
      where: { userId: 'u-1', revokedAt: null },
      data: { revokedAt: expect.any(Date) },
    });
  });

  it('me → returns user info with valid JWT', async () => {
    const token = app.jwt.sign({ userId: 'u-1', organizationId: 'o-1', role: 'ADMIN' });

    const res = await app.inject({
      method: 'GET',
      url: '/api/auth/me',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().data.userId).toBe('u-1');
    expect(res.json().data.role).toBe('ADMIN');
  });
});
