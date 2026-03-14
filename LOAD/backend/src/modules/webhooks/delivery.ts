import crypto from 'node:crypto';
import { Queue, Worker } from 'bullmq';
import type { ConnectionOptions, Job } from 'bullmq';
import IORedis from 'ioredis';
import { Prisma } from '@prisma/client';
import { prisma } from '../../database/client.js';
import { config } from '../../config/index.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type WebhookEvent =
  | 'call.started'
  | 'call.ended'
  | 'call.failed'
  | 'transcript.update'
  | 'campaign.progress'
  | 'campaign.completed';

export interface WebhookPayload {
  event: WebhookEvent;
  timestamp: string;
  data: Record<string, unknown>;
}

interface WebhookJobData {
  webhookId: string;
  url: string;
  secret: string;
  event: WebhookEvent;
  payload: WebhookPayload;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const QUEUE_NAME = 'webhook-delivery';
const DELIVERY_TIMEOUT_MS = 30_000;

const DEFAULT_JOB_OPTIONS = {
  attempts: 3,
  backoff: {
    type: 'exponential' as const,
    delay: 1000,
  },
  removeOnComplete: { count: 100 },
  removeOnFail: { count: 500 },
};

// ---------------------------------------------------------------------------
// Lazy-initialized singletons
// ---------------------------------------------------------------------------

let redisInstance: IORedis | null = null;
let queue: Queue<WebhookJobData> | null = null;

/**
 * Lazily create a shared ioredis connection. The cast to ConnectionOptions is
 * necessary because the top-level ioredis package may differ slightly from the
 * one BullMQ bundles internally; the runtime behaviour is identical.
 */
function getConnection(): ConnectionOptions {
  if (!redisInstance) {
    redisInstance = new IORedis(config.REDIS_URL, { maxRetriesPerRequest: null });
  }
  return redisInstance as unknown as ConnectionOptions;
}

function getQueue(): Queue<WebhookJobData> {
  if (!queue) {
    queue = new Queue<WebhookJobData>(QUEUE_NAME, {
      connection: getConnection(),
      defaultJobOptions: DEFAULT_JOB_OPTIONS,
    });
  }
  return queue;
}

// ---------------------------------------------------------------------------
// fireWebhookEvent
// ---------------------------------------------------------------------------

export async function fireWebhookEvent(
  organizationId: string,
  event: WebhookEvent,
  data: Record<string, unknown>,
): Promise<void> {
  let webhooks: { id: string; url: string; secret: string; events: string[] }[];

  try {
    webhooks = await prisma.webhook.findMany({
      where: {
        organizationId,
        active: true,
      },
      select: {
        id: true,
        url: true,
        secret: true,
        events: true,
      },
    });
  } catch (error) {
    console.error('[webhooks] Failed to query webhooks from database:', error);
    return;
  }

  const matching = webhooks.filter((wh) => wh.events.includes(event));

  if (matching.length === 0) {
    return;
  }

  const timestamp = new Date().toISOString();

  try {
    const q = getQueue();
    const jobs = matching.map((wh) =>
      q.add(QUEUE_NAME, {
        webhookId: wh.id,
        url: wh.url,
        secret: wh.secret,
        event,
        payload: { event, timestamp, data },
      }),
    );
    await Promise.all(jobs);
  } catch (error) {
    console.warn('[webhooks] Failed to enqueue webhook deliveries — Redis may be unavailable:', error);
  }
}

// ---------------------------------------------------------------------------
// Worker
// ---------------------------------------------------------------------------

async function processWebhookJob(job: Job<WebhookJobData>): Promise<void> {
  const { webhookId, url, secret, event, payload } = job.data;

  const jsonPayload = JSON.stringify(payload);
  const signature = crypto
    .createHmac('sha256', secret)
    .update(jsonPayload)
    .digest('hex');

  // Create pending delivery record
  let deliveryId: string | null = null;
  try {
    const delivery = await prisma.webhookDelivery.create({
      data: {
        webhookId,
        event,
        status: 'pending',
        requestBody: payload as unknown as Prisma.InputJsonValue,
        attemptNumber: (job.attemptsMade ?? 0) + 1,
      },
    });
    deliveryId = delivery.id;
  } catch (dbError: unknown) {
    console.warn('[webhooks] Failed to create delivery record:', dbError);
  }

  const startTime = Date.now();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DELIVERY_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Load-Signature': `sha256=${signature}`,
        'X-Load-Event': event,
      },
      body: jsonPayload,
      signal: controller.signal,
    });

    const responseTime = Date.now() - startTime;
    let responseBody: string | null = null;
    try {
      responseBody = await response.text();
    } catch {
      // ignore
    }

    // Update delivery record with response
    if (deliveryId) {
      await prisma.webhookDelivery.update({
        where: { id: deliveryId },
        data: {
          status: response.ok ? 'success' : 'failed',
          responseCode: response.status,
          responseBody: responseBody?.slice(0, 2000) ?? null,
          responseTime,
        },
      }).catch((dbError: unknown) => {
        console.warn('[webhooks] Failed to update delivery record:', dbError);
      });
    }

    if (!response.ok) {
      throw new Error(
        `Webhook delivery failed: ${response.status} ${response.statusText}`,
      );
    }
  } catch (error) {
    const responseTime = Date.now() - startTime;
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';

    // Update delivery record with error
    if (deliveryId) {
      await prisma.webhookDelivery.update({
        where: { id: deliveryId },
        data: {
          status: 'failed',
          responseTime,
          error: errorMessage,
        },
      }).catch((dbError: unknown) => {
        console.warn('[webhooks] Failed to update delivery record:', dbError);
      });
    }

    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export function createWebhookWorker(): Worker {
  const worker = new Worker<WebhookJobData>(
    QUEUE_NAME,
    processWebhookJob,
    { connection: getConnection() },
  );

  worker.on('failed', (job, error) => {
    console.error(
      `[webhooks] Delivery failed for job ${job?.id ?? 'unknown'} (webhook ${job?.data.webhookId ?? 'unknown'}):`,
      error.message,
    );
  });

  return worker;
}

// ---------------------------------------------------------------------------
// Cleanup
// ---------------------------------------------------------------------------

export async function closeWebhookQueue(): Promise<void> {
  if (queue) {
    await queue.close();
    queue = null;
  }
  if (redisInstance) {
    await redisInstance.quit();
    redisInstance = null;
  }
}
