import type {
  Assistant,
  ApiKey,
  Call,
  PhoneNumber,
  Tool,
  Squad,
  Campaign,
  Webhook,
  WebhookDelivery,
  User,
  Organization,
  OrgSettings,
  CreateToolRequest,
  UpdateToolRequest,
  CreateSquadRequest,
  UpdateSquadRequest,
  CreateCampaignRequest,
  UpdateCampaignRequest,
  SearchPhoneNumbersRequest,
  PurchasePhoneNumberRequest,
  CreateSipNumberRequest,
  CreateGoipNumberRequest,
  UpdatePhoneNumberRequest,
  CreateWebhookRequest,
  UpdateWebhookRequest,
  CreateAssistantRequest,
  UpdateAssistantRequest,
  TimeSeriesPoint,
  AnalyticsSummary,
  ToolTemplatesResponse,
} from '../types';

const API_BASE = '/api';

interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta?: { total: number; page: number; limit: number };
  error?: { code: string; message: string; statusCode: number };
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('load_token');
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

async function attemptTokenRefresh(): Promise<boolean> {
  const refreshToken = localStorage.getItem('load_refresh_token');
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken }),
    });
    if (!response.ok) return false;
    const json = await response.json();
    localStorage.setItem('load_token', json.data.token);
    localStorage.setItem('load_refresh_token', json.data.refreshToken);
    return true;
  } catch {
    return false;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  skipRetry = false
): Promise<ApiResponse<T>> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options.headers,
    },
  });

  if (response.status === 204) {
    return { success: true, data: null as T };
  }

  const json = await response.json();
  if (!response.ok) {
    // Auto-retry on 401 with refresh token (skip for auth endpoints)
    if (response.status === 401 && !skipRetry && !path.startsWith('/auth/')) {
      if (!isRefreshing) {
        isRefreshing = true;
        refreshPromise = attemptTokenRefresh().finally(() => {
          isRefreshing = false;
          refreshPromise = null;
        });
      }

      const refreshed = await (refreshPromise ?? attemptTokenRefresh());
      if (refreshed) {
        return request<T>(path, options, true);
      }

      // Refresh failed — redirect to login
      localStorage.removeItem('load_token');
      localStorage.removeItem('load_refresh_token');
      localStorage.removeItem('load_user');
      window.location.href = '/login';
    }

    throw new Error(json.error?.message ?? 'Request failed');
  }
  return json;
}

// Auth
export function register(data: {
  email: string;
  password: string;
  name: string;
  organizationName: string;
}) {
  return request<{ user: User; organization: Organization; token: string; refreshToken: string }>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function login(data: { email: string; password: string }) {
  return request<{ user: User; organization: Organization; token: string; refreshToken: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function refreshAccessToken(refreshToken: string) {
  return request<{ user: User; organization: Organization; token: string; refreshToken: string }>(
    '/auth/refresh',
    { method: 'POST', body: JSON.stringify({ refreshToken }) },
    true
  );
}

export function logoutApi() {
  return request<null>('/auth/logout', { method: 'POST' });
}

export function getMe() {
  return request<{ userId: string; organizationId: string; role: string }>('/auth/me');
}

export function updateProfile(data: { name?: string; email?: string; currentPassword?: string; newPassword?: string }) {
  return request<User>('/auth/me', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// Organization Management
export function getOrganization() {
  return request<Organization>('/organizations/me');
}

export function updateOrganization(data: { name: string }) {
  return request<Organization>('/organizations/me', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export interface OrgMember {
  id: string;
  email: string;
  name: string;
  role: string;
  createdAt: string;
}

export function listOrgMembers() {
  return request<OrgMember[]>('/organizations/me/members');
}

export function removeOrgMember(userId: string) {
  return request<void>(`/organizations/me/members/${userId}`, { method: 'DELETE' });
}

// API Keys
export function listApiKeys() {
  return request<ApiKey[]>('/api-keys');
}

export function createApiKey(data: { name: string }) {
  return request<ApiKey & { key: string }>('/api-keys', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function revokeApiKey(id: string) {
  return request<void>(`/api-keys/${id}`, { method: 'DELETE' });
}

// Assistants
export function listAssistants(page = 1, limit = 20) {
  return request<Assistant[]>(`/assistants?page=${page}&limit=${limit}`);
}

export function getAssistant(id: string) {
  return request<Assistant>(`/assistants/${id}`);
}

export function createAssistant(data: CreateAssistantRequest) {
  return request<Assistant>('/assistants', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function updateAssistant(id: string, data: UpdateAssistantRequest) {
  return request<Assistant>(`/assistants/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export function deleteAssistant(id: string) {
  return request<void>(`/assistants/${id}`, { method: 'DELETE' });
}

// Calls
export function listCalls(page = 1, limit = 20) {
  return request<Call[]>(`/calls?page=${page}&limit=${limit}`);
}

export function getCall(id: string) {
  return request<Call>(`/calls/${id}`);
}

// Phone Numbers
export function listPhoneNumbers(page = 1, limit = 20) {
  return request<PhoneNumber[]>(`/phone-numbers?page=${page}&limit=${limit}`);
}

export function searchPhoneNumbers(params: SearchPhoneNumbersRequest) {
  return request<Array<{ number: string; locality: string; region: string }>>('/phone-numbers/search', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export function purchasePhoneNumber(data: PurchasePhoneNumberRequest) {
  return request<PhoneNumber>('/phone-numbers', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function createSipNumber(data: CreateSipNumberRequest) {
  return request<PhoneNumber>('/phone-numbers', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function createGoipNumber(data: CreateGoipNumberRequest) {
  return request<PhoneNumber>('/phone-numbers', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function updatePhoneNumber(id: string, data: UpdatePhoneNumberRequest) {
  return request<PhoneNumber>(`/phone-numbers/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export function deletePhoneNumber(id: string) {
  return request<void>(`/phone-numbers/${id}`, { method: 'DELETE' });
}

// Tools
export function listTools(page = 1, limit = 20) {
  return request<Tool[]>(`/tools?page=${page}&limit=${limit}`);
}

export function createTool(data: CreateToolRequest) {
  return request<Tool>('/tools', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function updateTool(id: string, data: UpdateToolRequest) {
  return request<Tool>(`/tools/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export function deleteTool(id: string) {
  return request<void>(`/tools/${id}`, { method: 'DELETE' });
}

export function testTool(id: string) {
  return request<{ status: number; statusText: string; body: unknown; latencyMs: number }>(`/tools/${id}/test`, { method: 'POST' });
}

// Tool Templates
export function listToolTemplates() {
  return request<ToolTemplatesResponse>('/tools/templates');
}

export function createToolFromTemplate(data: {
  templateName: string;
  serverUrl: string;
  serverSecret?: string;
}) {
  return request<Tool>('/tools/from-template', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function bulkCreateToolsFromTemplates(data: {
  category: string;
  serverUrl: string;
  serverSecret?: string;
  assistantId?: string;
}) {
  return request<Tool[]>('/tools/from-templates/bulk', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// Assistant Tools
export function getAssistantTools(assistantId: string) {
  return request<Tool[]>(`/assistants/${assistantId}/tools`);
}

export function attachToolToAssistant(assistantId: string, toolId: string) {
  return request<Assistant>(`/assistants/${assistantId}/tools`, {
    method: 'POST',
    body: JSON.stringify({ toolId }),
  });
}

export function detachToolFromAssistant(assistantId: string, toolId: string) {
  return request<Assistant>(`/assistants/${assistantId}/tools/${toolId}`, {
    method: 'DELETE',
  });
}

// Squads
export function listSquads(page = 1, limit = 20) {
  return request<Squad[]>(`/squads?page=${page}&limit=${limit}`);
}

export function createSquad(data: CreateSquadRequest) {
  return request<Squad>('/squads', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function updateSquad(id: string, data: UpdateSquadRequest) {
  return request<Squad>(`/squads/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export function deleteSquad(id: string) {
  return request<void>(`/squads/${id}`, { method: 'DELETE' });
}

// Campaigns
export function listCampaigns(page = 1, limit = 20) {
  return request<Campaign[]>(`/campaigns?page=${page}&limit=${limit}`);
}

export function createCampaign(data: CreateCampaignRequest) {
  return request<Campaign>('/campaigns', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function updateCampaign(id: string, data: UpdateCampaignRequest) {
  return request<Campaign>(`/campaigns/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export function startCampaign(id: string) {
  return request<Campaign>(`/campaigns/${id}/start`, { method: 'POST' });
}

export function pauseCampaign(id: string) {
  return request<Campaign>(`/campaigns/${id}/pause`, { method: 'POST' });
}

export function resumeCampaign(id: string) {
  return request<Campaign>(`/campaigns/${id}/resume`, { method: 'POST' });
}

export function deleteCampaign(id: string) {
  return request<void>(`/campaigns/${id}`, { method: 'DELETE' });
}

// Webhooks
export function listWebhooks(page = 1, limit = 20) {
  return request<Webhook[]>(`/webhooks?page=${page}&limit=${limit}`);
}

export function createWebhook(data: CreateWebhookRequest) {
  return request<Webhook>('/webhooks', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function updateWebhook(id: string, data: UpdateWebhookRequest) {
  return request<Webhook>(`/webhooks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export function deleteWebhook(id: string) {
  return request<void>(`/webhooks/${id}`, { method: 'DELETE' });
}

export function getWebhookDeliveries(webhookId: string, page = 1, limit = 20) {
  return request<WebhookDelivery[]>(`/webhooks/${webhookId}/deliveries?page=${page}&limit=${limit}`);
}

// Assistant Chat
export function chatWithAssistant(
  assistantId: string,
  messages: Array<{ role: string; content: string }>
) {
  return request<{ message: string }>(`/assistants/${assistantId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ messages }),
  });
}

// Voices
export function listVoices() {
  return request<Array<{
    voiceId: string;
    name: string;
    provider: string;
    category: string;
    labels: Record<string, string>;
    previewUrl?: string;
  }>>('/voices');
}

export async function cloneVoice(name: string, description: string, audioFile: File) {
  const formData = new FormData();
  formData.append('name', name);
  formData.append('description', description);
  formData.append('file', audioFile);

  const token = localStorage.getItem('load_token');
  const response = await fetch('/api/voices/clone', {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  const json = await response.json();
  if (!response.ok) {
    throw new Error(json.error?.message ?? 'Voice cloning failed');
  }
  return json;
}

export function deleteVoice(voiceId: string) {
  return request<void>(`/voices/${voiceId}`, { method: 'DELETE' });
}

export async function previewVoice(provider: string, voiceId: string, text?: string) {
  const token = localStorage.getItem('load_token');
  const response = await fetch('/api/voices/preview', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ provider, voiceId, text }),
  });

  if (!response.ok) {
    throw new Error('Preview failed');
  }

  return response.blob();
}

// Pipeline Test — TTS & STT
export async function synthesizeTts(params: {
  text: string;
  provider?: string;
  voiceId?: string;
  speed?: number;
}): Promise<Blob> {
  const token = localStorage.getItem('load_token');
  const response = await fetch(`${API_BASE}/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const json = await response.json().catch(() => ({ error: { message: `TTS failed: ${response.status}` } }));
    throw new Error(json.error?.message ?? `TTS failed: ${response.status}`);
  }

  return response.blob();
}

export async function transcribeStt(
  audioBlob: Blob,
  filename: string,
  provider?: string,
): Promise<string> {
  const token = localStorage.getItem('load_token');
  const formData = new FormData();
  formData.append('file', audioBlob, filename);
  if (provider) formData.append('provider', provider);

  const response = await fetch(`${API_BASE}/stt`, {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  if (!response.ok) {
    const json = await response.json().catch(() => ({ error: { message: `STT failed: ${response.status}` } }));
    throw new Error(json.error?.message ?? `STT failed: ${response.status}`);
  }

  const json = await response.json();
  return json.data?.text ?? '';
}

// Organization Settings
export function getOrgSettings() {
  return request<OrgSettings>('/settings');
}

export function updateOrgSettings(data: Partial<OrgSettings>) {
  return request<OrgSettings>('/settings', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// Analytics
export function getCallAnalytics(params: {
  from?: string;
  to?: string;
  groupBy?: 'hour' | 'day' | 'week';
  assistantId?: string;
  type?: 'WEB' | 'INBOUND' | 'OUTBOUND';
}) {
  const searchParams = new URLSearchParams();
  if (params.from) searchParams.set('from', params.from);
  if (params.to) searchParams.set('to', params.to);
  if (params.groupBy) searchParams.set('groupBy', params.groupBy);
  if (params.assistantId) searchParams.set('assistantId', params.assistantId);
  if (params.type) searchParams.set('type', params.type);
  return request<TimeSeriesPoint[]>(`/analytics/calls?${searchParams}`);
}

export function getAnalyticsSummary(params: {
  from?: string;
  to?: string;
  assistantId?: string;
  type?: 'WEB' | 'INBOUND' | 'OUTBOUND';
}) {
  const searchParams = new URLSearchParams();
  if (params.from) searchParams.set('from', params.from);
  if (params.to) searchParams.set('to', params.to);
  if (params.assistantId) searchParams.set('assistantId', params.assistantId);
  if (params.type) searchParams.set('type', params.type);
  return request<AnalyticsSummary>(`/analytics/summary?${searchParams}`);
}
