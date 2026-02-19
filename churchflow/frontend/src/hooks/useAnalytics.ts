/**
 * Analytics Hook for ChurchFlow - Phase 7
 *
 * Provides hooks for fetching analytics data:
 * - Dashboard metrics
 * - Conference analytics
 * - Member engagement metrics
 * - Communication metrics
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import axios from 'axios';
import { encodeHeaderValue } from '../lib/header-utils';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://churchflow-api.ailabsafrica.com/api/v1';

// ============================================
// Types (matching backend Pydantic models)
// ============================================

export type MetricPeriod = '7d' | '30d' | '90d' | '1y' | 'custom';

export type EngagementLevel = 'very_high' | 'high' | 'medium' | 'low' | 'very_low';

export interface ConferenceAnalytics {
  conference_id: string;
  conference_name: string;
  organization_id: string;
  total_registrations: number;
  registrations_by_day: Array<{ date: string; count: number }>;
  peak_registration_day: string | null;
  peak_registration_count: number | null;
  total_check_ins: number;
  check_in_rate: number;
  session_check_ins: Record<string, number>;
  branch_distribution: Record<string, number>;
  top_branches: Array<{ name: string; count: number }>;
  bus_usage_rate: number;
  bus_route_distribution: Record<string, number>;
  other_churches_count: number;
  other_churches_percentage: number;
  avg_registration_days_before: number | null;
  last_minute_registrations: number;
  calculated_at: string;
}

export interface MemberEngagementMetrics {
  organization_id: string;
  period: MetricPeriod;
  period_start: string;
  period_end: string;
  total_members: number;
  active_members: number;
  inactive_members: number;
  new_members: number;
  engagement_score: number;
  engagement_level: EngagementLevel;
  avg_events_per_member: number;
  repeat_attendee_rate: number;
  top_engaged_members: Array<{
    email: string;
    name: string;
    event_count: number;
  }>;
  engagement_trends: Array<{ date: string; score: number }>;
  member_retention_rate: number;
  calculated_at: string;
}

export interface CommunicationMetrics {
  organization_id: string;
  period_start: string;
  period_end: string;
  sms_sent: number;
  sms_delivered: number;
  sms_failed: number;
  sms_delivery_rate: number;
  sms_cost_total: number;
  sms_cost_per_message: number;
  email_sent: number;
  email_delivered: number;
  email_opened: number;
  email_clicked: number;
  email_open_rate: number;
  email_click_rate: number;
  campaigns_sent: number;
  avg_campaign_size: number;
  most_effective_campaign: {
    id: string;
    name: string;
    open_rate: number;
  } | null;
  total_communication_cost: number;
  cost_per_attendee: number | null;
  calculated_at: string;
}

export interface ChurchDashboardMetrics {
  organization_id: string;
  organization_name: string;
  period: MetricPeriod;
  period_start: string;
  period_end: string;
  total_events: number;
  total_attendees: number;
  avg_attendance_per_event: number;
  upcoming_events: number;
  sms_sent: number;
  sms_delivery_rate: number;
  email_sent: number;
  email_open_rate: number;
  new_members: number;
  returning_members: number;
  member_retention_rate: number;
  engagement_score: number;
  total_giving?: number;
  avg_giving_per_member?: number;
  giving_growth_rate?: number;
  attendance_trend: number;
  engagement_trend: number;
  giving_trend?: number;
  communication_trend: number;
  insights: Array<{
    type: 'positive' | 'warning' | 'info';
    title: string;
    message: string;
    priority: 'high' | 'medium' | 'low';
  }>;
  alerts: Array<{
    severity: 'critical' | 'warning' | 'info';
    title: string;
    message: string;
    action: string;
  }>;
  previous_period_comparison?: Record<string, any>;
  calculated_at: string;
}

// ============================================
// API Functions
// ============================================

async function fetchDashboardMetrics(
  token: string,
  organizationId: string,
  period: MetricPeriod = '30d'
): Promise<ChurchDashboardMetrics> {
  const response = await axios.get(`${API_BASE_URL}/church-analytics/dashboard`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Organization-ID': encodeHeaderValue(organizationId) || '',
    },
    params: { period },
  });
  return response.data;
}

async function fetchConferenceAnalytics(
  token: string,
  organizationId: string,
  conferenceId: string
): Promise<ConferenceAnalytics> {
  const response = await axios.get(
    `${API_BASE_URL}/church-analytics/conference/${conferenceId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );
  return response.data;
}

async function fetchMemberEngagement(
  token: string,
  organizationId: string,
  period: MetricPeriod = '30d',
  startDate?: string,
  endDate?: string
): Promise<MemberEngagementMetrics> {
  const response = await axios.get(`${API_BASE_URL}/church-analytics/engagement`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Organization-ID': encodeHeaderValue(organizationId) || '',
    },
    params: {
      period,
      start_date: startDate,
      end_date: endDate,
    },
  });
  return response.data;
}

async function fetchCommunicationMetrics(
  token: string,
  organizationId: string,
  startDate: string,
  endDate: string
): Promise<CommunicationMetrics> {
  const response = await axios.get(`${API_BASE_URL}/church-analytics/communication`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Organization-ID': encodeHeaderValue(organizationId) || '',
    },
    params: {
      start_date: startDate,
      end_date: endDate,
    },
  });
  return response.data;
}

// ============================================
// React Query Hooks
// ============================================

/**
 * Hook to fetch dashboard metrics
 *
 * @param token - Auth token
 * @param organizationId - Organization ID
 * @param period - Time period (7d, 30d, 90d, 1y)
 * @returns Query result with dashboard metrics
 */
export function useDashboardMetrics(
  token: string | null,
  organizationId: string | null,
  period: MetricPeriod = '30d'
): UseQueryResult<ChurchDashboardMetrics, Error> {
  return useQuery({
    queryKey: ['dashboard-metrics', organizationId, period],
    queryFn: () => fetchDashboardMetrics(token!, organizationId!, period),
    enabled: !!token && !!organizationId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook to fetch conference analytics
 *
 * @param token - Auth token
 * @param organizationId - Organization ID
 * @param conferenceId - Conference ID
 * @returns Query result with conference analytics
 */
export function useConferenceAnalytics(
  token: string | null,
  organizationId: string | null,
  conferenceId: string | null
): UseQueryResult<ConferenceAnalytics, Error> {
  return useQuery({
    queryKey: ['conference-analytics', conferenceId],
    queryFn: () => fetchConferenceAnalytics(token!, organizationId!, conferenceId!),
    enabled: !!token && !!organizationId && !!conferenceId,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook to fetch member engagement metrics
 *
 * @param token - Auth token
 * @param organizationId - Organization ID
 * @param period - Time period
 * @param startDate - Custom start date (for custom period)
 * @param endDate - Custom end date (for custom period)
 * @returns Query result with engagement metrics
 */
export function useMemberEngagement(
  token: string | null,
  organizationId: string | null,
  period: MetricPeriod = '30d',
  startDate?: string,
  endDate?: string
): UseQueryResult<MemberEngagementMetrics, Error> {
  return useQuery({
    queryKey: ['member-engagement', organizationId, period, startDate, endDate],
    queryFn: () => fetchMemberEngagement(token!, organizationId!, period, startDate, endDate),
    enabled: !!token && !!organizationId,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook to fetch communication metrics
 *
 * @param token - Auth token
 * @param organizationId - Organization ID
 * @param startDate - Period start date (ISO format)
 * @param endDate - Period end date (ISO format)
 * @returns Query result with communication metrics
 */
export function useCommunicationMetrics(
  token: string | null,
  organizationId: string | null,
  startDate: string | null,
  endDate: string | null
): UseQueryResult<CommunicationMetrics, Error> {
  return useQuery({
    queryKey: ['communication-metrics', organizationId, startDate, endDate],
    queryFn: () => fetchCommunicationMetrics(token!, organizationId!, startDate!, endDate!),
    enabled: !!token && !!organizationId && !!startDate && !!endDate,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}
