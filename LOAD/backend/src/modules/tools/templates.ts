export interface ToolTemplate {
  name: string;
  description: string;
  category: ToolTemplateCategory;
  type: 'FUNCTION' | 'TRANSFER_CALL' | 'END_CALL';
  function: {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
  };
}

export type ToolTemplateCategory =
  | 'scheduling'
  | 'sales'
  | 'finance'
  | 'retention'
  | 'survey'
  | 'marketing'
  | 'insurance'
  | 'healthcare';

export const TOOL_TEMPLATE_CATEGORIES: Record<ToolTemplateCategory, string> = {
  scheduling: 'Scheduling',
  sales: 'Sales & Lead Nurturing',
  finance: 'Finance & Payments',
  retention: 'Customer Retention',
  survey: 'Survey & Feedback',
  marketing: 'Marketing & Product Launch',
  insurance: 'Insurance',
  healthcare: 'Healthcare',
};

// ─── Scheduling ──────────────────────────────────────────────────────

const schedulingTemplates: ToolTemplate[] = [
  {
    name: 'Check Availability',
    description: 'Check real-time calendar availability across team members and appointment types',
    category: 'scheduling',
    type: 'FUNCTION',
    function: {
      name: 'check_availability',
      description:
        'Check real-time calendar availability across team members and appointment types for optimal scheduling',
      parameters: {
        type: 'object',
        properties: {
          appointment_type: {
            type: 'string',
            enum: ['consultation', 'demo', 'meeting', 'service_appointment', 'follow_up', 'group_session'],
          },
          preferred_dates: { type: 'array', items: { type: 'string' } },
          preferred_times: { type: 'array', items: { type: 'string' } },
          duration_minutes: { type: 'integer' },
          team_member_preference: { type: 'string' },
          time_zone: { type: 'string' },
          urgent_booking: { type: 'boolean' },
        },
        required: ['appointment_type', 'duration_minutes'],
      },
    },
  },
  {
    name: 'Book Appointment',
    description: 'Schedule new appointments with calendar integration and confirmation sending',
    category: 'scheduling',
    type: 'FUNCTION',
    function: {
      name: 'book_appointment',
      description:
        'Schedule new appointments with automatic calendar integration and confirmation sending',
      parameters: {
        type: 'object',
        properties: {
          appointment_type: {
            type: 'string',
            enum: ['consultation', 'demo', 'meeting', 'service_appointment', 'follow_up', 'group_session'],
          },
          scheduled_datetime: { type: 'string' },
          duration_minutes: { type: 'integer' },
          team_member_id: { type: 'string' },
          customer_name: { type: 'string' },
          customer_email: { type: 'string' },
          customer_phone: { type: 'string' },
          appointment_notes: { type: 'string' },
          meeting_location: {
            type: 'string',
            enum: ['in_person', 'video_call', 'phone_call', 'customer_location'],
          },
          send_calendar_invite: { type: 'boolean' },
        },
        required: ['appointment_type', 'scheduled_datetime', 'duration_minutes', 'customer_name', 'customer_email'],
      },
    },
  },
  {
    name: 'Reschedule Appointment',
    description: 'Modify existing appointments and send update notifications to all participants',
    category: 'scheduling',
    type: 'FUNCTION',
    function: {
      name: 'reschedule_appointment',
      description:
        'Modify existing appointments and send update notifications to all participants',
      parameters: {
        type: 'object',
        properties: {
          appointment_id: { type: 'string' },
          new_datetime: { type: 'string' },
          new_duration_minutes: { type: 'integer' },
          reschedule_reason: {
            type: 'string',
            enum: ['customer_request', 'team_conflict', 'emergency', 'optimization', 'technical_issue'],
          },
          notify_customer: { type: 'boolean' },
          apology_message: { type: 'string' },
          compensation_offered: { type: 'string' },
        },
        required: ['appointment_id', 'new_datetime', 'reschedule_reason'],
      },
    },
  },
  {
    name: 'Cancel Appointment',
    description: 'Cancel appointments and manage cancellation processes including waiting list',
    category: 'scheduling',
    type: 'FUNCTION',
    function: {
      name: 'cancel_appointment',
      description:
        'Cancel appointments and manage cancellation processes including waiting list notifications',
      parameters: {
        type: 'object',
        properties: {
          appointment_id: { type: 'string' },
          cancellation_reason: {
            type: 'string',
            enum: ['customer_request', 'team_unavailable', 'emergency', 'no_show', 'technical_issue', 'weather'],
          },
          initiated_by: { type: 'string', enum: ['customer', 'team', 'system'] },
          refund_required: { type: 'boolean' },
          reschedule_offered: { type: 'boolean' },
          notify_waiting_list: { type: 'boolean' },
          cancellation_notes: { type: 'string' },
        },
        required: ['appointment_id', 'cancellation_reason', 'initiated_by'],
      },
    },
  },
  {
    name: 'Send Confirmation',
    description: 'Send appointment confirmations, calendar invitations, and preparation materials',
    category: 'scheduling',
    type: 'FUNCTION',
    function: {
      name: 'send_confirmation',
      description:
        'Send appointment confirmations, calendar invitations, and preparation materials to customers',
      parameters: {
        type: 'object',
        properties: {
          appointment_id: { type: 'string' },
          confirmation_type: {
            type: 'string',
            enum: ['initial_booking', 'reschedule_update', 'reminder', 'preparation_materials'],
          },
          include_calendar_invite: { type: 'boolean' },
          include_preparation_guide: { type: 'boolean' },
          include_location_details: { type: 'boolean' },
          custom_message: { type: 'string' },
          send_via: {
            type: 'array',
            items: { type: 'string', enum: ['email', 'sms', 'phone_call'] },
          },
        },
        required: ['appointment_id', 'confirmation_type'],
      },
    },
  },
  {
    name: 'Set Appointment Reminders',
    description: 'Schedule automated reminder notifications at specified intervals before appointments',
    category: 'scheduling',
    type: 'FUNCTION',
    function: {
      name: 'set_appointment_reminders',
      description:
        'Schedule automated reminder notifications at specified intervals before appointments',
      parameters: {
        type: 'object',
        properties: {
          appointment_id: { type: 'string' },
          reminder_schedule: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                time_before: {
                  type: 'string',
                  enum: ['24_hours', '2_hours', '30_minutes', '1_week', '3_days'],
                },
                reminder_type: {
                  type: 'string',
                  enum: ['email', 'sms', 'phone_call', 'app_notification'],
                },
                include_preparation: { type: 'boolean' },
              },
            },
          },
          customer_preferences: {
            type: 'object',
            properties: {
              preferred_reminder_method: {
                type: 'string',
                enum: ['email', 'sms', 'phone_call', 'app_notification'],
              },
              reminder_frequency: { type: 'string', enum: ['minimal', 'standard', 'frequent'] },
            },
          },
        },
        required: ['appointment_id', 'reminder_schedule'],
      },
    },
  },
  {
    name: 'Collect Appointment Details',
    description: 'Gather required information and special requirements for appointment types',
    category: 'scheduling',
    type: 'FUNCTION',
    function: {
      name: 'collect_appointment_details',
      description:
        'Gather required information and special requirements for specific appointment types',
      parameters: {
        type: 'object',
        properties: {
          appointment_type: {
            type: 'string',
            enum: ['consultation', 'demo', 'meeting', 'service_appointment', 'follow_up', 'group_session'],
          },
          required_information: { type: 'array', items: { type: 'string' } },
          special_requirements: { type: 'array', items: { type: 'string' } },
          preparation_materials: { type: 'array', items: { type: 'string' } },
          health_safety_requirements: { type: 'array', items: { type: 'string' } },
          technical_requirements: { type: 'array', items: { type: 'string' } },
        },
        required: ['appointment_type'],
      },
    },
  },
  {
    name: 'Coordinate Team Availability',
    description: 'Check multiple team member calendars for group appointments and coordination',
    category: 'scheduling',
    type: 'FUNCTION',
    function: {
      name: 'coordinate_team_availability',
      description:
        'Check multiple team member calendars for group appointments and team coordination',
      parameters: {
        type: 'object',
        properties: {
          team_members: { type: 'array', items: { type: 'string' } },
          appointment_type: {
            type: 'string',
            enum: ['group_consultation', 'team_demo', 'multi_expert_session', 'training_session'],
          },
          minimum_attendees: { type: 'integer' },
          preferred_dates: { type: 'array', items: { type: 'string' } },
          duration_minutes: { type: 'integer' },
          priority_level: { type: 'string', enum: ['low', 'medium', 'high', 'urgent'] },
          customer_flexibility: {
            type: 'string',
            enum: ['very_flexible', 'somewhat_flexible', 'specific_requirements'],
          },
        },
        required: ['team_members', 'appointment_type', 'duration_minutes'],
      },
    },
  },
];

// ─── Sales & Lead Nurturing ──────────────────────────────────────────

const salesTemplates: ToolTemplate[] = [
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

// ─── Finance & Payments ──────────────────────────────────────────────

const financeTemplates: ToolTemplate[] = [
  {
    name: 'Get Account Details',
    description: 'Retrieve account information including balance, payment history, and status',
    category: 'finance',
    type: 'FUNCTION',
    function: {
      name: 'get_account_details',
      description:
        'Retrieve comprehensive account information including balance, payment history, and account status',
      parameters: {
        type: 'object',
        properties: {
          account_number: { type: 'string' },
          include_history: { type: 'boolean' },
        },
        required: ['account_number'],
      },
    },
  },
  {
    name: 'Verify Customer Identity',
    description: 'Securely verify customer identity using multiple security questions',
    category: 'finance',
    type: 'FUNCTION',
    function: {
      name: 'verify_customer_identity',
      description: 'Securely verify customer identity using multiple security questions',
      parameters: {
        type: 'object',
        properties: {
          account_number: { type: 'string' },
          verification_method: {
            type: 'string',
            enum: ['ssn_last_four', 'billing_address', 'phone_number', 'date_of_birth'],
          },
          provided_value: { type: 'string' },
        },
        required: ['account_number', 'verification_method', 'provided_value'],
      },
    },
  },
  {
    name: 'Calculate Payment Plans',
    description: 'Generate affordable payment plan options based on customer financial situation',
    category: 'finance',
    type: 'FUNCTION',
    function: {
      name: 'calculate_payment_plans',
      description:
        'Generate affordable payment plan options based on customer financial situation',
      parameters: {
        type: 'object',
        properties: {
          account_number: { type: 'string' },
          current_balance: { type: 'number' },
          customer_budget: { type: 'number' },
          payment_frequency: {
            type: 'string',
            enum: ['weekly', 'bi_weekly', 'monthly'],
          },
          down_payment: { type: 'number' },
        },
        required: ['account_number', 'current_balance'],
      },
    },
  },
  {
    name: 'Process Payment',
    description: 'Securely process customer payment using various payment methods',
    category: 'finance',
    type: 'FUNCTION',
    function: {
      name: 'process_payment',
      description: 'Securely process customer payment using various payment methods',
      parameters: {
        type: 'object',
        properties: {
          account_number: { type: 'string' },
          payment_amount: { type: 'number' },
          payment_method: {
            type: 'string',
            enum: ['credit_card', 'debit_card', 'ach_bank_transfer', 'check_by_phone'],
          },
          payment_details: { type: 'object' },
          is_recurring: { type: 'boolean' },
        },
        required: ['account_number', 'payment_amount', 'payment_method'],
      },
    },
  },
  {
    name: 'Schedule Payment',
    description: 'Schedule future payment arrangements and set up payment reminders',
    category: 'finance',
    type: 'FUNCTION',
    function: {
      name: 'schedule_payment',
      description: 'Schedule future payment arrangements and set up payment reminders',
      parameters: {
        type: 'object',
        properties: {
          account_number: { type: 'string' },
          payment_date: { type: 'string', format: 'date' },
          payment_amount: { type: 'number' },
          payment_method: {
            type: 'string',
            enum: ['credit_card', 'debit_card', 'ach_bank_transfer', 'manual_payment'],
          },
          send_reminder: { type: 'boolean' },
          reminder_days_before: { type: 'number' },
        },
        required: ['account_number', 'payment_date', 'payment_amount'],
      },
    },
  },
  {
    name: 'Handle Dispute',
    description: 'Process customer disputes and initiate proper dispute handling procedures',
    category: 'finance',
    type: 'FUNCTION',
    function: {
      name: 'handle_dispute',
      description: 'Process customer disputes and initiate proper dispute handling procedures',
      parameters: {
        type: 'object',
        properties: {
          account_number: { type: 'string' },
          dispute_reason: {
            type: 'string',
            enum: ['never_received_service', 'incorrect_amount', 'already_paid', 'identity_theft', 'billing_error', 'other'],
          },
          dispute_details: { type: 'string' },
          pause_collections: { type: 'boolean' },
        },
        required: ['account_number', 'dispute_reason', 'dispute_details'],
      },
    },
  },
  {
    name: 'Generate Settlement Offer',
    description: 'Create settlement offers for accounts that qualify for reduced payment',
    category: 'finance',
    type: 'FUNCTION',
    function: {
      name: 'generate_settlement_offer',
      description: 'Create settlement offers for accounts that qualify for reduced payment',
      parameters: {
        type: 'object',
        properties: {
          account_number: { type: 'string' },
          current_balance: { type: 'number' },
          customer_financial_hardship: {
            type: 'string',
            enum: ['temporary', 'permanent', 'unemployment', 'medical', 'other'],
          },
          proposed_settlement_percentage: { type: 'number', minimum: 30, maximum: 90 },
          payment_terms: {
            type: 'string',
            enum: ['lump_sum', 'three_payments', 'six_payments'],
          },
        },
        required: ['account_number', 'current_balance', 'customer_financial_hardship'],
      },
    },
  },
  {
    name: 'Record Interaction',
    description: 'Document call details, customer responses, and outcomes for compliance',
    category: 'finance',
    type: 'FUNCTION',
    function: {
      name: 'record_interaction',
      description:
        'Document all call details, customer responses, and outcomes for compliance',
      parameters: {
        type: 'object',
        properties: {
          account_number: { type: 'string' },
          interaction_summary: { type: 'string' },
          customer_response: {
            type: 'string',
            enum: ['payment_made', 'payment_promised', 'dispute_raised', 'hardship_claimed', 'refused_to_pay', 'hung_up'],
          },
          next_action: { type: 'string' },
          compliance_notes: { type: 'string' },
          call_recording_id: { type: 'string' },
        },
        required: ['account_number', 'interaction_summary', 'customer_response'],
      },
    },
  },
];

// ─── Customer Retention ──────────────────────────────────────────────

const retentionTemplates: ToolTemplate[] = [
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

// ─── Survey & Feedback ───────────────────────────────────────────────

const surveyTemplates: ToolTemplate[] = [
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

// ─── Marketing & Product Launch ──────────────────────────────────────

const marketingTemplates: ToolTemplate[] = [
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

// ─── Insurance ───────────────────────────────────────────────────────

const insuranceTemplates: ToolTemplate[] = [
  {
    name: 'Lookup Customer Account',
    description: 'Look up customer account information using policy number',
    category: 'insurance',
    type: 'FUNCTION',
    function: {
      name: 'lookup_customer_account',
      description: 'Look up customer account information using policy number',
      parameters: {
        type: 'object',
        properties: {
          policy_number: { type: 'string' },
          verification_method: {
            type: 'string',
            enum: ['ssn', 'dob', 'security_question'],
          },
        },
        required: ['policy_number', 'verification_method'],
      },
    },
  },
  {
    name: 'Initiate Claims Process',
    description: 'Start the claims filing process for the customer',
    category: 'insurance',
    type: 'FUNCTION',
    function: {
      name: 'initiate_claims_process',
      description: 'Start the claims filing process for the customer',
      parameters: {
        type: 'object',
        properties: {
          claim_type: { type: 'string', enum: ['auto', 'home', 'life', 'health'] },
          incident_date: { type: 'string' },
          incident_description: { type: 'string' },
          estimated_amount: { type: 'number' },
        },
        required: ['claim_type', 'incident_date', 'incident_description'],
      },
    },
  },
  {
    name: 'Check Payment Status',
    description: 'Check the status of premium payments or claim payments',
    category: 'insurance',
    type: 'FUNCTION',
    function: {
      name: 'check_payment_status',
      description: 'Check the status of premium payments or claim payments',
      parameters: {
        type: 'object',
        properties: {
          payment_type: { type: 'string', enum: ['premium', 'claim'] },
          reference_number: { type: 'string' },
        },
        required: ['payment_type'],
      },
    },
  },
  {
    name: 'Assess Financial Hardship',
    description: 'Assess customer financial hardship situation for premium flexibility',
    category: 'insurance',
    type: 'FUNCTION',
    function: {
      name: 'assess_financial_hardship',
      description: 'Assess customer financial hardship situation',
      parameters: {
        type: 'object',
        properties: {
          employment_status: {
            type: 'string',
            enum: ['employed', 'unemployed', 'reduced_hours', 'disability'],
          },
          household_changes: { type: 'string' },
          medical_issues: { type: 'boolean' },
          other_circumstances: { type: 'string' },
        },
        required: ['employment_status'],
      },
    },
  },
  {
    name: 'Request Hardship Assistance',
    description: 'Request hardship assistance options for qualified customers',
    category: 'insurance',
    type: 'FUNCTION',
    function: {
      name: 'request_hardship_assistance',
      description: 'Request hardship assistance options for qualified customers',
      parameters: {
        type: 'object',
        properties: {
          assistance_type: {
            type: 'string',
            enum: ['payment_reduction', 'grace_period', 'policy_modification'],
          },
          duration: { type: 'string' },
          justification: { type: 'string' },
        },
        required: ['assistance_type', 'justification'],
      },
    },
  },
];

// ─── Healthcare ──────────────────────────────────────────────────────

const healthcareTemplates: ToolTemplate[] = [
  {
    name: 'Confirm Appointment',
    description: 'Confirm patient attendance for upcoming appointment',
    category: 'healthcare',
    type: 'FUNCTION',
    function: {
      name: 'confirm_appointment',
      description: 'Confirm patient attendance for upcoming appointment',
      parameters: {
        type: 'object',
        properties: {
          appointment_id: { type: 'string' },
          confirmation_status: {
            type: 'string',
            enum: ['confirmed', 'needs_reschedule', 'cancel'],
          },
          notes: { type: 'string' },
        },
        required: ['appointment_id', 'confirmation_status'],
      },
    },
  },
  {
    name: 'Reschedule Patient Appointment',
    description: 'Help patient reschedule their appointment',
    category: 'healthcare',
    type: 'FUNCTION',
    function: {
      name: 'reschedule_patient_appointment',
      description: 'Help patient reschedule their appointment',
      parameters: {
        type: 'object',
        properties: {
          current_appointment_id: { type: 'string' },
          preferred_date: { type: 'string' },
          preferred_time: { type: 'string' },
          reason: { type: 'string' },
        },
        required: ['current_appointment_id', 'preferred_date'],
      },
    },
  },
  {
    name: 'Provide Prep Instructions',
    description: 'Provide appointment preparation instructions to patients',
    category: 'healthcare',
    type: 'FUNCTION',
    function: {
      name: 'provide_prep_instructions',
      description: 'Provide appointment preparation instructions',
      parameters: {
        type: 'object',
        properties: {
          appointment_type: { type: 'string' },
          instruction_type: {
            type: 'string',
            enum: ['fasting', 'medications', 'documents', 'general'],
          },
          delivery_method: { type: 'string', enum: ['verbal', 'text', 'email'] },
        },
        required: ['appointment_type', 'instruction_type'],
      },
    },
  },
  {
    name: 'Check Insurance Verification',
    description: 'Check insurance verification status for patient appointment',
    category: 'healthcare',
    type: 'FUNCTION',
    function: {
      name: 'check_insurance_verification',
      description: 'Check insurance verification status',
      parameters: {
        type: 'object',
        properties: {
          patient_id: { type: 'string' },
          appointment_id: { type: 'string' },
        },
        required: ['patient_id', 'appointment_id'],
      },
    },
  },
  {
    name: 'Request Transportation Assistance',
    description: 'Request transportation assistance for patient appointment',
    category: 'healthcare',
    type: 'FUNCTION',
    function: {
      name: 'request_transportation_assistance',
      description: 'Request transportation assistance for appointment',
      parameters: {
        type: 'object',
        properties: {
          appointment_id: { type: 'string' },
          transportation_type: {
            type: 'string',
            enum: ['medical_transport', 'rideshare', 'family'],
          },
          special_needs: { type: 'string' },
        },
        required: ['appointment_id', 'transportation_type'],
      },
    },
  },
];

// ─── Common utility tools ────────────────────────────────────────────

const commonTemplates: ToolTemplate[] = [
  {
    name: 'Schedule Callback',
    description: 'Schedule a callback for further discussion',
    category: 'scheduling',
    type: 'FUNCTION',
    function: {
      name: 'schedule_callback',
      description: 'Schedule a callback for further discussion',
      parameters: {
        type: 'object',
        properties: {
          preferred_time: { type: 'string' },
          reason: { type: 'string' },
          urgency: { type: 'string', enum: ['low', 'medium', 'high'] },
          department: { type: 'string' },
        },
        required: ['preferred_time', 'reason'],
      },
    },
  },
  {
    name: 'Escalate to Supervisor',
    description: 'Transfer complex cases or disputes to human supervisors',
    category: 'finance',
    type: 'FUNCTION',
    function: {
      name: 'escalate_to_supervisor',
      description: 'Transfer complex cases or disputes to human supervisors',
      parameters: {
        type: 'object',
        properties: {
          account_number: { type: 'string' },
          escalation_reason: {
            type: 'string',
            enum: ['complex_dispute', 'customer_request', 'legal_threat', 'hardship_verification', 'large_settlement'],
          },
          customer_mood: {
            type: 'string',
            enum: ['cooperative', 'frustrated', 'angry', 'confused'],
          },
          context_summary: { type: 'string' },
          urgent: { type: 'boolean' },
        },
        required: ['account_number', 'escalation_reason', 'context_summary'],
      },
    },
  },
];

// ─── Aggregate all templates ─────────────────────────────────────────

export const TOOL_TEMPLATES: readonly ToolTemplate[] = [
  ...schedulingTemplates,
  ...salesTemplates,
  ...financeTemplates,
  ...retentionTemplates,
  ...surveyTemplates,
  ...marketingTemplates,
  ...insuranceTemplates,
  ...healthcareTemplates,
  ...commonTemplates,
];

export function getTemplatesByCategory(): Record<ToolTemplateCategory, ToolTemplate[]> {
  const grouped: Record<string, ToolTemplate[]> = {};
  for (const template of TOOL_TEMPLATES) {
    if (!grouped[template.category]) {
      grouped[template.category] = [];
    }
    grouped[template.category].push(template);
  }
  return grouped as Record<ToolTemplateCategory, ToolTemplate[]>;
}

export function getTemplateByFunctionName(functionName: string): ToolTemplate | undefined {
  return TOOL_TEMPLATES.find((t) => t.function.name === functionName);
}

export function getTemplatesByNames(names: string[]): ToolTemplate[] {
  return TOOL_TEMPLATES.filter((t) => names.includes(t.function.name));
}
