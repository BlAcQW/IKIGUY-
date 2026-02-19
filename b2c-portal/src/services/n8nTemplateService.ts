import type { AutomationTemplate as CampaignTemplate } from '@/services/TemplateManagementService';

export interface N8nWorkflowTemplate {
  id: number;
  name: string;
  description: string;
  nodes: Array<{
    id: string;
    type: string;
    name: string;
    position: [number, number];
  }>;
  connections: Record<string, any>;
  views: number;
  created: string;
  url: string;
  metadata?: {
    categories: string[];
    complexity: string;
    use_cases: string[];
    estimated_setup_minutes: number;
    required_services: string[];
    key_features: string[];
    target_audience: string[];
  };
}

export interface N8nWorkflowImportResult {
  success: boolean;
  workflow?: N8nWorkflowTemplate;
  error?: string;
}

class N8nTemplateService {
  private static instance: N8nTemplateService;
  private templateCache: Map<number, N8nWorkflowTemplate> = new Map();

  static getInstance(): N8nTemplateService {
    if (!N8nTemplateService.instance) {
      N8nTemplateService.instance = new N8nTemplateService();
    }
    return N8nTemplateService.instance;
  }

  async getTemplateById(templateId: number): Promise<N8nWorkflowImportResult> {
    try {
      if (this.templateCache.has(templateId)) {
        return {
          success: true,
          workflow: this.templateCache.get(templateId)!
        };
      }

      const response = await this.fetchFromN8nMcp(templateId);

      if (response.success && response.workflow) {
        this.templateCache.set(templateId, response.workflow);
      }

      return response;
    } catch (error) {
      console.error('Error fetching n8n template:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async searchTemplates(query: string, limit: number = 10): Promise<{
    success: boolean;
    templates?: Array<Partial<N8nWorkflowTemplate>>;
    error?: string;
  }> {
    try {
      const searchResult = await this.executeN8nMcpCommand('search_templates', {
        query,
        limit
      });

      if (searchResult.success) {
        return {
          success: true,
          templates: searchResult.items || []
        };
      }

      return {
        success: false,
        error: searchResult.error || 'Search failed'
      };
    } catch (error) {
      console.error('Error searching n8n templates:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Search error'
      };
    }
  }

  async importTemplateToWorkflow(
    templateId: number,
    campaignId: string
  ): Promise<{
    success: boolean;
    workflowId?: string;
    error?: string;
  }> {
    try {
      const templateResult = await this.getTemplateById(templateId);

      if (!templateResult.success || !templateResult.workflow) {
        return {
          success: false,
          error: templateResult.error || 'Template not found'
        };
      }

      const workflow = templateResult.workflow;

      const workflowName = `${workflow.name} - Campaign ${campaignId}`;
      const workflowData = {
        name: workflowName,
        nodes: workflow.nodes,
        connections: workflow.connections,
        settings: {
          executionOrder: 'v1' as const,
          saveDataErrorExecution: 'all' as const,
          saveDataSuccessExecution: 'all' as const,
          saveManualExecutions: true,
          saveExecutionProgress: true
        }
      };

      const createResult = await this.executeN8nMcpCommand('n8n_create_workflow', workflowData);

      if (createResult.success) {
        return {
          success: true,
          workflowId: createResult.id
        };
      }

      return {
        success: false,
        error: createResult.error || 'Failed to create workflow'
      };
    } catch (error) {
      console.error('Error importing template to workflow:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Import error'
      };
    }
  }

  async validateTemplate(template: CampaignTemplate): Promise<{
    valid: boolean;
    issues: string[];
    recommendations: string[];
  }> {
    const issues: string[] = [];
    const recommendations: string[] = [];

    if (template.n8nTemplateId) {
      try {
        const templateResult = await this.getTemplateById(template.n8nTemplateId);

        if (!templateResult.success) {
          issues.push(`Template ${template.n8nTemplateId} not found in n8n repository`);
        } else if (templateResult.workflow) {
          const workflow = templateResult.workflow;

          if (workflow.metadata?.complexity === 'complex' && template.difficulty === 'beginner') {
            recommendations.push('Consider marking this template as intermediate or advanced difficulty');
          }

          if (workflow.metadata?.estimated_setup_minutes &&
              workflow.metadata.estimated_setup_minutes > 60 &&
              !template.estimatedSetupTime.includes('60')) {
            recommendations.push(`Template may require longer setup time (${workflow.metadata.estimated_setup_minutes} minutes)`);
          }

          const requiredServices = workflow.metadata?.required_services || [];
          const missingIntegrations = requiredServices.filter(
            service => !template.defaultIntegrations.includes(service.toLowerCase())
          );

          if (missingIntegrations.length > 0) {
            recommendations.push(`Consider adding integrations: ${missingIntegrations.join(', ')}`);
          }
        }
      } catch (error) {
        issues.push(`Error validating template: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    return {
      valid: issues.length === 0,
      issues,
      recommendations
    };
  }

  clearCache(): void {
    this.templateCache.clear();
  }

  private async fetchFromN8nMcp(templateId: number): Promise<N8nWorkflowImportResult> {
    try {
      const result = await this.executeN8nMcpCommand('get_template', {
        templateId,
        mode: 'full'
      });

      if (result.success && result.template) {
        return {
          success: true,
          workflow: this.mapN8nTemplateResponse(result.template)
        };
      }

      return {
        success: false,
        error: result.error || 'Template fetch failed'
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'MCP communication error'
      };
    }
  }

  private async executeN8nMcpCommand(command: string, params: any): Promise<any> {
    const response = await fetch('/api/n8n-mcp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        command,
        params
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  private mapN8nTemplateResponse(template: any): N8nWorkflowTemplate {
    return {
      id: template.id,
      name: template.name,
      description: template.description || '',
      nodes: template.nodes || [],
      connections: template.connections || {},
      views: template.views || 0,
      created: template.created || new Date().toISOString(),
      url: template.url || `https://n8n.io/workflows/${template.id}`,
      metadata: template.metadata
    };
  }
}

export const n8nTemplateService = N8nTemplateService.getInstance();
export default n8nTemplateService;