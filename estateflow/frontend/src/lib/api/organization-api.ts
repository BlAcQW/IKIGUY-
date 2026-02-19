/**
 * Organization API client for EstateFlow.
 *
 * Provides functions to interact with the organization endpoints.
 * Admin-only endpoints for organization CRUD operations.
 */

import { buildApiUrl, getDefaultHeaders, API_ENDPOINTS } from "../api-config";
import { getAuthTokenSync } from "../auth";

/**
 * Organization interface matching backend model.
 */
export interface Organization {
  id: string;
  name: string;
  description?: string;
  email?: string;
  phone?: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * Organization create payload.
 */
export interface OrganizationCreate {
  name: string;
  description?: string;
  email?: string;
  phone?: string;
}

/**
 * Organization update payload.
 */
export interface OrganizationUpdate {
  name?: string;
  description?: string;
  email?: string;
  phone?: string;
}

/**
 * Organization list response.
 */
export interface OrganizationListResponse {
  organizations: Organization[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * List all organizations (admin only).
 *
 * @param limit - Page size
 * @param offset - Page offset
 * @returns List of organizations
 */
export async function listOrganizations(
  limit: number = 100,
  offset: number = 0
): Promise<OrganizationListResponse> {
  const url = buildApiUrl(`${API_ENDPOINTS.organizations.list}?limit=${limit}&offset=${offset}`);
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to list organizations" }));
    throw new Error(error.detail || "Failed to list organizations");
  }

  return response.json();
}

/**
 * Get organization by ID.
 *
 * @param organizationId - Organization ID
 * @returns Organization details
 */
export async function getOrganization(organizationId: string): Promise<Organization> {
  const url = buildApiUrl(`${API_ENDPOINTS.organizations.list}/${organizationId}`);
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to get organization" }));
    throw new Error(error.detail || "Failed to get organization");
  }

  return response.json();
}

/**
 * Create new organization (admin only).
 *
 * @param data - Organization creation data
 * @returns Created organization
 */
export async function createOrganization(data: OrganizationCreate): Promise<Organization> {
  const url = buildApiUrl(API_ENDPOINTS.organizations.list);
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to create organization" }));
    throw new Error(error.detail || "Failed to create organization");
  }

  return response.json();
}

/**
 * Update organization (admin only).
 *
 * @param organizationId - Organization ID
 * @param data - Organization update data
 * @returns Updated organization
 */
export async function updateOrganization(
  organizationId: string,
  data: OrganizationUpdate
): Promise<Organization> {
  const url = buildApiUrl(`${API_ENDPOINTS.organizations.list}/${organizationId}`);
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    method: "PUT",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to update organization" }));
    throw new Error(error.detail || "Failed to update organization");
  }

  return response.json();
}

/**
 * Delete organization (admin only).
 *
 * @param organizationId - Organization ID
 */
export async function deleteOrganization(organizationId: string): Promise<void> {
  const url = buildApiUrl(`${API_ENDPOINTS.organizations.list}/${organizationId}`);
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    method: "DELETE",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to delete organization" }));
    throw new Error(error.detail || "Failed to delete organization");
  }
}
