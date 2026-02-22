import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';

let prismaMock: PrismaMock;

vi.mock('../../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
}));

import { createCall, updateCallStatus, endCall, failCall, getCall, listCalls } from './service.js';

beforeEach(() => {
  prismaMock = createPrismaMock();
});

describe('createCall', () => {
  it('creates a call record with QUEUED status', async () => {
    const expected = { id: 'call-1', status: 'QUEUED', type: 'WEB' };
    prismaMock.call.create.mockResolvedValue(expected);

    const result = await createCall({
      organizationId: 'org-1',
      assistantId: 'ast-1',
      type: 'WEB',
    });

    expect(result.status).toBe('QUEUED');
    expect(prismaMock.call.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          organizationId: 'org-1',
          assistantId: 'ast-1',
          type: 'WEB',
          status: 'QUEUED',
        }),
      })
    );
  });
});

describe('updateCallStatus', () => {
  it('updates call status', async () => {
    prismaMock.call.update.mockResolvedValue({ id: 'call-1', status: 'IN_PROGRESS' });

    await updateCallStatus('call-1', 'IN_PROGRESS');

    expect(prismaMock.call.update).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: 'call-1' },
        data: expect.objectContaining({ status: 'IN_PROGRESS' }),
      })
    );
  });

  it('sets startedAt when status is IN_PROGRESS', async () => {
    prismaMock.call.update.mockResolvedValue({ id: 'call-1', status: 'IN_PROGRESS' });

    await updateCallStatus('call-1', 'IN_PROGRESS');

    const callData = prismaMock.call.update.mock.calls[0][0].data;
    expect(callData.startedAt).toBeInstanceOf(Date);
  });
});

describe('endCall', () => {
  it('ends the call with transcript and duration', async () => {
    const startedAt = new Date(Date.now() - 30000);
    prismaMock.call.findUnique.mockResolvedValue({ id: 'call-1', startedAt });
    prismaMock.call.update.mockResolvedValue({ id: 'call-1', status: 'ENDED' });

    const transcript = [{ role: 'user', content: 'Hi' }, { role: 'assistant', content: 'Hello' }];
    await endCall('call-1', transcript);

    expect(prismaMock.call.update).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          status: 'ENDED',
          transcript,
          endReason: 'completed',
        }),
      })
    );
    const data = prismaMock.call.update.mock.calls[0][0].data;
    expect(data.duration).toBeGreaterThanOrEqual(29);
  });

  it('throws 404 if call not found', async () => {
    prismaMock.call.findUnique.mockResolvedValue(null);

    await expect(endCall('bad-id', [])).rejects.toThrow('Call not found');
    await expect(endCall('bad-id', [])).rejects.toMatchObject({ statusCode: 404 });
  });
});

describe('failCall', () => {
  it('marks call as failed with reason', async () => {
    prismaMock.call.update.mockResolvedValue({ id: 'call-1', status: 'FAILED' });

    await failCall('call-1', 'websocket_error');

    expect(prismaMock.call.update).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          status: 'FAILED',
          endReason: 'websocket_error',
        }),
      })
    );
  });
});

describe('getCall', () => {
  it('returns the call when found', async () => {
    prismaMock.call.findFirst.mockResolvedValue({ id: 'call-1', organizationId: 'org-1' });

    const result = await getCall('call-1', 'org-1');
    expect(result.id).toBe('call-1');
  });

  it('throws 404 when not found', async () => {
    prismaMock.call.findFirst.mockResolvedValue(null);

    await expect(getCall('bad', 'org-1')).rejects.toThrow('Call not found');
  });
});

describe('listCalls', () => {
  it('returns paginated calls', async () => {
    prismaMock.call.findMany.mockResolvedValue([{ id: 'call-1' }]);
    prismaMock.call.count.mockResolvedValue(1);

    const result = await listCalls('org-1', { page: 1, limit: 20 });

    expect(result.data).toHaveLength(1);
    expect(result.meta.total).toBe(1);
  });

  it('filters by status when provided', async () => {
    prismaMock.call.findMany.mockResolvedValue([]);
    prismaMock.call.count.mockResolvedValue(0);

    await listCalls('org-1', { page: 1, limit: 20, status: 'ENDED' });

    expect(prismaMock.call.findMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: expect.objectContaining({ status: 'ENDED' }),
      })
    );
  });
});
