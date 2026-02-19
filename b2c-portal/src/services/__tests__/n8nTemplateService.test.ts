import { describe, it, expect, vi, beforeEach } from 'vitest';
import { n8nTemplateService } from '../n8nTemplateService';

// Mock fetch globally
global.fetch = vi.fn();

describe('N8nTemplateService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getTemplateById', () => {
    it('should fetch template successfully', async () => {
      const mockTemplate = {
        id: 6213,
        name: 'Customer Reactivation Template',
        description: 'Reactivate dormant customers',
        nodes: [
          { id: 'node1', type: 'webhook', name: 'Webhook' },
          { id: 'node2', type: 'googleSheets', name: 'Google Sheets' }
        ],
        connections: {},
        views: 100,
        created: '2025-01-01T00:00:00Z',
        url: 'https://n8n.io/workflows/6213'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ success: true, template: mockTemplate })
      });

      const result = await n8nTemplateService.getTemplateById(6213);

      expect(result.success).toBe(true);
      expect(result.workflow).toEqual(mockTemplate);
      expect(fetch).toHaveBeenCalledWith('/api/n8n-mcp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: 'get_template',
          params: { templateId: 6213, mode: 'full' }
        })
      });
    });

    it('should handle fetch errors', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found'
      });

      const result = await n8nTemplateService.getTemplateById(6213);

      expect(result.success).toBe(false);
      expect(result.error).toContain('HTTP 404');
    });

    it('should use cache for repeated requests', async () => {
      const mockTemplate = {
        id: 6213,
        name: 'Customer Reactivation Template',
        nodes: [],
        connections: {},
        views: 100,
        created: '2025-01-01T00:00:00Z',
        url: 'https://n8n.io/workflows/6213'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ success: true, template: mockTemplate })
      });

      // First call
      const result1 = await n8nTemplateService.getTemplateById(6213);
      expect(result1.success).toBe(true);

      // Second call should use cache
      const result2 = await n8nTemplateService.getTemplateById(6213);
      expect(result2.success).toBe(true);
      expect(result2.workflow).toEqual(mockTemplate);

      // Fetch should only be called once
      expect(fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('searchTemplates', () => {
    it('should search templates successfully', async () => {
      const mockSearchResults = {
        success: true,
        items: [
          {
            id: 6213,
            name: 'Customer Reactivation Template',
            description: 'Reactivate dormant customers'
          },
          {
            id: 5678,
            name: 'Lead Nurturing Template',
            description: 'Nurture leads through email sequences'
          }
        ]
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockSearchResults
      });

      const result = await n8nTemplateService.searchTemplates('customer reactivation', 10);

      expect(result.success).toBe(true);
      expect(result.templates).toHaveLength(2);
      expect(result.templates?.[0].id).toBe(6213);
      expect(fetch).toHaveBeenCalledWith('/api/n8n-mcp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: 'search_templates',
          params: { query: 'customer reactivation', limit: 10 }
        })
      });
    });

    it('should handle search errors', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      const result = await n8nTemplateService.searchTemplates('customer reactivation');

      expect(result.success).toBe(false);
      expect(result.error).toContain('HTTP 500');
    });
  });

  describe('importTemplateToWorkflow', () => {
    it('should import template and create workflow', async () => {
      const mockTemplate = {
        id: 6213,
        name: 'Customer Reactivation Template',
        nodes: [
          { id: 'node1', type: 'webhook', name: 'Webhook' }
        ],
        connections: {}
      };

      const mockWorkflowResponse = {
        success: true,
        id: 'workflow-123'
      };

      // Mock template fetch
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ success: true, template: mockTemplate })
      });

      // Mock workflow creation
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockWorkflowResponse
      });

      const result = await n8nTemplateService.importTemplateToWorkflow(6213, 'campaign-123');

      expect(result.success).toBe(true);
      expect(result.workflowId).toBe('workflow-123');
    });

    it('should handle template not found', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found'
      });

      const result = await n8nTemplateService.importTemplateToWorkflow(6213, 'campaign-123');

      expect(result.success).toBe(false);
      expect(result.error).toContain('Template not found');
    });
  });

  describe('validateTemplate', () => {
    it('should validate template with n8n integration', async () => {
      const mockTemplate = {
        id: 'customer_reactivation',
        name: 'Customer Reactivation Campaign',
        category: 'marketing' as const,
        difficulty: 'advanced' as const,
        estimatedSetupTime: '30-40 minutes',
        features: ['SMS', 'Email', 'AI'],
        defaultIntegrations: ['n8n', 'twilio', 'openai'],
        n8nTemplateId: 6213,
        icon: vi.fn(),
        sampleData: {
          expectedResponses: 45,
          conversionRate: '15-25%',
          avgCallDuration: '4-6 minutes'
        }
      };

      const mockWorkflow = {
        id: 6213,
        name: 'Reactivation Workflow',
        metadata: {
          complexity: 'complex',
          estimated_setup_minutes: 35,
          required_services: ['twilio', 'openai', 'google_sheets']
        }
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ success: true, template: mockWorkflow })
      });

      const result = await n8nTemplateService.validateTemplate(mockTemplate);

      expect(result.valid).toBe(true);
      expect(result.issues).toHaveLength(0);
      expect(result.recommendations).toContain('Consider adding integrations: google_sheets');
    });

    it('should detect missing template', async () => {
      const mockTemplate = {
        id: 'invalid_template',
        name: 'Invalid Template',
        category: 'marketing' as const,
        difficulty: 'beginner' as const,
        estimatedSetupTime: '10 minutes',
        features: [],
        defaultIntegrations: [],
        n8nTemplateId: 99999,
        icon: vi.fn(),
        sampleData: {
          expectedResponses: 0,
          conversionRate: '0%',
          avgCallDuration: '0 minutes'
        }
      };

      (fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found'
      });

      const result = await n8nTemplateService.validateTemplate(mockTemplate);

      expect(result.valid).toBe(false);
      expect(result.issues).toContain('Template 99999 not found in n8n repository');
    });
  });

  describe('clearCache', () => {
    it('should clear template cache', async () => {
      const mockTemplate = {
        id: 6213,
        name: 'Test Template',
        nodes: [],
        connections: {},
        views: 0,
        created: '2025-01-01T00:00:00Z',
        url: 'https://n8n.io/workflows/6213'
      };

      // First call to populate cache
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ success: true, template: mockTemplate })
      });

      await n8nTemplateService.getTemplateById(6213);
      expect(fetch).toHaveBeenCalledTimes(1);

      // Clear cache
      n8nTemplateService.clearCache();

      // Second call should fetch again
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ success: true, template: mockTemplate })
      });

      await n8nTemplateService.getTemplateById(6213);
      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });
});