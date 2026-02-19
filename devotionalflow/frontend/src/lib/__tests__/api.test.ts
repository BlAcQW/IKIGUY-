import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../api';

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('has getAdminAnalytics method', () => {
    expect(typeof apiClient.getAdminAnalytics).toBe('function');
  });

  it('has getSeriesDevotionals method', () => {
    expect(typeof apiClient.getSeriesDevotionals).toBe('function');
  });

  it('getAdminAnalytics calls correct endpoint', async () => {
    const mockGet = vi.fn().mockResolvedValue({ data: {} });
    apiClient.client.get = mockGet as any;

    await apiClient.getAdminAnalytics(30);

    expect(mockGet).toHaveBeenCalledWith('/analytics/dashboard', {
      params: { days: 30 },
    });
  });

  it('getSeriesDevotionals calls correct endpoint', async () => {
    const mockGet = vi.fn().mockResolvedValue({ data: [] });
    apiClient.client.get = mockGet as any;

    await apiClient.getSeriesDevotionals('test-series-id');

    expect(mockGet).toHaveBeenCalledWith('/series/test-series-id/devotionals');
  });
});

