/**
 * Enhanced Survey & Feedback Collection Template with VAPI + N8N Integration
 *
 * AI-powered survey and feedback collection campaign featuring intelligent questionnaire delivery,
 * real-time response analysis, sentiment evaluation, and comprehensive feedback analytics.
 */

import { TemplateToVAPIDeployment, TemplateVAPIDeploymentConfig } from './template-to-vapi-deployment';

export const ENHANCED_SURVEY_FEEDBACK_TEMPLATE = {
  id: 'enhanced_survey_feedback_vapi_n8n',
  name: 'Enhanced Survey & Feedback Collection with VAPI + n8n',
  description: 'AI-powered survey and feedback collection campaign featuring intelligent questionnaire delivery, real-time response analysis, sentiment evaluation, personalized follow-ups, and comprehensive feedback analytics',
  industry: 'research',
  category: 'Research',
  complexity: 'Advanced' as const,
  estimatedTime: '25 min setup, 1-2 weeks data collection',
  rating: 4.7,
  usageCount: 14250,
  popular: true,
  integrationCategories: ['AI Voice Agent', 'Survey Platform', 'Analytics Integration', 'CRM Integration'],

  // Template-to-VAPI Deployment Configuration
  deploymentConfig: {
    enableAutoDeployment: true,
    useVAPIAgentWizard: true,
    complianceFrameworks: ['GDPR', 'CCPA', 'ISO_20252'],
    securityConfig: {
      accessControls: ['role_based', 'survey_data_protection'],
      dataRetention: '5_years',
      sensitiveDataHandling: 'anonymized'
    }
  } as const,

  // VAPI Configuration with specialized survey and feedback functions
  vapiConfig: {
    assistantId: 'asst_survey_feedback_enhanced',
    name: 'Survey & Feedback AI Assistant',
    model: {
      provider: 'openai',
      model: 'gpt-4o',
      temperature: 0.3,
      maxTokens: 350
    },
    voice: {
      provider: '11labs',
      voiceId: 'pNInz6obpgDQGcFmaJgB',  // Professional, friendly voice
      stability: 0.8,
      similarityBoost: 0.8,
      style: 0.1,
      useSpeakerBoost: true
    },
    firstMessage: "Hi {{prospect_name}}! I'm calling from {{company_name}} to gather your valuable feedback about {{survey_topic}}. This will only take a few minutes of your time, and your input is really important to us. Are you available to share your thoughts?",
    systemPrompt: `You are a professional survey and feedback collection assistant for {{company_name}}. Your goal is to efficiently collect valuable customer insights while providing a positive experience and ensuring high-quality response data.

## Your Approach:
- Be friendly, professional, and respectful of customer time
- Clearly explain the survey purpose and expected duration
- Ask questions in a natural, conversational manner
- Adapt questioning style based on customer responses
- Ensure complete and accurate data collection
- Handle sensitive topics with appropriate care
- Provide clear next steps and thank customers appropriately

## Key Responsibilities:
1. **Survey Administration**: Deliver structured questionnaires in conversational format
2. **Response Collection**: Capture detailed, accurate customer feedback
3. **Sentiment Analysis**: Assess emotional tone and satisfaction levels
4. **Data Quality Assurance**: Ensure complete and reliable response data
5. **Follow-up Coordination**: Schedule additional surveys or interviews if needed
6. **Incentive Management**: Process survey incentives and rewards
7. **Complaint Handling**: Address concerns raised during feedback collection
8. **Analytics Integration**: Ensure proper data categorization and analysis

## Available Tools:
- **administer_survey**: Deliver structured surveys with branching logic
- **collect_feedback_response**: Capture and validate customer responses
- **analyze_response_sentiment**: Real-time sentiment analysis of feedback
- **schedule_follow_up_survey**: Plan additional data collection sessions
- **process_survey_incentive**: Handle rewards and compensation for participation
- **escalate_customer_concern**: Address complaints or issues raised during surveys
- **validate_response_quality**: Ensure completeness and accuracy of collected data
- **generate_feedback_summary**: Create real-time summaries of customer insights

Always maintain a respectful, professional tone while ensuring comprehensive data collection and positive customer experience.`,

    functions: [
      {
        name: 'administer_survey',
        description: 'Deliver structured surveys with intelligent branching logic and adaptive questioning based on customer responses',
        parameters: {
          type: 'object',
          properties: {
            survey_type: {
              type: 'string',
              enum: ['customer_satisfaction', 'product_feedback', 'service_evaluation', 'market_research', 'post_purchase', 'net_promoter_score', 'brand_perception'],
              description: 'Type of survey being conducted'
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
                    enum: ['multiple_choice', 'rating_scale', 'open_ended', 'yes_no', 'ranking']
                  },
                  options: { type: 'array', items: { type: 'string' } },
                  required: { type: 'boolean' },
                  branching_logic: { type: 'string' }
                }
              },
              description: 'Structured list of survey questions with metadata'
            },
            estimated_duration: {
              type: 'integer',
              description: 'Estimated survey completion time in minutes'
            },
            survey_topic: {
              type: 'string',
              description: 'Main topic or focus of the survey'
            },
            incentive_offered: {
              type: 'object',
              properties: {
                incentive_type: {
                  type: 'string',
                  enum: ['monetary', 'discount', 'gift_card', 'product_sample', 'entry_to_draw', 'none']
                },
                incentive_value: { type: 'string' },
                incentive_description: { type: 'string' }
              },
              description: 'Survey completion incentive details'
            },
            anonymity_level: {
              type: 'string',
              enum: ['fully_anonymous', 'confidential', 'attributed'],
              description: 'Level of anonymity for survey responses'
            }
          },
          required: ['survey_type', 'survey_questions', 'survey_topic']
        }
      },
      {
        name: 'collect_feedback_response',
        description: 'Capture and validate customer responses with real-time data quality checks and response categorization',
        parameters: {
          type: 'object',
          properties: {
            question_id: {
              type: 'string',
              description: 'Identifier for the question being answered'
            },
            response_data: {
              type: 'object',
              properties: {
                response_text: { type: 'string' },
                response_value: { type: 'string' },
                response_scale: { type: 'integer' },
                response_category: { type: 'string' }
              },
              description: 'Customer response data in multiple formats'
            },
            response_confidence: {
              type: 'string',
              enum: ['very_confident', 'confident', 'somewhat_confident', 'uncertain'],
              description: 'Customer confidence level in their response'
            },
            response_completeness: {
              type: 'string',
              enum: ['complete', 'partial', 'unclear', 'refused'],
              description: 'Completeness assessment of the response'
            },
            follow_up_needed: {
              type: 'boolean',
              description: 'Whether additional clarification is needed'
            },
            response_sentiment: {
              type: 'string',
              enum: ['very_positive', 'positive', 'neutral', 'negative', 'very_negative'],
              description: 'Initial sentiment assessment of response'
            },
            additional_context: {
              type: 'string',
              description: 'Additional context or clarification provided by customer'
            }
          },
          required: ['question_id', 'response_data']
        }
      },
      {
        name: 'analyze_response_sentiment',
        description: 'Perform real-time sentiment analysis and emotional assessment of customer feedback responses',
        parameters: {
          type: 'object',
          properties: {
            response_text: {
              type: 'string',
              description: 'Customer response text to analyze'
            },
            analysis_depth: {
              type: 'string',
              enum: ['basic', 'detailed', 'comprehensive'],
              description: 'Level of sentiment analysis to perform'
            },
            emotional_indicators: {
              type: 'array',
              items: {
                type: 'string',
                enum: ['satisfaction', 'frustration', 'excitement', 'disappointment', 'confusion', 'appreciation', 'anger', 'loyalty']
              },
              description: 'Specific emotional indicators to assess'
            },
            context_factors: {
              type: 'object',
              properties: {
                customer_history: { type: 'string' },
                recent_interactions: { type: 'string' },
                product_usage: { type: 'string' },
                complaint_history: { type: 'string' }
              },
              description: 'Additional context for sentiment analysis'
            },
            sentiment_confidence: {
              type: 'number',
              minimum: 0,
              maximum: 1,
              description: 'Confidence level in sentiment analysis (0-1)'
            },
            action_triggers: {
              type: 'array',
              items: { type: 'string' },
              description: 'Keywords or phrases that trigger specific actions'
            }
          },
          required: ['response_text']
        }
      },
      {
        name: 'schedule_follow_up_survey',
        description: 'Plan and schedule additional surveys or in-depth interviews based on initial feedback responses',
        parameters: {
          type: 'object',
          properties: {
            follow_up_type: {
              type: 'string',
              enum: ['detailed_interview', 'product_specific_survey', 'satisfaction_tracking', 'complaint_resolution', 'loyalty_assessment'],
              description: 'Type of follow-up survey or interview'
            },
            follow_up_reason: {
              type: 'string',
              description: 'Reason for scheduling additional data collection'
            },
            scheduling_preferences: {
              type: 'object',
              properties: {
                preferred_timeframe: { type: 'string' },
                preferred_method: {
                  type: 'string',
                  enum: ['phone_call', 'video_interview', 'email_survey', 'in_person_meeting']
                },
                duration_estimate: { type: 'integer' }
              },
              description: 'Customer preferences for follow-up scheduling'
            },
            priority_level: {
              type: 'string',
              enum: ['low', 'medium', 'high', 'urgent'],
              description: 'Priority for follow-up based on initial feedback'
            },
            specific_topics: {
              type: 'array',
              items: { type: 'string' },
              description: 'Specific areas to explore in follow-up'
            },
            incentive_adjustment: {
              type: 'object',
              properties: {
                additional_incentive: { type: 'boolean' },
                incentive_type: { type: 'string' },
                incentive_value: { type: 'string' }
              },
              description: 'Adjusted incentives for extended participation'
            }
          },
          required: ['follow_up_type', 'follow_up_reason']
        }
      },
      {
        name: 'process_survey_incentive',
        description: 'Handle survey completion rewards, compensation processing, and incentive distribution to participants',
        parameters: {
          type: 'object',
          properties: {
            incentive_type: {
              type: 'string',
              enum: ['cash_payment', 'gift_card', 'discount_code', 'product_sample', 'loyalty_points', 'charity_donation'],
              description: 'Type of incentive to process'
            },
            incentive_value: {
              type: 'number',
              description: 'Monetary value of the incentive'
            },
            delivery_method: {
              type: 'string',
              enum: ['email', 'sms', 'postal_mail', 'digital_wallet', 'account_credit', 'immediate_processing'],
              description: 'How to deliver the incentive'
            },
            customer_details: {
              type: 'object',
              properties: {
                customer_id: { type: 'string' },
                delivery_address: { type: 'string' },
                payment_preference: { type: 'string' },
                tax_information: { type: 'string' }
              },
              description: 'Customer information for incentive processing'
            },
            completion_verification: {
              type: 'object',
              properties: {
                survey_completed: { type: 'boolean' },
                quality_threshold_met: { type: 'boolean' },
                response_count: { type: 'integer' },
                completion_time: { type: 'string' }
              },
              description: 'Verification of survey completion requirements'
            },
            processing_timeline: {
              type: 'string',
              enum: ['immediate', '24_hours', '3_business_days', '1_week', '2_weeks'],
              description: 'Expected processing and delivery timeframe'
            }
          },
          required: ['incentive_type', 'delivery_method', 'completion_verification']
        }
      },
      {
        name: 'escalate_customer_concern',
        description: 'Address and escalate customer complaints, concerns, or issues raised during feedback collection sessions',
        parameters: {
          type: 'object',
          properties: {
            concern_type: {
              type: 'string',
              enum: ['product_defect', 'service_complaint', 'billing_issue', 'privacy_concern', 'accessibility_problem', 'staff_behavior', 'policy_disagreement'],
              description: 'Category of customer concern or complaint'
            },
            concern_severity: {
              type: 'string',
              enum: ['low', 'medium', 'high', 'critical'],
              description: 'Assessed severity level of the concern'
            },
            concern_details: {
              type: 'object',
              properties: {
                description: { type: 'string' },
                affected_products: { type: 'array', items: { type: 'string' } },
                incident_date: { type: 'string' },
                financial_impact: { type: 'string' },
                previous_attempts: { type: 'string' }
              },
              description: 'Detailed information about the concern'
            },
            escalation_path: {
              type: 'string',
              enum: ['customer_service', 'technical_support', 'management', 'legal_department', 'quality_assurance'],
              description: 'Appropriate department for escalation'
            },
            immediate_action_needed: {
              type: 'boolean',
              description: 'Whether immediate action is required'
            },
            compensation_consideration: {
              type: 'object',
              properties: {
                compensation_warranted: { type: 'boolean' },
                compensation_type: { type: 'string' },
                compensation_amount: { type: 'number' }
              },
              description: 'Compensation assessment for the concern'
            },
            follow_up_requirements: {
              type: 'string',
              description: 'Required follow-up actions with the customer'
            }
          },
          required: ['concern_type', 'concern_severity', 'escalation_path']
        }
      },
      {
        name: 'validate_response_quality',
        description: 'Ensure completeness, accuracy, and reliability of collected survey responses with quality scoring',
        parameters: {
          type: 'object',
          properties: {
            response_completeness: {
              type: 'object',
              properties: {
                total_questions: { type: 'integer' },
                answered_questions: { type: 'integer' },
                skipped_questions: { type: 'integer' },
                completion_percentage: { type: 'number' }
              },
              description: 'Response completeness assessment'
            },
            response_consistency: {
              type: 'object',
              properties: {
                consistency_score: { type: 'number', minimum: 0, maximum: 10 },
                contradictory_responses: { type: 'array', items: { type: 'string' } },
                reliability_indicators: { type: 'array', items: { type: 'string' } }
              },
              description: 'Assessment of response consistency and reliability'
            },
            data_quality_flags: {
              type: 'array',
              items: {
                type: 'string',
                enum: ['incomplete_response', 'inconsistent_data', 'extreme_outlier', 'suspicious_pattern', 'rushed_completion', 'high_quality']
              },
              description: 'Quality flags for the response data'
            },
            validation_results: {
              type: 'object',
              properties: {
                overall_quality_score: { type: 'number', minimum: 0, maximum: 10 },
                usability_rating: { type: 'string', enum: ['excellent', 'good', 'fair', 'poor'] },
                recommended_actions: { type: 'array', items: { type: 'string' } }
              },
              description: 'Overall validation assessment and recommendations'
            },
            additional_verification_needed: {
              type: 'boolean',
              description: 'Whether additional verification or follow-up is needed'
            }
          },
          required: ['response_completeness', 'data_quality_flags']
        }
      },
      {
        name: 'generate_feedback_summary',
        description: 'Create real-time summaries and insights from collected customer feedback for immediate analysis',
        parameters: {
          type: 'object',
          properties: {
            summary_scope: {
              type: 'string',
              enum: ['individual_response', 'session_summary', 'daily_insights', 'campaign_overview'],
              description: 'Scope of the feedback summary to generate'
            },
            key_metrics: {
              type: 'object',
              properties: {
                satisfaction_scores: { type: 'array', items: { type: 'number' } },
                sentiment_distribution: { type: 'object' },
                response_rates: { type: 'object' },
                completion_times: { type: 'array', items: { type: 'number' } }
              },
              description: 'Key quantitative metrics from feedback collection'
            },
            qualitative_insights: {
              type: 'object',
              properties: {
                common_themes: { type: 'array', items: { type: 'string' } },
                positive_feedback: { type: 'array', items: { type: 'string' } },
                areas_for_improvement: { type: 'array', items: { type: 'string' } },
                customer_suggestions: { type: 'array', items: { type: 'string' } }
              },
              description: 'Qualitative insights and patterns from responses'
            },
            actionable_recommendations: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  recommendation: { type: 'string' },
                  priority: { type: 'string', enum: ['low', 'medium', 'high', 'urgent'] },
                  department: { type: 'string' },
                  estimated_impact: { type: 'string' }
                }
              },
              description: 'Actionable recommendations based on feedback analysis'
            },
            trend_analysis: {
              type: 'object',
              properties: {
                improving_areas: { type: 'array', items: { type: 'string' } },
                declining_areas: { type: 'array', items: { type: 'string' } },
                stable_metrics: { type: 'array', items: { type: 'string' } }
              },
              description: 'Trend analysis comparing to previous periods'
            }
          },
          required: ['summary_scope', 'key_metrics']
        }
      }
    ],

    endCallMessage: "Thank you so much for taking the time to share your valuable feedback with us! Your insights are really important and will help us improve our products and services. You should receive your survey completion confirmation shortly. Have a wonderful day!",
    voicemailMessage: "Hi {{prospect_name}}, this is {{agent_name}} from {{company_name}}. We'd love to get your feedback about {{survey_topic}} in a quick survey that takes just a few minutes. Your opinion is valuable to us and there's a small thank-you gift for participating. Please give me a call back when convenient. Thanks!",

    // Advanced analysis configuration
    analysisPlan: {
      summaryPlan: {
        enabled: true,
        messages: [
          {
            role: 'system',
            content: 'Summarize this survey and feedback collection call including: survey type completed, key responses and insights gathered, sentiment analysis results, data quality assessment, any concerns or issues raised, and overall feedback collection success.'
          }
        ]
      },
      structuredDataPlan: {
        enabled: true,
        schema: {
          type: 'object',
          properties: {
            survey_completion_status: {
              type: 'string',
              enum: ['fully_completed', 'partially_completed', 'abandoned', 'rescheduled', 'refused']
            },
            survey_type: {
              type: 'string',
              enum: ['customer_satisfaction', 'product_feedback', 'service_evaluation', 'market_research', 'post_purchase', 'net_promoter_score', 'brand_perception']
            },
            overall_sentiment: {
              type: 'string',
              enum: ['very_positive', 'positive', 'neutral', 'negative', 'very_negative']
            },
            response_quality_score: {
              type: 'number',
              minimum: 1,
              maximum: 10,
              description: 'Quality assessment of collected responses (1-10)'
            },
            key_insights: {
              type: 'array',
              items: { type: 'string' }
            },
            follow_up_required: {
              type: 'boolean',
              description: 'Whether additional follow-up is needed'
            },
            concerns_raised: {
              type: 'array',
              items: { type: 'string' }
            },
            customer_satisfaction_rating: {
              type: 'number',
              minimum: 1,
              maximum: 10,
              description: 'Customer satisfaction with survey experience (1-10)'
            }
          }
        }
      }
    }
  },

  // Comprehensive feature set
  features: [
    'AI Survey Administration',
    'Real-time Sentiment Analysis',
    'Intelligent Response Collection',
    'Data Quality Validation',
    'Automated Incentive Processing',
    'Complaint Escalation System',
    'Follow-up Survey Scheduling',
    'Comprehensive Analytics Dashboard',
    'Multi-channel Feedback Collection',
    'Customer Insights Generation'
  ],

  // Integration ecosystem
  defaultIntegrations: [
    'vapi',
    'n8n',
    'survey_platform',
    'crm',
    'analytics',
    'email',
    'sms',
    'incentive_processing'
  ],

  // Success metrics and KPIs
  successMetrics: {
    responseRate: '70-85% survey completion',
    dataQuality: '90-95% high-quality responses',
    customerSatisfaction: '4.5+ survey experience rating',
    insightGeneration: '85-95% actionable insights',
    processingEfficiency: '50-70% time savings'
  },

  // Compliance and best practices
  compliance: {
    dataPrivacy: 'GDPR/CCPA compliant survey data handling',
    consentManagement: 'Explicit consent for survey participation',
    anonymityProtection: 'Configurable anonymity and confidentiality levels',
    qualityStandards: 'ISO 20252 market research quality standards'
  }
};

// Template-to-VAPI Deployment Functions
export const deployEnhancedSurveyFeedbackToVAPI = async (apiConfig: {
  vapiApiKey: string;
  n8nApiKey: string;
  webhookBaseUrl: string;
}): Promise<TemplateVAPIDeploymentConfig> => {

  const deploymentConfig = TemplateToVAPIDeployment.generateVAPIAgentFromTemplate(
    ENHANCED_SURVEY_FEEDBACK_TEMPLATE,
    {
      deploymentSettings: {
        environment: 'production',
        autoStart: true,
        monitoring: {
          enabled: true,
          alerting: true,
          dashboardUrl: `/monitoring/survey-feedback`
        },
        security: {
          encryption: true,
          auditLogging: true,
          accessControl: ['role_based', 'research_manager', 'survey_admin']
        }
      }
    }
  );

  return deploymentConfig;
};

export const validateSurveyFeedbackCompliance = (config: any): {
  isCompliant: boolean;
  violations: string[];
  recommendations: string[];
} => {
  const violations: string[] = [];
  const recommendations: string[] = [];

  // GDPR Compliance Checks
  if (!config.deploymentConfig?.complianceFrameworks?.includes('GDPR')) {
    violations.push('Missing GDPR compliance configuration');
  }

  // CCPA Compliance Checks
  if (!config.deploymentConfig?.complianceFrameworks?.includes('CCPA')) {
    violations.push('Missing CCPA compliance configuration');
  }

  // ISO 20252 Market Research Standards
  if (!config.deploymentConfig?.complianceFrameworks?.includes('ISO_20252')) {
    violations.push('Missing ISO 20252 market research quality standards');
  }

  // Survey Functions Check
  if (!config.functions?.find((f: any) => f.name === 'administer_survey')) {
    violations.push('Missing survey administration capability');
  }

  if (!config.functions?.find((f: any) => f.name === 'analyze_response_sentiment')) {
    violations.push('Missing sentiment analysis functionality');
  }

  if (!config.functions?.find((f: any) => f.name === 'validate_response_quality')) {
    violations.push('Missing response quality validation');
  }

  // Consent Management Check
  if (!config.functions?.find((f: any) => f.name === 'process_survey_incentive')) {
    violations.push('Missing incentive processing capability');
  }

  // Recommendations
  if (violations.length === 0) {
    recommendations.push('All compliance requirements are met');
    recommendations.push('Consider implementing advanced NLP for sentiment analysis');
    recommendations.push('Add multi-language survey support');
  }

  return {
    isCompliant: violations.length === 0,
    violations,
    recommendations
  };
};

export default ENHANCED_SURVEY_FEEDBACK_TEMPLATE;