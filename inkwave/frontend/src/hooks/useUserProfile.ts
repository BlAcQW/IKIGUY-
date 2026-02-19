/**
 * React Query hooks for public user profiles
 * Provides type-safe hooks for fetching user profiles, activity, and currently reading books
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { api } from '../lib/api';
import type {
  PublicProfileResponse,
  CurrentlyReadingResponse,
  ActivityResponse,
  UserSearchResponse,
} from '../types/social';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const USER_PROFILE_KEYS = {
  all: ['user-profile'] as const,
  profile: (userId: string) => ['user-profile', userId] as const,
  currentlyReading: (userId: string) => ['user-profile', userId, 'currently-reading'] as const,
  activity: (userId: string, limit: number) => ['user-profile', userId, 'activity', limit] as const,
  search: (query: string, page: number, per_page: number) =>
    ['user-profile', 'search', query, page, per_page] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

/**
 * Fetch public profile for a user
 *
 * @param userId - User ID to fetch profile for
 * @returns Query result with public profile
 *
 * @example
 * ```tsx
 * const { data: profile, isLoading } = usePublicProfile(userId);
 * ```
 */
export function usePublicProfile(
  userId: string,
  options?: UseQueryOptions<PublicProfileResponse>
) {
  return useQuery<PublicProfileResponse>({
    queryKey: USER_PROFILE_KEYS.profile(userId),
    queryFn: async () => {
      const response = await api.users.getPublicProfile(userId);
      return response.data;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!userId,
    ...options,
  });
}

/**
 * Fetch books user is currently reading
 *
 * @param userId - User ID to fetch books for
 * @returns Query result with currently reading books
 *
 * @example
 * ```tsx
 * const { data } = useCurrentlyReading(userId);
 * const books = data?.books || [];
 * ```
 */
export function useCurrentlyReading(
  userId: string,
  options?: UseQueryOptions<CurrentlyReadingResponse>
) {
  return useQuery<CurrentlyReadingResponse>({
    queryKey: USER_PROFILE_KEYS.currentlyReading(userId),
    queryFn: async () => {
      const response = await api.users.getCurrentlyReading(userId);
      return response.data;
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
    enabled: !!userId,
    ...options,
  });
}

/**
 * Fetch user's reading activity
 *
 * @param userId - User ID to fetch activity for
 * @param limit - Number of activities to fetch (default: 20)
 * @returns Query result with user activities
 *
 * @example
 * ```tsx
 * const { data } = useUserActivity(userId, 20);
 * const activities = data?.activities || [];
 * ```
 */
export function useUserActivity(
  userId: string,
  limit: number = 20,
  options?: UseQueryOptions<ActivityResponse>
) {
  return useQuery<ActivityResponse>({
    queryKey: USER_PROFILE_KEYS.activity(userId, limit),
    queryFn: async () => {
      const response = await api.users.getUserActivity(userId, limit);
      return response.data;
    },
    staleTime: 1000 * 60 * 1, // 1 minute
    enabled: !!userId,
    ...options,
  });
}

/**
 * Search users by username or display name
 *
 * @param query - Search query
 * @param page - Page number (default: 1)
 * @param per_page - Results per page (default: 20)
 * @returns Query result with search results
 *
 * @example
 * ```tsx
 * const { data } = useUserSearch(searchQuery, 1, 20);
 * const users = data?.users || [];
 * ```
 */
export function useUserSearch(
  query: string,
  page: number = 1,
  per_page: number = 20,
  options?: UseQueryOptions<UserSearchResponse>
) {
  return useQuery<UserSearchResponse>({
    queryKey: USER_PROFILE_KEYS.search(query, page, per_page),
    queryFn: async () => {
      const response = await api.users.searchUsers(query, page, per_page);
      return response.data;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: query.trim().length >= 2, // Only search if query is at least 2 characters
    ...options,
  });
}
