/**
 * Integration Hooks for ChurchFlow
 *
 * React Query hooks for managing external integrations:
 * - Google Calendar sync
 * - Zapier webhooks
 * - Integration dashboard
 */

import { useQuery, useMutation, useQueryClient, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import axios from 'axios';
import { encodeHeaderValue } from '../lib/header-utils';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://churchflow-api.ailabsafrica.com/api/v1';

// ============================================================================
// Types
// ============================================================================

export type IntegrationType = 'google_calendar' | 'zapier' | 'email_campaign' | 'stripe_billing';
export type IntegrationStatus = 'active' | 'inactive' | 'error' | 'pending_auth';
export type WebhookEventType =
  | 'conference.created'
  | 'conference.updated'
  | 'conference.deleted'
  | 'registration.created'
  | 'registration.updated'
  | 'registration.checked_in'
  | 'payment.received'
  | 'sms.sent'
  | 'email.sent';

export interface GoogleCalendarConfig {
  calendar_id: string;
  credentials_json?: Record<string, any>;
  auto_sync_events: boolean;
  two_way_sync: boolean;
  sync_interval_minutes: number;
  include_registration_count: boolean;
}

export interface ZapierWebhookConfig {
  webhook_url: string;
  enabled_events: WebhookEventType[];
  secret_key?: string;
  retry_on_failure: boolean;
  max_retries: number;
  timeout_seconds: number;
}

export interface IntegrationConfig {
  id?: string;
  organization_id: string;
  integration_type: IntegrationType;
  status: IntegrationStatus;
  google_calendar?: GoogleCalendarConfig;
  zapier_webhook?: ZapierWebhookConfig;
  email_campaign?: any;
  created_at: string;
  updated_at: string;
  last_sync_at?: string;
  error_message?: string;
  sync_count: number;
}

export interface IntegrationHealth {
  integration_type: IntegrationType;
  status: IntegrationStatus;
  last_sync_at?: string;
  error_message?: string;
  success_rate: number;
  total_syncs: number;
  successful_syncs: number;
  failed_syncs: number;
}

export interface IntegrationDashboard {
  organization_id: string;
  organization_name: string;
  integrations: IntegrationHealth[];
  total_active_integrations: number;
  total_inactive_integrations: number;
  total_error_integrations: number;
  last_updated: string;
}

export interface WebhookDelivery {
  id?: string;
  organization_id: string;
  webhook_url: string;
  event_type: WebhookEventType;
  payload: Record<string, any>;
  success: boolean;
  status_code?: number;
  response_body?: string;
  error_message?: string;
  attempt_number: number;
  max_attempts: number;
  next_retry_at?: string;
  created_at: string;
  delivered_at?: string;
}

export interface WebhookStats {
  total_deliveries: number;
  successful_deliveries: number;
  failed_deliveries: number;
  success_rate: number;
  avg_attempts: number;
}

// ============================================================================
// API Functions
// ============================================================================

async function fetchIntegrationDashboard(
  token: string,
  organizationId: string
): Promise<IntegrationDashboard> {
  const response = await axios.get(
    `${API_BASE_URL}/integrations/dashboard`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );
  return response.data;
}

async function fetchIntegrationConfig(
  token: string,
  organizationId: string,
  integrationType: IntegrationType
): Promise<IntegrationConfig> {
  const response = await axios.get(
    `${API_BASE_URL}/integrations/config/${integrationType}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );
  return response.data;
}

async function configureGoogleCalendar(
  token: string,
  organizationId: string,
  config: GoogleCalendarConfig,
  credentials: Record<string, any>
): Promise<any> {
  const response = await axios.post(
    `${API_BASE_URL}/integrations/google-calendar/configure`,
    { config, credentials },
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );
  return response.data;
}

async function testGoogleCalendar(
  token: string,
  organizationId: string
): Promise<any> {
  const response = await axios.post(
    `${API_BASE_URL}/integrations/google-calendar/test`,
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );
  return response.data;
}

async function syncConferenceToCalendar(
  token: string,
  organizationId: string,
  conferenceId: string
): Promise<any> {
  const response = await axios.post(
    `${API_BASE_URL}/integrations/google-calendar/sync/${conferenceId}`,
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );
  return response.data;
}

async function batchSyncConferences(
  token: string,
  organizationId: string,
  limit: number = 50
): Promise<any> {
  const response = await axios.post(
    `${API_BASE_URL}/integrations/google-calendar/batch-sync?limit=${limit}`,
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );
  return response.data;
}

async function configureZapierWebhook(
  token: string,
  organizationId: string,
  config: ZapierWebhookConfig
): Promise<any> {
  const response = await axios.post(
    `${API_BASE_URL}/integrations/zapier/configure`,
    config,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );
  return response.data;
}

async function testZapierWebhook(
  token: string,
  organizationId: string,
  webhookUrl: string
): Promise<any> {
  const response = await axios.post(
    `${API_BASE_URL}/integrations/zapier/test`,
    { webhook_url: webhookUrl },
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );
  return response.data;
}

async function fetchWebhookDeliveries(
  token: string,
  organizationId: string,
  params: {
    event_type?: WebhookEventType;
    webhook_url?: string;
    limit?: number;
  }
): Promise<WebhookDelivery[]> {
  const queryParams = new URLSearchParams();
  if (params.event_type) queryParams.append('event_type', params.event_type);
  if (params.webhook_url) queryParams.append('webhook_url', params.webhook_url);
  if (params.limit) queryParams.append('limit', params.limit.toString());

  const response = await axios.get(
    `${API_BASE_URL}/integrations/zapier/deliveries?${queryParams.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );
  return response.data;
}

async function fetchWebhookStats(
  token: string,
  organizationId: string,
  webhookUrl?: string,
  days: number = 7
): Promise<{ stats: WebhookStats; period_days: number }> {
  const queryParams = new URLSearchParams({ days: days.toString() });
  if (webhookUrl) queryParams.append('webhook_url', webhookUrl);

  const response = await axios.get(
    `${API_BASE_URL}/integrations/zapier/stats?${queryParams.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );
  return response.data;
}

async function deleteIntegration(
  token: string,
  organizationId: string,
  integrationType: IntegrationType
): Promise<any> {
  const response = await axios.delete(
    `${API_BASE_URL}/integrations/config/${integrationType}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );
  return response.data;
}

// ============================================================================
// React Query Hooks
// ============================================================================

export function useIntegrationDashboard(
  token: string | null,
  organizationId: string | null
): UseQueryResult<IntegrationDashboard, Error> {
  return useQuery({
    queryKey: ['integration-dashboard', organizationId],
    queryFn: () => fetchIntegrationDashboard(token!, organizationId!),
    enabled: !!token && !!organizationId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useIntegrationConfig(
  token: string | null,
  organizationId: string | null,
  integrationType: IntegrationType
): UseQueryResult<IntegrationConfig, Error> {
  return useQuery({
    queryKey: ['integration-config', organizationId, integrationType],
    queryFn: () => fetchIntegrationConfig(token!, organizationId!, integrationType),
    enabled: !!token && !!organizationId,
    staleTime: 5 * 60 * 1000,
    retry: false, // Don't retry if config not found
  });
}

export function useConfigureGoogleCalendar(
  token: string | null,
  organizationId: string | null
): UseMutationResult<any, Error, { config: GoogleCalendarConfig; credentials: Record<string, any> }> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ config, credentials }) =>
      configureGoogleCalendar(token!, organizationId!, config, credentials),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['integration-config', organizationId, 'google_calendar'] });
    },
  });
}

export function useTestGoogleCalendar(
  token: string | null,
  organizationId: string | null
): UseMutationResult<any, Error, void> {
  return useMutation({
    mutationFn: () => testGoogleCalendar(token!, organizationId!),
  });
}

export function useSyncConferenceToCalendar(
  token: string | null,
  organizationId: string | null
): UseMutationResult<any, Error, string> {
  return useMutation({
    mutationFn: (conferenceId: string) =>
      syncConferenceToCalendar(token!, organizationId!, conferenceId),
  });
}

export function useBatchSyncConferences(
  token: string | null,
  organizationId: string | null
): UseMutationResult<any, Error, number> {
  return useMutation({
    mutationFn: (limit: number = 50) =>
      batchSyncConferences(token!, organizationId!, limit),
  });
}

export function useConfigureZapierWebhook(
  token: string | null,
  organizationId: string | null
): UseMutationResult<any, Error, ZapierWebhookConfig> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (config: ZapierWebhookConfig) =>
      configureZapierWebhook(token!, organizationId!, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['integration-config', organizationId, 'zapier'] });
    },
  });
}

export function useTestZapierWebhook(
  token: string | null,
  organizationId: string | null
): UseMutationResult<any, Error, string> {
  return useMutation({
    mutationFn: (webhookUrl: string) =>
      testZapierWebhook(token!, organizationId!, webhookUrl),
  });
}

export function useWebhookDeliveries(
  token: string | null,
  organizationId: string | null,
  params: {
    event_type?: WebhookEventType;
    webhook_url?: string;
    limit?: number;
  }
): UseQueryResult<WebhookDelivery[], Error> {
  return useQuery({
    queryKey: ['webhook-deliveries', organizationId, params],
    queryFn: () => fetchWebhookDeliveries(token!, organizationId!, params),
    enabled: !!token && !!organizationId,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

export function useWebhookStats(
  token: string | null,
  organizationId: string | null,
  webhookUrl?: string,
  days: number = 7
): UseQueryResult<{ stats: WebhookStats; period_days: number }, Error> {
  return useQuery({
    queryKey: ['webhook-stats', organizationId, webhookUrl, days],
    queryFn: () => fetchWebhookStats(token!, organizationId!, webhookUrl, days),
    enabled: !!token && !!organizationId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useDeleteIntegration(
  token: string | null,
  organizationId: string | null
): UseMutationResult<any, Error, IntegrationType> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (integrationType: IntegrationType) =>
      deleteIntegration(token!, organizationId!, integrationType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['integration-config'] });
    },
  });
}
