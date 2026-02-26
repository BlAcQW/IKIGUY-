/**
 * E2E: Assistant CRUD lifecycle
 *
 * Create → List → Get → Update → Delete
 */
import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../helpers/prisma-mock.js';
import { buildAssistant } from '../helpers/factories.js';
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

let app: FastifyInstance;

function generateToken(payload?: { userId?: string; organizationId?: string; role?: string }) {
  return app.jwt.sign({
    userId: payload?.userId ?? 'user-1',
    organizationId: payload?.organizationId ?? 'org-1',
    role: payload?.role ?? 'OWNER',
  });
}

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

describe('Assistant CRUD E2E', () => {
  const orgId = 'org-1';

  it('creates an assistant', async () => {
    const assistant = buildAssistant({ organizationId: orgId, name: 'Sales Agent' });
    prismaMock.assistant.create.mockResolvedValue(assistant);

    const res = await app.inject({
      method: 'POST',
      url: '/api/assistants',
      headers: { authorization: `Bearer ${generateToken()}` },
      payload: { name: 'Sales Agent' },
    });

    expect(res.statusCode).toBe(201);
    expect(res.json().data.name).toBe('Sales Agent');
  });

  it('lists assistants', async () => {
    const assistants = [
      buildAssistant({ organizationId: orgId, name: 'Agent A' }),
      buildAssistant({ organizationId: orgId, name: 'Agent B' }),
    ];
    prismaMock.assistant.findMany.mockResolvedValue(assistants);
    prismaMock.assistant.count.mockResolvedValue(2);

    const res = await app.inject({
      method: 'GET',
      url: '/api/assistants',
      headers: { authorization: `Bearer ${generateToken()}` },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().data).toHaveLength(2);
  });

  it('gets a single assistant', async () => {
    const assistant = buildAssistant({ id: 'ast-1', organizationId: orgId });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);

    const res = await app.inject({
      method: 'GET',
      url: '/api/assistants/ast-1',
      headers: { authorization: `Bearer ${generateToken()}` },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().data.id).toBe('ast-1');
  });

  it('updates an assistant', async () => {
    const original = buildAssistant({ id: 'ast-1', organizationId: orgId, name: 'Old Name' });
    const updated = { ...original, name: 'New Name' };
    prismaMock.assistant.findFirst.mockResolvedValue(original);
    prismaMock.assistant.update.mockResolvedValue(updated);

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/assistants/ast-1',
      headers: { authorization: `Bearer ${generateToken()}` },
      payload: { name: 'New Name' },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().data.name).toBe('New Name');
  });

  it('deletes an assistant', async () => {
    const assistant = buildAssistant({ id: 'ast-1', organizationId: orgId });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.assistant.delete.mockResolvedValue(assistant);

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/assistants/ast-1',
      headers: { authorization: `Bearer ${generateToken()}` },
    });

    expect(res.statusCode).toBe(204);
  });

  it('returns 404 for non-existent assistant', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue(null);

    const res = await app.inject({
      method: 'GET',
      url: '/api/assistants/nonexistent',
      headers: { authorization: `Bearer ${generateToken()}` },
    });

    expect(res.statusCode).toBe(404);
  });

  it('returns 401 without authentication', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/assistants',
    });

    expect(res.statusCode).toBe(401);
  });
});
