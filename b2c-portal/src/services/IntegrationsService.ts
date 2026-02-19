/**
 * Integrations Service
 * API service for managing integrations with database backend
 */

import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


// API Base URL
// Using API_BASE_URL from api-config;

// Integration Types
export type IntegrationType =
  | 'tts' | 'stt' | 'llm' | 'telephony' | 'messaging' | 'email' | 'chat'
  | 'crm' | 'erp' | 'support' | 'payment' | 'banking' | 'financial'
  | 'productivity' | 'storage' | 'calendar' | 'analytics' | 'monitoring'
  | 'automation' | 'workflow' | 'healthcare' | 'enterprise'
  | 'database' | 'api' | 'notification' | 'security' | 'compliance' | 'backup';

export type IntegrationStatus = 'not_configured' | 'configured' | 'tested' | 'error' | 'disabled';

export interface IntegrationCapability {
  name: string;
  description: string;
  method: string;
  endpoint?: string;
  parameters?: Record<string, any>;
  response_format?: string;
  rate_limit?: number;
}

export interface IntegrationConfig {
  api_key?: string;
  api_secret?: string;
  endpoint_url?: string;
  webhook_url?: string;
  authentication_type?: string;
  region?: string;
  environment?: string;
  timeout?: number;
  retry_attempts?: number;
  rate_limit?: number;
  custom_headers?: Record<string, string>;
  additional_params?: Record<string, any>;
}

export interface IntegrationTestResult {
  success: boolean;
  message: string;
  response_time_ms?: number;
  status_code?: number;
  error_details?: Record<string, any>;
  tested_at: string;
}

export interface Integration {
  id: string;
  name: string;
  display_name: string;
  description: string;
  provider: string;
  integration_type: IntegrationType;
  category: string;
  website?: string;
  documentation_url?: string;
  icon?: string;
  icon_url?: string;
  version: string;
  config: IntegrationConfig;
  required_fields: string[];
  optional_fields: string[];
  capabilities: IntegrationCapability[];
  supported_operations: string[];
  status: IntegrationStatus;
  is_active: boolean;
  is_configured: boolean;
  is_tested: boolean;
  last_test_result?: IntegrationTestResult;
  usage_count: number;
  last_used?: string;
  error_count: number;
  last_error?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
  tenant_id?: string;
  compliance_certifications: string[];
  data_residency?: string;
  encryption_in_transit: boolean;
  encryption_at_rest: boolean;
  pricing_model?: string;
  free_tier_limits?: Record<string, any>;
  usage_limits?: Record<string, any>;
}

export interface IntegrationListResponse {
  integrations: Integration[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface IntegrationStatsResponse {
  total_integrations: number;
  configured_integrations: number;
  tested_integrations: number;
  active_integrations: number;
  integrations_by_type: Record<string, number>;
  integrations_by_status: Record<string, number>;
  most_used_integrations: Array<{
    id: string;
    name: string;
    provider: string;
    usage_count: number;
    type: string;
  }>;
  recent_errors: Array<{
    id: string;
    name: string;
    provider: string;
    error_count: number;
    last_error: string;
    updated_at?: string;
  }>;
}

export interface IntegrationCreateRequest {
  name: string;
  display_name: string;
  description: string;
  provider: string;
  integration_type: IntegrationType;
  category?: string;
  website?: string;
  documentation_url?: string;
  icon?: string;
  config?: IntegrationConfig;
  required_fields?: string[];
  capabilities?: IntegrationCapability[];
  tenant_id?: string;
}

export interface IntegrationUpdateRequest {
  display_name?: string;
  description?: string;
  website?: string;
  icon?: string;
  config?: IntegrationConfig;
  is_active?: boolean;
  tenant_id?: string;
}

export interface IntegrationConfigureRequest {
  api_key?: string;
  api_secret?: string;
  endpoint_url?: string;
  webhook_url?: string;
  authentication_type?: string;
  region?: string;
  environment?: string;
  additional_params?: Record<string, any>;
  test_connection?: boolean;
}

export interface IntegrationTestRequest {
  test_type?: string;
  test_params?: Record<string, any>;
  timeout?: number;
}

class IntegrationsService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/integrations`;
  }

  private async getHeaders(): Promise<Record<string, string>> {
    const authHeaders = await getAuthHeaders();
    return {
      'Content-Type': 'application/json',
      ...authHeaders,
    };
  }

  /**
   * List integrations with filtering and pagination
   */
  async listIntegrations(params?: {
    page?: number;
    per_page?: number;
    integration_type?: string;
    category?: string;
    status?: string;
    provider?: string;
    search?: string;
    tenant_id?: string;
  }): Promise<IntegrationListResponse> {
    try {
      const headers = await this.getHeaders();
      const url = new URL(this.baseUrl);

      // Add query parameters
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            url.searchParams.append(key, value.toString());
          }
        });
      }

      const response = await fetch(url.toString(), { headers });

      if (!response.ok) {
        throw new Error(`Failed to fetch integrations: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching integrations:', error);
      throw error;
    }
  }

  /**
   * Get a specific integration by ID
   */
  async getIntegration(integrationId: string): Promise<Integration> {
    try {
      const headers = await this.getHeaders();
      const response = await fetch(`${this.baseUrl}/${integrationId}`, { headers });

      if (!response.ok) {
        throw new Error(`Failed to fetch integration: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching integration:', error);
      throw error;
    }
  }

  /**
   * Create a new integration
   */
  async createIntegration(request: IntegrationCreateRequest): Promise<Integration> {
    try {
      const headers = await this.getHeaders();
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to create integration: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating integration:', error);
      throw error;
    }
  }

  /**
   * Update an existing integration
   */
  async updateIntegration(integrationId: string, request: IntegrationUpdateRequest): Promise<Integration> {
    try {
      const headers = await this.getHeaders();
      const response = await fetch(`${this.baseUrl}/${integrationId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to update integration: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating integration:', error);
      throw error;
    }
  }

  /**
   * Delete an integration
   */
  async deleteIntegration(integrationId: string): Promise<{ success: boolean; message: string }> {
    try {
      const headers = await this.getHeaders();
      const response = await fetch(`${this.baseUrl}/${integrationId}`, {
        method: 'DELETE',
        headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to delete integration: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error deleting integration:', error);
      throw error;
    }
  }

  /**
   * Configure an integration with API keys and settings
   */
  async configureIntegration(integrationId: string, request: IntegrationConfigureRequest): Promise<any> {
    try {
      const headers = await this.getHeaders();
      const response = await fetch(`${this.baseUrl}/${integrationId}/configure`, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to configure integration: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error configuring integration:', error);
      throw error;
    }
  }

  /**
   * Test an integration connection
   */
  async testIntegration(integrationId: string, request?: IntegrationTestRequest): Promise<any> {
    try {
      const headers = await this.getHeaders();
      const response = await fetch(`${this.baseUrl}/${integrationId}/test`, {
        method: 'POST',
        headers,
        body: request ? JSON.stringify(request) : undefined,
      });

      if (!response.ok) {
        throw new Error(`Failed to test integration: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error testing integration:', error);
      throw error;
    }
  }

  /**
   * Get integration statistics
   */
  async getIntegrationStats(): Promise<IntegrationStatsResponse> {
    try {
      const headers = await this.getHeaders();
      const response = await fetch(`${this.baseUrl}/stats`, { headers });

      if (!response.ok) {
        throw new Error(`Failed to fetch integration stats: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching integration stats:', error);
      throw error;
    }
  }

  /**
   * Get available integration types and providers
   */
  async getIntegrationTypes(): Promise<{
    types: string[];
    providers: string[];
    categories: string[];
  }> {
    try {
      const headers = await this.getHeaders();
      const response = await fetch(`${this.baseUrl}/types`, { headers });

      if (!response.ok) {
        throw new Error(`Failed to fetch integration types: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching integration types:', error);
      throw error;
    }
  }

  /**
   * Search integrations
   */
  async searchIntegrations(query: string, limit?: number): Promise<{
    query: string;
    results: Integration[];
    total_matches: number;
    returned: number;
  }> {
    try {
      const headers = await this.getHeaders();
      const url = new URL(`${this.baseUrl}/search`);
      url.searchParams.append('q', query);
      if (limit) {
        url.searchParams.append('limit', limit.toString());
      }

      const response = await fetch(url.toString(), { headers });

      if (!response.ok) {
        throw new Error(`Failed to search integrations: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error searching integrations:', error);
      throw error;
    }
  }

  /**
   * Seed the database with default integrations
   */
  async seedIntegrations(): Promise<{ success: boolean; message: string; count: number }> {
    try {
      const headers = await this.getHeaders();
      const response = await fetch(`${this.baseUrl}/seed`, {
        method: 'POST',
        headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to seed integrations: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error seeding integrations:', error);
      throw error;
    }
  }

  /**
   * Get integrations by category (helper method)
   */
  async getIntegrationsByCategory(category: string): Promise<Integration[]> {
    const response = await this.listIntegrations({ category, per_page: 100 });
    return response.integrations;
  }

  /**
   * Get integrations by type (helper method)
   */
  async getIntegrationsByType(type: IntegrationType): Promise<Integration[]> {
    const response = await this.listIntegrations({ integration_type: type, per_page: 100 });
    return response.integrations;
  }

  /**
   * Get configured integrations (helper method)
   */
  async getConfiguredIntegrations(): Promise<Integration[]> {
    const response = await this.listIntegrations({ status: 'configured', per_page: 100 });
    return response.integrations;
  }
}

export const integrationsService = new IntegrationsService();
export default integrationsService;

// Types are already exported above in this file