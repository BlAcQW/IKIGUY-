import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { assistantApi } from '../../src/lib/core-api';

// Mock Supabase session retrieval
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

describe('assistant workflow', () => {
  const baseUrl = 'http://localhost:8000/internal/assistants';
  const payload = {
    name: 'Test Assistant',
    template: 'sales',
    channel: 'voice',
    language: 'en',
    voice: 'standard',
    prompt: 'Hello there',
    tenant_id: '00000000-0000-0000-0000-000000000001',
  };

  it('sends correct payload and handles success', async () => {
    let receivedBody: typeof payload | null = null;
    server.use(
      http.post(baseUrl, async ({ request }) => {
        receivedBody = (await request.json()) as typeof payload;
        return HttpResponse.json({ id: 'asst_1', ...payload, created_at: 'now', updated_at: 'now' });
      })
    );

    const result = await assistantApi.create(payload);
    expect(receivedBody).toEqual(payload);
    expect(result.id).toBe('asst_1');
  });

  it('handles validation error responses', async () => {
    server.use(
      http.post(baseUrl, () =>
        HttpResponse.json({ detail: 'Invalid data' }, { status: 400 })
      )
    );

    await expect(assistantApi.create(payload)).rejects.toThrow('Invalid data');
  });

  it('handles server errors', async () => {
    server.use(
      http.post(baseUrl, () =>
        HttpResponse.json({ detail: 'Server exploded' }, { status: 500 })
      )
    );

    await expect(assistantApi.create(payload)).rejects.toThrow('Server exploded');
  });
});
