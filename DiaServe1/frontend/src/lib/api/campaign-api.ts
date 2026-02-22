/**
 * Campaign API Client
 *
 * Handles all campaign-related API calls including contacts, campaigns,
 * and segment management.
 */

import { API_BASE_URL, getSelectedOrganizationId } from '@/lib/api-config';
import { getAuthTokenSync } from '../auth';

// ==================== Types ====================

export type CampaignType = 'sms' | 'whatsapp' | 'email' | 'voice';
export type CampaignStatus = 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'cancelled' | 'failed';
export type InterestStatus = 'hot' | 'warm' | 'cold' | 'unqualified';
export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'negotiating' | 'converted' | 'lost';

export interface Contact {
  id: string;
  organization_id: string;
  name: string;
  email?: string;
  phone?: string;
  property_type_preferences: string[];
  location_preferences: string[];
  budget_min?: number;
  budget_max?: number;
  bedrooms_min?: number;
  bedrooms_max?: number;
  interest_status: InterestStatus;
  lead_status: LeadStatus;
  tags: string[];
  source?: string;
  opt_out_channels: string[];
  notes?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  last_contacted?: string;
}

export interface ContactCreate {
  name: string;
  email?: string;
  phone?: string;
  property_type_preferences?: string[];
  location_preferences?: string[];
  budget_min?: number;
  budget_max?: number;
  bedrooms_min?: number;
  bedrooms_max?: number;
  interest_status?: InterestStatus;
  lead_status?: LeadStatus;
  tags?: string[];
  source?: string;
  notes?: string;
}

export interface ContactUpdate {
  name?: string;
  email?: string;
  phone?: string;
  property_type_preferences?: string[];
  location_preferences?: string[];
  budget_min?: number;
  budget_max?: number;
  bedrooms_min?: number;
  bedrooms_max?: number;
  interest_status?: InterestStatus;
  lead_status?: LeadStatus;
  tags?: string[];
  source?: string;
  notes?: string;
  opt_out_channels?: string[];
}

export interface SegmentFilter {
  property_types?: string[];
  locations?: string[];
  budget_min?: number;
  budget_max?: number;
  bedrooms_min?: number;
  bedrooms_max?: number;
  interest_statuses?: InterestStatus[];
  lead_statuses?: LeadStatus[];
  tags?: string[];
  exclude_opted_out?: boolean;
}

export interface MessageTemplate {
  tts_text?: string;
  voice_provider?: string;
  voice_id?: string;
  text_content?: string;
  subject?: string;
  html_content?: string;
  variables?: Record<string, string>;
}

export interface Campaign {
  id: string;
  organization_id: string;
  user_id: string;
  name: string;
  campaign_type: CampaignType;
  status: CampaignStatus;
  message_template: MessageTemplate;
  segment_filter?: SegmentFilter;
  target_count: number;
  sent_count: number;
  delivered_count: number;
  opened_count: number;
  clicked_count: number;
  failed_count: number;
  total_cost: number;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  external_campaign_id?: string;
}

export interface CampaignCreate {
  name: string;
  campaign_type: CampaignType;
  message_template: MessageTemplate;
  segment_filter?: SegmentFilter;
  schedule_config?: {
    scheduled_time?: string;
    time_zone?: string;
  };
}

export interface CampaignAnalytics {
  campaign_id: string;
  status: CampaignStatus;
  target_count: number;
  sent_count: number;
  delivered_count: number;
  opened_count: number;
  clicked_count: number;
  failed_count: number;
  total_cost: number;
  delivery_rate: number;
  failure_rate: number;
  message_stats: Record<string, number>;
  started_at?: string;
  completed_at?: string;
}

export interface SegmentPreview {
  contact_count: number;
  sample_contacts: Contact[];
  estimated_cost: number;
}

// ==================== Helper Functions ====================


function buildHeaders(): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const token = getAuthTokenSync();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const orgId = getSelectedOrganizationId();
  if (orgId) {
    headers['X-Organization-ID'] = orgId;
  }

  return headers;
}

// ==================== Contact API ====================

export async function createContact(data: ContactCreate): Promise<Contact> {
  const response = await fetch(`${API_BASE_URL}/api/v1/campaigns/contacts`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create contact');
  }

  return response.json();
}

export async function getContacts(params?: {
  limit?: number;
  offset?: number;
  search?: string;
}): Promise<{ contacts: Contact[]; total: number; limit: number; offset: number }> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());
  if (params?.search) searchParams.set('search', params.search);

  const response = await fetch(
    `${API_BASE_URL}/api/v1/campaigns/contacts?${searchParams}`,
    { headers: buildHeaders() }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch contacts');
  }

  return response.json();
}

export async function getContact(id: string): Promise<Contact> {
  const response = await fetch(`${API_BASE_URL}/api/v1/campaigns/contacts/${id}`, {
    headers: buildHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch contact');
  }

  return response.json();
}

export async function updateContact(id: string, data: ContactUpdate): Promise<Contact> {
  const response = await fetch(`${API_BASE_URL}/api/v1/campaigns/contacts/${id}`, {
    method: 'PUT',
    headers: buildHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update contact');
  }

  return response.json();
}

export async function deleteContact(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/campaigns/contacts/${id}`, {
    method: 'DELETE',
    headers: buildHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to delete contact');
  }
}

export async function importContacts(file: File): Promise<{ imported: number; total_rows: number }> {
  const formData = new FormData();
  formData.append('file', file);

  const headers = buildHeaders();
  delete (headers as Record<string, string>)['Content-Type']; // Let browser set it for FormData

  const response = await fetch(`${API_BASE_URL}/api/v1/campaigns/contacts/import`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to import contacts');
  }

  return response.json();
}

// ==================== Campaign API ====================

export async function createCampaign(data: CampaignCreate): Promise<Campaign> {
  const response = await fetch(`${API_BASE_URL}/api/v1/campaigns`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create campaign');
  }

  return response.json();
}

export async function getCampaigns(params?: {
  campaign_type?: CampaignType;
  status?: CampaignStatus;
  limit?: number;
  offset?: number;
}): Promise<{ campaigns: Campaign[]; total: number; limit: number; offset: number }> {
  const searchParams = new URLSearchParams();
  if (params?.campaign_type) searchParams.set('campaign_type', params.campaign_type);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());

  const response = await fetch(
    `${API_BASE_URL}/api/v1/campaigns?${searchParams}`,
    { headers: buildHeaders() }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch campaigns');
  }

  return response.json();
}

export async function getCampaign(id: string): Promise<Campaign> {
  const response = await fetch(`${API_BASE_URL}/api/v1/campaigns/${id}`, {
    headers: buildHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch campaign');
  }

  return response.json();
}

export async function deleteCampaign(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/campaigns/${id}`, {
    method: 'DELETE',
    headers: buildHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to delete campaign');
  }
}

export async function launchCampaign(id: string): Promise<Campaign> {
  const response = await fetch(`${API_BASE_URL}/api/v1/campaigns/${id}/launch`, {
    method: 'POST',
    headers: buildHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to launch campaign');
  }

  return response.json();
}

export async function pauseCampaign(id: string): Promise<Campaign> {
  const response = await fetch(`${API_BASE_URL}/api/v1/campaigns/${id}/pause`, {
    method: 'POST',
    headers: buildHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to pause campaign');
  }

  return response.json();
}

export async function getCampaignAnalytics(id: string): Promise<CampaignAnalytics> {
  const response = await fetch(`${API_BASE_URL}/api/v1/campaigns/${id}/analytics`, {
    headers: buildHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch campaign analytics');
  }

  return response.json();
}

// ==================== Segment API ====================

export async function previewSegment(
  filter: SegmentFilter,
  campaignType: CampaignType
): Promise<SegmentPreview> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/campaigns/contacts/segment/preview?campaign_type=${campaignType}`,
    {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify(filter),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to preview segment');
  }

  return response.json();
}
