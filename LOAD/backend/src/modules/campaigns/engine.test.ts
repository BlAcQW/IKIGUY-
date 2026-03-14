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
const mockQueueClose = vi.fn().mockResolvedValue(undefined);
const mockWorkerClose = vi.fn().mockResolvedValue(undefined);
vi.mock('bullmq', () => ({
  Queue: vi.fn().mockImplementation(() => ({
    add: mockAdd,
    close: mockQueueClose,
  })),
  Worker: vi.fn().mockImplementation(() => ({
    on: vi.fn(),
    close: mockWorkerClose,
  })),
}));

// Mock prisma
vi.mock('../../database/client.js', () => ({
  prisma: {
    campaign: {
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      findUniqueOrThrow: vi.fn(),
      update: vi.fn(),
    },
  },
}));

// Mock webhook delivery
vi.mock('../webhooks/delivery.js', () => ({
  fireWebhookEvent: vi.fn().mockResolvedValue(undefined),
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

import {
  startCampaign,
  pauseCampaign,
  resumeCampaign,
  closeCampaignQueues,
} from './engine.js';
import { prisma } from '../../database/client.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const mockFindFirst = prisma.campaign.findFirst as ReturnType<typeof vi.fn>;
const mockFindUnique = prisma.campaign.findUnique as ReturnType<typeof vi.fn>;
const mockFindUniqueOrThrow = (prisma.campaign as any).findUniqueOrThrow as ReturnType<typeof vi.fn>;
const mockUpdate = prisma.campaign.update as ReturnType<typeof vi.fn>;

function buildCampaign(overrides: Record<string, unknown> = {}) {
  return {
    id: 'camp-1',
    organizationId: 'org-1',
    name: 'Test Campaign',
    assistantId: 'ast-1',
    phoneNumberId: 'pn-1',
    status: 'DRAFT',
    contacts: [
      { name: 'Alice', number: '+15551234567' },
      { name: 'Bob', number: '+15559876543' },
    ],
    schedule: { maxConcurrent: 2 },
    stats: null,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// startCampaign
// ---------------------------------------------------------------------------

describe('startCampaign', () => {
  it('validates campaign exists', async () => {
    mockFindFirst.mockResolvedValue(null);

    await expect(startCampaign('camp-1', 'org-1')).rejects.toThrow(
      'Campaign camp-1 not found',
    );
  });

  it('throws if campaign status is RUNNING', async () => {
    mockFindFirst.mockResolvedValue(buildCampaign({ status: 'RUNNING' }));

    await expect(startCampaign('camp-1', 'org-1')).rejects.toThrow(
      'cannot be started',
    );
  });

  it('throws if campaign has no contacts', async () => {
    mockFindFirst.mockResolvedValue(buildCampaign({ contacts: [] }));

    await expect(startCampaign('camp-1', 'org-1')).rejects.toThrow(
      'has no contacts',
    );
  });

  it('transitions status to RUNNING and enqueues job', async () => {
    const campaign = buildCampaign();
    mockFindFirst.mockResolvedValue(campaign);
    mockUpdate.mockResolvedValue({ ...campaign, status: 'RUNNING' });

    await startCampaign('camp-1', 'org-1');

    // Status should be updated to RUNNING
    expect(mockUpdate).toHaveBeenCalledWith({
      where: { id: 'camp-1' },
      data: { status: 'RUNNING' },
    });

    // A job should be enqueued in the execute queue
    expect(mockAdd).toHaveBeenCalledWith(
      'campaign-execute',
      { campaignId: 'camp-1', organizationId: 'org-1' },
    );
  });

  it('allows starting a PAUSED campaign', async () => {
    const campaign = buildCampaign({ status: 'PAUSED' });
    mockFindFirst.mockResolvedValue(campaign);
    mockUpdate.mockResolvedValue({ ...campaign, status: 'RUNNING' });

    await expect(startCampaign('camp-1', 'org-1')).resolves.toBeUndefined();

    expect(mockUpdate).toHaveBeenCalledWith({
      where: { id: 'camp-1' },
      data: { status: 'RUNNING' },
    });
  });

  it('throws if campaign status is COMPLETED', async () => {
    mockFindFirst.mockResolvedValue(buildCampaign({ status: 'COMPLETED' }));

    await expect(startCampaign('camp-1', 'org-1')).rejects.toThrow(
      'cannot be started',
    );
  });
});

// ---------------------------------------------------------------------------
// pauseCampaign
// ---------------------------------------------------------------------------

describe('pauseCampaign', () => {
  it('validates campaign exists', async () => {
    mockFindFirst.mockResolvedValue(null);

    await expect(pauseCampaign('camp-1', 'org-1')).rejects.toThrow(
      'Campaign camp-1 not found',
    );
  });

  it('throws if campaign is not RUNNING', async () => {
    mockFindFirst.mockResolvedValue(buildCampaign({ status: 'DRAFT' }));

    await expect(pauseCampaign('camp-1', 'org-1')).rejects.toThrow(
      'cannot be paused',
    );
  });

  it('transitions status to PAUSED', async () => {
    const campaign = buildCampaign({ status: 'RUNNING' });
    mockFindFirst.mockResolvedValue(campaign);
    mockUpdate.mockResolvedValue({ ...campaign, status: 'PAUSED' });

    await pauseCampaign('camp-1', 'org-1');

    expect(mockUpdate).toHaveBeenCalledWith({
      where: { id: 'camp-1' },
      data: { status: 'PAUSED' },
    });
  });
});

// ---------------------------------------------------------------------------
// resumeCampaign
// ---------------------------------------------------------------------------

describe('resumeCampaign', () => {
  it('validates campaign exists', async () => {
    mockFindFirst.mockResolvedValue(null);

    await expect(resumeCampaign('camp-1', 'org-1')).rejects.toThrow(
      'Campaign camp-1 not found',
    );
  });

  it('throws if campaign is not PAUSED', async () => {
    mockFindFirst.mockResolvedValue(buildCampaign({ status: 'DRAFT' }));

    await expect(resumeCampaign('camp-1', 'org-1')).rejects.toThrow(
      'cannot be resumed',
    );
  });

  it('transitions status to RUNNING and enqueues remaining contacts', async () => {
    const campaign = buildCampaign({ status: 'PAUSED' });
    mockFindFirst.mockResolvedValue(campaign);

    // readCampaignStats reads via findUniqueOrThrow
    mockFindUniqueOrThrow.mockResolvedValue({
      stats: { totalContacts: 2, completed: 1, failed: 0, inProgress: 0 },
    });

    mockUpdate.mockResolvedValue({ ...campaign, status: 'RUNNING' });

    await resumeCampaign('camp-1', 'org-1');

    // Status should transition to RUNNING
    expect(mockUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: 'camp-1' },
        data: { status: 'RUNNING' },
      }),
    );

    // Only the remaining contact (Bob) should be enqueued
    expect(mockAdd).toHaveBeenCalledWith(
      'campaign-calls',
      expect.objectContaining({
        campaignId: 'camp-1',
        contact: { name: 'Bob', number: '+15559876543' },
        contactIndex: 1,
      }),
      expect.objectContaining({ delay: expect.any(Number) }),
    );
  });

  it('marks campaign as COMPLETED if all contacts already processed', async () => {
    const campaign = buildCampaign({ status: 'PAUSED' });
    mockFindFirst.mockResolvedValue(campaign);

    // All contacts already processed
    mockFindUniqueOrThrow.mockResolvedValue({
      stats: { totalContacts: 2, completed: 2, failed: 0, inProgress: 0 },
    });

    mockUpdate.mockResolvedValue({ ...campaign, status: 'COMPLETED' });

    await resumeCampaign('camp-1', 'org-1');

    expect(mockUpdate).toHaveBeenCalledWith({
      where: { id: 'camp-1' },
      data: { status: 'COMPLETED' },
    });

    // No call jobs should be enqueued
    expect(mockAdd).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// closeCampaignQueues
// ---------------------------------------------------------------------------

describe('closeCampaignQueues', () => {
  it('closes cleanly', async () => {
    await expect(closeCampaignQueues()).resolves.toBeUndefined();
  });
});
