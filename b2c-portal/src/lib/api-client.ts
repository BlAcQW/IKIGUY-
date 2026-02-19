/**
 * API Client with Organization Context
 * Automatically adds X-Organization-ID header to all API requests
 */

import { API_BASE_URL } from '@/config/api-config';

interface ApiRequestOptions extends RequestInit {
  skipOrgHeader?: boolean;
  isFormData?: boolean;
}

/**
 * Make an authenticated API request with automatic organization context
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const { skipOrgHeader, isFormData, ...fetchOptions } = options;

  // Get current organization from localStorage
  const currentOrgId = localStorage.getItem('kasaai_current_organization_id');

  // Get access token
  const accessToken = localStorage.getItem('mongo_access_token');

  // Build headers - don't set Content-Type for FormData (browser sets it with boundary)
  const headers: HeadersInit = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...fetchOptions.headers,
  };

  // Add auth token if available
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  // Add organization context if available and not skipped
  if (currentOrgId && !skipOrgHeader) {
    headers['X-Organization-ID'] = currentOrgId;
  }

  // Make the request
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...fetchOptions,
    headers,
  });

  // Handle errors
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  // Return parsed JSON
  return response.json();
}

/**
 * Convenience methods for common HTTP verbs
 */
export const api = {
  get: <T = any>(endpoint: string, options?: ApiRequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),

  post: <T = any>(endpoint: string, data?: any, options?: ApiRequestOptions) => {
    const isFormData = data instanceof FormData;
    return apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: isFormData ? data : (data ? JSON.stringify(data) : undefined),
      isFormData,
    });
  },

  put: <T = any>(endpoint: string, data?: any, options?: ApiRequestOptions) => {
    const isFormData = data instanceof FormData;
    return apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: isFormData ? data : (data ? JSON.stringify(data) : undefined),
      isFormData,
    });
  },

  patch: <T = any>(endpoint: string, data?: any, options?: ApiRequestOptions) => {
    const isFormData = data instanceof FormData;
    return apiRequest<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: isFormData ? data : (data ? JSON.stringify(data) : undefined),
      isFormData,
    });
  },

  delete: <T = any>(endpoint: string, options?: ApiRequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
};

/**
 * Hook to get organization-aware API client
 * (for use in React components)
 */
export function useApi() {
  return api;
}
