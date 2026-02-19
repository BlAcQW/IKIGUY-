interface N8NWorkflowConfig {
  workflowId: string;
  workflowName: string;
  webhookUrl: string;
  calendarEndpoint: string;
  ticketEndpoint: string;
  availabilityEndpoint: string;
  escalationEndpoint: string;
}

interface CalendarAvailabilityRequest {
  date: string;
  timeZone: string;
  duration: number;
}

interface CalendarAvailabilityResponse {
  available: boolean;
  slots: Array<{
    start: string;
    end: string;
  }>;
}

interface AppointmentBookingRequest {
  date: string;
  time: string;
  duration: number;
  customerName: string;
  customerEmail: string;
  customerPhone: string;
  description: string;
  timeZone: string;
}

interface AppointmentBookingResponse {
  success: boolean;
  appointmentId?: string;
  confirmationUrl?: string;
  error?: string;
}

interface TicketCreationRequest {
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  customerName: string;
  customerEmail: string;
  customerPhone: string;
  category: string;
  source: 'voice' | 'email' | 'chat' | 'phone';
}

interface TicketCreationResponse {
  success: boolean;
  ticketId?: string;
  ticketNumber?: string;
  ticketUrl?: string;
  error?: string;
}

interface EscalationRequest {
  ticketId?: string;
  customerPhone: string;
  issue: string;
  escalationType: 'human_agent' | 'supervisor' | 'technical' | 'billing';
  priority: 'normal' | 'urgent';
}

interface EscalationResponse {
  success: boolean;
  escalationId?: string;
  assignedAgent?: string;
  estimatedWaitTime?: number;
  error?: string;
}

export class N8NWorkflowService {
  private config: N8NWorkflowConfig;
  private apiKey: string;

  constructor(config: N8NWorkflowConfig, apiKey: string) {
    this.config = config;
    this.apiKey = apiKey;
  }

  private async makeRequest<T>(endpoint: string, data: any): Promise<T> {
    const url = `${this.config.webhookUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
          'X-Workflow-ID': this.config.workflowId
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        throw new Error(`N8N API request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('N8N Workflow API Error:', error);
      throw error;
    }
  }

  async checkCalendarAvailability(request: CalendarAvailabilityRequest): Promise<CalendarAvailabilityResponse> {
    return this.makeRequest<CalendarAvailabilityResponse>(
      this.config.availabilityEndpoint,
      {
        action: 'check_availability',
        ...request
      }
    );
  }

  async bookAppointment(request: AppointmentBookingRequest): Promise<AppointmentBookingResponse> {
    return this.makeRequest<AppointmentBookingResponse>(
      this.config.calendarEndpoint,
      {
        action: 'book_appointment',
        ...request
      }
    );
  }

  async createTicket(request: TicketCreationRequest): Promise<TicketCreationResponse> {
    return this.makeRequest<TicketCreationResponse>(
      this.config.ticketEndpoint,
      {
        action: 'create_ticket',
        timestamp: new Date().toISOString(),
        ...request
      }
    );
  }

  async escalateIssue(request: EscalationRequest): Promise<EscalationResponse> {
    return this.makeRequest<EscalationResponse>(
      this.config.escalationEndpoint,
      {
        action: 'escalate_issue',
        timestamp: new Date().toISOString(),
        ...request
      }
    );
  }

  async getWorkflowStatus(): Promise<{ active: boolean; lastExecution?: string; errors?: string[] }> {
    try {
      const response = await this.makeRequest<any>('/status', {
        action: 'get_status',
        workflowId: this.config.workflowId
      });

      return {
        active: response.active || false,
        lastExecution: response.lastExecution,
        errors: response.errors || []
      };
    } catch (error) {
      return {
        active: false,
        errors: [error instanceof Error ? error.message : 'Unknown error']
      };
    }
  }

  async testConnection(): Promise<{ success: boolean; message: string }> {
    try {
      const response = await this.makeRequest<any>('/test', {
        action: 'test_connection',
        timestamp: new Date().toISOString()
      });

      return {
        success: true,
        message: response.message || 'Connection successful'
      };
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Connection failed'
      };
    }
  }

  static createHelpdeskWorkflow(config: {
    workflowName: string;
    calendarProvider: string;
    ticketProvider: string;
    businessHours: any;
  }): any {
    return {
      name: config.workflowName,
      nodes: [
        {
          id: 'webhook-trigger',
          type: 'webhook',
          position: [250, 300],
          parameters: {
            path: '/helpdesk',
            httpMethod: 'POST',
            responseMode: 'responseNode'
          }
        },
        {
          id: 'route-action',
          type: 'switch',
          position: [450, 300],
          parameters: {
            dataType: 'string',
            value1: '={{$json.action}}',
            rules: {
              rules: [
                { operation: 'equal', value2: 'check_availability' },
                { operation: 'equal', value2: 'book_appointment' },
                { operation: 'equal', value2: 'create_ticket' },
                { operation: 'equal', value2: 'escalate_issue' }
              ]
            }
          }
        },
        {
          id: 'calendar-availability',
          type: 'function',
          position: [650, 200],
          parameters: {
            code: `
              const { date, timeZone, duration } = items[0].json;

              // Business hours check
              const businessHours = ${JSON.stringify(config.businessHours)};
              const requestDate = new Date(date);
              const dayOfWeek = requestDate.toLocaleDateString('en-US', { weekday: 'lowercase' });

              if (!businessHours.schedule[dayOfWeek]?.enabled) {
                return [{
                  json: {
                    available: false,
                    slots: [],
                    reason: 'Outside business hours'
                  }
                }];
              }

              // Mock availability slots (integrate with actual calendar API)
              const slots = [
                { start: '09:00', end: '10:00' },
                { start: '14:00', end: '15:00' },
                { start: '16:00', end: '17:00' }
              ];

              return [{
                json: {
                  available: true,
                  slots,
                  date,
                  timeZone
                }
              }];
            `
          }
        },
        {
          id: 'book-appointment',
          type: 'function',
          position: [650, 300],
          parameters: {
            code: `
              const appointment = items[0].json;

              // Generate appointment ID
              const appointmentId = 'apt_' + Math.random().toString(36).substr(2, 9);

              // Mock booking (integrate with actual calendar API)
              return [{
                json: {
                  success: true,
                  appointmentId,
                  confirmationUrl: \`https://calendar.example.com/appointment/\${appointmentId}\`,
                  details: appointment
                }
              }];
            `
          }
        },
        {
          id: 'create-ticket',
          type: 'function',
          position: [650, 400],
          parameters: {
            code: `
              const ticket = items[0].json;

              // Generate ticket ID
              const ticketId = 'TKT-' + Math.random().toString(36).substr(2, 6).toUpperCase();

              // Mock ticket creation (integrate with actual ticket system)
              return [{
                json: {
                  success: true,
                  ticketId,
                  ticketNumber: ticketId,
                  ticketUrl: \`https://support.example.com/tickets/\${ticketId}\`,
                  details: ticket
                }
              }];
            `
          }
        },
        {
          id: 'escalate-issue',
          type: 'function',
          position: [650, 500],
          parameters: {
            code: `
              const escalation = items[0].json;

              // Generate escalation ID
              const escalationId = 'ESC-' + Math.random().toString(36).substr(2, 6).toUpperCase();

              // Mock escalation (integrate with actual escalation system)
              return [{
                json: {
                  success: true,
                  escalationId,
                  assignedAgent: 'Agent Smith',
                  estimatedWaitTime: escalation.priority === 'urgent' ? 60 : 300,
                  details: escalation
                }
              }];
            `
          }
        },
        {
          id: 'response',
          type: 'respond-to-webhook',
          position: [850, 350],
          parameters: {
            responseBody: '={{$json}}'
          }
        }
      ],
      connections: {
        'webhook-trigger': {
          main: [['route-action']]
        },
        'route-action': {
          main: [
            ['calendar-availability'],
            ['book-appointment'],
            ['create-ticket'],
            ['escalate-issue']
          ]
        },
        'calendar-availability': {
          main: [['response']]
        },
        'book-appointment': {
          main: [['response']]
        },
        'create-ticket': {
          main: [['response']]
        },
        'escalate-issue': {
          main: [['response']]
        }
      }
    };
  }
}

export type {
  N8NWorkflowConfig,
  CalendarAvailabilityRequest,
  CalendarAvailabilityResponse,
  AppointmentBookingRequest,
  AppointmentBookingResponse,
  TicketCreationRequest,
  TicketCreationResponse,
  EscalationRequest,
  EscalationResponse
};