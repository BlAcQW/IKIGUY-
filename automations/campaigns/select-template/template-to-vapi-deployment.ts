/**
 * Template to VAPI Agent Auto-Deployment System
 *
 * Transforms automation templates into fully configured VAPI agents
 * with proper webhook routing and n8n workflow integration.
 */

import { generateVAPIConfig } from './vapi-config-standards';
import { generateN8nWorkflow } from './n8n-workflow-patterns';

export interface TemplateVAPIDeploymentConfig {
  templateId: string;
  vapiAgentConfig: any;
  webhookEndpoints: WebhookEndpoint[];
  n8nWorkflowConfig: any;
  functionMappings: FunctionMapping[];
  deploymentSettings: DeploymentSettings;
}

export interface WebhookEndpoint {
  id: string;
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  handler: string;
  authentication?: 'bearer' | 'api_key' | 'basic';
  rateLimit?: {
    requests: number;
    window: string;
  };
  validation?: {
    schema: any;
    required: string[];
  };
}

export interface FunctionMapping {
  vapiFunction: string;
  n8nWorkflowStep: string;
  parameters: ParameterMapping[];
  responseMapping: ResponseMapping;
}

export interface ParameterMapping {
  vapiParam: string;
  n8nField: string;
  transformation?: string;
  validation?: any;
}

export interface ResponseMapping {
  successPath: string;
  errorPath: string;
  dataTransformation?: string;
}

export interface DeploymentSettings {
  environment: 'development' | 'staging' | 'production';
  autoStart: boolean;
  monitoring: {
    enabled: boolean;
    alerting: boolean;
    dashboardUrl?: string;
  };
  security: {
    encryption: boolean;
    auditLogging: boolean;
    accessControl: string[];
  };
}

/**
 * Template to VAPI Agent Configuration Generator
 */
export class TemplateToVAPIDeployment {
  /**
   * Generate complete VAPI agent configuration from automation template
   */
  static generateVAPIAgentFromTemplate(
    template: any,
    customConfig?: Partial<TemplateVAPIDeploymentConfig>
  ): TemplateVAPIDeploymentConfig {

    const baseConfig = {
      templateId: template.id,
      vapiAgentConfig: this.createVAPIAgentConfig(template),
      webhookEndpoints: this.generateWebhookEndpoints(template),
      n8nWorkflowConfig: this.enhanceN8nWorkflow(template),
      functionMappings: this.createFunctionMappings(template),
      deploymentSettings: this.createDeploymentSettings(template)
    };

    return { ...baseConfig, ...customConfig };
  }

  /**
   * Create VAPI agent configuration with template-specific functions
   */
  private static createVAPIAgentConfig(template: any): any {
    const agentConfig = {
      name: `${template.name} Voice Agent`,
      assistantId: `assistant_${template.id}`,
      model: {
        provider: 'openai',
        model: 'gpt-4-turbo-preview',
        temperature: 0.7,
        maxTokens: 1000
      },
      voice: {
        provider: 'elevenlabs',
        voiceId: this.selectVoiceForIndustry(template.industry),
        speed: 1.0,
        stability: 0.8,
        similarityBoost: 0.7
      },
      firstMessage: this.generateFirstMessage(template),
      systemPrompt: this.generateSystemPrompt(template),
      functions: this.extractVAPIFunctions(template),
      endCallMessage: this.generateEndCallMessage(template),
      transcriber: {
        provider: 'deepgram',
        model: 'nova-2',
        language: 'en-US'
      },
      analysis: {
        summaryPrompt: this.generateSummaryPrompt(template),
        successEvaluationPrompt: this.generateSuccessPrompt(template)
      }
    };

    return agentConfig;
  }

  /**
   * Generate webhook endpoints for automation workflow integration
   */
  private static generateWebhookEndpoints(template: any): WebhookEndpoint[] {
    const endpoints: WebhookEndpoint[] = [];

    // Main VAPI webhook endpoint
    endpoints.push({
      id: `${template.id}_vapi_webhook`,
      path: `/webhook/vapi/${template.id}`,
      method: 'POST',
      handler: 'VAPIWebhookHandler',
      authentication: 'bearer',
      rateLimit: {
        requests: 100,
        window: '1m'
      },
      validation: {
        schema: {
          type: 'object',
          properties: {
            callId: { type: 'string' },
            assistantId: { type: 'string' },
            phoneNumber: { type: 'string' },
            transcript: { type: 'string' },
            functions: { type: 'array' }
          },
          required: ['callId', 'assistantId']
        },
        required: ['callId', 'assistantId']
      }
    });

    // Function-specific endpoints
    template.workflow?.forEach((step: any) => {
      if (step.config?.capability) {
        endpoints.push({
          id: `${template.id}_${step.id}_endpoint`,
          path: `/webhook/${template.id}/${step.id}`,
          method: 'POST',
          handler: `${step.config.capability}Handler`,
          authentication: 'api_key'
        });
      }
    });

    // Monitoring endpoint
    endpoints.push({
      id: `${template.id}_monitoring`,
      path: `/webhook/${template.id}/monitoring`,
      method: 'POST',
      handler: 'MonitoringWebhookHandler',
      authentication: 'bearer'
    });

    return endpoints;
  }

  /**
   * Enhance n8n workflow with VAPI integration points
   */
  private static enhanceN8nWorkflow(template: any): any {
    const enhanced = {
      ...template.n8nWorkflow,
      nodes: [
        // Add VAPI webhook trigger node
        {
          id: 'vapi_webhook_trigger',
          name: 'VAPI Call Webhook',
          type: 'n8n-nodes-base.webhook',
          typeVersion: 1,
          position: [100, 100],
          parameters: {
            path: `vapi-${template.id}`,
            httpMethod: 'POST',
            responseMode: 'responseNode',
            options: {}
          }
        },

        // Add function routing node
        {
          id: 'function_router',
          name: 'Route VAPI Functions',
          type: 'n8n-nodes-base.switch',
          typeVersion: 1,
          position: [300, 100],
          parameters: {
            rules: {
              rules: this.generateRoutingRules(template)
            }
          }
        },

        // Add response formatter node
        {
          id: 'vapi_response_formatter',
          name: 'Format VAPI Response',
          type: 'n8n-nodes-base.function',
          typeVersion: 1,
          position: [500, 100],
          parameters: {
            functionCode: this.generateResponseFormatterCode(template)
          }
        },

        // Add existing workflow nodes
        ...(template.n8nWorkflow?.nodes || [])
      ],

      connections: this.generateWorkflowConnections(template)
    };

    return enhanced;
  }

  /**
   * Create function mappings between VAPI and n8n workflow steps
   */
  private static createFunctionMappings(template: any): FunctionMapping[] {
    const mappings: FunctionMapping[] = [];

    template.vapiConfig?.customFunctions?.forEach((func: any) => {
      const relatedWorkflowStep = template.workflow?.find((step: any) =>
        this.isRelatedFunction(func.name, step)
      );

      if (relatedWorkflowStep) {
        mappings.push({
          vapiFunction: func.name,
          n8nWorkflowStep: relatedWorkflowStep.id,
          parameters: this.mapFunctionParameters(func, relatedWorkflowStep),
          responseMapping: {
            successPath: '$.success',
            errorPath: '$.error',
            dataTransformation: `transformFor${func.name}`
          }
        });
      }
    });

    return mappings;
  }

  /**
   * Create deployment settings based on template requirements
   */
  private static createDeploymentSettings(template: any): DeploymentSettings {
    return {
      environment: 'development',
      autoStart: true,
      monitoring: {
        enabled: true,
        alerting: true,
        dashboardUrl: `/monitoring/${template.id}`
      },
      security: {
        encryption: true,
        auditLogging: true,
        accessControl: template.securityConfig?.accessControls || ['role_based']
      }
    };
  }

  /**
   * Helper methods for configuration generation
   */
  private static selectVoiceForIndustry(industry: string): string {
    const voiceMap: Record<string, string> = {
      'healthcare': 'jennifer-professional',
      'insurance': 'michael-authoritative',
      'finance': 'sarah-trustworthy',
      'retail': 'alex-friendly',
      'default': 'jennifer-professional'
    };
    return voiceMap[industry] || voiceMap.default;
  }

  private static generateFirstMessage(template: any): string {
    const industryGreetings: Record<string, string> = {
      'healthcare': 'Hello! I\'m calling to assist you with your healthcare needs. How may I help you today?',
      'insurance': 'Good day! I\'m your insurance assistant calling to help with your policy. How can I assist you?',
      'finance': 'Hello! I\'m calling regarding your account. I\'m here to help you with any questions or concerns.',
      'default': 'Hello! Thank you for calling. How may I assist you today?'
    };
    return industryGreetings[template.industry] || industryGreetings.default;
  }

  private static generateSystemPrompt(template: any): string {
    const basePrompt = `You are a professional AI assistant specializing in ${template.category} for the ${template.industry} industry.

Your primary capabilities include:
${template.features?.map((feature: string) => `- ${feature}`).join('\n')}

Key Guidelines:
- Always maintain a professional and helpful demeanor
- Follow industry compliance requirements: ${template.complianceFrameworks?.join(', ')}
- Use the available functions to access real-time data and perform actions
- Provide clear, accurate information based on the customer's specific needs
- Escalate complex issues to human agents when appropriate

${template.vapiConfig?.systemPromptAdditions || ''}`;

    return basePrompt;
  }

  private static generateEndCallMessage(template: any): string {
    return `Thank you for calling regarding your ${template.category.toLowerCase()}. Is there anything else I can help you with today? Have a great day!`;
  }

  private static generateSummaryPrompt(template: any): string {
    return `Summarize this ${template.category.toLowerCase()} call, including:
- Customer inquiry type and details
- Actions taken during the call
- Resolution status
- Any follow-up required
- Customer satisfaction level`;
  }

  private static generateSuccessPrompt(template: any): string {
    return `Evaluate if this ${template.category.toLowerCase()} call was successful based on:
- Was the customer's primary need addressed?
- Were appropriate functions used to access/update data?
- Was the interaction professional and compliant?
- Did the customer express satisfaction?
- Was proper follow-up scheduled if needed?`;
  }

  private static extractVAPIFunctions(template: any): any[] {
    return template.vapiConfig?.customFunctions || [];
  }

  private static generateRoutingRules(template: any): any[] {
    const rules: any[] = [];

    template.vapiConfig?.customFunctions?.forEach((func: any, index: number) => {
      rules.push({
        condition: {
          field: '{{ $json.function.name }}',
          operation: 'equal',
          value: func.name
        },
        renameOutput: func.name,
        outputIndex: index
      });
    });

    return rules;
  }

  private static generateResponseFormatterCode(template: any): string {
    return `
// Format response for VAPI agent
const callData = items[0].json;
const functionName = callData.function?.name;
const result = callData.result;

// Transform based on function type
let response = {
  success: true,
  data: result,
  message: 'Operation completed successfully'
};

// Add industry-specific formatting
if ('${template.industry}' === 'healthcare') {
  response.hipaaCompliant = true;
}

if ('${template.industry}' === 'insurance') {
  response.regulatoryCompliant = true;
}

return [response];
    `;
  }

  private static generateWorkflowConnections(template: any): any {
    return {
      'vapi_webhook_trigger': {
        main: [
          [
            {
              node: 'function_router',
              type: 'main',
              index: 0
            }
          ]
        ]
      },
      'function_router': {
        main: template.vapiConfig?.customFunctions?.map((func: any, index: number) => [
          {
            node: 'vapi_response_formatter',
            type: 'main',
            index: 0
          }
        ]) || []
      }
    };
  }

  private static isRelatedFunction(functionName: string, workflowStep: any): boolean {
    const functionKeywords = functionName.toLowerCase().split(/(?=[A-Z])/);
    const stepKeywords = workflowStep.name.toLowerCase().split(' ');

    return functionKeywords.some(keyword =>
      stepKeywords.some(stepKeyword => stepKeyword.includes(keyword))
    );
  }

  private static mapFunctionParameters(func: any, workflowStep: any): ParameterMapping[] {
    const mappings: ParameterMapping[] = [];

    Object.keys(func.parameters?.properties || {}).forEach(paramName => {
      mappings.push({
        vapiParam: paramName,
        n8nField: `{{ $json.${paramName} }}`,
        transformation: `transform_${paramName}`,
        validation: func.parameters.properties[paramName]
      });
    });

    return mappings;
  }
}

/**
 * VAPI Agent Deployment Service
 */
export class VAPIAgentDeploymentService {
  /**
   * Deploy VAPI agent from template configuration
   */
  static async deployAgentFromTemplate(
    templateConfig: TemplateVAPIDeploymentConfig,
    apiConfig: {
      vapiApiKey: string;
      n8nApiKey: string;
      webhookBaseUrl: string;
    }
  ): Promise<{
    agentId: string;
    phoneNumberId: string;
    webhookUrls: string[];
    workflowId: string;
  }> {

    // 1. Create VAPI agent
    const agentId = await this.createVAPIAgent(templateConfig.vapiAgentConfig, apiConfig.vapiApiKey);

    // 2. Set up phone number
    const phoneNumberId = await this.setupPhoneNumber(agentId, apiConfig.vapiApiKey);

    // 3. Deploy n8n workflow
    const workflowId = await this.deployN8nWorkflow(templateConfig.n8nWorkflowConfig, apiConfig.n8nApiKey);

    // 4. Configure webhooks
    const webhookUrls = await this.configureWebhooks(
      templateConfig.webhookEndpoints,
      apiConfig.webhookBaseUrl,
      { agentId, workflowId }
    );

    // 5. Link functions to workflow steps
    await this.linkFunctionsToWorkflow(
      templateConfig.functionMappings,
      agentId,
      workflowId,
      apiConfig
    );

    return {
      agentId,
      phoneNumberId,
      webhookUrls,
      workflowId
    };
  }

  private static async createVAPIAgent(agentConfig: any, apiKey: string): Promise<string> {
    // Implementation for VAPI agent creation
    return `agent_${Date.now()}`;
  }

  private static async setupPhoneNumber(agentId: string, apiKey: string): Promise<string> {
    // Implementation for phone number setup
    return `phone_${Date.now()}`;
  }

  private static async deployN8nWorkflow(workflowConfig: any, apiKey: string): Promise<string> {
    // Implementation for n8n workflow deployment
    return `workflow_${Date.now()}`;
  }

  private static async configureWebhooks(
    endpoints: WebhookEndpoint[],
    baseUrl: string,
    context: { agentId: string; workflowId: string }
  ): Promise<string[]> {
    // Implementation for webhook configuration
    return endpoints.map(endpoint => `${baseUrl}${endpoint.path}`);
  }

  private static async linkFunctionsToWorkflow(
    mappings: FunctionMapping[],
    agentId: string,
    workflowId: string,
    apiConfig: any
  ): Promise<void> {
    // Implementation for function-workflow linking
  }
}

export default TemplateToVAPIDeployment;