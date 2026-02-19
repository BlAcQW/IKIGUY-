/**
 * React Query hooks for AI property search.
 */

import { useQuery, useMutation, useQueryClient, UseQueryResult, UseMutationResult } from "@tanstack/react-query";
import {
  searchProperties,
  searchPropertiesGet,
  getPopularSearches,
  getZeroResultSearches,
  getSearchPerformance,
  getLocationSuggestions,
  getAmenitySuggestions,
  type SearchRequest,
  type SearchResponse,
  type SearchFilters,
  type PopularSearch,
  type ZeroResultSearch,
  type SearchPerformance,
  type LocationSuggestion,
  type AmenitySuggestion,
} from "../lib/api/search-api";

// ==================== Query Hooks ====================

/**
 * Hook to search properties with natural language or structured filters.
 *
 * Note: This is a mutation, not a query, because search requests
 * should not be automatically retried or cached indefinitely.
 *
 * @returns Mutation for searching properties
 */
export function useSearchProperties(): UseMutationResult<SearchResponse, Error, SearchRequest> {
  return useMutation({
    mutationFn: searchProperties,
  });
}

/**
 * Hook to get popular searches.
 *
 * @param limit - Number of results
 * @returns Query result with popular searches
 */
export function usePopularSearches(
  limit: number = 10
): UseQueryResult<{ popular_searches: PopularSearch[] }, Error> {
  return useQuery({
    queryKey: ["popularSearches", limit],
    queryFn: () => getPopularSearches(limit),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get searches that returned zero results.
 *
 * @param limit - Number of results
 * @returns Query result with zero result searches
 */
export function useZeroResultSearches(
  limit: number = 10
): UseQueryResult<{ zero_result_searches: ZeroResultSearch[] }, Error> {
  return useQuery({
    queryKey: ["zeroResultSearches", limit],
    queryFn: () => getZeroResultSearches(limit),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get search performance metrics.
 *
 * @returns Query result with search performance
 */
export function useSearchPerformance(): UseQueryResult<SearchPerformance, Error> {
  return useQuery({
    queryKey: ["searchPerformance"],
    queryFn: getSearchPerformance,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get location autocomplete suggestions.
 *
 * @param query - Location search query
 * @param limit - Number of suggestions
 * @param enabled - Whether the query should execute
 * @returns Query result with location suggestions
 */
export function useLocationSuggestions(
  query: string,
  limit: number = 10,
  enabled: boolean = true
): UseQueryResult<LocationSuggestion, Error> {
  return useQuery({
    queryKey: ["locationSuggestions", query, limit],
    queryFn: () => getLocationSuggestions(query, limit),
    enabled: enabled && query.length > 0,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to get amenity suggestions.
 *
 * @param query - Optional amenity search query
 * @param limit - Number of suggestions
 * @returns Query result with amenity suggestions
 */
export function useAmenitySuggestions(
  query: string = "",
  limit: number = 10
): UseQueryResult<AmenitySuggestion, Error> {
  return useQuery({
    queryKey: ["amenitySuggestions", query, limit],
    queryFn: () => getAmenitySuggestions(query, limit),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
}

// ==================== Helper Hook ====================

/**
 * Hook that provides a complete search interface with state management.
 *
 * @returns Search state and functions
 */
export function usePropertySearch() {
  const searchMutation = useSearchProperties();

  /**
   * Execute a natural language search.
   *
   * @param query - Natural language query
   * @param options - Additional search options
   */
  const searchWithQuery = (
    query: string,
    options?: {
      filters?: SearchFilters;
      useSemanticSearch?: boolean;
      currency?: string;
    }
  ) => {
    return searchMutation.mutate({
      query,
      filters: options?.filters,
      use_semantic_search: options?.useSemanticSearch ?? true,
      currency: options?.currency ?? "USD",
    });
  };

  /**
   * Execute a filter-based search.
   *
   * @param filters - Search filters
   * @param options - Additional search options
   */
  const searchWithFilters = (
    filters: SearchFilters,
    options?: {
      useSemanticSearch?: boolean;
      currency?: string;
    }
  ) => {
    return searchMutation.mutate({
      filters,
      use_semantic_search: options?.useSemanticSearch ?? false,
      currency: options?.currency ?? "USD",
    });
  };

  /**
   * Execute a hybrid search with both query and filters.
   *
   * @param query - Natural language query
   * @param filters - Additional filters
   * @param options - Additional search options
   */
  const searchHybrid = (
    query: string,
    filters: SearchFilters,
    options?: {
      useSemanticSearch?: boolean;
      currency?: string;
    }
  ) => {
    return searchMutation.mutate({
      query,
      filters,
      use_semantic_search: options?.useSemanticSearch ?? true,
      currency: options?.currency ?? "USD",
    });
  };

  return {
    // Search functions
    searchWithQuery,
    searchWithFilters,
    searchHybrid,

    // Mutation state
    results: searchMutation.data,
    isLoading: searchMutation.isPending,
    isError: searchMutation.isError,
    error: searchMutation.error,
    reset: searchMutation.reset,
  };
}
