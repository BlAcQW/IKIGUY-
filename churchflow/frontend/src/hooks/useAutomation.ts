/**
 * Automation React Query Hooks
 *
 * Custom hooks for managing automation workflows and reminders.
 */

import { useQuery, useMutation, useQueryClient, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import axios from 'axios';
import { encodeHeaderValue } from '../lib/header-utils';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://churchflow-api.ailabsafrica.com/api/v1';

// ==================== Types ====================

export type AutomationType = 'event_reminder' | 'member_onboarding' | 'post_event_followup' | 'volunteer_recruitment' | 'giving_campaign';
export type ReminderTiming = '7_days_before' | '3_days_before' | '1_day_before' | 'morning_of' | 'custom';
export type NotificationChannel = 'sms' | 'email' | 'push' | 'whatsapp';
export type AutomationStatus = 'active' | 'paused' | 'completed' | 'cancelled' | 'failed';

export interface ReminderStep {
  timing: ReminderTiming;
  days_before?: number;
  hours_before?: number;
  channel: NotificationChannel;
  message_template: string;
  enabled: boolean;
}

export interface EventReminderConfig {
  enabled: boolean;
  reminder_steps: ReminderStep[];
  send_to_registered_only: boolean;
  include_qr_code: boolean;
  include_venue_details: boolean;
}

export interface AutomationWorkflow {
  _id: string;
  organization_id: string;
  automation_type: string;
  name: string;
  description?: string;
  event_reminder_config?: EventReminderConfig;
  conference_id?: string;
  branch_id?: string;
  status: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  last_execution_at?: string;
  next_execution_at?: string;
}

export interface ScheduledReminder {
  _id: string;
  workflow_id: string;
  organization_id: string;
  conference_id: string;
  reminder_step: ReminderStep;
  scheduled_at: string;
  recipient_count: number;
  status: string;
  executed_at?: string;
  sms_campaign_id?: string;
  sent_count: number;
  delivered_count: number;
  failed_count: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface AutomationDashboard {
  total_workflows: number;
  active_workflows: number;
  paused_workflows: number;
  pending_reminders: number;
  upcoming_reminders_24h: number;
  total_executions_30d: number;
  successful_executions_30d: number;
  failed_executions_30d: number;
  success_rate: number;
  recent_workflows: AutomationWorkflow[];
  upcoming_reminders: ScheduledReminder[];
}

export interface CreateWorkflowRequest {
  automation_type: AutomationType;
  name: string;
  description?: string;
  event_reminder_config?: EventReminderConfig;
  conference_id?: string;
}

// ==================== API Functions ====================

async function fetchAutomationDashboard(token: string, organizationId: string): Promise<AutomationDashboard> {
  const response = await axios.get(`${API_BASE_URL}/automation/dashboard`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Organization-ID': encodeHeaderValue(organizationId) || '',
    },
  });
  return response.data;
}

async function fetchWorkflows(
  token: string,
  organizationId: string,
  automationType?: AutomationType,
  status?: AutomationStatus
): Promise<AutomationWorkflow[]> {
  const params = new URLSearchParams();
  if (automationType) params.append('automation_type', automationType);
  if (status) params.append('status', status);

  const response = await axios.get(`${API_BASE_URL}/automation/workflows?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Organization-ID': encodeHeaderValue(organizationId) || '',
    },
  });
  return response.data;
}

async function fetchWorkflow(token: string, organizationId: string, workflowId: string): Promise<AutomationWorkflow> {
  const response = await axios.get(`${API_BASE_URL}/automation/workflows/${workflowId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Organization-ID': encodeHeaderValue(organizationId) || '',
    },
  });
  return response.data;
}

async function createWorkflow(
  token: string,
  organizationId: string,
  data: CreateWorkflowRequest
): Promise<AutomationWorkflow> {
  const response = await axios.post(`${API_BASE_URL}/automation/workflows`, data, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Organization-ID': encodeHeaderValue(organizationId) || '',
    },
  });
  return response.data;
}

async function createDefaultEventReminderWorkflow(
  token: string,
  organizationId: string,
  conferenceId: string
): Promise<AutomationWorkflow> {
  const response = await axios.post(
    `${API_BASE_URL}/automation/workflows/default-event-reminder?conference_id=${conferenceId}`,
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

async function updateWorkflowStatus(
  token: string,
  organizationId: string,
  workflowId: string,
  status: AutomationStatus
): Promise<{ success: boolean; message: string }> {
  const response = await axios.put(
    `${API_BASE_URL}/automation/workflows/${workflowId}/status?status=${status}`,
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

async function deleteWorkflow(token: string, organizationId: string, workflowId: string): Promise<void> {
  await axios.delete(`${API_BASE_URL}/automation/workflows/${workflowId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Organization-ID': encodeHeaderValue(organizationId) || '',
    },
  });
}

async function scheduleReminders(
  token: string,
  organizationId: string,
  workflowId: string,
  conferenceId: string
): Promise<ScheduledReminder[]> {
  const response = await axios.post(
    `${API_BASE_URL}/automation/workflows/${workflowId}/schedule-reminders?conference_id=${conferenceId}`,
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

// ==================== React Query Hooks ====================

export function useAutomationDashboard(
  token: string | null,
  organizationId: string | null
): UseQueryResult<AutomationDashboard, Error> {
  return useQuery({
    queryKey: ['automation-dashboard', organizationId],
    queryFn: () => fetchAutomationDashboard(token!, organizationId!),
    enabled: !!token && !!organizationId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useWorkflows(
  token: string | null,
  organizationId: string | null,
  automationType?: AutomationType,
  status?: AutomationStatus
): UseQueryResult<AutomationWorkflow[], Error> {
  return useQuery({
    queryKey: ['automation-workflows', organizationId, automationType, status],
    queryFn: () => fetchWorkflows(token!, organizationId!, automationType, status),
    enabled: !!token && !!organizationId,
    staleTime: 2 * 60 * 1000,
  });
}

export function useWorkflow(
  token: string | null,
  organizationId: string | null,
  workflowId: string | null
): UseQueryResult<AutomationWorkflow, Error> {
  return useQuery({
    queryKey: ['automation-workflow', organizationId, workflowId],
    queryFn: () => fetchWorkflow(token!, organizationId!, workflowId!),
    enabled: !!token && !!organizationId && !!workflowId,
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateWorkflow(
  token: string | null,
  organizationId: string | null
): UseMutationResult<AutomationWorkflow, Error, CreateWorkflowRequest> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateWorkflowRequest) => createWorkflow(token!, organizationId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automation-workflows'] });
      queryClient.invalidateQueries({ queryKey: ['automation-dashboard'] });
    },
  });
}

export function useCreateDefaultEventReminderWorkflow(
  token: string | null,
  organizationId: string | null
): UseMutationResult<AutomationWorkflow, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conferenceId: string) => createDefaultEventReminderWorkflow(token!, organizationId!, conferenceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automation-workflows'] });
      queryClient.invalidateQueries({ queryKey: ['automation-dashboard'] });
    },
  });
}

export function useUpdateWorkflowStatus(
  token: string | null,
  organizationId: string | null
): UseMutationResult<{ success: boolean; message: string }, Error, { workflowId: string; status: AutomationStatus }> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workflowId, status }) => updateWorkflowStatus(token!, organizationId!, workflowId, status),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['automation-workflows'] });
      queryClient.invalidateQueries({ queryKey: ['automation-workflow', organizationId, variables.workflowId] });
      queryClient.invalidateQueries({ queryKey: ['automation-dashboard'] });
    },
  });
}

export function useDeleteWorkflow(
  token: string | null,
  organizationId: string | null
): UseMutationResult<void, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workflowId: string) => deleteWorkflow(token!, organizationId!, workflowId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automation-workflows'] });
      queryClient.invalidateQueries({ queryKey: ['automation-dashboard'] });
    },
  });
}

export function useScheduleReminders(
  token: string | null,
  organizationId: string | null
): UseMutationResult<ScheduledReminder[], Error, { workflowId: string; conferenceId: string }> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workflowId, conferenceId }) => scheduleReminders(token!, organizationId!, workflowId, conferenceId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['automation-workflow', organizationId, variables.workflowId] });
      queryClient.invalidateQueries({ queryKey: ['automation-dashboard'] });
    },
  });
}
