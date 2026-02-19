/**
 * Booking API client for EstateFlow.
 *
 * Provides functions to interact with the booking endpoints.
 */

import { buildApiUrl, getDefaultHeaders, API_ENDPOINTS } from "../api-config";
import { getAuthTokenSync } from "../auth";

/**
 * Get authentication token from localStorage or session storage.
 * TODO: Replace with actual auth implementation
 */

// ==================== Types ====================

export type BookingType = "in-person" | "virtual";

export type BookingStatus =
  | "requested"
  | "confirmed"
  | "rescheduled"
  | "completed"
  | "cancelled"
  | "no-show";

export interface Reminder {
  type: string;
  scheduled_at: string;
  sent_at?: string;
  status: "pending" | "sent" | "failed";
  channel: string;
  message_id?: string;
}

export interface Booking {
  id: string;
  organization_id: string;
  property_id: string;
  contact_id: string;
  agent_id?: string;
  scheduled_at: string;
  duration_minutes: number;
  booking_type: BookingType;
  status: BookingStatus;
  contact_name: string;
  contact_email?: string;
  contact_phone?: string;
  notes?: string;
  internal_notes?: string;
  meeting_link?: string;
  meeting_id?: string;
  meeting_password?: string;
  reminders: Reminder[];
  rating?: number;
  feedback?: string;
  created_at: string;
  updated_at: string;
  confirmed_at?: string;
  completed_at?: string;
  cancelled_at?: string;
  // Admin audit trail fields
  admin_override?: boolean;
  admin_override_reason?: string;
  reassigned_by?: string;
  reassigned_at?: string;
  manually_created_by?: string;
}

export interface BookingCreate {
  property_id: string;
  contact_id?: string;
  scheduled_at: string;
  duration_minutes?: number;
  booking_type?: BookingType;
  contact_name: string;
  contact_email?: string;
  contact_phone?: string;
  notes?: string;
}

export interface BookingUpdate {
  scheduled_at?: string;
  duration_minutes?: number;
  status?: BookingStatus;
  agent_id?: string;
  notes?: string;
  internal_notes?: string;
  rating?: number;
  feedback?: string;
  meeting_link?: string;
}

export interface AvailabilitySlot {
  start_time: string;
  end_time: string;
  available: boolean;
  agent_id?: string;
  reason?: string;
}

export interface AvailabilityRequest {
  property_id: string;
  start_date: string;
  end_date: string;
  duration_minutes?: number;
}

export interface AvailabilityResponse {
  property_id: string;
  slots: AvailabilitySlot[];
}

export interface BookingListResponse {
  bookings: Booking[];
  total: number;
  limit: number;
  offset: number;
}

export interface BookingFilters {
  property_id?: string;
  contact_id?: string;
  agent_id?: string;
  status?: BookingStatus;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

// ==================== Admin Types ====================

export interface AdminCreateBookingRequest extends BookingCreate {
  admin_override?: boolean;
  admin_override_reason?: string;
}

export interface BulkActionRequest {
  booking_ids: string[];
  action: "approve" | "reject" | "cancel" | "reschedule";
  reason?: string;
}

export interface BulkActionResponse {
  success_count: number;
  failed_count: number;
  failed_bookings: Array<{ id: string; reason: string }>;
  message: string;
}

export interface ActionLog {
  id: string;
  booking_id: string;
  organization_id: string;
  action_type: string;
  admin_email: string;
  admin_id: string;
  details: Record<string, any>;
  timestamp: string;
}

// ==================== API Functions ====================

/**
 * Create a new booking.
 *
 * @param booking - Booking data
 * @returns Created booking
 */
export async function createBooking(booking: BookingCreate): Promise<Booking> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.bookings.create), {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(booking),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to create booking");
  }

  return response.json();
}

/**
 * List bookings with optional filters.
 *
 * @param filters - Optional filters
 * @returns List of bookings
 */
export async function listBookings(filters?: BookingFilters): Promise<BookingListResponse> {
  const token = getAuthTokenSync();
  const params = new URLSearchParams();

  if (filters?.property_id) params.append("property_id", filters.property_id);
  if (filters?.contact_id) params.append("contact_id", filters.contact_id);
  if (filters?.agent_id) params.append("agent_id", filters.agent_id);
  if (filters?.status) params.append("status", filters.status);
  if (filters?.start_date) params.append("start_date", filters.start_date);
  if (filters?.end_date) params.append("end_date", filters.end_date);
  if (filters?.limit) params.append("limit", String(filters.limit));
  if (filters?.offset) params.append("offset", String(filters.offset));

  const url = `${buildApiUrl(API_ENDPOINTS.bookings.list)}?${params.toString()}`;
  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch bookings");
  }

  return response.json();
}

/**
 * Get booking by ID.
 *
 * @param bookingId - Booking ID
 * @returns Booking details
 */
export async function getBooking(bookingId: string): Promise<Booking> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.bookings.get(bookingId)), {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch booking");
  }

  return response.json();
}

/**
 * Update booking.
 *
 * @param bookingId - Booking ID
 * @param updates - Updates to apply
 * @returns Updated booking
 */
export async function updateBooking(bookingId: string, updates: BookingUpdate): Promise<Booking> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.bookings.update(bookingId)), {
    method: "PUT",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update booking");
  }

  return response.json();
}

/**
 * Cancel booking.
 *
 * @param bookingId - Booking ID
 * @returns Cancelled booking
 */
export async function cancelBooking(bookingId: string): Promise<Booking> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.bookings.cancel(bookingId)), {
    method: "DELETE",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to cancel booking");
  }

  return response.json();
}

/**
 * Confirm booking (agent action).
 *
 * @param bookingId - Booking ID
 * @returns Confirmed booking
 */
export async function confirmBooking(bookingId: string): Promise<Booking> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.bookings.confirm(bookingId)), {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to confirm booking");
  }

  return response.json();
}

/**
 * Complete booking with optional rating and feedback.
 *
 * @param bookingId - Booking ID
 * @param rating - Customer rating (1-5)
 * @param feedback - Customer feedback
 * @returns Completed booking
 */
export async function completeBooking(
  bookingId: string,
  rating?: number,
  feedback?: string
): Promise<Booking> {
  const token = getAuthTokenSync();
  const params = new URLSearchParams();
  if (rating) params.append("rating", String(rating));
  if (feedback) params.append("feedback", feedback);

  const url = `${buildApiUrl(API_ENDPOINTS.bookings.complete(bookingId))}?${params.toString()}`;
  const response = await fetch(url, {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to complete booking");
  }

  return response.json();
}

/**
 * Mark booking as no-show.
 *
 * @param bookingId - Booking ID
 * @returns Updated booking
 */
export async function markNoShow(bookingId: string): Promise<Booking> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.bookings.noShow(bookingId)), {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to mark as no-show");
  }

  return response.json();
}

/**
 * Get available time slots for a property.
 *
 * @param request - Availability request
 * @returns Available slots
 */
export async function getAvailability(request: AvailabilityRequest): Promise<AvailabilityResponse> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.bookings.availability), {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to get availability");
  }

  return response.json();
}

/**
 * Get available slots for a specific property (GET version).
 *
 * @param propertyId - Property ID
 * @param startDate - Start date (ISO string)
 * @param endDate - End date (ISO string)
 * @param durationMinutes - Duration in minutes
 * @returns Available slots
 */
export async function getPropertyAvailability(
  propertyId: string,
  startDate: string,
  endDate: string,
  durationMinutes: number = 30
): Promise<AvailabilityResponse> {
  const token = getAuthTokenSync();
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
    duration_minutes: String(durationMinutes),
  });

  const url = `${buildApiUrl(API_ENDPOINTS.bookings.propertyAvailability(propertyId))}?${params.toString()}`;
  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to get property availability");
  }

  return response.json();
}

// ==================== Admin API Functions ====================

/**
 * Admin-only: Manually create booking with optional availability override.
 *
 * Allows admin to:
 * - Create bookings even if slot is unavailable
 * - Manually assign agent
 * - Skip auto-assignment logic
 *
 * @param booking - Booking data
 * @param overrideAvailability - Whether to bypass availability check
 * @returns Created booking
 */
export async function adminCreateBooking(
  booking: AdminCreateBookingRequest,
  overrideAvailability: boolean = false
): Promise<Booking> {
  const token = getAuthTokenSync();
  const params = new URLSearchParams();
  if (overrideAvailability) {
    params.append("override_availability", "true");
  }

  const url = `${buildApiUrl(API_ENDPOINTS.bookings.admin.manualCreate)}?${params.toString()}`;
  const response = await fetch(url, {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(booking),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to create booking");
  }

  return response.json();
}

/**
 * Admin-only: Reassign booking to a different agent.
 *
 * Bypasses normal agent availability checks.
 *
 * @param bookingId - Booking ID
 * @param newAgentId - New agent ID
 * @returns Updated booking
 */
export async function adminReassignAgent(
  bookingId: string,
  newAgentId: string
): Promise<Booking> {
  const token = getAuthTokenSync();
  const params = new URLSearchParams();
  params.append("new_agent_id", newAgentId);

  const url = `${buildApiUrl(API_ENDPOINTS.bookings.admin.reassignAgent(bookingId))}?${params.toString()}`;
  const response = await fetch(url, {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to reassign agent");
  }

  return response.json();
}

/**
 * Admin-only: Perform bulk action on multiple bookings.
 *
 * Supported actions:
 * - approve: Confirm multiple bookings
 * - reject: Cancel multiple bookings
 * - cancel: Cancel multiple bookings
 *
 * @param request - Bulk action request
 * @returns Bulk action response with success/failure counts
 */
export async function adminBulkAction(
  request: BulkActionRequest
): Promise<BulkActionResponse> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.bookings.admin.bulkAction), {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to perform bulk action");
  }

  return response.json();
}

/**
 * Admin-only: Get audit trail for a booking.
 *
 * Returns all admin actions performed on this booking.
 *
 * @param bookingId - Booking ID
 * @returns Array of action logs
 */
export async function getBookingActionLogs(bookingId: string): Promise<ActionLog[]> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.bookings.admin.actionLogs(bookingId)), {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to get action logs");
  }

  const data = await response.json();
  return data.logs || [];
}
