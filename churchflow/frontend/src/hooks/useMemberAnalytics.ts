/**
 * React Query hooks for Member Analytics
 *
 * Provides data fetching hooks for member statistics dashboard
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { encodeHeaderValue } from '../lib/header-utils';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:30030';

/**
 * Age distribution data structure
 */
export interface AgeDistribution {
  age_0_18: number;
  age_19_25: number;
  age_26_35: number;
  age_36_50: number;
  age_51_65: number;
  age_65_plus: number;
  unknown: number;
}

/**
 * Gender distribution data structure
 */
export interface GenderDistribution {
  male: number;
  female: number;
  other: number;
  prefer_not_to_say: number;
  unknown: number;
}

/**
 * Member dashboard metrics response structure
 */
export interface MemberDashboardMetrics {
  organization_id: string;
  period: string;
  period_start: string;
  period_end: string;

  // Total counts
  total_members: number;
  active_members: number;
  inactive_members: number;
  visitors: number;
  alumni: number;

  // Growth metrics
  new_members_count: number;
  growth_rate: number;
  member_trend: Array<{
    date: string;
    count: number;
  }>;

  // Demographics
  gender_distribution: GenderDistribution;
  age_distribution: AgeDistribution;
  marital_status_distribution: Record<string, number>;

  // Activity & Engagement
  visit_frequency: Record<string, number>;
  average_visit_count: number;
  first_timers: number;
  returning_visitors: number;

  // Financial metrics
  total_donations: number;
  total_donors: number;
  average_donation: number;
  donor_percentage: number;

  // Branch distribution
  branch_distribution: Array<{
    branch_id: string;
    branch_name: string;
    member_count: number;
  }>;

  // Spiritual journey
  spiritual_stages: Record<string, number>;

  calculated_at: string;
}

/**
 * Fetch member dashboard metrics from API
 */
async function fetchMemberDashboardMetrics(
  token: string,
  organizationId: string,
  period: string = '30d',
  branchId?: string | null
): Promise<MemberDashboardMetrics> {
  const params = new URLSearchParams({
    period,
    ...(branchId && { branch_id: branchId })
  });

  const response = await fetch(
    `${API_BASE_URL}/api/v1/member-analytics/dashboard?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Hook for fetching member dashboard metrics
 *
 * @param token - Authentication token
 * @param organizationId - Organization ID
 * @param period - Time period (7d, 30d, 90d, 1y)
 * @param branchId - Optional branch filter
 * @returns Query result with member metrics
 */
export function useMemberDashboardMetrics(
  token: string | null,
  organizationId: string | null,
  period: string = '30d',
  branchId?: string | null
): UseQueryResult<MemberDashboardMetrics, Error> {
  return useQuery({
    queryKey: ['member-dashboard-metrics', organizationId, period, branchId],
    queryFn: () => {
      if (!token || !organizationId) {
        throw new Error('Token and organization ID are required');
      }
      return fetchMemberDashboardMetrics(token, organizationId, period, branchId);
    },
    enabled: !!token && !!organizationId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    retry: 1,
  });
}

/**
 * Format number as currency
 */
export function formatCurrency(amount: number, currency: string = 'GHS'): string {
  return new Intl.NumberFormat('en-GH', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format number with thousand separators
 */
export function formatNumber(num: number): string {
  return new Intl.NumberFormat('en-US').format(num);
}

/**
 * Format percentage with sign
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  const formatted = value.toFixed(decimals);
  return value > 0 ? `+${formatted}%` : `${formatted}%`;
}
