import { describe, it, expect, vi, beforeEach } from 'vitest';
import { N8NWorkflowService } from '../n8nWorkflowService';
import type { N8NWorkflowConfig } from '../n8nWorkflowService';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockConfig: N8NWorkflowConfig = {
  workflowId: 'test-workflow-123',
  workflowName: 'Helpdesk Automation',
  webhookUrl: 'https://n8n.example.com/webhook',
  calendarEndpoint: '/calendar',
  ticketEndpoint: '/tickets',
  availabilityEndpoint: '/availability',
  escalationEndpoint: '/escalation'
};

const mockApiKey = 'test-api-key-123';

describe('N8NWorkflowService', () => {
  let service: N8NWorkflowService;

  beforeEach(() => {
    vi.clearAllMocks();
    service = new N8NWorkflowService(mockConfig, mockApiKey);
  });

  describe('checkCalendarAvailability', () => {
    it('should make correct API request for availability check', async () => {
      const mockResponse = {
        available: true,
        slots: [
          { start: '09:00', end: '10:00' },
          { start: '14:00', end: '15:00' }
        ]
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const request = {
        date: '2024-01-15',
        timeZone: 'America/New_York',
        duration: 30
      };

      const result = await service.checkCalendarAvailability(request);

      expect(mockFetch).toHaveBeenCalledWith(
        'https://n8n.example.com/webhook/availability',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-api-key-123',
            'X-Workflow-ID': 'test-workflow-123'
          },
          body: JSON.stringify({
            action: 'check_availability',
            ...request
          })
        }
      );

      expect(result).toEqual(mockResponse);
    });

    it('should handle API errors correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      const request = {
        date: '2024-01-15',
        timeZone: 'America/New_York',
        duration: 30
      };

      await expect(service.checkCalendarAvailability(request)).rejects.toThrow(
        'N8N API request failed: 500 Internal Server Error'
      );
    });
  });

  describe('bookAppointment', () => {
    it('should successfully book an appointment', async () => {
      const mockResponse = {
        success: true,
        appointmentId: 'apt_123456789',
        confirmationUrl: 'https://calendar.example.com/appointment/apt_123456789'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const request = {
        date: '2024-01-15',
        time: '14:00',
        duration: 30,
        customerName: 'John Doe',
        customerEmail: 'john@example.com',
        customerPhone: '+1234567890',
        description: 'Support consultation',
        timeZone: 'America/New_York'
      };

      const result = await service.bookAppointment(request);

      expect(mockFetch).toHaveBeenCalledWith(
        'https://n8n.example.com/webhook/calendar',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-api-key-123',
            'X-Workflow-ID': 'test-workflow-123'
          },
          body: JSON.stringify({
            action: 'book_appointment',
            ...request
          })
        }
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('createTicket', () => {
    it('should successfully create a support ticket', async () => {
      const mockResponse = {
        success: true,
        ticketId: 'TKT-123456',
        ticketNumber: 'TKT-123456',
        ticketUrl: 'https://support.example.com/tickets/TKT-123456'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const request = {
        title: 'Login Issue',
        description: 'Cannot access account after password reset',
        priority: 'medium' as const,
        customerName: 'John Doe',
        customerEmail: 'john@example.com',
        customerPhone: '+1234567890',
        category: 'technical',
        source: 'voice' as const
      };

      const result = await service.createTicket(request);

      expect(mockFetch).toHaveBeenCalledWith(
        'https://n8n.example.com/webhook/tickets',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-api-key-123',
            'X-Workflow-ID': 'test-workflow-123'
          },
          body: expect.stringContaining('"action":"create_ticket"')
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('escalateIssue', () => {
    it('should successfully escalate an issue', async () => {
      const mockResponse = {
        success: true,
        escalationId: 'ESC-ABC123',
        assignedAgent: 'Agent Smith',
        estimatedWaitTime: 300
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const request = {
        customerPhone: '+1234567890',
        issue: 'Complex technical issue requiring specialist',
        escalationType: 'technical' as const,
        priority: 'urgent' as const
      };

      const result = await service.escalateIssue(request);

      expect(mockFetch).toHaveBeenCalledWith(
        'https://n8n.example.com/webhook/escalation',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"action":"escalate_issue"')
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('getWorkflowStatus', () => {
    it('should return workflow status', async () => {
      const mockResponse = {
        active: true,
        lastExecution: '2024-01-15T10:30:00Z',
        errors: []
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const result = await service.getWorkflowStatus();

      expect(result).toEqual({
        active: true,
        lastExecution: '2024-01-15T10:30:00Z',
        errors: []
      });
    });

    it('should handle errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await service.getWorkflowStatus();

      expect(result).toEqual({
        active: false,
        errors: ['Network error']
      });
    });
  });

  describe('testConnection', () => {
    it('should test connection successfully', async () => {
      const mockResponse = {
        message: 'Connection successful'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const result = await service.testConnection();

      expect(result).toEqual({
        success: true,
        message: 'Connection successful'
      });
    });

    it('should handle connection failure', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Connection failed'));

      const result = await service.testConnection();

      expect(result).toEqual({
        success: false,
        message: 'Connection failed'
      });
    });
  });

  describe('createHelpdeskWorkflow', () => {
    it('should create a valid workflow configuration', () => {
      const config = {
        workflowName: 'Test Helpdesk',
        calendarProvider: 'google',
        ticketProvider: 'zendesk',
        businessHours: {
          enabled: true,
          schedule: {
            monday: { start: '09:00', end: '17:00', enabled: true }
          }
        }
      };

      const workflow = N8NWorkflowService.createHelpdeskWorkflow(config);

      expect(workflow).toHaveProperty('name', 'Test Helpdesk');
      expect(workflow).toHaveProperty('nodes');
      expect(workflow).toHaveProperty('connections');
      expect(workflow.nodes).toHaveLength(7); // webhook, switch, 4 functions, response
      expect(workflow.nodes[0].type).toBe('webhook');
      expect(workflow.nodes[1].type).toBe('switch');
    });
  });
});