import type { ToolTemplate } from './types.js';

export const marketingTemplates: ToolTemplate[] = [
  {
    name: 'Get Product Details',
    description: 'Retrieve comprehensive product information and features',
    category: 'marketing',
    type: 'FUNCTION',
    function: {
      name: 'get_product_details',
      description: 'Retrieve comprehensive product information and features',
      parameters: {
        type: 'object',
        properties: {
          product_id: { type: 'string' },
          customer_segment: {
            type: 'string',
            enum: ['early_adopters', 'loyal_customers', 'tech_enthusiasts', 'price_conscious'],
          },
          detail_level: {
            type: 'string',
            enum: ['overview', 'detailed', 'technical', 'competitive'],
          },
          focus_areas: { type: 'array', items: { type: 'string' } },
        },
        required: ['product_id', 'customer_segment'],
      },
    },
  },
  {
    name: 'Assess Customer Interest',
    description: 'Assess and score customer interest level in a new product',
    category: 'marketing',
    type: 'FUNCTION',
    function: {
      name: 'assess_customer_interest',
      description: 'Assess and score customer interest level in the new product',
      parameters: {
        type: 'object',
        properties: {
          interest_indicators: { type: 'array', items: { type: 'string' } },
          questions: { type: 'array', items: { type: 'string' } },
          sentiment_score: { type: 'number', minimum: 1, maximum: 10 },
          purchase_intent: {
            type: 'string',
            enum: ['immediate', 'short_term', 'long_term', 'unlikely'],
          },
        },
        required: ['interest_indicators', 'sentiment_score'],
      },
    },
  },
  {
    name: 'Offer Exclusive Access',
    description: 'Offer exclusive early access or special launch benefits',
    category: 'marketing',
    type: 'FUNCTION',
    function: {
      name: 'offer_exclusive_access',
      description: 'Offer exclusive early access or special launch benefits',
      parameters: {
        type: 'object',
        properties: {
          access_type: {
            type: 'string',
            enum: ['early_access', 'beta_testing', 'exclusive_preview', 'early_bird_pricing'],
          },
          customer_segment: { type: 'string' },
          validity_period: { type: 'string' },
          special_terms: { type: 'string' },
        },
        required: ['access_type', 'customer_segment'],
      },
    },
  },
  {
    name: 'Schedule Product Demo',
    description: 'Schedule a personalized product demonstration or presentation',
    category: 'marketing',
    type: 'FUNCTION',
    function: {
      name: 'schedule_product_demo',
      description: 'Schedule a personalized product demonstration or presentation',
      parameters: {
        type: 'object',
        properties: {
          demo_type: {
            type: 'string',
            enum: ['individual_demo', 'group_webinar', 'technical_deep_dive', 'executive_overview'],
          },
          preferred_time: { type: 'string' },
          duration: { type: 'string' },
          specific_focus: { type: 'array', items: { type: 'string' } },
          attendees: { type: 'number', minimum: 1 },
        },
        required: ['demo_type', 'preferred_time'],
      },
    },
  },
  {
    name: 'Collect Launch Feedback',
    description: 'Collect customer feedback about the product launch and announcement',
    category: 'marketing',
    type: 'FUNCTION',
    function: {
      name: 'collect_launch_feedback',
      description: 'Collect customer feedback about the product launch and announcement',
      parameters: {
        type: 'object',
        properties: {
          feedback_type: {
            type: 'string',
            enum: ['product_features', 'pricing', 'messaging', 'competitive_positioning'],
          },
          rating: { type: 'number', minimum: 1, maximum: 10 },
          comments: { type: 'string' },
          suggestions: { type: 'string' },
          likely_to_recommend: { type: 'boolean' },
        },
        required: ['feedback_type', 'rating'],
      },
    },
  },
  {
    name: 'Capture Lead Information',
    description: 'Capture qualified lead information for product follow-up',
    category: 'marketing',
    type: 'FUNCTION',
    function: {
      name: 'capture_lead_information',
      description: 'Capture qualified lead information for product follow-up',
      parameters: {
        type: 'object',
        properties: {
          lead_quality: { type: 'string', enum: ['hot', 'warm', 'cold', 'nurture'] },
          timeframe: {
            type: 'string',
            enum: ['immediate', '1_month', '3_months', '6_months', 'next_year'],
          },
          budget: {
            type: 'string',
            enum: ['confirmed', 'estimated', 'need_approval', 'unknown'],
          },
          decision_maker: { type: 'boolean' },
          next_steps: { type: 'string' },
        },
        required: ['lead_quality', 'timeframe'],
      },
    },
  },
];
