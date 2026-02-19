/**
 * React Query hooks for booking management.
 */

import { useQuery, useMutation, useQueryClient, UseQueryResult, UseMutationResult } from "@tanstack/react-query";
import {
  listBookings,
  getBooking,
  createBooking,
  updateBooking,
  cancelBooking,
  confirmBooking,
  completeBooking,
  markNoShow,
  getAvailability,
  getPropertyAvailability,
  adminCreateBooking,
  adminReassignAgent,
  adminBulkAction,
  getBookingActionLogs,
  type Booking,
  type BookingCreate,
  type BookingUpdate,
  type BookingListResponse,
  type BookingFilters,
  type AvailabilityRequest,
  type AvailabilityResponse,
  type AdminCreateBookingRequest,
  type BulkActionRequest,
  type BulkActionResponse,
  type ActionLog,
} from "../lib/api/booking-api";

// ==================== Query Hooks ====================

/**
 * Hook to list bookings with optional filters.
 *
 * @param filters - Optional filters
 * @returns Query result with bookings
 */
export function useBookings(filters?: BookingFilters): UseQueryResult<BookingListResponse, Error> {
  return useQuery({
    queryKey: ["bookings", filters],
    queryFn: () => listBookings(filters),
  });
}

/**
 * Hook to get a single booking by ID.
 *
 * @param bookingId - Booking ID
 * @param enabled - Whether the query should execute
 * @returns Query result with booking details
 */
export function useBooking(bookingId: string, enabled: boolean = true): UseQueryResult<Booking, Error> {
  return useQuery({
    queryKey: ["booking", bookingId],
    queryFn: () => getBooking(bookingId),
    enabled: enabled && !!bookingId,
  });
}

/**
 * Hook to get available time slots for a property.
 *
 * @param request - Availability request
 * @param enabled - Whether the query should execute
 * @returns Query result with available slots
 */
export function useAvailability(
  request: AvailabilityRequest,
  enabled: boolean = true
): UseQueryResult<AvailabilityResponse, Error> {
  return useQuery({
    queryKey: ["availability", request],
    queryFn: () => getAvailability(request),
    enabled: enabled && !!request.property_id,
  });
}

/**
 * Hook to get available slots for a specific property (GET version).
 *
 * @param propertyId - Property ID
 * @param startDate - Start date
 * @param endDate - End date
 * @param durationMinutes - Duration in minutes
 * @param enabled - Whether the query should execute
 * @returns Query result with available slots
 */
export function usePropertyAvailability(
  propertyId: string,
  startDate: string,
  endDate: string,
  durationMinutes: number = 30,
  enabled: boolean = true
): UseQueryResult<AvailabilityResponse, Error> {
  return useQuery({
    queryKey: ["propertyAvailability", propertyId, startDate, endDate, durationMinutes],
    queryFn: () => getPropertyAvailability(propertyId, startDate, endDate, durationMinutes),
    enabled: enabled && !!propertyId,
  });
}

// ==================== Mutation Hooks ====================

/**
 * Hook to create a new booking.
 *
 * @returns Mutation for creating booking
 */
export function useCreateBooking(): UseMutationResult<Booking, Error, BookingCreate> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createBooking,
    onSuccess: () => {
      // Invalidate bookings list to refetch
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["availability"] });
      queryClient.invalidateQueries({ queryKey: ["propertyAvailability"] });
    },
  });
}

/**
 * Hook to update a booking.
 *
 * @returns Mutation for updating booking
 */
export function useUpdateBooking(): UseMutationResult<
  Booking,
  Error,
  { bookingId: string; updates: BookingUpdate }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ bookingId, updates }) => updateBooking(bookingId, updates),
    onSuccess: (data) => {
      // Update cache for this specific booking
      queryClient.setQueryData(["booking", data.id], data);
      // Invalidate bookings list
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["availability"] });
    },
  });
}

/**
 * Hook to cancel a booking.
 *
 * @returns Mutation for cancelling booking
 */
export function useCancelBooking(): UseMutationResult<Booking, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelBooking,
    onSuccess: (data) => {
      queryClient.setQueryData(["booking", data.id], data);
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["availability"] });
      queryClient.invalidateQueries({ queryKey: ["propertyAvailability"] });
    },
  });
}

/**
 * Hook to confirm a booking (agent action).
 *
 * @returns Mutation for confirming booking
 */
export function useConfirmBooking(): UseMutationResult<Booking, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: confirmBooking,
    onSuccess: (data) => {
      queryClient.setQueryData(["booking", data.id], data);
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
    },
  });
}

/**
 * Hook to complete a booking with optional rating and feedback.
 *
 * @returns Mutation for completing booking
 */
export function useCompleteBooking(): UseMutationResult<
  Booking,
  Error,
  { bookingId: string; rating?: number; feedback?: string }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ bookingId, rating, feedback }) => completeBooking(bookingId, rating, feedback),
    onSuccess: (data) => {
      queryClient.setQueryData(["booking", data.id], data);
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
    },
  });
}

/**
 * Hook to mark a booking as no-show.
 *
 * @returns Mutation for marking booking as no-show
 */
export function useMarkNoShow(): UseMutationResult<Booking, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: markNoShow,
    onSuccess: (data) => {
      queryClient.setQueryData(["booking", data.id], data);
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
    },
  });
}

// ==================== Admin Hooks ====================

/**
 * Hook to manually create booking with optional availability override (admin-only).
 *
 * Allows admin to:
 * - Create bookings even if slot is unavailable
 * - Manually assign agent
 * - Skip auto-assignment logic
 *
 * @returns Mutation for admin booking creation
 */
export function useAdminCreateBooking(): UseMutationResult<
  Booking,
  Error,
  { booking: AdminCreateBookingRequest; overrideAvailability?: boolean }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ booking, overrideAvailability }) => adminCreateBooking(booking, overrideAvailability),
    onSuccess: () => {
      // Invalidate bookings list to refetch
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["availability"] });
      queryClient.invalidateQueries({ queryKey: ["propertyAvailability"] });
    },
  });
}

/**
 * Hook to reassign booking to a different agent (admin-only).
 *
 * @returns Mutation for agent reassignment
 */
export function useAdminReassignAgent(): UseMutationResult<
  Booking,
  Error,
  { bookingId: string; newAgentId: string }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ bookingId, newAgentId }) => adminReassignAgent(bookingId, newAgentId),
    onSuccess: (data) => {
      // Update cache for this specific booking
      queryClient.setQueryData(["booking", data.id], data);
      // Invalidate bookings list and action logs
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["bookingActionLogs", data.id] });
    },
  });
}

/**
 * Hook to perform bulk action on multiple bookings (admin-only).
 *
 * Supported actions:
 * - approve: Confirm multiple bookings
 * - reject: Cancel multiple bookings
 * - cancel: Cancel multiple bookings
 *
 * @returns Mutation for bulk actions
 */
export function useAdminBulkAction(): UseMutationResult<
  BulkActionResponse,
  Error,
  BulkActionRequest
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: adminBulkAction,
    onSuccess: () => {
      // Invalidate all bookings-related queries
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["booking"] });
      queryClient.invalidateQueries({ queryKey: ["bookingActionLogs"] });
    },
  });
}

/**
 * Hook to get audit trail for a booking (admin-only).
 *
 * Returns all admin actions performed on this booking.
 *
 * @param bookingId - Booking ID
 * @param enabled - Whether the query should execute
 * @returns Query result with action logs
 */
export function useBookingActionLogs(
  bookingId: string,
  enabled: boolean = true
): UseQueryResult<ActionLog[], Error> {
  return useQuery({
    queryKey: ["bookingActionLogs", bookingId],
    queryFn: () => getBookingActionLogs(bookingId),
    enabled: enabled && !!bookingId,
  });
}
