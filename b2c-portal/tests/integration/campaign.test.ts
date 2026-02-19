import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { campaignApi } from '../../src/lib/core-api';

vi.mock('../../src/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'test-token' } },
      }),
    },
  },
}));

const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('campaign workflow', () => {
  const baseUrl = 'http://localhost:8000/internal/campaigns';
  const payload = {
    name: 'Test Campaign',
    assistant_id: '00000000-0000-0000-0000-000000000001',
    audience_id: '00000000-0000-0000-0000-000000000002',
    tenant_id: '00000000-0000-0000-0000-000000000001',
  };

  it('sends correct payload and handles success', async () => {
    let receivedBody: typeof payload | null = null;
    server.use(
      http.post(baseUrl, async ({ request }) => {
        receivedBody = (await request.json()) as typeof payload;
        return HttpResponse.json({ id: 'cmp_1', status: 'draft', ...payload, created_at: 'now', updated_at: 'now' });
      })
    );

    const result = await campaignApi.create(payload);
    expect(receivedBody).toEqual(payload);
    expect(result.id).toBe('cmp_1');
    expect(result.status).toBe('draft');
  });

  it('handles validation errors', async () => {
    server.use(
      http.post(baseUrl, () =>
        HttpResponse.json({ detail: 'Invalid campaign' }, { status: 400 })
      )
    );

    await expect(campaignApi.create(payload)).rejects.toThrow('Invalid campaign');
  });

  it('handles server errors', async () => {
    server.use(
      http.post(baseUrl, () =>
        HttpResponse.json({ detail: 'Server error' }, { status: 500 })
      )
    );

    await expect(campaignApi.create(payload)).rejects.toThrow('Server error');
  });
});
