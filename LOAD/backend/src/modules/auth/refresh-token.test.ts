import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildUser, buildOrganization, buildRefreshToken } from '../../../tests/helpers/factories.js';

let prismaMock: PrismaMock;

vi.mock('../../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
}));

vi.mock('bcryptjs', () => ({
  default: {
    hash: vi.fn().mockResolvedValue('$2b$12$hashed'),
    compare: vi.fn(),
  },
}));

import bcrypt from 'bcryptjs';
import { createRefreshToken, rotateRefreshToken, revokeAllRefreshTokens } from './service.js';

beforeEach(() => {
  prismaMock = createPrismaMock();
  vi.clearAllMocks();
});

describe('createRefreshToken', () => {
  it('creates a refresh token and returns the raw token', async () => {
    prismaMock.refreshToken.create.mockResolvedValue(buildRefreshToken());

    const rawToken = await createRefreshToken('user-1', 'org-1');

    expect(rawToken).toBeDefined();
    expect(typeof rawToken).toBe('string');
    expect(rawToken.length).toBeGreaterThan(0);
    expect(prismaMock.refreshToken.create).toHaveBeenCalledWith({
      data: expect.objectContaining({
        userId: 'user-1',
        organizationId: 'org-1',
        tokenHash: '$2b$12$hashed',
      }),
    });
  });

  it('sets expiration date in the future', async () => {
    prismaMock.refreshToken.create.mockResolvedValue(buildRefreshToken());

    await createRefreshToken('user-1', 'org-1');

    const createCall = prismaMock.refreshToken.create.mock.calls[0][0];
    const expiresAt = createCall.data.expiresAt as Date;
    expect(expiresAt.getTime()).toBeGreaterThan(Date.now());
  });
});

describe('rotateRefreshToken', () => {
  it('revokes the old token and issues a new one', async () => {
    const user = buildUser({ id: 'user-1' });
    const org = buildOrganization({ id: 'org-1' });
    const existingToken = buildRefreshToken({
      id: 'rt-1',
      userId: user.id,
      organizationId: org.id,
    });

    prismaMock.refreshToken.findMany.mockResolvedValue([
      { ...existingToken, user: { id: user.id, email: user.email, name: user.name, role: user.role }, organization: { id: org.id, name: org.name, slug: org.slug } },
    ]);
    vi.mocked(bcrypt.compare).mockResolvedValue(true as never);
    prismaMock.refreshToken.update.mockResolvedValue({ ...existingToken, revokedAt: new Date() });
    prismaMock.refreshToken.create.mockResolvedValue(buildRefreshToken());

    const result = await rotateRefreshToken('raw-token-value');

    expect(result.refreshToken).toBeDefined();
    expect(result.user.id).toBe(user.id);
    expect(result.organization.id).toBe(org.id);
    expect(prismaMock.refreshToken.update).toHaveBeenCalledWith({
      where: { id: 'rt-1' },
      data: { revokedAt: expect.any(Date) },
    });
  });

  it('throws 401 when no matching token is found', async () => {
    prismaMock.refreshToken.findMany.mockResolvedValue([]);

    await expect(rotateRefreshToken('invalid-token')).rejects.toThrow('Invalid or expired refresh token');
  });

  it('revokes all tokens when a revoked token is reused (stolen token detection)', async () => {
    const revokedToken = buildRefreshToken({
      id: 'rt-revoked',
      userId: 'user-1',
      revokedAt: new Date(),
    });

    // No active tokens
    prismaMock.refreshToken.findMany
      .mockResolvedValueOnce([]) // Active tokens query
      .mockResolvedValueOnce([revokedToken]); // Revoked tokens query

    vi.mocked(bcrypt.compare).mockResolvedValue(true as never);
    prismaMock.refreshToken.updateMany.mockResolvedValue({ count: 3 });

    await expect(rotateRefreshToken('stolen-token')).rejects.toThrow('Token reuse detected');
    expect(prismaMock.refreshToken.updateMany).toHaveBeenCalledWith({
      where: { userId: 'user-1', revokedAt: null },
      data: { revokedAt: expect.any(Date) },
    });
  });

  it('does not match expired tokens', async () => {
    prismaMock.refreshToken.findMany
      .mockResolvedValueOnce([]) // Active tokens - empty because expired
      .mockResolvedValueOnce([]); // Revoked tokens - also empty

    vi.mocked(bcrypt.compare).mockResolvedValue(false as never);

    await expect(rotateRefreshToken('expired-token')).rejects.toThrow('Invalid or expired refresh token');
  });
});

describe('revokeAllRefreshTokens', () => {
  it('revokes all tokens for a user', async () => {
    prismaMock.refreshToken.updateMany.mockResolvedValue({ count: 5 });

    await revokeAllRefreshTokens('user-1');

    expect(prismaMock.refreshToken.updateMany).toHaveBeenCalledWith({
      where: { userId: 'user-1', revokedAt: null },
      data: { revokedAt: expect.any(Date) },
    });
  });

  it('succeeds even when no tokens exist', async () => {
    prismaMock.refreshToken.updateMany.mockResolvedValue({ count: 0 });

    await expect(revokeAllRefreshTokens('user-no-tokens')).resolves.toBeUndefined();
  });
});
