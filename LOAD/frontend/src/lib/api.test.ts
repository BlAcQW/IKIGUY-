import { describe, it, expect, vi, beforeEach } from 'vitest';

// We test by importing the module functions and mocking global fetch
const fetchMock = vi.fn();
vi.stubGlobal('fetch', fetchMock);

function mockResponse(data: unknown, ok = true, status = 200) {
  return {
    ok,
    status,
    json: vi.fn().mockResolvedValue(data),
  };
}

describe('api', () => {
  beforeEach(() => {
    fetchMock.mockReset();
    localStorage.clear();
  });

  describe('request() — auth headers', () => {
    it('attaches Authorization header when token exists', async () => {
      localStorage.setItem('load_token', 'my-token');
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));

      const { getMe } = await import('./api');
      await getMe();

      expect(fetchMock).toHaveBeenCalledWith(
        '/api/auth/me',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer my-token',
          }),
        }),
      );
    });

    it('omits Authorization header when no token', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));

      const { getMe } = await import('./api');
      await getMe();

      const headers = fetchMock.mock.calls[0][1].headers;
      expect(headers.Authorization).toBeUndefined();
    });

    it('includes Content-Type: application/json', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));

      const { getMe } = await import('./api');
      await getMe();

      expect(fetchMock).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        }),
      );
    });
  });

  describe('request() — response handling', () => {
    it('returns parsed JSON on 2xx response', async () => {
      const payload = { success: true, data: { userId: '1' } };
      fetchMock.mockResolvedValue(mockResponse(payload));

      const { getMe } = await import('./api');
      const result = await getMe();

      expect(result).toEqual(payload);
    });

    it('handles 204 No Content', async () => {
      fetchMock.mockResolvedValue({ ok: true, status: 204, json: vi.fn() });

      const { deleteAssistant } = await import('./api');
      const result = await deleteAssistant('abc');

      expect(result).toEqual({ success: true, data: null });
    });

    it('throws error with server message on non-OK response', async () => {
      fetchMock.mockResolvedValue(
        mockResponse({ error: { message: 'Not found', code: 'NOT_FOUND', statusCode: 404 } }, false, 404),
      );

      const { getAssistant } = await import('./api');
      await expect(getAssistant('missing')).rejects.toThrow('Not found');
    });

    it('throws generic message when server error has no message', async () => {
      fetchMock.mockResolvedValue(mockResponse({}, false, 500));

      const { getAssistant } = await import('./api');
      await expect(getAssistant('bad')).rejects.toThrow('Request failed');
    });
  });

  describe('Auth endpoints', () => {
    it('register sends POST with body', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: { token: 'tok', user: {}, organization: {} } }));

      const { register } = await import('./api');
      await register({ email: 'a@b.com', password: 'pass', name: 'Test', organizationName: 'Org' });

      expect(fetchMock).toHaveBeenCalledWith(
        '/api/auth/register',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'a@b.com', password: 'pass', name: 'Test', organizationName: 'Org' }),
        }),
      );
    });

    it('login sends POST with credentials', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: { token: 'tok', user: {}, organization: {} } }));

      const { login } = await import('./api');
      await login({ email: 'a@b.com', password: 'pass' });

      expect(fetchMock).toHaveBeenCalledWith(
        '/api/auth/login',
        expect.objectContaining({ method: 'POST' }),
      );
    });
  });

  describe('Assistants CRUD', () => {
    it('listAssistants sends correct query params', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));

      const { listAssistants } = await import('./api');
      await listAssistants(2, 10);

      expect(fetchMock).toHaveBeenCalledWith(
        '/api/assistants?page=2&limit=10',
        expect.any(Object),
      );
    });

    it('createAssistant sends POST body', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));

      const { createAssistant } = await import('./api');
      await createAssistant({ name: 'New Bot' });

      expect(fetchMock).toHaveBeenCalledWith(
        '/api/assistants',
        expect.objectContaining({ method: 'POST', body: JSON.stringify({ name: 'New Bot' }) }),
      );
    });

    it('updateAssistant sends PATCH to correct URL', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));

      const { updateAssistant } = await import('./api');
      await updateAssistant('id-1', { name: 'Updated' });

      expect(fetchMock).toHaveBeenCalledWith(
        '/api/assistants/id-1',
        expect.objectContaining({ method: 'PATCH' }),
      );
    });

    it('deleteAssistant sends DELETE', async () => {
      fetchMock.mockResolvedValue({ ok: true, status: 204, json: vi.fn() });

      const { deleteAssistant } = await import('./api');
      await deleteAssistant('id-1');

      expect(fetchMock).toHaveBeenCalledWith(
        '/api/assistants/id-1',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });
  });

  describe('API Keys', () => {
    it('listApiKeys sends GET', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { listApiKeys } = await import('./api');
      await listApiKeys();
      expect(fetchMock).toHaveBeenCalledWith('/api/api-keys', expect.any(Object));
    });

    it('createApiKey sends POST', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: { key: 'load_abc' } }));
      const { createApiKey } = await import('./api');
      await createApiKey({ name: 'Production' });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/api-keys',
        expect.objectContaining({ method: 'POST' }),
      );
    });

    it('revokeApiKey sends DELETE', async () => {
      fetchMock.mockResolvedValue({ ok: true, status: 204, json: vi.fn() });
      const { revokeApiKey } = await import('./api');
      await revokeApiKey('key-1');
      expect(fetchMock).toHaveBeenCalledWith('/api/api-keys/key-1', expect.objectContaining({ method: 'DELETE' }));
    });
  });

  describe('Calls', () => {
    it('listCalls sends correct pagination', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { listCalls } = await import('./api');
      await listCalls(3, 50);
      expect(fetchMock).toHaveBeenCalledWith('/api/calls?page=3&limit=50', expect.any(Object));
    });

    it('getCall sends GET to correct URL', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { getCall } = await import('./api');
      await getCall('call-123');
      expect(fetchMock).toHaveBeenCalledWith('/api/calls/call-123', expect.any(Object));
    });
  });

  describe('Tools', () => {
    it('listTools sends correct pagination', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { listTools } = await import('./api');
      await listTools(3, 15);
      expect(fetchMock).toHaveBeenCalledWith('/api/tools?page=3&limit=15', expect.any(Object));
    });

    it('createTool sends POST with body', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { createTool } = await import('./api');
      await createTool({ name: 'my_tool', type: 'FUNCTION' });
      expect(fetchMock).toHaveBeenCalledWith('/api/tools', expect.objectContaining({ method: 'POST' }));
    });

    it('updateTool sends PATCH to correct URL', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { updateTool } = await import('./api');
      await updateTool('tool-1', { name: 'updated_tool' });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/tools/tool-1',
        expect.objectContaining({ method: 'PATCH' }),
      );
    });

    it('deleteTool sends DELETE', async () => {
      fetchMock.mockResolvedValue({ ok: true, status: 204, json: vi.fn() });
      const { deleteTool } = await import('./api');
      await deleteTool('tool-1');
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/tools/tool-1',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });

    it('listToolTemplates sends GET', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { listToolTemplates } = await import('./api');
      await listToolTemplates();
      expect(fetchMock).toHaveBeenCalledWith('/api/tools/templates', expect.any(Object));
    });

    it('createToolFromTemplate sends POST with body', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { createToolFromTemplate } = await import('./api');
      await createToolFromTemplate({ templateName: 'calendar', serverUrl: 'https://example.com' });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/tools/from-template',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ templateName: 'calendar', serverUrl: 'https://example.com' }),
        }),
      );
    });

    it('bulkCreateToolsFromTemplates sends POST with body', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { bulkCreateToolsFromTemplates } = await import('./api');
      await bulkCreateToolsFromTemplates({ category: 'scheduling', serverUrl: 'https://example.com', assistantId: 'a1' });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/tools/from-templates/bulk',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ category: 'scheduling', serverUrl: 'https://example.com', assistantId: 'a1' }),
        }),
      );
    });
  });

  describe('Webhooks', () => {
    it('listWebhooks sends correct pagination', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { listWebhooks } = await import('./api');
      await listWebhooks(1, 25);
      expect(fetchMock).toHaveBeenCalledWith('/api/webhooks?page=1&limit=25', expect.any(Object));
    });

    it('createWebhook sends POST with body', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { createWebhook } = await import('./api');
      await createWebhook({ url: 'https://example.com/hook', events: ['call.started'] });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/webhooks',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ url: 'https://example.com/hook', events: ['call.started'] }),
        }),
      );
    });

    it('updateWebhook sends PATCH to correct URL', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { updateWebhook } = await import('./api');
      await updateWebhook('wh-1', { url: 'https://new-url.com/hook' });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/webhooks/wh-1',
        expect.objectContaining({ method: 'PATCH' }),
      );
    });

    it('deleteWebhook sends DELETE', async () => {
      fetchMock.mockResolvedValue({ ok: true, status: 204, json: vi.fn() });
      const { deleteWebhook } = await import('./api');
      await deleteWebhook('wh-1');
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/webhooks/wh-1',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });

    it('getWebhookDeliveries builds correct URL', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { getWebhookDeliveries } = await import('./api');
      await getWebhookDeliveries('wh-1', 2, 5);
      expect(fetchMock).toHaveBeenCalledWith('/api/webhooks/wh-1/deliveries?page=2&limit=5', expect.any(Object));
    });
  });

  describe('Analytics', () => {
    it('getCallAnalytics builds URLSearchParams correctly', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { getCallAnalytics } = await import('./api');
      await getCallAnalytics({ from: '2024-01-01', to: '2024-01-31', groupBy: 'day', assistantId: 'a1' });

      const url = fetchMock.mock.calls[0][0] as string;
      expect(url).toContain('/api/analytics/calls?');
      expect(url).toContain('from=2024-01-01');
      expect(url).toContain('to=2024-01-31');
      expect(url).toContain('groupBy=day');
      expect(url).toContain('assistantId=a1');
    });

    it('getCallAnalytics omits undefined params', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { getCallAnalytics } = await import('./api');
      await getCallAnalytics({});

      const url = fetchMock.mock.calls[0][0] as string;
      expect(url).toBe('/api/analytics/calls?');
    });

    it('getAnalyticsSummary builds URLSearchParams correctly', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { getAnalyticsSummary } = await import('./api');
      await getAnalyticsSummary({ from: '2024-01-01', type: 'WEB' });

      const url = fetchMock.mock.calls[0][0] as string;
      expect(url).toContain('from=2024-01-01');
      expect(url).toContain('type=WEB');
    });
  });

  describe('Squads', () => {
    it('listSquads sends correct pagination', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { listSquads } = await import('./api');
      await listSquads(1, 10);
      expect(fetchMock).toHaveBeenCalledWith('/api/squads?page=1&limit=10', expect.any(Object));
    });

    it('createSquad sends POST with body', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { createSquad } = await import('./api');
      await createSquad({ name: 'Support Squad', members: [{ assistantId: 'a1' }] });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/squads',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ name: 'Support Squad', members: [{ assistantId: 'a1' }] }),
        }),
      );
    });

    it('updateSquad sends PATCH to correct URL', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { updateSquad } = await import('./api');
      await updateSquad('sq-1', { name: 'Updated Squad' });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/squads/sq-1',
        expect.objectContaining({ method: 'PATCH' }),
      );
    });

    it('deleteSquad sends DELETE', async () => {
      fetchMock.mockResolvedValue({ ok: true, status: 204, json: vi.fn() });
      const { deleteSquad } = await import('./api');
      await deleteSquad('sq-1');
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/squads/sq-1',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });
  });

  describe('Campaigns', () => {
    it('listCampaigns sends correct pagination', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { listCampaigns } = await import('./api');
      await listCampaigns(2, 25);
      expect(fetchMock).toHaveBeenCalledWith('/api/campaigns?page=2&limit=25', expect.any(Object));
    });

    it('createCampaign sends POST with body', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { createCampaign } = await import('./api');
      await createCampaign({ name: 'Q1 Outreach', assistantId: 'a1', phoneNumberId: 'pn-1', contacts: [] });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/campaigns',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ name: 'Q1 Outreach', assistantId: 'a1', phoneNumberId: 'pn-1', contacts: [] }),
        }),
      );
    });

    it('updateCampaign sends PATCH to correct URL', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { updateCampaign } = await import('./api');
      await updateCampaign('c-1', { name: 'Updated Campaign' });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/campaigns/c-1',
        expect.objectContaining({ method: 'PATCH' }),
      );
    });

    it('startCampaign sends POST to correct URL', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { startCampaign } = await import('./api');
      await startCampaign('c-1');
      expect(fetchMock).toHaveBeenCalledWith('/api/campaigns/c-1/start', expect.objectContaining({ method: 'POST' }));
    });

    it('pauseCampaign sends POST', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { pauseCampaign } = await import('./api');
      await pauseCampaign('c-1');
      expect(fetchMock).toHaveBeenCalledWith('/api/campaigns/c-1/pause', expect.objectContaining({ method: 'POST' }));
    });

    it('resumeCampaign sends POST', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { resumeCampaign } = await import('./api');
      await resumeCampaign('c-1');
      expect(fetchMock).toHaveBeenCalledWith('/api/campaigns/c-1/resume', expect.objectContaining({ method: 'POST' }));
    });

    it('deleteCampaign sends DELETE', async () => {
      fetchMock.mockResolvedValue({ ok: true, status: 204, json: vi.fn() });
      const { deleteCampaign } = await import('./api');
      await deleteCampaign('c-1');
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/campaigns/c-1',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });
  });

  describe('Phone Numbers', () => {
    it('searchPhoneNumbers sends POST', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { searchPhoneNumbers } = await import('./api');
      await searchPhoneNumbers({ country: 'US', areaCode: '415' });
      expect(fetchMock).toHaveBeenCalledWith('/api/phone-numbers/search', expect.objectContaining({ method: 'POST' }));
    });

    it('listPhoneNumbers sends correct pagination', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { listPhoneNumbers } = await import('./api');
      await listPhoneNumbers(2, 10);
      expect(fetchMock).toHaveBeenCalledWith('/api/phone-numbers?page=2&limit=10', expect.any(Object));
    });

    it('purchasePhoneNumber sends POST with body', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { purchasePhoneNumber } = await import('./api');
      await purchasePhoneNumber({ number: '+15551234567', assistantId: 'a1' });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/phone-numbers',
        expect.objectContaining({ method: 'POST', body: JSON.stringify({ number: '+15551234567', assistantId: 'a1' }) }),
      );
    });

    it('createSipNumber sends POST with body', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { createSipNumber } = await import('./api');
      await createSipNumber({ number: 'sip:user@domain.com', name: 'SIP Line' });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/phone-numbers',
        expect.objectContaining({ method: 'POST' }),
      );
    });

    it('updatePhoneNumber sends PATCH to correct URL', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { updatePhoneNumber } = await import('./api');
      await updatePhoneNumber('pn-1', { assistantId: 'a2' });
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/phone-numbers/pn-1',
        expect.objectContaining({ method: 'PATCH' }),
      );
    });

    it('deletePhoneNumber sends DELETE', async () => {
      fetchMock.mockResolvedValue({ ok: true, status: 204, json: vi.fn() });
      const { deletePhoneNumber } = await import('./api');
      await deletePhoneNumber('pn-1');
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/phone-numbers/pn-1',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });
  });

  describe('Assistant Tools', () => {
    it('getAssistantTools sends GET to correct URL', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: [] }));
      const { getAssistantTools } = await import('./api');
      await getAssistantTools('a1');
      expect(fetchMock).toHaveBeenCalledWith('/api/assistants/a1/tools', expect.any(Object));
    });

    it('attachToolToAssistant sends POST with toolId', async () => {
      fetchMock.mockResolvedValue(mockResponse({ success: true, data: {} }));
      const { attachToolToAssistant } = await import('./api');
      await attachToolToAssistant('a1', 't1');
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/assistants/a1/tools',
        expect.objectContaining({ method: 'POST', body: JSON.stringify({ toolId: 't1' }) }),
      );
    });

    it('detachToolFromAssistant sends DELETE', async () => {
      fetchMock.mockResolvedValue({ ok: true, status: 204, json: vi.fn() });
      const { detachToolFromAssistant } = await import('./api');
      await detachToolFromAssistant('a1', 't1');
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/assistants/a1/tools/t1',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });
  });
});
