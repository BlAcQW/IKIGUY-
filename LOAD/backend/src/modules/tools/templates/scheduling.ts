import type { ToolTemplate } from './types.js';

export const schedulingTemplates: ToolTemplate[] = [
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
