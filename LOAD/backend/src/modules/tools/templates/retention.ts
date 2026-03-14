import type { ToolTemplate } from './types.js';

export const retentionTemplates: ToolTemplate[] = [
  {
    name: 'Analyze Customer Behavior',
    description: 'Analyze customer history, purchase patterns, and behavioral signals',
    category: 'retention',
    type: 'FUNCTION',
    function: {
      name: 'analyze_customer_behavior',
      description:
        'Analyze customer history, purchase patterns, engagement data, and behavioral signals to understand their relationship with the company',
      parameters: {
        type: 'object',
        properties: {
          customer_id: { type: 'string' },
          include_purchase_history: { type: 'boolean' },
          analyze_engagement_patterns: { type: 'boolean' },
          time_period_months: { type: 'integer' },
        },
        required: ['customer_id'],
      },
    },
  },
  {
    name: 'Identify Churn Reasons',
    description: 'Determine likely reasons for customer churn using AI analysis',
    category: 'retention',
    type: 'FUNCTION',
    function: {
      name: 'identify_churn_reasons',
      description:
        'Determine likely reasons for customer churn using AI analysis of behavior patterns, support tickets, and engagement data',
      parameters: {
        type: 'object',
        properties: {
          customer_id: { type: 'string' },
          include_support_history: { type: 'boolean' },
          analyze_competitor_activity: { type: 'boolean' },
        },
        required: ['customer_id'],
      },
    },
  },
  {
    name: 'Generate Personalized Offer',
    description: 'Create customized win-back offers based on customer value and churn reasons',
    category: 'retention',
    type: 'FUNCTION',
    function: {
      name: 'generate_personalized_offer',
      description:
        'Create customized win-back offers based on customer value, preferences, and churn reasons',
      parameters: {
        type: 'object',
        properties: {
          customer_id: { type: 'string' },
          customer_value_tier: {
            type: 'string',
            enum: ['high_value', 'medium_value', 'standard'],
          },
          churn_reason: {
            type: 'string',
            enum: ['price_sensitivity', 'feature_gaps', 'poor_experience', 'competitor_switch', 'lack_of_engagement', 'life_changes'],
          },
          preferred_offer_type: {
            type: 'string',
            enum: ['discount', 'free_trial', 'bonus_features', 'personal_onboarding', 'account_credit'],
          },
        },
        required: ['customer_id', 'customer_value_tier'],
      },
    },
  },
  {
    name: 'Check Customer Segment',
    description: 'Determine customer value tier, lifecycle stage, and segmentation',
    category: 'retention',
    type: 'FUNCTION',
    function: {
      name: 'check_customer_segment',
      description:
        'Determine customer value tier, lifecycle stage, and segmentation for personalized approach',
      parameters: {
        type: 'object',
        properties: {
          customer_id: { type: 'string' },
          include_clv_calculation: { type: 'boolean' },
          segment_by_behavior: { type: 'boolean' },
        },
        required: ['customer_id'],
      },
    },
  },
  {
    name: 'Process Reactivation',
    description: 'Handle customer reactivation, account restoration, and offer redemption',
    category: 'retention',
    type: 'FUNCTION',
    function: {
      name: 'process_reactivation',
      description:
        'Handle immediate customer reactivation, account restoration, and offer redemption',
      parameters: {
        type: 'object',
        properties: {
          customer_id: { type: 'string' },
          reactivation_type: {
            type: 'string',
            enum: ['account_restoration', 'subscription_renewal', 'service_restart', 'plan_upgrade'],
          },
          offer_code: { type: 'string' },
          billing_update_required: { type: 'boolean' },
          immediate_access: { type: 'boolean' },
        },
        required: ['customer_id', 'reactivation_type'],
      },
    },
  },
  {
    name: 'Update Customer Preferences',
    description: 'Update communication preferences, frequency settings, and contact information',
    category: 'retention',
    type: 'FUNCTION',
    function: {
      name: 'update_preferences',
      description:
        'Update customer communication preferences, frequency settings, and contact information',
      parameters: {
        type: 'object',
        properties: {
          customer_id: { type: 'string' },
          communication_frequency: {
            type: 'string',
            enum: ['weekly', 'monthly', 'quarterly', 'minimal'],
          },
          preferred_channels: {
            type: 'array',
            items: { type: 'string', enum: ['email', 'phone', 'sms', 'app_notification'] },
          },
          content_interests: { type: 'array', items: { type: 'string' } },
          opt_out_categories: { type: 'array', items: { type: 'string' } },
        },
        required: ['customer_id'],
      },
    },
  },
  {
    name: 'Escalate to Retention Specialist',
    description: 'Transfer complex cases to human retention specialists with context',
    category: 'retention',
    type: 'FUNCTION',
    function: {
      name: 'escalate_to_retention_specialist',
      description:
        'Transfer complex cases to human retention specialists with context and conversation history',
      parameters: {
        type: 'object',
        properties: {
          customer_id: { type: 'string' },
          escalation_reason: {
            type: 'string',
            enum: ['complex_technical_issue', 'high_value_customer', 'legal_concerns', 'billing_dispute', 'custom_solution_needed'],
          },
          conversation_summary: { type: 'string' },
          customer_sentiment: {
            type: 'string',
            enum: ['positive', 'neutral', 'frustrated', 'angry'],
          },
          urgency_level: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
        },
        required: ['customer_id', 'escalation_reason', 'conversation_summary'],
      },
    },
  },
];
