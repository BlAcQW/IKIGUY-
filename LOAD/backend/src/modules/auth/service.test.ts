import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildUser, buildOrganization, buildApiKey } from '../../../tests/helpers/factories.js';

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
import { registerUser, loginUser, createApiKey, listApiKeys, revokeApiKey } from './service.js';

beforeEach(() => {
  prismaMock = createPrismaMock();
});

describe('registerUser', () => {
  const input = {
    email: 'new@example.com',
    password: 'securepass123',
    name: 'New User',
    organizationName: 'New Org',
  };

  it('creates an organization and user', async () => {
    const org = buildOrganization({ name: 'New Org' });
    const user = buildUser({ email: 'new@example.com', name: 'New User', organizationId: org.id });

    prismaMock.user.findUnique.mockResolvedValue(null);
    prismaMock.organization.create.mockResolvedValue(org);
    prismaMock.user.create.mockResolvedValue(user);

    const result = await registerUser(input);

    expect(prismaMock.organization.create).toHaveBeenCalledOnce();
    expect(prismaMock.user.create).toHaveBeenCalledOnce();
    expect(result.user.email).toBe('new@example.com');
    expect(result.organization.name).toBe('New Org');
  });

  it('hashes the password before storing', async () => {
    prismaMock.user.findUnique.mockResolvedValue(null);
    prismaMock.organization.create.mockResolvedValue(buildOrganization());
    prismaMock.user.create.mockResolvedValue(buildUser());

    await registerUser(input);

    expect(bcrypt.hash).toHaveBeenCalledWith('securepass123', 12);
    expect(prismaMock.user.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ passwordHash: '$2b$12$hashed' }),
      })
    );
  });

  it('returns sanitized user without passwordHash', async () => {
    prismaMock.user.findUnique.mockResolvedValue(null);
    prismaMock.organization.create.mockResolvedValue(buildOrganization());
    prismaMock.user.create.mockResolvedValue(buildUser());

    const result = await registerUser(input);

    expect(result.user).toHaveProperty('id');
    expect(result.user).toHaveProperty('email');
    expect(result.user).toHaveProperty('name');
    expect(result.user).toHaveProperty('role');
    expect(result.user).not.toHaveProperty('passwordHash');
  });

  it('throws 409 on duplicate email', async () => {
    prismaMock.user.findUnique.mockResolvedValue(buildUser());

    await expect(registerUser(input)).rejects.toThrow('Email already registered');
    await expect(registerUser(input)).rejects.toMatchObject({ statusCode: 409 });
  });

  it('generates a slug from organization name', async () => {
    prismaMock.user.findUnique.mockResolvedValue(null);
    prismaMock.organization.create.mockResolvedValue(buildOrganization());
    prismaMock.user.create.mockResolvedValue(buildUser());

    await registerUser({ ...input, organizationName: 'My Cool Org!' });

    expect(prismaMock.organization.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          slug: expect.stringMatching(/^my-cool-org-[0-9a-f]{6}$/),
        }),
      })
    );
  });

  it('assigns OWNER role to the first user', async () => {
    prismaMock.user.findUnique.mockResolvedValue(null);
    prismaMock.organization.create.mockResolvedValue(buildOrganization());
    prismaMock.user.create.mockResolvedValue(buildUser());

    await registerUser(input);

    expect(prismaMock.user.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ role: 'OWNER' }),
      })
    );
  });
});

describe('loginUser', () => {
  const input = { email: 'user@example.com', password: 'securepass123' };

  it('returns user and organization on valid credentials', async () => {
    const org = buildOrganization();
    const user = { ...buildUser({ organizationId: org.id }), organization: org };

    prismaMock.user.findUnique.mockResolvedValue(user);
    vi.mocked(bcrypt.compare).mockResolvedValue(true as never);

    const result = await loginUser(input);

    expect(result.user.email).toBe('test@example.com');
    expect(result.organization.id).toBe(org.id);
  });

  it('throws 401 when user is not found', async () => {
    prismaMock.user.findUnique.mockResolvedValue(null);

    await expect(loginUser(input)).rejects.toThrow('Invalid email or password');
    await expect(loginUser(input)).rejects.toMatchObject({ statusCode: 401 });
  });

  it('throws 401 on incorrect password', async () => {
    const org = buildOrganization();
    const user = { ...buildUser({ organizationId: org.id }), organization: org };

    prismaMock.user.findUnique.mockResolvedValue(user);
    vi.mocked(bcrypt.compare).mockResolvedValue(false as never);

    await expect(loginUser(input)).rejects.toThrow('Invalid email or password');
    await expect(loginUser(input)).rejects.toMatchObject({ statusCode: 401 });
  });

  it('returns sanitized user without passwordHash', async () => {
    const org = buildOrganization();
    const user = { ...buildUser({ organizationId: org.id }), organization: org };

    prismaMock.user.findUnique.mockResolvedValue(user);
    vi.mocked(bcrypt.compare).mockResolvedValue(true as never);

    const result = await loginUser(input);

    expect(result.user).not.toHaveProperty('passwordHash');
  });
});

describe('createApiKey', () => {
  const userId = 'user-1';
  const orgId = 'org-1';

  it('generates a key with load_ prefix', async () => {
    prismaMock.apiKey.create.mockResolvedValue(buildApiKey());

    const result = await createApiKey({ name: 'My Key' }, userId, orgId);

    expect(result.key).toMatch(/^load_[0-9a-f]{64}$/);
  });

  it('stores the hash, not the raw key', async () => {
    prismaMock.apiKey.create.mockResolvedValue(buildApiKey());

    await createApiKey({ name: 'My Key' }, userId, orgId);

    expect(prismaMock.apiKey.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          keyHash: '$2b$12$hashed',
        }),
      })
    );
  });

  it('returns the raw key exactly once', async () => {
    prismaMock.apiKey.create.mockResolvedValue(buildApiKey());

    const result = await createApiKey({ name: 'My Key' }, userId, orgId);

    expect(result).toHaveProperty('key');
    expect(result).toHaveProperty('id');
    expect(result).toHaveProperty('prefix');
    expect(result).not.toHaveProperty('keyHash');
  });

  it('handles expiresAt when provided', async () => {
    prismaMock.apiKey.create.mockResolvedValue(buildApiKey({ expiresAt: new Date('2025-12-31') }));

    await createApiKey({ name: 'My Key', expiresAt: '2025-12-31T00:00:00.000Z' }, userId, orgId);

    expect(prismaMock.apiKey.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          expiresAt: new Date('2025-12-31T00:00:00.000Z'),
        }),
      })
    );
  });

  it('sets expiresAt to null when not provided', async () => {
    prismaMock.apiKey.create.mockResolvedValue(buildApiKey());

    await createApiKey({ name: 'My Key' }, userId, orgId);

    expect(prismaMock.apiKey.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ expiresAt: null }),
      })
    );
  });

  it('stores the prefix (load_ + 8 hex chars)', async () => {
    prismaMock.apiKey.create.mockResolvedValue(buildApiKey());

    await createApiKey({ name: 'My Key' }, userId, orgId);

    expect(prismaMock.apiKey.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          prefix: expect.stringMatching(/^load_[0-9a-f]{8}$/),
        }),
      })
    );
  });
});

describe('listApiKeys', () => {
  it('returns keys for the organization ordered by createdAt desc', async () => {
    const keys = [
      buildApiKey({ name: 'Key 2', createdAt: new Date('2024-02-01') }),
      buildApiKey({ name: 'Key 1', createdAt: new Date('2024-01-01') }),
    ];
    prismaMock.apiKey.findMany.mockResolvedValue(keys);

    const result = await listApiKeys('org-1');

    expect(result).toHaveLength(2);
    expect(prismaMock.apiKey.findMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { organizationId: 'org-1' },
        orderBy: { createdAt: 'desc' },
      })
    );
  });
});

describe('revokeApiKey', () => {
  it('deletes the API key', async () => {
    prismaMock.apiKey.findFirst.mockResolvedValue(buildApiKey({ id: 'key-1' }));
    prismaMock.apiKey.delete.mockResolvedValue(buildApiKey({ id: 'key-1' }));

    await revokeApiKey('key-1', 'org-1');

    expect(prismaMock.apiKey.delete).toHaveBeenCalledWith({ where: { id: 'key-1' } });
  });

  it('throws 404 if key not found', async () => {
    prismaMock.apiKey.findFirst.mockResolvedValue(null);

    await expect(revokeApiKey('bad-id', 'org-1')).rejects.toThrow('API key not found');
    await expect(revokeApiKey('bad-id', 'org-1')).rejects.toMatchObject({ statusCode: 404 });
  });

  it('scopes the lookup to the organization', async () => {
    prismaMock.apiKey.findFirst.mockResolvedValue(null);

    await expect(revokeApiKey('key-1', 'org-1')).rejects.toThrow();

    expect(prismaMock.apiKey.findFirst).toHaveBeenCalledWith({
      where: { id: 'key-1', organizationId: 'org-1' },
    });
  });
});
