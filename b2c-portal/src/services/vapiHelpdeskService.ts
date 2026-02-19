import { N8NWorkflowService } from './n8nWorkflowService';

interface VAPIHelpdeskConfig {
  assistantId: string;
  phoneNumberId: string;
  voiceId: string;
  model: string;
  maxDuration: number;
  silenceTimeoutMs: number;
  responseDelayMs: number;
  n8nService: N8NWorkflowService;
  businessHours: any;
  escalationRules: any;
}

interface VAPIFunction {
  name: string;
  description: string;
  parameters: {
    type: string;
    properties: any;
    required: string[];
  };
}

interface VAPICall {
  id: string;
  phoneNumber: string;
  status: 'queued' | 'ringing' | 'in_progress' | 'completed' | 'failed';
  startedAt?: string;
  endedAt?: string;
  duration?: number;
  transcript?: string;
  summary?: string;
}

export class VAPIHelpdeskService {
  private config: VAPIHelpdeskConfig;
  private apiKey: string;
  private baseUrl: string = 'https://api.vapi.ai';

  constructor(config: VAPIHelpdeskConfig, apiKey: string) {
    this.config = config;
    this.apiKey = apiKey;
  }

  private async makeVAPIRequest(endpoint: string, method: string = 'POST', data?: any): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: data ? JSON.stringify(data) : undefined
      });

      if (!response.ok) {
        throw new Error(`VAPI request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('VAPI API Error:', error);
      throw error;
    }
  }

  private getHelpdeskFunctions(): VAPIFunction[] {
    return [
      {
        name: 'check_availability',
        description: 'Check calendar availability for booking appointments',
        parameters: {
          type: 'object',
          properties: {
            date: {
              type: 'string',
              description: 'Date to check availability (YYYY-MM-DD format)'
            },
            duration: {
              type: 'number',
              description: 'Duration of appointment in minutes',
              default: 30
            }
          },
          required: ['date']
        }
      },
      {
        name: 'book_appointment',
        description: 'Book an appointment with available time slot',
        parameters: {
          type: 'object',
          properties: {
            date: {
              type: 'string',
              description: 'Date for appointment (YYYY-MM-DD format)'
            },
            time: {
              type: 'string',
              description: 'Time for appointment (HH:MM format)'
            },
            duration: {
              type: 'number',
              description: 'Duration in minutes',
              default: 30
            },
            customerName: {
              type: 'string',
              description: 'Customer full name'
            },
            customerEmail: {
              type: 'string',
              description: 'Customer email address'
            },
            description: {
              type: 'string',
              description: 'Purpose or description of the appointment'
            }
          },
          required: ['date', 'time', 'customerName', 'customerEmail']
        }
      },
      {
        name: 'create_support_ticket',
        description: 'Create a support ticket for technical issues or requests',
        parameters: {
          type: 'object',
          properties: {
            title: {
              type: 'string',
              description: 'Brief title describing the issue'
            },
            description: {
              type: 'string',
              description: 'Detailed description of the issue or request'
            },
            priority: {
              type: 'string',
              enum: ['low', 'medium', 'high', 'urgent'],
              description: 'Priority level of the ticket'
            },
            category: {
              type: 'string',
              description: 'Category of the issue (e.g., technical, billing, general)'
            },
            customerName: {
              type: 'string',
              description: 'Customer full name'
            },
            customerEmail: {
              type: 'string',
              description: 'Customer email address'
            }
          },
          required: ['title', 'description', 'customerName', 'customerEmail']
        }
      },
      {
        name: 'escalate_to_human',
        description: 'Escalate the conversation to a human agent',
        parameters: {
          type: 'object',
          properties: {
            reason: {
              type: 'string',
              description: 'Reason for escalation'
            },
            escalationType: {
              type: 'string',
              enum: ['human_agent', 'supervisor', 'technical', 'billing'],
              description: 'Type of escalation needed'
            },
            priority: {
              type: 'string',
              enum: ['normal', 'urgent'],
              description: 'Priority of escalation'
            }
          },
          required: ['reason', 'escalationType']
        }
      },
      {
        name: 'get_business_hours',
        description: 'Get current business hours and availability',
        parameters: {
          type: 'object',
          properties: {},
          required: []
        }
      }
    ];
  }

  private generateHelpdeskPrompt(): string {
    return `You are a professional AI helpdesk assistant for our customer support team. Your role is to help customers with:

## Core Capabilities:
1. **Appointment Booking** - Check availability and schedule appointments
2. **Support Tickets** - Create tickets for technical issues and requests
3. **General Support** - Answer questions and provide information
4. **Escalation** - Connect customers with human agents when needed

## Guidelines:
- Always be polite, professional, and helpful
- Gather necessary information before making appointments or creating tickets
- Ask clarifying questions to understand the customer's needs
- If you cannot resolve an issue, offer to create a ticket or escalate to a human agent
- For urgent issues, prioritize escalation appropriately
- Respect business hours: ${JSON.stringify(this.config.businessHours)}

## Function Usage:
- Use \`check_availability\` before booking appointments
- Use \`book_appointment\` only after confirming customer details
- Use \`create_support_ticket\` for technical issues or complex requests
- Use \`escalate_to_human\` when you cannot provide adequate assistance
- Use \`get_business_hours\` to inform customers about availability

## Response Style:
- Be conversational but professional
- Confirm important details back to the customer
- Provide clear next steps and timeframes
- Thank customers for their patience

Start by greeting the customer and asking how you can assist them today.`;
  }

  async createHelpdeskAssistant(): Promise<any> {
    const assistantConfig = {
      name: 'Helpdesk Support Assistant',
      voice: {
        provider: 'playht',
        voiceId: this.config.voiceId
      },
      model: {
        provider: 'openai',
        model: this.config.model,
        messages: [
          {
            role: 'system',
            content: this.generateHelpdeskPrompt()
          }
        ],
        functions: this.getHelpdeskFunctions(),
        maxTokens: 500,
        temperature: 0.7
      },
      firstMessage: "Hello! I'm your AI helpdesk assistant. I can help you book appointments, create support tickets, or answer questions about our services. How may I assist you today?",
      recordingEnabled: true,
      endCallMessage: "Thank you for contacting our support. Have a great day!",
      endCallPhrases: ['goodbye', 'thank you', 'that\'s all', 'end call'],
      maxDurationSeconds: this.config.maxDuration,
      silenceTimeoutSeconds: Math.floor(this.config.silenceTimeoutMs / 1000),
      responseDelaySeconds: Math.floor(this.config.responseDelayMs / 1000),
      llmRequestDelaySeconds: 1,
      numWordsToInterruptAssistant: 2,
      interruptionThreshold: 100,
      voicemailMessage: "Hello, you've reached our support helpdesk. Please leave a message and we'll get back to you soon.",
      clientMessages: [
        'transcript',
        'hang',
        'function-call'
      ],
      serverMessages: [
        'end-of-call-report',
        'conversation-update',
        'function-call'
      ]
    };

    try {
      return await this.makeVAPIRequest('/assistant', 'POST', assistantConfig);
    } catch (error) {
      console.error('Failed to create helpdesk assistant:', error);
      throw error;
    }
  }

  async updateHelpdeskAssistant(assistantId: string, updates: any): Promise<any> {
    try {
      return await this.makeVAPIRequest(`/assistant/${assistantId}`, 'PATCH', updates);
    } catch (error) {
      console.error('Failed to update helpdesk assistant:', error);
      throw error;
    }
  }

  async handleFunctionCall(functionName: string, parameters: any, callContext: any): Promise<any> {
    const { customerPhone } = callContext;

    try {
      switch (functionName) {
        case 'check_availability':
          return await this.config.n8nService.checkCalendarAvailability({
            date: parameters.date,
            timeZone: this.config.businessHours.timeZone || 'America/New_York',
            duration: parameters.duration || 30
          });

        case 'book_appointment':
          return await this.config.n8nService.bookAppointment({
            date: parameters.date,
            time: parameters.time,
            duration: parameters.duration || 30,
            customerName: parameters.customerName,
            customerEmail: parameters.customerEmail,
            customerPhone: customerPhone,
            description: parameters.description || 'Phone appointment',
            timeZone: this.config.businessHours.timeZone || 'America/New_York'
          });

        case 'create_support_ticket':
          return await this.config.n8nService.createTicket({
            title: parameters.title,
            description: parameters.description,
            priority: parameters.priority || 'medium',
            customerName: parameters.customerName,
            customerEmail: parameters.customerEmail,
            customerPhone: customerPhone,
            category: parameters.category || 'general',
            source: 'voice'
          });

        case 'escalate_to_human':
          return await this.config.n8nService.escalateIssue({
            customerPhone: customerPhone,
            issue: parameters.reason,
            escalationType: parameters.escalationType,
            priority: parameters.priority || 'normal'
          });

        case 'get_business_hours':
          return {
            businessHours: this.config.businessHours,
            currentTime: new Date().toISOString(),
            isOpen: this.isCurrentlyOpen()
          };

        default:
          throw new Error(`Unknown function: ${functionName}`);
      }
    } catch (error) {
      console.error(`Function call error for ${functionName}:`, error);
      return {
        error: true,
        message: `Sorry, I encountered an error while ${functionName.replace('_', ' ')}. Let me escalate this to a human agent.`
      };
    }
  }

  private isCurrentlyOpen(): boolean {
    if (!this.config.businessHours.enabled) {
      return true;
    }

    const now = new Date();
    const dayOfWeek = now.toLocaleDateString('en-US', { weekday: 'lowercase' });
    const currentTime = now.toTimeString().slice(0, 5); // HH:MM format

    const schedule = this.config.businessHours.schedule[dayOfWeek];
    if (!schedule || !schedule.enabled) {
      return false;
    }

    return currentTime >= schedule.start && currentTime <= schedule.end;
  }

  async startCall(phoneNumber: string, assistantId?: string): Promise<VAPICall> {
    const callConfig = {
      phoneNumberId: this.config.phoneNumberId,
      assistantId: assistantId || this.config.assistantId,
      customer: {
        number: phoneNumber
      }
    };

    try {
      const response = await this.makeVAPIRequest('/call', 'POST', callConfig);
      return {
        id: response.id,
        phoneNumber,
        status: response.status || 'queued',
        startedAt: response.startedAt
      };
    } catch (error) {
      console.error('Failed to start call:', error);
      throw error;
    }
  }

  async getCall(callId: string): Promise<VAPICall> {
    try {
      const response = await this.makeVAPIRequest(`/call/${callId}`, 'GET');
      return {
        id: response.id,
        phoneNumber: response.customer?.number || '',
        status: response.status,
        startedAt: response.startedAt,
        endedAt: response.endedAt,
        duration: response.duration,
        transcript: response.transcript,
        summary: response.summary
      };
    } catch (error) {
      console.error('Failed to get call:', error);
      throw error;
    }
  }

  async endCall(callId: string): Promise<void> {
    try {
      await this.makeVAPIRequest(`/call/${callId}`, 'DELETE');
    } catch (error) {
      console.error('Failed to end call:', error);
      throw error;
    }
  }

  async getCallHistory(limit: number = 50): Promise<VAPICall[]> {
    try {
      const response = await this.makeVAPIRequest(`/call?limit=${limit}`, 'GET');
      return response.map((call: any) => ({
        id: call.id,
        phoneNumber: call.customer?.number || '',
        status: call.status,
        startedAt: call.startedAt,
        endedAt: call.endedAt,
        duration: call.duration,
        transcript: call.transcript,
        summary: call.summary
      }));
    } catch (error) {
      console.error('Failed to get call history:', error);
      throw error;
    }
  }
}

export type { VAPIHelpdeskConfig, VAPICall };