/**
 * Premier Health Healthcare Automation Template
 * Domain-specific configuration for the Universal Automation Wizard
 */

import { AutomationTemplate, DomainTemplate, ToolSchema } from '../core/types';

export const PREMIER_HEALTH_TEMPLATE: AutomationTemplate = {
  id: 'premier_health_locator',
  name: 'Healthcare Provider Locator',
  category: 'healthcare',
  version: '2.0.0',
  description: 'AI-powered healthcare provider search and appointment booking system',

  defaultConfig: {
    companyExtraction: {
      dataTypes: ['healthcare_providers', 'specialties', 'locations', 'insurance_networks'],
      sources: ['provider_database', 'insurance_apis', 'static_files'],
      nlpModels: ['medical_ner', 'location_extraction', 'specialty_classification'],
      validationRules: ['hipaa_compliance', 'provider_verification', 'location_accuracy']
    },

    promptTemplates: {
      systemPromptBase: `You are a professional healthcare provider location assistant for Premier Health Insurance.
Your role is to help customers find healthcare providers, book appointments, and provide accurate medical facility information.

## Core Responsibilities:
1. **Provider Search**: Find healthcare providers by location, specialty, insurance network
2. **Appointment Booking**: Schedule appointments with available providers
3. **Emergency Services**: Provide immediate emergency healthcare guidance
4. **Insurance Verification**: Verify provider coverage under customer's plan

## Search Capabilities:
- Search by specialty (e.g., "eye doctor", "pediatrician", "cardiologist")
- Search by location (e.g., "Accra", "Madina", "East Legon")
- Search by provider type (e.g., "hospital", "clinic", "pharmacy")
- Emergency provider prioritization
- Insurance network filtering

## Response Guidelines:
- Always verify provider availability and insurance coverage
- Provide complete contact information (phone, address, hours)
- Offer appointment booking when available
- Include walking directions or transport options
- Escalate to human support for complex medical queries

## Compliance Requirements:
- HIPAA-compliant information handling
- No medical advice or diagnosis
- Verify customer identity for sensitive information
- Maintain patient confidentiality at all times

How may I assist you in finding healthcare providers today?`,

      contextEnhancement: {
        providerDatabase: true,
        insuranceNetworks: true,
        emergencyProtocols: true,
        appointmentSystems: true
      },

      responseFormats: [
        'provider_search_results',
        'appointment_confirmation',
        'emergency_guidance',
        'insurance_verification'
      ]
    },

    n8nWorkflow: {
      workflowName: 'Premier Health Provider Locator',
      baseNodes: [
        {
          type: 'webhook_trigger',
          name: 'VAPI Healthcare Webhook',
          config: {
            path: 'premier-health/provider-search',
            method: 'POST'
          }
        },
        {
          type: 'data_extraction',
          name: 'Extract Search Intent',
          config: {
            jsCode: `
// Enhanced healthcare intent extraction
const callData = $input.first().json;

const healthcareIntentExtractor = {
  extractSearchIntent(query) {
    const patterns = {
      specialties: {
        'eye|ophthalmology|vision': 'Ophthalmology',
        'children|pediatric|kids': 'Pediatrics',
        'women|gynecology|obstetrics': 'Obstetrics/Gynecology',
        'heart|cardiology|cardiac': 'Cardiology',
        'mental|psychiatry|psychology': 'Mental Health',
        'emergency|urgent|ER': 'Emergency Medicine',
        'dental|dentist|teeth': 'Dental',
        'general|family|primary': 'General Practice'
      },
      locations: {
        'accra|central': 'ACCRA CENTRAL',
        'madina|adenta': 'MADINA',
        'circle|kaneshie': 'CIRCLE',
        'tesano|kokomlemle': 'KOKOMLEMLE',
        'east legon|legon': 'LEGON',
        'airport|residential': 'AIRPORT RESIDENTIAL AREA',
        'korle-bu|adabraka': 'ADABRAKA'
      },
      providerTypes: {
        'hospital|medical center': 'hospital',
        'clinic|health center': 'clinic',
        'pharmacy|drug store': 'pharmacy',
        'laboratory|lab|test': 'laboratory'
      },
      urgency: {
        'emergency|urgent|immediate|now': 'emergency',
        'today|asap|quickly': 'urgent',
        'soon|this week': 'normal'
      }
    };

    const intent = {
      specialty: null,
      location: null,
      providerType: null,
      urgency: 'normal',
      insuranceRequired: true
    };

    const lowerQuery = query.toLowerCase();

    // Extract intent components
    for (const [pattern, value] of Object.entries(patterns.specialties)) {
      if (new RegExp(pattern).test(lowerQuery)) {
        intent.specialty = value;
        break;
      }
    }

    for (const [pattern, value] of Object.entries(patterns.locations)) {
      if (new RegExp(pattern).test(lowerQuery)) {
        intent.location = value;
        break;
      }
    }

    for (const [pattern, value] of Object.entries(patterns.providerTypes)) {
      if (new RegExp(pattern).test(lowerQuery)) {
        intent.providerType = value;
        break;
      }
    }

    for (const [pattern, value] of Object.entries(patterns.urgency)) {
      if (new RegExp(pattern).test(lowerQuery)) {
        intent.urgency = value;
        break;
      }
    }

    return intent;
  }
};

const searchQuery = callData.message?.content || callData.transcript || '';
const extractedIntent = healthcareIntentExtractor.extractSearchIntent(searchQuery);

return [{
  json: {
    ...callData,
    searchIntent: extractedIntent,
    searchQuery: searchQuery,
    timestamp: new Date().toISOString()
  }
}];`
          }
        },
        {
          type: 'postgresql_query',
          name: 'Search Healthcare Providers',
          config: {
            operation: 'executeQuery',
            query: `
SELECT
  hp.*,
  CASE
    WHEN $json.searchIntent.urgency = 'emergency' THEN 1
    WHEN hp.provider_type = 'hospital' THEN 2
    ELSE 3
  END as priority_score,
  ts_rank(
    hp.search_vector,
    plainto_tsquery('english', $json.searchQuery)
  ) as relevance_score
FROM healthcare_providers hp
WHERE hp.is_active = true
  AND (
    $json.searchIntent.specialty IS NULL
    OR hp.specialties @> ARRAY[$json.searchIntent.specialty]
  )
  AND (
    $json.searchIntent.location IS NULL
    OR hp.area ILIKE '%' || $json.searchIntent.location || '%'
    OR hp.address ILIKE '%' || $json.searchIntent.location || '%'
  )
  AND (
    $json.searchIntent.providerType IS NULL
    OR hp.provider_type = $json.searchIntent.providerType
  )
ORDER BY
  priority_score ASC,
  relevance_score DESC,
  hp.name ASC
LIMIT $json.maxResults;`
          }
        }
      ],

      connections: {
        'webhook_trigger': ['data_extraction'],
        'data_extraction': ['postgresql_query'],
        'postgresql_query': ['format_response']
      }
    },

    vapiAgent: {
      voiceSettings: {
        voiceId: 'jennifer', // Professional, medical-appropriate voice
        model: 'gpt-4o',
        provider: '11labs',
        maxDuration: 900, // 15 minutes for complex searches
        temperature: 0.3 // Lower temperature for medical accuracy
      },

      tools: [
        'search_healthcare_providers',
        'get_provider_details',
        'book_appointment',
        'get_emergency_providers',
        'verify_insurance_coverage',
        'escalate_to_human'
      ],

      systemPromptEnhancement: {
        medicalCompliance: true,
        emergencyProtocols: true,
        insuranceVerification: true,
        appointmentBooking: true
      }
    },

    integrations: {
      supabase: {
        enabled: true,
        projectId: 'ljzbzjgvwzivpmlmuxhx',
        tables: ['healthcare_providers', 'call_logs', 'appointments']
      },
      calendly: {
        enabled: true,
        apiKey: '',
        bookingTypes: ['general_consultation', 'specialist_appointment', 'emergency_booking']
      },
      resend: {
        enabled: true,
        apiKey: '',
        templates: ['provider_info', 'appointment_confirmation', 'emergency_instructions']
      },
      vonage: {
        enabled: true,
        apiKey: '',
        smsTemplates: ['provider_contact', 'appointment_reminder', 'emergency_alert']
      },
      freshdesk: {
        enabled: true,
        apiKey: '',
        ticketTypes: ['provider_not_found', 'insurance_issue', 'appointment_problem']
      }
    },

    demoSettings: {
      enableDemo: true,
      demoTheme: 'healthcare',
      brandColors: ['#2563eb', '#16a34a', '#dc2626'], // Blue, Green, Red for emergency
      interactiveFeatures: [
        'provider_search_demo',
        'appointment_booking_demo',
        'emergency_services_demo',
        'insurance_verification_demo'
      ]
    },

    analytics: {
      enableTracking: true,
      kpis: [
        'search_success_rate',
        'appointment_booking_rate',
        'emergency_response_time',
        'escalation_rate',
        'customer_satisfaction'
      ],
      reportEmail: 'ailabsafrica@gmail.com',
      dashboardMetrics: [
        'provider_search_volume',
        'specialty_demand_trends',
        'location_popularity',
        'booking_conversion_rates'
      ]
    }
  },

  domainExtensions: {
    dataValidation: {
      providerVerification: true,
      insuranceNetworkValidation: true,
      medicalLicenseCheck: true,
      emergencyServiceVerification: true
    },

    complianceFrameworks: ['HIPAA', 'HITECH', 'Ghana Health Service Standards'],

    customEndpoints: [
      '/emergency-providers',
      '/verify-insurance',
      '/book-appointment',
      '/escalate-support'
    ],

    industryTools: [
      {
        name: 'HealthcareProviderSearch',
        implementation: 'PremierHealthTools.search_healthcare_providers',
        schema: 'HealthcareSearchSchema'
      },
      {
        name: 'EmergencyProviderLocator',
        implementation: 'PremierHealthTools.get_emergency_providers',
        schema: 'EmergencySearchSchema'
      },
      {
        name: 'AppointmentBooking',
        implementation: 'CalendlyIntegration.bookHealthcareAppointment',
        schema: 'AppointmentBookingSchema'
      }
    ]
  }
};

export const HEALTHCARE_TOOL_SCHEMAS: Record<string, ToolSchema> = {
  search_healthcare_providers: {
    name: 'search_healthcare_providers',
    description: 'Search for healthcare providers by location, specialty, or insurance network',
    parameters: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Natural language search query (e.g., "find an eye doctor in Accra")'
        },
        specialty: {
          type: 'string',
          enum: ['Ophthalmology', 'Pediatrics', 'Obstetrics/Gynecology', 'Cardiology', 'Mental Health', 'Emergency Medicine', 'Dental', 'General Practice'],
          description: 'Medical specialty filter'
        },
        location: {
          type: 'string',
          description: 'Location name (e.g., "Madina", "East Legon", "Circle")'
        },
        provider_type: {
          type: 'string',
          enum: ['hospital', 'clinic', 'pharmacy', 'laboratory'],
          description: 'Type of healthcare provider'
        },
        max_results: {
          type: 'number',
          default: 5,
          description: 'Maximum number of results to return'
        },
        insurance_network: {
          type: 'boolean',
          default: true,
          description: 'Filter by Premier Health insurance network'
        }
      },
      required: ['query']
    }
  },

  get_emergency_providers: {
    name: 'get_emergency_providers',
    description: 'Get emergency healthcare providers for urgent medical situations',
    parameters: {
      type: 'object',
      properties: {
        location: {
          type: 'string',
          description: 'Current location for finding nearest emergency services'
        },
        emergency_type: {
          type: 'string',
          enum: ['general_emergency', 'cardiac', 'trauma', 'pediatric_emergency', 'mental_health_crisis'],
          description: 'Type of medical emergency'
        },
        max_results: {
          type: 'number',
          default: 3,
          description: 'Maximum number of emergency providers to return'
        }
      },
      required: ['location']
    }
  },

  book_appointment: {
    name: 'book_appointment',
    description: 'Book an appointment with a healthcare provider',
    parameters: {
      type: 'object',
      properties: {
        provider_id: {
          type: 'number',
          description: 'ID of the healthcare provider'
        },
        appointment_type: {
          type: 'string',
          enum: ['consultation', 'follow_up', 'emergency', 'screening'],
          description: 'Type of appointment'
        },
        preferred_date: {
          type: 'string',
          description: 'Preferred appointment date (YYYY-MM-DD format)'
        },
        preferred_time: {
          type: 'string',
          description: 'Preferred appointment time (HH:MM format)'
        },
        patient_name: {
          type: 'string',
          description: 'Name of the patient'
        },
        contact_phone: {
          type: 'string',
          description: 'Contact phone number'
        },
        insurance_id: {
          type: 'string',
          description: 'Premier Health insurance ID'
        }
      },
      required: ['provider_id', 'appointment_type', 'patient_name', 'contact_phone']
    }
  },

  verify_insurance_coverage: {
    name: 'verify_insurance_coverage',
    description: 'Verify insurance coverage for a specific provider or service',
    parameters: {
      type: 'object',
      properties: {
        provider_id: {
          type: 'number',
          description: 'ID of the healthcare provider'
        },
        insurance_id: {
          type: 'string',
          description: 'Premier Health insurance ID'
        },
        service_type: {
          type: 'string',
          description: 'Type of medical service'
        }
      },
      required: ['provider_id', 'insurance_id']
    }
  },

  escalate_to_human: {
    name: 'escalate_to_human',
    description: 'Escalate complex queries to human support specialist',
    parameters: {
      type: 'object',
      properties: {
        reason: {
          type: 'string',
          enum: ['provider_not_found', 'insurance_issue', 'medical_emergency', 'technical_problem', 'complex_query'],
          description: 'Reason for escalation'
        },
        customer_phone: {
          type: 'string',
          description: 'Customer phone number for callback'
        },
        urgency: {
          type: 'string',
          enum: ['low', 'medium', 'high', 'emergency'],
          description: 'Urgency level of the escalation'
        },
        details: {
          type: 'string',
          description: 'Additional details about the query'
        }
      },
      required: ['reason', 'customer_phone']
    }
  }
};