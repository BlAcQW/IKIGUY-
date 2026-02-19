/**
 * General API client for EstateFlow.
 *
 * Provides HTTP request methods with authentication and organization context.
 */

import { API_BASE_URL } from './api-config';

interface RequestConfig extends RequestInit {
  token?: string;
  organizationId?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private getHeaders(config?: RequestConfig): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (config?.token) {
      headers['Authorization'] = `Bearer ${config.token}`;
    }

    if (config?.organizationId) {
      headers['X-Organization-ID'] = config.organizationId;
    }

    return headers;
  }

  async request<T>(
    endpoint: string,
    config?: RequestConfig
  ): Promise<T> {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...config,
      headers: {
        ...this.getHeaders(config),
        ...config?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: response.statusText,
      }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async get<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  async post<T>(
    endpoint: string,
    data?: any,
    config?: RequestConfig
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(
    endpoint: string,
    data?: any,
    config?: RequestConfig
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }
}

export const api = new ApiClient();
