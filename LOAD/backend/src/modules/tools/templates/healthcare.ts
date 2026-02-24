import type { ToolTemplate } from './types.js';

export const healthcareTemplates: ToolTemplate[] = [
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
