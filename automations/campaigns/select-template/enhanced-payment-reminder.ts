/**
 * Enhanced Payment Reminder Campaign Template
 *
 * AI-powered payment collection and debt recovery featuring:
 * - VAPI voice agent with compliance and negotiation tools
 * - N8N workflow automation for escalation sequences
 * - Real-time analytics and compliance monitoring
 * - Accounting system integration (QuickBooks, Xero, etc.)
 * - Advanced payment options and settlement workflows
 */

import { TemplateToVAPIDeployment, TemplateVAPIDeploymentConfig } from './template-to-vapi-deployment';

export const ENHANCED_PAYMENT_REMINDER_TEMPLATE = {
  id: 'enhanced_payment_reminder_vapi_n8n',
  name: 'Enhanced Payment Reminder with VAPI + n8n',
  description: 'AI-powered debt collection and payment recovery featuring personalized voice calls, compliance monitoring, escalation sequences, payment plan negotiation, and comprehensive collection analytics',
  industry: 'financial',
  category: 'Finance & Collections',
  complexity: 'Advanced' as const,
  estimatedTime: '45 min',
  rating: 4.9,
  usageCount: 156,
  popular: true,
  integrationCategories: [
    'Voice AI',
    'Workflow Automation',
    'Compliance',
    'Payment Processing',
    'Analytics',
    'CRM Integration'
  ],

  // Template-to-VAPI Deployment Configuration
  deploymentConfig: {
    enableAutoDeployment: true,
    useVAPIAgentWizard: true,
    complianceFrameworks: ['FDCPA', 'TCPA', 'PCI-DSS'],
    securityConfig: {
      accessControls: ['role_based', 'encryption', 'audit_logging'],
      dataRetention: '7_years',
      sensitiveDataHandling: 'masked'
    }
  } as const,

  // VAPI Configuration
  vapiConfig: {
    assistantId: 'asst_payment_reminder_enhanced',
    name: 'AI Payment Collection Agent',
    model: 'gpt-4',
    voice: {
      provider: 'rime-ai',
      voiceId: 'jennifer',
      speed: 1.0,
      stability: 0.8,
      clarity: 0.9
    },
    firstMessage: "Hello, this is Jennifer calling from the collections department regarding your account. I'm here to help you resolve your outstanding balance and discuss payment options that work for your situation.",
    systemPrompt: `You are a professional AI debt collection agent trained in FDCPA and TCPA compliance. Your role is to:

1. **Identity Verification**: Verify customer identity using security questions
2. **Account Review**: Present balance information clearly and professionally
3. **Payment Negotiation**: Offer payment plans, settlements, and hardship programs
4. **Compliance Monitoring**: Ensure all interactions follow debt collection laws
5. **Documentation**: Record all payment promises and agreements

COMPLIANCE REQUIREMENTS:
- Always identify yourself and the company at the beginning
- Verify customer identity before discussing account details
- Respect dispute requests and cease collection if disputed
- Offer payment plan options for financial hardship
- Maintain professional, respectful tone throughout
- Document all interactions for compliance records

TOOLS AVAILABLE:
- get_account_details: Retrieve current balance and payment history
- verify_customer_identity: Secure identity verification process
- calculate_payment_plans: Generate affordable payment options
- process_payment: Secure payment processing with multiple methods
- schedule_payment: Set up future payment arrangements
- handle_dispute: Properly process dispute requests
- check_compliance_status: Verify account compliance requirements
- generate_settlement_offer: Create settlement proposals when appropriate
- record_interaction: Document all call details and outcomes
- escalate_to_supervisor: Transfer complex cases to human agents

Always prioritize customer service while maintaining professional collection standards.`,

    functions: [
      {
        name: 'get_account_details',
        description: 'Retrieve comprehensive account information including balance, payment history, and account status',
        parameters: {
          type: 'object',
          properties: {
            account_number: {
              type: 'string',
              description: 'Customer account number for lookup'
            },
            include_history: {
              type: 'boolean',
              description: 'Include detailed payment history',
              default: true
            }
          },
          required: ['account_number']
        }
      },
      {
        name: 'verify_customer_identity',
        description: 'Securely verify customer identity using multiple security questions',
        parameters: {
          type: 'object',
          properties: {
            account_number: {
              type: 'string',
              description: 'Account number for verification'
            },
            verification_method: {
              type: 'string',
              enum: ['ssn_last_four', 'billing_address', 'phone_number', 'date_of_birth'],
              description: 'Method for identity verification'
            },
            provided_value: {
              type: 'string',
              description: 'Value provided by customer for verification'
            }
          },
          required: ['account_number', 'verification_method', 'provided_value']
        }
      },
      {
        name: 'calculate_payment_plans',
        description: 'Generate affordable payment plan options based on customer financial situation',
        parameters: {
          type: 'object',
          properties: {
            account_number: {
              type: 'string',
              description: 'Customer account number'
            },
            current_balance: {
              type: 'number',
              description: 'Outstanding balance amount'
            },
            customer_budget: {
              type: 'number',
              description: 'Customer stated monthly payment capability'
            },
            payment_frequency: {
              type: 'string',
              enum: ['weekly', 'bi_weekly', 'monthly'],
              description: 'Preferred payment frequency',
              default: 'monthly'
            },
            down_payment: {
              type: 'number',
              description: 'Initial down payment amount',
              default: 0
            }
          },
          required: ['account_number', 'current_balance']
        }
      },
      {
        name: 'process_payment',
        description: 'Securely process customer payment using various payment methods',
        parameters: {
          type: 'object',
          properties: {
            account_number: {
              type: 'string',
              description: 'Customer account number'
            },
            payment_amount: {
              type: 'number',
              description: 'Payment amount to process'
            },
            payment_method: {
              type: 'string',
              enum: ['credit_card', 'debit_card', 'ach_bank_transfer', 'check_by_phone'],
              description: 'Payment method selection'
            },
            payment_details: {
              type: 'object',
              description: 'Payment method specific details (encrypted)'
            },
            is_recurring: {
              type: 'boolean',
              description: 'Set up recurring payment',
              default: false
            }
          },
          required: ['account_number', 'payment_amount', 'payment_method']
        }
      },
      {
        name: 'schedule_payment',
        description: 'Schedule future payment arrangements and set up payment reminders',
        parameters: {
          type: 'object',
          properties: {
            account_number: {
              type: 'string',
              description: 'Customer account number'
            },
            payment_date: {
              type: 'string',
              format: 'date',
              description: 'Scheduled payment date (YYYY-MM-DD)'
            },
            payment_amount: {
              type: 'number',
              description: 'Amount to be paid'
            },
            payment_method: {
              type: 'string',
              enum: ['credit_card', 'debit_card', 'ach_bank_transfer', 'manual_payment'],
              description: 'Method for scheduled payment'
            },
            send_reminder: {
              type: 'boolean',
              description: 'Send payment reminder notifications',
              default: true
            },
            reminder_days_before: {
              type: 'number',
              description: 'Days before payment to send reminder',
              default: 3
            }
          },
          required: ['account_number', 'payment_date', 'payment_amount']
        }
      },
      {
        name: 'handle_dispute',
        description: 'Process customer disputes and initiate proper dispute handling procedures',
        parameters: {
          type: 'object',
          properties: {
            account_number: {
              type: 'string',
              description: 'Customer account number'
            },
            dispute_reason: {
              type: 'string',
              enum: ['never_received_service', 'incorrect_amount', 'already_paid', 'identity_theft', 'billing_error', 'other'],
              description: 'Reason for dispute'
            },
            dispute_details: {
              type: 'string',
              description: 'Detailed description of the dispute'
            },
            pause_collections: {
              type: 'boolean',
              description: 'Temporarily pause collection activities',
              default: true
            }
          },
          required: ['account_number', 'dispute_reason', 'dispute_details']
        }
      },
      {
        name: 'check_compliance_status',
        description: 'Verify account compliance with FDCPA, TCPA, and state regulations',
        parameters: {
          type: 'object',
          properties: {
            account_number: {
              type: 'string',
              description: 'Customer account number'
            },
            customer_state: {
              type: 'string',
              description: 'Customer state for regulation compliance'
            },
            interaction_type: {
              type: 'string',
              enum: ['voice_call', 'text_message', 'email', 'letter'],
              description: 'Type of customer interaction'
            }
          },
          required: ['account_number', 'interaction_type']
        }
      },
      {
        name: 'generate_settlement_offer',
        description: 'Create settlement offers for accounts that qualify for reduced payment',
        parameters: {
          type: 'object',
          properties: {
            account_number: {
              type: 'string',
              description: 'Customer account number'
            },
            current_balance: {
              type: 'number',
              description: 'Current outstanding balance'
            },
            customer_financial_hardship: {
              type: 'string',
              enum: ['temporary', 'permanent', 'unemployment', 'medical', 'other'],
              description: 'Type of financial hardship'
            },
            proposed_settlement_percentage: {
              type: 'number',
              minimum: 30,
              maximum: 90,
              description: 'Proposed settlement as percentage of balance'
            },
            payment_terms: {
              type: 'string',
              enum: ['lump_sum', 'three_payments', 'six_payments'],
              description: 'Settlement payment terms'
            }
          },
          required: ['account_number', 'current_balance', 'customer_financial_hardship']
        }
      },
      {
        name: 'record_interaction',
        description: 'Document all call details, customer responses, and outcomes for compliance',
        parameters: {
          type: 'object',
          properties: {
            account_number: {
              type: 'string',
              description: 'Customer account number'
            },
            interaction_summary: {
              type: 'string',
              description: 'Summary of the interaction'
            },
            customer_response: {
              type: 'string',
              enum: ['payment_made', 'payment_promised', 'dispute_raised', 'hardship_claimed', 'refused_to_pay', 'hung_up'],
              description: 'Customer response category'
            },
            next_action: {
              type: 'string',
              description: 'Next follow-up action required'
            },
            compliance_notes: {
              type: 'string',
              description: 'Any compliance-related notes'
            },
            call_recording_id: {
              type: 'string',
              description: 'Call recording reference ID'
            }
          },
          required: ['account_number', 'interaction_summary', 'customer_response']
        }
      },
      {
        name: 'escalate_to_supervisor',
        description: 'Transfer complex cases or disputes to human supervisors',
        parameters: {
          type: 'object',
          properties: {
            account_number: {
              type: 'string',
              description: 'Customer account number'
            },
            escalation_reason: {
              type: 'string',
              enum: ['complex_dispute', 'customer_request', 'legal_threat', 'hardship_verification', 'large_settlement'],
              description: 'Reason for escalation'
            },
            customer_mood: {
              type: 'string',
              enum: ['cooperative', 'frustrated', 'angry', 'confused'],
              description: 'Customer emotional state'
            },
            context_summary: {
              type: 'string',
              description: 'Summary of situation for supervisor'
            },
            urgent: {
              type: 'boolean',
              description: 'Mark as urgent escalation',
              default: false
            }
          },
          required: ['account_number', 'escalation_reason', 'context_summary']
        }
      }
    ]
  },

  // N8N Workflow Configuration
  n8nConfig: {
    workflowName: 'Enhanced Payment Reminder Automation',
    description: 'Comprehensive payment collection workflow with AI voice agents, compliance monitoring, and multi-channel escalation',

    nodes: [
      {
        name: 'Payment Reminder Webhook',
        type: 'webhook',
        description: 'Trigger point for initiating payment reminder campaigns'
      },
      {
        name: 'Account Data Retrieval',
        type: 'accounting-integration',
        description: 'Fetch account details from QuickBooks/Xero/Sage'
      },
      {
        name: 'Compliance Check',
        type: 'compliance-validator',
        description: 'Verify FDCPA/TCPA compliance before contact'
      },
      {
        name: 'Customer Segmentation',
        type: 'ai-classifier',
        description: 'Segment customers by risk level and payment history'
      },
      {
        name: 'VAPI Payment Collection Call',
        type: 'vapi-voice-agent',
        description: 'AI-powered collection call with negotiation capabilities'
      },
      {
        name: 'Payment Processing',
        type: 'payment-processor',
        description: 'Process payments via Stripe/ACH integration'
      },
      {
        name: 'Escalation Logic',
        type: 'conditional-router',
        description: 'Route to appropriate escalation based on outcome'
      },
      {
        name: 'Dispute Handling',
        type: 'dispute-processor',
        description: 'Process disputes and pause collections'
      },
      {
        name: 'Settlement Calculator',
        type: 'settlement-engine',
        description: 'Calculate and generate settlement offers'
      },
      {
        name: 'CRM Update',
        type: 'crm-integration',
        description: 'Update customer records with interaction results'
      },
      {
        name: 'Compliance Documentation',
        type: 'compliance-logger',
        description: 'Document all interactions for regulatory compliance'
      },
      {
        name: 'Analytics Tracking',
        type: 'analytics-collector',
        description: 'Track collection metrics and performance'
      },
      {
        name: 'Follow-up Scheduler',
        type: 'scheduler',
        description: 'Schedule follow-up actions based on outcomes'
      }
    ],

    // Based on Invoice Processing templates found
    templateInspiration: {
      invoiceProcessing: 3016, // "Invoices from Gmail to Drive and Google Sheets"
      documentClassification: 4557, // "Intelligent Email Organization with AI-Powered Content Classification"
      aiDocumentParsing: 3005, // "Advanced AI Powered Document Parsing & Text Extraction"
      invoiceValidation: 4247 // "Invoice Processor & Validator with OCR, AI & Google Sheets"
    }
  },

  // Workflow Steps
  workflowSteps: [
    {
      id: 'setup',
      title: 'Campaign Setup',
      description: 'Configure payment reminder campaign parameters',
      estimatedTime: '5 min',
      requirements: ['Account credentials', 'Compliance settings', 'Campaign parameters']
    },
    {
      id: 'account-integration',
      title: 'Accounting System Integration',
      description: 'Connect to QuickBooks, Xero, or Sage for account data',
      estimatedTime: '8 min',
      requirements: ['Accounting system API keys', 'Data sync permissions']
    },
    {
      id: 'vapi-configuration',
      title: 'VAPI Voice Agent Setup',
      description: 'Configure AI collection agent with compliance tools',
      estimatedTime: '10 min',
      requirements: ['VAPI account', 'Voice agent configuration', 'Compliance prompts']
    },
    {
      id: 'payment-processing',
      title: 'Payment Gateway Integration',
      description: 'Set up Stripe, ACH, and payment plan processing',
      estimatedTime: '8 min',
      requirements: ['Payment processor credentials', 'Merchant accounts']
    },
    {
      id: 'compliance-setup',
      title: 'Compliance & Legal Configuration',
      description: 'Configure FDCPA/TCPA compliance monitoring',
      estimatedTime: '7 min',
      requirements: ['Compliance rules', 'State regulations', 'Legal escalation contacts']
    },
    {
      id: 'analytics-dashboard',
      title: 'Analytics & Reporting Setup',
      description: 'Configure collection metrics and compliance reporting',
      estimatedTime: '5 min',
      requirements: ['Dashboard access', 'Reporting requirements']
    },
    {
      id: 'testing',
      title: 'Testing & Validation',
      description: 'Test complete workflow with sample accounts',
      estimatedTime: '2 min',
      requirements: ['Test accounts', 'Validation checklist']
    }
  ],

  // Integration Requirements
  integrations: [
    {
      name: 'VAPI',
      type: 'voice-ai',
      required: true,
      description: 'AI voice agent for collection calls',
      apiKey: 'VAPI_PRIVATE_KEY',
      setupUrl: 'https://dashboard.vapi.ai'
    },
    {
      name: 'N8N',
      type: 'workflow-automation',
      required: true,
      description: 'Workflow automation and orchestration',
      apiKey: 'N8N_API_KEY',
      setupUrl: 'https://automate.inspirecreations.it.com'
    },
    {
      name: 'QuickBooks/Xero/Sage',
      type: 'accounting-system',
      required: true,
      description: 'Accounting system for customer account data',
      apiKey: 'ACCOUNTING_API_KEY',
      setupUrl: 'Various'
    },
    {
      name: 'Stripe',
      type: 'payment-processing',
      required: true,
      description: 'Payment processing for collections',
      apiKey: 'STRIPE_SECRET_KEY',
      setupUrl: 'https://dashboard.stripe.com'
    },
    {
      name: 'Freshdesk',
      type: 'crm-ticketing',
      required: false,
      description: 'CRM integration for customer records',
      apiKey: 'FRESHDESK_API_KEY',
      setupUrl: 'https://ailabs-888099064326049059.myfreshworks.com/'
    },
    {
      name: 'Vonage',
      type: 'telephony',
      required: false,
      description: 'Telephony infrastructure for calls',
      apiKey: 'VONAGE_API_KEY',
      setupUrl: 'https://api.nexmo.com'
    }
  ],

  // Analytics & Monitoring
  analytics: {
    collectionMetrics: [
      'Recovery Rate (%)',
      'Average Time to Payment',
      'Contact Success Rate',
      'Settlement Ratio',
      'Payment Plan Success Rate',
      'Dispute Resolution Time'
    ],
    complianceMetrics: [
      'FDCPA Compliance Score',
      'TCPA Violation Alerts',
      'Call Recording Completion',
      'Documentation Completeness',
      'Legal Escalation Rate'
    ],
    operationalMetrics: [
      'Call Volume',
      'Agent Utilization',
      'Cost per Collection',
      'Revenue Recovery',
      'Customer Satisfaction',
      'Process Automation Rate'
    ]
  },

  // Compliance Features
  compliance: {
    fdcpaCompliant: true,
    tcpaCompliant: true,
    stateRegulations: true,
    callRecording: true,
    disputeHandling: true,
    legalEscalation: true,
    auditTrail: true,
    dataRetention: '7 years'
  }
};

// Template-to-VAPI Deployment Functions
export const deployEnhancedPaymentReminderToVAPI = async (apiConfig: {
  vapiApiKey: string;
  n8nApiKey: string;
  webhookBaseUrl: string;
}): Promise<TemplateVAPIDeploymentConfig> => {

  const deploymentConfig = TemplateToVAPIDeployment.generateVAPIAgentFromTemplate(
    ENHANCED_PAYMENT_REMINDER_TEMPLATE,
    {
      deploymentSettings: {
        environment: 'production',
        autoStart: true,
        monitoring: {
          enabled: true,
          alerting: true,
          dashboardUrl: `/monitoring/payment-reminder`
        },
        security: {
          encryption: true,
          auditLogging: true,
          accessControl: ['role_based', 'compliance_officer', 'financial_admin']
        }
      }
    }
  );

  return deploymentConfig;
};

export const validatePaymentReminderCompliance = (config: any): {
  isCompliant: boolean;
  violations: string[];
  recommendations: string[];
} => {
  const violations: string[] = [];
  const recommendations: string[] = [];

  // FDCPA Compliance Checks
  if (!config.vapiConfig?.systemPrompt?.includes('FDCPA')) {
    violations.push('Missing FDCPA compliance requirements in system prompt');
  }

  if (!config.functions?.find((f: any) => f.name === 'verify_customer_identity')) {
    violations.push('Missing customer identity verification function');
  }

  if (!config.functions?.find((f: any) => f.name === 'handle_dispute')) {
    violations.push('Missing dispute handling capability');
  }

  // TCPA Compliance Checks
  if (!config.vapiConfig?.systemPrompt?.includes('TCPA')) {
    violations.push('Missing TCPA compliance requirements');
  }

  // Data Security Checks
  if (!config.deploymentConfig?.securityConfig?.accessControls?.includes('encryption')) {
    violations.push('Missing data encryption requirements');
  }

  // Recommendations
  if (violations.length === 0) {
    recommendations.push('All compliance requirements are met');
    recommendations.push('Consider adding additional payment plan options');
    recommendations.push('Implement advanced sentiment analysis for better customer experience');
  }

  return {
    isCompliant: violations.length === 0,
    violations,
    recommendations
  };
};

export default ENHANCED_PAYMENT_REMINDER_TEMPLATE;