/**
 * Enhanced Product Launch Announcement Campaign with VAPI + n8n
 *
 * AI-powered product launch campaign featuring personalized announcements,
 * customer segmentation, engagement tracking, and comprehensive launch analytics.
 */

import { generateVAPIConfig } from './vapi-config-standards';
import { generateN8nWorkflow } from './n8n-workflow-patterns';
import { generateMonitoringConfig } from './monitoring-integration';

export const ENHANCED_PRODUCT_LAUNCH_ANNOUNCEMENT_TEMPLATE = {
  id: 'enhanced_product_launch_announcement_vapi_n8n',
  name: 'Enhanced Product Launch Announcement with VAPI + n8n',
  description: 'AI-powered product launch campaign featuring personalized voice announcements, customer segmentation, excitement generation, early adopter identification, and comprehensive launch performance analytics',
  industry: 'technology',
  category: 'Product Marketing',
  complexity: 'Advanced' as const,
  estimatedTime: '35 min',
  integrationCategories: ['automation', 'crm', 'analytics', 'messaging', 'database', 'social'],
  defaultIntegrations: ['n8n', 'vapi', 'crm.customer_database', 'analytics.product_analytics', 'messaging.multi_channel', 'social.social_media'],

  workflow: [
    {
      id: 'vapi_product_announcement_call',
      name: 'VAPI Product Launch Announcement Call',
      type: 'integration',
      integrationCategory: 'automation',
      config: {
        tool: 'VAPI Voice Agent',
        action: 'initiate_product_announcement_call',
        n8n_webhook_trigger: true,
        monitoring_enabled: true,
        personalization: true,
        description: 'Personalized voice agent announces new product to segmented customers'
      }
    },

    {
      id: 'segment_customer_base',
      name: 'Intelligent Customer Segmentation',
      type: 'integration',
      integrationCategory: 'analytics',
      config: {
        capability: 'customer_segmentation',
        action: 'segment_by_launch_relevance',
        n8n_node: 'OpenAI GPT-4',
        segmentation_criteria: ['purchase_history', 'product_interest', 'engagement_level', 'customer_value'],
        ml_enhanced: true,
        target_segments: ['early_adopters', 'loyal_customers', 'tech_enthusiasts', 'price_conscious']
      }
    },

    {
      id: 'validate_customer_eligibility',
      name: 'Validate Customer Eligibility',
      type: 'integration',
      integrationCategory: 'crm',
      config: {
        capability: 'customer_verification',
        action: 'validate_announcement_eligibility',
        n8n_node: 'Function',
        validation_rules: ['active_customer', 'communication_preferences', 'segment_match'],
        preference_respect: true,
        gdpr_compliant: true
      }
    },

    {
      id: 'personalize_product_message',
      name: 'Personalize Product Announcement',
      type: 'integration',
      integrationCategory: 'analytics',
      config: {
        capability: 'message_personalization',
        action: 'generate_personalized_announcement',
        n8n_node: 'OpenAI GPT-4',
        personalization_factors: ['customer_segment', 'past_purchases', 'interests', 'communication_style'],
        product_positioning: true,
        value_proposition_optimization: true
      }
    },

    {
      id: 'retrieve_customer_profile',
      name: 'Retrieve Customer Product Interest Profile',
      type: 'integration',
      integrationCategory: 'crm',
      config: {
        capability: 'customer_analytics',
        action: 'get_product_interest_profile',
        n8n_node: 'HTTP Request',
        endpoint: '{{api_base_url}}/api/customers/product-interests',
        data_enrichment: true,
        behavior_analysis: true
      }
    },

    {
      id: 'generate_excitement_metrics',
      name: 'Real-time Excitement & Interest Analysis',
      type: 'integration',
      integrationCategory: 'analytics',
      config: {
        capability: 'sentiment_analysis',
        action: 'analyze_customer_excitement',
        n8n_node: 'OpenAI GPT-4',
        real_time_tracking: true,
        interest_scoring: true,
        engagement_triggers: ['very_interested', 'wants_demo', 'price_inquiry', 'early_access_request']
      }
    },

    {
      id: 'provide_product_details',
      name: 'Provide Detailed Product Information',
      type: 'integration',
      integrationCategory: 'automation',
      config: {
        capability: 'product_education',
        action: 'deliver_product_overview',
        n8n_node: 'Function',
        information_types: ['features', 'benefits', 'pricing', 'availability', 'comparison'],
        adaptive_depth: true,
        customer_specific_relevance: true
      }
    },

    {
      id: 'capture_early_interest',
      name: 'Capture Early Adopter Interest',
      type: 'condition',
      config: {
        condition: 'excitement_score > 7 AND customer_segment IN ["early_adopters", "tech_enthusiasts"]',
        n8n_node: 'IF Conditional',
        interest_capture_strategy: {
          'early_adopters': 'exclusive_early_access_offer',
          'tech_enthusiasts': 'beta_testing_invitation',
          'loyal_customers': 'special_preview_access',
          'price_conscious': 'early_bird_discount'
        }
      }
    },

    {
      id: 'schedule_product_demo',
      name: 'Schedule Product Demo/Presentation',
      type: 'integration',
      integrationCategory: 'calendar',
      config: {
        capability: 'demo_scheduling',
        action: 'schedule_product_demonstration',
        n8n_node: 'Calendly Integration',
        demo_types: ['1_on_1_demo', 'group_webinar', 'self_guided_tour', 'technical_deep_dive'],
        calendar_sync: true,
        reminder_automation: true
      }
    },

    {
      id: 'capture_feedback',
      name: 'Capture Launch Feedback & Suggestions',
      type: 'integration',
      integrationCategory: 'analytics',
      config: {
        capability: 'feedback_collection',
        action: 'collect_product_feedback',
        n8n_node: 'HTTP Request',
        feedback_categories: ['product_features', 'pricing_perception', 'competitive_positioning', 'purchase_intent'],
        sentiment_analysis: true,
        actionable_insights: true
      }
    },

    {
      id: 'update_customer_journey',
      name: 'Update Customer Product Journey',
      type: 'integration',
      integrationCategory: 'crm',
      config: {
        capability: 'customer_journey_tracking',
        action: 'update_product_interest_journey',
        n8n_node: 'HTTP Request',
        journey_stages: ['awareness', 'interest', 'consideration', 'trial_intent', 'purchase_ready'],
        lifecycle_progression: true,
        next_action_planning: true
      }
    },

    {
      id: 'trigger_follow_up_sequence',
      name: 'Trigger Intelligent Follow-up Sequence',
      type: 'integration',
      integrationCategory: 'automation',
      config: {
        capability: 'follow_up_automation',
        action: 'initiate_product_nurture_sequence',
        n8n_node: 'Schedule Trigger',
        sequence_personalization: true,
        channel_optimization: ['voice', 'email', 'sms', 'in_app'],
        timing_optimization: true
      }
    },

    {
      id: 'track_launch_metrics',
      name: 'Track Launch Performance Metrics',
      type: 'integration',
      integrationCategory: 'analytics',
      config: {
        capability: 'launch_analytics',
        action: 'record_launch_performance',
        n8n_node: 'HTTP Request',
        metrics: ['reach_rate', 'engagement_rate', 'interest_score', 'demo_conversion', 'early_adoption_rate'],
        real_time_dashboard: true,
        competitive_benchmarking: true
      }
    }
  ],

  // VAPI Configuration for product launch announcement
  vapiConfig: generateVAPIConfig('technology', {
    agentName: 'Product Launch Specialist',
    agentRole: 'Product Marketing Representative',
    specificExpertise: [
      'Product positioning and messaging',
      'Feature benefit communication',
      'Early adopter engagement',
      'Competitive differentiation',
      'Customer excitement generation'
    ],
    customFunctions: [
      {
        name: 'getProductDetails',
        description: 'Retrieve comprehensive product information and features',
        parameters: {
          type: 'object',
          properties: {
            productId: { type: 'string' },
            customerSegment: { type: 'string', enum: ['early_adopters', 'loyal_customers', 'tech_enthusiasts', 'price_conscious'] },
            detailLevel: { type: 'string', enum: ['overview', 'detailed', 'technical', 'competitive'] },
            focusAreas: { type: 'array', items: { type: 'string' } }
          },
          required: ['productId', 'customerSegment']
        }
      },
      {
        name: 'assessCustomerInterest',
        description: 'Assess and score customer interest level in the new product',
        parameters: {
          type: 'object',
          properties: {
            interestIndicators: { type: 'array', items: { type: 'string' } },
            questions: { type: 'array', items: { type: 'string' } },
            sentimentScore: { type: 'number', minimum: 1, maximum: 10 },
            purchaseIntent: { type: 'string', enum: ['immediate', 'short_term', 'long_term', 'unlikely'] }
          },
          required: ['interestIndicators', 'sentimentScore']
        }
      },
      {
        name: 'offerExclusiveAccess',
        description: 'Offer exclusive early access or special launch benefits',
        parameters: {
          type: 'object',
          properties: {
            accessType: { type: 'string', enum: ['early_access', 'beta_testing', 'exclusive_preview', 'early_bird_pricing'] },
            customerSegment: { type: 'string' },
            validityPeriod: { type: 'string' },
            specialTerms: { type: 'string' }
          },
          required: ['accessType', 'customerSegment']
        }
      },
      {
        name: 'scheduleProductDemo',
        description: 'Schedule a personalized product demonstration or presentation',
        parameters: {
          type: 'object',
          properties: {
            demoType: { type: 'string', enum: ['individual_demo', 'group_webinar', 'technical_deep_dive', 'executive_overview'] },
            preferredTime: { type: 'string' },
            duration: { type: 'string' },
            specificFocus: { type: 'array', items: { type: 'string' } },
            attendees: { type: 'number', minimum: 1 }
          },
          required: ['demoType', 'preferredTime']
        }
      },
      {
        name: 'collectLaunchFeedback',
        description: 'Collect customer feedback about the product launch and announcement',
        parameters: {
          type: 'object',
          properties: {
            feedbackType: { type: 'string', enum: ['product_features', 'pricing', 'messaging', 'competitive_positioning'] },
            rating: { type: 'number', minimum: 1, maximum: 10 },
            comments: { type: 'string' },
            suggestions: { type: 'string' },
            likelyToRecommend: { type: 'boolean' }
          },
          required: ['feedbackType', 'rating']
        }
      },
      {
        name: 'captureLeadInformation',
        description: 'Capture qualified lead information for product follow-up',
        parameters: {
          type: 'object',
          properties: {
            leadQuality: { type: 'string', enum: ['hot', 'warm', 'cold', 'nurture'] },
            timeframe: { type: 'string', enum: ['immediate', '1_month', '3_months', '6_months', 'next_year'] },
            budget: { type: 'string', enum: ['confirmed', 'estimated', 'need_approval', 'unknown'] },
            decisionMaker: { type: 'boolean' },
            nextSteps: { type: 'string' }
          },
          required: ['leadQuality', 'timeframe']
        }
      }
    ],
    systemPromptAdditions: `
Product Launch Guidelines:
- Generate enthusiasm and excitement about the new product
- Focus on value proposition and customer benefits
- Listen for buying signals and interest indicators
- Tailor messaging to customer segment and history
- Be knowledgeable about competitive advantages
- Create urgency through exclusive offers when appropriate
- Always aim to move customers forward in their product journey

Announcement Strategy:
- Start with personalized greeting acknowledging customer relationship
- Present product as solution to known customer needs
- Highlight exclusive benefits for their customer segment
- Use storytelling to make features relatable
- Address potential concerns proactively
- End with clear next steps and follow-up plan
- Capture valuable feedback for launch optimization

Communication Style:
- Enthusiastic but professional
- Customer-centric messaging
- Clear value articulation
- Genuine interest in customer success
- Respectful of customer time and preferences
`
  }),

  // n8n Workflow Configuration
  n8nWorkflow: generateN8nWorkflow('enhanced_product_launch_announcement_vapi_n8n', {
    name: 'Enhanced Product Launch Announcement with VAPI + n8n',
    description: 'AI-powered product launch workflow with voice agent and customer segmentation',
    webhookPath: 'product-launch-announcement-enhanced',
    industry: 'technology',
    monitoringEnabled: true
  }),

  // Monitoring Configuration
  monitoringConfig: generateMonitoringConfig(
    'enhanced_product_launch_announcement_vapi_n8n',
    'technology',
    {
      dashboardConfig: {
        realTimeMetrics: [
          'announcement_reach_rate',
          'customer_engagement_rate',
          'interest_conversion_rate',
          'demo_booking_rate',
          'early_adopter_capture_rate',
          'launch_sentiment_score'
        ],
        customWidgets: [
          {
            id: 'launch_engagement_funnel',
            type: 'funnel',
            title: 'Product Launch Engagement Funnel',
            dataSource: 'launch_analytics',
            refreshInterval: 30000,
            config: {
              stages: ['contacted', 'engaged', 'interested', 'demo_booked', 'early_adopter'],
              conversionTarget: 25,
              timeRange: '7d'
            }
          },
          {
            id: 'customer_segment_performance',
            type: 'bar_chart',
            title: 'Engagement by Customer Segment',
            dataSource: 'segmentation_analytics',
            refreshInterval: 60000,
            config: {
              segments: ['early_adopters', 'loyal_customers', 'tech_enthusiasts', 'price_conscious'],
              metrics: ['engagement_rate', 'interest_score', 'conversion_rate'],
              timeRange: '24h'
            }
          },
          {
            id: 'launch_sentiment_tracker',
            type: 'gauge',
            title: 'Overall Launch Sentiment',
            dataSource: 'sentiment_analytics',
            refreshInterval: 30000,
            config: {
              metric: 'average_sentiment_score',
              format: 'score',
              target: 8.0,
              thresholds: {
                excellent: 8.5,
                good: 7.5,
                warning: 6.0,
                critical: 5.0
              }
            }
          }
        ]
      }
    }
  ),

  complianceFrameworks: ['GDPR', 'CCPA', 'CAN-SPAM', 'TCPA', 'SOX'],

  features: [
    'AI-Powered Voice Agent',
    'Intelligent Customer Segmentation',
    'Personalized Product Announcements',
    'Real-time Interest Scoring',
    'Early Adopter Identification',
    'Automated Demo Scheduling',
    'Multi-Channel Follow-up',
    'Launch Performance Analytics',
    'Competitive Positioning',
    'Customer Journey Tracking'
  ],

  specializedServices: {
    monitoringService: 'ProductLaunchMonitoringService',
    analyticsService: 'LaunchPerformanceAnalyticsService',
    segmentationService: 'CustomerSegmentationService',
    personalizationService: 'ProductMessagingPersonalizationService'
  },

  securityConfig: {
    complianceFrameworks: ['GDPR', 'CCPA', 'CAN-SPAM', 'TCPA'],
    dataEncryption: true,
    auditTrail: true,
    accessControls: ['role_based', 'mfa_required', 'session_timeout'],
    dataRetentionPolicy: '3_years',
    piiProtection: true,
    consentTracking: true,
    competitiveInformationProtection: true
  },

  popular: true,
  rating: 4.8,
  usageCount: 1247
};

export default ENHANCED_PRODUCT_LAUNCH_ANNOUNCEMENT_TEMPLATE;