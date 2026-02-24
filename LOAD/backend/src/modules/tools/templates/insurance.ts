import type { ToolTemplate } from './types.js';

export const insuranceTemplates: ToolTemplate[] = [
  {
    name: 'Lookup Customer Account',
    description: 'Look up customer account information using policy number',
    category: 'insurance',
    type: 'FUNCTION',
    function: {
      name: 'lookup_customer_account',
      description: 'Look up customer account information using policy number',
      parameters: {
        type: 'object',
        properties: {
          policy_number: { type: 'string' },
          verification_method: {
            type: 'string',
            enum: ['ssn', 'dob', 'security_question'],
          },
        },
        required: ['policy_number', 'verification_method'],
      },
    },
  },
  {
    name: 'Initiate Claims Process',
    description: 'Start the claims filing process for the customer',
    category: 'insurance',
    type: 'FUNCTION',
    function: {
      name: 'initiate_claims_process',
      description: 'Start the claims filing process for the customer',
      parameters: {
        type: 'object',
        properties: {
          claim_type: { type: 'string', enum: ['auto', 'home', 'life', 'health'] },
          incident_date: { type: 'string' },
          incident_description: { type: 'string' },
          estimated_amount: { type: 'number' },
        },
        required: ['claim_type', 'incident_date', 'incident_description'],
      },
    },
  },
  {
    name: 'Check Payment Status',
    description: 'Check the status of premium payments or claim payments',
    category: 'insurance',
    type: 'FUNCTION',
    function: {
      name: 'check_payment_status',
      description: 'Check the status of premium payments or claim payments',
      parameters: {
        type: 'object',
        properties: {
          payment_type: { type: 'string', enum: ['premium', 'claim'] },
          reference_number: { type: 'string' },
        },
        required: ['payment_type'],
      },
    },
  },
  {
    name: 'Assess Financial Hardship',
    description: 'Assess customer financial hardship situation for premium flexibility',
    category: 'insurance',
    type: 'FUNCTION',
    function: {
      name: 'assess_financial_hardship',
      description: 'Assess customer financial hardship situation',
      parameters: {
        type: 'object',
        properties: {
          employment_status: {
            type: 'string',
            enum: ['employed', 'unemployed', 'reduced_hours', 'disability'],
          },
          household_changes: { type: 'string' },
          medical_issues: { type: 'boolean' },
          other_circumstances: { type: 'string' },
        },
        required: ['employment_status'],
      },
    },
  },
  {
    name: 'Request Hardship Assistance',
    description: 'Request hardship assistance options for qualified customers',
    category: 'insurance',
    type: 'FUNCTION',
    function: {
      name: 'request_hardship_assistance',
      description: 'Request hardship assistance options for qualified customers',
      parameters: {
        type: 'object',
        properties: {
          assistance_type: {
            type: 'string',
            enum: ['payment_reduction', 'grace_period', 'policy_modification'],
          },
          duration: { type: 'string' },
          justification: { type: 'string' },
        },
        required: ['assistance_type', 'justification'],
      },
    },
  },
];
