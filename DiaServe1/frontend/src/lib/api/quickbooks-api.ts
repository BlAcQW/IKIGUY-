/**
 * QuickBooks Online API Client
 *
 * Handles QBO connection management and invoice sync operations.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getAuthTokenSync } from '../auth';
import { buildApiUrl, API_ENDPOINTS } from '../api-config';

// ============================================================================
// Types
// ============================================================================

export interface QBOConnectionStatus {
  is_connected: boolean;
  company_name: string | null;
  realm_id: string | null;
  connected_at: string | null;
}

export interface QBOSyncResult {
  total_invoices: number;
  synced: number;
  failed: number;
  errors: string[];
}

// ============================================================================
// API Functions
// ============================================================================

const getHeaders = () => {
  const token = getAuthTokenSync();
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };
};

/**
 * Get QBO OAuth authorization URL
 */
export const getQBOAuthUrl = async (): Promise<{ auth_url: string }> => {
  const response = await fetch(
    buildApiUrl(API_ENDPOINTS.quickbooks.authUrl),
    { headers: getHeaders() }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get QuickBooks auth URL');
  }
  return response.json();
};

/**
 * Get QBO connection status
 */
export const getQBOStatus = async (): Promise<QBOConnectionStatus> => {
  const response = await fetch(
    buildApiUrl(API_ENDPOINTS.quickbooks.status),
    { headers: getHeaders() }
  );
  if (!response.ok) {
    throw new Error('Failed to get QuickBooks status');
  }
  return response.json();
};

/**
 * Disconnect QBO
 */
export const disconnectQBO = async (): Promise<void> => {
  const response = await fetch(
    buildApiUrl(API_ENDPOINTS.quickbooks.disconnect),
    {
      method: 'POST',
      headers: getHeaders(),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to disconnect QuickBooks');
  }
};

/**
 * Sync all unsynced invoices to QBO
 */
export const syncAllInvoices = async (): Promise<QBOSyncResult> => {
  const response = await fetch(
    buildApiUrl(API_ENDPOINTS.quickbooks.sync),
    {
      method: 'POST',
      headers: getHeaders(),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to sync invoices');
  }
  return response.json();
};

/**
 * Sync a single invoice to QBO
 */
export const syncSingleInvoice = async (
  invoiceId: string
): Promise<{ message: string; qbo_invoice_id: string }> => {
  const response = await fetch(
    buildApiUrl(API_ENDPOINTS.quickbooks.syncInvoice(invoiceId)),
    {
      method: 'POST',
      headers: getHeaders(),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to sync invoice');
  }
  return response.json();
};

// ============================================================================
// React Query Hooks
// ============================================================================

/**
 * Hook to get QBO connection status
 */
export const useQBOStatus = () => {
  return useQuery({
    queryKey: ['qbo-status'],
    queryFn: getQBOStatus,
    retry: false,
    staleTime: 30_000,
  });
};

/**
 * Hook to sync all invoices to QBO
 */
export const useQBOSync = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: syncAllInvoices,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
  });
};

/**
 * Hook to sync a single invoice to QBO
 */
export const useQBOSyncInvoice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: syncSingleInvoice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
  });
};

/**
 * Hook to disconnect QBO
 */
export const useQBODisconnect = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: disconnectQBO,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['qbo-status'] });
    },
  });
};
