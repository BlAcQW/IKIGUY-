/**
 * Property API client for EstateFlow.
 *
 * Provides functions to interact with the property endpoints.
 */

import { buildApiUrl, getDefaultHeaders, API_ENDPOINTS, getSelectedOrganizationId, USE_MOCK_DATA } from "../api-config";
import { getAuthTokenSync } from "../auth";
import { mockFetch } from '@/lib/mock-api';
import type {
  Property,
  PropertyCreate,
  PropertyUpdate,
  PropertyListResponse,
  PropertyFilters,
  PropertyStats,
} from "../types/property";

// Helper to choose fetch implementation
const apiFetch = async (url: string, options?: RequestInit) => {
  if (USE_MOCK_DATA) {
    return mockFetch(url, options);
  }
  return fetch(url, options);
};

/**
 * Build query string from filters object.
 *
 * @param filters - Property filters
 * @returns Query string
 */
function buildQueryString(filters?: PropertyFilters): string {
  if (!filters) return "";

  const params = new URLSearchParams();

  if (filters.property_type) {
    filters.property_type.forEach((type) => params.append("property_type", type));
  }
  if (filters.status) {
    filters.status.forEach((status) => params.append("status", status));
  }
  if (filters.min_price !== undefined) params.append("min_price", String(filters.min_price));
  if (filters.max_price !== undefined) params.append("max_price", String(filters.max_price));
  if (filters.min_bedrooms !== undefined) params.append("min_bedrooms", String(filters.min_bedrooms));
  if (filters.max_bedrooms !== undefined) params.append("max_bedrooms", String(filters.max_bedrooms));
  if (filters.min_bathrooms !== undefined) params.append("min_bathrooms", String(filters.min_bathrooms));
  if (filters.max_bathrooms !== undefined) params.append("max_bathrooms", String(filters.max_bathrooms));
  if (filters.city) params.append("city", filters.city);
  if (filters.neighborhood) params.append("neighborhood", filters.neighborhood);
  if (filters.location) params.append("location", filters.location);
  if (filters.pet_policy) {
    filters.pet_policy.forEach((policy) => params.append("pet_policy", policy));
  }
  if (filters.has_pool !== undefined) params.append("has_pool", String(filters.has_pool));
  if (filters.has_garden !== undefined) params.append("has_garden", String(filters.has_garden));
  if (filters.furnished !== undefined) params.append("furnished", String(filters.furnished));
  if (filters.limit !== undefined) params.append("limit", String(filters.limit));
  if (filters.offset !== undefined) params.append("offset", String(filters.offset));
  if (filters.sort_by) params.append("sort_by", filters.sort_by);
  if (filters.sort_order) params.append("sort_order", filters.sort_order);
  if (filters.currency) params.append("currency", filters.currency);

  const queryString = params.toString();
  return queryString ? `?${queryString}` : "";
}

/**
 * List properties with optional filters.
 *
 * @param filters - Property filters
 * @returns Promise<PropertyListResponse>
 */
export async function listProperties(filters?: PropertyFilters): Promise<PropertyListResponse> {
  const queryString = buildQueryString(filters);
  const url = buildApiUrl(`${API_ENDPOINTS.properties.list}${queryString}`);
  const token = getAuthTokenSync();
  const orgId = getSelectedOrganizationId();

  const response = await apiFetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined, orgId || undefined),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to fetch properties" }));
    throw new Error(error.detail || "Failed to fetch properties");
  }

  return response.json();
}

/**
 * Get property by ID.
 *
 * @param id - Property ID
 * @param currency - Optional currency for price conversion
 * @returns Promise<Property>
 */
export async function getProperty(id: string, currency?: string): Promise<Property> {
  const queryString = currency ? `?currency=${currency}` : "";
  const url = buildApiUrl(`${API_ENDPOINTS.properties.get(id)}${queryString}`);
  const token = getAuthTokenSync();
  const orgId = getSelectedOrganizationId();

  const response = await apiFetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined, orgId || undefined),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to fetch property" }));
    throw new Error(error.detail || "Failed to fetch property");
  }

  return response.json();
}

/**
 * Create a new property.
 *
 * @param property - Property creation data
 * @returns Promise<Property>
 */
export async function createProperty(property: PropertyCreate): Promise<Property> {
  const url = buildApiUrl(API_ENDPOINTS.properties.create);
  const token = getAuthTokenSync();

  if (!token) {
    throw new Error("Authentication required to create property");
  }

  const response = await apiFetch(url, {
    method: "POST",
    headers: getDefaultHeaders(token),
    body: JSON.stringify(property),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to create property" }));
    throw new Error(error.detail || "Failed to create property");
  }

  return response.json();
}

/**
 * Update an existing property.
 *
 * @param id - Property ID
 * @param updates - Property updates (partial)
 * @returns Promise<Property>
 */
export async function updateProperty(id: string, updates: PropertyUpdate): Promise<Property> {
  const url = buildApiUrl(API_ENDPOINTS.properties.update(id));
  const token = getAuthTokenSync();

  if (!token) {
    throw new Error("Authentication required to update property");
  }

  const response = await apiFetch(url, {
    method: "PUT",
    headers: getDefaultHeaders(token),
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to update property" }));
    throw new Error(error.detail || "Failed to update property");
  }

  return response.json();
}

/**
 * Delete a property (soft delete).
 *
 * @param id - Property ID
 * @returns Promise<void>
 */
export async function deleteProperty(id: string): Promise<void> {
  const url = buildApiUrl(API_ENDPOINTS.properties.delete(id));
  const token = getAuthTokenSync();

  if (!token) {
    throw new Error("Authentication required to delete property");
  }

  const response = await apiFetch(url, {
    method: "DELETE",
    headers: getDefaultHeaders(token),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to delete property" }));
    throw new Error(error.detail || "Failed to delete property");
  }
}

/**
 * Search properties with full-text search.
 *
 * @param query - Search query string
 * @param filters - Additional filters
 * @returns Promise<PropertyListResponse>
 */
export async function searchProperties(
  query: string,
  filters?: PropertyFilters
): Promise<PropertyListResponse> {
  const params = new URLSearchParams({ q: query });

  // Add filters to query string
  if (filters) {
    if (filters.property_type) {
      filters.property_type.forEach((type) => params.append("property_type", type));
    }
    if (filters.status) {
      filters.status.forEach((status) => params.append("status", status));
    }
    if (filters.min_price !== undefined) params.append("min_price", String(filters.min_price));
    if (filters.max_price !== undefined) params.append("max_price", String(filters.max_price));
    if (filters.city) params.append("city", filters.city);
    if (filters.limit !== undefined) params.append("limit", String(filters.limit));
    if (filters.offset !== undefined) params.append("offset", String(filters.offset));
    if (filters.currency) params.append("currency", filters.currency);
  }

  const url = buildApiUrl(`${API_ENDPOINTS.properties.search}?${params.toString()}`);
  const token = getAuthTokenSync();

  const response = await apiFetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to search properties" }));
    throw new Error(error.detail || "Failed to search properties");
  }

  return response.json();
}

/**
 * Get property statistics by status.
 *
 * @returns Promise<PropertyStats>
 */
export async function getPropertyStats(): Promise<PropertyStats> {
  // Since the backend doesn't have a dedicated stats endpoint yet,
  // we'll calculate stats from the properties list
  const url = buildApiUrl(API_ENDPOINTS.properties.list);
  const token = getAuthTokenSync();

  if (!token) {
    throw new Error("Authentication required to fetch property stats");
  }

  const response = await apiFetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to fetch property stats" }));
    throw new Error(error.detail || "Failed to fetch property stats");
  }

  const data: PropertyListResponse = await response.json();
  const properties = data.properties;

  // Calculate statistics
  const total = properties.length;
  const active = properties.filter(p => p.status === 'active').length;
  const pending = properties.filter(p => p.status === 'pending').length;
  const sold = properties.filter(p => p.status === 'sold').length;
  const rented = properties.filter(p => p.status === 'rented').length;
  const inactive = properties.filter(p => p.status === 'inactive').length;

  const totalValue = properties.reduce((sum, p) => sum + p.financial.price_usd, 0);
  const averagePrice = total > 0 ? totalValue / total : 0;

  // Group by property type
  const byType: Record<string, number> = {};
  properties.forEach(p => {
    byType[p.property_type] = (byType[p.property_type] || 0) + 1;
  });

  return {
    total,
    active,
    pending,
    sold,
    rented,
    inactive,
    total_value: totalValue,
    average_price: averagePrice,
    by_type: byType,
  };
}
