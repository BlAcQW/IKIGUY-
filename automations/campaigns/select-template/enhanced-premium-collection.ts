/**
 * Enhanced Premium Collection Automation with VAPI + n8n
 *
 * Empathetic voice-enabled premium collection with payment facilitation,
 * hardship assessment, and compliance with debt collection regulations.
 */

import { generateVAPIConfig } from './vapi-config-standards';
import { generateN8nWorkflow } from './n8n-workflow-patterns';
import { generateMonitoringConfig } from './monitoring-integration';

export const ENHANCED_PREMIUM_COLLECTION_TEMPLATE = {
  id: 'enhanced_premium_collection_vapi_n8n',
  name: 'Enhanced Premium Collection with VAPI + n8n',
  description: 'Compassionate voice-enabled premium collection automation with AI-powered hardship assessment, flexible payment options, regulatory compliance, and real-time monitoring',
  industry: 'insurance',
  category: 'Financial Operations',
  complexity: 'Advanced' as const,
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
      id: 'check_payment_status',
      name: 'Check Current Payment Status',
      type: 'integration',
      integrationCategory: 'database',
      config: {
        capability: 'billing_inquiry',
        action: 'get_payment_status',
        n8n_node: 'HTTP Request',
        endpoint: '{{api_base_url}}/api/billing/payment-status',
        real_time_data: true
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
      id: 'payment_history_analysis',
      name: 'Payment History Pattern Analysis',
      type: 'integration',
      integrationCategory: 'analytics',
      config: {
        capability: 'payment_analytics',
        action: 'analyze_payment_patterns',
        n8n_node: 'HTTP Request',
        ml_prediction: true,
        risk_scoring: true
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
      id: 'process_immediate_payment',
      name: 'Process Immediate Payment',
      type: 'integration',
      integrationCategory: 'payment',
      config: {
        capability: 'payment_processing',
        action: 'process_payment',
        n8n_node: 'Payment Gateway',
        payment_methods: ['credit_card', 'bank_transfer', 'digital_wallet'],
        security_compliance: 'PCI_DSS'
      }
    },

    {
      id: 'setup_payment_plan',
      name: 'Setup Custom Payment Plan',
      type: 'integration',
      integrationCategory: 'database',
      config: {
        capability: 'payment_planning',
        action: 'create_payment_plan',
        n8n_node: 'HTTP Request',
        plan_types: ['weekly', 'bi_weekly', 'monthly'],
        auto_approval_limits: true
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
      id: 'customer_satisfaction_check',
      name: 'Post-Call Satisfaction Survey',
      type: 'integration',
      integrationCategory: 'messaging',
      config: {
        capability: 'customer_feedback',
        action: 'send_satisfaction_survey',
        n8n_node: 'Multi-Channel Notification',
        timing: 'immediate',
        channels: ['sms', 'email']
      }
    },

    {
      id: 'update_collection_analytics',
      name: 'Update Collection Performance Analytics',
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

  // VAPI Configuration for empathetic collection calls
  vapiConfig: generateVAPIConfig('insurance', {
    agentName: 'Premium Collection Assistant',
    agentRole: 'Financial Collections Specialist',
    specificExpertise: [
      'Payment assistance',
      'Financial hardship assessment',
      'Payment plan creation',
      'Debt collection regulations',
      'Customer retention strategies'
    ],
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
      },
      {
        name: 'scheduleCallback',
        description: 'Schedule a callback for further discussion',
        parameters: {
          type: 'object',
          properties: {
            preferredTime: { type: 'string' },
            reason: { type: 'string' },
            urgency: { type: 'string', enum: ['low', 'medium', 'high'] }
          },
          required: ['preferredTime', 'reason']
        }
      }
    ],
    systemPromptAdditions: `
Collection Call Guidelines:
- Always approach with empathy and understanding
- Listen actively to customer circumstances
- Offer solutions before discussing consequences
- Comply with all debt collection regulations (FDCPA, TCPA)
- Focus on customer retention and relationship preservation
- Document all promises and agreements clearly
- Escalate to human agents for complex hardship cases
- Never make threats or use aggressive language
- Respect customer preference for communication methods
- Maintain professional demeanor throughout the call

Important Compliance Rules:
- Only call between 8 AM and 9 PM in customer's time zone
- Stop calling if customer requests written communication only
- Clearly identify yourself and the purpose of the call
- Provide debt validation information when requested
- Honor payment arrangements once established
- Document all customer communications accurately
`
  }),

  // n8n Workflow Configuration
  n8nWorkflow: generateN8nWorkflow('enhanced_premium_collection_vapi_n8n', {
    name: 'Enhanced Premium Collection with VAPI + n8n',
    description: 'Empathetic collection workflow with payment facilitation',
    webhookPath: 'premium-collection-enhanced',
    industry: 'insurance',
    monitoringEnabled: true
  }),

  // Monitoring Configuration
  monitoringConfig: generateMonitoringConfig(
    'enhanced_premium_collection_vapi_n8n',
    'insurance',
    {
      dashboardConfig: {
        realTimeMetrics: [
          'collection_rate',
          'payment_plan_setup_rate',
          'customer_satisfaction',
          'compliance_score',
          'hardship_assistance_rate',
          'call_resolution_rate'
        ],
        customWidgets: [
          {
            id: 'collection_effectiveness',
            type: 'gauge',
            title: 'Collection Effectiveness',
            dataSource: 'collection_analytics',
            refreshInterval: 30000,
            config: {
              metric: 'total_collection_rate',
              format: 'percentage',
              target: 75,
              thresholds: {
                excellent: 80,
                good: 75,
                warning: 65,
                critical: 50
              }
            }
          },
          {
            id: 'compliance_monitoring',
            type: 'alert',
            title: 'Compliance Monitoring',
            dataSource: 'compliance_tracking',
            refreshInterval: 10000,
            config: {
              alertTypes: ['fdcpa_violation', 'tcpa_violation', 'state_law_issue'],
              severity: 'critical',
              autoEscalation: true,
              notificationChannels: ['email', 'slack', 'sms']
            }
          },
          {
            id: 'payment_plan_success',
            type: 'chart',
            title: 'Payment Plan Success Rate',
            dataSource: 'payment_analytics',
            refreshInterval: 60000,
            config: {
              chartType: 'line',
              timeRange: '30d',
              metrics: ['setup_rate', 'adherence_rate', 'completion_rate']
            }
          }
        ]
      }
    }
  ),

  complianceFrameworks: ['FDCPA', 'TCPA', 'State Collection Laws', 'PCI DSS'],

  features: [
    'Empathetic VAPI Voice Agent',
    'AI-Powered Hardship Assessment',
    'Flexible Payment Plan Creation',
    'Real-time Payment Processing',
    'Regulatory Compliance Monitoring',
    'Customer Retention Focus',
    'Adaptive Follow-up Scheduling',
    'Satisfaction Survey Integration',
    'Performance Analytics Dashboard',
    'Compliance Documentation'
  ],

  specializedServices: {
    monitoringService: 'PremiumCollectionMonitoringService',
    analyticsService: 'CollectionAnalyticsService',
    complianceService: 'DebtCollectionComplianceService',
    paymentService: 'FlexiblePaymentProcessingService'
  },

  securityConfig: {
    complianceFrameworks: ['FDCPA', 'TCPA', 'PCI DSS'],
    dataEncryption: true,
    auditTrail: true,
    accessControls: ['role_based', 'mfa_required', 'call_recording'],
    dataRetentionPolicy: '7_years',
    piiProtection: true,
    paymentSecurity: 'PCI_DSS_Level_1'
  }
};

export default ENHANCED_PREMIUM_COLLECTION_TEMPLATE;