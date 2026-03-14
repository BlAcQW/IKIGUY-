import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildAssistant } from '../../../tests/helpers/factories.js';
import type { FastifyInstance } from 'fastify';

let prismaMock: PrismaMock;

vi.mock('../../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
  connectDatabase: vi.fn(),
  disconnectDatabase: vi.fn(),
}));

vi.mock('bcrypt', () => ({
  default: {
    hash: vi.fn().mockResolvedValue('$2b$12$hashed'),
    compare: vi.fn(),
  },
}));

let app: FastifyInstance;

beforeEach(async () => {
  prismaMock = createPrismaMock();
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

describe('POST /api/assistants', () => {
  it('returns 201 with auth', async () => {
    const assistant = buildAssistant({ organizationId: 'test-org-id' });
    prismaMock.assistant.create.mockResolvedValue(assistant);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/assistants',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'Sales Bot' },
    });

    expect(res.statusCode).toBe(201);
    expect(res.json().success).toBe(true);
    expect(res.json().data).toBeDefined();
  });

  it('returns 401 without auth', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/assistants',
      payload: { name: 'Sales Bot' },
    });

    expect(res.statusCode).toBe(401);
  });

  it('returns 400 for missing name', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/assistants',
      headers: { authorization: `Bearer ${token}` },
      payload: {},
    });

    expect(res.statusCode).toBe(400);
  });
});

describe('GET /api/assistants', () => {
  it('returns 200 with paginated list', async () => {
    const assistants = [buildAssistant(), buildAssistant()];
    prismaMock.assistant.findMany.mockResolvedValue(assistants);
    prismaMock.assistant.count.mockResolvedValue(2);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/assistants',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data).toHaveLength(2);
    expect(body.meta).toBeDefined();
    expect(body.meta.total).toBe(2);
  });

  it('returns 401 without auth', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/assistants',
    });

    expect(res.statusCode).toBe(401);
  });
});

describe('GET /api/assistants/:id', () => {
  it('returns 200 when found', async () => {
    const assistant = buildAssistant({ id: 'ast-1', organizationId: 'test-org-id' });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/assistants/ast-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().data.id).toBe('ast-1');
  });

  it('returns 401 without auth', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/assistants/ast-1',
    });

    expect(res.statusCode).toBe(401);
  });

  it('returns 404 when not found', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/assistants/nonexistent',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
  });
});

describe('PATCH /api/assistants/:id', () => {
  it('returns 200 when updated', async () => {
    const assistant = buildAssistant({ id: 'ast-1', organizationId: 'test-org-id' });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.assistant.update.mockResolvedValue({ ...assistant, name: 'Updated' });
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/assistants/ast-1',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'Updated' },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().data.name).toBe('Updated');
  });

  it('returns 401 without auth', async () => {
    const res = await app.inject({
      method: 'PATCH',
      url: '/api/assistants/ast-1',
      payload: { name: 'Updated' },
    });

    expect(res.statusCode).toBe(401);
  });

  it('returns 404 when not found', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/assistants/nonexistent',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'Updated' },
    });

    expect(res.statusCode).toBe(404);
  });
});

describe('DELETE /api/assistants/:id', () => {
  it('returns 204 when deleted', async () => {
    const assistant = buildAssistant({ id: 'ast-1', organizationId: 'test-org-id' });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.assistant.delete.mockResolvedValue(assistant);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/assistants/ast-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(204);
  });

  it('returns 401 without auth', async () => {
    const res = await app.inject({
      method: 'DELETE',
      url: '/api/assistants/ast-1',
    });

    expect(res.statusCode).toBe(401);
  });

  it('returns 404 when not found', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/assistants/nonexistent',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
  });
});
