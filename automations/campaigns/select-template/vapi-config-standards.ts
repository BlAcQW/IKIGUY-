/**
 * Standardized VAPI Configuration Templates
 *
 * Based on successful implementations from Claims Processing and Medical Exam Scheduling
 * templates. These standards ensure consistency across all voice-enabled automations.
 */

export interface VAPIStandardConfig {
  voiceAgentEnabled: boolean;
  agentPersonality: VAPIAgentPersonality;
  systemPromptTemplate: string;
  contextualKnowledge: string[];
  conversationStarters: string[];
  customFunctions: VAPIFunction[];
  callScenarios: VAPICallScenarios;
  webhookConfig: VAPIWebhookConfig;
  voiceSettings: VAPIVoiceSettings;
  conversationFlow: VAPIConversationFlow;
  monitoringConfig: VAPIMonitoringConfig;
}

export interface VAPIAgentPersonality {
  name: string;
  role: string;
  tone: 'professional' | 'friendly' | 'empathetic' | 'authoritative';
  expertise: string[];
  complianceRequirements?: string[];
}

export interface VAPIFunction {
  name: string;
  description: string;
  parameters: {
    type: 'object';
    properties: Record<string, any>;
    required: string[];
  };
  endpoint?: string;
  authentication?: boolean;
}

export interface VAPICallScenarios {
  inbound: boolean;
  outbound: boolean;
  scenarios: string[];
}

export interface VAPIWebhookConfig {
  triggerWorkflow: boolean;
  n8nWebhookUrl: string;
  monitoringWebhookUrl: string;
  authRequired: boolean;
  realTimeAnalytics: boolean;
  sentimentAnalysisEnabled: boolean;
}

export interface VAPIVoiceSettings {
  provider: 'openai' | '11labs' | 'azure';
  voiceId: string;
  model?: string;
  speed?: number;
  stability?: number;
  similarityBoost?: number;
  useSpeakerBoost?: boolean;
  optimizeStreamingLatency?: number;
}

export interface VAPIConversationFlow {
  maxDuration: number;
  silenceTimeout: number;
  interruptible: boolean;
  endCallPhrases: string[];
  escalationTriggers: string[];
}

export interface VAPIMonitoringConfig {
  enabled: boolean;
  sentimentTracking: boolean;
  callRecording: boolean;
  transcriptionEnabled: boolean;
  analyticsWebhook: string;
  performanceMetrics: boolean;
}

/**
 * Insurance Industry VAPI Standards
 */
export const INSURANCE_VAPI_STANDARDS = {
  basePersonality: {
    tone: 'empathetic' as const,
    complianceRequirements: ['NAIC', 'SOX', 'State Regulations'],
    commonExpertise: ['Insurance policies', 'Claims processing', 'Customer service', 'Regulatory compliance']
  },

  standardFunctions: [
    {
      name: 'verifyPolicyHolder',
      description: 'Verify customer identity and policy information',
      parameters: {
        type: 'object',
        properties: {
          policyNumber: { type: 'string' },
          customerName: { type: 'string' },
          dateOfBirth: { type: 'string' }
        },
        required: ['policyNumber', 'customerName']
      }
    },
    {
      name: 'scheduleCallback',
      description: 'Schedule a callback for customer service',
      parameters: {
        type: 'object',
        properties: {
          preferredTime: { type: 'string' },
          phoneNumber: { type: 'string' },
          reason: { type: 'string' }
        },
        required: ['preferredTime', 'phoneNumber']
      }
    }
  ],

  webhookConfig: {
    triggerWorkflow: true,
    authRequired: true,
    realTimeAnalytics: true,
    sentimentAnalysisEnabled: true
  },

  voiceSettings: {
    provider: 'openai' as const,
    voiceId: 'alloy',
    speed: 1.0,
    optimizeStreamingLatency: 2
  },

  conversationFlow: {
    maxDuration: 900, // 15 minutes
    silenceTimeout: 30,
    interruptible: true,
    endCallPhrases: ['goodbye', 'thank you', 'end call', 'hang up'],
    escalationTriggers: ['speak to manager', 'escalate', 'complaint', 'frustrated']
  }
};

/**
 * Healthcare Industry VAPI Standards
 */
export const HEALTHCARE_VAPI_STANDARDS = {
  basePersonality: {
    tone: 'professional' as const,
    complianceRequirements: ['HIPAA', 'SOC2', 'GDPR'],
    commonExpertise: ['Medical scheduling', 'Patient care', 'Insurance coordination', 'HIPAA compliance']
  },

  standardFunctions: [
    {
      name: 'verifyPatientIdentity',
      description: 'Verify patient identity with HIPAA compliance',
      parameters: {
        type: 'object',
        properties: {
          dateOfBirth: { type: 'string' },
          lastName: { type: 'string' },
          memberID: { type: 'string' }
        },
        required: ['dateOfBirth', 'lastName']
      }
    },
    {
      name: 'scheduleAppointment',
      description: 'Schedule medical appointment with availability check',
      parameters: {
        type: 'object',
        properties: {
          appointmentType: { type: 'string' },
          preferredDate: { type: 'string' },
          preferredTime: { type: 'string' },
          locationPreference: { type: 'string' }
        },
        required: ['appointmentType', 'preferredDate']
      }
    }
  ],

  webhookConfig: {
    triggerWorkflow: true,
    authRequired: true,
    realTimeAnalytics: true,
    sentimentAnalysisEnabled: false // HIPAA consideration
  },

  voiceSettings: {
    provider: 'openai' as const,
    voiceId: 'nova',
    speed: 0.9,
    optimizeStreamingLatency: 1
  },

  conversationFlow: {
    maxDuration: 600, // 10 minutes
    silenceTimeout: 20,
    interruptible: true,
    endCallPhrases: ['goodbye', 'thank you', 'end call'],
    escalationTriggers: ['speak to nurse', 'medical emergency', 'urgent']
  }
};

/**
 * Generate VAPI Configuration for Template
 */
export function generateVAPIConfig(
  industry: 'insurance' | 'healthcare' | 'finance',
  templateSpecifics: {
    agentName: string;
    agentRole: string;
    specificExpertise: string[];
    customFunctions: VAPIFunction[];
    systemPromptAdditions?: string;
  }
): VAPIStandardConfig {
  const baseStandards = industry === 'insurance' ? INSURANCE_VAPI_STANDARDS :
                      industry === 'healthcare' ? HEALTHCARE_VAPI_STANDARDS :
                      INSURANCE_VAPI_STANDARDS; // Default to insurance

  const baseSystemPrompt = `You are a professional ${templateSpecifics.agentRole} for {{companyName}}. Your role is to assist customers with ${templateSpecifics.specificExpertise.join(', ')}.

Key responsibilities:
1. Maintain a ${baseStandards.basePersonality.tone} and helpful demeanor
2. Gather accurate information efficiently
3. Provide clear guidance and next steps
4. Escalate complex issues appropriately
5. Ensure compliance with ${baseStandards.basePersonality.complianceRequirements?.join(', ')}

${templateSpecifics.systemPromptAdditions || ''}

Always verify customer identity before proceeding with sensitive information.`;

  return {
    voiceAgentEnabled: true,
    agentPersonality: {
      name: templateSpecifics.agentName,
      role: templateSpecifics.agentRole,
      tone: baseStandards.basePersonality.tone,
      expertise: [...baseStandards.basePersonality.commonExpertise, ...templateSpecifics.specificExpertise],
      complianceRequirements: baseStandards.basePersonality.complianceRequirements
    },
    systemPromptTemplate: baseSystemPrompt,
    contextualKnowledge: [
      'Company policies and procedures',
      'Regulatory requirements',
      'Customer service best practices',
      'Escalation procedures'
    ],
    conversationStarters: [
      "Thank you for calling {{companyName}}. How can I assist you today?",
      "Hello! I'm here to help with your request. May I start by verifying your information?",
      "Good day! I'm your virtual assistant. What can I help you with?"
    ],
    customFunctions: [...baseStandards.standardFunctions, ...templateSpecifics.customFunctions],
    callScenarios: {
      inbound: true,
      outbound: true,
      scenarios: [
        'Customer service inquiries',
        'Information requests',
        'Appointment scheduling',
        'Status updates'
      ]
    },
    webhookConfig: {
      ...baseStandards.webhookConfig,
      n8nWebhookUrl: '{{n8n_instance_url}}/webhook/{{template_id}}',
      monitoringWebhookUrl: '{{api_base_url}}/api/monitoring/webhook/vapi-call'
    },
    voiceSettings: baseStandards.voiceSettings,
    conversationFlow: baseStandards.conversationFlow,
    monitoringConfig: {
      enabled: true,
      sentimentTracking: industry !== 'healthcare', // HIPAA consideration
      callRecording: true,
      transcriptionEnabled: true,
      analyticsWebhook: '{{api_base_url}}/api/monitoring/vapi-analytics',
      performanceMetrics: true
    }
  };
}

/**
 * n8n Webhook Integration Standards
 */
export const N8N_WEBHOOK_STANDARDS = {
  triggerNode: {
    nodeType: 'Webhook',
    config: {
      path: '{{template_id}}',
      method: 'POST',
      authentication: 'basicAuth',
      responseMode: 'responseNode'
    }
  },

  monitoringNode: {
    nodeType: 'HTTP Request',
    config: {
      url: '{{api_base_url}}/api/monitoring/automation-health',
      method: 'POST',
      sendBody: true,
      bodyContentType: 'json'
    }
  },

  conditionalNode: {
    nodeType: 'IF',
    config: {
      conditions: {
        string: [
          {
            value1: '={{$json["status"]}}',
            operation: 'equal',
            value2: 'success'
          }
        ]
      }
    }
  }
};