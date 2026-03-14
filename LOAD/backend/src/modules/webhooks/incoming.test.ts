import { describe, it, expect, vi, beforeEach } from 'vitest';
import Fastify from 'fastify';
import crypto from 'node:crypto';

// Mutable config so individual tests can toggle NODE_ENV / WEBHOOK_SECRET
const { mockConfig } = vi.hoisted(() => ({
  mockConfig: {
    NODE_ENV: 'test' as string,
    WEBHOOK_SECRET: 'test-webhook-secret',
  },
}));

vi.mock('../../config/index.js', () => ({
  config: mockConfig,
}));

import { incomingWebhookRoutes } from './incoming.js';
import { errorHandler } from '../../middleware/error-handler.js';

function makeSignature(payload: string, secret: string): string {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(payload);
  return `sha256=${hmac.digest('hex')}`;
}

async function buildTestApp() {
  const app = Fastify();
  app.setErrorHandler(errorHandler);
  await app.register(incomingWebhookRoutes);
  return app;
}

// ---------------------------------------------------------------------------
// POST /api/webhooks/incoming
// ---------------------------------------------------------------------------
describe('POST /api/webhooks/incoming', () => {
  beforeEach(() => {
    // Default: test mode with placeholder — middleware skips signature check
    mockConfig.NODE_ENV = 'test';
    mockConfig.WEBHOOK_SECRET = 'test-webhook-secret';
  });

  it('accepts a valid request', async () => {
    const app = await buildTestApp();
    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks/incoming',
      payload: { event: 'payment.completed', data: { amount: 100 } },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body).toEqual({
      success: true,
      data: { received: true, event: 'payment.completed' },
    });
  });

  it('returns 401 when signature is missing (production mode)', async () => {
    mockConfig.NODE_ENV = 'production';
    mockConfig.WEBHOOK_SECRET = 'production-secret-key-min-16';

    const app = await buildTestApp();
    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks/incoming',
      payload: { event: 'test.event' },
    });

    expect(res.statusCode).toBe(401);
  });

  it('returns 400 when event is missing', async () => {
    const app = await buildTestApp();
    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks/incoming',
      payload: { data: { foo: 'bar' } },
    });

    expect(res.statusCode).toBe(400);
    expect(res.json().error.code).toBe('VALIDATION_ERROR');
  });

  it('returns 400 when event is empty', async () => {
    const app = await buildTestApp();
    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks/incoming',
      payload: { event: '' },
    });

    expect(res.statusCode).toBe(400);
    expect(res.json().error.code).toBe('VALIDATION_ERROR');
  });

  it('accepts request with optional timestamp', async () => {
    const app = await buildTestApp();
    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks/incoming',
      payload: {
        event: 'user.created',
        timestamp: '2026-02-26T12:00:00Z',
      },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().data.event).toBe('user.created');
  });

  it('accepts request with optional data', async () => {
    const app = await buildTestApp();
    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks/incoming',
      payload: {
        event: 'order.shipped',
        data: { orderId: 'abc', items: 3 },
      },
    });

    expect(res.statusCode).toBe(200);
  });

  it('accepts request with event only', async () => {
    const app = await buildTestApp();
    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks/incoming',
      payload: { event: 'ping' },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().data).toEqual({ received: true, event: 'ping' });
  });

  it('accepts a valid signature in production mode', async () => {
    mockConfig.NODE_ENV = 'production';
    mockConfig.WEBHOOK_SECRET = 'production-secret-key-min-16';

    const payload = { event: 'invoice.paid', data: { id: 'inv-1' } };
    const sig = makeSignature(JSON.stringify(payload), mockConfig.WEBHOOK_SECRET);

    const app = await buildTestApp();
    const res = await app.inject({
      method: 'POST',
      url: '/api/webhooks/incoming',
      headers: { 'x-load-signature': sig },
      payload,
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().data.event).toBe('invoice.paid');
  });
});
