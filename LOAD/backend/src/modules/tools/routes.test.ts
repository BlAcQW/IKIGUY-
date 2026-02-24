import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildTool } from '../../../tests/helpers/factories.js';
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

// ─── Template endpoints ──────────────────────────────────────────────

describe('GET /api/tools/templates', () => {
  it('returns 200 with templates grouped by category', async () => {
    const token = generateToken();
    const res = await app.inject({
      method: 'GET',
      url: '/api/tools/templates',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.categories).toBeDefined();
    expect(body.data.templates).toBeDefined();
    expect(body.data.templates.scheduling.length).toBeGreaterThan(0);
  });

  it('returns 401 without auth', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/tools/templates',
    });
    expect(res.statusCode).toBe(401);
  });
});

describe('POST /api/tools/from-template', () => {
  it('returns 201 when creating from a valid template', async () => {
    const tool = buildTool({ organizationId: 'test-org-id', name: 'Check Availability' });
    prismaMock.tool.create.mockResolvedValue(tool);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/tools/from-template',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        templateName: 'check_availability',
        serverUrl: 'https://example.com/webhook',
      },
    });

    expect(res.statusCode).toBe(201);
    expect(res.json().success).toBe(true);
    expect(prismaMock.tool.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          organizationId: 'test-org-id',
          serverUrl: 'https://example.com/webhook',
        }),
      }),
    );
  });

  it('returns 404 for unknown template name', async () => {
    const token = generateToken();
    const res = await app.inject({
      method: 'POST',
      url: '/api/tools/from-template',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        templateName: 'nonexistent_template',
        serverUrl: 'https://example.com/webhook',
      },
    });

    expect(res.statusCode).toBe(404);
    expect(res.json().error.code).toBe('TEMPLATE_NOT_FOUND');
  });

  it('returns 400 for invalid serverUrl', async () => {
    const token = generateToken();
    const res = await app.inject({
      method: 'POST',
      url: '/api/tools/from-template',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        templateName: 'check_availability',
        serverUrl: 'not-a-url',
      },
    });

    expect(res.statusCode).toBe(400);
  });

  it('passes serverSecret when provided', async () => {
    const tool = buildTool({ organizationId: 'test-org-id' });
    prismaMock.tool.create.mockResolvedValue(tool);
    const token = generateToken();

    await app.inject({
      method: 'POST',
      url: '/api/tools/from-template',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        templateName: 'check_availability',
        serverUrl: 'https://example.com/webhook',
        serverSecret: 'my-secret',
      },
    });

    expect(prismaMock.tool.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          serverSecret: 'my-secret',
        }),
      }),
    );
  });
});

describe('POST /api/tools/from-templates/bulk', () => {
  it('returns 201 when creating from a valid category', async () => {
    const tools = [
      buildTool({ organizationId: 'test-org-id', name: 'Tool 1' }),
      buildTool({ organizationId: 'test-org-id', name: 'Tool 2' }),
    ];
    prismaMock.$transaction.mockResolvedValue(tools);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/tools/from-templates/bulk',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        category: 'scheduling',
        serverUrl: 'https://example.com/webhook',
      },
    });

    expect(res.statusCode).toBe(201);
    expect(res.json().success).toBe(true);
    expect(res.json().data).toHaveLength(2);
  });

  it('returns 404 for unknown category', async () => {
    const token = generateToken();
    const res = await app.inject({
      method: 'POST',
      url: '/api/tools/from-templates/bulk',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        category: 'nonexistent_category',
        serverUrl: 'https://example.com/webhook',
      },
    });

    expect(res.statusCode).toBe(404);
    expect(res.json().error.code).toBe('CATEGORY_NOT_FOUND');
  });

  it('attaches tools to assistant when assistantId provided', async () => {
    const tools = [buildTool({ id: 'tool-1' }), buildTool({ id: 'tool-2' })];
    prismaMock.$transaction.mockResolvedValue(tools);
    const assistant = {
      id: '00000000-0000-0000-0000-000000000001',
      organizationId: 'test-org-id',
      model: { provider: 'openai', model: 'gpt-4' },
    };
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.assistant.update.mockResolvedValue(assistant);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/tools/from-templates/bulk',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        category: 'scheduling',
        serverUrl: 'https://example.com/webhook',
        assistantId: '00000000-0000-0000-0000-000000000001',
      },
    });

    expect(res.statusCode).toBe(201);
    expect(prismaMock.assistant.update).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: '00000000-0000-0000-0000-000000000001' },
        data: expect.objectContaining({
          model: expect.objectContaining({
            toolIds: ['tool-1', 'tool-2'],
          }),
        }),
      }),
    );
  });
});

// ─── Standard CRUD ───────────────────────────────────────────────────

describe('POST /api/tools', () => {
  it('returns 201 with auth', async () => {
    const tool = buildTool({ organizationId: 'test-org-id' });
    prismaMock.tool.create.mockResolvedValue(tool);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/tools',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'my_tool' },
    });

    expect(res.statusCode).toBe(201);
    expect(res.json().success).toBe(true);
  });

  it('returns 401 without auth', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/tools',
      payload: { name: 'my_tool' },
    });
    expect(res.statusCode).toBe(401);
  });
});

describe('GET /api/tools', () => {
  it('returns 200 with tools list', async () => {
    prismaMock.tool.findMany.mockResolvedValue([buildTool(), buildTool()]);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/tools',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().data).toHaveLength(2);
  });
});

describe('GET /api/tools/:id', () => {
  it('returns 200 when found', async () => {
    const tool = buildTool({ id: 'tool-1', organizationId: 'test-org-id' });
    prismaMock.tool.findFirst.mockResolvedValue(tool);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/tools/tool-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().data.id).toBe('tool-1');
  });

  it('returns 404 when not found', async () => {
    prismaMock.tool.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/tools/nonexistent',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
  });
});

describe('PATCH /api/tools/:id', () => {
  it('returns 200 when updated', async () => {
    const tool = buildTool({ id: 'tool-1', organizationId: 'test-org-id' });
    prismaMock.tool.findFirst.mockResolvedValue(tool);
    prismaMock.tool.update.mockResolvedValue({ ...tool, name: 'Updated' });
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/tools/tool-1',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'Updated' },
    });

    expect(res.statusCode).toBe(200);
  });

  it('returns 404 when not found', async () => {
    prismaMock.tool.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/tools/nonexistent',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'Updated' },
    });

    expect(res.statusCode).toBe(404);
  });
});

describe('DELETE /api/tools/:id', () => {
  it('returns 204 when deleted', async () => {
    const tool = buildTool({ id: 'tool-1', organizationId: 'test-org-id' });
    prismaMock.tool.findFirst.mockResolvedValue(tool);
    prismaMock.tool.delete.mockResolvedValue(tool);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/tools/tool-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(204);
  });

  it('returns 404 when not found', async () => {
    prismaMock.tool.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/tools/nonexistent',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
  });
});
