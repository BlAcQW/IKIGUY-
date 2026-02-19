/**
 * Enhanced Insurance Customer Service Automation with VAPI + n8n
 *
 * Complete implementation based on standardized patterns and best practices.
 * Includes VAPI voice agent, n8n workflow orchestration, and comprehensive monitoring.
 */

import { generateVAPIConfig } from './vapi-config-standards';
import { generateN8nWorkflow } from './n8n-workflow-patterns';
import { generateMonitoringConfig } from './monitoring-integration';

export interface EnhancedInsuranceCustomerServiceTemplate {
  id: string;
  name: string;
  description: string;
  industry: string;
  category: string;
  complexity: 'Advanced';
  estimatedTime: string;
  integrationCategories: string[];
  defaultIntegrations: string[];
  workflow: any[]; // Enhanced workflow steps
  vapiConfig: any; // VAPI configuration
  n8nWorkflow: any; // n8n workflow definition
  monitoringConfig: any; // Monitoring configuration
  complianceFrameworks: string[];
  features: string[];
  specializedServices: any;
  securityConfig: any;
}

/**
 * Enhanced Insurance Customer Service Automation Template
 */
export const ENHANCED_INSURANCE_CUSTOMER_SERVICE_TEMPLATE: EnhancedInsuranceCustomerServiceTemplate = {
  id: 'enhanced_insurance_customer_service_vapi_n8n',
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
      id: 'claims_processing_route',
      name: 'Route to Claims Department',
      type: 'integration',
      integrationCategory: 'automation',
      config: {
        capability: 'claims_workflow',
        action: 'initiate_claims_process',
        n8n_node: 'HTTP Request',
        workflow_integration: 'claims_processing_automation',
        priority_escalation: true
      }
    },

    {
      id: 'billing_support_route',
      name: 'Route to Billing Support',
      type: 'integration',
      integrationCategory: 'database',
      config: {
        capability: 'billing_support',
        action: 'handle_billing_inquiry',
        n8n_node: 'HTTP Request',
        payment_integration: true,
        account_analysis: true
      }
    },

    {
      id: 'policy_management_route',
      name: 'Route to Policy Management',
      type: 'integration',
      integrationCategory: 'database',
      config: {
        capability: 'policy_management',
        action: 'handle_policy_changes',
        n8n_node: 'HTTP Request',
        underwriting_integration: true,
        compliance_check: true
      }
    },

    {
      id: 'general_support_route',
      name: 'Route to General Support',
      type: 'integration',
      integrationCategory: 'messaging',
      config: {
        capability: 'general_support',
        action: 'handle_general_inquiry',
        n8n_node: 'HTTP Request',
        knowledge_base_integration: true,
        escalation_rules: true
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
      id: 'customer_satisfaction_survey',
      name: 'Automated Satisfaction Survey',
      type: 'integration',
      integrationCategory: 'messaging',
      config: {
        capability: 'customer_feedback',
        action: 'send_satisfaction_survey',
        n8n_node: 'Multi-Channel Notification',
        delivery_delay: '1_hour',
        personalization: true
      }
    },

    {
      id: 'case_resolution_tracking',
      name: 'Track Case Resolution',
      type: 'integration',
      integrationCategory: 'analytics',
      config: {
        capability: 'case_analytics',
        action: 'track_resolution_metrics',
        n8n_node: 'HTTP Request',
        sla_monitoring: true,
        performance_kpis: true
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

  // VAPI Configuration using standardized patterns
  vapiConfig: generateVAPIConfig('insurance', {
    agentName: 'Insurance Service Assistant',
    agentRole: 'Customer Service Representative',
    specificExpertise: [
      'Policy inquiries',
      'Claims assistance',
      'Billing support',
      'Coverage explanations',
      'Account management'
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
        name: 'checkPaymentStatus',
        description: 'Check the status of premium payments or claim payments',
        parameters: {
          type: 'object',
          properties: {
            paymentType: { type: 'string', enum: ['premium', 'claim'] },
            referenceNumber: { type: 'string' }
          },
          required: ['paymentType']
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
      },
      {
        name: 'updateContactPreferences',
        description: 'Update customer communication preferences',
        parameters: {
          type: 'object',
          properties: {
            emailPreference: { type: 'boolean' },
            smsPreference: { type: 'boolean' },
            callPreference: { type: 'boolean' },
            preferredTime: { type: 'string' }
          },
          required: []
        }
      }
    ],
    systemPromptAdditions: `
Important Guidelines:
- Always verify customer identity before discussing policy details
- Be empathetic when handling claims or complaints
- Escalate to human agents for complex policy changes
- Maintain detailed records of all interactions
- Follow NAIC guidelines for customer communications
- Identify potential fraud indicators and escalate appropriately
- Ensure regulatory compliance in all responses
`
  }),

  // n8n Workflow Configuration
  n8nWorkflow: generateN8nWorkflow('enhanced_insurance_customer_service_vapi_n8n', {
    name: 'Enhanced Insurance Customer Service with VAPI + n8n',
    description: 'Complete customer service workflow with voice agent integration',
    webhookPath: 'insurance-customer-service-enhanced',
    industry: 'insurance',
    monitoringEnabled: true
  }),

  // Monitoring Configuration
  monitoringConfig: generateMonitoringConfig(
    'enhanced_insurance_customer_service_vapi_n8n',
    'insurance',
    {
      dashboardConfig: {
        realTimeMetrics: [
          'call_volume',
          'resolution_rate',
          'customer_satisfaction',
          'fraud_detection_rate',
          'average_handling_time',
          'first_call_resolution'
        ],
        customWidgets: [
          {
            id: 'service_level_agreement',
            type: 'gauge',
            title: 'SLA Compliance',
            dataSource: 'case_management',
            refreshInterval: 30000,
            config: {
              metric: 'sla_compliance_rate',
              format: 'percentage',
              target: 95,
              thresholds: {
                excellent: 98,
                good: 95,
                warning: 90,
                critical: 85
              }
            }
          },
          {
            id: 'fraud_alerts',
            type: 'alert',
            title: 'Real-time Fraud Alerts',
            dataSource: 'fraud_detection',
            refreshInterval: 10000,
            config: {
              alertTypes: ['high_risk_call', 'suspicious_pattern', 'known_fraudster'],
              severity: 'high',
              autoEscalation: true
            }
          }
        ]
      }
    }
  ),

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

  specializedServices: {
    monitoringService: 'InsuranceCustomerServiceMonitoringService',
    analyticsService: 'CustomerServiceAnalyticsService',
    complianceService: 'InsuranceComplianceService',
    fraudDetectionService: 'RealTimeFraudDetectionService'
  },

  securityConfig: {
    complianceFrameworks: ['NAIC', 'SOX', 'State Regulations'],
    dataEncryption: true,
    auditTrail: true,
    accessControls: ['role_based', 'mfa_required', 'session_timeout'],
    dataRetentionPolicy: '7_years',
    piiProtection: true,
    regulatoryReporting: true
  }
};

/**
 * Template Deployment Configuration
 */
export const DEPLOYMENT_CONFIG = {
  environment: {
    development: {
      n8nInstance: 'https://dev-n8n.kasaai.com',
      vapiInstance: 'https://dev-vapi.kasaai.com',
      monitoringDashboard: 'https://dev-monitoring.kasaai.com'
    },
    staging: {
      n8nInstance: 'https://staging-n8n.kasaai.com',
      vapiInstance: 'https://staging-vapi.kasaai.com',
      monitoringDashboard: 'https://staging-monitoring.kasaai.com'
    },
    production: {
      n8nInstance: 'https://n8n.kasaai.com',
      vapiInstance: 'https://vapi.kasaai.com',
      monitoringDashboard: 'https://monitoring.kasaai.com'
    }
  },

  requiredEnvironmentVariables: [
    'API_BASE_URL',
    'TENANT_ID',
    'VAPI_API_KEY',
    'N8N_API_KEY',
    'OPENAI_API_KEY',
    'DATABASE_CONNECTION_STRING',
    'MONITORING_WEBHOOK_SECRET'
  ],

  setupInstructions: [
    '1. Deploy n8n workflow to configured instance',
    '2. Configure VAPI agent with provided configuration',
    '3. Set up monitoring dashboard and alerts',
    '4. Configure database connections and API endpoints',
    '5. Test end-to-end workflow with sample data',
    '6. Enable compliance logging and audit trails',
    '7. Configure fraud detection thresholds',
    '8. Set up customer satisfaction survey automation'
  ]
};

export default ENHANCED_INSURANCE_CUSTOMER_SERVICE_TEMPLATE;