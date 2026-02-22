/**
 * Payment API Client
 *
 * Handles payment processing with Stripe and Flutterwave integration.
 */

import { API_BASE_URL } from "../api-config";
import { getAuthTokenSync } from '../auth';

// ==================== Types ====================

export enum PaymentGateway {
  STRIPE = "stripe",
  FLUTTERWAVE = "flutterwave",
  MANUAL = "manual"
}

export enum PaymentMethod {
  CARD = "card",
  MOBILE_MONEY = "mobile_money",
  BANK_TRANSFER = "bank_transfer",
  CASH = "cash",
  CHECK = "check"
}

export enum MobileMoneyProvider {
  MTN_MOMO = "mtn_momo",
  VODAFONE_CASH = "vodafone_cash",
  AIRTELTIGO_MONEY = "airteltigo_money"
}

export enum PaymentStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
  REFUNDED = "refunded",
  PARTIALLY_REFUNDED = "partially_refunded"
}

export enum PaymentPurpose {
  RENT = "rent",
  SECURITY_DEPOSIT = "security_deposit",
  PURCHASE = "purchase",
  COMMISSION = "commission",
  SERVICE_FEE = "service_fee",
  BOOKING_FEE = "booking_fee",
  OTHER = "other"
}

export interface CardDetails {
  last4: string;
  brand: string;
  exp_month: number;
  exp_year: number;
  country?: string;
}

export interface MobileMoneyDetails {
  provider: MobileMoneyProvider;
  phone_number: string;
  account_name?: string;
}

export interface PaymentMetadata {
  invoice_id?: string;
  property_id?: string;
  booking_id?: string;
  contract_id?: string;
  custom_fields?: Record<string, any>;
}

export interface Payment {
  id: string;
  organization_id: string;
  amount: number;
  currency: string;
  description: string;
  purpose: PaymentPurpose;
  gateway: PaymentGateway;
  payment_method: PaymentMethod;
  status: PaymentStatus;
  gateway_payment_id?: string;
  gateway_customer_id?: string;
  gateway_charge_id?: string;
  card_details?: CardDetails;
  mobile_money_details?: MobileMoneyDetails;
  customer_id: string;
  customer_name: string;
  customer_email?: string;
  customer_phone?: string;
  metadata: PaymentMetadata;
  refunded_amount: number;
  refund_reason?: string;
  error_code?: string;
  error_message?: string;
  platform_fee: number;
  gateway_fee: number;
  net_amount: number;
  created_at: string;
  updated_at: string;
  processed_at?: string;
  completed_at?: string;
  failed_at?: string;
  refunded_at?: string;
  notes?: string;
}

export interface PaymentIntent {
  id: string;
  amount: number;
  currency: string;
  client_secret?: string;
  gateway: PaymentGateway;
  status: string;
  created_at: string;
}

export interface CreatePaymentData {
  amount: number;
  currency: string;
  description: string;
  purpose: PaymentPurpose;
  gateway: PaymentGateway;
  payment_method: PaymentMethod;
  customer_id?: string;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
  invoice_id?: string;
  property_id?: string;
  booking_id?: string;
  custom_metadata?: Record<string, any>;
  mobile_money_provider?: MobileMoneyProvider;
  mobile_money_phone?: string;
  return_url?: string;
  cancel_url?: string;
}

export interface ConfirmPaymentData {
  payment_intent_id?: string;
  gateway_payment_id?: string;
  payment_method_details?: Record<string, any>;
}

export interface RefundPaymentData {
  amount?: number;
  reason: string;
  notes?: string;
}

export interface PaymentListResponse {
  payments: Payment[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface PaymentStats {
  total_payments: number;
  total_revenue: number;
  pending_amount: number;
  failed_amount: number;
  refunded_amount: number;
  completed_count: number;
  pending_count: number;
  failed_count: number;
  refunded_count: number;
  card_revenue: number;
  mobile_money_revenue: number;
  bank_transfer_revenue: number;
  cash_revenue: number;
  currency: string;
  period?: string;
}

// ==================== Helper Functions ====================

function buildHeaders(): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  const token = getAuthTokenSync();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const orgId = localStorage.getItem('selectedOrganizationId');
  if (orgId) {
    headers["X-Organization-ID"] = orgId;
  }

  return headers;
}

function buildUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

// ==================== API Functions ====================

/**
 * Create a new payment.
 */
export async function createPayment(data: CreatePaymentData): Promise<Payment> {
  const response = await fetch(buildUrl("/api/v1/payments"), {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(data),
  });

  return handleResponse<Payment>(response);
}

/**
 * Create payment intent for client-side initialization.
 */
export async function createPaymentIntent(paymentId: string): Promise<PaymentIntent> {
  const response = await fetch(buildUrl(`/api/v1/payments/${paymentId}/intent`), {
    method: "POST",
    headers: buildHeaders(),
  });

  return handleResponse<PaymentIntent>(response);
}

/**
 * Confirm payment after gateway processing.
 */
export async function confirmPayment(
  paymentId: string,
  data?: ConfirmPaymentData
): Promise<Payment> {
  const response = await fetch(buildUrl(`/api/v1/payments/${paymentId}/confirm`), {
    method: "POST",
    headers: buildHeaders(),
    body: data ? JSON.stringify(data) : undefined,
  });

  return handleResponse<Payment>(response);
}

/**
 * Get payment by ID.
 */
export async function getPayment(paymentId: string): Promise<Payment> {
  const response = await fetch(buildUrl(`/api/v1/payments/${paymentId}`), {
    method: "GET",
    headers: buildHeaders(),
  });

  return handleResponse<Payment>(response);
}

/**
 * List payments with filters.
 */
export async function listPayments(params?: {
  status?: PaymentStatus;
  gateway?: PaymentGateway;
  payment_method?: PaymentMethod;
  customer_id?: string;
  property_id?: string;
  invoice_id?: string;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}): Promise<PaymentListResponse> {
  const queryParams = new URLSearchParams();

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, String(value));
      }
    });
  }

  const url = buildUrl(`/api/v1/payments?${queryParams.toString()}`);
  const response = await fetch(url, {
    method: "GET",
    headers: buildHeaders(),
  });

  return handleResponse<PaymentListResponse>(response);
}

/**
 * Refund a payment (full or partial).
 */
export async function refundPayment(
  paymentId: string,
  data: RefundPaymentData
): Promise<Payment> {
  const response = await fetch(buildUrl(`/api/v1/payments/${paymentId}/refund`), {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(data),
  });

  return handleResponse<Payment>(response);
}

/**
 * Get payment statistics.
 */
export async function getPaymentStats(currency: string = "GHS"): Promise<PaymentStats> {
  const response = await fetch(buildUrl(`/api/v1/payments/stats/overview?currency=${currency}`), {
    method: "GET",
    headers: buildHeaders(),
  });

  return handleResponse<PaymentStats>(response);
}

/**
 * Format payment amount with currency symbol.
 */
export function formatPaymentAmount(amount: number, currency: string): string {
  const symbols: Record<string, string> = {
    GHS: "GH₵",
    USD: "$",
    EUR: "€",
    GBP: "£",
  };

  const symbol = symbols[currency] || currency;
  return `${symbol}${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Get human-readable payment status.
 */
export function getPaymentStatusLabel(status: PaymentStatus): string {
  const labels: Record<PaymentStatus, string> = {
    [PaymentStatus.PENDING]: "Pending",
    [PaymentStatus.PROCESSING]: "Processing",
    [PaymentStatus.COMPLETED]: "Completed",
    [PaymentStatus.FAILED]: "Failed",
    [PaymentStatus.CANCELLED]: "Cancelled",
    [PaymentStatus.REFUNDED]: "Refunded",
    [PaymentStatus.PARTIALLY_REFUNDED]: "Partially Refunded",
  };

  return labels[status] || status;
}

/**
 * Get payment method display name.
 */
export function getPaymentMethodLabel(method: PaymentMethod): string {
  const labels: Record<PaymentMethod, string> = {
    [PaymentMethod.CARD]: "Card",
    [PaymentMethod.MOBILE_MONEY]: "Mobile Money",
    [PaymentMethod.BANK_TRANSFER]: "Bank Transfer",
    [PaymentMethod.CASH]: "Cash",
    [PaymentMethod.CHECK]: "Check",
  };

  return labels[method] || method;
}

/**
 * Get mobile money provider display name.
 */
export function getMobileMoneyProviderLabel(provider: MobileMoneyProvider): string {
  const labels: Record<MobileMoneyProvider, string> = {
    [MobileMoneyProvider.MTN_MOMO]: "MTN Mobile Money",
    [MobileMoneyProvider.VODAFONE_CASH]: "Vodafone Cash",
    [MobileMoneyProvider.AIRTELTIGO_MONEY]: "AirtelTigo Money",
  };

  return labels[provider] || provider;
}

/**
 * Get payment gateway display name.
 */
export function getPaymentGatewayLabel(gateway: PaymentGateway): string {
  const labels: Record<PaymentGateway, string> = {
    [PaymentGateway.STRIPE]: "Stripe",
    [PaymentGateway.FLUTTERWAVE]: "Flutterwave",
    [PaymentGateway.MANUAL]: "Manual Payment",
  };

  return labels[gateway] || gateway;
}
