/**
 * React Query hooks for payment operations.
 *
 * Wraps payment API functions with React Query for caching,
 * loading states, and automatic cache invalidation.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listPayments,
  getPayment,
  getPaymentStats,
  createPayment,
  createPaymentIntent,
  confirmPayment,
  refundPayment,
  type Payment,
  type PaymentListResponse,
  type PaymentStats,
  type PaymentIntent,
  type CreatePaymentData,
  type ConfirmPaymentData,
  type RefundPaymentData,
  type PaymentStatus,
  type PaymentMethod,
  type PaymentGateway,
} from '@/lib/api/payment-api';

// ==================== Types ====================

export interface PaymentFilters {
  status?: PaymentStatus;
  payment_method?: PaymentMethod;
  gateway?: PaymentGateway;
  customer_id?: string;
  property_id?: string;
  invoice_id?: string;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// ==================== Query Keys ====================

export const paymentKeys = {
  all: ['payments'] as const,
  lists: () => [...paymentKeys.all, 'list'] as const,
  list: (filters?: PaymentFilters) => [...paymentKeys.lists(), filters] as const,
  details: () => [...paymentKeys.all, 'detail'] as const,
  detail: (id: string) => [...paymentKeys.details(), id] as const,
  stats: () => [...paymentKeys.all, 'stats'] as const,
};

// ==================== Query Hooks ====================

/**
 * Hook to list payments with filters and pagination.
 */
export function usePayments(filters?: PaymentFilters) {
  return useQuery({
    queryKey: paymentKeys.list(filters),
    queryFn: () => listPayments(filters),
    staleTime: 1000 * 60 * 2,
  });
}

/**
 * Hook to get a single payment by ID.
 */
export function usePayment(id: string) {
  return useQuery({
    queryKey: paymentKeys.detail(id),
    queryFn: () => getPayment(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 2,
  });
}

/**
 * Hook to get payment statistics.
 */
export function usePaymentStats(currency: string = 'GHS') {
  return useQuery({
    queryKey: paymentKeys.stats(),
    queryFn: () => getPaymentStats(currency),
    staleTime: 1000 * 60 * 5,
  });
}

// ==================== Mutation Hooks ====================

/**
 * Hook to create a new payment.
 */
export function useCreatePayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreatePaymentData) => createPayment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: paymentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: paymentKeys.stats() });
    },
  });
}

/**
 * Hook to create a payment intent.
 */
export function useCreatePaymentIntent() {
  return useMutation({
    mutationFn: (paymentId: string) => createPaymentIntent(paymentId),
  });
}

/**
 * Hook to confirm a payment.
 */
export function useConfirmPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ paymentId, data }: { paymentId: string; data?: ConfirmPaymentData }) =>
      confirmPayment(paymentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: paymentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: paymentKeys.stats() });
    },
  });
}

/**
 * Hook to refund a payment.
 */
export function useRefundPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ paymentId, data }: { paymentId: string; data: RefundPaymentData }) =>
      refundPayment(paymentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: paymentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: paymentKeys.stats() });
    },
  });
}
