/**
 * Custom Tools Service
 * Handles API calls for managing custom business tools available for N8N and VAPI agents
 */

import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


// Using API_BASE_URL from api-config;

export interface CustomTool {
  name: string;
  description: string;
  category: string;
  endpoint: string;
  method: string;
  parameters_schema: {
    type: string;
    properties: Record<string, any>;
    required?: string[];
  };
  response_schema: {
    type: string;
    properties: Record<string, any>;
  };
  is_active: boolean;
  created_by: string;
  tags: string[];
}

export interface CustomToolsResponse {
  success: boolean;
  tools: CustomTool[];
  total: number;
  categories: string[];
}

export interface CustomToolResponse {
  success: boolean;
  tool: CustomTool;
}

export interface CustomToolExecutionRequest {
  tool_name: string;
  parameters: Record<string, any>;
  context?: Record<string, any>;
}

export interface CustomToolExecutionResponse {
  success: boolean;
  result: Record<string, any>;
  tool_name: string;
  execution_time_ms: number;
  timestamp: string;
}

class CustomToolsService {
  /**
   * Get all available custom tools
   */
  async getCustomTools(category?: string, is_active?: boolean): Promise<CustomToolsResponse> {
    try {
      const headers = await getAuthHeaders();
      const params = new URLSearchParams();

      if (category) params.append('category', category);
      if (is_active !== undefined) params.append('is_active', is_active.toString());

      const queryString = params.toString() ? `?${params.toString()}` : '';
      const response = await fetch(`${API_BASE_URL}/custom-tools/${queryString}`, {
        method: 'GET',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to fetch custom tools');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching custom tools:', error);
      throw error;
    }
  }

  /**
   * Get details about a specific custom tool
   */
  async getCustomTool(toolName: string): Promise<CustomToolResponse> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/${toolName}`, {
        method: 'GET',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to fetch custom tool');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching custom tool:', error);
      throw error;
    }
  }

  /**
   * Execute a custom tool with parameters
   */
  async executeCustomTool(request: CustomToolExecutionRequest): Promise<CustomToolExecutionResponse> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to execute custom tool');
      }

      return await response.json();
    } catch (error) {
      console.error('Error executing custom tool:', error);
      throw error;
    }
  }

  /**
   * Healthcare Provider Tools - Direct API calls
   */

  /**
   * Search for healthcare providers
   */
  async searchHealthcareProviders(
    query: string,
    maxResults: number = 5,
    location?: string,
    specialty?: string,
    providerType?: string
  ): Promise<CustomToolExecutionResponse> {
    try {
      const headers = await getAuthHeaders();
      const params = new URLSearchParams({
        query,
        max_results: maxResults.toString(),
      });

      if (location) params.append('location', location);
      if (specialty) params.append('specialty', specialty);
      if (providerType) params.append('provider_type', providerType);

      const response = await fetch(`${API_BASE_URL}/custom-tools/healthcare/search-providers?${params}`, {
        method: 'POST',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to search healthcare providers');
      }

      return await response.json();
    } catch (error) {
      console.error('Error searching healthcare providers:', error);
      throw error;
    }
  }

  /**
   * Get emergency healthcare providers
   */
  async getEmergencyProviders(location?: string, maxResults: number = 5): Promise<CustomToolExecutionResponse> {
    try {
      const headers = await getAuthHeaders();
      const params = new URLSearchParams({
        max_results: maxResults.toString(),
      });

      if (location) params.append('location', location);

      const response = await fetch(`${API_BASE_URL}/custom-tools/healthcare/get-emergency-providers?${params}`, {
        method: 'POST',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to get emergency providers');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting emergency providers:', error);
      throw error;
    }
  }

  /**
   * Get healthcare provider details
   */
  async getProviderDetails(providerId: number): Promise<CustomToolExecutionResponse> {
    try {
      const headers = await getAuthHeaders();
      const params = new URLSearchParams({
        provider_id: providerId.toString(),
      });

      const response = await fetch(`${API_BASE_URL}/custom-tools/healthcare/get-provider-details?${params}`, {
        method: 'POST',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to get provider details');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting provider details:', error);
      throw error;
    }
  }

  /**
   * Send provider information via email
   */
  async sendProviderInfoEmail(
    email: string,
    providerData: any[],
    searchQuery: string = '',
    customerName: string = 'Customer'
  ): Promise<CustomToolExecutionResponse> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/healthcare/send-provider-info-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
        body: JSON.stringify({
          email,
          provider_data: providerData,
          search_query: searchQuery,
          customer_name: customerName,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to send provider info email');
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending provider info email:', error);
      throw error;
    }
  }

  /**
   * Send provider information via SMS
   */
  async sendProviderInfoSMS(
    phone: string,
    providerData: any[],
    searchQuery: string = ''
  ): Promise<CustomToolExecutionResponse> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/healthcare/send-provider-info-sms`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
        body: JSON.stringify({
          phone,
          provider_data: providerData,
          search_query: searchQuery,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to send provider info SMS');
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending provider info SMS:', error);
      throw error;
    }
  }

  /**
   * Escalate query to support
   */
  async escalateToSupport(
    customerName: string,
    customerEmail: string,
    customerPhone: string,
    searchQuery: string,
    locationSearched: string,
    issueDescription: string = ''
  ): Promise<CustomToolExecutionResponse> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/healthcare/escalate-to-support`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
        body: JSON.stringify({
          customer_name: customerName,
          customer_email: customerEmail,
          customer_phone: customerPhone,
          search_query: searchQuery,
          location_searched: locationSearched,
          issue_description: issueDescription,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to escalate to support');
      }

      return await response.json();
    } catch (error) {
      console.error('Error escalating to support:', error);
      throw error;
    }
  }

  /**
   * Get tool configuration for N8N
   */
  getN8NToolConfig(tool: CustomTool): any {
    return {
      name: tool.name,
      description: tool.description,
      type: 'httpRequest',
      parameters: {
        method: tool.method,
        url: tool.endpoint,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer {{$credentials.api_token}}',
        },
        body: tool.parameters_schema,
      },
    };
  }

  /**
   * Get tool configuration for VAPI
   */
  getVAPIToolConfig(tool: CustomTool): any {
    return {
      type: 'function',
      function: {
        name: tool.name.replace(/[^a-zA-Z0-9_]/g, '_'),
        description: tool.description,
        parameters: tool.parameters_schema,
      },
      server: {
        url: tool.endpoint,
        method: tool.method,
      },
    };
  }

  /**
   * CRUD Operations for Custom Tools
   */

  /**
   * Register a new custom tool from database
   */
  async registerCustomTool(toolData: {
    name: string;
    description: string;
    schema: Record<string, any>;
    client_id: string;
    industry?: string;
    category?: string;
    version?: string;
    tags?: string[];
    dependencies?: string[];
    code?: string;
    endpoint?: string;
    metadata?: Record<string, any>;
  }): Promise<{ success: boolean; tool_id?: string; message?: string; error?: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/db/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
        body: JSON.stringify(toolData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to register custom tool');
      }

      return await response.json();
    } catch (error) {
      console.error('Error registering custom tool:', error);
      throw error;
    }
  }

  /**
   * Update an existing custom tool
   */
  async updateCustomTool(
    toolId: string,
    updates: {
      name?: string;
      description?: string;
      schema?: Record<string, any>;
      category?: string;
      version?: string;
      tags?: string[];
      endpoint?: string;
      metadata?: Record<string, any>;
      active?: boolean;
    }
  ): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/${toolId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to update custom tool');
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating custom tool:', error);
      throw error;
    }
  }

  /**
   * Delete (deactivate) a custom tool
   */
  async deleteCustomTool(toolId: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/${toolId}`, {
        method: 'DELETE',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to delete custom tool');
      }

      return await response.json();
    } catch (error) {
      console.error('Error deleting custom tool:', error);
      throw error;
    }
  }

  /**
   * Get detailed information about a specific tool by ID
   */
  async getCustomToolById(toolId: string): Promise<{ success: boolean; tool?: CustomTool; error?: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/${toolId}`, {
        method: 'GET',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to get custom tool');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting custom tool:', error);
      throw error;
    }
  }

  /**
   * Search custom tools with advanced filters
   */
  async searchCustomTools(
    query: string,
    filters?: {
      client_id?: string;
      industry?: string;
      category?: string;
      limit?: number;
    }
  ): Promise<{ success: boolean; tools?: CustomTool[]; count?: number; error?: string }> {
    try {
      const headers = await getAuthHeaders();
      const params = new URLSearchParams({ query });

      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.append(key, value.toString());
          }
        });
      }

      const response = await fetch(`${API_BASE_URL}/custom-tools/search?${params}`, {
        method: 'GET',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to search custom tools');
      }

      return await response.json();
    } catch (error) {
      console.error('Error searching custom tools:', error);
      throw error;
    }
  }

  /**
   * Sync tool with VAPI platform
   */
  async syncToolWithVAPI(toolId: string): Promise<{ success: boolean; vapi_tool_id?: string; message?: string; error?: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/${toolId}/sync-vapi`, {
        method: 'POST',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to sync tool with VAPI');
      }

      return await response.json();
    } catch (error) {
      console.error('Error syncing tool with VAPI:', error);
      throw error;
    }
  }

  /**
   * Bulk register multiple tools
   */
  async bulkRegisterTools(
    tools: Array<{
      name: string;
      description: string;
      schema: Record<string, any>;
      client_id: string;
      industry?: string;
      category?: string;
      version?: string;
      tags?: string[];
      code?: string;
      endpoint?: string;
      metadata?: Record<string, any>;
    }>,
    clientId: string,
    source: string = 'bulk_import'
  ): Promise<{ success: boolean; total_processed?: number; successful_count?: number; failed_count?: number; results?: any[]; error?: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/db/bulk-register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
        body: JSON.stringify({
          tools,
          client_id: clientId,
          source
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to bulk register tools');
      }

      return await response.json();
    } catch (error) {
      console.error('Error bulk registering tools:', error);
      throw error;
    }
  }

  /**
   * Get analytics for a specific tool
   */
  async getToolAnalytics(toolId: string): Promise<{ success: boolean; analytics?: any; tool_name?: string; client_id?: string; error?: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/analytics/${toolId}`, {
        method: 'GET',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to get tool analytics');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting tool analytics:', error);
      throw error;
    }
  }

  /**
   * Get VAPI sync status for tools
   */
  async getVAPISyncStatus(clientId?: string): Promise<{ success: boolean; sync_status?: any; total_tools?: number; error?: string }> {
    try {
      const headers = await getAuthHeaders();
      const params = new URLSearchParams();
      if (clientId) params.append('client_id', clientId);

      const response = await fetch(`${API_BASE_URL}/custom-tools/vapi-sync-status?${params}`, {
        method: 'GET',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to get VAPI sync status');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting VAPI sync status:', error);
      throw error;
    }
  }
}

export const customToolsService = new CustomToolsService();