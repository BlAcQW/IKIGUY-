import { describe, it, expect, vi, beforeEach } from 'vitest';

// ---------------------------------------------------------------------------
// Mocks — must be declared before importing the module under test
// ---------------------------------------------------------------------------

// Mock ioredis
vi.mock('ioredis', () => {
  const MockRedis = vi.fn().mockImplementation(() => ({
    quit: vi.fn().mockResolvedValue('OK'),
  }));
  return { default: MockRedis };
});

// Mock bullmq
const mockAdd = vi.fn().mockResolvedValue({ id: 'job-1' });
const mockClose = vi.fn().mockResolvedValue(undefined);
vi.mock('bullmq', () => ({
  Queue: vi.fn().mockImplementation(() => ({
    add: mockAdd,
    close: mockClose,
  })),
  Worker: vi.fn().mockImplementation((_name: string, processor: Function) => ({
    on: vi.fn(),
    close: vi.fn().mockResolvedValue(undefined),
    processor,
  })),
}));

// Mock prisma
vi.mock('../../database/client.js', () => ({
  prisma: {
    webhook: {
      findMany: vi.fn(),
    },
  },
}));

// Mock config
vi.mock('../../config/index.js', () => ({
  config: {
    REDIS_URL: 'redis://localhost:6379',
  },
}));

// ---------------------------------------------------------------------------
// Imports (after mocks)
// ---------------------------------------------------------------------------

import { fireWebhookEvent, createWebhookWorker, closeWebhookQueue } from './delivery.js';
import { prisma } from '../../database/client.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const mockFindMany = prisma.webhook.findMany as ReturnType<typeof vi.fn>;

const activeWebhooks = [
  {
    id: 'wh-1',
    url: 'https://example.com/hook',
    secret: 'test-secret',
    events: ['call.started', 'call.ended'],
  },
  {
    id: 'wh-2',
    url: 'https://other.com/hook',
    secret: 'other-secret',
    events: ['call.ended'],
  },
];

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
});

describe('fireWebhookEvent', () => {
  it('queries active webhooks for organization', async () => {
    mockFindMany.mockResolvedValue([]);

    await fireWebhookEvent('org-1', 'call.started', { callId: 'c1' });

    expect(mockFindMany).toHaveBeenCalledWith({
      where: {
        organizationId: 'org-1',
        active: true,
      },
      select: {
        id: true,
        url: true,
        secret: true,
        events: true,
      },
    });
  });

  it('enqueues jobs for matching webhooks', async () => {
    mockFindMany.mockResolvedValue(activeWebhooks);

    await fireWebhookEvent('org-1', 'call.ended', { callId: 'c1' });

    // Both wh-1 and wh-2 subscribe to 'call.ended'
    expect(mockAdd).toHaveBeenCalledTimes(2);

    // Verify first job payload
    expect(mockAdd).toHaveBeenCalledWith(
      'webhook-delivery',
      expect.objectContaining({
        webhookId: 'wh-1',
        url: 'https://example.com/hook',
        secret: 'test-secret',
        event: 'call.ended',
        payload: expect.objectContaining({
          event: 'call.ended',
          data: { callId: 'c1' },
        }),
      }),
    );

    // Verify second job payload
    expect(mockAdd).toHaveBeenCalledWith(
      'webhook-delivery',
      expect.objectContaining({
        webhookId: 'wh-2',
        url: 'https://other.com/hook',
        secret: 'other-secret',
        event: 'call.ended',
      }),
    );
  });

  it('skips webhooks that do not match the event', async () => {
    mockFindMany.mockResolvedValue(activeWebhooks);

    await fireWebhookEvent('org-1', 'call.started', { callId: 'c1' });

    // Only wh-1 subscribes to 'call.started'
    expect(mockAdd).toHaveBeenCalledTimes(1);
    expect(mockAdd).toHaveBeenCalledWith(
      'webhook-delivery',
      expect.objectContaining({
        webhookId: 'wh-1',
      }),
    );
  });

  it('handles empty webhook list', async () => {
    mockFindMany.mockResolvedValue([]);

    await fireWebhookEvent('org-1', 'call.started', { callId: 'c1' });

    expect(mockAdd).not.toHaveBeenCalled();
  });

  it('handles database errors gracefully', async () => {
    mockFindMany.mockRejectedValue(new Error('DB connection lost'));

    // Should not throw — errors are caught and logged
    await expect(
      fireWebhookEvent('org-1', 'call.started', { callId: 'c1' }),
    ).resolves.toBeUndefined();

    expect(mockAdd).not.toHaveBeenCalled();
  });
});

describe('createWebhookWorker', () => {
  it('creates a worker', () => {
    const worker = createWebhookWorker();

    expect(worker).toBeDefined();
    expect(worker.on).toBeDefined();
  });
});

describe('closeWebhookQueue', () => {
  it('closes queue and redis', async () => {
    // Trigger lazy initialization by firing an event (which creates queue + redis)
    mockFindMany.mockResolvedValue([]);
    await fireWebhookEvent('org-1', 'call.started', {});

    await closeWebhookQueue();

    // After closing, a subsequent close should be a no-op (no errors)
    await expect(closeWebhookQueue()).resolves.toBeUndefined();
  });
});
