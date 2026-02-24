import type { ToolTemplate } from './types.js';

export const financeTemplates: ToolTemplate[] = [
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
