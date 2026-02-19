/**
 * WhatsApp Campaigns API Client for ChurchFlow
 *
 * Provides functions for managing WhatsApp campaigns using WhatsApp Business API.
 * Includes support for templates, media, buttons, and delivery tracking.
 */

import { getApiUrl } from '../config';

// ==================== Types ====================

export interface WhatsAppButton {
  type: 'reply' | 'url' | 'phone_number';
  title: string;
  payload?: string;
  url?: string;
  phone_number?: string;
}

export interface WhatsAppCampaignConfig {
  send_rate_per_second: number;
  batch_size: number;
  retry_failed: boolean;
  max_retries: number;
  scheduled_time?: string;
  template_name: string;
  enable_media: boolean;
  media_url?: string;
  media_type?: 'image' | 'video' | 'audio' | 'document';
  media_caption?: string;
  enable_buttons: boolean;
  buttons: WhatsAppButton[];
  phone_number_id: string;
}

export interface WhatsAppCampaign {
  id: string;
  name: string;
  organization_id: string;
  user_id: string;
  template_name?: string;
  template_content: string;
  audience_id?: string;
  status: 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  progress: {
    total_recipients: number;
    sent: number;
    delivered: number;
    read: number;
    failed: number;
    pending: number;
  };
  config: WhatsAppCampaignConfig;
  total_cost: number;
  cost_per_message: number;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  phone_number_id: string;
}

export interface WhatsAppTemplate {
  id: string;
  name: string;
  language: string;
  category: string;
  status: 'APPROVED' | 'PENDING' | 'REJECTED' | 'DISABLED';
  components: any[];
  placeholders: string[];
}

export interface WhatsAppCampaignAnalytics {
  campaign_id: string;
  name: string;
  status: string;
  progress: {
    total: number;
    sent: number;
    delivered: number;
    read: number;
    failed: number;
    pending: number;
    progress_percentage: number;
    success_rate: number;
    delivery_rate: number;
    read_rate: number;
  };
  cost: {
    total: number;
    per_message: number;
    average: number;
  };
  timing: {
    created_at: string;
    started_at?: string;
    completed_at?: string;
    duration_seconds?: number;
  };
}

export interface WhatsAppMessage {
  id: string;
  campaign_id: string;
  recipient_phone: string;
  recipient_name?: string;
  recipient_email?: string;
  recipient_data: any;
  message_content: string;
  template_name?: string;
  template_variables: Record<string, any>;
  status: 'pending' | 'sent' | 'delivered' | 'read' | 'failed';
  provider_message_id?: string;
  sent_at?: string;
  delivered_at?: string;
  read_at?: string;
  failed_at?: string;
  media_url?: string;
  media_id?: string;
  media_caption?: string;
  buttons: WhatsAppButton[];
  error_message?: string;
  retry_count: number;
  cost: number;
  created_at: string;
}

export interface CreateWhatsAppCampaignRequest {
  name: string;
  template_name: string;
  audience_id?: string;
  config: Partial<WhatsAppCampaignConfig>;
}

export interface UpdateWhatsAppCampaignRequest {
  name?: string;
  template_name?: string;
  audience_id?: string;
  config?: Partial<WhatsAppCampaignConfig>;
}

export interface StartWhatsAppCampaignRequest {
  contacts?: Array<{
    phone: string;
    name?: string;
    email?: string;
    [key: string]: any;
  }>;
}

// ==================== Helper Functions ====================

const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` })
  };
};

const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail || error.message || 'Request failed');
  }
  return response.json();
};

// ==================== API Functions ====================

export async function createWhatsAppCampaign(data: CreateWhatsAppCampaignRequest): Promise<WhatsAppCampaign> {
  const response = await fetch(`${getApiUrl()}/api/whatsapp-campaigns/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
}

export async function getWhatsAppCampaigns(params?: {
  status?: string;
  limit?: number;
  skip?: number;
}): Promise<{ campaigns: WhatsAppCampaign[]; total: number }> {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.append('status', params.status);
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.skip) queryParams.append('skip', params.skip.toString());

  const queryString = queryParams.toString();
  const endpoint = `${getApiUrl()}/api/whatsapp-campaigns/${queryString ? `?${queryString}` : ''}`;

  const response = await fetch(endpoint, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
}

export async function getWhatsAppCampaign(campaignId: string): Promise<WhatsAppCampaign> {
  const response = await fetch(`${getApiUrl()}/api/whatsapp-campaigns/${campaignId}`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
}

export async function updateWhatsAppCampaign(
  campaignId: string,
  data: UpdateWhatsAppCampaignRequest
): Promise<WhatsAppCampaign> {
  const response = await fetch(`${getApiUrl()}/api/whatsapp-campaigns/${campaignId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
}

export async function deleteWhatsAppCampaign(campaignId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${getApiUrl()}/api/whatsapp-campaigns/${campaignId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
}

export async function startWhatsAppCampaign(
  campaignId: string,
  data?: StartWhatsAppCampaignRequest
): Promise<{ success: boolean; message: string; campaign_id: string }> {
  const response = await fetch(`${getApiUrl()}/api/whatsapp-campaigns/${campaignId}/start`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data || {})
  });
  return handleResponse(response);
}

export async function pauseWhatsAppCampaign(campaignId: string): Promise<{ success: boolean; message: string; campaign_id: string }> {
  const response = await fetch(`${getApiUrl()}/api/whatsapp-campaigns/${campaignId}/pause`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
}

export async function cancelWhatsAppCampaign(campaignId: string): Promise<{ success: boolean; message: string; campaign_id: string }> {
  const response = await fetch(`${getApiUrl()}/api/whatsapp-campaigns/${campaignId}/cancel`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
}

export async function getWhatsAppTemplates(): Promise<{ templates: WhatsAppTemplate[]; total: number }> {
  const response = await fetch(`${getApiUrl()}/api/whatsapp-campaigns/templates/list`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
}

export async function syncWhatsAppTemplates(): Promise<{ success: boolean; message: string; count: number }> {
  const response = await fetch(`${getApiUrl()}/api/whatsapp-campaigns/templates/sync`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
}

export async function getWhatsAppCampaignAnalytics(campaignId: string): Promise<WhatsAppCampaignAnalytics> {
  const response = await fetch(`${getApiUrl()}/api/whatsapp-campaigns/${campaignId}/analytics`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
}

export async function getWhatsAppCampaignMessages(
  campaignId: string,
  params?: {
    status?: string;
    limit?: number;
    skip?: number;
  }
): Promise<{ messages: WhatsAppMessage[]; total: number; campaign_id: string }> {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.append('status', params.status);
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.skip) queryParams.append('skip', params.skip.toString());

  const queryString = queryParams.toString();
  const endpoint = `${getApiUrl()}/api/whatsapp-campaigns/${campaignId}/messages${queryString ? `?${queryString}` : ''}`;

  const response = await fetch(endpoint, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
}

// ==================== Helper Functions for UI ====================

export function getCampaignStatusColor(status: string): string {
  const colors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-800',
    scheduled: 'bg-blue-100 text-blue-800',
    running: 'bg-green-100 text-green-800 animate-pulse',
    paused: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
}

export function formatCampaignStatus(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export function calculateProgressPercentage(campaign: WhatsAppCampaign): number {
  if (campaign.progress.total_recipients === 0) return 0;
  return Math.round(
    ((campaign.progress.sent + campaign.progress.failed) / campaign.progress.total_recipients) * 100
  );
}

export function formatCost(cost: number): string {
  return `$${cost.toFixed(4)}`;
}

export function formatPhoneNumber(phone: string): string {
  if (phone.startsWith('+')) return phone;
  return `+${phone}`;
}
