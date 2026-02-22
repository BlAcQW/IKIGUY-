import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';

let prismaMock: PrismaMock;

vi.mock('../../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
}));

import { getAnalyticsSummary } from './service.js';

beforeEach(() => {
  prismaMock = createPrismaMock();
});

describe('getAnalyticsSummary', () => {
  it('should return summary with correct counts and rates', async () => {
    prismaMock.call.count
      .mockResolvedValueOnce(100)   // totalCalls
      .mockResolvedValueOnce(80)    // completedCalls
      .mockResolvedValueOnce(10);   // failedCalls

    prismaMock.call.aggregate.mockResolvedValue({
      _avg: { duration: 120 },
      _sum: { duration: 6000 },
    });

    prismaMock.call.groupBy
      .mockResolvedValueOnce([      // byType
        { type: 'WEB', _count: 50 },
        { type: 'INBOUND', _count: 30 },
        { type: 'OUTBOUND', _count: 20 },
      ])
      .mockResolvedValueOnce([      // byAssistant
        { assistantId: 'a-1', _count: 60 },
        { assistantId: 'a-2', _count: 40 },
      ]);

    prismaMock.assistant.findMany.mockResolvedValue([
      { id: 'a-1', name: 'Sales Bot' },
      { id: 'a-2', name: 'Support Bot' },
    ]);

    const result = await getAnalyticsSummary('org-1', {});

    expect(result.totalCalls).toBe(100);
    expect(result.completedCalls).toBe(80);
    expect(result.failedCalls).toBe(10);
    expect(result.successRate).toBe(80);
    expect(result.avgDuration).toBe(120);
    expect(result.totalMinutes).toBe(100);
    expect(result.byType).toHaveLength(3);
    expect(result.byAssistant).toHaveLength(2);
    expect(result.byAssistant[0].assistantName).toBe('Sales Bot');
  });

  it('should handle empty data (no calls)', async () => {
    prismaMock.call.count.mockResolvedValue(0);
    prismaMock.call.aggregate.mockResolvedValue({
      _avg: { duration: null },
      _sum: { duration: null },
    });
    prismaMock.call.groupBy.mockResolvedValue([]);

    const result = await getAnalyticsSummary('org-1', {});

    expect(result.totalCalls).toBe(0);
    expect(result.successRate).toBe(0);
    expect(result.avgDuration).toBe(0);
    expect(result.totalMinutes).toBe(0);
    expect(result.byType).toEqual([]);
    expect(result.byAssistant).toEqual([]);
  });

  it('should pass filter parameters correctly', async () => {
    prismaMock.call.count.mockResolvedValue(0);
    prismaMock.call.aggregate.mockResolvedValue({
      _avg: { duration: null },
      _sum: { duration: null },
    });
    prismaMock.call.groupBy.mockResolvedValue([]);

    await getAnalyticsSummary('org-1', {
      assistantId: 'a-1',
      type: 'WEB',
      from: '2026-01-01T00:00:00Z',
      to: '2026-01-31T23:59:59Z',
    });

    // Verify the first call.count was called with correct filters
    const countCall = prismaMock.call.count.mock.calls[0][0];
    expect(countCall.where.organizationId).toBe('org-1');
    expect(countCall.where.assistantId).toBe('a-1');
    expect(countCall.where.type).toBe('WEB');
  });
});
