import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildCampaign } from '../../../tests/helpers/factories.js';
import type { FastifyInstance } from 'fastify';

let prismaMock: PrismaMock;

vi.mock('../../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
  connectDatabase: vi.fn(),
  disconnectDatabase: vi.fn(),
}));

vi.mock('./engine.js', () => ({
  startCampaign: vi.fn(),
  pauseCampaign: vi.fn(),
  resumeCampaign: vi.fn(),
  createCampaignQueues: vi.fn(),
  closeCampaignQueues: vi.fn(),
  setCallBridge: vi.fn(),
}));

import { startCampaign, pauseCampaign, resumeCampaign } from './engine.js';

let app: FastifyInstance;

beforeEach(async () => {
  prismaMock = createPrismaMock();
  vi.clearAllMocks();
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

const validCreateBody = {
  name: 'Spring Outreach',
  assistantId: '00000000-0000-4000-a000-000000000001',
  phoneNumberId: '00000000-0000-4000-a000-000000000002',
  contacts: [
    { name: 'Alice', number: '+15551110000' },
    { name: 'Bob', number: '+15552220000' },
  ],
  schedule: {
    startTime: '09:00',
    endTime: '17:00',
    timezone: 'America/New_York',
    maxConcurrent: 3,
  },
};

// -------------------------------------------------------------------------
// POST /api/campaigns (Create)
// -------------------------------------------------------------------------

describe('POST /api/campaigns', () => {
  it('returns 201 with the created campaign', async () => {
    const campaign = buildCampaign({ name: 'Spring Outreach' });
    prismaMock.campaign.create.mockResolvedValue(campaign);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/campaigns',
      headers: { authorization: `Bearer ${token}` },
      payload: validCreateBody,
    });

    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.name).toBe('Spring Outreach');
    expect(prismaMock.campaign.create).toHaveBeenCalledOnce();
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/campaigns',
      payload: validCreateBody,
    });

    expect(res.statusCode).toBe(401);
  });

  it('returns 400 when name is missing', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/campaigns',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        assistantId: '00000000-0000-4000-a000-000000000001',
        phoneNumberId: '00000000-0000-4000-a000-000000000002',
      },
    });

    expect(res.statusCode).toBe(400);
  });

  it('returns 400 when assistantId is not a valid UUID', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/campaigns',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        name: 'Bad Campaign',
        assistantId: 'not-a-uuid',
        phoneNumberId: '00000000-0000-4000-a000-000000000002',
      },
    });

    expect(res.statusCode).toBe(400);
  });

  it('returns 400 when phoneNumberId is not a valid UUID', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/campaigns',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        name: 'Bad Campaign',
        assistantId: '00000000-0000-4000-a000-000000000001',
        phoneNumberId: 'not-a-uuid',
      },
    });

    expect(res.statusCode).toBe(400);
  });

  it('defaults contacts to an empty array when not provided', async () => {
    const campaign = buildCampaign({ contacts: [] });
    prismaMock.campaign.create.mockResolvedValue(campaign);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/campaigns',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        name: 'No Contacts Campaign',
        assistantId: '00000000-0000-4000-a000-000000000001',
        phoneNumberId: '00000000-0000-4000-a000-000000000002',
      },
    });

    expect(res.statusCode).toBe(201);
    expect(prismaMock.campaign.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ contacts: [] }),
      }),
    );
  });
});

// -------------------------------------------------------------------------
// GET /api/campaigns (List)
// -------------------------------------------------------------------------

describe('GET /api/campaigns', () => {
  it('returns 200 with a list of campaigns', async () => {
    const campaigns = [buildCampaign({ name: 'Camp A' }), buildCampaign({ name: 'Camp B' })];
    prismaMock.campaign.findMany.mockResolvedValue(campaigns);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/campaigns',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data).toHaveLength(2);
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/campaigns',
    });

    expect(res.statusCode).toBe(401);
  });
});

// -------------------------------------------------------------------------
// GET /api/campaigns/:id (Get by ID)
// -------------------------------------------------------------------------

describe('GET /api/campaigns/:id', () => {
  it('returns 200 with the campaign when found', async () => {
    const campaign = buildCampaign({ id: 'camp-1' });
    prismaMock.campaign.findFirst.mockResolvedValue(campaign);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/campaigns/camp-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.id).toBe('camp-1');
  });

  it('returns 404 when campaign does not exist', async () => {
    prismaMock.campaign.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/campaigns/nonexistent',
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
      url: '/api/campaigns/camp-1',
    });

    expect(res.statusCode).toBe(401);
  });
});

// -------------------------------------------------------------------------
// PATCH /api/campaigns/:id (Update)
// -------------------------------------------------------------------------

describe('PATCH /api/campaigns/:id', () => {
  it('returns 200 with the updated campaign', async () => {
    const existing = buildCampaign({ id: 'camp-1', name: 'Old Name' });
    const updated = buildCampaign({ id: 'camp-1', name: 'New Name' });
    prismaMock.campaign.findFirst.mockResolvedValue(existing);
    prismaMock.campaign.update.mockResolvedValue(updated);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/campaigns/camp-1',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'New Name' },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.name).toBe('New Name');
    expect(prismaMock.campaign.update).toHaveBeenCalledWith({
      where: { id: 'camp-1' },
      data: { name: 'New Name' },
    });
  });

  it('returns 404 when the campaign does not exist', async () => {
    prismaMock.campaign.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/campaigns/nonexistent',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'Updated' },
    });

    expect(res.statusCode).toBe(404);
    expect(res.json().error.code).toBe('NOT_FOUND');
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'PATCH',
      url: '/api/campaigns/camp-1',
      payload: { name: 'Updated' },
    });

    expect(res.statusCode).toBe(401);
  });
});

// -------------------------------------------------------------------------
// DELETE /api/campaigns/:id
// -------------------------------------------------------------------------

describe('DELETE /api/campaigns/:id', () => {
  it('returns 204 on successful deletion', async () => {
    const existing = buildCampaign({ id: 'camp-1' });
    prismaMock.campaign.findFirst.mockResolvedValue(existing);
    prismaMock.campaign.delete.mockResolvedValue(existing);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/campaigns/camp-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(204);
    expect(prismaMock.campaign.delete).toHaveBeenCalledWith({ where: { id: 'camp-1' } });
  });

  it('returns 404 when campaign does not exist', async () => {
    prismaMock.campaign.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/campaigns/nonexistent',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
    expect(res.json().error.code).toBe('NOT_FOUND');
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'DELETE',
      url: '/api/campaigns/camp-1',
    });

    expect(res.statusCode).toBe(401);
  });
});

// -------------------------------------------------------------------------
// POST /api/campaigns/:id/start
// -------------------------------------------------------------------------

describe('POST /api/campaigns/:id/start', () => {
  it('returns 200 after starting the campaign', async () => {
    const campaign = buildCampaign({ id: 'camp-1', status: 'DRAFT' });
    const updatedCampaign = buildCampaign({ id: 'camp-1', status: 'RUNNING' });
    prismaMock.campaign.findFirst.mockResolvedValue(campaign);
    prismaMock.campaign.findUnique.mockResolvedValue(updatedCampaign);
    vi.mocked(startCampaign).mockResolvedValue(undefined);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/campaigns/camp-1/start',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.status).toBe('RUNNING');
    expect(startCampaign).toHaveBeenCalledWith('camp-1', 'test-org-id');
  });

  it('returns 404 when campaign does not exist', async () => {
    prismaMock.campaign.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/campaigns/nonexistent/start',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
    expect(res.json().error.code).toBe('NOT_FOUND');
    expect(startCampaign).not.toHaveBeenCalled();
  });
});

// -------------------------------------------------------------------------
// POST /api/campaigns/:id/pause
// -------------------------------------------------------------------------

describe('POST /api/campaigns/:id/pause', () => {
  it('returns 200 after pausing the campaign', async () => {
    const campaign = buildCampaign({ id: 'camp-1', status: 'RUNNING' });
    const pausedCampaign = buildCampaign({ id: 'camp-1', status: 'PAUSED' });
    prismaMock.campaign.findFirst.mockResolvedValue(campaign);
    prismaMock.campaign.findUnique.mockResolvedValue(pausedCampaign);
    vi.mocked(pauseCampaign).mockResolvedValue(undefined);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/campaigns/camp-1/pause',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.status).toBe('PAUSED');
    expect(pauseCampaign).toHaveBeenCalledWith('camp-1', 'test-org-id');
  });

  it('returns 404 when campaign does not exist', async () => {
    prismaMock.campaign.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/campaigns/nonexistent/pause',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
    expect(res.json().error.code).toBe('NOT_FOUND');
    expect(pauseCampaign).not.toHaveBeenCalled();
  });
});

// -------------------------------------------------------------------------
// POST /api/campaigns/:id/resume
// -------------------------------------------------------------------------

describe('POST /api/campaigns/:id/resume', () => {
  it('returns 200 after resuming the campaign', async () => {
    const campaign = buildCampaign({ id: 'camp-1', status: 'PAUSED' });
    const resumedCampaign = buildCampaign({ id: 'camp-1', status: 'RUNNING' });
    prismaMock.campaign.findFirst.mockResolvedValue(campaign);
    prismaMock.campaign.findUnique.mockResolvedValue(resumedCampaign);
    vi.mocked(resumeCampaign).mockResolvedValue(undefined);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/campaigns/camp-1/resume',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.status).toBe('RUNNING');
    expect(resumeCampaign).toHaveBeenCalledWith('camp-1', 'test-org-id');
  });

  it('returns 404 when campaign does not exist', async () => {
    prismaMock.campaign.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/campaigns/nonexistent/resume',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
    expect(res.json().error.code).toBe('NOT_FOUND');
    expect(resumeCampaign).not.toHaveBeenCalled();
  });
});
