/**
 * React Query hooks for property operations.
 *
 * Provides hooks for fetching, creating, updating, and deleting properties.
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from "@tanstack/react-query";
import {
  listProperties,
  getProperty,
  createProperty,
  updateProperty,
  deleteProperty,
  searchProperties,
  getPropertyStats,
} from "@/lib/api/property-api";
import type {
  Property,
  PropertyCreate,
  PropertyUpdate,
  PropertyListResponse,
  PropertyFilters,
  PropertyStats,
} from "@/lib/types/property";

/**
 * Query keys for React Query cache management.
 */
export const propertyKeys = {
  all: ["properties"] as const,
  lists: () => [...propertyKeys.all, "list"] as const,
  list: (filters?: PropertyFilters) => [...propertyKeys.lists(), filters] as const,
  details: () => [...propertyKeys.all, "detail"] as const,
  detail: (id: string, currency?: string) => [...propertyKeys.details(), id, currency] as const,
  search: (query: string, filters?: PropertyFilters) => [...propertyKeys.all, "search", query, filters] as const,
  stats: () => [...propertyKeys.all, "stats"] as const,
};

/**
 * Hook to list properties with filters.
 *
 * @param filters - Property filters
 * @param options - React Query options
 * @returns Query result
 */
export function useProperties(
  filters?: PropertyFilters,
  options?: Omit<UseQueryOptions<PropertyListResponse, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: propertyKeys.list(filters),
    queryFn: () => listProperties(filters),
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

/**
 * Hook to get a single property by ID.
 *
 * @param id - Property ID
 * @param currency - Optional currency for price conversion
 * @param options - React Query options
 * @returns Query result
 */
export function useProperty(
  id: string,
  currency?: string,
  options?: Omit<UseQueryOptions<Property, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: propertyKeys.detail(id, currency),
    queryFn: () => getProperty(id, currency),
    enabled: !!id,
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

/**
 * Hook to search properties with full-text search.
 *
 * @param query - Search query
 * @param filters - Additional filters
 * @param options - React Query options
 * @returns Query result
 */
export function usePropertySearch(
  query: string,
  filters?: PropertyFilters,
  options?: Omit<UseQueryOptions<PropertyListResponse, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: propertyKeys.search(query, filters),
    queryFn: () => searchProperties(query, filters),
    enabled: query.length > 0,
    staleTime: 1000 * 60 * 2, // 2 minutes
    ...options,
  });
}

/**
 * Hook to get property statistics.
 *
 * @param options - React Query options
 * @returns Query result
 */
export function usePropertyStats(
  options?: Omit<UseQueryOptions<PropertyStats, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: propertyKeys.stats(),
    queryFn: getPropertyStats,
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}

/**
 * Hook to create a new property.
 *
 * @param options - React Query mutation options
 * @returns Mutation result
 */
export function useCreateProperty(
  options?: UseMutationOptions<Property, Error, PropertyCreate>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createProperty,
    onSuccess: (data) => {
      // Invalidate and refetch property lists
      queryClient.invalidateQueries({ queryKey: propertyKeys.lists() });
      queryClient.invalidateQueries({ queryKey: propertyKeys.stats() });

      // Optionally call the onSuccess callback
      options?.onSuccess?.(data, data as PropertyCreate, undefined);
    },
    ...options,
  });
}

/**
 * Hook to update an existing property.
 *
 * @param options - React Query mutation options
 * @returns Mutation result
 */
export function useUpdateProperty(
  options?: UseMutationOptions<Property, Error, { id: string; updates: PropertyUpdate }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }) => updateProperty(id, updates),
    onSuccess: (data, variables) => {
      // Invalidate and refetch property lists
      queryClient.invalidateQueries({ queryKey: propertyKeys.lists() });
      queryClient.invalidateQueries({ queryKey: propertyKeys.stats() });

      // Update the specific property in cache
      queryClient.setQueryData(propertyKeys.detail(variables.id), data);

      // Optionally call the onSuccess callback
      options?.onSuccess?.(data, variables, undefined);
    },
    ...options,
  });
}

/**
 * Hook to delete a property.
 *
 * @param options - React Query mutation options
 * @returns Mutation result
 */
export function useDeleteProperty(
  options?: UseMutationOptions<void, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteProperty,
    onSuccess: (data, propertyId) => {
      // Invalidate and refetch property lists
      queryClient.invalidateQueries({ queryKey: propertyKeys.lists() });
      queryClient.invalidateQueries({ queryKey: propertyKeys.stats() });

      // Remove the specific property from cache
      queryClient.removeQueries({ queryKey: propertyKeys.detail(propertyId) });

      // Optionally call the onSuccess callback
      options?.onSuccess?.(data, propertyId, undefined);
    },
    ...options,
  });
}
