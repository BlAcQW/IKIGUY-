import type { ToolTemplate } from './types.js';

export const salesTemplates: ToolTemplate[] = [
  {
    name: 'Score Lead Behavior',
    description: 'Analyze lead engagement patterns and behavioral signals to calculate lead score',
    category: 'sales',
    type: 'FUNCTION',
    function: {
      name: 'score_lead_behavior',
      description:
        'Analyze lead engagement patterns, website activity, email interactions, and behavioral signals to calculate lead score and buying intent',
      parameters: {
        type: 'object',
        properties: {
          lead_id: { type: 'string' },
          include_website_activity: { type: 'boolean' },
          include_email_engagement: { type: 'boolean' },
          include_social_signals: { type: 'boolean' },
          time_period_days: { type: 'integer' },
        },
        required: ['lead_id'],
      },
    },
  },
  {
    name: 'Assess Lead Qualification',
    description: 'Evaluate lead qualification using BANT criteria and sales readiness scoring',
    category: 'sales',
    type: 'FUNCTION',
    function: {
      name: 'assess_lead_qualification',
      description:
        'Evaluate lead qualification using BANT criteria (Budget, Authority, Need, Timeline) and sales readiness scoring',
      parameters: {
        type: 'object',
        properties: {
          lead_id: { type: 'string' },
          budget_range: {
            type: 'string',
            enum: ['under_1k', '1k_10k', '10k_50k', '50k_plus', 'unknown'],
          },
          decision_authority: {
            type: 'string',
            enum: ['decision_maker', 'influencer', 'end_user', 'gatekeeper', 'unknown'],
          },
          business_need: { type: 'string', enum: ['urgent', 'high', 'medium', 'low', 'unclear'] },
          purchase_timeline: {
            type: 'string',
            enum: ['immediate', '30_days', '90_days', '6_months', 'no_timeline'],
          },
          pain_points: { type: 'array', items: { type: 'string' } },
        },
        required: ['lead_id'],
      },
    },
  },
  {
    name: 'Track Lead Interaction',
    description: 'Log conversation details, outcomes, and key insights from lead interactions',
    category: 'sales',
    type: 'FUNCTION',
    function: {
      name: 'track_lead_interaction',
      description:
        'Log conversation details, outcomes, and key insights from lead interactions for CRM and follow-up purposes',
      parameters: {
        type: 'object',
        properties: {
          lead_id: { type: 'string' },
          interaction_type: {
            type: 'string',
            enum: ['phone_call', 'email', 'demo', 'meeting', 'follow_up'],
          },
          conversation_summary: { type: 'string' },
          lead_sentiment: {
            type: 'string',
            enum: ['very_interested', 'interested', 'neutral', 'skeptical', 'not_interested'],
          },
          objections_raised: { type: 'array', items: { type: 'string' } },
          next_steps_discussed: { type: 'string' },
          lead_temperature: { type: 'string', enum: ['hot', 'warm', 'cold'] },
        },
        required: ['lead_id', 'interaction_type', 'conversation_summary'],
      },
    },
  },
  {
    name: 'Schedule Follow Up',
    description: 'Schedule demos, meetings, or follow-up conversations based on lead preferences',
    category: 'sales',
    type: 'FUNCTION',
    function: {
      name: 'schedule_follow_up',
      description:
        'Schedule demos, meetings, or follow-up conversations based on lead preferences and sales process requirements',
      parameters: {
        type: 'object',
        properties: {
          lead_id: { type: 'string' },
          follow_up_type: {
            type: 'string',
            enum: ['product_demo', 'discovery_call', 'proposal_meeting', 'check_in', 'decision_call'],
          },
          preferred_date: { type: 'string' },
          preferred_time: { type: 'string' },
          duration_minutes: { type: 'integer' },
          meeting_objectives: { type: 'string' },
          attendees: { type: 'array', items: { type: 'string' } },
        },
        required: ['lead_id', 'follow_up_type'],
      },
    },
  },
  {
    name: 'Send Lead Content',
    description: 'Share relevant resources, case studies, or materials based on lead interests',
    category: 'sales',
    type: 'FUNCTION',
    function: {
      name: 'send_lead_content',
      description:
        'Share relevant resources, case studies, whitepapers, or materials based on lead interests and stage',
      parameters: {
        type: 'object',
        properties: {
          lead_id: { type: 'string' },
          content_type: {
            type: 'string',
            enum: ['case_study', 'whitepaper', 'product_demo', 'pricing_info', 'roi_calculator', 'comparison_guide'],
          },
          industry_specific: { type: 'boolean' },
          use_case_focus: { type: 'string' },
          delivery_method: {
            type: 'string',
            enum: ['email', 'portal_access', 'calendar_invite', 'direct_link'],
          },
          personalized_message: { type: 'string' },
        },
        required: ['lead_id', 'content_type'],
      },
    },
  },
  {
    name: 'Update Lead Status',
    description: 'Progress leads through sales stages and update CRM status',
    category: 'sales',
    type: 'FUNCTION',
    function: {
      name: 'update_lead_status',
      description:
        'Progress leads through sales stages and update CRM status based on qualification and readiness',
      parameters: {
        type: 'object',
        properties: {
          lead_id: { type: 'string' },
          new_stage: {
            type: 'string',
            enum: [
              'new_lead', 'contacted', 'qualified', 'demo_scheduled',
              'proposal_sent', 'negotiation', 'closed_won', 'closed_lost',
            ],
          },
          stage_reason: { type: 'string' },
          lead_score_update: { type: 'integer' },
          priority_level: { type: 'string', enum: ['high', 'medium', 'low'] },
          sales_notes: { type: 'string' },
        },
        required: ['lead_id', 'new_stage'],
      },
    },
  },
  {
    name: 'Create Lead Task',
    description: 'Create tasks, reminders, and action items for sales team follow-up',
    category: 'sales',
    type: 'FUNCTION',
    function: {
      name: 'create_lead_task',
      description:
        'Create tasks, reminders, and action items for sales team follow-up and lead management',
      parameters: {
        type: 'object',
        properties: {
          lead_id: { type: 'string' },
          task_type: {
            type: 'string',
            enum: ['follow_up_call', 'send_proposal', 'schedule_demo', 'send_contract', 'check_decision_status'],
          },
          assigned_to: { type: 'string' },
          due_date: { type: 'string' },
          priority: { type: 'string', enum: ['urgent', 'high', 'normal', 'low'] },
          task_description: { type: 'string' },
          related_opportunity: { type: 'string' },
        },
        required: ['lead_id', 'task_type', 'task_description'],
      },
    },
  },
  {
    name: 'Escalate to Sales',
    description: 'Transfer qualified leads to account executives with complete context',
    category: 'sales',
    type: 'FUNCTION',
    function: {
      name: 'escalate_to_sales',
      description:
        'Transfer qualified leads to account executives with complete context and qualification details',
      parameters: {
        type: 'object',
        properties: {
          lead_id: { type: 'string' },
          sales_rep_id: { type: 'string' },
          qualification_summary: { type: 'string' },
          deal_size_estimate: { type: 'number' },
          close_probability: { type: 'number' },
          key_stakeholders: { type: 'array', items: { type: 'string' } },
          recommended_next_steps: { type: 'string' },
          urgency_level: { type: 'string', enum: ['immediate', 'high', 'normal'] },
        },
        required: ['lead_id', 'qualification_summary'],
      },
    },
  },
];
