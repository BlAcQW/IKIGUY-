import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildPhoneNumber, buildAssistant } from '../../../tests/helpers/factories.js';
import type { FastifyInstance } from 'fastify';

let prismaMock: PrismaMock;

vi.mock('../../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
  connectDatabase: vi.fn(),
  disconnectDatabase: vi.fn(),
}));

vi.mock('../../telephony/twilio.js', () => ({
  searchAvailableNumbers: vi.fn(),
  buyNumber: vi.fn(),
  releaseNumber: vi.fn(),
  configureNumberWebhooks: vi.fn(),
}));

import {
  searchAvailableNumbers,
  buyNumber,
  releaseNumber as twilioRelease,
} from '../../telephony/twilio.js';

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

// ---------------------------------------------------------------------------
// GET /api/phone-numbers — List phone numbers
// ---------------------------------------------------------------------------

describe('GET /api/phone-numbers', () => {
  it('returns 200 with paginated phone numbers', async () => {
    const numbers = [
      buildPhoneNumber({ organizationId: 'test-org-id', number: '+15551110001' }),
      buildPhoneNumber({ organizationId: 'test-org-id', number: '+15551110002' }),
    ];
    prismaMock.phoneNumber.findMany.mockResolvedValue(numbers);
    prismaMock.phoneNumber.count.mockResolvedValue(2);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/phone-numbers',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data).toHaveLength(2);
    expect(body.meta).toEqual({ total: 2, page: 1, limit: 20 });
  });

  it('returns 200 with custom page and limit', async () => {
    prismaMock.phoneNumber.findMany.mockResolvedValue([]);
    prismaMock.phoneNumber.count.mockResolvedValue(0);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/phone-numbers?page=2&limit=5',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.meta).toEqual({ total: 0, page: 2, limit: 5 });
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/phone-numbers',
    });

    expect(res.statusCode).toBe(401);
  });
});

// ---------------------------------------------------------------------------
// GET /api/phone-numbers/:id — Get single phone number
// ---------------------------------------------------------------------------

describe('GET /api/phone-numbers/:id', () => {
  it('returns 200 with the phone number', async () => {
    const phoneNumber = buildPhoneNumber({ id: 'pn-1', organizationId: 'test-org-id' });
    prismaMock.phoneNumber.findFirst.mockResolvedValue(phoneNumber);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/phone-numbers/pn-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.id).toBe('pn-1');
  });

  it('returns 404 when phone number does not exist', async () => {
    prismaMock.phoneNumber.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'GET',
      url: '/api/phone-numbers/nonexistent',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'GET',
      url: '/api/phone-numbers/pn-1',
    });

    expect(res.statusCode).toBe(401);
  });
});

// ---------------------------------------------------------------------------
// POST /api/phone-numbers/search — Search available numbers
// ---------------------------------------------------------------------------

describe('POST /api/phone-numbers/search', () => {
  it('returns 200 with available numbers from Twilio', async () => {
    const available = [
      { number: '+15551110001', friendlyName: '(555) 111-0001', locality: 'New York', region: 'NY', country: 'US', capabilities: { voice: true, sms: true, mms: false } },
    ];
    vi.mocked(searchAvailableNumbers).mockResolvedValue(available);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/phone-numbers/search',
      headers: { authorization: `Bearer ${token}` },
      payload: { country: 'US', type: 'local', limit: 5 },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data).toHaveLength(1);
    expect(body.data[0].number).toBe('+15551110001');
  });

  it('uses default values when optional fields are omitted', async () => {
    vi.mocked(searchAvailableNumbers).mockResolvedValue([]);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/phone-numbers/search',
      headers: { authorization: `Bearer ${token}` },
      payload: {},
    });

    expect(res.statusCode).toBe(200);
    expect(searchAvailableNumbers).toHaveBeenCalledWith(
      expect.objectContaining({ country: 'US', type: 'local', limit: 10 }),
    );
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/phone-numbers/search',
      payload: { country: 'US' },
    });

    expect(res.statusCode).toBe(401);
  });
});

// ---------------------------------------------------------------------------
// POST /api/phone-numbers — Purchase Twilio number
// ---------------------------------------------------------------------------

describe('POST /api/phone-numbers (Twilio purchase)', () => {
  it('returns 201 when purchasing a Twilio number', async () => {
    const purchased = { number: '+15559876543', sid: 'PN_abc123', friendlyName: '(555) 987-6543' };
    vi.mocked(buyNumber).mockResolvedValue(purchased);
    const storedNumber = buildPhoneNumber({
      organizationId: 'test-org-id',
      number: '+15559876543',
      twilioSid: 'PN_abc123',
      provider: 'TWILIO',
    });
    prismaMock.phoneNumber.create.mockResolvedValue(storedNumber);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/phone-numbers',
      headers: { authorization: `Bearer ${token}` },
      payload: { phoneNumber: '+15559876543', name: 'Main Line' },
    });

    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.number).toBe('+15559876543');
    expect(buyNumber).toHaveBeenCalledWith('+15559876543', expect.any(String));
  });

  it('returns 400 for invalid E.164 phone number format', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/phone-numbers',
      headers: { authorization: `Bearer ${token}` },
      payload: { phoneNumber: '5551234567' },
    });

    expect(res.statusCode).toBe(400);
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/phone-numbers',
      payload: { phoneNumber: '+15551234567' },
    });

    expect(res.statusCode).toBe(401);
  });
});

// ---------------------------------------------------------------------------
// POST /api/phone-numbers — Create SIP trunk number
// ---------------------------------------------------------------------------

describe('POST /api/phone-numbers (SIP_TRUNK)', () => {
  it('returns 201 when registering a SIP trunk number', async () => {
    const sipNumber = buildPhoneNumber({
      organizationId: 'test-org-id',
      number: '+15553334444',
      provider: 'SIP_TRUNK',
      sipDomain: 'sip.example.com',
    });
    prismaMock.phoneNumber.create.mockResolvedValue(sipNumber);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/phone-numbers',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        provider: 'SIP_TRUNK',
        number: '+15553334444',
        name: 'SIP Line',
        sipDomain: 'sip.example.com',
      },
    });

    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.provider).toBe('SIP_TRUNK');
    expect(buyNumber).not.toHaveBeenCalled();
  });

  it('returns 400 for invalid phone number format on SIP trunk', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/phone-numbers',
      headers: { authorization: `Bearer ${token}` },
      payload: { provider: 'SIP_TRUNK', number: 'not-a-number' },
    });

    expect(res.statusCode).toBe(400);
  });
});

// ---------------------------------------------------------------------------
// POST /api/phone-numbers — Create GoIP number
// ---------------------------------------------------------------------------

describe('POST /api/phone-numbers (GOIP)', () => {
  it('returns 201 when registering a GoIP number', async () => {
    const goipNumber = buildPhoneNumber({
      organizationId: 'test-org-id',
      number: '+233241234567',
      provider: 'GOIP',
      metadata: { trunkName: 'goip-trunk', country: 'GH', gateway: 'GoIP/Hybertone' },
    });
    prismaMock.phoneNumber.create.mockResolvedValue(goipNumber);
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/phone-numbers',
      headers: { authorization: `Bearer ${token}` },
      payload: {
        provider: 'GOIP',
        number: '+233241234567',
        name: 'Ghana Line',
        trunkName: 'goip-trunk',
        country: 'GH',
      },
    });

    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.provider).toBe('GOIP');
    expect(buyNumber).not.toHaveBeenCalled();
  });

  it('returns 400 for invalid phone number format on GoIP', async () => {
    const token = generateToken();

    const res = await app.inject({
      method: 'POST',
      url: '/api/phone-numbers',
      headers: { authorization: `Bearer ${token}` },
      payload: { provider: 'GOIP', number: 'invalid' },
    });

    expect(res.statusCode).toBe(400);
  });
});

// ---------------------------------------------------------------------------
// PATCH /api/phone-numbers/:id — Update phone number
// ---------------------------------------------------------------------------

describe('PATCH /api/phone-numbers/:id', () => {
  it('returns 200 when updating the name', async () => {
    const existing = buildPhoneNumber({ id: 'pn-1', organizationId: 'test-org-id', status: 'ACTIVE' });
    const updated = { ...existing, name: 'Renamed Line' };
    prismaMock.phoneNumber.findFirst.mockResolvedValue(existing);
    prismaMock.phoneNumber.update.mockResolvedValue(updated);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/phone-numbers/pn-1',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'Renamed Line' },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.name).toBe('Renamed Line');
  });

  it('returns 200 when assigning an assistant', async () => {
    const assistantId = '00000000-0000-4000-a000-000000000001';
    const existing = buildPhoneNumber({ id: 'pn-1', organizationId: 'test-org-id', status: 'ACTIVE' });
    const assistant = buildAssistant({ id: assistantId, organizationId: 'test-org-id' });
    const updated = { ...existing, assistantId };
    prismaMock.phoneNumber.findFirst.mockResolvedValue(existing);
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.phoneNumber.update.mockResolvedValue(updated);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/phone-numbers/pn-1',
      headers: { authorization: `Bearer ${token}` },
      payload: { assistantId },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.assistantId).toBe(assistantId);
  });

  it('returns 200 when unassigning an assistant with null', async () => {
    const existing = buildPhoneNumber({ id: 'pn-1', organizationId: 'test-org-id', status: 'ACTIVE', assistantId: 'asst-1' });
    const updated = { ...existing, assistantId: null };
    prismaMock.phoneNumber.findFirst.mockResolvedValue(existing);
    prismaMock.phoneNumber.update.mockResolvedValue(updated);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/phone-numbers/pn-1',
      headers: { authorization: `Bearer ${token}` },
      payload: { assistantId: null },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.assistantId).toBeNull();
  });

  it('returns 404 when phone number does not exist', async () => {
    prismaMock.phoneNumber.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/phone-numbers/nonexistent',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'New Name' },
    });

    expect(res.statusCode).toBe(404);
  });

  it('returns 400 when updating a released phone number', async () => {
    const released = buildPhoneNumber({ id: 'pn-1', organizationId: 'test-org-id', status: 'RELEASED' });
    prismaMock.phoneNumber.findFirst.mockResolvedValue(released);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/phone-numbers/pn-1',
      headers: { authorization: `Bearer ${token}` },
      payload: { name: 'New Name' },
    });

    expect(res.statusCode).toBe(400);
  });

  it('returns 404 when assigning a nonexistent assistant', async () => {
    const existing = buildPhoneNumber({ id: 'pn-1', organizationId: 'test-org-id', status: 'ACTIVE' });
    prismaMock.phoneNumber.findFirst.mockResolvedValue(existing);
    prismaMock.assistant.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'PATCH',
      url: '/api/phone-numbers/pn-1',
      headers: { authorization: `Bearer ${token}` },
      payload: { assistantId: '00000000-0000-0000-0000-000000000000' },
    });

    expect(res.statusCode).toBe(404);
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'PATCH',
      url: '/api/phone-numbers/pn-1',
      payload: { name: 'New Name' },
    });

    expect(res.statusCode).toBe(401);
  });
});

// ---------------------------------------------------------------------------
// DELETE /api/phone-numbers/:id — Release phone number
// ---------------------------------------------------------------------------

describe('DELETE /api/phone-numbers/:id', () => {
  it('returns 200 when releasing a Twilio number', async () => {
    const existing = buildPhoneNumber({
      id: 'pn-1',
      organizationId: 'test-org-id',
      provider: 'TWILIO',
      twilioSid: 'PN_abc123',
      status: 'ACTIVE',
    });
    const released = { ...existing, status: 'RELEASED', assistantId: null };
    prismaMock.phoneNumber.findFirst.mockResolvedValue(existing);
    prismaMock.phoneNumber.update.mockResolvedValue(released);
    vi.mocked(twilioRelease).mockResolvedValue(undefined);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/phone-numbers/pn-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.success).toBe(true);
    expect(body.data.status).toBe('RELEASED');
    expect(twilioRelease).toHaveBeenCalledWith('PN_abc123');
  });

  it('returns 200 when releasing a SIP trunk number without calling Twilio', async () => {
    const existing = buildPhoneNumber({
      id: 'pn-2',
      organizationId: 'test-org-id',
      provider: 'SIP_TRUNK',
      twilioSid: null,
      status: 'ACTIVE',
    });
    const released = { ...existing, status: 'RELEASED', assistantId: null };
    prismaMock.phoneNumber.findFirst.mockResolvedValue(existing);
    prismaMock.phoneNumber.update.mockResolvedValue(released);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/phone-numbers/pn-2',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(200);
    expect(body(res).data.status).toBe('RELEASED');
    expect(twilioRelease).not.toHaveBeenCalled();
  });

  it('returns 404 when phone number does not exist', async () => {
    prismaMock.phoneNumber.findFirst.mockResolvedValue(null);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/phone-numbers/nonexistent',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(404);
  });

  it('returns 400 when phone number is already released', async () => {
    const released = buildPhoneNumber({
      id: 'pn-1',
      organizationId: 'test-org-id',
      status: 'RELEASED',
    });
    prismaMock.phoneNumber.findFirst.mockResolvedValue(released);
    const token = generateToken();

    const res = await app.inject({
      method: 'DELETE',
      url: '/api/phone-numbers/pn-1',
      headers: { authorization: `Bearer ${token}` },
    });

    expect(res.statusCode).toBe(400);
  });

  it('returns 401 without authorization', async () => {
    const res = await app.inject({
      method: 'DELETE',
      url: '/api/phone-numbers/pn-1',
    });

    expect(res.statusCode).toBe(401);
  });
});

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

function body(res: { json: () => Record<string, unknown> }) {
  return res.json() as { success: boolean; data: Record<string, unknown>; meta?: Record<string, unknown> };
}
