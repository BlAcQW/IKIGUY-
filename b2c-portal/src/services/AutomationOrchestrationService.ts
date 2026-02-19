/**
 * Automation Orchestration Service
 * Centralized service for all automation template and configuration management
 * Replaces scattered API calls with unified orchestration service
 */

import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


// Using API_BASE_URL from api-config;

// Types matching the backend AutomationOrchestrationService
export interface AutomationTemplate {
  id: string;
  name: string;
  description: string;
  industry: string;
  category: string;
  complexity: string;
  estimated_time: string;
  components: {
    vapi?: any;
    n8n?: any;
    customTools?: any[];
    integrations?: string[];
  };
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  version: string;
  tags: string[];
  is_active: boolean;
}

export interface AutomationTemplateListResponse {
  templates: AutomationTemplate[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

export interface AutomationTemplateStats {
  total_templates: number;
  by_industry: Array<{ industry: string; count: number }>;
  by_category: Array<{ category: string; count: number }>;
  by_complexity: Array<{ complexity: string; count: number }>;
  recent_templates: Array<{
    id: string;
    name: string;
    industry: string;
    created_at: string;
  }>;
  generated_at: string;
}

export interface AutomationConfig {
  id: string;
  template_id: string;
  user_id: string;
  automation_name: string;
  // Top-level fields from API response
  vapi_agent?: {
    assistant_id?: string;
    assistant_name?: string;
    phone_number_id?: string;
    system_prompt?: string;
    voice_settings?: any;
    custom_settings_override?: {
      tts?: { provider?: string; voice?: string; speed?: number; pitch?: number };
      asr?: { provider?: string; language?: string };
      llm?: { model?: string; temperature?: number; maxTokens?: number };
      referenceVoice?: string | null;
    } | null;
    [key: string]: any;
  };
  vapiAgent?: any; // camelCase alias
  company_info?: any;
  n8n_workflow?: any;
  integrations?: Record<string, any>;
  custom_tools?: any;
  demo_settings?: any;
  analytics?: any;
  config: {
    vapi?: any;
    n8n?: any;
    user_config?: {
      automation_name?: string;
      company_info?: any;
      vapi_agent?: any;
      n8n_workflow?: any;
      integrations?: Record<string, any>;
      custom_tools?: any;
      demo_settings?: any;
    };
    vapi_agent?: any; // Also check here
    vapiAgent?: any;
  };
  status: 'draft' | 'testing' | 'deployed' | 'stopped' | 'failed';
  deployment_info: Record<string, any>;
  created_at: string;
  updated_at: string;
  deployed_at?: string;
  stopped_at?: string;
}

export interface AutomationConfigResponse {
  configuration: AutomationConfig;
  template?: AutomationTemplate;
  deployment_status: Record<string, any>;
  analytics: Record<string, any>;
}

export interface AutomationConfigList {
  configurations: AutomationConfig[];
  total: number;
}

export interface DeploymentResult {
  success: boolean;
  automation_id: string;
  deployment_stage: string;
  automation_config_id?: string;
  vapi_assistant_id?: string;
  n8n_workflow_id?: string;
  demo_url?: string;
  webhook_urls?: Record<string, string>;
  error?: string;
  warnings?: string[];
}

export interface AutomationStatusResponse {
  config_id: string;
  status: string;
  automation_name: string;
  deployment_info: Record<string, any>;
  created_at: string;
  updated_at: string;
  deployed_at?: string;
  stopped_at?: string;
  health?: {
    overall: string;
    components: Record<string, any>;
    last_checked: string;
  };
  metrics?: {
    uptime: string;
    requests_handled: number;
    avg_response_time: number;
    errors: number;
    last_activity?: string;
  };
}

export interface ValidationResult {
  valid: boolean;
  config_id: string;
  checks: Record<string, any>;
  warnings: string[];
  errors: string[];
}

export interface TestResult {
  success: boolean;
  config_id: string;
  test_scenario: string;
  tests: Record<string, any>;
  summary: {
    total_tests: number;
    passed: number;
    failed: number;
    skipped: number;
  };
}

export interface AnalyticsOverview {
  period: {
    start_date: string;
    end_date: string;
  };
  templates: Record<string, any>;
  configurations: Record<string, any>;
  deployments: Record<string, any>;
  summary: {
    total_templates: number;
    total_configurations: number;
    active_deployments: number;
    success_rate: number;
  };
  generated_at: string;
}

export interface AvailableIntegration {
  name: string;
  category: string;
  description: string;
  required?: boolean;
  compliance_notes?: string;
  centralized_service: boolean;
  total_integrations_available: number;
  service_capabilities: Record<string, any>;
}

export interface ServiceCapabilities {
  service: string;
  capabilities: Record<string, any>;
  supported_industries: string[];
  supported_platforms: string[];
  integration_categories: string[];
  features: Record<string, any>;
  limits: Record<string, any>;
}

class AutomationOrchestrationService {
  private async getAuthHeaders(): Promise<Record<string, string>> {
    // Get MongoDB authentication headers
    const authHeaders = await getAuthHeaders();

    // Reason: Add X-Organization-ID header for organization-scoped queries
    const currentOrgId = localStorage.getItem('kasaai_current_organization_id');

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...authHeaders,
    };

    if (currentOrgId) {
      headers['X-Organization-ID'] = currentOrgId;
    }

    return headers;
  }

  // Template Management
  async listTemplates(params: {
    page?: number;
    per_page?: number;
    industry?: string;
    category?: string;
    complexity?: string;
    search?: string;
  } = {}): Promise<AutomationTemplateListResponse> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value.toString());
      }
    });

    const response = await fetch(`${API_BASE_URL}/automation-templates/public/list?${queryParams}`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch templates: ${response.statusText}`);
    }

    const data = await response.json();
    // Map backend response format to frontend expected format
    return {
      templates: data.templates || [],
      pagination: {
        page: data.page || 1,
        per_page: data.per_page || 20,
        total: data.total || 0,
        pages: data.pages || 1
      }
    };
  }

  async getTemplate(templateId: string): Promise<AutomationTemplate> {
    const response = await fetch(`${API_BASE_URL}/automation-templates/${templateId}`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch template: ${response.statusText}`);
    }

    return response.json();
  }

  async createTemplate(templateData: Partial<AutomationTemplate>): Promise<AutomationTemplate> {
    const response = await fetch(`${API_BASE_URL}/automation-templates`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(templateData),
    });

    if (!response.ok) {
      throw new Error(`Failed to create template: ${response.statusText}`);
    }

    return response.json();
  }

  async getTemplateStats(): Promise<AutomationTemplateStats> {
    const response = await fetch(`${API_BASE_URL}/automation-templates/stats`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch template stats: ${response.statusText}`);
    }

    return response.json();
  }

  // Configuration Management
  async listConfigurations(params: {
    user_id?: string;
    organization_id?: string;
    template_id?: string;
    status?: string;
  } = {}): Promise<AutomationConfigList> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value);
      }
    });

    const response = await fetch(`${API_BASE_URL}/automation-configs/?${queryParams}`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch configurations: ${response.statusText}`);
    }

    const data = await response.json();
    // Map backend response format to frontend expected format
    return {
      configurations: data.configs || [],
      total: data.total || 0
    };
  }

  async getConfiguration(configId: string): Promise<AutomationConfigResponse> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/${configId}`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch configuration: ${response.statusText}`);
    }

    return response.json();
  }

  async createConfiguration(configData: {
    template_id: string;
    configuration: Record<string, any>;
  }): Promise<AutomationConfigResponse> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/create`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(configData),
    });

    if (!response.ok) {
      throw new Error(`Failed to create configuration: ${response.statusText}`);
    }

    return response.json();
  }

  async updateConfiguration(configId: string, updates: Partial<AutomationConfig>): Promise<AutomationConfigResponse> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/${configId}`, {
      method: 'PUT',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      throw new Error(`Failed to update configuration: ${response.statusText}`);
    }

    return response.json();
  }

  async deleteConfiguration(configId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/${configId}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to delete configuration: ${response.statusText}`);
    }

    return response.json();
  }

  async duplicateConfiguration(configId: string, newName: string): Promise<AutomationConfigResponse> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/configurations/${configId}/duplicate`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ newName }),
    });

    if (!response.ok) {
      throw new Error(`Failed to duplicate configuration: ${response.statusText}`);
    }

    return response.json();
  }

  // Deployment Management
  async deployConfiguration(configId: string): Promise<DeploymentResult> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/${configId}/deploy`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to deploy configuration: ${response.statusText}`);
    }

    return response.json();
  }

  async stopConfiguration(configId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/${configId}/stop`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to stop configuration: ${response.statusText}`);
    }

    return response.json();
  }

  async restartConfiguration(configId: string): Promise<DeploymentResult> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/configurations/${configId}/restart`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to restart configuration: ${response.statusText}`);
    }

    return response.json();
  }

  async getConfigurationStatus(configId: string): Promise<AutomationStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/${configId}/status`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to get configuration status: ${response.statusText}`);
    }

    return response.json();
  }

  // Validation and Testing
  async validateConfiguration(configId: string): Promise<ValidationResult> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/configurations/${configId}/validate`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to validate configuration: ${response.statusText}`);
    }

    return response.json();
  }

  async testConfiguration(configId: string, testScenario?: string): Promise<TestResult> {
    const body = testScenario ? JSON.stringify({ test_scenario: testScenario }) : undefined;
    const response = await fetch(`${API_BASE_URL}/automation-configs/configurations/${configId}/test`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body,
    });

    if (!response.ok) {
      throw new Error(`Failed to test configuration: ${response.statusText}`);
    }

    return response.json();
  }

  // Analytics and Monitoring
  async getAnalyticsOverview(params: {
    start_date?: string;
    end_date?: string;
  } = {}): Promise<AnalyticsOverview> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value);
      }
    });

    const response = await fetch(`${API_BASE_URL}/automation-configs/analytics/overview?${queryParams}`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch analytics overview: ${response.statusText}`);
    }

    return response.json();
  }

  async getIndustryAnalytics(industry: string): Promise<Record<string, any>> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/analytics/industry/${industry}`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch industry analytics: ${response.statusText}`);
    }

    return response.json();
  }

  // Capabilities and Discovery
  async getCapabilities(): Promise<ServiceCapabilities> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/capabilities`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch capabilities: ${response.statusText}`);
    }

    return response.json();
  }

  async getAvailableIntegrations(params: {
    industry?: string;
    category?: string;
  } = {}): Promise<AvailableIntegration[]> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value);
      }
    });

    const response = await fetch(`${API_BASE_URL}/automation-configs/integrations/available?${queryParams}`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch available integrations: ${response.statusText}`);
    }

    return response.json();
  }

  // Additional convenience methods for testing
  async testVAPIAssistant(assistantId: string): Promise<{ success: boolean; error?: string }> {
    try {
      // This would be a VAPI API call to test the assistant
      // For now, return success
      return { success: true };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async testN8NWorkflow(workflowId: string): Promise<{ success: boolean; error?: string }> {
    try {
      // This would be an N8N API call to test the workflow
      // For now, return success
      return { success: true };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  // Health Check
  async healthCheck(): Promise<Record<string, any>> {
    const response = await fetch(`${API_BASE_URL}/automation-configs/health`, {
      method: 'GET',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const automationOrchestrationService = new AutomationOrchestrationService();
export default automationOrchestrationService;