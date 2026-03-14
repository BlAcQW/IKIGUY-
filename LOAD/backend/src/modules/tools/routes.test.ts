import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildTool, buildAssistant } from '../../../tests/helpers/factories.js';
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

// ─── CRUD: Create Tool ──────────────────────────────────────────────────────

describe('POST /api/tools', () => {
  const validBody = {
    name: 'Lookup Customer',
    type: 'FUNCTION' as const,
    description: 'Looks up a customer record by email',
    function: {
      name: 'lookup_customer',
      description: 'Looks up a customer by email',
      parameters: { type: 'object', properties: { email: { type: 'string' } } },
    },
    serverUrl: 'https://api.example.com/tools/lookup',
  };

  it('returns 201 on successful creation with full payload', async () => {
    const tool = buildTool({ name: 'Lookup Customer', organizationId: 'test-org-id' });
    prismaMock.tool.create.mockResolvedValue(tool);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/tools',
      headers: { authorization: `Bearer ${token}` },
      payload: validBody,
    });

    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.name).toBe('Lookup Customer');
    expect(prismaMock.tool.create).toHaveBeenCalledOnce();
    expect(prismaMock.tool.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          organizationId: 'test-org-id',
          name: 'Lookup Customer',
          type: 'FUNCTION',
          description: 'Looks up a customer record by email',
          serverUrl: 'https://api.example.com/tools/lookup',
        }),
      }),
    );
  });

  it('returns 401 without authorization header', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/tools',
      payload: validBody,
    });

    expect(res.statusCode).toBe(401);
  });

  it('returns 400 when required name field is missing', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/tools',
      headers: { authorization: `Bearer ${token}` },
      payload: { description: 'No name provided', type: 'FUNCTION' },
    });

    expect(res.statusCode).toBe(400);
    expect(res.json().success).toBe(false);
  });

  it('returns 400 when serverUrl is not a valid URL', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/tools',
      headers: { authorization: `Bearer ${token}` },
      payload: { ...validBody, serverUrl: 'not-a-url' },
    });

    expect(res.statusCode).toBe(400);
    expect(res.json().success).toBe(false);
  });
});

// ─── CRUD: List Tools ───────────────────────────────────────────────────────

describe('GET /api/tools', () => {
  it('returns 200 with tools list scoped to organization', async () => {
    const tools = [
      buildTool({ name: 'Tool A', organizationId: 'test-org-id' }),
      buildTool({ name: 'Tool B', organizationId: 'test-org-id' }),
    ];
    prismaMock.tool.findMany.mockResolvedValue(tools);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/tools',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data).toHaveLength(2);
    expect(prismaMock.tool.findMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { organizationId: 'test-org-id' },
        orderBy: { createdAt: 'desc' },
      }),
    );
  });

  it('returns 401 without authorization header', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/tools',
    });

    expect(res.statusCode).toBe(401);
  });
});

// ─── CRUD: Get Tool by ID ───────────────────────────────────────────────────

describe('GET /api/tools/:id', () => {
  it('returns 200 with the tool when found', async () => {
    const tool = buildTool({ id: 'tool-1', organizationId: 'test-org-id', name: 'My Tool' });
    prismaMock.tool.findFirst.mockResolvedValue(tool);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/tools/tool-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.id).toBe('tool-1');
    expect(body.data.name).toBe('My Tool');
    expect(prismaMock.tool.findFirst).toHaveBeenCalledWith({
      where: { id: 'tool-1', organizationId: 'test-org-id' },
    });
  });

  it('returns 404 when tool does not exist', async () => {
    prismaMock.tool.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/tools/nonexistent',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
    const body = res.json();
    expect(body.success).toBe(false);
    expect(body.error.code).toBe('NOT_FOUND');
    expect(body.error.message).toBe('Tool not found');
  });
});

// ─── CRUD: Update Tool ──────────────────────────────────────────────────────

describe('PATCH /api/tools/:id', () => {
  it('returns 200 with updated tool on partial update', async () => {
    const existing = buildTool({ id: 'tool-1', name: 'Old Name', organizationId: 'test-org-id' });
    const updated = { ...existing, name: 'Updated Name', description: 'New description' };
    prismaMock.tool.findFirst.mockResolvedValue(existing);
    prismaMock.tool.update.mockResolvedValue(updated);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/tools/tool-1',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'Updated Name', description: 'New description' },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.name).toBe('Updated Name');
    expect(body.data.description).toBe('New description');
    expect(prismaMock.tool.update).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: 'tool-1' },
        data: expect.objectContaining({ name: 'Updated Name', description: 'New description' }),
      }),
    );
  });

  it('returns 404 when tool to update is not found', async () => {
    prismaMock.tool.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/tools/nonexistent',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'Updated' },
    });

    expect(res.statusCode).toBe(404);
    expect(res.json().error.code).toBe('NOT_FOUND');
    expect(prismaMock.tool.update).not.toHaveBeenCalled();
  });
});

// ─── CRUD: Delete Tool ──────────────────────────────────────────────────────

describe('DELETE /api/tools/:id', () => {
  it('returns 204 on successful deletion', async () => {
    const existing = buildTool({ id: 'tool-1', organizationId: 'test-org-id' });
    prismaMock.tool.findFirst.mockResolvedValue(existing);
    prismaMock.tool.delete.mockResolvedValue(existing);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/tools/tool-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(204);
    expect(prismaMock.tool.delete).toHaveBeenCalledWith({ where: { id: 'tool-1' } });
  });

  it('returns 404 when tool to delete is not found', async () => {
    prismaMock.tool.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/tools/nonexistent',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
    expect(res.json().error.code).toBe('NOT_FOUND');
    expect(prismaMock.tool.delete).not.toHaveBeenCalled();
  });
});

// ─── Templates: List ────────────────────────────────────────────────────────

describe('GET /api/tools/templates', () => {
  it('returns 200 with categories and grouped templates', async () => {
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
    expect(body.data.categories).toHaveProperty('scheduling', 'Scheduling');
    expect(body.data.categories).toHaveProperty('sales', 'Sales & Lead Nurturing');
    expect(body.data.templates).toBeDefined();
    expect(body.data.templates.scheduling.length).toBeGreaterThan(0);
  });

  it('returns 401 without authorization header', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/tools/templates',
    });

    expect(res.statusCode).toBe(401);
  });
});

// ─── Templates: Create from single template ─────────────────────────────────

describe('POST /api/tools/from-template', () => {
  it('returns 201 when creating tool from a valid template name', async () => {
    const tool = buildTool({
      organizationId: 'test-org-id',
      name: 'Check Availability',
      metadata: { templateName: 'check_availability', category: 'scheduling' },
    });
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
    const body = res.json();
    expect(body.success).toBe(true);
    expect(prismaMock.tool.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          organizationId: 'test-org-id',
          name: 'Check Availability',
          serverUrl: 'https://example.com/webhook',
          metadata: expect.objectContaining({
            templateName: 'check_availability',
            category: 'scheduling',
          }),
        }),
      }),
    );
  });

  it('returns 404 for an unknown template name', async () => {
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
    const body = res.json();
    expect(body.success).toBe(false);
    expect(body.error.code).toBe('TEMPLATE_NOT_FOUND');
    expect(body.error.message).toContain('nonexistent_template');
  });

  it('returns 400 when serverUrl is missing', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/tools/from-template',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        templateName: 'check_availability',
      },
    });

    expect(res.statusCode).toBe(400);
    expect(res.json().success).toBe(false);
  });

  it('passes serverSecret through to created tool', async () => {
    const tool = buildTool({ organizationId: 'test-org-id', serverSecret: 'my-secret' });
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

// ─── Templates: Bulk create from category ───────────────────────────────────

describe('POST /api/tools/from-templates/bulk', () => {
  it('returns 201 with all tools created from a valid category', async () => {
    const tools = [
      buildTool({ organizationId: 'test-org-id', name: 'Check Availability' }),
      buildTool({ organizationId: 'test-org-id', name: 'Book Appointment' }),
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
    const body = res.json();
    expect(body.success).toBe(true);
    expect(Array.isArray(body.data)).toBe(true);
    expect(body.data).toHaveLength(2);
    expect(prismaMock.$transaction).toHaveBeenCalledOnce();
  });

  it('returns 404 for an unknown category', async () => {
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
    const body = res.json();
    expect(body.success).toBe(false);
    expect(body.error.code).toBe('CATEGORY_NOT_FOUND');
    expect(body.error.message).toContain('nonexistent_category');
  });

  it('attaches created tools to assistant when assistantId is provided', async () => {
    const tools = [
      buildTool({ id: 'new-tool-1', organizationId: 'test-org-id' }),
      buildTool({ id: 'new-tool-2', organizationId: 'test-org-id' }),
    ];
    prismaMock.$transaction.mockResolvedValue(tools);

    const assistant = buildAssistant({
      id: '00000000-0000-0000-0000-000000000001',
      organizationId: 'test-org-id',
      model: { provider: 'openai', model: 'gpt-4', toolIds: ['existing-tool'] },
    });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.assistant.update.mockResolvedValue({
      ...assistant,
      model: {
        provider: 'openai',
        model: 'gpt-4',
        toolIds: ['existing-tool', 'new-tool-1', 'new-tool-2'],
      },
    });
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
    expect(prismaMock.assistant.findFirst).toHaveBeenCalledWith({
      where: { id: '00000000-0000-0000-0000-000000000001', organizationId: 'test-org-id' },
    });
    expect(prismaMock.assistant.update).toHaveBeenCalledOnce();
    const updateCall = prismaMock.assistant.update.mock.calls[0][0];
    const updatedModel = updateCall.data.model as Record<string, unknown>;
    expect(updatedModel.toolIds).toEqual(['existing-tool', 'new-tool-1', 'new-tool-2']);
  });

  it('returns 400 when assistantId is not a valid UUID', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/tools/from-templates/bulk',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        category: 'scheduling',
        serverUrl: 'https://example.com/webhook',
        assistantId: 'not-a-uuid',
      },
    });

    expect(res.statusCode).toBe(400);
    expect(res.json().success).toBe(false);
  });
});
