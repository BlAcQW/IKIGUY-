import type { ToolTemplate } from './types.js';

export const surveyTemplates: ToolTemplate[] = [
  {
    name: 'Administer Survey',
    description: 'Deliver structured surveys with intelligent branching logic',
    category: 'survey',
    type: 'FUNCTION',
    function: {
      name: 'administer_survey',
      description:
        'Deliver structured surveys with intelligent branching logic and adaptive questioning based on customer responses',
      parameters: {
        type: 'object',
        properties: {
          survey_type: {
            type: 'string',
            enum: [
              'customer_satisfaction', 'product_feedback', 'service_evaluation',
              'market_research', 'post_purchase', 'net_promoter_score', 'brand_perception',
            ],
          },
          survey_questions: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                question_id: { type: 'string' },
                question_text: { type: 'string' },
                question_type: {
                  type: 'string',
                  enum: ['multiple_choice', 'rating_scale', 'open_ended', 'yes_no', 'ranking'],
                },
                options: { type: 'array', items: { type: 'string' } },
                required: { type: 'boolean' },
                branching_logic: { type: 'string' },
              },
            },
          },
          estimated_duration: { type: 'integer' },
          survey_topic: { type: 'string' },
          anonymity_level: {
            type: 'string',
            enum: ['fully_anonymous', 'confidential', 'attributed'],
          },
        },
        required: ['survey_type', 'survey_questions', 'survey_topic'],
      },
    },
  },
  {
    name: 'Collect Feedback Response',
    description: 'Capture and validate customer responses with data quality checks',
    category: 'survey',
    type: 'FUNCTION',
    function: {
      name: 'collect_feedback_response',
      description:
        'Capture and validate customer responses with real-time data quality checks and response categorization',
      parameters: {
        type: 'object',
        properties: {
          question_id: { type: 'string' },
          response_data: {
            type: 'object',
            properties: {
              response_text: { type: 'string' },
              response_value: { type: 'string' },
              response_scale: { type: 'integer' },
              response_category: { type: 'string' },
            },
          },
          response_confidence: {
            type: 'string',
            enum: ['very_confident', 'confident', 'somewhat_confident', 'uncertain'],
          },
          response_completeness: {
            type: 'string',
            enum: ['complete', 'partial', 'unclear', 'refused'],
          },
          follow_up_needed: { type: 'boolean' },
          response_sentiment: {
            type: 'string',
            enum: ['very_positive', 'positive', 'neutral', 'negative', 'very_negative'],
          },
          additional_context: { type: 'string' },
        },
        required: ['question_id', 'response_data'],
      },
    },
  },
  {
    name: 'Analyze Response Sentiment',
    description: 'Perform real-time sentiment analysis of customer feedback responses',
    category: 'survey',
    type: 'FUNCTION',
    function: {
      name: 'analyze_response_sentiment',
      description:
        'Perform real-time sentiment analysis and emotional assessment of customer feedback responses',
      parameters: {
        type: 'object',
        properties: {
          response_text: { type: 'string' },
          analysis_depth: { type: 'string', enum: ['basic', 'detailed', 'comprehensive'] },
          emotional_indicators: {
            type: 'array',
            items: {
              type: 'string',
              enum: [
                'satisfaction', 'frustration', 'excitement', 'disappointment',
                'confusion', 'appreciation', 'anger', 'loyalty',
              ],
            },
          },
          sentiment_confidence: { type: 'number', minimum: 0, maximum: 1 },
          action_triggers: { type: 'array', items: { type: 'string' } },
        },
        required: ['response_text'],
      },
    },
  },
  {
    name: 'Schedule Follow-Up Survey',
    description: 'Plan and schedule additional surveys based on initial feedback responses',
    category: 'survey',
    type: 'FUNCTION',
    function: {
      name: 'schedule_follow_up_survey',
      description:
        'Plan and schedule additional surveys or in-depth interviews based on initial feedback responses',
      parameters: {
        type: 'object',
        properties: {
          follow_up_type: {
            type: 'string',
            enum: ['detailed_interview', 'product_specific_survey', 'satisfaction_tracking', 'complaint_resolution', 'loyalty_assessment'],
          },
          follow_up_reason: { type: 'string' },
          scheduling_preferences: {
            type: 'object',
            properties: {
              preferred_timeframe: { type: 'string' },
              preferred_method: {
                type: 'string',
                enum: ['phone_call', 'video_interview', 'email_survey', 'in_person_meeting'],
              },
              duration_estimate: { type: 'integer' },
            },
          },
          priority_level: { type: 'string', enum: ['low', 'medium', 'high', 'urgent'] },
          specific_topics: { type: 'array', items: { type: 'string' } },
        },
        required: ['follow_up_type', 'follow_up_reason'],
      },
    },
  },
  {
    name: 'Process Survey Incentive',
    description: 'Handle survey completion rewards and incentive distribution',
    category: 'survey',
    type: 'FUNCTION',
    function: {
      name: 'process_survey_incentive',
      description:
        'Handle survey completion rewards, compensation processing, and incentive distribution to participants',
      parameters: {
        type: 'object',
        properties: {
          incentive_type: {
            type: 'string',
            enum: ['cash_payment', 'gift_card', 'discount_code', 'product_sample', 'loyalty_points', 'charity_donation'],
          },
          incentive_value: { type: 'number' },
          delivery_method: {
            type: 'string',
            enum: ['email', 'sms', 'postal_mail', 'digital_wallet', 'account_credit', 'immediate_processing'],
          },
          customer_id: { type: 'string' },
          survey_completed: { type: 'boolean' },
          quality_threshold_met: { type: 'boolean' },
          processing_timeline: {
            type: 'string',
            enum: ['immediate', '24_hours', '3_business_days', '1_week', '2_weeks'],
          },
        },
        required: ['incentive_type', 'delivery_method'],
      },
    },
  },
  {
    name: 'Escalate Customer Concern',
    description: 'Address and escalate complaints or issues raised during feedback collection',
    category: 'survey',
    type: 'FUNCTION',
    function: {
      name: 'escalate_customer_concern',
      description:
        'Address and escalate customer complaints, concerns, or issues raised during feedback collection sessions',
      parameters: {
        type: 'object',
        properties: {
          concern_type: {
            type: 'string',
            enum: [
              'product_defect', 'service_complaint', 'billing_issue',
              'privacy_concern', 'accessibility_problem', 'staff_behavior', 'policy_disagreement',
            ],
          },
          concern_severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
          description: { type: 'string' },
          escalation_path: {
            type: 'string',
            enum: ['customer_service', 'technical_support', 'management', 'legal_department', 'quality_assurance'],
          },
          immediate_action_needed: { type: 'boolean' },
          follow_up_requirements: { type: 'string' },
        },
        required: ['concern_type', 'concern_severity', 'escalation_path'],
      },
    },
  },
  {
    name: 'Generate Feedback Summary',
    description: 'Create real-time summaries and insights from collected customer feedback',
    category: 'survey',
    type: 'FUNCTION',
    function: {
      name: 'generate_feedback_summary',
      description:
        'Create real-time summaries and insights from collected customer feedback for immediate analysis',
      parameters: {
        type: 'object',
        properties: {
          summary_scope: {
            type: 'string',
            enum: ['individual_response', 'session_summary', 'daily_insights', 'campaign_overview'],
          },
          satisfaction_scores: { type: 'array', items: { type: 'number' } },
          common_themes: { type: 'array', items: { type: 'string' } },
          positive_feedback: { type: 'array', items: { type: 'string' } },
          areas_for_improvement: { type: 'array', items: { type: 'string' } },
          customer_suggestions: { type: 'array', items: { type: 'string' } },
        },
        required: ['summary_scope'],
      },
    },
  },
];
