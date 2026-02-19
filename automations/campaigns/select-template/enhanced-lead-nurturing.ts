/**
 * Enhanced Lead Nurturing Template with VAPI + N8N Integration
 *
 * AI-powered lead nurturing campaign featuring behavioral scoring, personalized voice outreach,
 * conversion optimization, multi-touch sequences, and comprehensive sales analytics.
 */

import { TemplateToVAPIDeployment, TemplateVAPIDeploymentConfig } from './template-to-vapi-deployment';

export const ENHANCED_LEAD_NURTURING_TEMPLATE = {
  id: 'enhanced_lead_nurturing_vapi_n8n',
  name: 'Enhanced Lead Nurturing with VAPI + n8n',
  description: 'AI-powered lead nurturing and conversion campaign featuring behavioral scoring, personalized voice calls, intelligent follow-up sequences, conversion optimization, and comprehensive sales funnel analytics',
  industry: 'sales',
  category: 'Sales',
  complexity: 'Advanced' as const,
  estimatedTime: '35 min setup, 2-4 weeks campaign',
  rating: 4.9,
  usageCount: 18750,
  popular: true,
  integrationCategories: ['AI Voice Agent', 'Sales Automation', 'CRM Integration', 'Analytics'],

  // Template-to-VAPI Deployment Configuration
  deploymentConfig: {
    enableAutoDeployment: true,
    useVAPIAgentWizard: true,
    complianceFrameworks: ['CAN-SPAM', 'TCPA', 'GDPR'],
    securityConfig: {
      accessControls: ['role_based', 'sales_data_protection'],
      dataRetention: '3_years',
      sensitiveDataHandling: 'encrypted'
    }
  } as const,

  // VAPI Configuration with specialized lead nurturing functions
  vapiConfig: {
    assistantId: 'asst_lead_nurturing_enhanced',
    name: 'Lead Nurturing AI Assistant',
    model: {
      provider: 'openai',
      model: 'gpt-4o',
      temperature: 0.3,
      maxTokens: 350
    },
    voice: {
      provider: '11labs',
      voiceId: 'pNInz6obpgDQGcFmaJgB',  // Professional, trustworthy voice
      stability: 0.7,
      similarityBoost: 0.8,
      style: 0.2,
      useSpeakerBoost: true
    },
    firstMessage: "Hi {{lead_name}}! I'm calling from {{company_name}} regarding your recent interest in {{lead_source}}. I'd love to learn more about your needs and see how we can help you achieve your goals. Do you have a few minutes to chat?",
    systemPrompt: `You are a professional sales development representative for {{company_name}}. Your goal is to nurture leads through the sales funnel by building relationships, understanding needs, and guiding them toward conversion.

## Your Approach:
- Be consultative and value-focused, not pushy
- Ask thoughtful discovery questions to understand their business needs
- Listen actively and take detailed notes about their challenges
- Provide relevant insights and solutions based on their specific situation
- Build trust through expertise and genuine interest in their success
- Guide them naturally toward the next step in the sales process

## Key Responsibilities:
1. **Lead Qualification**: Assess fit, budget, authority, and timeline
2. **Need Discovery**: Uncover pain points, goals, and decision criteria
3. **Value Communication**: Articulate relevant benefits and ROI
4. **Objection Handling**: Address concerns and misconceptions professionally
5. **Next Step Guidance**: Move qualified leads forward in the sales process
6. **Relationship Building**: Establish trust and ongoing communication

## Available Tools:
- **score_lead_behavior**: Analyze lead engagement and behavioral signals
- **assess_lead_qualification**: Evaluate BANT criteria and sales readiness
- **track_lead_interaction**: Log conversation details and outcomes
- **schedule_follow_up**: Book demos, meetings, or next conversations
- **send_lead_content**: Share relevant resources and materials
- **update_lead_status**: Progress leads through sales stages
- **create_lead_task**: Set reminders and action items for sales team
- **escalate_to_sales**: Transfer qualified leads to account executives

Always maintain a helpful, professional tone while focusing on understanding their needs and providing value.`,

    functions: [
      {
        name: 'score_lead_behavior',
        description: 'Analyze lead engagement patterns, website activity, email interactions, and behavioral signals to calculate lead score and buying intent',
        parameters: {
          type: 'object',
          properties: {
            lead_id: {
              type: 'string',
              description: 'Unique lead identifier'
            },
            include_website_activity: {
              type: 'boolean',
              description: 'Include website visit tracking and page views'
            },
            include_email_engagement: {
              type: 'boolean',
              description: 'Include email opens, clicks, and response patterns'
            },
            include_social_signals: {
              type: 'boolean',
              description: 'Include social media engagement and company signals'
            },
            time_period_days: {
              type: 'integer',
              description: 'Number of days to analyze (default: 30)'
            }
          },
          required: ['lead_id']
        }
      },
      {
        name: 'assess_lead_qualification',
        description: 'Evaluate lead qualification using BANT criteria (Budget, Authority, Need, Timeline) and sales readiness scoring',
        parameters: {
          type: 'object',
          properties: {
            lead_id: {
              type: 'string',
              description: 'Lead identifier'
            },
            budget_range: {
              type: 'string',
              enum: ['under_1k', '1k_10k', '10k_50k', '50k_plus', 'unknown'],
              description: 'Estimated budget range for solution'
            },
            decision_authority: {
              type: 'string',
              enum: ['decision_maker', 'influencer', 'end_user', 'gatekeeper', 'unknown'],
              description: 'Level of decision-making authority'
            },
            business_need: {
              type: 'string',
              enum: ['urgent', 'high', 'medium', 'low', 'unclear'],
              description: 'Urgency and clarity of business need'
            },
            purchase_timeline: {
              type: 'string',
              enum: ['immediate', '30_days', '90_days', '6_months', 'no_timeline'],
              description: 'Expected purchase or decision timeline'
            },
            pain_points: {
              type: 'array',
              items: { type: 'string' },
              description: 'Identified business pain points and challenges'
            }
          },
          required: ['lead_id']
        }
      },
      {
        name: 'track_lead_interaction',
        description: 'Log conversation details, outcomes, and key insights from lead interactions for CRM and follow-up purposes',
        parameters: {
          type: 'object',
          properties: {
            lead_id: {
              type: 'string',
              description: 'Lead identifier'
            },
            interaction_type: {
              type: 'string',
              enum: ['phone_call', 'email', 'demo', 'meeting', 'follow_up'],
              description: 'Type of interaction'
            },
            conversation_summary: {
              type: 'string',
              description: 'Summary of conversation topics and outcomes'
            },
            lead_sentiment: {
              type: 'string',
              enum: ['very_interested', 'interested', 'neutral', 'skeptical', 'not_interested'],
              description: 'Lead interest level and sentiment'
            },
            objections_raised: {
              type: 'array',
              items: { type: 'string' },
              description: 'Any objections or concerns mentioned'
            },
            next_steps_discussed: {
              type: 'string',
              description: 'Agreed upon next steps or actions'
            },
            lead_temperature: {
              type: 'string',
              enum: ['hot', 'warm', 'cold'],
              description: 'Overall lead temperature assessment'
            }
          },
          required: ['lead_id', 'interaction_type', 'conversation_summary']
        }
      },
      {
        name: 'schedule_follow_up',
        description: 'Schedule demos, meetings, or follow-up conversations based on lead preferences and sales process requirements',
        parameters: {
          type: 'object',
          properties: {
            lead_id: {
              type: 'string',
              description: 'Lead identifier'
            },
            follow_up_type: {
              type: 'string',
              enum: ['product_demo', 'discovery_call', 'proposal_meeting', 'check_in', 'decision_call'],
              description: 'Type of follow-up to schedule'
            },
            preferred_date: {
              type: 'string',
              description: 'Lead preferred date for follow-up'
            },
            preferred_time: {
              type: 'string',
              description: 'Lead preferred time of day'
            },
            duration_minutes: {
              type: 'integer',
              description: 'Expected duration of follow-up (default: 30)'
            },
            meeting_objectives: {
              type: 'string',
              description: 'Goals and objectives for the follow-up meeting'
            },
            attendees: {
              type: 'array',
              items: { type: 'string' },
              description: 'Additional attendees from lead side'
            }
          },
          required: ['lead_id', 'follow_up_type']
        }
      },
      {
        name: 'send_lead_content',
        description: 'Share relevant resources, case studies, whitepapers, or materials based on lead interests and stage',
        parameters: {
          type: 'object',
          properties: {
            lead_id: {
              type: 'string',
              description: 'Lead identifier'
            },
            content_type: {
              type: 'string',
              enum: ['case_study', 'whitepaper', 'product_demo', 'pricing_info', 'roi_calculator', 'comparison_guide'],
              description: 'Type of content to send'
            },
            industry_specific: {
              type: 'boolean',
              description: 'Send industry-specific content if available'
            },
            use_case_focus: {
              type: 'string',
              description: 'Specific use case or business challenge to focus on'
            },
            delivery_method: {
              type: 'string',
              enum: ['email', 'portal_access', 'calendar_invite', 'direct_link'],
              description: 'How to deliver the content'
            },
            personalized_message: {
              type: 'string',
              description: 'Personalized message to accompany the content'
            }
          },
          required: ['lead_id', 'content_type']
        }
      },
      {
        name: 'update_lead_status',
        description: 'Progress leads through sales stages and update CRM status based on qualification and readiness',
        parameters: {
          type: 'object',
          properties: {
            lead_id: {
              type: 'string',
              description: 'Lead identifier'
            },
            new_stage: {
              type: 'string',
              enum: ['new_lead', 'contacted', 'qualified', 'demo_scheduled', 'proposal_sent', 'negotiation', 'closed_won', 'closed_lost'],
              description: 'New sales stage for the lead'
            },
            stage_reason: {
              type: 'string',
              description: 'Reason for stage change'
            },
            lead_score_update: {
              type: 'integer',
              description: 'Updated lead score (0-100)'
            },
            priority_level: {
              type: 'string',
              enum: ['high', 'medium', 'low'],
              description: 'Priority level for follow-up'
            },
            sales_notes: {
              type: 'string',
              description: 'Additional notes for sales team'
            }
          },
          required: ['lead_id', 'new_stage']
        }
      },
      {
        name: 'create_lead_task',
        description: 'Create tasks, reminders, and action items for sales team follow-up and lead management',
        parameters: {
          type: 'object',
          properties: {
            lead_id: {
              type: 'string',
              description: 'Lead identifier'
            },
            task_type: {
              type: 'string',
              enum: ['follow_up_call', 'send_proposal', 'schedule_demo', 'send_contract', 'check_decision_status'],
              description: 'Type of task to create'
            },
            assigned_to: {
              type: 'string',
              description: 'Sales team member to assign task to'
            },
            due_date: {
              type: 'string',
              description: 'Task due date'
            },
            priority: {
              type: 'string',
              enum: ['urgent', 'high', 'normal', 'low'],
              description: 'Task priority level'
            },
            task_description: {
              type: 'string',
              description: 'Detailed task description and context'
            },
            related_opportunity: {
              type: 'string',
              description: 'Related opportunity or deal ID'
            }
          },
          required: ['lead_id', 'task_type', 'task_description']
        }
      },
      {
        name: 'escalate_to_sales',
        description: 'Transfer qualified leads to account executives with complete context and qualification details',
        parameters: {
          type: 'object',
          properties: {
            lead_id: {
              type: 'string',
              description: 'Lead identifier'
            },
            sales_rep_id: {
              type: 'string',
              description: 'Assigned sales representative ID'
            },
            qualification_summary: {
              type: 'string',
              description: 'Summary of lead qualification and readiness'
            },
            deal_size_estimate: {
              type: 'number',
              description: 'Estimated deal size or annual contract value'
            },
            close_probability: {
              type: 'number',
              description: 'Estimated probability of closing (0-100%)'
            },
            key_stakeholders: {
              type: 'array',
              items: { type: 'string' },
              description: 'Key decision makers and influencers identified'
            },
            recommended_next_steps: {
              type: 'string',
              description: 'Recommended approach and next steps for AE'
            },
            urgency_level: {
              type: 'string',
              enum: ['immediate', 'high', 'normal'],
              description: 'Urgency for sales follow-up'
            }
          },
          required: ['lead_id', 'qualification_summary']
        }
      }
    ],

    endCallMessage: "Thank you for your time today! I'm excited about the opportunity to help {{company_name}} achieve its goals. I'll follow up with the information we discussed and look forward to our next conversation.",
    voicemailMessage: "Hi {{lead_name}}, this is {{agent_name}} from {{company_name}}. I'm following up on your interest in {{lead_source}}. I have some valuable insights that could help with {{pain_point}}. Please give me a call back when you have a moment. Thanks!",

    // Advanced analysis configuration
    analysisPlan: {
      summaryPlan: {
        enabled: true,
        messages: [
          {
            role: 'system',
            content: 'Summarize this lead nurturing call including: lead qualification level, identified needs and pain points, interest level and buying signals, objections or concerns raised, next steps agreed upon, and overall sales potential assessment.'
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
              enum: ['qualified_lead', 'demo_scheduled', 'follow_up_needed', 'not_qualified', 'no_interest']
            },
            lead_qualification_score: {
              type: 'number',
              minimum: 0,
              maximum: 100
            },
            buying_signals_identified: {
              type: 'array',
              items: { type: 'string' }
            },
            pain_points_discovered: {
              type: 'array',
              items: { type: 'string' }
            },
            objections_raised: {
              type: 'array',
              items: { type: 'string' }
            },
            decision_timeline: {
              type: 'string',
              enum: ['immediate', '30_days', '90_days', '6_months', 'unclear']
            },
            budget_indication: {
              type: 'string',
              enum: ['confirmed', 'estimated', 'unclear']
            },
            next_action_required: {
              type: 'string'
            },
            conversion_probability: {
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
    'AI Behavioral Scoring',
    'Lead Qualification Automation',
    'Personalized Voice Outreach',
    'Multi-Touch Nurture Sequences',
    'Real-time Conversion Tracking',
    'Sales Funnel Analytics',
    'CRM Integration & Updates',
    'Automated Follow-up Scheduling',
    'Content Delivery System',
    'Sales Team Collaboration'
  ],

  // Integration ecosystem
  defaultIntegrations: [
    'vapi',
    'n8n',
    'crm',
    'email_marketing',
    'calendar',
    'analytics',
    'content_management',
    'lead_scoring'
  ],

  // Success metrics and KPIs
  successMetrics: {
    leadQualificationRate: '65-85%',
    conversionToDemo: '35-55%',
    salesCycleReduction: '25-40%',
    leadResponseRate: '70-90%',
    campaignROI: '400-700%'
  },

  // Compliance and best practices
  compliance: {
    dataPrivacy: 'GDPR/CCPA compliant lead data handling',
    communicationLaws: 'TCPA and CAN-SPAM compliance',
    optOutRespect: 'Immediate opt-out processing and DNC list updates',
    consentManagement: 'Clear consent tracking and preference management'
  }
};

// Template-to-VAPI Deployment Functions
export const deployEnhancedLeadNurturingToVAPI = async (apiConfig: {
  vapiApiKey: string;
  n8nApiKey: string;
  webhookBaseUrl: string;
}): Promise<TemplateVAPIDeploymentConfig> => {

  const deploymentConfig = TemplateToVAPIDeployment.generateVAPIAgentFromTemplate(
    ENHANCED_LEAD_NURTURING_TEMPLATE,
    {
      deploymentSettings: {
        environment: 'production',
        autoStart: true,
        monitoring: {
          enabled: true,
          alerting: true,
          dashboardUrl: `/monitoring/lead-nurturing`
        },
        security: {
          encryption: true,
          auditLogging: true,
          accessControl: ['role_based', 'sales_manager', 'lead_specialist']
        }
      }
    }
  );

  return deploymentConfig;
};

export const validateLeadNurturingCompliance = (config: any): {
  isCompliant: boolean;
  violations: string[];
  recommendations: string[];
} => {
  const violations: string[] = [];
  const recommendations: string[] = [];

  // CAN-SPAM Compliance Checks
  if (!config.deploymentConfig?.complianceFrameworks?.includes('CAN-SPAM')) {
    violations.push('Missing CAN-SPAM compliance configuration');
  }

  // TCPA Compliance Checks
  if (!config.deploymentConfig?.complianceFrameworks?.includes('TCPA')) {
    violations.push('Missing TCPA compliance requirements');
  }

  // GDPR Compliance Checks
  if (!config.deploymentConfig?.complianceFrameworks?.includes('GDPR')) {
    violations.push('Missing GDPR compliance configuration');
  }

  // Lead Scoring Function Check
  if (!config.functions?.find((f: any) => f.name === 'score_lead_behavior')) {
    violations.push('Missing lead behavioral scoring capability');
  }

  // Lead Qualification Check
  if (!config.functions?.find((f: any) => f.name === 'assess_lead_qualification')) {
    violations.push('Missing lead qualification assessment');
  }

  // Recommendations
  if (violations.length === 0) {
    recommendations.push('All compliance requirements are met');
    recommendations.push('Consider implementing predictive lead scoring');
    recommendations.push('Add multi-channel nurturing sequences');
  }

  return {
    isCompliant: violations.length === 0,
    violations,
    recommendations
  };
};

export default ENHANCED_LEAD_NURTURING_TEMPLATE;