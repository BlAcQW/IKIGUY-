import { describe, it, expect, vi, beforeEach } from 'vitest';
import { campaignApi } from '@/lib/core-api';

// Mock fetch and Supabase client
global.fetch = vi.fn();

vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'mock-token' } },
      }),
    },
  },
}));

describe('campaignApi actions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('starts a campaign', async () => {
    const mockResponse = {
      id: '00000000-0000-0000-0000-000000000001',
      status: 'running',
    };
    (global.fetch as unknown as vi.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await campaignApi.start(
      '00000000-0000-0000-0000-000000000001',
    );
    expect(result).toEqual(mockResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining(
        '/internal/campaigns/00000000-0000-0000-0000-000000000001/start',
      ),
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('pauses a campaign', async () => {
    const mockResponse = {
      id: '00000000-0000-0000-0000-000000000001',
      status: 'paused',
    };
    (global.fetch as unknown as vi.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await campaignApi.pause(
      '00000000-0000-0000-0000-000000000001',
    );
    expect(result).toEqual(mockResponse);
  });

  it('handles start errors', async () => {
    (global.fetch as unknown as vi.Mock).mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ error: { message: 'Server Error' } }),
    });

    await expect(
      campaignApi.start('00000000-0000-0000-0000-000000000001'),
    ).rejects.toThrow('HTTP 500');
  });
});

