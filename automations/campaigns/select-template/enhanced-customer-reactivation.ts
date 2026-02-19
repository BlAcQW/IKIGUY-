/**
 * Enhanced Customer Reactivation Template with VAPI + N8N Integration
 *
 * AI-powered customer reactivation campaign featuring behavioral analysis,
 * personalized voice outreach, win-back offers, churn prediction, and comprehensive analytics.
 */

import { TemplateToVAPIDeployment, TemplateVAPIDeploymentConfig } from './template-to-vapi-deployment';

export const ENHANCED_CUSTOMER_REACTIVATION_TEMPLATE = {
  id: 'enhanced_customer_reactivation_vapi_n8n',
  name: 'Enhanced Customer Reactivation with VAPI + n8n',
  description: 'AI-powered customer reactivation and win-back campaign featuring behavioral analysis, personalized voice calls, churn prediction, dynamic offer generation, and comprehensive reactivation analytics',
  industry: 'retention',
  category: 'Customer Retention',
  complexity: 'Advanced' as const,
  estimatedTime: '30 min setup, 2-4 weeks campaign',
  rating: 4.8,
  usageCount: 15420,
  popular: true,
  integrationCategories: ['AI Voice Agent', 'Workflow Automation', 'CRM Integration', 'Analytics'],

  // Template-to-VAPI Deployment Configuration
  deploymentConfig: {
    enableAutoDeployment: true,
    useVAPIAgentWizard: true,
    complianceFrameworks: ['GDPR', 'CCPA', 'CAN-SPAM'],
    securityConfig: {
      accessControls: ['role_based', 'customer_data_protection'],
      dataRetention: '2_years',
      sensitiveDataHandling: 'encrypted'
    }
  } as const,

  // VAPI Configuration with specialized customer reactivation functions
  vapiConfig: {
    assistantId: 'asst_customer_reactivation_enhanced',
    name: 'Customer Reactivation AI Assistant',
    model: {
      provider: 'openai',
      model: 'gpt-4o',
      temperature: 0.4,
      maxTokens: 300
    },
    voice: {
      provider: '11labs',
      voiceId: 'pNInz6obpgDQGcFmaJgB',  // Warm, friendly voice
      stability: 0.6,
      similarityBoost: 0.8,
      style: 0.3,
      useSpeakerBoost: true
    },
    firstMessage: "Hi! I'm calling from [COMPANY_NAME] because we've missed having you as a valued customer. I'd love to chat about how we can welcome you back with some exciting new benefits. Do you have a moment to talk?",
    systemPrompt: `You are a warm, empathetic customer reactivation specialist for [COMPANY_NAME]. Your goal is to reconnect with dormant customers and understand why they stopped engaging, then provide personalized solutions to bring them back.

## Your Approach:
- Be genuinely curious about their experience and listen actively
- Acknowledge any past issues without being defensive
- Focus on value and benefits that matter to them specifically
- Offer personalized incentives and solutions
- Create urgency around limited-time offers when appropriate
- Always end with a clear next step

## Key Responsibilities:
1. **Relationship Rebuilding**: Reconnect warmly and professionally
2. **Churn Analysis**: Understand why they became inactive
3. **Value Demonstration**: Show new features, improvements, or benefits
4. **Personalized Offers**: Present relevant win-back incentives
5. **Objection Handling**: Address concerns and barriers to return
6. **Next Steps**: Schedule follow-ups or process reactivations

## Available Tools:
- **analyze_customer_behavior**: Analyze customer history and engagement patterns
- **identify_churn_reasons**: Determine likely reasons for customer inactivity
- **generate_personalized_offer**: Create customized win-back offers
- **check_customer_segment**: Determine customer value and segment
- **schedule_follow_up**: Book future touchpoints or demos
- **process_reactivation**: Handle immediate reactivation requests
- **update_preferences**: Modify customer preferences and communication settings
- **escalate_to_retention_specialist**: Transfer complex cases to human agents

Always maintain a helpful, understanding tone and focus on rebuilding the relationship.`,

    functions: [
      {
        name: 'analyze_customer_behavior',
        description: 'Analyze customer history, purchase patterns, engagement data, and behavioral signals to understand their relationship with the company',
        parameters: {
          type: 'object',
          properties: {
            customer_id: {
              type: 'string',
              description: 'Unique customer identifier'
            },
            include_purchase_history: {
              type: 'boolean',
              description: 'Include detailed purchase and transaction history'
            },
            analyze_engagement_patterns: {
              type: 'boolean',
              description: 'Analyze email opens, website visits, app usage, etc.'
            },
            time_period_months: {
              type: 'integer',
              description: 'Number of months to analyze (default: 12)'
            }
          },
          required: ['customer_id']
        }
      },
      {
        name: 'identify_churn_reasons',
        description: 'Determine likely reasons for customer churn using AI analysis of behavior patterns, support tickets, and engagement data',
        parameters: {
          type: 'object',
          properties: {
            customer_id: {
              type: 'string',
              description: 'Customer identifier'
            },
            include_support_history: {
              type: 'boolean',
              description: 'Include support ticket analysis for issue identification'
            },
            analyze_competitor_activity: {
              type: 'boolean',
              description: 'Check for signs of competitor switching'
            }
          },
          required: ['customer_id']
        }
      },
      {
        name: 'generate_personalized_offer',
        description: 'Create customized win-back offers based on customer value, preferences, and churn reasons',
        parameters: {
          type: 'object',
          properties: {
            customer_id: {
              type: 'string',
              description: 'Customer identifier'
            },
            customer_value_tier: {
              type: 'string',
              enum: ['high_value', 'medium_value', 'standard'],
              description: 'Customer value classification'
            },
            churn_reason: {
              type: 'string',
              enum: ['price_sensitivity', 'feature_gaps', 'poor_experience', 'competitor_switch', 'lack_of_engagement', 'life_changes'],
              description: 'Primary reason for churn'
            },
            preferred_offer_type: {
              type: 'string',
              enum: ['discount', 'free_trial', 'bonus_features', 'personal_onboarding', 'account_credit'],
              description: 'Type of offer to generate'
            }
          },
          required: ['customer_id', 'customer_value_tier']
        }
      },
      {
        name: 'check_customer_segment',
        description: 'Determine customer value tier, lifecycle stage, and segmentation for personalized approach',
        parameters: {
          type: 'object',
          properties: {
            customer_id: {
              type: 'string',
              description: 'Customer identifier'
            },
            include_clv_calculation: {
              type: 'boolean',
              description: 'Include Customer Lifetime Value calculation'
            },
            segment_by_behavior: {
              type: 'boolean',
              description: 'Include behavioral segmentation analysis'
            }
          },
          required: ['customer_id']
        }
      },
      {
        name: 'schedule_follow_up',
        description: 'Schedule future touchpoints, demos, or check-ins based on customer preferences and reactivation strategy',
        parameters: {
          type: 'object',
          properties: {
            customer_id: {
              type: 'string',
              description: 'Customer identifier'
            },
            follow_up_type: {
              type: 'string',
              enum: ['phone_call', 'email_sequence', 'product_demo', 'check_in', 'offer_reminder'],
              description: 'Type of follow-up to schedule'
            },
            days_from_now: {
              type: 'integer',
              description: 'Number of days from today to schedule follow-up'
            },
            preferred_time: {
              type: 'string',
              description: 'Customer preferred contact time'
            },
            notes: {
              type: 'string',
              description: 'Notes about the conversation and next steps'
            }
          },
          required: ['customer_id', 'follow_up_type', 'days_from_now']
        }
      },
      {
        name: 'process_reactivation',
        description: 'Handle immediate customer reactivation, account restoration, and offer redemption',
        parameters: {
          type: 'object',
          properties: {
            customer_id: {
              type: 'string',
              description: 'Customer identifier'
            },
            reactivation_type: {
              type: 'string',
              enum: ['account_restoration', 'subscription_renewal', 'service_restart', 'plan_upgrade'],
              description: 'Type of reactivation to process'
            },
            offer_code: {
              type: 'string',
              description: 'Promotional offer code to apply'
            },
            billing_update_required: {
              type: 'boolean',
              description: 'Whether billing information needs updating'
            },
            immediate_access: {
              type: 'boolean',
              description: 'Whether to provide immediate access to services'
            }
          },
          required: ['customer_id', 'reactivation_type']
        }
      },
      {
        name: 'update_preferences',
        description: 'Update customer communication preferences, frequency settings, and contact information',
        parameters: {
          type: 'object',
          properties: {
            customer_id: {
              type: 'string',
              description: 'Customer identifier'
            },
            communication_frequency: {
              type: 'string',
              enum: ['weekly', 'monthly', 'quarterly', 'minimal'],
              description: 'Preferred communication frequency'
            },
            preferred_channels: {
              type: 'array',
              items: {
                type: 'string',
                enum: ['email', 'phone', 'sms', 'app_notification']
              },
              description: 'Preferred communication channels'
            },
            content_interests: {
              type: 'array',
              items: {
                type: 'string'
              },
              description: 'Topics and content types of interest'
            },
            opt_out_categories: {
              type: 'array',
              items: {
                type: 'string'
              },
              description: 'Communication categories to opt out of'
            }
          },
          required: ['customer_id']
        }
      },
      {
        name: 'escalate_to_retention_specialist',
        description: 'Transfer complex cases to human retention specialists with context and conversation history',
        parameters: {
          type: 'object',
          properties: {
            customer_id: {
              type: 'string',
              description: 'Customer identifier'
            },
            escalation_reason: {
              type: 'string',
              enum: ['complex_technical_issue', 'high_value_customer', 'legal_concerns', 'billing_dispute', 'custom_solution_needed'],
              description: 'Reason for escalation to human agent'
            },
            conversation_summary: {
              type: 'string',
              description: 'Summary of conversation and customer concerns'
            },
            customer_sentiment: {
              type: 'string',
              enum: ['positive', 'neutral', 'frustrated', 'angry'],
              description: 'Current customer sentiment'
            },
            urgency_level: {
              type: 'string',
              enum: ['low', 'medium', 'high', 'critical'],
              description: 'Urgency level for human follow-up'
            }
          },
          required: ['customer_id', 'escalation_reason', 'conversation_summary']
        }
      }
    ],

    endCallMessage: "Thank you so much for your time today. We're excited about the possibility of welcoming you back, and I'll make sure to follow up as promised. Have a wonderful day!",
    voicemailMessage: "Hi, this is [AGENT_NAME] from [COMPANY_NAME]. We've missed having you as a customer and have some exciting updates and special offers just for you. Please give me a call back when you have a moment. Thanks!",

    // Advanced analysis configuration
    analysisPlan: {
      summaryPlan: {
        enabled: true,
        messages: [
          {
            role: 'system',
            content: 'Summarize this customer reactivation call including: customer feedback about their experience, reasons for churn, their receptiveness to returning, offers presented, objections raised, and next steps agreed upon.'
          }
        ]
      },
      structuredDataPlan: {
        enabled: true,
        schema: {
          type: 'object',
          properties: {
            call_outcome: {
              type: 'string',
              enum: ['immediate_reactivation', 'follow_up_scheduled', 'not_interested', 'objections_raised', 'escalated_to_human']
            },
            churn_reasons_identified: {
              type: 'array',
              items: { type: 'string' }
            },
            customer_interest_level: {
              type: 'string',
              enum: ['high', 'medium', 'low', 'none']
            },
            offers_presented: {
              type: 'array',
              items: { type: 'string' }
            },
            objections_raised: {
              type: 'array',
              items: { type: 'string' }
            },
            next_action_required: {
              type: 'string'
            },
            reactivation_likelihood: {
              type: 'number',
              minimum: 0,
              maximum: 100
            }
          }
        }
      }
    }
  },

  // Comprehensive feature set
  features: [
    'AI Behavioral Analysis',
    'Churn Prediction Modeling',
    'Personalized Offer Generation',
    'Multi-Channel Win-Back Campaigns',
    'Real-time Sentiment Analysis',
    'Automated Follow-up Sequences',
    'Customer Value Segmentation',
    'Competitive Analysis Integration',
    'Success Rate Optimization',
    'Comprehensive Analytics Dashboard'
  ],

  // Integration ecosystem
  defaultIntegrations: [
    'vapi',
    'n8n',
    'crm',
    'email_marketing',
    'sms',
    'analytics',
    'billing',
    'support'
  ],

  // Success metrics and KPIs
  successMetrics: {
    reactivationRate: '25-45%',
    customerLifetimeValue: '40-60% increase',
    timeToReactivation: '7-14 days average',
    customerSatisfaction: '4.2+ rating',
    campaignROI: '300-500%'
  },

  // Compliance and best practices
  compliance: {
    dataPrivacy: 'GDPR/CCPA compliant data handling',
    communicationLaws: 'TCPA and CAN-SPAM compliance',
    optOutRespect: 'Immediate opt-out processing',
    consentManagement: 'Clear consent tracking and management'
  }
};

// Template-to-VAPI Deployment Functions
export const deployEnhancedCustomerReactivationToVAPI = async (apiConfig: {
  vapiApiKey: string;
  n8nApiKey: string;
  webhookBaseUrl: string;
}): Promise<TemplateVAPIDeploymentConfig> => {

  const deploymentConfig = TemplateToVAPIDeployment.generateVAPIAgentFromTemplate(
    ENHANCED_CUSTOMER_REACTIVATION_TEMPLATE,
    {
      deploymentSettings: {
        environment: 'production',
        autoStart: true,
        monitoring: {
          enabled: true,
          alerting: true,
          dashboardUrl: `/monitoring/customer-reactivation`
        },
        security: {
          encryption: true,
          auditLogging: true,
          accessControl: ['role_based', 'customer_success', 'retention_manager']
        }
      }
    }
  );

  return deploymentConfig;
};

export const validateCustomerReactivationCompliance = (config: any): {
  isCompliant: boolean;
  violations: string[];
  recommendations: string[];
} => {
  const violations: string[] = [];
  const recommendations: string[] = [];

  // GDPR/CCPA Compliance Checks
  if (!config.deploymentConfig?.complianceFrameworks?.includes('GDPR')) {
    violations.push('Missing GDPR compliance configuration');
  }

  if (!config.deploymentConfig?.complianceFrameworks?.includes('CCPA')) {
    violations.push('Missing CCPA compliance configuration');
  }

  // CAN-SPAM Compliance Checks
  if (!config.deploymentConfig?.complianceFrameworks?.includes('CAN-SPAM')) {
    violations.push('Missing CAN-SPAM compliance requirements');
  }

  // Customer Data Protection
  if (!config.deploymentConfig?.securityConfig?.accessControls?.includes('customer_data_protection')) {
    violations.push('Missing customer data protection measures');
  }

  // Opt-out mechanism check
  if (!config.functions?.find((f: any) => f.name === 'handle_opt_out_request')) {
    violations.push('Missing opt-out request handling capability');
  }

  // Recommendations
  if (violations.length === 0) {
    recommendations.push('All compliance requirements are met');
    recommendations.push('Consider implementing advanced churn prediction models');
    recommendations.push('Add A/B testing for different win-back offers');
  }

  return {
    isCompliant: violations.length === 0,
    violations,
    recommendations
  };
};

export default ENHANCED_CUSTOMER_REACTIVATION_TEMPLATE;