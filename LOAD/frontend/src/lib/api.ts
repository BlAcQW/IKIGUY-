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

async function request<T>(
  path: string,
  options: RequestInit = {}
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
  return request<{ user: User; organization: Organization; token: string }>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function login(data: { email: string; password: string }) {
  return request<{ user: User; organization: Organization; token: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getMe() {
  return request<{ userId: string; organizationId: string; role: string }>('/auth/me');
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
