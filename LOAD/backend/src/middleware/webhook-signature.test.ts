import { describe, it, expect, vi, beforeEach } from 'vitest';
import crypto from 'node:crypto';

const { mockConfig } = vi.hoisted(() => ({
  mockConfig: {
    NODE_ENV: 'production' as string,
    WEBHOOK_SECRET: 'production-secret-key-min-16',
  },
}));

vi.mock('../config/index.js', () => ({
  config: mockConfig,
}));

import { verifyWebhookSignature, computeWebhookSignature } from './webhook-signature.js';

function makeSignature(payload: string, secret: string): string {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(payload);
  return `sha256=${hmac.digest('hex')}`;
}

function buildRequest(body: unknown, signature?: string) {
  return {
    headers: signature ? { 'x-load-signature': signature } : {},
    body,
  } as any;
}

function buildReply() {
  const reply = {
    status: vi.fn().mockReturnThis(),
    send: vi.fn().mockReturnThis(),
  };
  return reply as any;
}

// ---------------------------------------------------------------------------
// verifyWebhookSignature
// ---------------------------------------------------------------------------
describe('verifyWebhookSignature', () => {
  beforeEach(() => {
    mockConfig.NODE_ENV = 'production';
    mockConfig.WEBHOOK_SECRET = 'production-secret-key-min-16';
  });

  it('passes with a valid signature', async () => {
    const body = { event: 'test.event', data: { id: '123' } };
    const payload = JSON.stringify(body);
    const sig = makeSignature(payload, mockConfig.WEBHOOK_SECRET);
    const request = buildRequest(body, sig);
    const reply = buildReply();

    await verifyWebhookSignature(request, reply);

    expect(reply.status).not.toHaveBeenCalled();
    expect(reply.send).not.toHaveBeenCalled();
  });

  it('returns 401 when X-Load-Signature header is missing', async () => {
    const request = buildRequest({ event: 'test' });
    const reply = buildReply();

    await verifyWebhookSignature(request, reply);

    expect(reply.status).toHaveBeenCalledWith(401);
    expect(reply.send).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false,
        error: expect.objectContaining({ message: 'Missing X-Load-Signature header' }),
      }),
    );
  });

  it('returns 401 for malformed signature format', async () => {
    const request = buildRequest({ event: 'test' }, 'not-a-valid-format');
    const reply = buildReply();

    await verifyWebhookSignature(request, reply);

    expect(reply.status).toHaveBeenCalledWith(401);
    expect(reply.send).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false,
        error: expect.objectContaining({ message: 'Malformed X-Load-Signature header' }),
      }),
    );
  });

  it('returns 401 for wrong signature', async () => {
    const body = { event: 'test' };
    const payload = JSON.stringify(body);
    const sig = makeSignature(payload, 'wrong-secret-key-min-16');
    const request = buildRequest(body, sig);
    const reply = buildReply();

    await verifyWebhookSignature(request, reply);

    expect(reply.status).toHaveBeenCalledWith(401);
    expect(reply.send).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false,
        error: expect.objectContaining({ message: 'Invalid webhook signature' }),
      }),
    );
  });

  it('returns 401 for wrong hex length', async () => {
    const request = buildRequest({ event: 'test' }, 'sha256=abc123');
    const reply = buildReply();

    await verifyWebhookSignature(request, reply);

    expect(reply.status).toHaveBeenCalledWith(401);
    expect(reply.send).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false,
        error: expect.objectContaining({ message: 'Malformed X-Load-Signature header' }),
      }),
    );
  });

  it('skips validation in dev/test with placeholder secret', async () => {
    mockConfig.NODE_ENV = 'test';
    mockConfig.WEBHOOK_SECRET = 'test-webhook-secret';

    const request = buildRequest({ event: 'test' }); // no signature
    const reply = buildReply();

    await verifyWebhookSignature(request, reply);

    expect(reply.status).not.toHaveBeenCalled();
    expect(reply.send).not.toHaveBeenCalled();
  });

  it('does not skip validation in production even with placeholder secret', async () => {
    mockConfig.NODE_ENV = 'production';
    mockConfig.WEBHOOK_SECRET = 'test-webhook-secret';

    const request = buildRequest({ event: 'test' }); // no signature
    const reply = buildReply();

    await verifyWebhookSignature(request, reply);

    expect(reply.status).toHaveBeenCalledWith(401);
  });
});

// ---------------------------------------------------------------------------
// computeWebhookSignature
// ---------------------------------------------------------------------------
describe('computeWebhookSignature', () => {
  beforeEach(() => {
    mockConfig.WEBHOOK_SECRET = 'production-secret-key-min-16';
  });

  it('returns sha256={hex} format', () => {
    const result = computeWebhookSignature('{"event":"test"}');
    expect(result).toMatch(/^sha256=[a-f0-9]{64}$/);
  });

  it('produces consistent results for the same input', () => {
    const payload = '{"event":"test","data":{"id":"1"}}';
    const a = computeWebhookSignature(payload);
    const b = computeWebhookSignature(payload);
    expect(a).toBe(b);
  });

  it('produces different results for different inputs', () => {
    const a = computeWebhookSignature('{"event":"a"}');
    const b = computeWebhookSignature('{"event":"b"}');
    expect(a).not.toBe(b);
  });
});
