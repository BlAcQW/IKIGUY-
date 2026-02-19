/**
 * User API client for EstateFlow.
 *
 * Provides functions to interact with user and invitation endpoints.
 * Admin-only endpoints for user management and invitations.
 */

import { buildApiUrl, getDefaultHeaders, API_ENDPOINTS } from "../api-config";
import { getAuthTokenSync } from "../auth";

/**
 * User role types.
 */
export type UserRole = "user" | "agent" | "manager" | "admin";

/**
 * User status types.
 */
export type UserStatus = "active" | "invited" | "suspended";

/**
 * User interface.
 */
export interface User {
  id: string;
  email: string;
  name?: string;
  role: UserRole;
  status: UserStatus;
  organization_id: string;
  created_at?: string;
  invited_at?: string;
  last_login?: string;
}

/**
 * User invitation payload.
 */
export interface UserInvite {
  email: string;
  name?: string;
  role: UserRole;
  organization_id: string;
}

/**
 * User update payload.
 */
export interface UserUpdate {
  name?: string;
  role?: UserRole;
  status?: UserStatus;
  organization_id?: string;
}

/**
 * Invitation response.
 */
export interface InvitationResponse {
  message: string;
  email: string;
  organization_id: string;
  role: UserRole;
  token: string;
  expires_at: string;
  invitation_url: string;
}

/**
 * User list response.
 */
export interface UserListResponse {
  users: User[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Pending invitation.
 */
export interface PendingInvitation {
  token: string;
  email: string;
  name?: string;
  role: UserRole;
  organization_id: string;
  created_at: string;
  expires_at: string;
  invited_by?: string;
}

/**
 * Pending invitations response.
 */
export interface PendingInvitationsResponse {
  invitations: PendingInvitation[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Invite a new user (admin only).
 *
 * @param data - User invitation data
 * @returns Invitation response with token
 */
export async function inviteUser(data: UserInvite): Promise<InvitationResponse> {
  const url = buildApiUrl(`${API_ENDPOINTS.users.list}/invite`);
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to invite user" }));
    throw new Error(error.detail || "Failed to invite user");
  }

  return response.json();
}

/**
 * List all users (admin only).
 *
 * @param params - Query parameters
 * @returns List of users
 */
export async function listUsers(params?: {
  limit?: number;
  offset?: number;
  organization_id?: string;
  role?: UserRole;
  status?: UserStatus;
}): Promise<UserListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));
  if (params?.offset !== undefined) queryParams.append("offset", String(params.offset));
  if (params?.organization_id) queryParams.append("organization_id", params.organization_id);
  if (params?.role) queryParams.append("role", params.role);
  if (params?.status) queryParams.append("status", params.status);

  const queryString = queryParams.toString();
  const url = buildApiUrl(`${API_ENDPOINTS.users.list}${queryString ? `?${queryString}` : ""}`);
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to list users" }));
    throw new Error(error.detail || "Failed to list users");
  }

  return response.json();
}

/**
 * Update user details (admin only).
 *
 * @param userId - User ID
 * @param data - User update data
 * @returns Updated user
 */
export async function updateUser(userId: string, data: UserUpdate): Promise<User> {
  const url = buildApiUrl(`${API_ENDPOINTS.users.list}/${userId}`);
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    method: "PUT",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to update user" }));
    throw new Error(error.detail || "Failed to update user");
  }

  return response.json();
}

/**
 * List pending invitations (admin only).
 *
 * @param params - Query parameters
 * @returns List of pending invitations
 */
export async function listPendingInvitations(params?: {
  limit?: number;
  offset?: number;
}): Promise<PendingInvitationsResponse> {
  const queryParams = new URLSearchParams();
  if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));
  if (params?.offset !== undefined) queryParams.append("offset", String(params.offset));

  const queryString = queryParams.toString();
  const url = buildApiUrl(`${API_ENDPOINTS.users.list}/invitations/pending${queryString ? `?${queryString}` : ""}`);
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to list invitations" }));
    throw new Error(error.detail || "Failed to list invitations");
  }

  return response.json();
}

// ========================= SAVED PROPERTIES =========================

/**
 * Saved property interface.
 */
export interface SavedProperty {
  id: string;
  user_id: string;
  property_id: string;
  saved_at: string;
  property?: any; // Full property details if included
}

/**
 * Saved properties list response.
 */
export interface SavedPropertiesListResponse {
  saved_properties: SavedProperty[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Is saved response.
 */
export interface IsSavedResponse {
  is_saved: boolean;
  saved_at?: string;
}

/**
 * Save property response.
 */
export interface SavePropertyResponse {
  message: string;
  id: string;
  property_id: string;
  saved_at: string;
}

/**
 * Save a property to favorites.
 *
 * @param propertyId - Property ID to save
 * @returns Save response
 */
export async function saveProperty(propertyId: string): Promise<SavePropertyResponse> {
  const url = buildApiUrl(API_ENDPOINTS.users.savedProperties.save(propertyId));
  const token = getAuthTokenSync();

  if (!token) {
    throw new Error("Authentication required to save properties");
  }

  const response = await fetch(url, {
    method: "POST",
    headers: getDefaultHeaders(token),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to save property" }));
    throw new Error(error.detail || "Failed to save property");
  }

  return response.json();
}

/**
 * Remove a property from favorites.
 *
 * @param propertyId - Property ID to unsave
 * @returns Unsave response
 */
export async function unsaveProperty(propertyId: string): Promise<{ message: string; property_id: string }> {
  const url = buildApiUrl(API_ENDPOINTS.users.savedProperties.unsave(propertyId));
  const token = getAuthTokenSync();

  if (!token) {
    throw new Error("Authentication required to unsave properties");
  }

  const response = await fetch(url, {
    method: "DELETE",
    headers: getDefaultHeaders(token),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to unsave property" }));
    throw new Error(error.detail || "Failed to unsave property");
  }

  return response.json();
}

/**
 * Get user's saved properties.
 *
 * @param params - Query parameters
 * @returns List of saved properties
 */
export async function getSavedProperties(params?: {
  limit?: number;
  offset?: number;
  include_property_details?: boolean;
}): Promise<SavedPropertiesListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));
  if (params?.offset !== undefined) queryParams.append("offset", String(params.offset));
  if (params?.include_property_details !== undefined) {
    queryParams.append("include_property_details", String(params.include_property_details));
  }

  const queryString = queryParams.toString();
  const url = buildApiUrl(`${API_ENDPOINTS.users.savedProperties.list}${queryString ? `?${queryString}` : ""}`);
  const token = getAuthTokenSync();

  if (!token) {
    throw new Error("Authentication required to get saved properties");
  }

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to get saved properties" }));
    throw new Error(error.detail || "Failed to get saved properties");
  }

  return response.json();
}

/**
 * Check if a property is saved.
 *
 * @param propertyId - Property ID to check
 * @returns Whether property is saved
 */
export async function checkPropertySaved(propertyId: string): Promise<IsSavedResponse> {
  const url = buildApiUrl(API_ENDPOINTS.users.savedProperties.check(propertyId));
  const token = getAuthTokenSync();

  if (!token) {
    // If not authenticated, property is not saved
    return { is_saved: false };
  }

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token),
  });

  if (!response.ok) {
    // If check fails, assume not saved
    return { is_saved: false };
  }

  return response.json();
}

// ========================= BOOKED PROPERTIES =========================

/**
 * Booked property interface (extends Property with booking info).
 */
export interface BookedProperty {
  id: string;
  name: string;
  description?: string;
  location?: string;
  price?: number;
  currency?: string;
  bedrooms?: number;
  bathrooms?: number;
  area_sqm?: number;
  property_type?: string;
  status?: string;
  images?: string[];
  video_url?: string | null;
  booking_count: number;
  latest_booking_date: string;
  latest_booking_status: string;
  [key: string]: any; // For additional property fields
}

/**
 * Get properties that the user has bookings for.
 *
 * Returns properties with booking information using MongoDB aggregation.
 * Excludes cancelled and no-show bookings by default.
 *
 * @param params - Query parameters
 * @param params.status_filter - Optional booking status filter
 * @param params.limit - Maximum number of properties to return (default: 100)
 * @param params.offset - Number of properties to skip for pagination (default: 0)
 * @returns Promise<BookedProperty[]> - List of properties with booking info
 */
export async function getBookedProperties(params?: {
  status_filter?: string;
  limit?: number;
  offset?: number;
}): Promise<BookedProperty[]> {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const queryParams = new URLSearchParams();
  if (params?.status_filter) queryParams.append("status_filter", params.status_filter);
  if (params?.limit) queryParams.append("limit", params.limit.toString());
  if (params?.offset) queryParams.append("offset", params.offset.toString());

  const url = `${API_CONFIG.baseUrl}/users/me/booked-properties${
    queryParams.toString() ? `?${queryParams.toString()}` : ""
  }`;

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Failed to fetch booked properties" }));
    throw new Error(errorData.detail || "Failed to fetch booked properties");
  }

  return response.json();
}

// ========================= USER PROFILE =========================

/**
 * User profile interface.
 */
export interface UserProfile {
  id: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  avatar_url?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

/**
 * User profile update payload.
 */
export interface UserProfileUpdate {
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
}

/**
 * Get current user's profile.
 *
 * @returns User profile
 */
export async function getUserProfile(): Promise<UserProfile> {
  const url = buildApiUrl(`${API_ENDPOINTS.users.list}/me/profile`);
  const token = getAuthTokenSync();

  if (!token) {
    throw new Error("Authentication required to get profile");
  }

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to get profile" }));
    throw new Error(error.detail || "Failed to get profile");
  }

  return response.json();
}

/**
 * Update current user's profile.
 *
 * @param data - Profile fields to update
 * @returns Updated user profile
 */
export async function updateUserProfile(data: UserProfileUpdate): Promise<UserProfile> {
  const url = buildApiUrl(`${API_ENDPOINTS.users.list}/me/profile`);
  const token = getAuthTokenSync();

  if (!token) {
    throw new Error("Authentication required to update profile");
  }

  const response = await fetch(url, {
    method: "PUT",
    headers: getDefaultHeaders(token),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to update profile" }));
    throw new Error(error.detail || "Failed to update profile");
  }

  return response.json();
}
