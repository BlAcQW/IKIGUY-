/**
 * Search API client for EstateFlow.
 *
 * AI-powered property search with natural language processing.
 */

import { buildApiUrl, getDefaultHeaders, API_ENDPOINTS } from "../api-config";
import { getAuthTokenSync } from "../auth";

/**
 * Get authentication token from localStorage or session storage.
 * TODO: Replace with actual auth implementation
 */

// ==================== Types ====================

export type SearchIntent =
  | "browse"
  | "specific_property"
  | "investment"
  | "urgent"
  | "budget_focused"
  | "location_focused"
  | "amenity_focused";

export type PropertyType =
  | "apartment"
  | "house"
  | "villa"
  | "penthouse"
  | "loft"
  | "townhouse"
  | "land"
  | "commercial";

export type PetPolicy = "allowed" | "not_allowed" | "conditional";

export interface ParsedSearchQuery {
  original_query: string;
  intent: SearchIntent;
  confidence: number;
  property_types: PropertyType[];
  locations: string[];
  min_price?: number;
  max_price?: number;
  min_bedrooms?: number;
  max_bedrooms?: number;
  min_bathrooms?: number;
  min_sqft?: number;
  max_sqft?: number;
  must_have_amenities: string[];
  nice_to_have_amenities: string[];
  pet_policy?: PetPolicy;
  furnished?: boolean;
  semantic_keywords: string[];
  language: string;
  parsed_at: string;
}

export interface SearchFilters {
  property_types?: PropertyType[];
  locations?: string[];
  min_price?: number;
  max_price?: number;
  min_bedrooms?: number;
  max_bedrooms?: number;
  min_bathrooms?: number;
  min_sqft?: number;
  max_sqft?: number;
  amenities?: string[];
  pet_policy?: PetPolicy;
  furnished?: boolean;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

export interface SearchRequest {
  query?: string;
  filters?: SearchFilters;
  use_semantic_search?: boolean;
  currency?: string;
}

export interface PropertyMatch {
  property_id: string;
  relevance_score: number;
  semantic_score?: number;
  filter_score: number;
  match_reasons: string[];
  missing_criteria: string[];
  property_data: any; // Full property object
}

export interface SearchResponse {
  matches: PropertyMatch[];
  total: number;
  parsed_query?: ParsedSearchQuery;
  applied_filters: Record<string, any>;
  search_time_ms: number;
  used_semantic_search: boolean;
  suggested_refinements: string[];
  alternative_locations: string[];
  limit: number;
  offset: number;
}

export interface PopularSearch {
  query: string;
  count: number;
}

export interface ZeroResultSearch {
  query: string;
  parsed_query?: ParsedSearchQuery;
  timestamp: string;
}

export interface SearchPerformance {
  total_searches: number;
  avg_search_time_ms: number;
  avg_results: number;
  zero_results_rate: number;
}

export interface LocationSuggestion {
  suggestions: string[];
}

export interface AmenitySuggestion {
  suggestions: string[];
}

// ==================== API Functions ====================

/**
 * Search properties with natural language or structured filters.
 *
 * @param request - Search request
 * @returns Search results
 */
export async function searchProperties(request: SearchRequest): Promise<SearchResponse> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.search.query), {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Search failed");
  }

  return response.json();
}

/**
 * Search properties using GET request (URL-based).
 *
 * @param query - Natural language query
 * @param filters - Optional filters
 * @returns Search results
 */
export async function searchPropertiesGet(
  query: string,
  filters?: Partial<SearchFilters>
): Promise<SearchResponse> {
  const token = getAuthTokenSync();
  const params = new URLSearchParams({ query });

  if (filters?.property_types) {
    filters.property_types.forEach((type) => params.append("property_type", type));
  }
  if (filters?.locations) {
    filters.locations.forEach((loc) => params.append("location", loc));
  }
  if (filters?.min_price !== undefined) params.append("min_price", String(filters.min_price));
  if (filters?.max_price !== undefined) params.append("max_price", String(filters.max_price));
  if (filters?.min_bedrooms !== undefined)
    params.append("min_bedrooms", String(filters.min_bedrooms));
  if (filters?.max_bedrooms !== undefined)
    params.append("max_bedrooms", String(filters.max_bedrooms));
  if (filters?.min_bathrooms !== undefined)
    params.append("min_bathrooms", String(filters.min_bathrooms));
  if (filters?.amenities) {
    filters.amenities.forEach((amenity) => params.append("amenities", amenity));
  }
  if (filters?.pet_policy) params.append("pet_policy", filters.pet_policy);
  if (filters?.furnished !== undefined) params.append("furnished", String(filters.furnished));
  if (filters?.sort_by) params.append("sort_by", filters.sort_by);
  if (filters?.sort_order) params.append("sort_order", filters.sort_order);
  if (filters?.limit) params.append("limit", String(filters.limit));
  if (filters?.offset) params.append("offset", String(filters.offset));

  const url = `${buildApiUrl(API_ENDPOINTS.search.query)}?${params.toString()}`;
  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Search failed");
  }

  return response.json();
}

/**
 * Get popular searches.
 *
 * @param limit - Number of results
 * @returns Popular searches
 */
export async function getPopularSearches(limit: number = 10): Promise<{ popular_searches: PopularSearch[] }> {
  const token = getAuthTokenSync();
  const url = `${buildApiUrl(API_ENDPOINTS.search.popularSearches)}?limit=${limit}`;
  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch popular searches");
  }

  return response.json();
}

/**
 * Get searches that returned zero results.
 *
 * @param limit - Number of results
 * @returns Zero result searches
 */
export async function getZeroResultSearches(
  limit: number = 10
): Promise<{ zero_result_searches: ZeroResultSearch[] }> {
  const token = getAuthTokenSync();
  const url = `${buildApiUrl(API_ENDPOINTS.search.zeroResults)}?limit=${limit}`;
  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch zero result searches");
  }

  return response.json();
}

/**
 * Get search performance metrics.
 *
 * @returns Search performance stats
 */
export async function getSearchPerformance(): Promise<SearchPerformance> {
  const token = getAuthTokenSync();
  const response = await fetch(buildApiUrl(API_ENDPOINTS.search.performance), {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch search performance");
  }

  return response.json();
}

/**
 * Get location autocomplete suggestions.
 *
 * @param query - Location search query
 * @param limit - Number of suggestions
 * @returns Location suggestions
 */
export async function getLocationSuggestions(
  query: string,
  limit: number = 10
): Promise<LocationSuggestion> {
  const token = getAuthTokenSync();
  const params = new URLSearchParams({ query, limit: String(limit) });
  const url = `${buildApiUrl(API_ENDPOINTS.search.locationSuggestions)}?${params.toString()}`;

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch location suggestions");
  }

  return response.json();
}

/**
 * Get amenity suggestions.
 *
 * @param query - Optional amenity search query
 * @param limit - Number of suggestions
 * @returns Amenity suggestions
 */
export async function getAmenitySuggestions(
  query: string = "",
  limit: number = 10
): Promise<AmenitySuggestion> {
  const token = getAuthTokenSync();
  const params = new URLSearchParams({ query, limit: String(limit) });
  const url = `${buildApiUrl(API_ENDPOINTS.search.amenitySuggestions)}?${params.toString()}`;

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch amenity suggestions");
  }

  return response.json();
}
