import crypto from 'node:crypto';
import type { FastifyRequest, FastifyReply } from 'fastify';
import { config } from '../config/index.js';

const DEV_PLACEHOLDER = 'test-webhook-secret';

/**
 * Compute HMAC-SHA256 signature for a webhook payload.
 * Returns a string in the format `sha256={hex}`.
 */
export function computeWebhookSignature(payload: string): string {
  const hmac = crypto.createHmac('sha256', config.WEBHOOK_SECRET);
  hmac.update(payload);
  return `sha256=${hmac.digest('hex')}`;
}

/**
 * Fastify preHandler hook that verifies incoming webhook requests
 * using HMAC-SHA256 signature in the X-Load-Signature header.
 *
 * Skips validation in dev/test when WEBHOOK_SECRET is the well-known placeholder.
 */
export async function verifyWebhookSignature(
  request: FastifyRequest,
  reply: FastifyReply,
): Promise<void> {
  // Skip validation in dev/test when using the test placeholder secret
  if (config.NODE_ENV !== 'production' && config.WEBHOOK_SECRET === DEV_PLACEHOLDER) {
    return;
  }

  const signature = request.headers['x-load-signature'] as string | undefined;
  if (!signature) {
    reply.status(401).send({
      success: false,
      error: {
        code: 'UNAUTHORIZED',
        message: 'Missing X-Load-Signature header',
        statusCode: 401,
      },
    });
    return;
  }

  // Validate format: sha256={64 hex chars}
  const match = /^sha256=([a-f0-9]{64})$/i.exec(signature);
  if (!match) {
    reply.status(401).send({
      success: false,
      error: {
        code: 'UNAUTHORIZED',
        message: 'Malformed X-Load-Signature header',
        statusCode: 401,
      },
    });
    return;
  }

  const expected = computeWebhookSignature(JSON.stringify(request.body));
  const expectedHex = expected.slice('sha256='.length);
  const receivedHex = match[1];

  const expectedBuf = Buffer.from(expectedHex, 'hex');
  const receivedBuf = Buffer.from(receivedHex, 'hex');

  if (!crypto.timingSafeEqual(expectedBuf, receivedBuf)) {
    reply.status(401).send({
      success: false,
      error: {
        code: 'UNAUTHORIZED',
        message: 'Invalid webhook signature',
        statusCode: 401,
      },
    });
  }
}
