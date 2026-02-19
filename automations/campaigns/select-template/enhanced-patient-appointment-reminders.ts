/**
 * Enhanced Patient Appointment Reminders with VAPI + n8n
 *
 * HIPAA-compliant voice-enabled appointment reminder system with
 * intelligent scheduling, no-show prediction, and patient engagement.
 */

import { generateVAPIConfig } from './vapi-config-standards';
import { generateN8nWorkflow } from './n8n-workflow-patterns';
import { generateMonitoringConfig } from './monitoring-integration';

export const ENHANCED_PATIENT_APPOINTMENT_REMINDERS_TEMPLATE = {
  id: 'enhanced_patient_appointment_reminders_vapi_n8n',
  name: 'Enhanced Patient Appointment Reminders with VAPI + n8n',
  description: 'HIPAA-compliant voice-enabled appointment reminder system with AI-powered no-show prediction, intelligent scheduling optimization, patient engagement tracking, and comprehensive healthcare analytics',
  industry: 'healthcare',
  category: 'Patient Management',
  complexity: 'Advanced' as const,
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
      id: 'fetch_appointment_details',
      name: 'Fetch Appointment Information',
      type: 'integration',
      integrationCategory: 'database',
      config: {
        capability: 'appointment_management',
        action: 'get_appointment_details',
        n8n_node: 'HTTP Request',
        endpoint: '{{api_base_url}}/api/appointments/details',
        hipaa_secure_api: true,
        data_minimization: true
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
      id: 'check_patient_preferences',
      name: 'Check Communication Preferences',
      type: 'integration',
      integrationCategory: 'database',
      config: {
        capability: 'patient_preferences',
        action: 'get_communication_settings',
        n8n_node: 'HTTP Request',
        preference_types: ['call_time', 'language', 'reminder_frequency'],
        consent_validation: true
      }
    },

    {
      id: 'deliver_personalized_reminder',
      name: 'Deliver Personalized Reminder',
      type: 'condition',
      config: {
        condition: 'no_show_risk > 0.6 OR patient_preference == "detailed_reminder"',
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
      id: 'schedule_follow_up_reminder',
      name: 'Schedule Follow-up Reminder',
      type: 'integration',
      integrationCategory: 'automation',
      config: {
        capability: 'reminder_scheduling',
        action: 'schedule_additional_reminders',
        n8n_node: 'Schedule Trigger',
        adaptive_timing: true,
        reminder_sequence: ['24_hour', '2_hour', 'day_of']
      }
    },

    {
      id: 'update_provider_schedule',
      name: 'Update Provider Schedule',
      type: 'integration',
      integrationCategory: 'calendar',
      config: {
        capability: 'schedule_management',
        action: 'update_provider_availability',
        n8n_node: 'Calendar Integration',
        real_time_sync: true,
        capacity_optimization: true
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
      id: 'update_appointment_analytics',
      name: 'Update Appointment Analytics',
      type: 'integration',
      integrationCategory: 'analytics',
      config: {
        capability: 'appointment_analytics',
        action: 'update_performance_metrics',
        n8n_node: 'HTTP Request',
        endpoint: '{{api_base_url}}/api/monitoring/appointment-metrics',
        dashboard_integration: true
      }
    }
  ],

  // VAPI Configuration for healthcare appointment reminders
  vapiConfig: generateVAPIConfig('healthcare', {
    agentName: 'Appointment Reminder Assistant',
    agentRole: 'Healthcare Appointment Coordinator',
    specificExpertise: [
      'Appointment scheduling',
      'Patient communication',
      'Medical prep instructions',
      'HIPAA compliance',
      'Healthcare customer service'
    ],
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
        name: 'requestTransportationAssistance',
        description: 'Request transportation assistance for appointment',
        parameters: {
          type: 'object',
          properties: {
            appointmentId: { type: 'string' },
            transportationType: { type: 'string', enum: ['medical_transport', 'rideshare', 'family'] },
            specialNeeds: { type: 'string' }
          },
          required: ['appointmentId', 'transportationType']
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
    systemPromptAdditions: `
Healthcare Appointment Reminder Guidelines:
- Always maintain HIPAA compliance and patient confidentiality
- Use professional, caring, and empathetic tone
- Verify patient identity before discussing appointment details
- Provide clear appointment information (date, time, location, provider)
- Offer preparation instructions when relevant
- Be flexible with rescheduling needs
- Respect patient communication preferences
- Document all interactions in compliance with healthcare regulations
- Escalate complex medical questions to healthcare providers
- Ensure accessibility for patients with special needs

HIPAA Compliance Requirements:
- Only discuss appointments with verified patients
- Do not leave detailed voicemail messages
- Use minimum necessary information principle
- Respect patient rights and preferences
- Maintain audit trail of all communications
- Follow organizational privacy policies
`
  }),

  // n8n Workflow Configuration
  n8nWorkflow: generateN8nWorkflow('enhanced_patient_appointment_reminders_vapi_n8n', {
    name: 'Enhanced Patient Appointment Reminders with VAPI + n8n',
    description: 'HIPAA-compliant appointment reminder workflow with voice agent',
    webhookPath: 'patient-appointment-reminders-enhanced',
    industry: 'healthcare',
    monitoringEnabled: true
  }),

  // Monitoring Configuration
  monitoringConfig: generateMonitoringConfig(
    'enhanced_patient_appointment_reminders_vapi_n8n',
    'healthcare',
    {
      dashboardConfig: {
        realTimeMetrics: [
          'reminder_delivery_rate',
          'appointment_confirmation_rate',
          'no_show_reduction',
          'patient_satisfaction',
          'rescheduling_rate',
          'compliance_score'
        ],
        customWidgets: [
          {
            id: 'no_show_prediction_accuracy',
            type: 'gauge',
            title: 'No-Show Prediction Accuracy',
            dataSource: 'prediction_analytics',
            refreshInterval: 30000,
            config: {
              metric: 'prediction_accuracy',
              format: 'percentage',
              target: 85,
              thresholds: {
                excellent: 90,
                good: 85,
                warning: 75,
                critical: 65
              }
            }
          },
          {
            id: 'hipaa_compliance_monitoring',
            type: 'alert',
            title: 'HIPAA Compliance Monitoring',
            dataSource: 'compliance_tracking',
            refreshInterval: 10000,
            config: {
              alertTypes: ['phi_exposure', 'unauthorized_access', 'audit_trail_gap'],
              severity: 'critical',
              autoEscalation: true,
              notificationChannels: ['email', 'pager']
            }
          },
          {
            id: 'appointment_efficiency',
            type: 'chart',
            title: 'Appointment Efficiency Trends',
            dataSource: 'appointment_analytics',
            refreshInterval: 60000,
            config: {
              chartType: 'area',
              timeRange: '30d',
              metrics: ['utilization_rate', 'reminder_effectiveness', 'patient_satisfaction']
            }
          }
        ]
      }
    }
  ),

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

  securityConfig: {
    complianceFrameworks: ['HIPAA', 'SOC2', 'GDPR'],
    dataEncryption: true,
    auditTrail: true,
    accessControls: ['role_based', 'mfa_required', 'session_timeout'],
    dataRetentionPolicy: '6_years',
    phiProtection: true,
    patientConsent: true,
    dataMinimization: true
  }
};

export default ENHANCED_PATIENT_APPOINTMENT_REMINDERS_TEMPLATE;