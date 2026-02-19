/**
 * React hook for deployment tracking and automation analytics
 *
 * Provides hooks for tracking automation deployments, component health,
 * and deployment analytics integration with the Core Backend.
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


const CORE_API_BASE_URL = CORE_API_URL;

// Types for deployment tracking
export interface DeploymentStatus {
  automation_id: string;
  tenant_id: string;
  status: 'PENDING' | 'DEPLOYING' | 'DEPLOYED' | 'FAILED' | 'STOPPED';
  components: {
    vapi_agent: ComponentStatus;
    n8n_workflow: ComponentStatus;
    integrations: ComponentStatus[];
    custom_tools: ComponentStatus[];
    demo_page: ComponentStatus;
  };
  deployment_summary: {
    total_components: number;
    deployed_components: number;
    failed_components: number;
    deployment_progress: number;
  };
  health_metrics: {
    last_check: string;
    response_time: number;
    uptime_percentage: number;
    error_rate: number;
  };
  created_at: string;
  updated_at: string;
}

export interface ComponentStatus {
  component_id: string;
  component_type: 'VAPI_AGENT' | 'N8N_WORKFLOW' | 'INTEGRATION' | 'CUSTOM_TOOL' | 'DEMO_PAGE';
  status: 'PENDING' | 'DEPLOYING' | 'DEPLOYED' | 'FAILED' | 'STOPPED';
  external_id?: string;
  endpoint_url?: string;
  health_status: 'HEALTHY' | 'DEGRADED' | 'DOWN' | 'UNKNOWN';
  last_health_check: string;
  deployment_logs?: string[];
  error_message?: string;
  metadata?: Record<string, any>;
}

export interface DeploymentAnalytics {
  tenant_id: string;
  time_range: string;
  summary: {
    total_automations: number;
    deployed_automations: number;
    failed_deployments: number;
    avg_deployment_time: number;
    success_rate: number;
  };
  deployment_trends: {
    date: string;
    deployments: number;
    successes: number;
    failures: number;
  }[];
  component_health: {
    component_type: string;
    total: number;
    healthy: number;
    degraded: number;
    down: number;
  }[];
  top_errors: {
    error_type: string;
    count: number;
    component_type: string;
    last_occurrence: string;
  }[];
}

export interface ActivityLogEntry {
  id: string;
  automation_id: string;
  tenant_id: string;
  component_id?: string;
  action: string;
  status: string;
  message: string;
  metadata?: Record<string, any>;
  created_at: string;
}

// Helper function to get auth headers
const getAuthHeaders = async () => {
  const token = localStorage.getItem('supabase.auth.token');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
};

// API functions
const fetchDeploymentStatus = async (automationId: string): Promise<DeploymentStatus> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${CORE_API_BASE_URL}/deployment-tracking/automations/${automationId}/status`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch deployment status: ${response.statusText}`);
  }

  return response.json();
};

const fetchDeploymentAnalytics = async (tenantId: string, timeRange: string): Promise<DeploymentAnalytics> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${CORE_API_BASE_URL}/deployment-tracking/analytics?tenant_id=${tenantId}&time_range=${timeRange}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch deployment analytics: ${response.statusText}`);
  }

  return response.json();
};

const fetchActivityLog = async (automationId: string, limit: number = 50): Promise<ActivityLogEntry[]> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${CORE_API_BASE_URL}/deployment-tracking/automations/${automationId}/activity?limit=${limit}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch activity log: ${response.statusText}`);
  }

  return response.json();
};

const fetchAllDeployments = async (tenantId: string): Promise<DeploymentStatus[]> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${CORE_API_BASE_URL}/deployment-tracking/automations?tenant_id=${tenantId}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch deployments: ${response.statusText}`);
  }

  return response.json();
};

const triggerHealthCheck = async (automationId: string): Promise<void> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${CORE_API_BASE_URL}/deployment-tracking/automations/${automationId}/health-check`, {
    method: 'POST',
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to trigger health check: ${response.statusText}`);
  }
};

/**
 * Hook for tracking deployment status of a specific automation
 */
export function useDeploymentStatus(automationId: string) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const {
    data: deploymentStatus,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['deployment-status', automationId],
    queryFn: () => fetchDeploymentStatus(automationId),
    enabled: !!automationId,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const healthCheckMutation = useMutation({
    mutationFn: () => triggerHealthCheck(automationId),
    onSuccess: () => {
      // Refetch status after health check
      setTimeout(() => refetch(), 2000);
      toast({
        title: "Health Check Triggered",
        description: "Component health check initiated",
      });
    },
    onError: (error) => {
      toast({
        title: "Health Check Failed",
        description: `Failed to trigger health check: ${error.message}`,
        variant: "destructive",
      });
    },
  });

  return {
    deploymentStatus,
    isLoading,
    error,
    refetch,
    triggerHealthCheck: healthCheckMutation.mutate,
    isTriggering: healthCheckMutation.isPending,
  };
}

/**
 * Hook for deployment analytics across all automations
 */
export function useDeploymentAnalytics(tenantId: string, timeRange: string = '30d') {
  const { toast } = useToast();

  const {
    data: analytics,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['deployment-analytics', tenantId, timeRange],
    queryFn: () => fetchDeploymentAnalytics(tenantId, timeRange),
    enabled: !!tenantId,
    refetchInterval: 60000, // Refresh every minute
  });

  return {
    analytics,
    isLoading,
    error,
    refetch,
  };
}

/**
 * Hook for activity log of a specific automation
 */
export function useActivityLog(automationId: string, limit: number = 50) {
  const {
    data: activityLog,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['activity-log', automationId, limit],
    queryFn: () => fetchActivityLog(automationId, limit),
    enabled: !!automationId,
    refetchInterval: 15000, // Refresh every 15 seconds
  });

  return {
    activityLog,
    isLoading,
    error,
    refetch,
  };
}

/**
 * Hook for all deployments overview
 */
export function useAllDeployments(tenantId: string) {
  const {
    data: deployments,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['all-deployments', tenantId],
    queryFn: () => fetchAllDeployments(tenantId),
    enabled: !!tenantId,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  return {
    deployments,
    isLoading,
    error,
    refetch,
  };
}

/**
 * Hook for real-time deployment monitoring with WebSocket support
 */
export function useRealTimeDeploymentUpdates(automationId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!automationId) return;

    // WebSocket connection for real-time updates
    const wsUrl = `${CORE_API_BASE_URL.replace('http', 'ws')}/deployment-tracking/ws/${automationId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('Connected to deployment tracking WebSocket');
    };

    ws.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data);
        setLastUpdate(new Date());

        // Update the query cache with real-time data
        queryClient.setQueryData(['deployment-status', automationId], update);

        // Also invalidate to trigger a fresh fetch
        queryClient.invalidateQueries({ queryKey: ['deployment-status', automationId] });
        queryClient.invalidateQueries({ queryKey: ['activity-log', automationId] });
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('Disconnected from deployment tracking WebSocket');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [automationId, queryClient]);

  return {
    isConnected,
    lastUpdate,
  };
}