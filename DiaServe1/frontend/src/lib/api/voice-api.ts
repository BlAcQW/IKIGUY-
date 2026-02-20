/**
 * Voice Agent API Client
 *
 * Handles voice call management, configuration, and statistics.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { API_BASE_URL } from '@/lib/api-config';
import { getAuthTokenSync } from '@/lib/auth';

// ==================== Types ====================

export type CallStatus = 'queued' | 'ringing' | 'in_progress' | 'completed' | 'failed' | 'no_answer' | 'busy' | 'cancelled';
export type CallDirection = 'inbound' | 'outbound';
export type CallOutcome = 'tour_scheduled' | 'information_provided' | 'transferred' | 'callback_requested' | 'voicemail' | 'no_outcome';

export interface VoiceCall {
  id: string;
  organization_id: string;
  caller_name: string;
  caller_phone: string;
  direction: CallDirection;
  status: CallStatus;
  outcome: CallOutcome;
  duration_seconds: number;
  property_id?: string;
  property_name?: string;
  transcript?: string;
  created_at: string;
  ended_at?: string;
}

export interface VoiceConfig {
  organization_id: string;
  is_active: boolean;
  assistant_id?: string;
  phone_number?: string;
  greeting_message: string;
  transfer_phone?: string;
  working_hours_start: string;
  working_hours_end: string;
  after_hours_message: string;
}

export interface VoiceConfigUpdate {
  is_active?: boolean;
  assistant_id?: string;
  phone_number?: string;
  greeting_message?: string;
  transfer_phone?: string;
  working_hours_start?: string;
  working_hours_end?: string;
  after_hours_message?: string;
}

export interface CallStats {
  total_calls: number;
  calls_today: number;
  avg_duration_seconds: number;
  tours_scheduled: number;
  satisfaction_rate: number;
  calls_by_outcome: Record<string, number>;
  calls_by_status: Record<string, number>;
}

export interface CallListResponse {
  calls: VoiceCall[];
  total: number;
  limit: number;
  offset: number;
}

// ==================== Helpers ====================

function buildHeaders(): HeadersInit {
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  const token = getAuthTokenSync();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const orgId = localStorage.getItem('selectedOrganizationId');
  if (orgId) headers['X-Organization-ID'] = orgId;
  return headers;
}

// ==================== API Functions ====================

export async function fetchCalls(params?: { limit?: number; offset?: number; status?: string }): Promise<CallListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());
  if (params?.status) searchParams.set('status', params.status);

  const response = await fetch(`${API_BASE_URL}/api/v1/voice/calls?${searchParams}`, { headers: buildHeaders() });
  if (!response.ok) throw new Error('Failed to fetch calls');
  return response.json();
}

export async function fetchCallStats(): Promise<CallStats> {
  const response = await fetch(`${API_BASE_URL}/api/v1/voice/stats`, { headers: buildHeaders() });
  if (!response.ok) throw new Error('Failed to fetch call stats');
  return response.json();
}

export async function fetchVoiceConfig(): Promise<VoiceConfig> {
  const response = await fetch(`${API_BASE_URL}/api/v1/voice/config`, { headers: buildHeaders() });
  if (!response.ok) throw new Error('Failed to fetch voice config');
  return response.json();
}

export async function updateVoiceConfig(data: VoiceConfigUpdate): Promise<VoiceConfig> {
  const response = await fetch(`${API_BASE_URL}/api/v1/voice/config`, {
    method: 'PUT',
    headers: buildHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to update voice config');
  return response.json();
}

// ==================== React Query Hooks ====================

export function useVoiceCalls(params?: { limit?: number; offset?: number; status?: string }) {
  return useQuery({
    queryKey: ['voice-calls', params],
    queryFn: () => fetchCalls(params),
    staleTime: 30000,
  });
}

export function useCallStats() {
  return useQuery({
    queryKey: ['voice-stats'],
    queryFn: fetchCallStats,
    staleTime: 30000,
  });
}

export function useVoiceConfig() {
  return useQuery({
    queryKey: ['voice-config'],
    queryFn: fetchVoiceConfig,
    staleTime: 60000,
  });
}

export function useUpdateVoiceConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateVoiceConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['voice-config'] });
    },
  });
}

// ==================== Formatting Helpers ====================

export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
}

export function getOutcomeLabel(outcome: CallOutcome): string {
  const labels: Record<CallOutcome, string> = {
    tour_scheduled: 'Tour Scheduled',
    information_provided: 'Information Provided',
    transferred: 'Transferred to Agent',
    callback_requested: 'Callback Requested',
    voicemail: 'Voicemail',
    no_outcome: 'No Outcome',
  };
  return labels[outcome] || outcome;
}
