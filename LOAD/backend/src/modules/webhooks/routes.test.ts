import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildWebhook, buildWebhookDelivery } from '../../../tests/helpers/factories.js';
import type { FastifyInstance } from 'fastify';

let prismaMock: PrismaMock;

vi.mock('../../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
  connectDatabase: vi.fn(),
  disconnectDatabase: vi.fn(),
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

// ---------------------------------------------------------------------------
// POST /api/webhooks
// ---------------------------------------------------------------------------
describe('POST /api/webhooks', () => {
  const validBody = {
    url: 'https://example.com/hook',
    events: ['call.started', 'call.ended'],
  };

  it('returns 201 with created webhook on success', async () => {
    const webhook = buildWebhook({ organizationId: 'test-org-id', url: validBody.url, events: validBody.events });
    prismaMock.webhook.create.mockResolvedValue(webhook);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks',
      headers: { authorization: `Bearer ${token}` },
      payload: validBody,
    });

    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.url).toBe('https://example.com/hook');
    expect(body.data.events).toEqual(['call.started', 'call.ended']);
    expect(body.data.secret).toBeDefined();
  });

  it('returns 201 with active defaulting to true', async () => {
    const webhook = buildWebhook({ active: true });
    prismaMock.webhook.create.mockResolvedValue(webhook);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks',
      headers: { authorization: `Bearer ${token}` },
      payload: validBody,
    });

    expect(res.statusCode).toBe(201);
    expect(res.json().data.active).toBe(true);
  });

  it('returns 201 when active is explicitly set to false', async () => {
    const webhook = buildWebhook({ active: false });
    prismaMock.webhook.create.mockResolvedValue(webhook);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks',
      headers: { authorization: `Bearer ${token}` },
      payload: { ...validBody, active: false },
    });

    expect(res.statusCode).toBe(201);
    expect(res.json().data.active).toBe(false);
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks',
      payload: validBody,
    });

    expect(res.statusCode).toBe(401);
  });

  it('returns 400 for invalid url', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks',
      headers: { authorization: `Bearer ${token}` },
      payload: { url: 'not-a-url', events: ['call.started'] },
    });

    expect(res.statusCode).toBe(400);
  });

  it('returns 400 for empty events array', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks',
      headers: { authorization: `Bearer ${token}` },
      payload: { url: 'https://example.com/hook', events: [] },
    });

    expect(res.statusCode).toBe(400);
  });

  it('returns 400 for missing required fields', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks',
      headers: { authorization: `Bearer ${token}` },
      payload: {},
    });

    expect(res.statusCode).toBe(400);
  });
});

// ---------------------------------------------------------------------------
// GET /api/webhooks
// ---------------------------------------------------------------------------
describe('GET /api/webhooks', () => {
  it('returns 200 with list of webhooks', async () => {
    const webhooks = [
      buildWebhook({ id: 'wh-1', organizationId: 'test-org-id' }),
      buildWebhook({ id: 'wh-2', organizationId: 'test-org-id' }),
    ];
    prismaMock.webhook.findMany.mockResolvedValue(webhooks);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/webhooks',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data).toHaveLength(2);
  });

  it('returns 200 with empty array when no webhooks exist', async () => {
    prismaMock.webhook.findMany.mockResolvedValue([]);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/webhooks',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().data).toEqual([]);
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/webhooks',
    });

    expect(res.statusCode).toBe(401);
  });
});

// ---------------------------------------------------------------------------
// GET /api/webhooks/:id
// ---------------------------------------------------------------------------
describe('GET /api/webhooks/:id', () => {
  it('returns 200 with the webhook', async () => {
    const webhook = buildWebhook({ id: 'wh-1', organizationId: 'test-org-id' });
    prismaMock.webhook.findFirst.mockResolvedValue(webhook);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/webhooks/wh-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.id).toBe('wh-1');
  });

  it('returns 404 when webhook not found', async () => {
    prismaMock.webhook.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/webhooks/nonexistent',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
    const body = res.json();
    expect(body.success).toBe(false);
    expect(body.error.code).toBe('NOT_FOUND');
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/webhooks/wh-1',
    });

    expect(res.statusCode).toBe(401);
  });
});

// ---------------------------------------------------------------------------
// PATCH /api/webhooks/:id
// ---------------------------------------------------------------------------
describe('PATCH /api/webhooks/:id', () => {
  it('returns 200 with updated webhook', async () => {
    const existing = buildWebhook({ id: 'wh-1', organizationId: 'test-org-id' });
    const updated = { ...existing, url: 'https://new-url.com/hook' };
    prismaMock.webhook.findFirst.mockResolvedValue(existing);
    prismaMock.webhook.update.mockResolvedValue(updated);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/webhooks/wh-1',
      headers: { authorization: `Bearer ${token}` },
      payload: { url: 'https://new-url.com/hook' },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.url).toBe('https://new-url.com/hook');
  });

  it('returns 404 when webhook not found', async () => {
    prismaMock.webhook.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/webhooks/nonexistent',
      headers: { authorization: `Bearer ${token}` },
      payload: { active: false },
    });

    expect(res.statusCode).toBe(404);
    expect(res.json().error.code).toBe('NOT_FOUND');
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'PATCH',
      url: '/api/webhooks/wh-1',
      payload: { active: false },
    });

    expect(res.statusCode).toBe(401);
  });
});

// ---------------------------------------------------------------------------
// DELETE /api/webhooks/:id
// ---------------------------------------------------------------------------
describe('DELETE /api/webhooks/:id', () => {
  it('returns 204 on successful deletion', async () => {
    const existing = buildWebhook({ id: 'wh-1', organizationId: 'test-org-id' });
    prismaMock.webhook.findFirst.mockResolvedValue(existing);
    prismaMock.webhook.delete.mockResolvedValue(existing);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/webhooks/wh-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(204);
  });

  it('returns 404 when webhook not found', async () => {
    prismaMock.webhook.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/webhooks/nonexistent',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
    expect(res.json().error.code).toBe('NOT_FOUND');
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'DELETE',
      url: '/api/webhooks/wh-1',
    });

    expect(res.statusCode).toBe(401);
  });
});

// ---------------------------------------------------------------------------
// GET /api/webhooks/:id/deliveries
// ---------------------------------------------------------------------------
describe('GET /api/webhooks/:id/deliveries', () => {
  it('returns 200 with paginated deliveries', async () => {
    const webhook = buildWebhook({ id: 'wh-1', organizationId: 'test-org-id' });
    const deliveries = [
      buildWebhookDelivery({ webhookId: 'wh-1', event: 'call.started' }),
      buildWebhookDelivery({ webhookId: 'wh-1', event: 'call.ended' }),
    ];
    prismaMock.webhook.findFirst.mockResolvedValue(webhook);
    prismaMock.webhookDelivery.findMany.mockResolvedValue(deliveries);
    prismaMock.webhookDelivery.count.mockResolvedValue(2);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/webhooks/wh-1/deliveries',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data).toHaveLength(2);
    expect(body.meta).toEqual({ total: 2, page: 1, limit: 20 });
  });

  it('returns 200 with custom pagination parameters', async () => {
    const webhook = buildWebhook({ id: 'wh-1', organizationId: 'test-org-id' });
    prismaMock.webhook.findFirst.mockResolvedValue(webhook);
    prismaMock.webhookDelivery.findMany.mockResolvedValue([]);
    prismaMock.webhookDelivery.count.mockResolvedValue(50);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/webhooks/wh-1/deliveries?page=3&limit=10',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.meta.page).toBe(3);
    expect(body.meta.limit).toBe(10);
    expect(body.meta.total).toBe(50);
  });

  it('returns 404 when webhook not found', async () => {
    prismaMock.webhook.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/webhooks/nonexistent/deliveries',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
    expect(res.json().error.code).toBe('NOT_FOUND');
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/webhooks/wh-1/deliveries',
    });

    expect(res.statusCode).toBe(401);
  });
});
