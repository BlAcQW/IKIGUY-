/**
 * VAPI Agent Generator Service
 *
 * Converts automation templates into fully configured VAPI agents
 * with proper system prompts, functions, and webhook configurations.
 */

import { AutomationTemplate, VAPITemplateConfig, VAPIFunction } from '@/config/automation-templates';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


interface GeneratedVAPIAgent {
  name: string;
  model: {
    provider: string;
    model: string;
    temperature: number;
    systemPrompt: string;
  };
  voice: {
    provider: string;
    voiceId: string;
    stability?: number;
    speed?: number;
  };
  firstMessage: string;
  endCallMessage: string;
  functions: VAPIFunction[];
  serverUrl: string;
  serverUrlSecret: string;
  maxDuration: number;
  silenceTimeout: number;
  interruptible: boolean;
  recordingEnabled: boolean;
  transcriptionEnabled: boolean;
  metadata: {
    templateId: string;
    industry: string;
    category: string;
    tenantId: string;
  };
}

interface WebhookConfiguration {
  endpoint: string;
  secret: string;
  authRequired: boolean;
  triggerWorkflow: boolean;
}

export class VAPIAgentGenerator {
  private static readonly DEFAULT_MODEL = 'gpt-4';
  private static readonly DEFAULT_TEMPERATURE = 0.7;
  private static readonly DEFAULT_VOICE_PROVIDER = '11labs';

  /**
   * Generate a complete VAPI agent configuration from an automation template
   */
  static generateVAPIAgent(
    template: AutomationTemplate,
    tenantId: string,
    customization?: {
      companyName?: string;
      supportEmail?: string;
      supportPhone?: string;
      customPrompt?: string;
    }
  ): GeneratedVAPIAgent {
    if (!template.vapiConfig?.voiceAgentEnabled) {
      throw new Error(`Template ${template.id} does not support voice agent generation`);
    }

    const vapiConfig = template.vapiConfig;
    const agentId = `${template.id}_${tenantId}_${Date.now()}`;

    // Generate system prompt
    const systemPrompt = this.generateSystemPrompt(template, vapiConfig, customization);

    // Generate functions from template workflow
    const functions = this.generateFunctions(template, vapiConfig);

    // Generate webhook configuration
    const webhookConfig = this.generateWebhookConfig(template, tenantId, agentId);

    // Select conversation starter
    const firstMessage = this.selectConversationStarter(vapiConfig);

    return {
      name: `${vapiConfig.agentPersonality.name} - ${template.name}`,
      model: {
        provider: 'openai',
        model: this.DEFAULT_MODEL,
        temperature: this.DEFAULT_TEMPERATURE,
        systemPrompt
      },
      voice: {
        provider: vapiConfig.voiceSettings.provider,
        voiceId: vapiConfig.voiceSettings.voiceId,
        model: vapiConfig.voiceSettings.model || "eleven_flash_v2_5", // Default ElevenLabs model
        stability: vapiConfig.voiceSettings.stability || 0.5,
        similarityBoost: vapiConfig.voiceSettings.similarityBoost || 0.75,
        useSpeakerBoost: vapiConfig.voiceSettings.useSpeakerBoost || true,
        optimizeStreamingLatency: vapiConfig.voiceSettings.optimizeStreamingLatency || 3
      },
      firstMessage,
      endCallMessage: this.generateEndCallMessage(template, vapiConfig),
      functions,
      serverUrl: webhookConfig.endpoint,
      serverUrlSecret: webhookConfig.secret,
      maxDuration: vapiConfig.conversationFlow.maxDuration,
      silenceTimeout: vapiConfig.conversationFlow.silenceTimeout,
      interruptible: vapiConfig.conversationFlow.interruptible,
      recordingEnabled: true,
      transcriptionEnabled: true,
      metadata: {
        templateId: template.id,
        industry: template.industry,
        category: template.category || 'general',
        tenantId
      }
    };
  }

  /**
   * Generate system prompt with template variables filled in
   */
  private static generateSystemPrompt(
    template: AutomationTemplate,
    vapiConfig: VAPITemplateConfig,
    customization?: {
      companyName?: string;
      supportEmail?: string;
      supportPhone?: string;
      customPrompt?: string;
    }
  ): string {
    let systemPrompt = vapiConfig.systemPromptTemplate;

    // Replace template variables
    const variables = {
      companyName: customization?.companyName || 'Your Company',
      supportEmail: customization?.supportEmail || 'support@yourcompany.com',
      supportPhone: customization?.supportPhone || '1-800-SUPPORT',
      templateName: template.name,
      industry: template.industry,
      category: template.category || 'general'
    };

    Object.entries(variables).forEach(([key, value]) => {
      const regex = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
      systemPrompt = systemPrompt.replace(regex, value);
    });

    // Add contextual knowledge
    if (vapiConfig.contextualKnowledge.length > 0) {
      systemPrompt += '\n\nAdditional Context:\n';
      vapiConfig.contextualKnowledge.forEach(knowledge => {
        systemPrompt += `- ${knowledge}\n`;
      });
    }

    // Add workflow-specific instructions
    systemPrompt += '\n\nWorkflow Integration:\n';
    systemPrompt += 'You have access to automated workflow functions that can:\n';
    template.workflow.forEach(step => {
      systemPrompt += `- ${step.name}: ${this.getStepDescription(step)}\n`;
    });

    // Add compliance information
    if (template.complianceFrameworks && template.complianceFrameworks.length > 0) {
      systemPrompt += '\n\nCompliance Requirements:\n';
      systemPrompt += `This conversation must comply with: ${template.complianceFrameworks.join(', ')}\n`;
    }

    // Add custom prompt if provided
    if (customization?.customPrompt) {
      systemPrompt += '\n\nAdditional Instructions:\n';
      systemPrompt += customization.customPrompt;
    }

    return systemPrompt;
  }

  /**
   * Generate VAPI functions from template configuration and workflow
   */
  private static generateFunctions(
    template: AutomationTemplate,
    vapiConfig: VAPITemplateConfig
  ): VAPIFunction[] {
    const functions: VAPIFunction[] = [];

    // Add custom functions from template
    if (vapiConfig.customFunctions) {
      functions.push(...vapiConfig.customFunctions);
    }

    // Auto-generate functions from workflow steps if enabled
    if (vapiConfig.autoGenerateFunctions) {
      const autoFunctions = this.generateFunctionsFromWorkflow(template);
      functions.push(...autoFunctions);
    }

    // Add standard utility functions
    const utilityFunctions = this.generateUtilityFunctions(template);
    functions.push(...utilityFunctions);

    return functions;
  }

  /**
   * Generate functions automatically from workflow steps
   */
  private static generateFunctionsFromWorkflow(template: AutomationTemplate): VAPIFunction[] {
    const functions: VAPIFunction[] = [];

    template.workflow.forEach(step => {
      // Only create functions for integration steps that make sense for voice interaction
      if (step.type === 'integration' && this.isVoiceCompatibleStep(step)) {
        const func = this.createFunctionFromStep(step, template);
        if (func) {
          functions.push(func);
        }
      }
    });

    return functions;
  }

  /**
   * Check if a workflow step is compatible with voice interaction
   */
  private static isVoiceCompatibleStep(step: any): boolean {
    const voiceCompatibleCategories = [
      'messaging', 'email', 'crm', 'database', 'calendar', 'support'
    ];
    return voiceCompatibleCategories.includes(step.integrationCategory);
  }

  /**
   * Create a VAPI function from a workflow step
   */
  private static createFunctionFromStep(step: any, template: AutomationTemplate): VAPIFunction | null {
    const capability = step.config?.capability;
    if (!capability) return null;

    // Generate function based on capability type
    switch (capability) {
      case 'customer_communication':
        return {
          name: 'sendCustomerUpdate',
          description: `Send update to customer via ${step.integrationCategory}`,
          parameters: {
            type: 'object',
            properties: {
              message: { type: 'string', description: 'Message to send to customer' },
              urgency: { type: 'string', enum: ['low', 'medium', 'high'], description: 'Message urgency level' }
            },
            required: ['message']
          },
          workflowStepId: step.id
        };

      case 'claims_processing':
        return {
          name: 'processClaimAction',
          description: `Process claim action: ${step.config.action}`,
          parameters: {
            type: 'object',
            properties: {
              claimId: { type: 'string', description: 'Claim identifier' },
              action: { type: 'string', description: 'Action to perform' },
              notes: { type: 'string', description: 'Additional notes' }
            },
            required: ['claimId', 'action']
          },
          workflowStepId: step.id
        };

      default:
        return {
          name: `execute${step.name.replace(/\s+/g, '')}`,
          description: step.name,
          parameters: {
            type: 'object',
            properties: {
              input: { type: 'string', description: 'Input for the workflow step' }
            },
            required: ['input']
          },
          workflowStepId: step.id
        };
    }
  }

  /**
   * Generate standard utility functions for all agents
   */
  private static generateUtilityFunctions(template: AutomationTemplate): VAPIFunction[] {
    return [
      {
        name: 'transferToHuman',
        description: 'Transfer the call to a human agent when the issue is too complex',
        parameters: {
          type: 'object',
          properties: {
            reason: { type: 'string', description: 'Reason for transfer' },
            department: {
              type: 'string',
              enum: ['general', 'technical', 'billing', 'claims', 'sales'],
              description: 'Department to transfer to'
            },
            urgent: { type: 'boolean', description: 'Whether this is an urgent transfer' }
          },
          required: ['reason', 'department']
        }
      },
      {
        name: 'scheduleFollowUp',
        description: 'Schedule a follow-up call or email',
        parameters: {
          type: 'object',
          properties: {
            contactMethod: { type: 'string', enum: ['call', 'email'], description: 'How to follow up' },
            timeframe: { type: 'string', description: 'When to follow up (e.g., "tomorrow", "next week")' },
            reason: { type: 'string', description: 'Reason for follow-up' }
          },
          required: ['contactMethod', 'timeframe', 'reason']
        }
      }
    ];
  }

  /**
   * Generate webhook configuration for the agent
   */
  private static generateWebhookConfig(
    template: AutomationTemplate,
    tenantId: string,
    agentId: string
  ): WebhookConfiguration {
    const baseUrl = process.env.VITE_API_BASE_URL || API_BASE_URL;

    return {
      endpoint: `${baseUrl}/vapi/webhooks/${tenantId}/${template.id}/${agentId}`,
      secret: this.generateWebhookSecret(tenantId, template.id),
      authRequired: template.vapiConfig?.webhookConfig?.authRequired ?? true,
      triggerWorkflow: template.vapiConfig?.webhookConfig?.triggerWorkflow ?? true
    };
  }

  /**
   * Generate a secure webhook secret
   */
  private static generateWebhookSecret(tenantId: string, templateId: string): string {
    const timestamp = Date.now();
    const randomBytes = Math.random().toString(36).substring(2, 15);
    return `vapi_${tenantId}_${templateId}_${timestamp}_${randomBytes}`;
  }

  /**
   * Select an appropriate conversation starter
   */
  private static selectConversationStarter(vapiConfig: VAPITemplateConfig): string {
    if (vapiConfig.conversationStarters.length > 0) {
      // Select first starter for consistency
      return vapiConfig.conversationStarters[0];
    }

    // Fallback based on agent role
    const role = vapiConfig.agentPersonality.role.toLowerCase();
    if (role.includes('claims')) {
      return 'Hello, thank you for calling our claims department. How may I assist you today?';
    } else if (role.includes('sales')) {
      return 'Hello! Thank you for your interest in our services. How can I help you today?';
    } else if (role.includes('support')) {
      return 'Hi there! I\'m here to help you with any questions or issues. What can I assist you with?';
    }

    return 'Hello! Thank you for calling. How may I assist you today?';
  }

  /**
   * Generate appropriate end call message
   */
  private static generateEndCallMessage(
    template: AutomationTemplate,
    vapiConfig: VAPITemplateConfig
  ): string {
    if (vapiConfig.conversationFlow.endCallPhrases.length > 0) {
      return vapiConfig.conversationFlow.endCallPhrases[0];
    }

    const industry = template.industry;
    switch (industry) {
      case 'insurance':
        return 'Thank you for calling. Your reference number will be sent to your phone. Have a great day!';
      case 'healthcare':
        return 'Thank you for calling. Take care of yourself and have a wonderful day!';
      case 'financial':
        return 'Thank you for your business. If you need any further assistance, please don\'t hesitate to call.';
      default:
        return 'Thank you for calling. Have a great day!';
    }
  }

  /**
   * Get description for a workflow step
   */
  private static getStepDescription(step: any): string {
    const action = step.config?.action || 'process';
    const category = step.integrationCategory || 'system';

    return `${action} using ${category} integration`;
  }

  /**
   * Validate generated VAPI agent configuration
   */
  static validateVAPIAgent(agent: GeneratedVAPIAgent): {
    valid: boolean;
    errors: string[];
    warnings: string[];
  } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Required field validation
    if (!agent.name || agent.name.length < 3) {
      errors.push('Agent name must be at least 3 characters long');
    }

    if (!agent.model.systemPrompt || agent.model.systemPrompt.length < 50) {
      errors.push('System prompt must be at least 50 characters long');
    }

    if (!agent.voice.voiceId) {
      errors.push('Voice ID is required');
    }

    if (!agent.firstMessage || agent.firstMessage.length < 10) {
      errors.push('First message must be at least 10 characters long');
    }

    if (!agent.functions || agent.functions.length === 0) {
      warnings.push('No functions defined - agent will have limited capabilities');
    }

    // Configuration validation
    if (agent.maxDuration < 60 || agent.maxDuration > 3600) {
      warnings.push('Max duration should be between 1 minute and 1 hour');
    }

    if (agent.silenceTimeout < 5 || agent.silenceTimeout > 30) {
      warnings.push('Silence timeout should be between 5 and 30 seconds');
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }
}

export default VAPIAgentGenerator;