import type { ToolTemplate } from './types.js';

export const commonTemplates: ToolTemplate[] = [
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
