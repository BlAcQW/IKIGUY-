import { describe, it, expect, vi, beforeEach } from 'vitest';
import { VAPIHelpdeskService } from '../vapiHelpdeskService';
import { N8NWorkflowService } from '../n8nWorkflowService';
import type { VAPIHelpdeskConfig } from '../vapiHelpdeskService';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock N8N service
const mockN8NService = {
  checkCalendarAvailability: vi.fn(),
  bookAppointment: vi.fn(),
  createTicket: vi.fn(),
  escalateIssue: vi.fn(),
  getWorkflowStatus: vi.fn(),
  testConnection: vi.fn()
} as unknown as N8NWorkflowService;

const mockConfig: VAPIHelpdeskConfig = {
  assistantId: 'test-assistant-123',
  phoneNumberId: 'test-phone-123',
  voiceId: 'jennifer',
  model: 'gpt-4',
  maxDuration: 600,
  silenceTimeoutMs: 30000,
  responseDelayMs: 1000,
  n8nService: mockN8NService,
  businessHours: {
    enabled: true,
    timeZone: 'America/New_York',
    schedule: {
      monday: { start: '09:00', end: '17:00', enabled: true },
      tuesday: { start: '09:00', end: '17:00', enabled: true },
      wednesday: { start: '09:00', end: '17:00', enabled: true },
      thursday: { start: '09:00', end: '17:00', enabled: true },
      friday: { start: '09:00', end: '17:00', enabled: true },
      saturday: { start: '10:00', end: '14:00', enabled: false },
      sunday: { start: '10:00', end: '14:00', enabled: false }
    }
  },
  escalationRules: {
    enabled: true,
    maxWaitTime: 300,
    escalateToPhone: '+1234567890',
    escalateToEmail: 'support@example.com'
  }
};

const mockApiKey = 'test-vapi-key-123';

describe('VAPIHelpdeskService', () => {
  let service: VAPIHelpdeskService;

  beforeEach(() => {
    vi.clearAllMocks();
    service = new VAPIHelpdeskService(mockConfig, mockApiKey);
  });

  describe('createHelpdeskAssistant', () => {
    it('should create a helpdesk assistant with correct configuration', async () => {
      const mockResponse = {
        id: 'assistant-123',
        name: 'Helpdesk Support Assistant'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const result = await service.createHelpdeskAssistant();

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.vapi.ai/assistant',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-vapi-key-123'
          },
          body: expect.stringContaining('"name":"Helpdesk Support Assistant"')
        }
      );

      expect(result).toEqual(mockResponse);
    });

    it('should include all required functions in assistant configuration', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 'assistant-123' })
      });

      await service.createHelpdeskAssistant();

      const callArgs = mockFetch.mock.calls[0];
      const requestBody = JSON.parse(callArgs[1].body);

      expect(requestBody.model.functions).toHaveLength(5);

      const functionNames = requestBody.model.functions.map((f: any) => f.name);
      expect(functionNames).toContain('check_availability');
      expect(functionNames).toContain('book_appointment');
      expect(functionNames).toContain('create_support_ticket');
      expect(functionNames).toContain('escalate_to_human');
      expect(functionNames).toContain('get_business_hours');
    });
  });

  describe('handleFunctionCall', () => {
    const mockCallContext = {
      customerPhone: '+1234567890'
    };

    it('should handle check_availability function call', async () => {
      const mockAvailabilityResponse = {
        available: true,
        slots: [{ start: '09:00', end: '10:00' }]
      };

      (mockN8NService.checkCalendarAvailability as any).mockResolvedValueOnce(mockAvailabilityResponse);

      const result = await service.handleFunctionCall(
        'check_availability',
        { date: '2024-01-15', duration: 30 },
        mockCallContext
      );

      expect(mockN8NService.checkCalendarAvailability).toHaveBeenCalledWith({
        date: '2024-01-15',
        timeZone: 'America/New_York',
        duration: 30
      });

      expect(result).toEqual(mockAvailabilityResponse);
    });

    it('should handle book_appointment function call', async () => {
      const mockBookingResponse = {
        success: true,
        appointmentId: 'apt_123'
      };

      (mockN8NService.bookAppointment as any).mockResolvedValueOnce(mockBookingResponse);

      const parameters = {
        date: '2024-01-15',
        time: '14:00',
        customerName: 'John Doe',
        customerEmail: 'john@example.com',
        description: 'Support meeting'
      };

      const result = await service.handleFunctionCall(
        'book_appointment',
        parameters,
        mockCallContext
      );

      expect(mockN8NService.bookAppointment).toHaveBeenCalledWith({
        ...parameters,
        customerPhone: '+1234567890',
        timeZone: 'America/New_York',
        duration: 30
      });

      expect(result).toEqual(mockBookingResponse);
    });

    it('should handle create_support_ticket function call', async () => {
      const mockTicketResponse = {
        success: true,
        ticketId: 'TKT-123'
      };

      (mockN8NService.createTicket as any).mockResolvedValueOnce(mockTicketResponse);

      const parameters = {
        title: 'Login Issue',
        description: 'Cannot access account',
        customerName: 'John Doe',
        customerEmail: 'john@example.com',
        priority: 'medium'
      };

      const result = await service.handleFunctionCall(
        'create_support_ticket',
        parameters,
        mockCallContext
      );

      expect(mockN8NService.createTicket).toHaveBeenCalledWith({
        ...parameters,
        customerPhone: '+1234567890',
        category: 'general',
        source: 'voice'
      });

      expect(result).toEqual(mockTicketResponse);
    });

    it('should handle escalate_to_human function call', async () => {
      const mockEscalationResponse = {
        success: true,
        escalationId: 'ESC-123'
      };

      (mockN8NService.escalateIssue as any).mockResolvedValueOnce(mockEscalationResponse);

      const parameters = {
        reason: 'Complex technical issue',
        escalationType: 'technical',
        priority: 'urgent'
      };

      const result = await service.handleFunctionCall(
        'escalate_to_human',
        parameters,
        mockCallContext
      );

      expect(mockN8NService.escalateIssue).toHaveBeenCalledWith({
        customerPhone: '+1234567890',
        issue: 'Complex technical issue',
        escalationType: 'technical',
        priority: 'urgent'
      });

      expect(result).toEqual(mockEscalationResponse);
    });

    it('should handle get_business_hours function call', async () => {
      const result = await service.handleFunctionCall(
        'get_business_hours',
        {},
        mockCallContext
      );

      expect(result).toHaveProperty('businessHours');
      expect(result).toHaveProperty('currentTime');
      expect(result).toHaveProperty('isOpen');
      expect(result.businessHours).toEqual(mockConfig.businessHours);
    });

    it('should handle unknown function calls gracefully', async () => {
      const result = await service.handleFunctionCall(
        'unknown_function',
        {},
        mockCallContext
      );

      expect(result).toHaveProperty('error', true);
      expect(result).toHaveProperty('message');
      expect(result.message).toContain('Unknown function');
    });

    it('should handle function errors gracefully', async () => {
      (mockN8NService.checkCalendarAvailability as any).mockRejectedValueOnce(
        new Error('N8N service error')
      );

      const result = await service.handleFunctionCall(
        'check_availability',
        { date: '2024-01-15' },
        mockCallContext
      );

      expect(result).toHaveProperty('error', true);
      expect(result).toHaveProperty('message');
      expect(result.message).toContain('escalate this to a human agent');
    });
  });

  describe('startCall', () => {
    it('should start a call with correct parameters', async () => {
      const mockResponse = {
        id: 'call-123',
        status: 'queued',
        startedAt: '2024-01-15T10:00:00Z'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const result = await service.startCall('+1234567890');

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.vapi.ai/call',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-vapi-key-123'
          },
          body: JSON.stringify({
            phoneNumberId: 'test-phone-123',
            assistantId: 'test-assistant-123',
            customer: {
              number: '+1234567890'
            }
          })
        }
      );

      expect(result).toEqual({
        id: 'call-123',
        phoneNumber: '+1234567890',
        status: 'queued',
        startedAt: '2024-01-15T10:00:00Z'
      });
    });
  });

  describe('getCall', () => {
    it('should retrieve call details', async () => {
      const mockResponse = {
        id: 'call-123',
        status: 'completed',
        customer: { number: '+1234567890' },
        startedAt: '2024-01-15T10:00:00Z',
        endedAt: '2024-01-15T10:05:00Z',
        duration: 300,
        transcript: 'Hello, how can I help you?',
        summary: 'Customer inquiry about billing'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const result = await service.getCall('call-123');

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.vapi.ai/call/call-123',
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-vapi-key-123'
          }
        }
      );

      expect(result).toEqual({
        id: 'call-123',
        phoneNumber: '+1234567890',
        status: 'completed',
        startedAt: '2024-01-15T10:00:00Z',
        endedAt: '2024-01-15T10:05:00Z',
        duration: 300,
        transcript: 'Hello, how can I help you?',
        summary: 'Customer inquiry about billing'
      });
    });
  });

  describe('business hours logic', () => {
    it('should correctly determine if currently open during business hours', () => {
      // Mock current time to be Tuesday 2PM (14:00)
      const mockDate = new Date('2024-01-16T14:00:00'); // Tuesday
      vi.spyOn(global, 'Date').mockImplementation(() => mockDate);

      const isOpen = (service as any).isCurrentlyOpen();
      expect(isOpen).toBe(true);

      vi.restoreAllMocks();
    });

    it('should correctly determine if closed outside business hours', () => {
      // Mock current time to be Tuesday 6PM (18:00) - after hours
      const mockDate = new Date('2024-01-16T18:00:00'); // Tuesday
      vi.spyOn(global, 'Date').mockImplementation(() => mockDate);

      const isOpen = (service as any).isCurrentlyOpen();
      expect(isOpen).toBe(false);

      vi.restoreAllMocks();
    });

    it('should return true when business hours are disabled', () => {
      const configWithDisabledHours = {
        ...mockConfig,
        businessHours: {
          ...mockConfig.businessHours,
          enabled: false
        }
      };

      const serviceWithDisabledHours = new VAPIHelpdeskService(configWithDisabledHours, mockApiKey);
      const isOpen = (serviceWithDisabledHours as any).isCurrentlyOpen();
      expect(isOpen).toBe(true);
    });
  });
});