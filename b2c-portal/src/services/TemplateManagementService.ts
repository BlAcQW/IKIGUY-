import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';

/**
 * Template Management Service
 * Handles CRUD operations for automation templates
 */

// Use the same API base URL as core-api
// Using API_BASE_URL from api-config;

export interface AutomationTemplate {
  id: string;
  template_name: string;
  industry: string;
  category: string;
  description: string;
  company_name: string;
  company_url?: string;
  system_prompt: string;
  custom_tool_names: string[];
  integrations: Integration[];
  vapi_config: VAPIConfig;
  n8n_config: N8NConfig;
  demo_config: DemoConfig;
  monitoring_config: MonitoringConfig;
  created_at: string;
  updated_at: string;
  created_by: string;
  is_active: boolean;
  usage_count: number;
}

export interface Integration {
  name: string;
  enabled: boolean;
  api_key?: string;
  config: Record<string, any>;
  required_fields: string[];
}

export interface VAPIConfig {
  model: string;
  voice_id: string;
  voice_provider: string;
  temperature: number;
  max_tokens: number;
  max_duration: number;
  first_message: string;
  end_call_message: string;
  tools: string[];
  compliance_level: string;
}

export interface N8NConfig {
  workflow_name: string;
  workflow_id?: string;
  webhook_path: string;
  nodes: any[];
  connections: Record<string, any>;
  endpoints: Record<string, string>;
}

export interface DemoConfig {
  enabled: boolean;
  theme: string;
  brand_colors: string[];
  interactive_features: string[];
  emergency_simulation: boolean;
}

export interface MonitoringConfig {
  enabled: boolean;
  kpis: string[];
  alert_rules: string[];
  dashboard_widgets: string[];
  compliance_monitoring: boolean;
}

export interface TemplateUpdateRequest {
  template_name?: string;
  description?: string;
  company_name?: string;
  company_url?: string;
  company_description?: string;
  system_prompt?: string;
  is_active?: boolean;
}

export interface TemplateCreateRequest {
  template_name: string;
  industry: string;
  category: string;
  description: string;
  company_name: string;
  company_url?: string;
  company_description?: string;
  custom_integrations?: string[];
}

class TemplateManagementService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/automation-templates`;
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const token = localStorage.getItem('auth_token') || 'test';
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  /**
   * List all templates with optional filtering
   */
  async listTemplates(filters?: {
    industry?: string;
    category?: string;
    active_only?: boolean;
  }): Promise<AutomationTemplate[]> {
    const params = new URLSearchParams();
    if (filters?.industry) params.append('industry', filters.industry);
    if (filters?.category) params.append('category', filters.category);
    if (filters?.active_only !== undefined) params.append('active_only', String(filters.active_only));

    const url = `${this.baseUrl}/list?${params.toString()}`;
    const headers = await this.getAuthHeaders();

    try {
      const response = await fetch(url, { headers });
      if (!response.ok) {
        throw new Error(`Failed to fetch templates: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching templates:', error);
      throw error;
    }
  }

  /**
   * Get a specific template by ID
   */
  async getTemplate(templateId: string): Promise<AutomationTemplate> {
    const headers = await this.getAuthHeaders();

    try {
      const response = await fetch(`${this.baseUrl}/${templateId}`, { headers });
      if (!response.ok) {
        throw new Error(`Failed to fetch template: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching template:', error);
      throw error;
    }
  }

  /**
   * Create a new template
   */
  async createTemplate(templateData: TemplateCreateRequest): Promise<AutomationTemplate> {
    const headers = await this.getAuthHeaders();

    try {
      const response = await fetch(`${this.baseUrl}/create`, {
        method: 'POST',
        headers,
        body: JSON.stringify(templateData),
      });

      if (!response.ok) {
        throw new Error(`Failed to create template: ${response.statusText}`);
      }

      const result = await response.json();
      return result.template;
    } catch (error) {
      console.error('Error creating template:', error);
      throw error;
    }
  }

  /**
   * Update an existing template
   */
  async updateTemplate(templateId: string, updates: TemplateUpdateRequest): Promise<AutomationTemplate> {
    const headers = await this.getAuthHeaders();

    try {
      const response = await fetch(`${this.baseUrl}/${templateId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`Failed to update template: ${response.statusText}`);
      }

      const result = await response.json();
      return result.template;
    } catch (error) {
      console.error('Error updating template:', error);
      throw error;
    }
  }

  /**
   * Delete a template
   */
  async deleteTemplate(templateId: string): Promise<void> {
    const headers = await this.getAuthHeaders();

    try {
      const response = await fetch(`${this.baseUrl}/${templateId}`, {
        method: 'DELETE',
        headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to delete template: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting template:', error);
      throw error;
    }
  }

  /**
   * Populate default templates
   */
  async populateDefaultTemplates(): Promise<{ message: string; templates: any[] }> {
    const headers = await this.getAuthHeaders();

    try {
      const response = await fetch(`${this.baseUrl}/populate-defaults`, {
        method: 'POST',
        headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to populate templates: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error populating templates:', error);
      throw error;
    }
  }

  /**
   * Get available integrations
   */
  async getAvailableIntegrations(): Promise<{ integrations: any[] }> {
    const headers = await this.getAuthHeaders();

    try {
      const response = await fetch(`${this.baseUrl}/integrations/available`, { headers });
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
   * Get templates by industry for specific pages
   */
  async getTemplatesForCampaignPage(): Promise<AutomationTemplate[]> {
    return this.listTemplates({ industry: 'Generic', active_only: true });
  }

  async getTemplatesForAutomationPage(): Promise<AutomationTemplate[]> {
    const templates = await this.listTemplates({ active_only: true });
    return templates.filter(t => t.industry !== 'Generic');
  }

  /**
   * Deploy a template (creates VAPI agent, N8N workflow, etc.)
   */
  async deployTemplate(templateId: string): Promise<{ success: boolean; deploymentInfo: any }> {
    // This would integrate with the existing deployment services
    // For now, return a mock response
    return {
      success: true,
      deploymentInfo: {
        vapi_assistant_id: `vapi_${templateId}`,
        n8n_workflow_id: `n8n_${templateId}`,
        demo_url: `https://ailabsafrica.com/demos/${templateId}.html`,
      },
    };
  }
}

export const templateManagementService = new TemplateManagementService();
export default templateManagementService;