/**
 * Enhanced Appointment Booking Template with VAPI + N8N Integration
 *
 * AI-powered appointment booking and scheduling campaign featuring intelligent calendar management,
 * personalized consultation scheduling, availability optimization, and comprehensive booking analytics.
 */

import { TemplateToVAPIDeployment, TemplateVAPIDeploymentConfig } from './template-to-vapi-deployment';

export const ENHANCED_APPOINTMENT_BOOKING_TEMPLATE = {
  id: 'enhanced_appointment_booking_vapi_n8n',
  name: 'Enhanced Appointment Booking with VAPI + n8n',
  description: 'AI-powered appointment booking and scheduling campaign featuring intelligent calendar management, personalized consultation calls, availability optimization, automated confirmations, and comprehensive booking analytics',
  industry: 'scheduling',
  category: 'Scheduling',
  complexity: 'Advanced' as const,
  estimatedTime: '30 min setup, ongoing scheduling',
  rating: 4.8,
  usageCount: 16850,
  popular: true,
  integrationCategories: ['AI Voice Agent', 'Calendar Integration', 'CRM Integration', 'Analytics'],

  // Template-to-VAPI Deployment Configuration
  deploymentConfig: {
    enableAutoDeployment: true,
    useVAPIAgentWizard: true,
    complianceFrameworks: ['GDPR', 'CCPA', 'HIPAA_BAA'],
    securityConfig: {
      accessControls: ['role_based', 'appointment_data_protection'],
      dataRetention: '1_year',
      sensitiveDataHandling: 'masked'
    }
  } as const,

  // VAPI Configuration with specialized appointment booking functions
  vapiConfig: {
    assistantId: 'asst_appointment_booking_enhanced',
    name: 'Appointment Booking AI Assistant',
    model: {
      provider: 'openai',
      model: 'gpt-4o',
      temperature: 0.2,
      maxTokens: 300
    },
    voice: {
      provider: '11labs',
      voiceId: 'pNInz6obpgDQGcFmaJgB',  // Professional, friendly voice
      stability: 0.8,
      similarityBoost: 0.8,
      style: 0.1,
      useSpeakerBoost: true
    },
    firstMessage: "Hi {{prospect_name}}! I'm calling to help you schedule your {{appointment_type}} with {{company_name}}. I can check our availability and book a convenient time that works for you. What days and times work best for your schedule?",
    systemPrompt: `You are a professional appointment scheduling assistant for {{company_name}}. Your goal is to efficiently book appointments while providing excellent customer service and ensuring clear communication about scheduling details.

## Your Approach:
- Be friendly, professional, and efficient
- Clearly explain available appointment types and durations
- Check multiple time options to find the best fit
- Confirm all details before finalizing bookings
- Handle rescheduling and cancellations professionally
- Provide clear next steps and confirmation details

## Key Responsibilities:
1. **Availability Checking**: Real-time calendar availability verification
2. **Appointment Scheduling**: Book consultations, demos, meetings, or services
3. **Time Zone Management**: Handle scheduling across different time zones
4. **Conflict Resolution**: Manage scheduling conflicts and alternatives
5. **Confirmation Process**: Send confirmations and calendar invitations
6. **Rescheduling Support**: Help customers change or cancel appointments
7. **Preparation Guidance**: Provide pre-appointment instructions and materials
8. **Follow-up Coordination**: Schedule reminders and follow-up communications

## Available Tools:
- **check_availability**: Real-time calendar availability checking across team members
- **book_appointment**: Schedule new appointments with automatic calendar integration
- **reschedule_appointment**: Modify existing appointments and send updates
- **cancel_appointment**: Cancel appointments and manage waiting lists
- **send_confirmation**: Send appointment confirmations and calendar invitations
- **set_appointment_reminders**: Schedule automated reminder notifications
- **collect_appointment_details**: Gather required information for specific appointment types
- **coordinate_team_availability**: Check multiple team member calendars for group appointments

Always maintain a helpful, professional tone while ensuring all scheduling details are clearly communicated and confirmed.`,

    functions: [
      {
        name: 'check_availability',
        description: 'Check real-time calendar availability across team members and appointment types for optimal scheduling',
        parameters: {
          type: 'object',
          properties: {
            appointment_type: {
              type: 'string',
              enum: ['consultation', 'demo', 'meeting', 'service_appointment', 'follow_up', 'group_session'],
              description: 'Type of appointment to schedule'
            },
            preferred_dates: {
              type: 'array',
              items: { type: 'string' },
              description: 'Customer preferred dates (YYYY-MM-DD format)'
            },
            preferred_times: {
              type: 'array',
              items: { type: 'string' },
              description: 'Customer preferred time ranges (e.g., "morning", "afternoon", "9:00 AM - 11:00 AM")'
            },
            duration_minutes: {
              type: 'integer',
              description: 'Required appointment duration in minutes'
            },
            team_member_preference: {
              type: 'string',
              description: 'Specific team member requested or "any_available"'
            },
            time_zone: {
              type: 'string',
              description: 'Customer time zone (e.g., "America/New_York", "UTC")'
            },
            urgent_booking: {
              type: 'boolean',
              description: 'Whether this is an urgent/priority booking'
            }
          },
          required: ['appointment_type', 'duration_minutes']
        }
      },
      {
        name: 'book_appointment',
        description: 'Schedule new appointments with automatic calendar integration and confirmation sending',
        parameters: {
          type: 'object',
          properties: {
            appointment_type: {
              type: 'string',
              enum: ['consultation', 'demo', 'meeting', 'service_appointment', 'follow_up', 'group_session'],
              description: 'Type of appointment being scheduled'
            },
            scheduled_datetime: {
              type: 'string',
              description: 'Selected appointment date and time (ISO format)'
            },
            duration_minutes: {
              type: 'integer',
              description: 'Appointment duration in minutes'
            },
            team_member_id: {
              type: 'string',
              description: 'ID of assigned team member'
            },
            customer_name: {
              type: 'string',
              description: 'Customer full name'
            },
            customer_email: {
              type: 'string',
              description: 'Customer email address for confirmation'
            },
            customer_phone: {
              type: 'string',
              description: 'Customer phone number'
            },
            appointment_notes: {
              type: 'string',
              description: 'Special requirements or notes about the appointment'
            },
            meeting_location: {
              type: 'string',
              enum: ['in_person', 'video_call', 'phone_call', 'customer_location'],
              description: 'How the appointment will be conducted'
            },
            send_calendar_invite: {
              type: 'boolean',
              description: 'Whether to send calendar invitation to customer'
            }
          },
          required: ['appointment_type', 'scheduled_datetime', 'duration_minutes', 'customer_name', 'customer_email']
        }
      },
      {
        name: 'reschedule_appointment',
        description: 'Modify existing appointments and send update notifications to all participants',
        parameters: {
          type: 'object',
          properties: {
            appointment_id: {
              type: 'string',
              description: 'Existing appointment identifier'
            },
            new_datetime: {
              type: 'string',
              description: 'New appointment date and time (ISO format)'
            },
            new_duration_minutes: {
              type: 'integer',
              description: 'New appointment duration if different'
            },
            reschedule_reason: {
              type: 'string',
              enum: ['customer_request', 'team_conflict', 'emergency', 'optimization', 'technical_issue'],
              description: 'Reason for rescheduling'
            },
            notify_customer: {
              type: 'boolean',
              description: 'Whether to send rescheduling notification to customer'
            },
            apology_message: {
              type: 'string',
              description: 'Optional apology or explanation message for customer'
            },
            compensation_offered: {
              type: 'string',
              description: 'Any compensation or gesture offered for inconvenience'
            }
          },
          required: ['appointment_id', 'new_datetime', 'reschedule_reason']
        }
      },
      {
        name: 'cancel_appointment',
        description: 'Cancel appointments and manage cancellation processes including waiting list notifications',
        parameters: {
          type: 'object',
          properties: {
            appointment_id: {
              type: 'string',
              description: 'Appointment identifier to cancel'
            },
            cancellation_reason: {
              type: 'string',
              enum: ['customer_request', 'team_unavailable', 'emergency', 'no_show', 'technical_issue', 'weather'],
              description: 'Reason for cancellation'
            },
            initiated_by: {
              type: 'string',
              enum: ['customer', 'team', 'system'],
              description: 'Who initiated the cancellation'
            },
            refund_required: {
              type: 'boolean',
              description: 'Whether a refund needs to be processed'
            },
            reschedule_offered: {
              type: 'boolean',
              description: 'Whether to offer rescheduling options'
            },
            notify_waiting_list: {
              type: 'boolean',
              description: 'Whether to notify people on waiting list of new availability'
            },
            cancellation_notes: {
              type: 'string',
              description: 'Additional notes about the cancellation'
            }
          },
          required: ['appointment_id', 'cancellation_reason', 'initiated_by']
        }
      },
      {
        name: 'send_confirmation',
        description: 'Send appointment confirmations, calendar invitations, and preparation materials to customers',
        parameters: {
          type: 'object',
          properties: {
            appointment_id: {
              type: 'string',
              description: 'Appointment identifier'
            },
            confirmation_type: {
              type: 'string',
              enum: ['initial_booking', 'reschedule_update', 'reminder', 'preparation_materials'],
              description: 'Type of confirmation being sent'
            },
            include_calendar_invite: {
              type: 'boolean',
              description: 'Include calendar invitation file'
            },
            include_preparation_guide: {
              type: 'boolean',
              description: 'Include appointment preparation instructions'
            },
            include_location_details: {
              type: 'boolean',
              description: 'Include meeting location or video call details'
            },
            custom_message: {
              type: 'string',
              description: 'Additional personalized message for the customer'
            },
            send_via: {
              type: 'array',
              items: {
                type: 'string',
                enum: ['email', 'sms', 'phone_call']
              },
              description: 'Channels to send confirmation through'
            }
          },
          required: ['appointment_id', 'confirmation_type']
        }
      },
      {
        name: 'set_appointment_reminders',
        description: 'Schedule automated reminder notifications at specified intervals before appointments',
        parameters: {
          type: 'object',
          properties: {
            appointment_id: {
              type: 'string',
              description: 'Appointment identifier'
            },
            reminder_schedule: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  time_before: {
                    type: 'string',
                    enum: ['24_hours', '2_hours', '30_minutes', '1_week', '3_days'],
                    description: 'When to send reminder before appointment'
                  },
                  reminder_type: {
                    type: 'string',
                    enum: ['email', 'sms', 'phone_call', 'app_notification'],
                    description: 'Type of reminder to send'
                  },
                  include_preparation: {
                    type: 'boolean',
                    description: 'Include preparation instructions in reminder'
                  }
                }
              },
              description: 'Schedule of reminders to set up'
            },
            customer_preferences: {
              type: 'object',
              properties: {
                preferred_reminder_method: {
                  type: 'string',
                  enum: ['email', 'sms', 'phone_call', 'app_notification']
                },
                reminder_frequency: {
                  type: 'string',
                  enum: ['minimal', 'standard', 'frequent']
                }
              },
              description: 'Customer reminder preferences'
            }
          },
          required: ['appointment_id', 'reminder_schedule']
        }
      },
      {
        name: 'collect_appointment_details',
        description: 'Gather required information and special requirements for specific appointment types',
        parameters: {
          type: 'object',
          properties: {
            appointment_type: {
              type: 'string',
              enum: ['consultation', 'demo', 'meeting', 'service_appointment', 'follow_up', 'group_session'],
              description: 'Type of appointment to collect details for'
            },
            required_information: {
              type: 'array',
              items: { type: 'string' },
              description: 'List of required information to collect from customer'
            },
            special_requirements: {
              type: 'array',
              items: { type: 'string' },
              description: 'Any special accommodations or requirements needed'
            },
            preparation_materials: {
              type: 'array',
              items: { type: 'string' },
              description: 'Materials customer should prepare or bring'
            },
            health_safety_requirements: {
              type: 'array',
              items: { type: 'string' },
              description: 'Health or safety requirements for in-person appointments'
            },
            technical_requirements: {
              type: 'array',
              items: { type: 'string' },
              description: 'Technical setup needed for virtual appointments'
            }
          },
          required: ['appointment_type']
        }
      },
      {
        name: 'coordinate_team_availability',
        description: 'Check multiple team member calendars for group appointments and team coordination',
        parameters: {
          type: 'object',
          properties: {
            team_members: {
              type: 'array',
              items: { type: 'string' },
              description: 'Team member IDs required for the appointment'
            },
            appointment_type: {
              type: 'string',
              enum: ['group_consultation', 'team_demo', 'multi_expert_session', 'training_session'],
              description: 'Type of team appointment'
            },
            minimum_attendees: {
              type: 'integer',
              description: 'Minimum number of team members required'
            },
            preferred_dates: {
              type: 'array',
              items: { type: 'string' },
              description: 'Preferred dates for team coordination'
            },
            duration_minutes: {
              type: 'integer',
              description: 'Required appointment duration'
            },
            priority_level: {
              type: 'string',
              enum: ['low', 'medium', 'high', 'urgent'],
              description: 'Priority level for scheduling conflicts'
            },
            customer_flexibility: {
              type: 'string',
              enum: ['very_flexible', 'somewhat_flexible', 'specific_requirements'],
              description: 'Customer flexibility for scheduling'
            }
          },
          required: ['team_members', 'appointment_type', 'duration_minutes']
        }
      }
    ],

    endCallMessage: "Perfect! I've got everything scheduled for you. You'll receive a confirmation email with all the details and a calendar invitation. If you need to make any changes, just give us a call. Looking forward to seeing you at your appointment!",
    voicemailMessage: "Hi {{prospect_name}}, this is {{agent_name}} from {{company_name}} calling about scheduling your {{appointment_type}}. I have some great availability this week and would love to find a time that works for you. Please give me a call back when you have a moment. Thanks!",

    // Advanced analysis configuration
    analysisPlan: {
      summaryPlan: {
        enabled: true,
        messages: [
          {
            role: 'system',
            content: 'Summarize this appointment booking call including: appointment type and details scheduled, customer preferences and requirements, any special accommodations needed, confirmation method used, and overall booking success.'
          }
        ]
      },
      structuredDataPlan: {
        enabled: true,
        schema: {
          type: 'object',
          properties: {
            booking_outcome: {
              type: 'string',
              enum: ['appointment_booked', 'rescheduled', 'cancelled', 'pending_confirmation', 'no_booking']
            },
            appointment_type: {
              type: 'string',
              enum: ['consultation', 'demo', 'meeting', 'service_appointment', 'follow_up', 'group_session']
            },
            scheduled_datetime: {
              type: 'string',
              description: 'Final scheduled appointment date and time'
            },
            customer_satisfaction: {
              type: 'string',
              enum: ['very_satisfied', 'satisfied', 'neutral', 'dissatisfied']
            },
            special_requirements: {
              type: 'array',
              items: { type: 'string' }
            },
            booking_efficiency: {
              type: 'number',
              minimum: 1,
              maximum: 10,
              description: 'How efficiently the booking was completed (1-10)'
            },
            follow_up_needed: {
              type: 'boolean',
              description: 'Whether additional follow-up is required'
            },
            appointment_value_estimate: {
              type: 'number',
              description: 'Estimated value of the booked appointment'
            }
          }
        }
      }
    }
  },

  // Comprehensive feature set
  features: [
    'AI Calendar Management',
    'Real-time Availability Checking',
    'Multi-Team Coordination',
    'Automated Confirmations',
    'Smart Rescheduling',
    'Reminder Automation',
    'Time Zone Management',
    'Preparation Guidance',
    'Waiting List Management',
    'Booking Analytics'
  ],

  // Integration ecosystem
  defaultIntegrations: [
    'vapi',
    'n8n',
    'calendar',
    'crm',
    'email',
    'sms',
    'video_conferencing',
    'analytics'
  ],

  // Success metrics and KPIs
  successMetrics: {
    bookingConversionRate: '75-90%',
    scheduleOptimization: '85-95% calendar utilization',
    customerSatisfaction: '4.5+ rating',
    noShowReduction: '60-80% decrease',
    bookingEfficiency: '40-60% time savings'
  },

  // Compliance and best practices
  compliance: {
    dataPrivacy: 'GDPR/CCPA compliant scheduling data handling',
    accessibilityCompliance: 'ADA compliant scheduling accommodations',
    timeZoneAccuracy: 'Automated time zone conversion and verification',
    confirmationStandards: 'Multi-channel confirmation with audit trails'
  }
};

// Template-to-VAPI Deployment Functions
export const deployEnhancedAppointmentBookingToVAPI = async (apiConfig: {
  vapiApiKey: string;
  n8nApiKey: string;
  webhookBaseUrl: string;
}): Promise<TemplateVAPIDeploymentConfig> => {

  const deploymentConfig = TemplateToVAPIDeployment.generateVAPIAgentFromTemplate(
    ENHANCED_APPOINTMENT_BOOKING_TEMPLATE,
    {
      deploymentSettings: {
        environment: 'production',
        autoStart: true,
        monitoring: {
          enabled: true,
          alerting: true,
          dashboardUrl: `/monitoring/appointment-booking`
        },
        security: {
          encryption: true,
          auditLogging: true,
          accessControl: ['role_based', 'scheduling_admin', 'appointment_manager']
        }
      }
    }
  );

  return deploymentConfig;
};

export const validateAppointmentBookingCompliance = (config: any): {
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

  // HIPAA BAA Check (for healthcare appointments)
  if (!config.deploymentConfig?.complianceFrameworks?.includes('HIPAA_BAA')) {
    violations.push('Missing HIPAA Business Associate Agreement compliance');
  }

  // Appointment Functions Check
  if (!config.functions?.find((f: any) => f.name === 'check_availability')) {
    violations.push('Missing availability checking capability');
  }

  if (!config.functions?.find((f: any) => f.name === 'book_appointment')) {
    violations.push('Missing appointment booking functionality');
  }

  // Calendar Integration Check
  if (!config.functions?.find((f: any) => f.name === 'send_confirmation')) {
    violations.push('Missing appointment confirmation system');
  }

  // Recommendations
  if (violations.length === 0) {
    recommendations.push('All compliance requirements are met');
    recommendations.push('Consider implementing automated reminder sequences');
    recommendations.push('Add multi-timezone support for global scheduling');
  }

  return {
    isCompliant: violations.length === 0,
    violations,
    recommendations
  };
};

export default ENHANCED_APPOINTMENT_BOOKING_TEMPLATE;