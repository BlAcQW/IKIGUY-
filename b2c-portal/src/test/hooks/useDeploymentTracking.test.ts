/**
 * Test suite for useDeploymentTracking hooks
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useDeploymentStatus,
  useDeploymentAnalytics,
  useActivityLog,
  useAllDeployments
} from '@/hooks/useDeploymentTracking';

// Mock fetch globally
global.fetch = jest.fn();

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
});

// Mock WebSocket
global.WebSocket = jest.fn().mockImplementation(() => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  close: jest.fn(),
  send: jest.fn(),
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    React.createElement(QueryClientProvider, { client: queryClient }, children)
  );
};

describe('useDeploymentTracking hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue('mock-token');
  });

  describe('useDeploymentStatus', () => {
    const mockDeploymentStatus = {
      automation_id: 'test-automation-123',
      tenant_id: 'test-tenant',
      status: 'DEPLOYED',
      components: {
        vapi_agent: {
          component_id: 'vapi-1',
          component_type: 'VAPI_AGENT',
          status: 'DEPLOYED',
          health_status: 'HEALTHY',
          last_health_check: '2024-01-01T12:00:00Z'
        },
        n8n_workflow: {
          component_id: 'n8n-1',
          component_type: 'N8N_WORKFLOW',
          status: 'DEPLOYED',
          health_status: 'HEALTHY',
          last_health_check: '2024-01-01T12:00:00Z'
        },
        integrations: [],
        custom_tools: [],
        demo_page: {
          component_id: 'demo-1',
          component_type: 'DEMO_PAGE',
          status: 'DEPLOYED',
          health_status: 'HEALTHY',
          last_health_check: '2024-01-01T12:00:00Z'
        }
      },
      deployment_summary: {
        total_components: 3,
        deployed_components: 3,
        failed_components: 0,
        deployment_progress: 100
      },
      health_metrics: {
        last_check: '2024-01-01T12:00:00Z',
        response_time: 150,
        uptime_percentage: 99.9,
        error_rate: 0.01
      },
      created_at: '2024-01-01T10:00:00Z',
      updated_at: '2024-01-01T12:00:00Z'
    };

    it('should fetch deployment status successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDeploymentStatus,
      });

      const { result } = renderHook(
        () => useDeploymentStatus('test-automation-123'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.deploymentStatus).toEqual(mockDeploymentStatus);
      expect(result.current.error).toBeNull();
    });

    it('should handle fetch error gracefully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      });

      const { result } = renderHook(
        () => useDeploymentStatus('non-existent-automation'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.deploymentStatus).toBeUndefined();
      expect(result.current.error).toBeTruthy();
    });

    it('should not fetch when automationId is empty', () => {
      const { result } = renderHook(
        () => useDeploymentStatus(''),
        { wrapper: createWrapper() }
      );

      expect(result.current.isLoading).toBe(false);
      expect(result.current.deploymentStatus).toBeUndefined();
      expect(fetch).not.toHaveBeenCalled();
    });

    it('should trigger health check successfully', async () => {
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockDeploymentStatus,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        });

      const { result } = renderHook(
        () => useDeploymentStatus('test-automation-123'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Trigger health check
      result.current.triggerHealthCheck();

      expect(result.current.isTriggering).toBe(true);

      await waitFor(() => {
        expect(result.current.isTriggering).toBe(false);
      });

      // Should have called health check endpoint
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('health-check'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('useDeploymentAnalytics', () => {
    const mockAnalytics = {
      tenant_id: 'test-tenant',
      time_range: '30d',
      summary: {
        total_automations: 5,
        deployed_automations: 4,
        failed_deployments: 1,
        avg_deployment_time: 15.5,
        success_rate: 0.8
      },
      deployment_trends: [
        {
          date: '2024-01-01',
          deployments: 2,
          successes: 2,
          failures: 0
        }
      ],
      component_health: [
        {
          component_type: 'VAPI_AGENT',
          total: 5,
          healthy: 4,
          degraded: 1,
          down: 0
        }
      ],
      top_errors: []
    };

    it('should fetch analytics successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAnalytics,
      });

      const { result } = renderHook(
        () => useDeploymentAnalytics('test-tenant', '30d'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.analytics).toEqual(mockAnalytics);
      expect(result.current.error).toBeNull();
    });

    it('should handle analytics fetch error', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      });

      const { result } = renderHook(
        () => useDeploymentAnalytics('test-tenant', '30d'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.analytics).toBeUndefined();
      expect(result.current.error).toBeTruthy();
    });

    it('should not fetch when tenantId is empty', () => {
      const { result } = renderHook(
        () => useDeploymentAnalytics('', '30d'),
        { wrapper: createWrapper() }
      );

      expect(result.current.isLoading).toBe(false);
      expect(result.current.analytics).toBeUndefined();
      expect(fetch).not.toHaveBeenCalled();
    });
  });

  describe('useActivityLog', () => {
    const mockActivityLog = [
      {
        id: 'log-1',
        automation_id: 'test-automation-123',
        tenant_id: 'test-tenant',
        component_id: 'vapi-1',
        action: 'DEPLOYMENT_STARTED',
        status: 'SUCCESS',
        message: 'VAPI agent deployment initiated',
        metadata: {},
        created_at: '2024-01-01T12:00:00Z'
      },
      {
        id: 'log-2',
        automation_id: 'test-automation-123',
        tenant_id: 'test-tenant',
        action: 'HEALTH_CHECK',
        status: 'SUCCESS',
        message: 'All components healthy',
        created_at: '2024-01-01T12:05:00Z'
      }
    ];

    it('should fetch activity log successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockActivityLog,
      });

      const { result } = renderHook(
        () => useActivityLog('test-automation-123', 20),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.activityLog).toEqual(mockActivityLog);
      expect(result.current.error).toBeNull();
    });

    it('should include limit parameter in request', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockActivityLog,
      });

      renderHook(
        () => useActivityLog('test-automation-123', 10),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('limit=10'),
          expect.any(Object)
        );
      });
    });
  });

  describe('useAllDeployments', () => {
    const mockDeployments = [
      {
        automation_id: 'auto-1',
        tenant_id: 'test-tenant',
        status: 'DEPLOYED',
        components: {
          vapi_agent: { health_status: 'HEALTHY' },
          n8n_workflow: { health_status: 'HEALTHY' },
          integrations: [],
          custom_tools: [],
          demo_page: { health_status: 'HEALTHY' }
        },
        deployment_summary: {
          total_components: 3,
          deployed_components: 3,
          failed_components: 0,
          deployment_progress: 100
        },
        health_metrics: {
          last_check: '2024-01-01T12:00:00Z',
          response_time: 150,
          uptime_percentage: 99.9,
          error_rate: 0.01
        },
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T12:00:00Z'
      }
    ];

    it('should fetch all deployments successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDeployments,
      });

      const { result } = renderHook(
        () => useAllDeployments('test-tenant'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.deployments).toEqual(mockDeployments);
      expect(result.current.error).toBeNull();
    });

    it('should include tenant_id parameter in request', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDeployments,
      });

      renderHook(
        () => useAllDeployments('test-tenant'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('tenant_id=test-tenant'),
          expect.any(Object)
        );
      });
    });
  });
});