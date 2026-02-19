/**
 * Phone Number Management API Client
 * Handles phone number provisioning, importing, assignment, and testing
 */

import { API_BASE_URL } from '@/config/api-config';

export interface PhoneNumber {
  id: string;
  number: string;
  provider: 'kasaai' | 'twilio' | 'vonage' | 'telnyx' | 'vapi' | 'sip_trunk';
  type: 'inbound' | 'outbound' | 'both';
  status: 'active' | 'inactive' | 'pending' | 'porting' | 'failed';
  country: string;
  country_code: string;
  capabilities: string[];
  monthly_cost?: number;
  setup_cost?: number;
  ported_from?: string;
  sip_username?: string;
  sip_password?: string;
  sip_server?: string;
  webhook_url?: string;
  assigned_assistant_id?: string;
  assigned_at?: string;

  // Cost tracking and billing fields
  cost_per_minute: number;
  credit_balance: number;
  total_minutes_used: number;
  total_cost_spent: number;
  currency: string;
  low_balance_threshold?: number;

  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface ProviderConfig {
  provider: string;
  api_key?: string;
  api_secret?: string;
  account_sid?: string;
  auth_token?: string;
  webhook_url?: string;
  sip_server?: string;
  sip_username?: string;
  sip_password?: string;
  phone_id?: string; // For VAPI BYO phone import
}

export interface ImportRequest {
  provider: 'twilio' | 'vonage' | 'telnyx' | 'vapi';
  config: ProviderConfig;
  filter_country?: string;
  filter_capabilities?: string[];
}

export interface ProvisionRequest {
  provider: 'kasaai';
  country_code: string;
  area_code?: string;
  capabilities?: string[];
  plan?: 'starter' | 'professional' | 'enterprise';
  sip_provider?: 'freeswitch' | 'asterisk';
}

export interface AssignRequest {
  assistant_id: string;
}

export interface TestPhoneRequest {
  assistant_id: string;
  ui_title?: string;
  ui_subtitle?: string;
}

export interface LaunchUIRequest {
  assistant_id: string;
  ui_title?: string;
  ui_subtitle?: string;
  share?: boolean;
}

const PHONE_API_BASE = `${API_BASE_URL}/phone-numbers`;
const TESTING_API_BASE = `${API_BASE_URL}/assistant-testing`;

/**
 * Get all phone numbers
 */
export async function getPhoneNumbers(): Promise<{ success: boolean; numbers: PhoneNumber[]; count: number }> {
  const response = await fetch(PHONE_API_BASE, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch phone numbers: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get a specific phone number by ID
 */
export async function getPhoneNumber(numberId: string): Promise<PhoneNumber> {
  const response = await fetch(`${PHONE_API_BASE}/${numberId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch phone number: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get phone numbers assigned to an assistant
 */
export async function getAssistantPhoneNumbers(assistantId: string): Promise<{ success: boolean; numbers: PhoneNumber[]; count: number }> {
  const response = await fetch(`${PHONE_API_BASE}/assistant/${assistantId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch assistant phone numbers: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Import phone numbers from a provider (Twilio, Vonage, Telnyx)
 */
export async function importPhoneNumbers(request: ImportRequest): Promise<{ success: boolean; numbers: PhoneNumber[]; message: string }> {
  const response = await fetch(`${PHONE_API_BASE}/import`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to import phone numbers: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Provision a new phone number (Kasa AI)
 */
export async function provisionPhoneNumber(request: ProvisionRequest): Promise<{ success: boolean; number: PhoneNumber; message: string }> {
  const response = await fetch(`${PHONE_API_BASE}/provision`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to provision phone number: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Assign phone number to assistant (or unassign if already assigned to same assistant)
 */
export async function assignPhoneToAssistant(numberId: string, assistantId: string): Promise<{ success: boolean; number: PhoneNumber; message: string; action: 'assigned' | 'unassigned' }> {
  const response = await fetch(`${PHONE_API_BASE}/${numberId}/assign`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ assistant_id: assistantId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to assign phone number: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Unassign phone number from assistant
 */
export async function unassignPhoneFromAssistant(numberId: string): Promise<{ success: boolean; number: PhoneNumber; message: string }> {
  const response = await fetch(`${PHONE_API_BASE}/${numberId}/unassign`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to unassign phone number: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Delete/release a phone number
 */
export async function deletePhoneNumber(numberId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${PHONE_API_BASE}/${numberId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to delete phone number: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Configure phone number settings
 */
export async function configurePhoneNumber(
  numberId: string,
  config: { webhook_url?: string; sip_config?: { server?: string; username?: string; password?: string } }
): Promise<{ success: boolean; number: PhoneNumber; message: string }> {
  const response = await fetch(`${PHONE_API_BASE}/${numberId}/configure`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to configure phone number: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get available providers
 */
export async function getAvailableProviders(): Promise<{ providers: any[] }> {
  const response = await fetch(`${PHONE_API_BASE}/providers/available`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch providers: ${response.statusText}`);
  }

  return response.json();
}

// ==================== Assistant Testing APIs ====================

/**
 * Generate temporary test phone number for assistant using .fastphone()
 */
export async function generateTestPhone(request: TestPhoneRequest): Promise<{ success: boolean; number: string; country: string; expires_at: string; message: string }> {
  const response = await fetch(`${TESTING_API_BASE}/generate-phone`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to generate test phone: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Launch shareable testing UI for assistant using .ui.launch()
 */
export async function launchShareableUI(request: LaunchUIRequest): Promise<{ success: boolean; url: string; local_url: string; share_url?: string; message: string; expires_in_hours?: number }> {
  const response = await fetch(`${TESTING_API_BASE}/launch-ui`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to launch UI: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get testing status (check if FastRTC features are available)
 */
export async function getTestingStatus(): Promise<{ fastrtc_available: boolean; huggingface_token_set: boolean; features: Record<string, boolean>; requirements: Record<string, string> }> {
  const response = await fetch(`${TESTING_API_BASE}/status`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch testing status: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get testing info for a specific assistant
 */
export async function getAssistantTestingInfo(assistantId: string): Promise<any> {
  const response = await fetch(`${TESTING_API_BASE}/assistant/${assistantId}/testing-info`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch assistant testing info: ${response.statusText}`);
  }

  return response.json();
}

// ==================== Credit Management APIs ====================

export interface CreditTransaction {
  id: string;
  phone_id: string;
  phone_number: string;
  amount: number;
  transaction_type: 'credit' | 'debit';
  timestamp: string;
  balance_before: number;
  balance_after: number;
  added_by_user_id?: string;
  payment_method?: string;
  reference_number?: string;
  notes?: string;
  call_id?: string;
  call_duration_seconds?: number;
  call_duration_minutes?: number;
  campaign_id?: string;
  metadata?: Record<string, any>;
}

export interface AddCreditRequest {
  amount: number;
  user_id?: string;
  payment_method?: string;
  reference_number?: string;
  notes?: string;
}

export interface UpdateCostRateRequest {
  cost_per_minute: number;
  currency?: string;
  low_balance_threshold?: number;
}

export interface PhoneUsageStats {
  success: boolean;
  phone_id: string;
  phone_number: string;
  currency: string;
  cost_per_minute: number;
  credit_balance: number;
  remaining_minutes: number;
  total_minutes_used: number;
  total_cost_spent: number;
  usage_percentage: number;
  low_balance_alert: boolean;
  low_balance_threshold?: number;
  recent_transactions_count: number;
}

export interface CostSummary {
  success: boolean;
  summary: {
    total_phones: number;
    phones_with_activity: number;
    total_balance: number;
    total_minutes_used: number;
    total_cost_spent: number;
    low_balance_alerts: number;
  };
  phones: Array<{
    id: string;
    number: string;
    provider: string;
    currency: string;
    credit_balance: number;
    total_minutes_used: number;
    total_cost_spent: number;
    vapi_cost_usd: number;
    cost_per_minute: number;
    low_balance_alert: boolean;
  }>;
}

/**
 * Add credit to a phone number
 */
export async function addPhoneCredit(
  phoneId: string,
  request: AddCreditRequest
): Promise<{ success: boolean; message: string; transaction: CreditTransaction; phone: PhoneNumber }> {
  const response = await fetch(`${PHONE_API_BASE}/${phoneId}/credit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to add credit: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get credit transaction history for a phone number
 */
export async function getPhoneCreditHistory(
  phoneId: string,
  limit: number = 100,
  transactionType?: 'credit' | 'debit'
): Promise<{ success: boolean; count: number; transactions: CreditTransaction[] }> {
  const params = new URLSearchParams();
  params.append('limit', limit.toString());
  if (transactionType) {
    params.append('transaction_type', transactionType);
  }

  const response = await fetch(`${PHONE_API_BASE}/${phoneId}/credit-history?${params}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to fetch credit history: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get usage statistics for a phone number
 */
export async function getPhoneUsageStats(phoneId: string): Promise<PhoneUsageStats> {
  const response = await fetch(`${PHONE_API_BASE}/${phoneId}/usage-stats`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to fetch usage stats: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update cost per minute rate for a phone number
 */
export async function updatePhoneCostRate(
  phoneId: string,
  request: UpdateCostRateRequest
): Promise<{ success: boolean; message: string; phone: PhoneNumber }> {
  const response = await fetch(`${PHONE_API_BASE}/${phoneId}/cost-rate`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to update cost rate: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get cost summary across all phone numbers
 */
export async function getCostSummary(): Promise<CostSummary> {
  const response = await fetch(`${PHONE_API_BASE}/cost-summary`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to fetch cost summary: ${response.statusText}`);
  }

  return response.json();
}

// ==================== Slack Alert APIs ====================

export interface SlackLowCreditAlertRequest {
  phone_number: string;
  current_balance: number;
  threshold?: number; // Default: 500 GHC
  currency?: string; // Default: GHC
  phone_name?: string;
  remaining_minutes?: number;
}

/**
 * Send a Slack notification for low phone credit
 * Should be called when credit falls below the threshold (default: 500 GHC)
 */
export async function sendSlackLowCreditAlert(
  request: SlackLowCreditAlertRequest
): Promise<{ success: boolean; message: string; skipped?: boolean }> {
  const response = await fetch(`${PHONE_API_BASE}/alerts/slack/low-credit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      phone_number: request.phone_number,
      current_balance: request.current_balance,
      threshold: request.threshold ?? 500,
      currency: request.currency ?? 'GHC',
      phone_name: request.phone_name,
      remaining_minutes: request.remaining_minutes,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to send Slack alert: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Send a critical Slack alert when total system balance is low
 */
export async function sendSlackCriticalBalanceAlert(
  total_balance: number,
  threshold: number = 500,
  currency: string = 'GHC',
  phones_below_threshold: number = 0
): Promise<{ success: boolean; message: string }> {
  const params = new URLSearchParams({
    total_balance: total_balance.toString(),
    threshold: threshold.toString(),
    currency,
    phones_below_threshold: phones_below_threshold.toString(),
  });

  const response = await fetch(`${PHONE_API_BASE}/alerts/slack/critical-balance?${params}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to send critical alert: ${response.statusText}`);
  }

  return response.json();
}
