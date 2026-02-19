/**
 * React Query hooks for user-related data.
 */

import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { getBookedProperties, BookedProperty } from "@/lib/api/user-api";
import { useAuth } from "@/contexts/AuthContext";

/**
 * Hook to get properties that the user has bookings for.
 *
 * Returns properties with booking information using MongoDB aggregation.
 * Excludes cancelled and no-show bookings by default.
 * Only fetches if user is authenticated.
 *
 * @param params - Query parameters
 * @param params.status_filter - Optional booking status filter
 * @param params.limit - Maximum number of properties to return (default: 100)
 * @param params.offset - Number of properties to skip for pagination (default: 0)
 * @returns UseQueryResult<BookedProperty[], Error>
 *
 * @example
 * ```tsx
 * const { data: bookedProperties, isLoading, error } = useBookedProperties({ limit: 50 });
 * ```
 */
export function useBookedProperties(params?: {
  status_filter?: string;
  limit?: number;
  offset?: number;
}): UseQueryResult<BookedProperty[], Error> {
  const { user } = useAuth();

  return useQuery({
    queryKey: ["booked-properties", params],
    queryFn: () => getBookedProperties(params),
    enabled: !!user, // Only fetch if authenticated
    staleTime: 1000 * 60 * 5, // Consider data fresh for 5 minutes
    retry: 1, // Only retry once on failure
  });
}
