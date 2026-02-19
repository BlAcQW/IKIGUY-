import { assistantApi, paymentApi } from '../core-api';
import { vi } from 'vitest';

// Mock MongoDB auth
vi.mock('@/lib/mongo-auth', () => ({
  mongoAuth: {
    getAccessToken: vi.fn(),
    isAuthenticated: vi.fn(),
    getUser: vi.fn(),
    getTenantId: vi.fn()
  }
}));

// Import after mocking
import { mongoAuth } from '@/lib/mongo-auth';

global.fetch = vi.fn();

describe('assistantApi.list', () => {
  beforeEach(() => {
    vi.mocked(mongoAuth.getAccessToken).mockReset();
    vi.mocked(mongoAuth.isAuthenticated).mockReset();
    (fetch as any).mockReset();
  });

  it('returns assistants on success', async () => {
    vi.mocked(mongoAuth.isAuthenticated).mockReturnValue(true);
    vi.mocked(mongoAuth.getAccessToken).mockReturnValue('mock-token');
    (fetch as any).mockResolvedValue({ ok: true, json: () => Promise.resolve([{ id: 'a1' }]) });

    const result = await assistantApi.list('tenant');
    expect(result).toEqual([{ id: 'a1' }]);
  });

  it('throws when no session token', async () => {
    vi.mocked(mongoAuth.isAuthenticated).mockReturnValue(false);
    vi.mocked(mongoAuth.getAccessToken).mockReturnValue(null);
    await expect(assistantApi.list('tenant')).rejects.toThrow('No active MongoDB session');
  });

  it('throws on fetch error', async () => {
    vi.mocked(mongoAuth.isAuthenticated).mockReturnValue(true);
    vi.mocked(mongoAuth.getAccessToken).mockReturnValue('mock-token');
    (fetch as any).mockResolvedValue({ ok: false, status: 500, statusText: 'Server Error', json: () => Promise.resolve({ detail: 'bad' }) });
    await expect(assistantApi.list('tenant')).rejects.toThrow('bad');
  });
});

describe('paymentApi.getWalletBalance', () => {
  beforeEach(() => {
    vi.mocked(mongoAuth.getAccessToken).mockReset();
    vi.mocked(mongoAuth.isAuthenticated).mockReset();
    (fetch as any).mockReset();
  });

  it('returns balance on success', async () => {
    vi.mocked(mongoAuth.isAuthenticated).mockReturnValue(true);
    vi.mocked(mongoAuth.getAccessToken).mockReturnValue('mock-token');
    (fetch as any).mockResolvedValue({ ok: true, json: () => Promise.resolve({ balance: 20 }) });
    const result = await paymentApi.getWalletBalance('tenant');
    expect(result.balance).toBe(20);
  });

  it('handles zero balance edge case', async () => {
    vi.mocked(mongoAuth.isAuthenticated).mockReturnValue(true);
    vi.mocked(mongoAuth.getAccessToken).mockReturnValue('mock-token');
    (fetch as any).mockResolvedValue({ ok: true, json: () => Promise.resolve({ balance: 0 }) });
    const result = await paymentApi.getWalletBalance('tenant');
    expect(result.balance).toBe(0);
  });

  it('throws on failure', async () => {
    vi.mocked(mongoAuth.isAuthenticated).mockReturnValue(true);
    vi.mocked(mongoAuth.getAccessToken).mockReturnValue('mock-token');
    (fetch as any).mockResolvedValue({ ok: false, status: 500, statusText: 'Server Error', json: () => Promise.resolve({ detail: 'fail' }) });
    await expect(paymentApi.getWalletBalance('tenant')).rejects.toThrow('fail');
  });
});