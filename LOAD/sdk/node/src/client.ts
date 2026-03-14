/**
 * LOAD Node.js SDK — typed HTTP client for the LOAD voice AI platform API.
 *
 * Usage:
 *   const client = new LoadClient({ apiKey: 'load_...' });
 *   const assistants = await client.listAssistants();
 */

import type {
  ApiResponse,
  Assistant,
  Call,
  Campaign,
  PhoneNumber,
  Squad,
  Tool,
  Webhook,
} from './types.js';

export interface LoadClientOptions {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

export class LoadAPIError extends Error {
  public readonly statusCode: number;
  public readonly code: string;

  constructor(message: string, statusCode: number, code = 'API_ERROR') {
    super(message);
    this.name = 'LoadAPIError';
    this.statusCode = statusCode;
    this.code = code;
  }
}

export class LoadClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly timeout: number;

  constructor(options: LoadClientOptions) {
    this.apiKey = options.apiKey;
    this.baseUrl = (options.baseUrl ?? 'https://api.tryload.ai').replace(/\/$/, '');
    this.timeout = options.timeout ?? 30_000;
  }

  // ---------------------------------------------------------------------------
  // Internal
  // ---------------------------------------------------------------------------

  private async request<T>(
    method: string,
    path: string,
    body?: Record<string, unknown>,
    params?: Record<string, string | number>,
  ): Promise<ApiResponse<T>> {
    const url = new URL(`/api${path}`, this.baseUrl);
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        url.searchParams.set(k, String(v));
      }
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url.toString(), {
        method,
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      if (response.status === 204) {
        return { success: true, data: null as T };
      }

      const json = (await response.json()) as ApiResponse<T>;

      if (!response.ok) {
        throw new LoadAPIError(
          json.error?.message ?? 'Request failed',
          response.status,
          json.error?.code,
        );
      }

      return json;
    } finally {
      clearTimeout(timer);
    }
  }

  // ---------------------------------------------------------------------------
  // Assistants
  // ---------------------------------------------------------------------------

  async listAssistants(page = 1, limit = 20): Promise<ApiResponse<Assistant[]>> {
    return this.request<Assistant[]>('GET', '/assistants', undefined, { page, limit });
  }

  async getAssistant(id: string): Promise<ApiResponse<Assistant>> {
    return this.request<Assistant>('GET', `/assistants/${id}`);
  }

  async createAssistant(data: Partial<Assistant>): Promise<ApiResponse<Assistant>> {
    return this.request<Assistant>('POST', '/assistants', data as Record<string, unknown>);
  }

  async updateAssistant(id: string, data: Partial<Assistant>): Promise<ApiResponse<Assistant>> {
    return this.request<Assistant>('PATCH', `/assistants/${id}`, data as Record<string, unknown>);
  }

  async deleteAssistant(id: string): Promise<ApiResponse<void>> {
    return this.request<void>('DELETE', `/assistants/${id}`);
  }

  // ---------------------------------------------------------------------------
  // Calls
  // ---------------------------------------------------------------------------

  async listCalls(page = 1, limit = 20): Promise<ApiResponse<Call[]>> {
    return this.request<Call[]>('GET', '/calls', undefined, { page, limit });
  }

  async getCall(id: string): Promise<ApiResponse<Call>> {
    return this.request<Call>('GET', `/calls/${id}`);
  }

  // ---------------------------------------------------------------------------
  // Phone Numbers
  // ---------------------------------------------------------------------------

  async listPhoneNumbers(page = 1, limit = 20): Promise<ApiResponse<PhoneNumber[]>> {
    return this.request<PhoneNumber[]>('GET', '/phone-numbers', undefined, { page, limit });
  }

  // ---------------------------------------------------------------------------
  // Tools
  // ---------------------------------------------------------------------------

  async listTools(page = 1, limit = 20): Promise<ApiResponse<Tool[]>> {
    return this.request<Tool[]>('GET', '/tools', undefined, { page, limit });
  }

  async createTool(data: Partial<Tool>): Promise<ApiResponse<Tool>> {
    return this.request<Tool>('POST', '/tools', data as Record<string, unknown>);
  }

  async deleteTool(id: string): Promise<ApiResponse<void>> {
    return this.request<void>('DELETE', `/tools/${id}`);
  }

  // ---------------------------------------------------------------------------
  // Squads
  // ---------------------------------------------------------------------------

  async listSquads(page = 1, limit = 20): Promise<ApiResponse<Squad[]>> {
    return this.request<Squad[]>('GET', '/squads', undefined, { page, limit });
  }

  async createSquad(data: { name: string; members: Array<{ assistantId: string }> }): Promise<ApiResponse<Squad>> {
    return this.request<Squad>('POST', '/squads', data as Record<string, unknown>);
  }

  async deleteSquad(id: string): Promise<ApiResponse<void>> {
    return this.request<void>('DELETE', `/squads/${id}`);
  }

  // ---------------------------------------------------------------------------
  // Campaigns
  // ---------------------------------------------------------------------------

  async listCampaigns(page = 1, limit = 20): Promise<ApiResponse<Campaign[]>> {
    return this.request<Campaign[]>('GET', '/campaigns', undefined, { page, limit });
  }

  async createCampaign(data: Partial<Campaign>): Promise<ApiResponse<Campaign>> {
    return this.request<Campaign>('POST', '/campaigns', data as Record<string, unknown>);
  }

  async startCampaign(id: string): Promise<ApiResponse<Campaign>> {
    return this.request<Campaign>('POST', `/campaigns/${id}/start`);
  }

  async pauseCampaign(id: string): Promise<ApiResponse<Campaign>> {
    return this.request<Campaign>('POST', `/campaigns/${id}/pause`);
  }

  // ---------------------------------------------------------------------------
  // Webhooks
  // ---------------------------------------------------------------------------

  async listWebhooks(page = 1, limit = 20): Promise<ApiResponse<Webhook[]>> {
    return this.request<Webhook[]>('GET', '/webhooks', undefined, { page, limit });
  }

  async createWebhook(data: { url: string; events: string[] }): Promise<ApiResponse<Webhook>> {
    return this.request<Webhook>('POST', '/webhooks', data as Record<string, unknown>);
  }

  async deleteWebhook(id: string): Promise<ApiResponse<void>> {
    return this.request<void>('DELETE', `/webhooks/${id}`);
  }
}
