/**
 * Invoice API Client
 *
 * Handles all invoice-related API calls including CRUD operations,
 * payment tracking, and PDF generation.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getAuthToken } from '../auth';
import { buildApiUrl } from '../api-config';

// ============================================================================
// Types
// ============================================================================

export enum InvoiceStatus {
  DRAFT = 'draft',
  SENT = 'sent',
  PAID = 'paid',
  OVERDUE = 'overdue',
  CANCELLED = 'cancelled',
}

export enum PaymentMethod {
  CASH = 'cash',
  BANK_TRANSFER = 'bank_transfer',
  CREDIT_CARD = 'credit_card',
  MOBILE_MONEY = 'mobile_money',
  CHECK = 'check',
  OTHER = 'other',
}

export interface InvoiceLineItem {
  description: string;
  quantity: number;
  unit_price: number;
  amount?: number;
  tax_rate?: number;
  tax_amount?: number;
}

export interface Invoice {
  id: string;
  organization_id: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;

  contact_id: string;
  contact_name: string;
  contact_email?: string;
  contact_phone?: string;
  contact_address?: string;

  property_id?: string;
  property_name?: string;

  line_items: InvoiceLineItem[];

  subtotal: number;
  tax_amount: number;
  total_amount: number;
  currency: string;

  status: InvoiceStatus;
  payment_method?: PaymentMethod;
  paid_date?: string;
  paid_amount: number;

  notes?: string;
  terms?: string;

  created_by: string;
  created_at: string;
  updated_at: string;
  sent_at?: string;
}

export interface InvoiceCreate {
  contact_id: string;
  property_id?: string;
  due_date: string;
  line_items: InvoiceLineItem[];
  currency?: string;
  notes?: string;
  terms?: string;
}

export interface InvoiceUpdate {
  due_date?: string;
  line_items?: InvoiceLineItem[];
  notes?: string;
  terms?: string;
  status?: InvoiceStatus;
}

export interface InvoiceMarkPaid {
  payment_method: PaymentMethod;
  paid_amount: number;
  paid_date?: string;
  notes?: string;
}

export interface InvoiceFilters {
  status?: InvoiceStatus[];
  contact_id?: string;
  property_id?: string;
  search?: string;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface InvoiceListResponse {
  invoices: Invoice[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface InvoiceStats {
  total_invoices: number;
  total_revenue: number;
  pending_amount: number;
  overdue_amount: number;
  draft_count: number;
  sent_count: number;
  paid_count: number;
  overdue_count: number;
  currency: string;
  period?: string;
}

// ============================================================================
// API Functions
// ============================================================================

const getHeaders = () => {
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
};

/**
 * List invoices with optional filters
 */
export const listInvoices = async (filters?: InvoiceFilters): Promise<InvoiceListResponse> => {
  const params = new URLSearchParams();

  if (filters?.status?.length) {
    params.append('status_filter', filters.status.join(','));
  }
  if (filters?.contact_id) params.append('contact_id', filters.contact_id);
  if (filters?.property_id) params.append('property_id', filters.property_id);
  if (filters?.search) params.append('search', filters.search);
  if (filters?.limit) params.append('limit', filters.limit.toString());
  if (filters?.offset) params.append('offset', filters.offset.toString());
  if (filters?.sort_by) params.append('sort_by', filters.sort_by);
  if (filters?.sort_order) params.append('sort_order', filters.sort_order);

  const response = await fetch(
    buildApiUrl(`/api/v1/invoices?${params.toString()}`),
    {
      headers: getHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch invoices');
  }

  return response.json();
};

/**
 * Get invoice by ID
 */
export const getInvoice = async (invoiceId: string): Promise<Invoice> => {
  const response = await fetch(buildApiUrl(`/api/v1/invoices/${invoiceId}`), {
    headers: getHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch invoice ${invoiceId}`);
  }

  return response.json();
};

/**
 * Create a new invoice
 */
export const createInvoice = async (data: InvoiceCreate): Promise<Invoice> => {
  const response = await fetch(buildApiUrl('/api/v1/invoices'), {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create invoice');
  }

  return response.json();
};

/**
 * Update an invoice
 */
export const updateInvoice = async (
  invoiceId: string,
  updates: InvoiceUpdate
): Promise<Invoice> => {
  const response = await fetch(buildApiUrl(`/api/v1/invoices/${invoiceId}`), {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update invoice');
  }

  return response.json();
};

/**
 * Delete an invoice
 */
export const deleteInvoice = async (invoiceId: string): Promise<void> => {
  const response = await fetch(buildApiUrl(`/api/v1/invoices/${invoiceId}`), {
    method: 'DELETE',
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete invoice');
  }
};

/**
 * Mark invoice as paid
 */
export const markInvoicePaid = async (
  invoiceId: string,
  paymentData: InvoiceMarkPaid
): Promise<Invoice> => {
  const response = await fetch(
    buildApiUrl(`/api/v1/invoices/${invoiceId}/mark-paid`),
    {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(paymentData),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to mark invoice as paid');
  }

  return response.json();
};

/**
 * Send invoice via email
 */
export const sendInvoice = async (invoiceId: string): Promise<{message: string}> => {
  const response = await fetch(buildApiUrl(`/api/v1/invoices/${invoiceId}/send`), {
    method: 'POST',
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to send invoice');
  }

  return response.json();
};

/**
 * Get invoice statistics
 */
export const getInvoiceStats = async (currency = 'GHS'): Promise<InvoiceStats> => {
  const response = await fetch(
    buildApiUrl(`/api/v1/invoices/stats?currency=${currency}`),
    {
      headers: getHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch invoice statistics');
  }

  return response.json();
};

/**
 * Download invoice as PDF
 */
export const downloadInvoicePDF = async (invoiceId: string): Promise<Blob> => {
  const response = await fetch(
    buildApiUrl(`/api/v1/invoices/${invoiceId}/download/pdf`),
    {
      headers: getHeaders(),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to download PDF');
  }

  return response.blob();
};

// ============================================================================
// React Query Hooks
// ============================================================================

/**
 * Hook to list invoices
 */
export const useInvoices = (filters?: InvoiceFilters) => {
  return useQuery({
    queryKey: ['invoices', filters],
    queryFn: () => listInvoices(filters),
  });
};

/**
 * Hook to get a single invoice
 */
export const useInvoice = (invoiceId: string | null) => {
  return useQuery({
    queryKey: ['invoices', invoiceId],
    queryFn: () => getInvoice(invoiceId!),
    enabled: !!invoiceId,
  });
};

/**
 * Hook to get invoice statistics
 */
export const useInvoiceStats = (currency = 'GHS') => {
  return useQuery({
    queryKey: ['invoice-stats', currency],
    queryFn: () => getInvoiceStats(currency),
  });
};

/**
 * Hook to create an invoice
 */
export const useCreateInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createInvoice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['invoice-stats'] });
    },
  });
};

/**
 * Hook to update an invoice
 */
export const useUpdateInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ invoiceId, updates }: { invoiceId: string; updates: InvoiceUpdate }) =>
      updateInvoice(invoiceId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['invoices', variables.invoiceId] });
      queryClient.invalidateQueries({ queryKey: ['invoice-stats'] });
    },
  });
};

/**
 * Hook to delete an invoice
 */
export const useDeleteInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteInvoice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['invoice-stats'] });
    },
  });
};

/**
 * Hook to mark invoice as paid
 */
export const useMarkInvoicePaid = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      invoiceId,
      paymentData,
    }: {
      invoiceId: string;
      paymentData: InvoiceMarkPaid;
    }) => markInvoicePaid(invoiceId, paymentData),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['invoices', variables.invoiceId] });
      queryClient.invalidateQueries({ queryKey: ['invoice-stats'] });
    },
  });
};

/**
 * Hook to send invoice
 */
export const useSendInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: sendInvoice,
    onSuccess: (_, invoiceId) => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['invoices', invoiceId] });
    },
  });
};

/**
 * Hook to download invoice PDF
 */
export const useDownloadInvoicePDF = () => {
  return useMutation({
    mutationFn: downloadInvoicePDF,
    onSuccess: (blob, invoiceId) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-${invoiceId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
};
