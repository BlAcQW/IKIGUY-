/**
 * Comprehensive Automation Templates Configuration
 * 
 * This file contains all automation templates mapped from @apps/shared/modules/
 * capabilities with proper integration categories and provider selection.
 */

export interface IntegrationCategory {
  id: string;
  name: string;
  description: string;
  providers: IntegrationProvider[];
}

export interface IntegrationProvider {
  id: string;
  name: string;
  type: string;
  icon?: string;
}

export interface AutomationTemplate {
  id: string;
  name: string;
  description: string;
  industry: string;
  category: string;
  complexity: 'Simple' | 'Medium' | 'Advanced';
  estimatedTime: string;
  integrationCategories: string[];
  defaultIntegrations?: string[];
  workflow: WorkflowStep[];
  complianceFrameworks?: string[];
  features: string[];
  popular: boolean;
  rating: number;
  usageCount: number;
  // VAPI-specific configuration
  vapiConfig?: VAPITemplateConfig;
}

export interface VAPITemplateConfig {
  // Voice agent configuration
  voiceAgentEnabled: boolean;
  agentPersonality: {
    name: string;
    role: string;
    tone: 'professional' | 'friendly' | 'empathetic' | 'authoritative';
    expertise: string[];
  };

  // System prompt generation
  systemPromptTemplate: string;
  contextualKnowledge: string[];
  conversationStarters: string[];

  // Function generation from workflow
  autoGenerateFunctions: boolean;
  customFunctions?: VAPIFunction[];

  // Call handling
  callScenarios: {
    inbound: boolean;
    outbound: boolean;
    scenarios: string[];
  };

  // Integration with workflow
  webhookConfig: {
    triggerWorkflow: boolean;
    webhookEndpoint?: string;
    authRequired: boolean;
  };

  // Voice settings
  voiceSettings: {
    provider: 'openai' | '11labs' | 'azure';
    voiceId: string;
    model?: string;
    speed?: number;
    stability?: number;
    similarityBoost?: number;
    useSpeakerBoost?: boolean;
    optimizeStreamingLatency?: number;
  };

  // Conversation flow
  conversationFlow: {
    maxDuration: number;
    silenceTimeout: number;
    interruptible: boolean;
    endCallPhrases: string[];
  };
}

export interface VAPIFunction {
  name: string;
  description: string;
  parameters: {
    type: 'object';
    properties: Record<string, {
      type: string;
      description: string;
      enum?: string[];
    }>;
    required: string[];
  };
  workflowStepId?: string; // Links to workflow step
}

export interface WorkflowStep {
  id: string;
  name: string;
  type: 'integration' | 'condition' | 'transform' | 'delay' | 'notification';
  integrationCategory?: string;
  allowProviderSelection?: boolean;
  config: Record<string, any>;
  params?: Record<string, any>;
}

// Import Enhanced Templates
import ENHANCED_PRODUCT_LAUNCH_ANNOUNCEMENT_TEMPLATE from '../../../automations/campaigns/select-template/enhanced-product-launch-announcement';

// Integration Categories with Provider Selection
export const INTEGRATION_CATEGORIES: IntegrationCategory[] = [
  {
    id: 'messaging',
    name: 'Messaging',
    description: 'SMS, WhatsApp, and other messaging services',
    providers: [
      { id: 'vonage_sms', name: 'Vonage SMS', type: 'sms', icon: '📱' },
      { id: 'aws_sns', name: 'AWS SNS', type: 'sms', icon: '📨' },
      { id: 'telnyx_sms', name: 'Telnyx SMS', type: 'sms', icon: '💬' },
      { id: 'africas_talking', name: "Africa's Talking", type: 'sms', icon: '🌍' },
      { id: 'whatsapp_business', name: 'WhatsApp Business', type: 'whatsapp', icon: '💚' },
      { id: 'telegram', name: 'Telegram', type: 'telegram', icon: '✈️' },
    ]
  },
  {
    id: 'email',
    name: 'Email',
    description: 'Email sending and management services',
    providers: [
      { id: 'sendgrid', name: 'SendGrid', type: 'email', icon: '📧' },
      { id: 'mailgun', name: 'Mailgun', type: 'email', icon: '🔫' },
      { id: 'aws_ses', name: 'AWS SES', type: 'email', icon: '📮' },
      { id: 'gmail_api', name: 'Gmail API', type: 'email', icon: '📬' },
      { id: 'outlook_api', name: 'Outlook API', type: 'email', icon: '📭' },
      { id: 'smtp', name: 'SMTP', type: 'email', icon: '⚙️' },
    ]
  },
  {
    id: 'calendar',
    name: 'Calendar',
    description: 'Calendar and scheduling services',
    providers: [
      { id: 'google_calendar', name: 'Google Calendar', type: 'calendar', icon: '📅' },
      { id: 'outlook_calendar', name: 'Outlook Calendar', type: 'calendar', icon: '🗓️' },
      { id: 'calendly', name: 'Calendly', type: 'calendar', icon: '⏰' },
    ]
  },
  {
    id: 'crm',
    name: 'CRM',
    description: 'Customer relationship management systems',
    providers: [
      { id: 'pipedrive', name: 'Pipedrive', type: 'crm', icon: '🔄' },
      { id: 'freshsales', name: 'Freshsales', type: 'crm', icon: '🌿' },
      { id: 'zoho_crm', name: 'Zoho CRM', type: 'crm', icon: '🏢' },
      { id: 'microsoft_dynamics', name: 'Microsoft Dynamics', type: 'crm', icon: '🔷' },
    ]
  },
  {
    id: 'payment',
    name: 'Payment',
    description: 'Payment processing and financial services',
    providers: [
      { id: 'paystack', name: 'Paystack', type: 'payment', icon: '💳' },
      { id: 'flutterwave', name: 'Flutterwave', type: 'payment', icon: '🦋' },
      { id: 'mtn_mobile_money', name: 'MTN Mobile Money', type: 'payment', icon: '📱' },
      { id: 'quickbooks', name: 'QuickBooks', type: 'accounting', icon: '📊' },
    ]
  },
  {
    id: 'storage',
    name: 'Storage',
    description: 'File storage and document management',
    providers: [
      { id: 'google_drive', name: 'Google Drive', type: 'storage', icon: '💾' },
      { id: 'notion', name: 'Notion', type: 'storage', icon: '📝' },
      { id: 'confluence', name: 'Confluence', type: 'storage', icon: '📚' },
    ]
  },
  {
    id: 'support',
    name: 'Customer Support',
    description: 'Customer service and support platforms',
    providers: [
      { id: 'freshdesk', name: 'Freshdesk', type: 'support', icon: '🎫' },
      { id: 'zendesk', name: 'Zendesk', type: 'support', icon: '🎯' },
      { id: 'intercom', name: 'Intercom', type: 'support', icon: '💬' },
      { id: 'servicenow', name: 'ServiceNow', type: 'support', icon: '🛠️' },
    ]
  },
  {
    id: 'analytics',
    name: 'Analytics',
    description: 'Analytics and reporting platforms',
    providers: [
      { id: 'google_analytics', name: 'Google Analytics', type: 'analytics', icon: '📈' },
      { id: 'mixpanel', name: 'Mixpanel', type: 'analytics', icon: '🎛️' },
    ]
  },
  {
    id: 'database',
    name: 'Database',
    description: 'Database and data storage services',
    providers: [
      { id: 'mongodb', name: 'MongoDB', type: 'database', icon: '🗄️' },
      { id: 'postgresql', name: 'PostgreSQL', type: 'database', icon: '🐘' },
    ]
  },
  {
    id: 'automation',
    name: 'Workflow Automation',
    description: 'Workflow automation and integration platforms',
    providers: [
      { id: 'zapier', name: 'Zapier', type: 'automation', icon: '⚡' },
      { id: 'n8n', name: 'n8n', type: 'automation', icon: '🔗' },
      { id: 'make', name: 'Make (Integromat)', type: 'automation', icon: '🔧' },
    ]
  },
  {
    id: 'compliance',
    name: 'Compliance & Regulatory',
    description: 'Compliance monitoring and regulatory reporting',
    providers: [
      { id: 'regulatory_api', name: 'Regulatory API', type: 'compliance', icon: '📋' },
      { id: 'compliance_monitor', name: 'Compliance Monitor', type: 'compliance', icon: '🔍' },
      { id: 'audit_trail', name: 'Audit Trail', type: 'compliance', icon: '📊' },
    ]
  },
  {
    id: 'medical',
    name: 'Medical Services',
    description: 'Medical examination and health services integration',
    providers: [
      { id: 'medical_provider', name: 'Medical Provider Network', type: 'medical', icon: '🏥' },
      { id: 'exam_scheduler', name: 'Exam Scheduler', type: 'medical', icon: '📅' },
      { id: 'health_records', name: 'Health Records', type: 'medical', icon: '📋' },
    ]
  }
];

// Comprehensive Automation Templates for All Industries
export const AUTOMATION_TEMPLATES: AutomationTemplate[] = [
  // Healthcare Templates
  {
    id: 'patient_appointment_reminder',
    name: 'Enhanced Patient Appointment Reminders with VAPI + n8n',
    description: 'HIPAA-compliant voice-enabled appointment reminder system with AI-powered no-show prediction, intelligent scheduling optimization, patient engagement tracking, and comprehensive healthcare analytics',
    industry: 'healthcare',
    category: 'Patient Management',
    complexity: 'Advanced',
    estimatedTime: '35 min',
    integrationCategories: ['automation', 'calendar', 'messaging', 'database', 'analytics', 'compliance'],
    defaultIntegrations: ['n8n', 'vapi', 'healthcare.ehr_system', 'healthcare.appointment_scheduling', 'healthcare.patient_communication'],
    workflow: [
      {
        id: 'appointment_reminder_trigger',
        name: 'VAPI Appointment Reminder Call',
        type: 'integration',
        integrationCategory: 'automation',
        config: {
          tool: 'VAPI Voice Agent',
          action: 'initiate_reminder_call',
          n8n_webhook_trigger: true,
          monitoring_enabled: true,
          hipaa_compliant: true,
          description: 'Professional voice agent delivers personalized appointment reminders'
        }
      },
      {
        id: 'validate_patient_data',
        name: 'Validate Patient Information',
        type: 'integration',
        integrationCategory: 'database',
        config: {
          capability: 'patient_verification',
          action: 'validate_patient_identity',
          n8n_node: 'Function',
          hipaa_compliance: true,
          validation_rules: ['patient_id', 'appointment_id', 'contact_preferences'],
          phi_protection: true
        }
      },
      {
        id: 'assess_no_show_risk',
        name: 'AI-Powered No-Show Risk Assessment',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'predictive_analytics',
          action: 'calculate_no_show_probability',
          n8n_node: 'OpenAI GPT-4',
          ml_model: 'appointment_prediction_v2',
          risk_factors: ['history', 'timing', 'weather', 'demographics'],
          cost_tracking: true
        }
      },
      {
        id: 'personalize_reminder_message',
        name: 'Personalize Reminder Content',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'message_personalization',
          action: 'generate_personalized_reminder',
          n8n_node: 'OpenAI GPT-4',
          personalization_factors: ['appointment_type', 'provider', 'prep_instructions'],
          language_preferences: true
        }
      },
      {
        id: 'deliver_personalized_reminder',
        name: 'Deliver Personalized Reminder',
        type: 'condition',
        config: {
          condition: 'no_show_risk > 0.6 OR patient_preference == \"detailed_reminder\"',
          n8n_node: 'IF Conditional',
          routing_logic: {
            'high_risk': 'detailed_reminder_with_benefits',
            'standard_risk': 'standard_reminder',
            'low_risk': 'brief_confirmation'
          }
        }
      },
      {
        id: 'offer_reschedule_options',
        name: 'Offer Reschedule if Needed',
        type: 'integration',
        integrationCategory: 'calendar',
        config: {
          capability: 'appointment_rescheduling',
          action: 'provide_reschedule_options',
          n8n_node: 'Calendar Integration',
          availability_check: true,
          provider_schedule_sync: true
        }
      },
      {
        id: 'send_prep_instructions',
        name: 'Send Appointment Prep Instructions',
        type: 'integration',
        integrationCategory: 'messaging',
        config: {
          capability: 'patient_education',
          action: 'send_prep_instructions',
          n8n_node: 'Multi-Channel Notification',
          instruction_types: ['fasting', 'medications', 'documents', 'arrival_time'],
          multimedia_support: true
        }
      },
      {
        id: 'confirm_attendance',
        name: 'Confirm Patient Attendance',
        type: 'integration',
        integrationCategory: 'database',
        config: {
          capability: 'attendance_tracking',
          action: 'record_confirmation_status',
          n8n_node: 'HTTP Request',
          confirmation_types: ['confirmed', 'rescheduled', 'cancelled', 'no_response'],
          provider_notification: true
        }
      },
      {
        id: 'hipaa_audit_logging',
        name: 'HIPAA Compliance Audit Logging',
        type: 'integration',
        integrationCategory: 'compliance',
        config: {
          capability: 'hipaa_compliance',
          action: 'log_phi_access',
          n8n_node: 'HTTP Request',
          audit_requirements: ['access_log', 'data_usage', 'consent_tracking'],
          retention_policy: '6_years'
        }
      },
      {
        id: 'track_patient_engagement',
        name: 'Track Patient Engagement Metrics',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'engagement_analytics',
          action: 'record_interaction_metrics',
          n8n_node: 'HTTP Request',
          metrics: ['response_rate', 'satisfaction', 'compliance'],
          hipaa_anonymized: true
        }
      }
    ],
    vapiConfig: {
      voiceAgentEnabled: true,
      agentPersonality: {
        name: 'Appointment Reminder Assistant',
        role: 'Healthcare Appointment Coordinator',
        tone: 'professional',
        expertise: [
          'Appointment scheduling',
          'Patient communication',
          'Medical prep instructions',
          'HIPAA compliance',
          'Healthcare customer service'
        ],
        complianceGuidelines: [
          'Always maintain HIPAA compliance and patient confidentiality',
          'Use professional, caring, and empathetic tone',
          'Verify patient identity before discussing appointment details',
          'Provide clear appointment information (date, time, location, provider)',
          'Offer preparation instructions when relevant',
          'Be flexible with rescheduling needs',
          'Respect patient communication preferences'
        ]
      },
      customFunctions: [
        {
          name: 'confirmAppointment',
          description: 'Confirm patient attendance for upcoming appointment',
          parameters: {
            type: 'object',
            properties: {
              appointmentId: { type: 'string' },
              confirmationStatus: { type: 'string', enum: ['confirmed', 'needs_reschedule', 'cancel'] },
              notes: { type: 'string' }
            },
            required: ['appointmentId', 'confirmationStatus']
          }
        },
        {
          name: 'rescheduleAppointment',
          description: 'Help patient reschedule their appointment',
          parameters: {
            type: 'object',
            properties: {
              currentAppointmentId: { type: 'string' },
              preferredDate: { type: 'string' },
              preferredTime: { type: 'string' },
              reason: { type: 'string' }
            },
            required: ['currentAppointmentId', 'preferredDate']
          }
        },
        {
          name: 'providePrepInstructions',
          description: 'Provide appointment preparation instructions',
          parameters: {
            type: 'object',
            properties: {
              appointmentType: { type: 'string' },
              instructionType: { type: 'string', enum: ['fasting', 'medications', 'documents', 'general'] },
              deliveryMethod: { type: 'string', enum: ['verbal', 'text', 'email'] }
            },
            required: ['appointmentType', 'instructionType']
          }
        },
        {
          name: 'checkInsuranceVerification',
          description: 'Check insurance verification status',
          parameters: {
            type: 'object',
            properties: {
              patientId: { type: 'string' },
              appointmentId: { type: 'string' }
            },
            required: ['patientId', 'appointmentId']
          }
        },
        {
          name: 'updateContactPreferences',
          description: 'Update patient communication preferences',
          parameters: {
            type: 'object',
            properties: {
              preferredMethod: { type: 'string', enum: ['phone', 'text', 'email', 'portal'] },
              timePreference: { type: 'string' },
              language: { type: 'string' }
            },
            required: ['preferredMethod']
          }
        }
      ],
      webhookConfig: {
        n8nWebhookUrl: '{{n8n_instance_url}}/webhook/patient-appointment-reminders-enhanced',
        monitoringWebhookUrl: '{{api_base_url}}/api/monitoring/webhook/vapi-call',
        hipaaAuditWebhookUrl: '{{api_base_url}}/api/compliance/webhook/hipaa-audit'
      },
      monitoringIntegration: {
        realTimeMetrics: [
          'reminder_delivery_rate',
          'appointment_confirmation_rate',
          'no_show_reduction',
          'patient_satisfaction',
          'rescheduling_rate',
          'compliance_score'
        ],
        alertThresholds: {
          hipaa_violation: 'immediate',
          high_no_show_rate: 0.2,
          low_patient_satisfaction: 3.5
        }
      }
    },
    complianceFrameworks: ['HIPAA', 'SOC2', 'GDPR', 'State Healthcare Regulations'],
    features: [
      'HIPAA-Compliant VAPI Voice Agent',
      'AI-Powered No-Show Prediction',
      'Personalized Reminder Content',
      'Multi-Channel Communication',
      'Intelligent Rescheduling Options',
      'Appointment Prep Instructions',
      'Patient Engagement Tracking',
      'Real-time Provider Schedule Updates',
      'Compliance Audit Logging',
      'Healthcare Analytics Dashboard'
    ],
    specializedServices: {
      monitoringService: 'AppointmentMonitoringService',
      analyticsService: 'HealthcareAnalyticsService',
      complianceService: 'HIPAAComplianceService',
      predictionService: 'NoShowPredictionService'
    },
    popular: true,
    rating: 4.9,
    usageCount: 1534
  },
  {
    id: 'prescription_refill_automation',
    name: 'Prescription Refill Automation',
    description: 'Automatically notify patients when prescriptions are ready for pickup or renewal',
    industry: 'healthcare',
    category: 'Medication Management',
    complexity: 'Medium',
    estimatedTime: '25 min',
    integrationCategories: ['messaging', 'email', 'database'],
    workflow: [
      {
        id: 'check_prescriptions',
        name: 'Check Prescription Status',
        type: 'integration',
        integrationCategory: 'database',
        config: { query: 'prescription_ready_for_pickup' }
      },
      {
        id: 'notify_patient',
        name: 'Notify Patient',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'prescription_ready' }
      },
      {
        id: 'schedule_followup',
        name: 'Schedule Follow-up',
        type: 'integration',
        integrationCategory: 'calendar',
        config: { delay: '3_days' }
      }
    ],
    complianceFrameworks: ['HIPAA', 'FDA'],
    features: ['Pharmacy integration', 'Patient notifications', 'Automated follow-up', 'Compliance tracking'],
    popular: true,
    rating: 4.7,
    usageCount: 980
  },

  // Financial Templates
  {
    id: 'payment_reminder_automation',
    name: 'Payment Due Reminders',
    description: 'Automated reminders for loan payments, credit cards, and bill due dates',
    industry: 'financial',
    category: 'Collections',
    complexity: 'Simple',
    estimatedTime: '10 min',
    integrationCategories: ['messaging', 'email', 'payment'],
    workflow: [
      {
        id: 'check_overdue',
        name: 'Check Overdue Payments',
        type: 'integration',
        integrationCategory: 'payment',
        allowProviderSelection: true,
        config: { query: 'overdue_payments' }
      },
      {
        id: 'send_reminder',
        name: 'Send Payment Reminder',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'payment_reminder' }
      },
      {
        id: 'escalate_if_needed',
        name: 'Escalate if No Response',
        type: 'condition',
        config: { condition: 'no_response_48h', action: 'escalate' }
      }
    ],
    complianceFrameworks: ['PCI DSS', 'GDPR'],
    features: ['Payment tracking', 'Multi-channel reminders', 'Escalation workflow', 'Compliance reporting'],
    popular: true,
    rating: 4.9,
    usageCount: 2100
  },
  {
    id: 'fraud_detection_alerts',
    name: 'Fraud Detection Alerts',
    description: 'Instantly notify customers of suspicious account activity',
    industry: 'financial',
    category: 'Security',
    complexity: 'Advanced',
    estimatedTime: '35 min',
    integrationCategories: ['messaging', 'email', 'analytics'],
    workflow: [
      {
        id: 'monitor_transactions',
        name: 'Monitor Transaction Patterns',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { model: 'fraud_detection' }
      },
      {
        id: 'evaluate_risk',
        name: 'Evaluate Risk Score',
        type: 'condition',
        config: { threshold: 0.8 }
      },
      {
        id: 'send_alert',
        name: 'Send Fraud Alert',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { priority: 'high', template: 'fraud_alert' }
      }
    ],
    complianceFrameworks: ['PCI DSS', 'AML', 'SOX'],
    features: ['Real-time monitoring', 'AI-powered detection', 'Instant alerts', 'Compliance reporting'],
    popular: true,
    rating: 4.8,
    usageCount: 1800
  },

  // Retail Templates
  {
    id: 'order_status_updates',
    name: 'Order Status Updates',
    description: 'Keep customers informed about their order status from purchase to delivery',
    industry: 'retail',
    category: 'Order Management',
    complexity: 'Simple',
    estimatedTime: '12 min',
    integrationCategories: ['messaging', 'email', 'crm'],
    workflow: [
      {
        id: 'track_order_status',
        name: 'Track Order Status Changes',
        type: 'integration',
        integrationCategory: 'crm',
        allowProviderSelection: true,
        config: { webhook: 'order_status_change' }
      },
      {
        id: 'send_update',
        name: 'Send Status Update',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'order_status_update' }
      }
    ],
    complianceFrameworks: ['GDPR', 'CCPA'],
    features: ['Real-time updates', 'Multi-channel notifications', 'Order tracking', 'Customer satisfaction'],
    popular: true,
    rating: 4.7,
    usageCount: 3200
  },
  {
    id: 'abandoned_cart_recovery',
    name: 'Abandoned Cart Recovery',
    description: 'Re-engage customers who left items in their cart with personalized follow-ups',
    industry: 'retail',
    category: 'Sales Recovery',
    complexity: 'Medium',
    estimatedTime: '25 min',
    integrationCategories: ['messaging', 'email', 'analytics'],
    workflow: [
      {
        id: 'detect_abandonment',
        name: 'Detect Cart Abandonment',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { trigger: 'cart_abandoned_30min' }
      },
      {
        id: 'wait_period',
        name: 'Wait 1 Hour',
        type: 'delay',
        config: { duration: '1h' }
      },
      {
        id: 'send_recovery_message',
        name: 'Send Recovery Message',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'cart_recovery', personalization: true }
      }
    ],
    features: ['Behavioral triggers', 'Personalized messaging', 'Revenue recovery', 'A/B testing'],
    popular: true,
    rating: 4.8,
    usageCount: 2800
  },

  // Manufacturing Templates
  {
    id: 'production_workflow_automation',
    name: 'Production Workflow Automation',
    description: 'Automate production planning, scheduling, and execution monitoring',
    industry: 'manufacturing',
    category: 'Production Management',
    complexity: 'Advanced',
    estimatedTime: '45 min',
    integrationCategories: ['database', 'messaging', 'analytics'],
    workflow: [
      {
        id: 'plan_production',
        name: 'Plan Production Schedule',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'generate_production_plan' }
      },
      {
        id: 'schedule_resources',
        name: 'Schedule Resources',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'allocate_resources' }
      },
      {
        id: 'monitor_execution',
        name: 'Monitor Production Execution',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { dashboard: 'production_monitoring' }
      },
      {
        id: 'notify_completion',
        name: 'Notify on Completion',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'production_complete' }
      }
    ],
    complianceFrameworks: ['ISO 9001', 'OSHA'],
    features: ['Resource optimization', 'Real-time monitoring', 'Quality tracking', 'Compliance reporting'],
    popular: false,
    rating: 4.6,
    usageCount: 345
  },
  {
    id: 'quality_control_workflow',
    name: 'Quality Control Workflow',
    description: 'Automated quality inspection, testing, and approval process',
    industry: 'manufacturing',
    category: 'Quality Management',
    complexity: 'Medium',
    estimatedTime: '30 min',
    integrationCategories: ['database', 'messaging', 'storage'],
    workflow: [
      {
        id: 'schedule_inspection',
        name: 'Schedule Quality Inspection',
        type: 'integration',
        integrationCategory: 'database',
        config: { trigger: 'production_batch_complete' }
      },
      {
        id: 'conduct_tests',
        name: 'Conduct Quality Tests',
        type: 'integration',
        integrationCategory: 'database',
        config: { checklist: 'quality_standards' }
      },
      {
        id: 'document_results',
        name: 'Document Results',
        type: 'integration',
        integrationCategory: 'storage',
        allowProviderSelection: true,
        config: { folder: 'quality_reports' }
      },
      {
        id: 'notify_stakeholders',
        name: 'Notify Stakeholders',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'quality_report' }
      }
    ],
    complianceFrameworks: ['ISO 9001', 'FDA'],
    features: ['Automated testing', 'Compliance tracking', 'Document management', 'Stakeholder notifications'],
    popular: false,
    rating: 4.5,
    usageCount: 267
  },

  // Insurance Templates
  {
    id: 'claims_processing_automation',
    name: 'AI-Powered Claims Processing with VAPI + n8n',
    description: 'Complete end-to-end claims processing automation with VAPI voice agent, n8n workflow orchestration, real-time monitoring, fraud detection, and automated settlement - based on n8n template #7849',
    industry: 'insurance',
    category: 'Claims Management',
    complexity: 'Advanced',
    estimatedTime: '45 min',
    integrationCategories: ['database', 'messaging', 'analytics', 'storage', 'automation'],
    defaultIntegrations: ['n8n', 'vlm_run', 'google_drive', 'google_sheets', 'insurance.fraud_detection'],
    workflow: [
      {
        id: 'vapi_call_trigger',
        name: 'VAPI Call Trigger',
        type: 'integration',
        integrationCategory: 'automation',
        config: {
          tool: 'VAPI Voice Agent',
          action: 'receive_call',
          n8n_webhook_trigger: true,
          monitoring_enabled: true,
          description: 'Customer calls VAPI agent to file or check claim status'
        }
      },
      {
        id: 'intake_claim',
        name: 'Intake Claim Information',
        type: 'integration',
        integrationCategory: 'database',
        config: {
          capability: 'claims_processing',
          action: 'intake_claim',
          n8n_node: 'HTTP Request',
          monitoring_webhook: true,
          automation_health_tracking: true
        }
      },
      {
        id: 'document_extraction',
        name: 'Extract Documents with VLM',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'vlm_document_processing',
          action: 'extract_claim_documents',
          n8n_node: 'VLM Run',
          cost_tracking: true
        }
      },
      {
        id: 'analyze_claim',
        name: 'Analyze for Fraud with AI',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'fraud_detection',
          action: 'analyze',
          n8n_node: 'OpenAI GPT-4',
          ai_cost_tracking: true,
          performance_metrics: true
        }
      },
      {
        id: 'review_claim',
        name: 'Review Claim Details',
        type: 'integration',
        integrationCategory: 'database',
        config: {
          capability: 'claims_processing',
          action: 'review_claim',
          n8n_node: 'Google Sheets',
          data_validation: true
        }
      },
      {
        id: 'notify_customer',
        name: 'Send Multi-Channel Status Update',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: {
          capability: 'customer_communication',
          message_type: 'status_update',
          n8n_node: 'Multi-Channel Notification',
          delivery_tracking: true
        }
      },
      {
        id: 'conditional_approval',
        name: 'Conditional Auto-Approval',
        type: 'condition',
        config: {
          condition: 'fraud_score < 0.3 AND claim_amount < auto_approval_limit',
          n8n_node: 'IF Conditional',
          business_rules_engine: true
        }
      },
      {
        id: 'process_settlement',
        name: 'Process Settlement Payment',
        type: 'integration',
        integrationCategory: 'payment',
        allowProviderSelection: true,
        config: {
          capability: 'claims_processing',
          action: 'settle_claim',
          n8n_node: 'Payment API',
          transaction_monitoring: true,
          compliance_logging: true
        }
      },
      {
        id: 'update_monitoring',
        name: 'Update Automation Health',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'monitoring_service',
          action: 'record_metrics',
          n8n_node: 'Webhook',
          real_time_dashboard: true
        }
      }
    ],
    complianceFrameworks: ['NAIC', 'GLBA', 'State Insurance Regulations'],
    features: [
      'VAPI Voice Agent Integration',
      'n8n Workflow Orchestration',
      'Real-time Monitoring & Analytics',
      'AI-Powered Fraud Detection',
      'Automated Settlement Processing',
      'Multi-channel Customer Communication',
      'Compliance Tracking & Reporting',
      'Call Recording & Sentiment Analysis',
      'VLM Document Processing',
      'Conditional Auto-Approval',
      'Performance Metrics Dashboard'
    ],
    popular: true,
    rating: 4.6,
    usageCount: 1456,
    vapiConfig: {
      voiceAgentEnabled: true,
      agentPersonality: {
        name: 'Claims Assistant',
        role: 'Insurance Claims Specialist',
        tone: 'empathetic',
        expertise: ['Claims processing', 'Insurance policies', 'Documentation requirements', 'Fraud detection']
      },
      systemPromptTemplate: `You are a professional insurance claims assistant for {{companyName}}. Your role is to help customers with filing claims, checking claim status, and answering questions about their coverage.

Key responsibilities:
1. Collect complete claim information (name, policy number, claim type, description, amount)
2. Verify customer identity using policy details
3. Provide claim status updates using real-time data
4. Schedule callbacks for complex issues
5. Answer coverage questions within policy guidelines
6. Guide customers through required documentation

Always:
- Be empathetic and professional, especially during difficult situations
- Speak clearly and at a moderate pace
- Confirm important details by repeating them back
- Offer to repeat information if needed
- Provide claim reference numbers for tracking
- Set clear expectations about processing times (typically 3-5 business days, urgent claims within 24 hours)

Never:
- Make promises about claim approval amounts
- Share other customers' information
- Provide medical or legal advice
- Discuss specific coverage amounts without proper verification

For urgent medical situations, immediately advise calling 911.`,
      contextualKnowledge: [
        'Claims processing takes 3-5 business days typically',
        'Urgent claims are processed within 24 hours',
        'Required documents vary by claim type',
        'Fraud detection is automatic for all claims',
        'Settlement calculations use AI analysis',
        'All calls are recorded for quality assurance'
      ],
      conversationStarters: [
        'Hello, thank you for calling our claims department. I can help you file a new claim, check existing claim status, or answer coverage questions. How may I assist you today?',
        'Good morning! I\'m your automated claims assistant. I can process new claims, provide status updates, or help with documentation. What can I help you with?'
      ],
      autoGenerateFunctions: true,
      customFunctions: [
        {
          name: 'fileNewClaim',
          description: 'File a new insurance claim with complete information',
          parameters: {
            type: 'object',
            properties: {
              customerName: { type: 'string', description: 'Full name of the customer' },
              policyNumber: { type: 'string', description: 'Insurance policy number' },
              claimType: {
                type: 'string',
                enum: ['auto', 'home', 'health', 'life', 'property'],
                description: 'Type of insurance claim'
              },
              description: { type: 'string', description: 'Detailed description of the incident' },
              dateOfIncident: { type: 'string', description: 'Date when the incident occurred (YYYY-MM-DD)' },
              estimatedAmount: { type: 'number', description: 'Estimated claim amount in dollars' },
              urgent: { type: 'boolean', description: 'Whether this is an urgent claim requiring immediate attention' }
            },
            required: ['customerName', 'policyNumber', 'claimType', 'description', 'dateOfIncident']
          },
          workflowStepId: 'intake_claim'
        },
        {
          name: 'checkClaimStatus',
          description: 'Check the status of an existing insurance claim',
          parameters: {
            type: 'object',
            properties: {
              claimId: { type: 'string', description: 'The claim ID to check status for' },
              policyNumber: { type: 'string', description: 'Customer\'s policy number for verification' }
            },
            required: ['claimId']
          },
          workflowStepId: 'review_claim'
        },
        {
          name: 'scheduleCallback',
          description: 'Schedule a callback from a claims specialist for complex issues',
          parameters: {
            type: 'object',
            properties: {
              claimId: { type: 'string', description: 'Related claim ID if applicable' },
              customerPhone: { type: 'string', description: 'Phone number for callback' },
              preferredTime: { type: 'string', description: 'Preferred time for callback (e.g., "tomorrow morning", "this afternoon")' },
              reason: { type: 'string', description: 'Reason for requesting callback' }
            },
            required: ['customerPhone', 'preferredTime', 'reason']
          },
          workflowStepId: 'notify_customer'
        }
      ],
      callScenarios: {
        inbound: true,
        outbound: true,
        scenarios: [
          'Customer filing new claim',
          'Customer checking claim status',
          'Customer asking about coverage',
          'Customer requesting callback'
        ]
      },
      webhookConfig: {
        triggerWorkflow: true,
        authRequired: true,
        n8nWebhookUrl: '{{n8n_instance_url}}/webhook/claims-processing',
        monitoringWebhookUrl: '{{api_base_url}}/api/monitoring/webhook/vapi-call',
        realTimeAnalytics: true,
        callRecordingEnabled: true,
        sentimentAnalysisEnabled: true,
        customHeaders: {
          'X-Automation-ID': '{{automation_id}}',
          'X-Campaign-ID': '{{campaign_id}}',
          'X-Tenant-ID': '{{tenant_id}}'
        }
      },
      voiceSettings: {
        provider: '11labs',
        voiceId: 'bIHbv24MWmeRgasZH58o', // Professional female voice
        model: 'eleven_flash_v2_5',
        speed: 1.0,
        stability: 0.5,
        similarityBoost: 0.75,
        useSpeakerBoost: true,
        optimizeStreamingLatency: 3
      },
      conversationFlow: {
        maxDuration: 1800,
        silenceTimeout: 10,
        interruptible: true,
        endCallPhrases: [
          'Thank you for calling our claims department',
          'Your claim reference number has been sent to your phone',
          'Have a great day and take care'
        ]
      }
    }
  },
  {
    id: 'policy_renewal_automation',
    name: 'Smart Policy Renewal with GPT-4 Analysis',
    description: 'Advanced policy renewal automation with GPT-4 contract analysis, Slack approvals, and automated vendor outreach based on n8n template #6935',
    industry: 'insurance',
    category: 'Policy Management',
    complexity: 'Advanced',
    estimatedTime: '45 min',
    integrationCategories: ['database', 'messaging', 'email', 'analytics'],
    defaultIntegrations: ['google_sheets', 'slack', 'openai', 'gmail', 'insurance.risk_assessment'],
    workflow: [
      {
        id: 'check_expiring_policies',
        name: 'Check Expiring Policies',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'policy_management', action: 'check_renewal' }
      },
      {
        id: 'assess_risk',
        name: 'Assess Risk Profile',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'risk_assessment', action: 'assess' }
      },
      {
        id: 'generate_quote',
        name: 'Generate Renewal Quote',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'rate_quotes', action: 'generate' }
      },
      {
        id: 'send_renewal_notice',
        name: 'Send Renewal Notice',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { capability: 'customer_communication', message_type: 'renewal_reminder' }
      }
    ],
    complianceFrameworks: ['NAIC', 'State Insurance Regulations'],
    features: ['Risk assessment', 'Dynamic pricing', 'Automated notifications', 'Payment processing'],
    popular: false,
    rating: 4.4,
    usageCount: 789
  },
  {
    id: 'underwriting_automation',
    name: 'Underwriting Process Automation',
    description: 'Automated underwriting process with risk assessment and decision making',
    industry: 'insurance',
    category: 'Underwriting',
    complexity: 'Advanced',
    estimatedTime: '45 min',
    integrationCategories: ['database', 'analytics', 'messaging', 'storage'],
    defaultIntegrations: ['insurance.underwriting', 'insurance.risk_assessment'],
    workflow: [
      {
        id: 'receive_application',
        name: 'Receive Application',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'underwriting', action: 'review' }
      },
      {
        id: 'assess_risk',
        name: 'Assess Risk Profile',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'risk_assessment', action: 'assess' }
      },
      {
        id: 'request_documents',
        name: 'Request Additional Documents',
        type: 'integration',
        integrationCategory: 'messaging',
        config: { capability: 'customer_communication', message_type: 'additional_info_request' }
      },
      {
        id: 'finalize_decision',
        name: 'Finalize Decision',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'underwriting', action: 'finalize_decision' }
      },
      {
        id: 'notify_approval',
        name: 'Send Approval Notification',
        type: 'integration',
        integrationCategory: 'messaging',
        config: { capability: 'customer_communication', message_type: 'approval_notification' }
      }
    ],
    complianceFrameworks: ['NAIC', 'State Insurance Regulations', 'GLBA'],
    features: ['Risk assessment', 'Automated decision making', 'Document management', 'Customer communication'],
    popular: true,
    rating: 4.5,
    usageCount: 892
  },
  {
    id: 'fraud_detection_automation',
    name: 'Fraud Detection Automation',
    description: 'Advanced fraud detection and investigation workflow with AI-powered analysis',
    industry: 'insurance',
    category: 'Security & Fraud',
    complexity: 'Advanced',
    estimatedTime: '35 min',
    integrationCategories: ['analytics', 'database', 'messaging', 'compliance'],
    defaultIntegrations: ['insurance.fraud_detection', 'insurance.compliance_reporting'],
    workflow: [
      {
        id: 'analyze_patterns',
        name: 'Analyze Fraud Patterns',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'fraud_detection', action: 'analyze_patterns' }
      },
      {
        id: 'flag_suspicious',
        name: 'Flag Suspicious Claims',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'fraud_detection', action: 'flag_suspicious' }
      },
      {
        id: 'report_incident',
        name: 'Report Fraud Incident',
        type: 'integration',
        integrationCategory: 'compliance',
        config: { capability: 'compliance_reporting', action: 'report_fraud' }
      },
      {
        id: 'notify_investigation',
        name: 'Send Investigation Notice',
        type: 'integration',
        integrationCategory: 'messaging',
        config: { capability: 'customer_communication', message_type: 'investigation_notice' }
      }
    ],
    complianceFrameworks: ['NAIC', 'AML', 'State Fraud Regulations'],
    features: ['AI-powered detection', 'Pattern analysis', 'Automated reporting', 'Investigation workflow'],
    popular: true,
    rating: 4.7,
    usageCount: 1123
  },
  {
    id: 'premium_collection_automation',
    name: 'Enhanced Premium Collection with VAPI + n8n',
    description: 'Compassionate voice-enabled premium collection automation with AI-powered hardship assessment, flexible payment options, regulatory compliance, and real-time monitoring',
    industry: 'insurance',
    category: 'Financial Operations',
    complexity: 'Advanced',
    estimatedTime: '40 min',
    integrationCategories: ['automation', 'database', 'messaging', 'payment', 'analytics', 'compliance'],
    defaultIntegrations: ['n8n', 'vapi', 'insurance.billing_system', 'insurance.payment_processing', 'insurance.hardship_assessment'],
    workflow: [
      {
        id: 'vapi_collection_call',
        name: 'VAPI Premium Collection Call',
        type: 'integration',
        integrationCategory: 'automation',
        config: {
          tool: 'VAPI Voice Agent',
          action: 'initiate_collection_call',
          n8n_webhook_trigger: true,
          monitoring_enabled: true,
          compliance_recording: true,
          description: 'Empathetic voice agent initiates premium collection conversation'
        }
      },
      {
        id: 'validate_account_data',
        name: 'Validate Account Information',
        type: 'integration',
        integrationCategory: 'database',
        config: {
          capability: 'account_validation',
          action: 'verify_account_details',
          n8n_node: 'Function',
          validation_rules: ['policy_number', 'account_status', 'payment_history'],
          compliance_check: true
        }
      },
      {
        id: 'assess_financial_hardship',
        name: 'AI-Powered Hardship Assessment',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'hardship_analysis',
          action: 'assess_customer_situation',
          n8n_node: 'OpenAI GPT-4',
          assessment_criteria: ['employment_status', 'family_circumstances', 'medical_issues'],
          empathy_scoring: true,
          cost_tracking: true
        }
      },
      {
        id: 'determine_collection_strategy',
        name: 'Intelligent Collection Strategy',
        type: 'condition',
        config: {
          condition: 'hardship_score > 0.7 OR payment_history_score < 0.3',
          n8n_node: 'IF Conditional',
          strategy_matrix: {
            'high_hardship': 'compassionate_assistance',
            'good_history': 'gentle_reminder',
            'poor_history': 'structured_payment_plan',
            'default': 'standard_collection'
          }
        }
      },
      {
        id: 'offer_payment_assistance',
        name: 'Offer Financial Assistance Options',
        type: 'integration',
        integrationCategory: 'database',
        config: {
          capability: 'financial_assistance',
          action: 'generate_assistance_options',
          n8n_node: 'HTTP Request',
          options: ['payment_plan', 'grace_period', 'hardship_discount', 'policy_modification'],
          approval_workflow: true
        }
      },
      {
        id: 'process_payment_plan',
        name: 'Process Payment or Setup Plan',
        type: 'integration',
        integrationCategory: 'payment',
        config: {
          capability: 'payment_processing',
          action: 'handle_payment_solution',
          n8n_node: 'Payment Gateway',
          payment_methods: ['credit_card', 'bank_transfer', 'digital_wallet'],
          security_compliance: 'PCI_DSS',
          plan_creation: true
        }
      },
      {
        id: 'compliance_documentation',
        name: 'Regulatory Compliance Documentation',
        type: 'integration',
        integrationCategory: 'compliance',
        config: {
          capability: 'compliance_logging',
          action: 'document_collection_activity',
          n8n_node: 'HTTP Request',
          frameworks: ['FDCPA', 'TCPA', 'State_Collection_Laws'],
          call_recording: true,
          consent_tracking: true
        }
      },
      {
        id: 'schedule_follow_up',
        name: 'Schedule Intelligent Follow-up',
        type: 'integration',
        integrationCategory: 'automation',
        config: {
          capability: 'follow_up_scheduling',
          action: 'schedule_next_contact',
          n8n_node: 'Schedule Trigger',
          adaptive_timing: true,
          compliance_intervals: true
        }
      },
      {
        id: 'update_collection_analytics',
        name: 'Update Collection Analytics',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'collection_analytics',
          action: 'update_performance_metrics',
          n8n_node: 'HTTP Request',
          metrics: ['collection_rate', 'payment_plan_adherence', 'customer_retention'],
          real_time_dashboard: true
        }
      }
    ],
    vapiConfig: {
      voiceAgentEnabled: true,
      agentPersonality: {
        name: 'Premium Collection Assistant',
        role: 'Financial Collections Specialist',
        tone: 'empathetic',
        expertise: [
          'Payment assistance',
          'Financial hardship assessment',
          'Payment plan creation',
          'Debt collection regulations',
          'Customer retention strategies'
        ],
        complianceGuidelines: [
          'Always approach with empathy and understanding',
          'Listen actively to customer circumstances',
          'Offer solutions before discussing consequences',
          'Comply with all debt collection regulations (FDCPA, TCPA)',
          'Focus on customer retention and relationship preservation',
          'Never make threats or use aggressive language'
        ]
      },
      customFunctions: [
        {
          name: 'checkAccountBalance',
          description: 'Check current account balance and payment history',
          parameters: {
            type: 'object',
            properties: {
              policyNumber: { type: 'string' },
              includeHistory: { type: 'boolean', default: true }
            },
            required: ['policyNumber']
          }
        },
        {
          name: 'assessFinancialHardship',
          description: 'Assess customer financial hardship situation',
          parameters: {
            type: 'object',
            properties: {
              employmentStatus: { type: 'string', enum: ['employed', 'unemployed', 'reduced_hours', 'disability'] },
              householdChanges: { type: 'string' },
              medicalIssues: { type: 'boolean' },
              otherCircumstances: { type: 'string' }
            },
            required: ['employmentStatus']
          }
        },
        {
          name: 'createPaymentPlan',
          description: 'Create a customized payment plan for the customer',
          parameters: {
            type: 'object',
            properties: {
              totalAmount: { type: 'number' },
              numberOfPayments: { type: 'number' },
              frequency: { type: 'string', enum: ['weekly', 'bi-weekly', 'monthly'] },
              firstPaymentDate: { type: 'string' },
              downPayment: { type: 'number' }
            },
            required: ['totalAmount', 'numberOfPayments', 'frequency', 'firstPaymentDate']
          }
        },
        {
          name: 'processPayment',
          description: 'Process immediate payment using various methods',
          parameters: {
            type: 'object',
            properties: {
              amount: { type: 'number' },
              paymentMethod: { type: 'string', enum: ['credit_card', 'debit_card', 'bank_transfer', 'check'] },
              paymentDetails: { type: 'object' }
            },
            required: ['amount', 'paymentMethod']
          }
        },
        {
          name: 'requestHardshipAssistance',
          description: 'Request hardship assistance options for qualified customers',
          parameters: {
            type: 'object',
            properties: {
              assistanceType: { type: 'string', enum: ['payment_reduction', 'grace_period', 'policy_modification'] },
              duration: { type: 'string' },
              justification: { type: 'string' }
            },
            required: ['assistanceType', 'justification']
          }
        }
      ],
      webhookConfig: {
        n8nWebhookUrl: '{{n8n_instance_url}}/webhook/premium-collection-enhanced',
        monitoringWebhookUrl: '{{api_base_url}}/api/monitoring/webhook/vapi-call',
        complianceWebhookUrl: '{{api_base_url}}/api/compliance/webhook/collection-call'
      },
      monitoringIntegration: {
        realTimeMetrics: [
          'collection_rate',
          'payment_plan_setup_rate',
          'customer_satisfaction',
          'compliance_score',
          'hardship_assistance_rate',
          'call_resolution_rate'
        ],
        alertThresholds: {
          compliance_violation: 'immediate',
          low_collection_rate: 0.5,
          high_customer_complaints: 0.1
        }
      }
    },
    complianceFrameworks: ['FDCPA', 'TCPA', 'State Collection Laws', 'PCI DSS'],
    features: [
      'Empathetic VAPI Voice Agent',
      'AI-Powered Hardship Assessment',
      'Flexible Payment Plan Creation',
      'Real-time Payment Processing',
      'Regulatory Compliance Monitoring',
      'Customer Retention Focus',
      'Adaptive Follow-up Scheduling',
      'Performance Analytics Dashboard',
      'Compliance Documentation'
    ],
    specializedServices: {
      monitoringService: 'PremiumCollectionMonitoringService',
      analyticsService: 'CollectionAnalyticsService',
      complianceService: 'DebtCollectionComplianceService',
      paymentService: 'FlexiblePaymentProcessingService'
    },
    popular: true,
    rating: 4.8,
    usageCount: 1287
  },
  {
    id: 'medical_exam_scheduling',
    name: 'AI-Powered Medical Exam Scheduling with VAPI + n8n',
    description: 'Comprehensive voice-enabled medical examination scheduling automation with AI-powered patient interaction, intelligent scheduling optimization, real-time monitoring, and HIPAA-compliant workflow orchestration',
    industry: 'insurance',
    category: 'Medical Services',
    complexity: 'Advanced',
    estimatedTime: '45 min',
    integrationCategories: ['calendar', 'messaging', 'database', 'email', 'automation', 'analytics'],
    defaultIntegrations: ['n8n', 'google_calendar', 'calendly', 'insurance.medical_exam_scheduling', 'insurance.customer_communication'],
    workflow: [
      {
        id: 'vapi_call_trigger',
        name: 'VAPI Medical Scheduling Call',
        type: 'integration',
        integrationCategory: 'automation',
        config: {
          tool: 'VAPI Voice Agent',
          action: 'receive_call',
          n8n_webhook_trigger: true,
          monitoring_enabled: true,
          description: 'Patient calls to schedule medical examination'
        }
      },
      {
        id: 'patient_verification',
        name: 'Verify Patient Identity',
        type: 'integration',
        integrationCategory: 'database',
        config: {
          capability: 'patient_verification',
          action: 'verify_identity',
          n8n_node: 'HTTP Request',
          monitoring_webhook: true,
          hipaa_compliance: true
        }
      },
      {
        id: 'identify_requirements',
        name: 'AI-Powered Exam Requirements Analysis',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'underwriting',
          action: 'analyze_medical_requirements',
          n8n_node: 'OpenAI GPT-4',
          ai_cost_tracking: true,
          performance_metrics: true
        }
      },
      {
        id: 'check_availability',
        name: 'Real-time Availability Check',
        type: 'integration',
        integrationCategory: 'calendar',
        config: {
          capability: 'calendar_integration',
          action: 'check_availability',
          n8n_node: 'Google Calendar',
          real_time_sync: true
        }
      },
      {
        id: 'intelligent_scheduling',
        name: 'Intelligent Exam Scheduling',
        type: 'integration',
        integrationCategory: 'calendar',
        config: {
          capability: 'smart_scheduling',
          action: 'optimize_schedule',
          n8n_node: 'Calendly API',
          ai_optimization: true,
          location_matching: true
        }
      },
      {
        id: 'conditional_priority',
        name: 'Priority & Urgency Assessment',
        type: 'condition',
        config: {
          condition: 'patient_age > 65 OR medical_history_flags.high_risk OR exam_type == "urgent"',
          n8n_node: 'IF Conditional',
          business_rules_engine: true,
          priority_escalation: true
        }
      },
      {
        id: 'send_confirmation',
        name: 'Multi-Channel Confirmation',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: {
          capability: 'customer_communication',
          message_type: 'exam_confirmation',
          n8n_node: 'Multi-Channel Notification',
          delivery_tracking: true,
          hipaa_secure: true
        }
      },
      {
        id: 'prep_instructions',
        name: 'Send Personalized Prep Instructions',
        type: 'integration',
        integrationCategory: 'email',
        config: {
          capability: 'patient_education',
          action: 'send_prep_instructions',
          n8n_node: 'Email Template',
          personalization: true,
          exam_specific: true
        }
      },
      {
        id: 'automated_reminders',
        name: 'Smart Reminder Sequence',
        type: 'integration',
        integrationCategory: 'messaging',
        config: {
          capability: 'reminder_automation',
          action: 'schedule_reminders',
          n8n_node: 'Scheduler',
          multi_stage_reminders: true,
          behavioral_optimization: true
        }
      },
      {
        id: 'no_show_prediction',
        name: 'AI No-Show Risk Assessment',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'predictive_analytics',
          action: 'assess_no_show_risk',
          n8n_node: 'ML Model',
          risk_scoring: true,
          proactive_intervention: true
        }
      },
      {
        id: 'provider_notification',
        name: 'Notify Medical Provider Network',
        type: 'integration',
        integrationCategory: 'messaging',
        config: {
          capability: 'provider_communication',
          action: 'notify_providers',
          n8n_node: 'Slack/Teams',
          real_time_updates: true
        }
      },
      {
        id: 'update_monitoring',
        name: 'Update Scheduling Analytics',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'monitoring_service',
          action: 'record_scheduling_metrics',
          n8n_node: 'Webhook',
          real_time_dashboard: true,
          appointment_analytics: true
        }
      }
    ],
    complianceFrameworks: ['HIPAA', 'HITECH', 'State Insurance Regulations', 'Medical Privacy Standards'],
    features: [
      'VAPI Voice Agent Integration',
      'n8n Workflow Orchestration',
      'Real-time Monitoring & Analytics',
      'AI-Powered Exam Requirements Analysis',
      'Intelligent Scheduling Optimization',
      'Multi-channel Patient Communication',
      'HIPAA-Compliant Data Handling',
      'Call Recording & Sentiment Analysis',
      'Predictive No-Show Analytics',
      'Priority & Urgency Assessment',
      'Provider Network Integration',
      'Automated Reminder Sequences',
      'Performance Metrics Dashboard',
      'Cost Tracking & Optimization'
    ],
    popular: true,
    rating: 4.8,
    usageCount: 2156,
    vapiConfig: {
      voiceAgentEnabled: true,
      agentPersonality: {
        name: 'Medical Scheduling Assistant',
        role: 'Healthcare Appointment Coordinator',
        tone: 'professional',
        expertise: ['Medical scheduling', 'Insurance requirements', 'Patient care coordination', 'HIPAA compliance']
      },
      systemPromptTemplate: `You are a professional medical scheduling assistant for {{companyName}}. Your role is to help patients schedule medical examinations required for their life insurance applications while maintaining strict HIPAA compliance.

Key responsibilities:
1. Verify patient identity using policy and personal information
2. Explain medical exam requirements clearly and compassionately
3. Find optimal appointment times based on patient preferences and availability
4. Provide detailed preparation instructions for specific exam types
5. Schedule follow-up appointments if needed
6. Handle rescheduling and cancellation requests professionally

Always:
- Maintain strict patient confidentiality (HIPAA compliance)
- Speak clearly and at an appropriate pace for healthcare discussions
- Confirm all appointment details by repeating them back
- Explain the purpose and process of required medical exams
- Provide clear preparation instructions and timing requirements
- Offer multiple appointment options when available
- Be empathetic about patient concerns regarding medical exams

Never:
- Share any patient medical information with unauthorized parties
- Provide medical advice or interpret test results
- Make promises about insurance approval based on exam results
- Rush patients through important medical scheduling decisions
- Discuss other patients' appointments or information

For medical emergencies, immediately advise calling 911 or going to the nearest emergency room.`,
      contextualKnowledge: [
        'Medical exams typically take 30-90 minutes depending on requirements',
        'Fasting may be required for blood work (usually 8-12 hours)',
        'Most exams are completed within 2-3 weeks of scheduling',
        'Results are sent directly to the insurance company within 5-7 business days',
        'Common exams include: basic physical, blood work, EKG, stress test',
        'Age and coverage amount determine specific exam requirements',
        'Mobile exam services available for qualifying patients',
        'Rescheduling is allowed up to 24 hours before appointment'
      ],
      conversationStarters: [
        'Hello, thank you for calling our medical scheduling department. I can help you schedule your required life insurance medical examination. May I have your policy application number to get started?',
        'Good morning! I\'m your automated medical scheduling assistant. I can schedule exams, explain requirements, or help with rescheduling. How may I assist you with your medical examination today?'
      ],
      autoGenerateFunctions: true,
      customFunctions: [
        {
          name: 'scheduleExam',
          description: 'Schedule a medical examination appointment for life insurance',
          parameters: {
            type: 'object',
            properties: {
              patientName: { type: 'string', description: 'Full name of the patient' },
              policyNumber: { type: 'string', description: 'Life insurance policy application number' },
              dateOfBirth: { type: 'string', description: 'Patient date of birth (YYYY-MM-DD)' },
              examType: {
                type: 'string',
                enum: ['basic_physical', 'comprehensive_physical', 'blood_work_only', 'ekg', 'stress_test', 'full_medical'],
                description: 'Type of medical examination required'
              },
              preferredDate: { type: 'string', description: 'Preferred appointment date (YYYY-MM-DD)' },
              preferredTime: { type: 'string', description: 'Preferred time (e.g., "morning", "afternoon", "evening")' },
              location: { type: 'string', description: 'Preferred exam location or "mobile" for home visit' },
              specialRequirements: { type: 'string', description: 'Any special accommodation needs' }
            },
            required: ['patientName', 'policyNumber', 'dateOfBirth', 'examType']
          },
          workflowStepId: 'intelligent_scheduling'
        },
        {
          name: 'checkAppointmentStatus',
          description: 'Check the status of a scheduled medical examination',
          parameters: {
            type: 'object',
            properties: {
              appointmentId: { type: 'string', description: 'Medical exam appointment ID' },
              policyNumber: { type: 'string', description: 'Policy number for verification' },
              patientName: { type: 'string', description: 'Patient name for verification' }
            },
            required: ['appointmentId', 'policyNumber']
          },
          workflowStepId: 'check_availability'
        },
        {
          name: 'rescheduleAppointment',
          description: 'Reschedule an existing medical examination appointment',
          parameters: {
            type: 'object',
            properties: {
              appointmentId: { type: 'string', description: 'Current appointment ID to reschedule' },
              newPreferredDate: { type: 'string', description: 'New preferred date (YYYY-MM-DD)' },
              newPreferredTime: { type: 'string', description: 'New preferred time' },
              reason: { type: 'string', description: 'Reason for rescheduling' }
            },
            required: ['appointmentId', 'newPreferredDate']
          },
          workflowStepId: 'intelligent_scheduling'
        },
        {
          name: 'provideExamInstructions',
          description: 'Provide detailed preparation instructions for specific exam types',
          parameters: {
            type: 'object',
            properties: {
              examType: {
                type: 'string',
                enum: ['basic_physical', 'comprehensive_physical', 'blood_work_only', 'ekg', 'stress_test', 'full_medical'],
                description: 'Type of examination'
              },
              appointmentDate: { type: 'string', description: 'Scheduled appointment date' },
              patientAge: { type: 'number', description: 'Patient age for age-specific instructions' }
            },
            required: ['examType']
          },
          workflowStepId: 'prep_instructions'
        }
      ],
      callScenarios: {
        inbound: true,
        outbound: true,
        scenarios: [
          'Patient scheduling new medical exam',
          'Patient checking appointment status',
          'Patient rescheduling existing appointment',
          'Patient asking about exam requirements',
          'Patient requesting preparation instructions',
          'Patient inquiring about mobile exam services',
          'Provider calling about appointment updates'
        ]
      },
      webhookConfig: {
        triggerWorkflow: true,
        authRequired: true,
        n8nWebhookUrl: '{{n8n_instance_url}}/webhook/medical-exam-scheduling',
        monitoringWebhookUrl: '{{api_base_url}}/api/monitoring/webhook/vapi-call',
        realTimeAnalytics: true,
        callRecordingEnabled: true,
        sentimentAnalysisEnabled: true,
        hipaaCompliant: true,
        customHeaders: {
          'X-Automation-ID': '{{automation_id}}',
          'X-Campaign-ID': '{{campaign_id}}',
          'X-Tenant-ID': '{{tenant_id}}',
          'X-HIPAA-Compliant': 'true'
        }
      },
      voiceSettings: {
        provider: '11labs',
        voiceId: 'EXAVITQu4vr4xnSDxMaL', // Professional, calm female voice
        model: 'eleven_flash_v2_5',
        speed: 0.9,
        stability: 0.7,
        similarityBoost: 0.8,
        useSpeakerBoost: true,
        optimizeStreamingLatency: 2
      },
      conversationFlow: {
        maxDuration: 1200, // 20 minutes for medical scheduling
        silenceTimeout: 15,
        interruptible: true,
        endCallPhrases: [
          'Thank you for calling our medical scheduling department',
          'Your appointment confirmation has been sent to your email and phone',
          'Please call us if you have any questions before your exam',
          'Have a great day and we look forward to seeing you for your appointment'
        ]
      }
    }
  },
  {
    id: 'claim_appeal_processing',
    name: 'Claim Appeal Processing Automation',
    description: 'Automated claim appeal process with document review and decision workflow',
    industry: 'insurance',
    category: 'Appeals Management',
    complexity: 'Advanced',
    estimatedTime: '40 min',
    integrationCategories: ['database', 'storage', 'messaging', 'analytics'],
    defaultIntegrations: ['insurance.appeal_processing', 'insurance.document_management'],
    workflow: [
      {
        id: 'receive_appeal',
        name: 'Receive Appeal Request',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'appeal_processing', action: 'process' }
      },
      {
        id: 'review_documents',
        name: 'Review Supporting Documents',
        type: 'integration',
        integrationCategory: 'storage',
        config: { capability: 'document_management', action: 'verify' }
      },
      {
        id: 'conduct_review',
        name: 'Conduct Appeal Review',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'appeal_processing', action: 'review' }
      },
      {
        id: 'notify_decision',
        name: 'Notify Appeal Decision',
        type: 'integration',
        integrationCategory: 'messaging',
        config: { capability: 'customer_communication', message_type: 'appeal_decision' }
      }
    ],
    complianceFrameworks: ['NAIC', 'State Insurance Regulations', 'Fair Claims Settlement'],
    features: ['Document review', 'Appeal tracking', 'Decision workflow', 'Customer communication'],
    popular: false,
    rating: 4.4,
    usageCount: 234
  },
  {
    id: 'coverage_analysis_automation',
    name: 'Coverage Analysis & Recommendations',
    description: 'Automated coverage gap analysis with personalized recommendations',
    industry: 'insurance',
    category: 'Coverage Optimization',
    complexity: 'Medium',
    estimatedTime: '30 min',
    integrationCategories: ['analytics', 'database', 'messaging', 'crm'],
    defaultIntegrations: ['insurance.coverage_analysis', 'insurance.rate_quotes'],
    workflow: [
      {
        id: 'analyze_coverage',
        name: 'Analyze Current Coverage',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'coverage_analysis', action: 'analyze' }
      },
      {
        id: 'identify_gaps',
        name: 'Identify Coverage Gaps',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'coverage_analysis', action: 'identify_gaps' }
      },
      {
        id: 'generate_recommendations',
        name: 'Generate Recommendations',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'coverage_analysis', action: 'recommend' }
      },
      {
        id: 'send_recommendations',
        name: 'Send Recommendations',
        type: 'integration',
        integrationCategory: 'messaging',
        config: { capability: 'customer_communication', message_type: 'coverage_recommendations' }
      }
    ],
    complianceFrameworks: ['State Insurance Regulations', 'Fair Business Practices'],
    features: ['Gap analysis', 'Personalized recommendations', 'Quote generation', 'Customer engagement'],
    popular: true,
    rating: 4.5,
    usageCount: 678
  },
  {
    id: 'customer_service_automation',
    name: 'Enhanced Insurance Customer Service with VAPI + n8n',
    description: 'Advanced insurance customer service automation featuring intelligent voice agents, comprehensive case management, real-time monitoring, fraud detection integration, and regulatory compliance tracking',
    industry: 'insurance',
    category: 'Customer Service',
    complexity: 'Advanced',
    estimatedTime: '45 min',
    integrationCategories: ['automation', 'database', 'messaging', 'analytics', 'compliance'],
    defaultIntegrations: ['n8n', 'vapi', 'insurance.customer_database', 'insurance.case_management', 'insurance.fraud_detection'],
    workflow: [
      {
        id: 'vapi_call_trigger',
        name: 'VAPI Customer Service Call',
        type: 'integration',
        integrationCategory: 'automation',
        config: {
          tool: 'VAPI Voice Agent',
          action: 'receive_call',
          n8n_webhook_trigger: true,
          monitoring_enabled: true,
          real_time_analytics: true,
          description: 'Customer calls VAPI agent for insurance service inquiries'
        }
      },
      {
        id: 'validate_caller_data',
        name: 'Validate and Parse Call Data',
        type: 'integration',
        integrationCategory: 'automation',
        config: {
          capability: 'data_validation',
          action: 'validate_webhook_data',
          n8n_node: 'Function',
          validation_rules: ['policy_number', 'customer_name', 'call_metadata'],
          error_handling: true
        }
      },
      {
        id: 'customer_authentication',
        name: 'Authenticate Customer Identity',
        type: 'integration',
        integrationCategory: 'database',
        config: {
          capability: 'customer_authentication',
          action: 'verify_identity',
          n8n_node: 'HTTP Request',
          endpoint: '{{api_base_url}}/api/customers/authenticate',
          security_level: 'high',
          audit_trail: true
        }
      },
      {
        id: 'fraud_risk_assessment',
        name: 'Real-time Fraud Risk Assessment',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'fraud_detection',
          action: 'assess_call_risk',
          n8n_node: 'HTTP Request',
          ai_analysis: true,
          risk_scoring: true,
          alert_threshold: 0.7
        }
      },
      {
        id: 'create_service_case',
        name: 'Create Customer Service Case',
        type: 'integration',
        integrationCategory: 'database',
        config: {
          capability: 'case_management',
          action: 'create_case',
          n8n_node: 'HTTP Request',
          case_priority_rules: true,
          sla_tracking: true,
          automatic_routing: true
        }
      },
      {
        id: 'inquiry_classification',
        name: 'AI-Powered Inquiry Classification',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'nlp_classification',
          action: 'classify_inquiry',
          n8n_node: 'OpenAI GPT-4',
          classification_model: 'insurance_inquiries_v2',
          confidence_threshold: 0.8,
          cost_tracking: true
        }
      },
      {
        id: 'intelligent_routing',
        name: 'Intelligent Inquiry Routing',
        type: 'condition',
        config: {
          condition: 'inquiry_type IN ("claims", "billing", "policy_changes", "coverage_questions")',
          n8n_node: 'Switch',
          routing_algorithm: 'ai_optimized',
          load_balancing: true,
          expertise_matching: true
        }
      },
      {
        id: 'sentiment_analysis',
        name: 'Customer Sentiment Analysis',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'sentiment_analysis',
          action: 'analyze_call_sentiment',
          n8n_node: 'OpenAI GPT-4',
          real_time_tracking: true,
          escalation_triggers: ['negative', 'frustrated', 'angry']
        }
      },
      {
        id: 'compliance_logging',
        name: 'Regulatory Compliance Logging',
        type: 'integration',
        integrationCategory: 'compliance',
        config: {
          capability: 'compliance_audit',
          action: 'log_regulatory_data',
          n8n_node: 'HTTP Request',
          frameworks: ['NAIC', 'SOX', 'State_Regulations'],
          data_retention: '7_years',
          encryption: true
        }
      },
      {
        id: 'update_monitoring_analytics',
        name: 'Update Monitoring & Analytics',
        type: 'integration',
        integrationCategory: 'analytics',
        config: {
          capability: 'automation_monitoring',
          action: 'update_health_metrics',
          n8n_node: 'HTTP Request',
          endpoint: '{{api_base_url}}/api/monitoring/automation-health',
          real_time_dashboard: true
        }
      }
    ],
    complianceFrameworks: ['NAIC', 'SOX', 'State Regulations', 'GDPR'],
    features: [
      'Advanced VAPI Voice Agent',
      'Real-time Fraud Detection',
      'Intelligent Inquiry Routing',
      'AI-Powered Sentiment Analysis',
      'Automated Case Management',
      'SLA Monitoring & Tracking',
      'Regulatory Compliance Logging',
      'Customer Satisfaction Tracking',
      'Multi-Channel Communication',
      'Performance Analytics Dashboard'
    ],
    popular: true,
    rating: 4.8,
    usageCount: 1234,
    vapiConfig: {
      voiceAgentEnabled: true,
      agentPersonality: {
        name: 'Insurance Service Assistant',
        role: 'Customer Service Representative',
        tone: 'empathetic',
        expertise: ['Policy inquiries', 'Claims assistance', 'Billing support', 'Coverage explanations', 'Account management']
      },
      systemPromptTemplate: `You are a professional Insurance Service Assistant for {{companyName}}. Your role is to assist customers with policy inquiries, claims assistance, billing support, coverage explanations, and account management.

Key responsibilities:
1. Maintain a empathetic and helpful demeanor
2. Gather accurate information efficiently
3. Provide clear guidance and next steps
4. Escalate complex issues appropriately
5. Ensure compliance with NAIC, SOX, State Regulations

Important Guidelines:
- Always verify customer identity before discussing policy details
- Be empathetic when handling claims or complaints
- Escalate to human agents for complex policy changes
- Maintain detailed records of all interactions
- Follow NAIC guidelines for customer communications
- Identify potential fraud indicators and escalate appropriately
- Ensure regulatory compliance in all responses

Always verify customer identity before proceeding with sensitive information.`,
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
      customFunctions: [
        {
          name: 'lookupCustomerAccount',
          description: 'Look up customer account information using policy number',
          parameters: {
            type: 'object',
            properties: {
              policyNumber: { type: 'string' },
              verificationMethod: { type: 'string', enum: ['ssn', 'dob', 'security_question'] }
            },
            required: ['policyNumber', 'verificationMethod']
          }
        },
        {
          name: 'initiateClaimsProcess',
          description: 'Start the claims filing process for the customer',
          parameters: {
            type: 'object',
            properties: {
              claimType: { type: 'string', enum: ['auto', 'home', 'life', 'health'] },
              incidentDate: { type: 'string' },
              incidentDescription: { type: 'string' },
              estimatedAmount: { type: 'number' }
            },
            required: ['claimType', 'incidentDate', 'incidentDescription']
          }
        },
        {
          name: 'scheduleAgentCallback',
          description: 'Schedule a callback with a human agent for complex issues',
          parameters: {
            type: 'object',
            properties: {
              preferredTime: { type: 'string' },
              urgency: { type: 'string', enum: ['low', 'medium', 'high', 'urgent'] },
              department: { type: 'string', enum: ['claims', 'billing', 'underwriting', 'general'] },
              notes: { type: 'string' }
            },
            required: ['preferredTime', 'urgency', 'department']
          }
        }
      ],
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
        triggerWorkflow: true,
        n8nWebhookUrl: '{{n8n_instance_url}}/webhook/insurance-customer-service-enhanced',
        monitoringWebhookUrl: '{{api_base_url}}/api/monitoring/webhook/vapi-call',
        authRequired: true,
        realTimeAnalytics: true,
        sentimentAnalysisEnabled: true
      },
      voiceSettings: {
        provider: 'openai',
        voiceId: 'alloy',
        speed: 1.0,
        optimizeStreamingLatency: 2
      },
      conversationFlow: {
        maxDuration: 900,
        silenceTimeout: 30,
        interruptible: true,
        endCallPhrases: ['goodbye', 'thank you', 'end call', 'hang up'],
        escalationTriggers: ['speak to manager', 'escalate', 'complaint', 'frustrated']
      },
      monitoringConfig: {
        enabled: true,
        sentimentTracking: true,
        callRecording: true,
        transcriptionEnabled: true,
        analyticsWebhook: '{{api_base_url}}/api/monitoring/vapi-analytics',
        performanceMetrics: true
      }
    }
  },
  {
    id: 'compliance_reporting_automation',
    name: 'Insurance Compliance Reporting',
    description: 'Automated regulatory compliance reporting and documentation',
    industry: 'insurance',
    category: 'Compliance & Reporting',
    complexity: 'Advanced',
    estimatedTime: '45 min',
    integrationCategories: ['analytics', 'storage', 'database', 'compliance'],
    defaultIntegrations: ['insurance.compliance_reporting', 'insurance.document_management'],
    workflow: [
      {
        id: 'collect_data',
        name: 'Collect Compliance Data',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'compliance_reporting', action: 'collect_data' }
      },
      {
        id: 'generate_report',
        name: 'Generate Compliance Report',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'compliance_reporting', action: 'generate' }
      },
      {
        id: 'validate_report',
        name: 'Validate Report',
        type: 'integration',
        integrationCategory: 'compliance',
        config: { capability: 'compliance_reporting', action: 'validate_report' }
      },
      {
        id: 'submit_report',
        name: 'Submit to Regulatory Body',
        type: 'integration',
        integrationCategory: 'compliance',
        config: { capability: 'compliance_reporting', action: 'submit_report' }
      }
    ],
    complianceFrameworks: ['NAIC', 'State Insurance Regulations', 'Federal Compliance'],
    features: ['Data collection', 'Report generation', 'Validation checks', 'Automated submission'],
    popular: false,
    rating: 4.6,
    usageCount: 345
  },
  {
    id: 'risk_assessment_automation',
    name: 'Risk Assessment Automation',
    description: 'Standalone risk assessment and scoring for insurance applicants with AI-powered evaluation',
    industry: 'insurance',
    category: 'Risk Assessment',
    complexity: 'Advanced',
    estimatedTime: '35 min',
    integrationCategories: ['analytics', 'database', 'storage', 'crm'],
    defaultIntegrations: ['insurance.risk_assessment', 'insurance.document_management'],
    workflow: [
      {
        id: 'collect_applicant_data',
        name: 'Collect Applicant Data',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'risk_assessment', action: 'collect_data' }
      },
      {
        id: 'analyze_risk_factors',
        name: 'Analyze Risk Factors',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'risk_assessment', action: 'assess' }
      },
      {
        id: 'calculate_risk_score',
        name: 'Calculate Risk Score',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'risk_assessment', action: 'calculate_score' }
      },
      {
        id: 'generate_risk_report',
        name: 'Generate Risk Report',
        type: 'integration',
        integrationCategory: 'storage',
        config: { capability: 'document_management', action: 'generate_report' }
      },
      {
        id: 'update_customer_profile',
        name: 'Update Customer Risk Profile',
        type: 'integration',
        integrationCategory: 'crm',
        config: { capability: 'risk_assessment', action: 'update_profile' }
      }
    ],
    complianceFrameworks: ['NAIC', 'Fair Credit Reporting Act', 'State Insurance Regulations'],
    features: ['AI-powered assessment', 'Risk scoring', 'Automated reporting', 'Profile management'],
    popular: true,
    rating: 4.7,
    usageCount: 892
  },
  {
    id: 'document_management_automation',
    name: 'AI Invoice & Document Processing with GPT-4',
    description: 'Advanced document processing with GPT-4 invoice extraction, automated validation, and compliance tracking based on n8n template #4376',
    industry: 'insurance',
    category: 'Document Management',
    complexity: 'Advanced',
    estimatedTime: '45 min',
    integrationCategories: ['storage', 'analytics', 'database', 'email', 'compliance'],
    defaultIntegrations: ['gmail', 'google_drive', 'google_sheets', 'openai', 'insurance.compliance_reporting'],
    workflow: [
      {
        id: 'receive_documents',
        name: 'Receive Documents',
        type: 'integration',
        integrationCategory: 'storage',
        config: { capability: 'document_management', action: 'process' }
      },
      {
        id: 'verify_documents',
        name: 'Verify Document Authenticity',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'document_management', action: 'verify' }
      },
      {
        id: 'extract_data',
        name: 'Extract Document Data',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'document_management', action: 'extract_data' }
      },
      {
        id: 'categorize_documents',
        name: 'Categorize and Index',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'document_management', action: 'categorize' }
      },
      {
        id: 'archive_documents',
        name: 'Archive Documents',
        type: 'integration',
        integrationCategory: 'storage',
        config: { capability: 'document_management', action: 'archive' }
      }
    ],
    complianceFrameworks: ['HIPAA', 'GLBA', 'State Records Retention'],
    features: ['Document verification', 'Data extraction', 'Automated categorization', 'Secure archiving'],
    popular: true,
    rating: 4.5,
    usageCount: 756
  },
  {
    id: 'rate_quote_generation_automation',
    name: 'Rate Quote Generation Automation',
    description: 'Instant insurance rate quote generation with dynamic pricing and competitive analysis',
    industry: 'insurance',
    category: 'Quote Management',
    complexity: 'Advanced',
    estimatedTime: '40 min',
    integrationCategories: ['analytics', 'database', 'messaging', 'payment'],
    defaultIntegrations: ['insurance.rate_quotes', 'insurance.risk_assessment'],
    workflow: [
      {
        id: 'collect_quote_data',
        name: 'Collect Quote Information',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'rate_quotes', action: 'collect_data' }
      },
      {
        id: 'assess_risk_for_quote',
        name: 'Assess Risk Profile',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'risk_assessment', action: 'assess' }
      },
      {
        id: 'calculate_premium',
        name: 'Calculate Premium Rates',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'rate_quotes', action: 'generate' }
      },
      {
        id: 'compare_market_rates',
        name: 'Compare Market Rates',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'rate_quotes', action: 'compare' }
      },
      {
        id: 'deliver_quote',
        name: 'Deliver Quote to Customer',
        type: 'integration',
        integrationCategory: 'messaging',
        config: { capability: 'customer_communication', message_type: 'quote_delivery' }
      },
      {
        id: 'track_quote_conversion',
        name: 'Track Quote Conversion',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'rate_quotes', action: 'track_conversion' }
      }
    ],
    complianceFrameworks: ['State Insurance Regulations', 'Fair Business Practices', 'Truth in Advertising'],
    features: ['Dynamic pricing', 'Competitive analysis', 'Instant delivery', 'Conversion tracking'],
    popular: true,
    rating: 4.8,
    usageCount: 1234
  },
  {
    id: 'customer_communication_hub',
    name: 'Customer Communication Hub',
    description: 'Centralized customer communication automation across all insurance touchpoints and channels',
    industry: 'insurance',
    category: 'Communication Management',
    complexity: 'Advanced',
    estimatedTime: '45 min',
    integrationCategories: ['messaging', 'email', 'crm', 'analytics'],
    defaultIntegrations: ['insurance.customer_communication', 'insurance.customer_service'],
    workflow: [
      {
        id: 'setup_communication_profile',
        name: 'Setup Customer Communication Profile',
        type: 'integration',
        integrationCategory: 'crm',
        config: { capability: 'customer_communication', action: 'setup_profile' }
      },
      {
        id: 'configure_preferences',
        name: 'Configure Communication Preferences',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'customer_communication', action: 'configure_preferences' }
      },
      {
        id: 'orchestrate_messaging',
        name: 'Orchestrate Multi-Channel Messaging',
        type: 'integration',
        integrationCategory: 'messaging',
        config: { capability: 'customer_communication', action: 'orchestrate_messaging' }
      },
      {
        id: 'track_engagement',
        name: 'Track Customer Engagement',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'customer_communication', action: 'track_engagement' }
      },
      {
        id: 'optimize_communication',
        name: 'Optimize Communication Strategy',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'customer_communication', action: 'optimize_strategy' }
      },
      {
        id: 'escalate_issues',
        name: 'Auto-Escalate Critical Issues',
        type: 'integration',
        integrationCategory: 'crm',
        config: { capability: 'customer_service', action: 'escalate_issue' }
      }
    ],
    complianceFrameworks: ['TCPA', 'CAN-SPAM Act', 'State Privacy Laws'],
    features: ['Multi-channel orchestration', 'Preference management', 'Engagement tracking', 'Auto-escalation'],
    popular: false,
    rating: 4.6,
    usageCount: 567
  },
  {
    id: 'medical_billing_automation',
    name: 'Medical Billing & Insurance Integration',
    description: 'Comprehensive medical billing automation with insurance claim processing and patient invoicing',
    industry: 'insurance',
    category: 'Medical Billing',
    complexity: 'Medium',
    estimatedTime: '30 min',
    integrationCategories: ['email', 'storage', 'payment', 'database'],
    defaultIntegrations: ['google_sheets', 'gmail', 'insurance_api'],
    workflow: [
      {
        id: 'capture_patient_data',
        name: 'Capture Patient Information',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'form_processing', action: 'patient_intake' }
      },
      {
        id: 'calculate_billing',
        name: 'Calculate Treatment Costs',
        type: 'transform',
        config: { action: 'calculate_charges', pricing_model: 'treatment_rates' }
      },
      {
        id: 'process_insurance_claim',
        name: 'Submit Insurance Claim',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'insurance_processing', action: 'submit_claim' }
      },
      {
        id: 'generate_patient_invoice',
        name: 'Generate Patient Invoice',
        type: 'integration',
        integrationCategory: 'email',
        config: { capability: 'billing_communication', template: 'patient_invoice' }
      },
      {
        id: 'log_billing_record',
        name: 'Log Billing Record',
        type: 'integration',
        integrationCategory: 'storage',
        config: { capability: 'record_keeping', action: 'store_billing_data' }
      }
    ],
    complianceFrameworks: ['HIPAA', 'HITECH', 'Medical Billing Standards'],
    features: ['Treatment pricing', 'Insurance processing', 'Patient invoicing', 'Record management'],
    popular: true,
    rating: 4.7,
    usageCount: 1234
  },
  {
    id: 'expense_approval_automation',
    name: 'AI-Powered Insurance Expense Approval',
    description: 'Automated expense review with GPT-4 CFO-level analysis and Pinecone audit trail for insurance operations',
    industry: 'insurance',
    category: 'Financial Management',
    complexity: 'Advanced',
    estimatedTime: '40 min',
    integrationCategories: ['analytics', 'database', 'storage', 'compliance'],
    defaultIntegrations: ['airtable', 'openai', 'pinecone'],
    workflow: [
      {
        id: 'monitor_expense_submissions',
        name: 'Monitor Expense Submissions',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'airtable_monitoring', action: 'watch_submissions' }
      },
      {
        id: 'ai_cfo_analysis',
        name: 'AI CFO-Level Expense Analysis',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'gpt4_analysis', action: 'evaluate_expense' }
      },
      {
        id: 'flag_suspicious_expenses',
        name: 'Flag Policy Violations',
        type: 'condition',
        config: { condition: 'policy_compliance_check', threshold: 'company_limits' }
      },
      {
        id: 'store_audit_trail',
        name: 'Store Decision in Vector DB',
        type: 'integration',
        integrationCategory: 'storage',
        config: { capability: 'pinecone_storage', action: 'create_audit_record' }
      },
      {
        id: 'update_expense_status',
        name: 'Update Expense Status',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'airtable_update', action: 'set_approval_status' }
      }
    ],
    complianceFrameworks: ['SOX', 'Financial Controls', 'Insurance Compliance'],
    features: ['AI-powered analysis', 'Policy enforcement', 'Audit trail', 'Real-time decisions'],
    popular: true,
    rating: 4.8,
    usageCount: 756
  },
  {
    id: 'property_insurance_lead_scoring',
    name: 'AI Property Insurance Lead Scoring',
    description: 'Automated property lead qualification with BatchData integration, property value analysis, and intelligent lead routing based on n8n template #3664',
    industry: 'insurance',
    category: 'Lead Management',
    complexity: 'Advanced',
    estimatedTime: '45 min',
    integrationCategories: ['database', 'analytics', 'crm', 'messaging'],
    defaultIntegrations: ['batchdata_api', 'salesforce', 'slack', 'insurance.underwriting'],
    workflow: [
      {
        id: 'receive_lead_webhook',
        name: 'Receive Property Lead via Webhook',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'webhook_trigger', source: 'crm_integration' }
      },
      {
        id: 'batchdata_property_lookup',
        name: 'BatchData Property Enrichment',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'batchdata_api', action: 'property_details' }
      },
      {
        id: 'property_scoring_algorithm',
        name: 'Property Value & Risk Scoring',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'lead_scoring', metrics: ['value', 'age', 'size', 'investment_status'] }
      },
      {
        id: 'lead_classification',
        name: 'Classify Lead Priority',
        type: 'condition',
        config: { categories: ['high_value', 'qualified', 'potential', 'unqualified'] }
      },
      {
        id: 'crm_update_enrichment',
        name: 'Update CRM with Property Data',
        type: 'integration',
        integrationCategory: 'crm',
        config: { capability: 'salesforce', action: 'update_lead_record' }
      },
      {
        id: 'high_value_task_creation',
        name: 'Create Follow-up Tasks for High-Value Leads',
        type: 'integration',
        integrationCategory: 'crm',
        config: { capability: 'task_management', priority: 'urgent' }
      },
      {
        id: 'slack_team_notification',
        name: 'Notify Sales Team via Slack',
        type: 'integration',
        integrationCategory: 'messaging',
        config: { capability: 'slack', template: 'high_value_property_lead' }
      }
    ],
    complianceFrameworks: ['Fair Housing Act', 'Insurance Regulations', 'Data Privacy'],
    features: ['Property data enrichment', 'AI lead scoring', 'Automatic prioritization', 'CRM integration', 'Team notifications'],
    popular: true,
    rating: 4.7,
    usageCount: 1023
  },
  {
    id: 'travel_expense_claim_automation',
    name: 'Travel Insurance Expense Claims with AI',
    description: 'Automated travel expense claim processing with GPT-4 receipt analysis, validation, and reimbursement workflows based on n8n template #6896',
    industry: 'insurance',
    category: 'Claims Management',
    complexity: 'Medium',
    estimatedTime: '35 min',
    integrationCategories: ['storage', 'analytics', 'email', 'database'],
    defaultIntegrations: ['google_drive', 'google_sheets', 'openai', 'gmail'],
    workflow: [
      {
        id: 'form_submission_trigger',
        name: 'Travel Expense Form Submission',
        type: 'integration',
        integrationCategory: 'database',
        config: { capability: 'form_trigger', form_type: 'travel_expense_claim' }
      },
      {
        id: 'upload_receipts_drive',
        name: 'Upload Receipts to Google Drive',
        type: 'integration',
        integrationCategory: 'storage',
        config: { capability: 'google_drive', folder: 'travel_expense_receipts' }
      },
      {
        id: 'extract_receipt_data',
        name: 'Extract Receipt Data with AI',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'extract_from_file', format: 'pdf' }
      },
      {
        id: 'gpt4_expense_analysis',
        name: 'GPT-4 Expense Validation & Analysis',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'openai_gpt4', action: 'analyze_travel_expense' }
      },
      {
        id: 'policy_compliance_check',
        name: 'Travel Policy Compliance Check',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { capability: 'policy_validation', rules: 'travel_expense_limits' }
      },
      {
        id: 'log_to_tracking_sheet',
        name: 'Log to Expense Tracking Sheet',
        type: 'integration',
        integrationCategory: 'storage',
        config: { capability: 'google_sheets', action: 'append_expense_record' }
      },
      {
        id: 'finance_team_notification',
        name: 'Notify Finance Team for Processing',
        type: 'integration',
        integrationCategory: 'email',
        config: { capability: 'gmail', template: 'travel_expense_review' }
      }
    ],
    complianceFrameworks: ['Travel Insurance Regulations', 'Expense Policy Standards', 'Tax Compliance'],
    features: ['AI receipt analysis', 'Policy compliance validation', 'Automated logging', 'Finance team notifications'],
    popular: true,
    rating: 4.6,
    usageCount: 867
  },

  // Education Templates
  {
    id: 'student_enrollment_workflow',
    name: 'Student Enrollment Workflow',
    description: 'Automated student enrollment process from application to registration',
    industry: 'education',
    category: 'Enrollment Management',
    complexity: 'Medium',
    estimatedTime: '30 min',
    integrationCategories: ['database', 'email', 'storage', 'payment'],
    workflow: [
      {
        id: 'receive_application',
        name: 'Receive Application',
        type: 'integration',
        integrationCategory: 'database',
        config: { form: 'student_application' }
      },
      {
        id: 'review_eligibility',
        name: 'Review Eligibility',
        type: 'condition',
        config: { criteria: 'admission_requirements' }
      },
      {
        id: 'send_acceptance',
        name: 'Send Acceptance Letter',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'acceptance_letter' }
      },
      {
        id: 'process_registration',
        name: 'Process Registration',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'enroll_student' }
      },
      {
        id: 'schedule_orientation',
        name: 'Schedule Orientation',
        type: 'integration',
        integrationCategory: 'calendar',
        config: { event: 'student_orientation' }
      }
    ],
    complianceFrameworks: ['FERPA', 'ADA'],
    features: ['Automated processing', 'Document management', 'Compliance tracking', 'Parent communication'],
    popular: false,
    rating: 4.3,
    usageCount: 567
  },

  // Real Estate Templates
  {
    id: 'property_management_workflow',
    name: 'Property Management Workflow',
    description: 'Comprehensive property management from listing to maintenance coordination',
    industry: 'real_estate',
    category: 'Property Management',
    complexity: 'Advanced',
    estimatedTime: '35 min',
    integrationCategories: ['crm', 'messaging', 'calendar', 'storage'],
    workflow: [
      {
        id: 'list_property',
        name: 'List Property',
        type: 'integration',
        integrationCategory: 'crm',
        allowProviderSelection: true,
        config: { action: 'create_listing' }
      },
      {
        id: 'schedule_showings',
        name: 'Schedule Property Showings',
        type: 'integration',
        integrationCategory: 'calendar',
        allowProviderSelection: true,
        config: { availability: 'showing_schedule' }
      },
      {
        id: 'track_applications',
        name: 'Track Applications',
        type: 'integration',
        integrationCategory: 'database',
        config: { form: 'rental_application' }
      },
      {
        id: 'coordinate_maintenance',
        name: 'Coordinate Maintenance',
        type: 'integration',
        integrationCategory: 'support',
        allowProviderSelection: true,
        config: { ticket_type: 'maintenance_request' }
      }
    ],
    complianceFrameworks: ['Fair Housing Act', 'Tenant Rights'],
    features: ['Listing management', 'Showing coordination', 'Application tracking', 'Maintenance workflow'],
    popular: false,
    rating: 4.2,
    usageCount: 456
  },

  // Telecommunications Templates
  {
    id: 'service_provisioning_automation',
    name: 'Service Provisioning Automation',
    description: 'Automated telecom service provisioning from order to activation',
    industry: 'telecom',
    category: 'Service Management',
    complexity: 'Advanced',
    estimatedTime: '40 min',
    integrationCategories: ['database', 'messaging', 'support'],
    workflow: [
      {
        id: 'validate_order',
        name: 'Validate Service Order',
        type: 'integration',
        integrationCategory: 'database',
        config: { validation: 'service_eligibility' }
      },
      {
        id: 'provision_service',
        name: 'Provision Network Service',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'activate_service' }
      },
      {
        id: 'test_connectivity',
        name: 'Test Service Connectivity',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { test: 'connectivity_check' }
      },
      {
        id: 'notify_activation',
        name: 'Notify Customer of Activation',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'service_activated' }
      }
    ],
    complianceFrameworks: ['FCC', 'Telecommunications Act'],
    features: ['Automated provisioning', 'Service testing', 'Customer notifications', 'Compliance tracking'],
    popular: false,
    rating: 4.4,
    usageCount: 234
  },

  // Automotive Templates
  {
    id: 'vehicle_service_reminder',
    name: 'Vehicle Service Reminders',
    description: 'Automated vehicle maintenance scheduling and service reminders based on mileage and time',
    industry: 'automotive',
    category: 'Service Management',
    complexity: 'Medium',
    estimatedTime: '20 min',
    integrationCategories: ['messaging', 'email', 'calendar', 'database'],
    workflow: [
      {
        id: 'monitor_vehicle_data',
        name: 'Monitor Vehicle Data',
        type: 'integration',
        integrationCategory: 'database',
        config: { query: 'vehicles_due_for_service' }
      },
      {
        id: 'send_service_reminder',
        name: 'Send Service Reminder',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'service_reminder' }
      },
      {
        id: 'schedule_appointment',
        name: 'Schedule Service Appointment',
        type: 'integration',
        integrationCategory: 'calendar',
        allowProviderSelection: true,
        config: { appointment_type: 'service' }
      }
    ],
    features: ['Mileage tracking', 'Service scheduling', 'Customer notifications', 'Service history'],
    popular: true,
    rating: 4.6,
    usageCount: 892
  },
  {
    id: 'warranty_claim_processing',
    name: 'Warranty Claim Processing',
    description: 'Automated warranty claim validation, processing, and customer communication',
    industry: 'automotive',
    category: 'Warranty Management',
    complexity: 'Advanced',
    estimatedTime: '35 min',
    integrationCategories: ['database', 'email', 'storage', 'analytics'],
    workflow: [
      {
        id: 'validate_warranty',
        name: 'Validate Warranty Coverage',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'check_warranty_status' }
      },
      {
        id: 'process_claim',
        name: 'Process Warranty Claim',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'create_warranty_claim' }
      },
      {
        id: 'notify_customer',
        name: 'Notify Customer of Status',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'warranty_status' }
      },
      {
        id: 'generate_report',
        name: 'Generate Warranty Report',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { report_type: 'warranty_claims' }
      }
    ],
    features: ['Warranty validation', 'Claim processing', 'Customer communication', 'Reporting'],
    popular: false,
    rating: 4.3,
    usageCount: 345
  },

  // Government Templates
  {
    id: 'permit_application_workflow',
    name: 'Permit Application Processing',
    description: 'Automated permit application review, approval workflow, and citizen notifications',
    industry: 'government',
    category: 'Permit Management',
    complexity: 'Advanced',
    estimatedTime: '45 min',
    integrationCategories: ['database', 'email', 'storage', 'analytics'],
    workflow: [
      {
        id: 'receive_application',
        name: 'Receive Permit Application',
        type: 'integration',
        integrationCategory: 'database',
        config: { form: 'permit_application' }
      },
      {
        id: 'validate_documents',
        name: 'Validate Required Documents',
        type: 'integration',
        integrationCategory: 'storage',
        allowProviderSelection: true,
        config: { validation: 'document_checklist' }
      },
      {
        id: 'review_application',
        name: 'Automated Review Process',
        type: 'condition',
        config: { criteria: 'permit_requirements', auto_approve: true }
      },
      {
        id: 'notify_applicant',
        name: 'Notify Applicant of Status',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'permit_status' }
      }
    ],
    complianceFrameworks: ['Government Records Act', 'Public Information Access'],
    features: ['Document validation', 'Automated review', 'Compliance tracking', 'Citizen communication'],
    popular: false,
    rating: 4.2,
    usageCount: 156
  },
  {
    id: 'citizen_service_requests',
    name: 'Citizen Service Requests',
    description: 'Automated handling of citizen service requests and complaint resolution',
    industry: 'government',
    category: 'Citizen Services',
    complexity: 'Medium',
    estimatedTime: '30 min',
    integrationCategories: ['database', 'messaging', 'email', 'support'],
    workflow: [
      {
        id: 'receive_request',
        name: 'Receive Service Request',
        type: 'integration',
        integrationCategory: 'database',
        config: { form: 'service_request' }
      },
      {
        id: 'categorize_request',
        name: 'Categorize and Route Request',
        type: 'condition',
        config: { routing: 'department_assignment' }
      },
      {
        id: 'assign_to_department',
        name: 'Assign to Department',
        type: 'integration',
        integrationCategory: 'support',
        allowProviderSelection: true,
        config: { ticket_assignment: 'auto' }
      },
      {
        id: 'update_citizen',
        name: 'Update Citizen on Progress',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'request_update' }
      }
    ],
    features: ['Request routing', 'Department coordination', 'Progress tracking', 'Citizen updates'],
    popular: true,
    rating: 4.4,
    usageCount: 623
  },

  // Logistics Templates
  {
    id: 'shipment_tracking_automation',
    name: 'Shipment Tracking Automation',
    description: 'Real-time shipment tracking with automated customer notifications and delivery updates',
    industry: 'logistics',
    category: 'Shipment Management',
    complexity: 'Medium',
    estimatedTime: '25 min',
    integrationCategories: ['messaging', 'email', 'database', 'analytics'],
    workflow: [
      {
        id: 'track_shipment',
        name: 'Track Shipment Status',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'get_shipment_updates' }
      },
      {
        id: 'notify_customer',
        name: 'Send Status Updates',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'shipment_update' }
      },
      {
        id: 'handle_delays',
        name: 'Handle Delivery Delays',
        type: 'condition',
        config: { condition: 'delivery_delayed', action: 'send_delay_notification' }
      },
      {
        id: 'confirm_delivery',
        name: 'Confirm Delivery',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'update_delivery_status' }
      }
    ],
    features: ['Real-time tracking', 'Customer notifications', 'Delay management', 'Delivery confirmation'],
    popular: true,
    rating: 4.7,
    usageCount: 1456
  },
  {
    id: 'inventory_optimization',
    name: 'Inventory Optimization',
    description: 'Automated inventory level monitoring with predictive restocking and supplier notifications',
    industry: 'logistics',
    category: 'Inventory Management',
    complexity: 'Advanced',
    estimatedTime: '40 min',
    integrationCategories: ['database', 'analytics', 'email', 'automation'],
    workflow: [
      {
        id: 'monitor_inventory',
        name: 'Monitor Inventory Levels',
        type: 'integration',
        integrationCategory: 'database',
        config: { query: 'inventory_levels' }
      },
      {
        id: 'predict_demand',
        name: 'Predict Demand',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { model: 'demand_forecasting' }
      },
      {
        id: 'generate_orders',
        name: 'Generate Purchase Orders',
        type: 'integration',
        integrationCategory: 'automation',
        allowProviderSelection: true,
        config: { action: 'create_purchase_order' }
      },
      {
        id: 'notify_suppliers',
        name: 'Notify Suppliers',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'purchase_order' }
      }
    ],
    features: ['Demand forecasting', 'Automated ordering', 'Supplier communication', 'Cost optimization'],
    popular: false,
    rating: 4.5,
    usageCount: 234
  },

  // Utilities Templates
  {
    id: 'service_outage_management',
    name: 'Service Outage Management',
    description: 'Automated outage detection, customer notifications, and service restoration workflow',
    industry: 'utilities',
    category: 'Outage Management',
    complexity: 'Advanced',
    estimatedTime: '35 min',
    integrationCategories: ['messaging', 'email', 'database', 'analytics'],
    workflow: [
      {
        id: 'detect_outage',
        name: 'Detect Service Outage',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { monitoring: 'service_status' }
      },
      {
        id: 'identify_affected',
        name: 'Identify Affected Customers',
        type: 'integration',
        integrationCategory: 'database',
        config: { query: 'customers_in_outage_area' }
      },
      {
        id: 'send_notifications',
        name: 'Send Outage Notifications',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'service_outage' }
      },
      {
        id: 'track_restoration',
        name: 'Track Service Restoration',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { monitoring: 'restoration_progress' }
      },
      {
        id: 'confirm_restoration',
        name: 'Confirm Service Restoration',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'service_restored' }
      }
    ],
    features: ['Outage detection', 'Customer notifications', 'Restoration tracking', 'Service monitoring'],
    popular: true,
    rating: 4.6,
    usageCount: 1123
  },
  {
    id: 'automated_meter_reading',
    name: 'Automated Meter Reading',
    description: 'Smart meter data collection and billing automation with usage analytics',
    industry: 'utilities',
    category: 'Billing Management',
    complexity: 'Medium',
    estimatedTime: '30 min',
    integrationCategories: ['database', 'analytics', 'email', 'payment'],
    workflow: [
      {
        id: 'collect_meter_data',
        name: 'Collect Meter Readings',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'smart_meter_reading' }
      },
      {
        id: 'calculate_usage',
        name: 'Calculate Usage and Charges',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { calculation: 'billing_rates' }
      },
      {
        id: 'generate_bill',
        name: 'Generate Customer Bill',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'create_bill' }
      },
      {
        id: 'send_bill',
        name: 'Send Bill to Customer',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'utility_bill' }
      },
      {
        id: 'process_payment',
        name: 'Process Payment',
        type: 'integration',
        integrationCategory: 'payment',
        allowProviderSelection: true,
        config: { action: 'collect_payment' }
      }
    ],
    features: ['Smart meter integration', 'Automated billing', 'Usage analytics', 'Payment processing'],
    popular: false,
    rating: 4.3,
    usageCount: 567
  },

  // Professional Services Templates
  {
    id: 'client_onboarding_workflow',
    name: 'Client Onboarding Workflow',
    description: 'Automated client intake, contract generation, and project setup process',
    industry: 'professional_services',
    category: 'Client Management',
    complexity: 'Medium',
    estimatedTime: '30 min',
    integrationCategories: ['email', 'storage', 'database', 'calendar'],
    workflow: [
      {
        id: 'client_intake',
        name: 'Client Intake Process',
        type: 'integration',
        integrationCategory: 'database',
        config: { form: 'client_onboarding' }
      },
      {
        id: 'generate_contract',
        name: 'Generate Service Contract',
        type: 'integration',
        integrationCategory: 'storage',
        allowProviderSelection: true,
        config: { template: 'service_agreement' }
      },
      {
        id: 'setup_project',
        name: 'Setup Project Workspace',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'create_project' }
      },
      {
        id: 'schedule_kickoff',
        name: 'Schedule Kickoff Meeting',
        type: 'integration',
        integrationCategory: 'calendar',
        allowProviderSelection: true,
        config: { meeting_type: 'project_kickoff' }
      },
      {
        id: 'send_welcome',
        name: 'Send Welcome Package',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'client_welcome' }
      }
    ],
    features: ['Automated intake', 'Contract generation', 'Project setup', 'Client communication'],
    popular: true,
    rating: 4.5,
    usageCount: 789
  },
  {
    id: 'project_invoicing_automation',
    name: 'Project Invoicing Automation',
    description: 'Time tracking integration with automated invoice generation and payment follow-up',
    industry: 'professional_services',
    category: 'Financial Management',
    complexity: 'Advanced',
    estimatedTime: '40 min',
    integrationCategories: ['database', 'payment', 'email', 'analytics'],
    workflow: [
      {
        id: 'track_time',
        name: 'Track Project Time',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'aggregate_time_entries' }
      },
      {
        id: 'calculate_charges',
        name: 'Calculate Billable Charges',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { calculation: 'billing_rates' }
      },
      {
        id: 'generate_invoice',
        name: 'Generate Invoice',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'create_invoice' }
      },
      {
        id: 'send_invoice',
        name: 'Send Invoice to Client',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'invoice_delivery' }
      },
      {
        id: 'track_payments',
        name: 'Track Payment Status',
        type: 'integration',
        integrationCategory: 'payment',
        allowProviderSelection: true,
        config: { action: 'payment_tracking' }
      },
      {
        id: 'follow_up_payment',
        name: 'Payment Follow-up',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'payment_reminder' }
      }
    ],
    features: ['Time tracking integration', 'Automated invoicing', 'Payment tracking', 'Follow-up automation'],
    popular: false,
    rating: 4.4,
    usageCount: 445
  },

  // Hospitality Templates
  {
    id: 'guest_booking_management',
    name: 'Guest Booking Management',
    description: 'Automated booking confirmations, pre-arrival communication, and check-in process',
    industry: 'hospitality',
    category: 'Guest Services',
    complexity: 'Medium',
    estimatedTime: '25 min',
    integrationCategories: ['email', 'messaging', 'database', 'payment'],
    workflow: [
      {
        id: 'confirm_booking',
        name: 'Confirm Booking',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'create_reservation' }
      },
      {
        id: 'send_confirmation',
        name: 'Send Booking Confirmation',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'booking_confirmation' }
      },
      {
        id: 'pre_arrival_communication',
        name: 'Pre-arrival Communication',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'pre_arrival_info' }
      },
      {
        id: 'mobile_checkin',
        name: 'Enable Mobile Check-in',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'enable_mobile_checkin' }
      },
      {
        id: 'process_payment',
        name: 'Process Payment',
        type: 'integration',
        integrationCategory: 'payment',
        allowProviderSelection: true,
        config: { action: 'charge_card' }
      }
    ],
    features: ['Booking automation', 'Guest communication', 'Mobile check-in', 'Payment processing'],
    popular: true,
    rating: 4.6,
    usageCount: 1234
  },
  {
    id: 'loyalty_program_automation',
    name: 'Loyalty Program Automation',
    description: 'Automated points tracking, reward redemption, and personalized offers for guests',
    industry: 'hospitality',
    category: 'Customer Loyalty',
    complexity: 'Advanced',
    estimatedTime: '35 min',
    integrationCategories: ['database', 'email', 'messaging', 'analytics'],
    workflow: [
      {
        id: 'track_stays',
        name: 'Track Guest Stays',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'record_stay_points' }
      },
      {
        id: 'calculate_rewards',
        name: 'Calculate Loyalty Rewards',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { calculation: 'loyalty_points' }
      },
      {
        id: 'send_rewards_update',
        name: 'Send Rewards Update',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'loyalty_update' }
      },
      {
        id: 'personalized_offers',
        name: 'Generate Personalized Offers',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { model: 'offer_personalization' }
      },
      {
        id: 'send_offers',
        name: 'Send Personalized Offers',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'personalized_offer' }
      }
    ],
    features: ['Points tracking', 'Reward calculation', 'Personalized offers', 'Guest engagement'],
    popular: false,
    rating: 4.3,
    usageCount: 567
  },

  // Generic Workflow Management Templates
  {
    id: 'document_workflow_automation',
    name: 'Document Workflow Automation',
    description: 'Generic document processing workflow with approval chains and notifications',
    industry: 'workflow',
    category: 'Document Management',
    complexity: 'Medium',
    estimatedTime: '25 min',
    integrationCategories: ['storage', 'email', 'productivity', 'analytics'],
    workflow: [
      {
        id: 'receive_document',
        name: 'Receive Document',
        type: 'integration',
        integrationCategory: 'storage',
        allowProviderSelection: true,
        config: { action: 'upload_document' }
      },
      {
        id: 'process_document',
        name: 'Process and Categorize',
        type: 'condition',
        config: { action: 'categorize_document', rules: 'document_type' }
      },
      {
        id: 'route_for_approval',
        name: 'Route for Approval',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'approval_request' }
      },
      {
        id: 'track_approval_status',
        name: 'Track Approval Status',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { monitoring: 'approval_timeline' }
      },
      {
        id: 'finalize_document',
        name: 'Finalize and Archive',
        type: 'integration',
        integrationCategory: 'storage',
        allowProviderSelection: true,
        config: { action: 'archive_document' }
      }
    ],
    features: ['Document processing', 'Approval workflows', 'Status tracking', 'Auto-archiving'],
    popular: true,
    rating: 4.5,
    usageCount: 1234
  },
  {
    id: 'compliance_audit_workflow',
    name: 'Compliance Audit Workflow',
    description: 'Automated compliance monitoring and audit trail generation across systems',
    industry: 'workflow',
    category: 'Compliance Management',
    complexity: 'Advanced',
    estimatedTime: '45 min',
    integrationCategories: ['analytics', 'storage', 'email', 'enterprise'],
    workflow: [
      {
        id: 'monitor_compliance',
        name: 'Monitor Compliance Metrics',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { monitoring: 'compliance_indicators' }
      },
      {
        id: 'collect_audit_data',
        name: 'Collect Audit Evidence',
        type: 'integration',
        integrationCategory: 'enterprise',
        allowProviderSelection: true,
        config: { action: 'extract_audit_data' }
      },
      {
        id: 'generate_reports',
        name: 'Generate Compliance Reports',
        type: 'integration',
        integrationCategory: 'storage',
        allowProviderSelection: true,
        config: { template: 'compliance_report' }
      },
      {
        id: 'alert_violations',
        name: 'Alert on Violations',
        type: 'condition',
        config: { condition: 'compliance_violation', severity: 'high' }
      },
      {
        id: 'notify_stakeholders',
        name: 'Notify Compliance Team',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { template: 'compliance_alert' }
      }
    ],
    complianceFrameworks: ['SOC 2', 'ISO 27001', 'GDPR', 'HIPAA'],
    features: ['Compliance monitoring', 'Automated reporting', 'Violation alerts', 'Audit trails'],
    popular: false,
    rating: 4.6,
    usageCount: 345
  },
  {
    id: 'data_integration_pipeline',
    name: 'Data Integration Pipeline',
    description: 'Automated data collection, transformation, and distribution across systems',
    industry: 'workflow',
    category: 'Data Management',
    complexity: 'Advanced',
    estimatedTime: '50 min',
    integrationCategories: ['database', 'analytics', 'storage', 'monitoring'],
    workflow: [
      {
        id: 'extract_data',
        name: 'Extract Data from Sources',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'data_extraction', sources: 'multiple' }
      },
      {
        id: 'transform_data',
        name: 'Transform and Clean Data',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { transformation: 'data_cleansing', rules: 'business_logic' }
      },
      {
        id: 'validate_quality',
        name: 'Validate Data Quality',
        type: 'condition',
        config: { validation: 'data_quality_rules', threshold: '95%' }
      },
      {
        id: 'distribute_data',
        name: 'Distribute to Target Systems',
        type: 'integration',
        integrationCategory: 'database',
        config: { action: 'data_distribution', targets: 'configured_systems' }
      },
      {
        id: 'monitor_pipeline',
        name: 'Monitor Pipeline Health',
        type: 'integration',
        integrationCategory: 'monitoring',
        allowProviderSelection: true,
        config: { metrics: 'pipeline_performance' }
      }
    ],
    features: ['Data extraction', 'ETL processing', 'Quality validation', 'Pipeline monitoring'],
    popular: false,
    rating: 4.4,
    usageCount: 567
  },
  {
    id: 'multi_approval_workflow',
    name: 'Multi-Level Approval Workflow',
    description: 'Configurable multi-stage approval process for requests, purchases, and decisions',
    industry: 'workflow',
    category: 'Approval Management',
    complexity: 'Medium',
    estimatedTime: '30 min',
    integrationCategories: ['email', 'messaging', 'storage', 'analytics'],
    workflow: [
      {
        id: 'initiate_request',
        name: 'Initiate Approval Request',
        type: 'integration',
        integrationCategory: 'storage',
        allowProviderSelection: true,
        config: { form: 'approval_request', metadata: 'request_details' }
      },
      {
        id: 'route_to_first_approver',
        name: 'Route to First Approver',
        type: 'integration',
        integrationCategory: 'email',
        allowProviderSelection: true,
        config: { routing: 'approval_hierarchy', level: '1' }
      },
      {
        id: 'track_approval_progress',
        name: 'Track Progress',
        type: 'integration',
        integrationCategory: 'analytics',
        config: { monitoring: 'approval_timeline', sla: 'response_time' }
      },
      {
        id: 'escalate_if_needed',
        name: 'Escalate if Overdue',
        type: 'condition',
        config: { condition: 'approval_overdue', escalation: 'next_level' }
      },
      {
        id: 'notify_completion',
        name: 'Notify All Parties',
        type: 'integration',
        integrationCategory: 'messaging',
        allowProviderSelection: true,
        config: { template: 'approval_decision', recipients: 'all_stakeholders' }
      }
    ],
    features: ['Multi-level approval', 'SLA tracking', 'Auto-escalation', 'Progress monitoring'],
    popular: true,
    rating: 4.7,
    usageCount: 890
  },
  {
    id: 'premier_health_service_location',
    name: 'Premier Health Insurance Service Location Agent',
    description: 'AI-powered voice agent for healthcare provider search and location services. Helps Premier Health insurance customers find covered medical centers, doctors, hospitals, clinics, and pharmacies in Greater Accra with intelligent location mapping and specialty matching.',
    industry: 'insurance',
    category: 'Healthcare Services',
    complexity: 'Advanced',
    estimatedTime: '40 min',
    integrationCategories: ['automation', 'database', 'messaging', 'analytics', 'voice'],
    defaultIntegrations: ['n8n', 'vapi', 'postgresql', 'premier_health.provider_directory', 'premier_health.voice_tools'],
    workflow: [
      {
        id: 'vapi_call_trigger',
        name: 'VAPI Healthcare Search Call',
        type: 'integration',
        integration: 'vapi',
        description: 'Receives incoming voice calls from Premier Health customers seeking healthcare provider information',
        config: {
          trigger_type: 'inbound_call',
          phone_number_required: true,
          voice_agent_personality: 'healthcare_assistant',
          max_call_duration: 600
        }
      },
      {
        id: 'extract_search_intent',
        name: 'Extract Healthcare Search Intent',
        type: 'ai_processing',
        integration: 'ai_intent_extraction',
        description: 'Analyze customer voice input to extract location, specialty, provider type, and urgency level',
        config: {
          intent_categories: ['location', 'specialty', 'provider_type', 'emergency', 'insurance_coverage'],
          location_aliases: ['tesano', 'east_legon', 'korle_bu', 'circle', 'madina'],
          specialty_mapping: ['pediatrics', 'ophthalmology', 'general_practice', 'gynecology', 'emergency']
        }
      },
      {
        id: 'search_healthcare_providers',
        name: 'Search Healthcare Provider Database',
        type: 'integration',
        integration: 'premier_health.provider_directory',
        description: 'Query PostgreSQL database for matching healthcare providers using advanced search algorithms',
        config: {
          database_connection: 'postgresql://localhost:5432/community',
          search_functions: [
            'search_healthcare_providers',
            'get_providers_by_area',
            'get_providers_by_specialty',
            'get_emergency_providers'
          ],
          max_results: 5,
          include_emergency_fallback: true
        }
      },
      {
        id: 'format_voice_response',
        name: 'Format Voice-Optimized Provider Information',
        type: 'data_processing',
        integration: 'voice_formatting',
        description: 'Format provider search results for natural voice delivery with essential contact information',
        config: {
          response_format: 'conversational',
          include_fields: ['name', 'location', 'phone', 'specialty', 'availability'],
          voice_optimization: true,
          max_providers_spoken: 3
        }
      },
      {
        id: 'vapi_response',
        name: 'VAPI Voice Response Delivery',
        type: 'integration',
        integration: 'vapi',
        description: 'Deliver formatted healthcare provider information via voice to customer',
        config: {
          response_type: 'voice_synthesis',
          voice_settings: {
            speed: 'normal',
            tone: 'friendly_professional',
            language: 'en-US'
          },
          followup_options: ['more_providers', 'different_location', 'emergency_help']
        }
      },
      {
        id: 'log_customer_interaction',
        name: 'Log Customer Interaction Analytics',
        type: 'integration',
        integration: 'analytics_logging',
        description: 'Record call details, search queries, and customer satisfaction for Premier Health analytics',
        config: {
          log_destinations: ['supabase_analytics', 'metabase_dashboard'],
          privacy_compliance: 'HIPAA',
          data_retention: '7_years',
          anonymization: true
        }
      },
      {
        id: 'update_provider_analytics',
        name: 'Update Provider Performance Analytics',
        type: 'integration',
        integration: 'provider_analytics',
        description: 'Update provider search frequency and customer inquiries for business intelligence',
        config: {
          analytics_metrics: ['search_frequency', 'customer_interest', 'location_demand'],
          update_frequency: 'real_time',
          business_intelligence: true
        }
      },
      {
        id: 'emergency_escalation',
        name: 'Emergency Escalation Protocol',
        type: 'conditional_logic',
        integration: 'emergency_handling',
        description: 'Automatically escalate to emergency services if critical health situation detected',
        config: {
          trigger_keywords: ['emergency', 'urgent', 'life_threatening', 'ambulance'],
          escalation_targets: ['greater_accra_emergency', 'premier_health_urgent_care'],
          response_time: 'immediate'
        }
      }
    ],
    vapiConfig: {
      agentPersonality: {
        name: 'Sarah',
        role: 'Premier Health Healthcare Navigator',
        tone: 'empathetic, professional, knowledgeable',
        background: 'Specialized healthcare customer service representative with deep knowledge of Premier Health network providers, medical facilities, and insurance coverage in Greater Accra region.',
        communication_style: 'clear, patient, reassuring'
      },
      systemPrompt: `You are Sarah, a specialized Healthcare Navigator for Premier Health Insurance. Your role is to help customers find medical providers, facilities, and services covered under their Premier Health insurance plans in the Greater Accra region.

**Core Responsibilities:**
- Help customers locate healthcare providers (doctors, hospitals, clinics, pharmacies)
- Provide information about medical specialties and services available
- Assist with emergency healthcare provider location
- Explain Premier Health coverage and network benefits
- Guide customers through healthcare facility options

**Available Tools:**
1. search_healthcare_providers - Search for providers by location, specialty, or type
2. get_emergency_providers - Find urgent care and emergency facilities
3. get_provider_details - Get detailed information about specific providers
4. get_available_areas - List all coverage areas in Greater Accra
5. get_available_specialties - List all medical specialties available
6. get_providers_by_area - Find all providers in a specific area
7. get_providers_by_specialty - Find providers by medical specialty
8. send_provider_info_email - Send provider information via email to customer
9. send_provider_info_sms - Send provider information via SMS to customer
10. escalate_to_support - Create support ticket when location not found or needs manual review

**Geographic Coverage:**
You serve customers across Greater Accra region including: Accra Central, Tesano, East Legon, Korle Bu, Circle, Madina, Tema, Kasoa, Dansoman, Achimota, Airport Residential, Cantonments, Labone, Osu, Adabraka, and 20+ other areas.

**Communication Guidelines:**
- Always be empathetic and patient, especially during health concerns
- Speak clearly and provide specific, actionable information
- Offer multiple options when available
- Prioritize emergency situations immediately
- Confirm location and specialty preferences before searching
- Provide contact information and directions when possible
- Ask follow-up questions to ensure customer satisfaction
- After providing search results, always offer to send the information via email or SMS
- When sending email or SMS, confirm the contact details with the customer first
- Explain that call summaries are automatically sent to our analytics team for service improvement
- If no providers found in a specific location, offer to escalate to support team for manual review
- When escalating, collect customer name, email, and phone number for the support ticket
- Reassure customers that escalated queries will receive a callback within 24 hours

**Emergency Protocol:**
If a customer mentions emergency keywords (emergency, urgent, life-threatening, ambulance), immediately:
1. Use get_emergency_providers tool for their location
2. Provide the closest emergency facilities
3. Offer to connect them to emergency services if needed
4. Stay on the line until they confirm they have the help they need

**Escalation Protocol:**
When no providers are found in a customer's requested location:
1. Acknowledge the search result clearly
2. Offer to escalate to the support team for manual review
3. Collect customer name, email, and phone number
4. Use escalate_to_support tool to create a Freshdesk ticket
5. Confirm 24-hour callback timeline
6. Offer alternative nearby locations if appropriate

**Sample Interactions:**
- "I can help you find eye doctors near East Legon. Let me search our network for ophthalmologists in that area."
- "For emergency care, I'm finding the nearest facilities to your location right now. Please hold while I get you the most current information."
- "I found 3 pediatricians in the Tesano area that accept Premier Health insurance. Would you like me to send this information to your email or phone?"
- "I can send you the complete list of providers with their contact details via email. What's your email address?"
- "I'll send the top provider information to your phone via SMS. Can you confirm your phone number?"
- "I couldn't find any providers in [location] at the moment. Let me escalate this to our support team - they can review our database and call you back within 24 hours. May I have your name, email, and phone number?"

**PREMIER HEALTH APOMODEN PLAN KNOWLEDGE BASE:**

**About Premier Health Insurance:**
- NHIA-licensed insurer operating since 2011
- Serves ~270 corporate policies and 100,000+ lives
- Specializes in Apomoden Plan for dependents of Ghanaians abroad and Ghana residents

**Apomoden Plan Coverage:**
- Network: 700+ service providers nationwide (medical, dental, optical, lab/diagnostics)
- All providers recognized by HeFRA & NHIA
- Coverage includes: consultation, treatment, medications, lab tests, imaging, minor surgeries
- Age ranges: 0-59, 60-69, 70-85 years with different premium tiers

**Premium Structure (Annual, paid in advance):**
- Ages 0-59: Base premium tier
- Ages 60-69: Higher premium tier
- Ages 70-85: Highest premium tier
- Exchange rate used: USD 1 = GHS 12.50

**Important Coverage Limitations:**
- First-year waiting period: Maternity care (antenatal, delivery, postnatal) and surgeries not covered in year 1
- Excluded: cosmetic procedures, overseas treatment, alternative therapies, fertility treatments, dental prosthetics, organ transplants

**Customer Service Contacts:**
- Marketing: 020-1354186 / 050-3328300
- Apomoden Operations: 050-1550579 / 050-1550580 (apomuden@premierhealthinsurance.org)
- Client Service: 059-6920715 (info@premierhealthinsurance.org)
- Website: premierhealthinsurance.org

**ID Cards & Administration:**
- One ID card per member per insurance year
- Replacement cards issued within 5 days (fee applies)
- Extensive IT & claims systems (RX Health) for utilization tracking

**When customers ask about:**
- Coverage details: Refer to Apomoden Plan specifics above
- Premium costs: Direct them to contact marketing team for current rates
- Claims: Explain the extensive IT systems and utilization tracking
- Waiting periods: Clearly explain first-year limitations
- Network providers: Emphasize 700+ nationwide network

Always remember: Your goal is to connect customers with the right healthcare providers quickly and efficiently while providing excellent customer service that reflects Premier Health's commitment to quality care and comprehensive Apomoden Plan coverage.`,
      voiceSettings: {
        provider: 'elevenlabs',
        voiceId: 'sarah_healthcare',
        model: 'eleven_turbo_v2',
        speed: 1.0,
        stability: 0.8,
        similarityBoost: 0.7
      },
      functions: [
        {
          name: 'search_healthcare_providers',
          description: 'Search for healthcare providers by query, location, specialty, or provider type',
          parameters: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Natural language search query (e.g., "eye doctor near East Legon")'
              },
              location: {
                type: 'string',
                description: 'Specific area or location in Greater Accra'
              },
              specialty: {
                type: 'string',
                description: 'Medical specialty (e.g., "ophthalmology", "pediatrics")'
              },
              provider_type: {
                type: 'string',
                description: 'Type of provider (e.g., "hospital", "clinic", "pharmacy")'
              },
              max_results: {
                type: 'integer',
                description: 'Maximum number of results to return (default: 5)',
                default: 5
              }
            },
            required: ['query']
          }
        },
        {
          name: 'get_emergency_providers',
          description: 'Get emergency healthcare providers and urgent care facilities',
          parameters: {
            type: 'object',
            properties: {
              location: {
                type: 'string',
                description: 'Customer location for finding nearest emergency facilities'
              },
              max_results: {
                type: 'integer',
                description: 'Maximum number of emergency facilities to return (default: 5)',
                default: 5
              }
            }
          }
        },
        {
          name: 'get_provider_details',
          description: 'Get detailed information about a specific healthcare provider',
          parameters: {
            type: 'object',
            properties: {
              provider_id: {
                type: 'integer',
                description: 'Unique identifier of the healthcare provider'
              }
            },
            required: ['provider_id']
          }
        },
        {
          name: 'send_provider_info_email',
          description: 'Send healthcare provider information via email to the caller',
          parameters: {
            type: 'object',
            properties: {
              email: {
                type: 'string',
                description: 'Customer email address to send provider information to'
              },
              provider_data: {
                type: 'array',
                description: 'List of provider information to include in the email'
              },
              search_query: {
                type: 'string',
                description: 'Original search query for reference in the email'
              },
              customer_name: {
                type: 'string',
                description: 'Customer name for personalization',
                default: 'Customer'
              }
            },
            required: ['email', 'provider_data']
          }
        },
        {
          name: 'send_provider_info_sms',
          description: 'Send healthcare provider information via SMS to the caller\'s phone',
          parameters: {
            type: 'object',
            properties: {
              phone: {
                type: 'string',
                description: 'Customer phone number to send provider information to (format: +233XXXXXXXXX)'
              },
              provider_data: {
                type: 'array',
                description: 'List of provider information to include in the SMS'
              },
              search_query: {
                type: 'string',
                description: 'Original search query for reference in the SMS'
              }
            },
            required: ['phone', 'provider_data']
          }
        },
        {
          name: 'escalate_to_support',
          description: 'Escalate query to Freshdesk support when location not found or customer needs additional assistance',
          parameters: {
            type: 'object',
            properties: {
              customer_name: {
                type: 'string',
                description: 'Customer\'s full name for the support ticket'
              },
              customer_email: {
                type: 'string',
                description: 'Customer\'s email address for follow-up communication'
              },
              customer_phone: {
                type: 'string',
                description: 'Customer\'s phone number for callback within 24 hours'
              },
              search_query: {
                type: 'string',
                description: 'Original search query that needs escalation'
              },
              location_searched: {
                type: 'string',
                description: 'Location that was not found or caused the issue'
              },
              issue_description: {
                type: 'string',
                description: 'Additional details about why escalation is needed',
                default: ''
              }
            },
            required: ['customer_name', 'customer_email', 'customer_phone', 'search_query', 'location_searched']
          }
        }
      ]
    },
    configurations: {
      vapi: {
        apiKey: '42cf1e7c-2ef9-4bd7-ba30-52f2813605a2',
        model: 'gpt-4o-mini',
        voice: {
          provider: 'eleven_labs',
          voiceId: 'sarah'
        },
        phoneNumberId: 'f4a4c2c4-ea24-4e8e-8c8b-f5b7a4d7a6c2'
      },
      n8n: {
        apiUrl: 'https://automate.inspirecreations.it.com',
        apiKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MTBhMTUzMi04YmRkLTRkYjAtYjU1OS01ZTIxYTAzNjI4ODMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU2NDQxNjg4fQ.oAcaO5v0As8jl543StOB87l21jkURptt7bn9X6E7NcU'
      },
      database: {
        type: 'postgresql',
        connectionString: 'postgresql://community_user:secure_password@localhost:5432/healthcare_community_db',
        schema: 'public'
      },
      integrations: {
        freshdesk: {
          url: 'https://ailabs-888099064326049059.myfreshworks.com/',
          apiKey: 'FRESHDESK_API_KEY_PLACEHOLDER'
        },
        vonage: {
          apiKey: '4109fdf7',
          apiSecret: 'mativo3saMI3cAWG',
          baseUrl: 'https://api.nexmo.com'
        },
        openai: {
          apiKey: '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'
        },
        resend: {
          apiKey: 're_fUUrbkMk_BzeDa7cCxa96waYmiVXxX9RT'
        },
        supabase: {
          projectId: 'ljzbzjgvwzivpmlmuxhx',
          secretKey: 'sb_secret_MSB5XcvfMpI5sJb-KcRGqA_8d-q7ehk'
        }
      },
      voiceTools: {
        pythonModulePath: '@apps/automations/premier-health/voice_agent_tools.py',
        className: 'HealthcareVoiceTools',
        functions: [
          'search_healthcare_providers',
          'get_emergency_providers',
          'get_provider_details',
          'get_available_areas',
          'get_available_specialties',
          'get_providers_by_area',
          'get_providers_by_specialty',
          'send_provider_info_email',
          'send_provider_info_sms',
          'escalate_to_support'
        ]
      },
      knowledgeBase: {
        defaultFiles: [
          '@apps/automations/premier-health/knowledge_base/apomoden_knowledge_base.docx'
        ],
        extractedContent: 'Premier Health Apomoden Plan knowledge integrated into system prompt'
      },
      deployment: {
        autoActivate: true,
        createWebhooks: true,
        enableMonitoring: true,
        testMode: false
      }
    },
    features: ['Voice-enabled search', 'Natural language processing', 'Emergency escalation', 'HIPAA compliance', 'Real-time analytics'],
    popular: false,
    rating: 4.8,
    usageCount: 0
  },

  // Enhanced Product Launch Announcement Template
  ENHANCED_PRODUCT_LAUNCH_ANNOUNCEMENT_TEMPLATE
];

// Helper functions
export const getTemplatesByIndustry = (industry: string): AutomationTemplate[] => {
  return AUTOMATION_TEMPLATES.filter(template => template.industry === industry);
};

export const getTemplatesByCategory = (category: string): AutomationTemplate[] => {
  return AUTOMATION_TEMPLATES.filter(template => template.category === category);
};

export const getIntegrationProviders = (categoryId: string): IntegrationProvider[] => {
  const category = INTEGRATION_CATEGORIES.find(cat => cat.id === categoryId);
  return category ? category.providers : [];
};

export const getTemplateComplexityColor = (complexity: string): string => {
  switch (complexity) {
    case 'Simple': return 'bg-green-100 text-green-800 border-green-200';
    case 'Medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'Advanced': return 'bg-red-100 text-red-800 border-red-200';
    default: return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

export const getIndustryIcon = (industry: string): string => {
  const icons = {
    healthcare: '🏥',
    financial: '🏦',
    retail: '🛒',
    manufacturing: '🏭',
    insurance: '🛡️',
    education: '🎓',
    real_estate: '🏠',
    telecom: '📡',
    automotive: '🚗',
    government: '🏛️',
    logistics: '📦',
    utilities: '⚡',
    professional_services: '💼',
    hospitality: '🏨',
    workflow: '⚙️',
    technology: '💻',
  };
  return icons[industry as keyof typeof icons] || '🏢';
};