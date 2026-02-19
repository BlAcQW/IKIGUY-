/**
 * React Query hooks for Online Giving functionality
 */

import { useQuery, useMutation, useQueryClient, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { encodeHeaderValue } from '../lib/header-utils';

// ==================== Types ====================

export interface Donation {
  _id: string;
  organization_id: string;
  donor_id?: string;
  donor_name: string;
  donor_email?: string;
  donor_phone?: string;
  amount: number;
  currency: string;
  donation_type: string;
  category: string;
  payment_method: string;
  status: string;
  is_anonymous: boolean;
  is_recurring: boolean;
  receipt_sent: boolean;
  receipt_url?: string;
  tax_deductible: boolean;
  created_at: string;
  completed_at?: string;
}

export interface RecurringDonation {
  _id: string;
  organization_id: string;
  donor_id: string;
  donor_name: string;
  amount: number;
  currency: string;
  frequency: string;
  donation_type: string;
  category: string;
  status: string;
  is_active: boolean;
  next_payment_date?: string;
  total_donations: number;
  total_amount: number;
  created_at: string;
}

export interface DonorProfile {
  _id: string;
  organization_id: string;
  user_id: string;
  donor_name: string;
  donor_email?: string;
  donor_phone?: string;
  total_donated: number;
  currency: string;
  donation_count: number;
  first_donation_date?: string;
  last_donation_date?: string;
  average_donation: number;
  largest_donation: number;
  is_recurring_donor: boolean;
  active_recurring_count: number;
  active_pledge_count: number;
  created_at: string;
}

export interface GivingAnalytics {
  organization_id: string;
  period_start: string;
  period_end: string;
  total_donations: number;
  total_amount: number;
  currency: string;
  average_donation: number;
  unique_donors: number;
  new_donors: number;
  recurring_donors: number;
  donation_types: Record<string, number>;
  top_categories: Array<{ category: string; amount: number }>;
  monthly_trend: Array<{ month: string; amount: number }>;
  donor_retention_rate: number;
}

export interface CreateDonationRequest {
  donor_name: string;
  donor_email?: string;
  donor_phone?: string;
  amount: number;
  currency?: string;
  donation_type: string;
  category: string;
  payment_method: string;
  is_anonymous?: boolean;
  notes?: string;
}

export interface ProcessDonationRequest {
  donation_id: string;
  stripe_payment_method_id: string;
}

export interface CreateRecurringDonationRequest {
  amount: number;
  currency?: string;
  frequency: string;
  donation_type: string;
  category: string;
  payment_method: string;
  stripe_payment_method_id: string;
}

// ==================== API Functions ====================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:30030';

async function fetchDonations(
  token: string,
  organizationId: string,
  page: number = 1,
  pageSize: number = 50
): Promise<{ donations: Donation[]; total: number }> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/giving/donations?page=${page}&page_size=${pageSize}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch donations');
  }

  return response.json();
}

async function fetchMyDonationHistory(
  token: string,
  organizationId: string,
  page: number = 1
): Promise<{ donations: Donation[]; total: number }> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/giving/donations/my/history?page=${page}&page_size=50`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch donation history');
  }

  return response.json();
}

async function createDonation(
  token: string | null,
  organizationId: string | null,
  donationData: CreateDonationRequest
): Promise<Donation> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // Add auth header only if token exists (public donations don't require auth)
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Add organization ID if provided (encode for HTTP header safety)
  if (organizationId) {
    const encoded = encodeHeaderValue(organizationId);
    if (encoded) {
      headers['X-Organization-ID'] = encoded;
    }
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/giving/donations`, {
    method: 'POST',
    headers,
    body: JSON.stringify(donationData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create donation');
  }

  return response.json();
}

async function processDonationPayment(
  token: string | null,
  organizationId: string | null,
  paymentData: ProcessDonationRequest
): Promise<Donation> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // Add auth header only if token exists (public donations don't require auth)
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Add organization ID if provided (encode for HTTP header safety)
  if (organizationId) {
    const encoded = encodeHeaderValue(organizationId);
    if (encoded) {
      headers['X-Organization-ID'] = encoded;
    }
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/giving/donations/process`, {
    method: 'POST',
    headers,
    body: JSON.stringify(paymentData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Payment processing failed');
  }

  return response.json();
}

async function fetchMyRecurringDonations(
  token: string,
  organizationId: string
): Promise<{ recurring_donations: RecurringDonation[] }> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/giving/recurring-donations/my/active`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch recurring donations');
  }

  return response.json();
}

async function createRecurringDonation(
  token: string,
  organizationId: string,
  recurringData: CreateRecurringDonationRequest
): Promise<RecurringDonation> {
  const response = await fetch(`${API_BASE_URL}/api/v1/giving/recurring-donations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Organization-ID': organizationId,
    },
    body: JSON.stringify(recurringData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create recurring donation');
  }

  return response.json();
}

async function cancelRecurringDonation(
  token: string,
  organizationId: string,
  recurringId: string
): Promise<RecurringDonation> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/giving/recurring-donations/${recurringId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to cancel recurring donation');
  }

  return response.json();
}

async function fetchDonorProfile(
  token: string,
  organizationId: string
): Promise<DonorProfile> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/giving/donor-profile/me`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch donor profile');
  }

  return response.json();
}

async function fetchGivingAnalytics(
  token: string,
  organizationId: string,
  period: string = '30d'
): Promise<GivingAnalytics> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/giving/analytics?period=${period}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': encodeHeaderValue(organizationId) || '',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch giving analytics');
  }

  return response.json();
}

// ==================== React Query Hooks ====================

export function useMyDonationHistory(
  token: string | null,
  organizationId: string | null,
  page: number = 1
): UseQueryResult<{ donations: Donation[]; total: number }, Error> {
  return useQuery({
    queryKey: ['my-donation-history', organizationId, page],
    queryFn: () => fetchMyDonationHistory(token!, organizationId!, page),
    enabled: !!token && !!organizationId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useCreateDonation(
  token: string | null,
  organizationId: string | null
): UseMutationResult<Donation, Error, CreateDonationRequest> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (donationData: CreateDonationRequest) =>
      createDonation(token!, organizationId!, donationData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-donation-history'] });
      queryClient.invalidateQueries({ queryKey: ['donor-profile'] });
    },
  });
}

export function useProcessDonation(
  token: string | null,
  organizationId: string | null
): UseMutationResult<Donation, Error, ProcessDonationRequest> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (paymentData: ProcessDonationRequest) =>
      processDonationPayment(token, organizationId, paymentData),
    onSuccess: () => {
      // Only invalidate queries if authenticated
      if (token && organizationId) {
        queryClient.invalidateQueries({ queryKey: ['my-donation-history'] });
        queryClient.invalidateQueries({ queryKey: ['donor-profile'] });
      }
    },
  });
}

export function useMyRecurringDonations(
  token: string | null,
  organizationId: string | null
): UseQueryResult<{ recurring_donations: RecurringDonation[] }, Error> {
  return useQuery({
    queryKey: ['my-recurring-donations', organizationId],
    queryFn: () => fetchMyRecurringDonations(token!, organizationId!),
    enabled: !!token && !!organizationId,
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateRecurringDonation(
  token: string | null,
  organizationId: string | null
): UseMutationResult<RecurringDonation, Error, CreateRecurringDonationRequest> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (recurringData: CreateRecurringDonationRequest) =>
      createRecurringDonation(token!, organizationId!, recurringData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-recurring-donations'] });
      queryClient.invalidateQueries({ queryKey: ['donor-profile'] });
    },
  });
}

export function useCancelRecurringDonation(
  token: string | null,
  organizationId: string | null
): UseMutationResult<RecurringDonation, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (recurringId: string) =>
      cancelRecurringDonation(token!, organizationId!, recurringId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-recurring-donations'] });
      queryClient.invalidateQueries({ queryKey: ['donor-profile'] });
    },
  });
}

export function useDonorProfile(
  token: string | null,
  organizationId: string | null
): UseQueryResult<DonorProfile, Error> {
  return useQuery({
    queryKey: ['donor-profile', organizationId],
    queryFn: () => fetchDonorProfile(token!, organizationId!),
    enabled: !!token && !!organizationId,
    staleTime: 2 * 60 * 1000,
  });
}

export function useGivingAnalytics(
  token: string | null,
  organizationId: string | null,
  period: string = '30d'
): UseQueryResult<GivingAnalytics, Error> {
  return useQuery({
    queryKey: ['giving-analytics', organizationId, period],
    queryFn: () => fetchGivingAnalytics(token!, organizationId!, period),
    enabled: !!token && !!organizationId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
