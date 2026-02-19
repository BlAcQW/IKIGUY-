/**
 * React Query hooks for Member Portal functionality
 */

import { useQuery, useMutation, useQueryClient, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { encodeHeaderValue } from '../lib/header-utils';

// ==================== Types ====================

export interface MemberProfile {
  _id: string;
  supabase_id: string;
  email?: string;
  phone?: string;
  full_name?: string;
  name?: string;
  date_of_birth?: string;
  gender?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  occupation?: string;
  employer?: string;
  marital_status?: string;
  spouse_name?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  branch_id?: string;
  member_status?: string;
  roles: string[];
  volunteer_roles: string[];
  profile_picture_url?: string;
  bio?: string;
  joined_at?: string;
  created_at: string;
  updated_at: string;
}

export interface UpdateProfileRequest {
  full_name?: string;
  email?: string;
  phone?: string;
  date_of_birth?: string;
  gender?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  occupation?: string;
  employer?: string;
  marital_status?: string;
  spouse_name?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  bio?: string;
  profile_picture_url?: string;
}

export interface NotificationPreferences {
  email_notifications: boolean;
  sms_notifications: boolean;
  push_notifications: boolean;
  event_reminders: boolean;
  giving_receipts: boolean;
  newsletter: boolean;
  prayer_requests: boolean;
}

export interface PrivacyPreferences {
  show_profile_in_directory: boolean;
  show_phone_number: boolean;
  show_email: boolean;
  show_address: boolean;
  allow_contact_from_members: boolean;
}

export interface MemberPreferences {
  user_id: string;
  notifications: NotificationPreferences;
  privacy: PrivacyPreferences;
  language: string;
  timezone: string;
  updated_at: string;
}

export interface UpdatePreferencesRequest {
  notifications?: NotificationPreferences;
  privacy?: PrivacyPreferences;
  language?: string;
  timezone?: string;
}

export interface MemberActivity {
  conferences_attended: number;
  events_registered: number;
  donations_made: number;
  volunteer_hours: number;
  cell_group?: string;
  last_attendance?: string;
  last_donation?: string;
  member_since?: string;
}

export interface MemberDashboard {
  profile: MemberProfile;
  activity: MemberActivity;
  upcoming_conferences: any[];
  recent_donations: any[];
  notification_count: number;
  unread_messages: number;
}

export interface MemberDirectoryEntry {
  _id: string;
  full_name: string;
  profile_picture_url?: string;
  email?: string;
  phone?: string;
  cell_group?: string;
  roles: string[];
  volunteer_roles: string[];
  joined_at?: string;
}

export interface MyRegistrations {
  upcoming: any[];
  past: any[];
  total_registered: number;
  total_attended: number;
  attendance_rate: number;
}

// ==================== API Functions ====================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:30030';

async function fetchMyProfile(token: string): Promise<MemberProfile> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/member-portal/profile/me`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch profile');
  }

  return response.json();
}

async function updateMyProfile(
  token: string,
  profileData: UpdateProfileRequest
): Promise<MemberProfile> {
  const response = await fetch(`${API_BASE_URL}/api/v1/member-portal/profile/me`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(profileData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update profile');
  }

  return response.json();
}

async function fetchMyPreferences(token: string): Promise<MemberPreferences> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/member-portal/preferences`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch preferences');
  }

  return response.json();
}

async function updateMyPreferences(
  token: string,
  preferences: UpdatePreferencesRequest
): Promise<MemberPreferences> {
  const response = await fetch(`${API_BASE_URL}/api/v1/member-portal/preferences`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(preferences),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update preferences');
  }

  return response.json();
}

async function fetchMyActivity(token: string): Promise<MemberActivity> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/member-portal/activity/me`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch activity');
  }

  return response.json();
}

async function fetchMemberDashboard(
  token: string,
  organizationId: string
): Promise<MemberDashboard> {
  // Base64 encode organization ID to handle special characters in HTTP headers
  const encodedOrgId = encodeHeaderValue(organizationId);
  if (!encodedOrgId) {
    throw new Error('Invalid organization ID');
  }
  
  const response = await fetch(
    `${API_BASE_URL}/api/v1/member-portal/dashboard`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': encodedOrgId,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch dashboard');
  }

  return response.json();
}

async function fetchMemberDirectory(
  token: string,
  organizationId: string,
  page: number = 1,
  search?: string
): Promise<{ members: MemberDirectoryEntry[]; total: number }> {
  const params = new URLSearchParams({ page: page.toString() });
  if (search) params.append('search', search);

  // Base64 encode organization ID to handle special characters in HTTP headers
  const encodedOrgId = encodeHeaderValue(organizationId);
  if (!encodedOrgId) {
    throw new Error('Invalid organization ID');
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/member-portal/directory?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': encodedOrgId,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch member directory');
  }

  return response.json();
}

async function fetchMyRegistrations(token: string): Promise<MyRegistrations> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/member-portal/registrations/my`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch registrations');
  }

  return response.json();
}

// ==================== React Query Hooks ====================

export function useMyProfile(token: string | null): UseQueryResult<MemberProfile, Error> {
  return useQuery({
    queryKey: ['my-profile'],
    queryFn: () => fetchMyProfile(token!),
    enabled: !!token,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useUpdateMyProfile(
  token: string | null
): UseMutationResult<MemberProfile, Error, UpdateProfileRequest> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (profileData: UpdateProfileRequest) =>
      updateMyProfile(token!, profileData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-profile'] });
      queryClient.invalidateQueries({ queryKey: ['member-dashboard'] });
    },
  });
}

export function useMyPreferences(token: string | null): UseQueryResult<MemberPreferences, Error> {
  return useQuery({
    queryKey: ['my-preferences'],
    queryFn: () => fetchMyPreferences(token!),
    enabled: !!token,
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdateMyPreferences(
  token: string | null
): UseMutationResult<MemberPreferences, Error, UpdatePreferencesRequest> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (preferences: UpdatePreferencesRequest) =>
      updateMyPreferences(token!, preferences),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-preferences'] });
    },
  });
}

export function useMyActivity(token: string | null): UseQueryResult<MemberActivity, Error> {
  return useQuery({
    queryKey: ['my-activity'],
    queryFn: () => fetchMyActivity(token!),
    enabled: !!token,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useMemberDashboard(
  token: string | null,
  organizationId: string | null
): UseQueryResult<MemberDashboard, Error> {
  return useQuery({
    queryKey: ['member-dashboard', organizationId],
    queryFn: () => fetchMemberDashboard(token!, organizationId!),
    enabled: !!token && !!organizationId,
    staleTime: 2 * 60 * 1000,
  });
}

export function useMemberDirectory(
  token: string | null,
  organizationId: string | null,
  page: number = 1,
  search?: string
): UseQueryResult<{ members: MemberDirectoryEntry[]; total: number }, Error> {
  return useQuery({
    queryKey: ['member-directory', organizationId, page, search],
    queryFn: () => fetchMemberDirectory(token!, organizationId!, page, search),
    enabled: !!token && !!organizationId,
    staleTime: 30 * 1000, // 30 seconds cache
  });
}

export function useMyRegistrations(token: string | null): UseQueryResult<MyRegistrations, Error> {
  return useQuery({
    queryKey: ['my-registrations'],
    queryFn: () => fetchMyRegistrations(token!),
    enabled: !!token,
    staleTime: 2 * 60 * 1000,
  });
}
