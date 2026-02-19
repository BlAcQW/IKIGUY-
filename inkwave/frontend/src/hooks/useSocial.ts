/**
 * React Query hooks for social functionality
 * Provides type-safe hooks for follow/unfollow, followers/following, and activity feed
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { api } from '../lib/api';
import toast from 'react-hot-toast';
import type {
  UserListResponse,
  FollowResponse,
  ActivityFeedResponse,
  FollowSuggestionsResponse,
  BlockResponse,
  ReportUserResponse,
  ReportUserRequest,
} from '../types/social';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const SOCIAL_KEYS = {
  all: ['social'] as const,
  followers: (userId: string) => ['social', 'followers', userId] as const,
  following: (userId: string) => ['social', 'following', userId] as const,
  suggestions: ['social', 'suggestions'] as const,
  feed: ['social', 'feed'] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

/**
 * Fetch followers list for a user
 *
 * @param userId - User ID to fetch followers for
 * @param page - Page number (optional)
 * @param per_page - Results per page (optional)
 * @returns Query result with followers list
 */
export function useFollowers(
  userId: string,
  page?: number,
  per_page?: number,
  options?: UseQueryOptions<UserListResponse>
) {
  return useQuery<UserListResponse>({
    queryKey: [...SOCIAL_KEYS.followers(userId), page, per_page],
    queryFn: async () => {
      const response = await api.social.getFollowers(userId, page, per_page);
      return response.data;
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
    enabled: !!userId,
    ...options,
  });
}

/**
 * Fetch following list for a user
 *
 * @param userId - User ID to fetch following for
 * @param page - Page number (optional)
 * @param per_page - Results per page (optional)
 * @returns Query result with following list
 */
export function useFollowing(
  userId: string,
  page?: number,
  per_page?: number,
  options?: UseQueryOptions<UserListResponse>
) {
  return useQuery<UserListResponse>({
    queryKey: [...SOCIAL_KEYS.following(userId), page, per_page],
    queryFn: async () => {
      const response = await api.social.getFollowing(userId, page, per_page);
      return response.data;
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
    enabled: !!userId,
    ...options,
  });
}

/**
 * Fetch follow suggestions for current user
 *
 * @param limit - Number of suggestions to fetch (optional)
 * @returns Query result with suggested users
 */
export function useFollowSuggestions(
  limit?: number,
  options?: UseQueryOptions<FollowSuggestionsResponse>
) {
  return useQuery<FollowSuggestionsResponse>({
    queryKey: [...SOCIAL_KEYS.suggestions, limit],
    queryFn: async () => {
      const response = await api.social.getFollowSuggestions(limit);
      return response.data;
    },
    staleTime: 1000 * 60 * 10, // 10 minutes
    ...options,
  });
}

/**
 * Fetch activity feed from followed users
 *
 * @param limit - Number of activities to fetch (optional)
 * @returns Query result with activity feed
 */
export function useFollowingFeed(
  limit?: number,
  options?: UseQueryOptions<ActivityFeedResponse>
) {
  return useQuery<ActivityFeedResponse>({
    queryKey: [...SOCIAL_KEYS.feed, limit],
    queryFn: async () => {
      const response = await api.social.getFollowingFeed(limit);
      return response.data;
    },
    staleTime: 1000 * 60 * 1, // 1 minute (fresh feed)
    refetchInterval: 1000 * 60 * 2, // Auto-refresh every 2 minutes
    ...options,
  });
}

// ============================================================================
// MUTATION HOOKS
// ============================================================================

/**
 * Follow a user
 * Automatically invalidates relevant queries on success
 *
 * @returns Mutation hook for following a user
 */
export function useFollowUser() {
  const queryClient = useQueryClient();

  return useMutation<FollowResponse, Error, string>({
    mutationFn: async (userId: string) => {
      const response = await api.social.followUser(userId);
      return response.data;
    },
    onSuccess: (_, userId) => {
      // Invalidate followers/following lists
      queryClient.invalidateQueries({ queryKey: SOCIAL_KEYS.followers(userId) });
      queryClient.invalidateQueries({ queryKey: SOCIAL_KEYS.following(userId) });

      // Invalidate suggestions (they may change after following)
      queryClient.invalidateQueries({ queryKey: SOCIAL_KEYS.suggestions });

      // Invalidate feed (new user's activities will appear)
      queryClient.invalidateQueries({ queryKey: SOCIAL_KEYS.feed });

      toast.success('Following user');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to follow user';
      toast.error(message);
    },
  });
}

/**
 * Unfollow a user
 * Automatically invalidates relevant queries on success
 *
 * @returns Mutation hook for unfollowing a user
 */
export function useUnfollowUser() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, string>({
    mutationFn: async (userId: string) => {
      const response = await api.social.unfollowUser(userId);
      return response.data;
    },
    onSuccess: (_, userId) => {
      // Invalidate followers/following lists
      queryClient.invalidateQueries({ queryKey: SOCIAL_KEYS.followers(userId) });
      queryClient.invalidateQueries({ queryKey: SOCIAL_KEYS.following(userId) });

      // Invalidate suggestions
      queryClient.invalidateQueries({ queryKey: SOCIAL_KEYS.suggestions });

      // Invalidate feed (user's activities won't appear anymore)
      queryClient.invalidateQueries({ queryKey: SOCIAL_KEYS.feed });

      toast.success('Unfollowed user');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to unfollow user';
      toast.error(message);
    },
  });
}

/**
 * Block a user
 * Automatically removes follow relationships
 *
 * @returns Mutation hook for blocking a user
 */
export function useBlockUser() {
  const queryClient = useQueryClient();

  return useMutation<BlockResponse, Error, { userId: string; reason?: string }>({
    mutationFn: async ({ userId, reason }) => {
      const response = await api.social.blockUser(userId, reason);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate all social queries (block affects many relationships)
      queryClient.invalidateQueries({ queryKey: SOCIAL_KEYS.all });

      toast.success('User blocked successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to block user';
      toast.error(message);
    },
  });
}

/**
 * Unblock a user
 *
 * @returns Mutation hook for unblocking a user
 */
export function useUnblockUser() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, string>({
    mutationFn: async (userId: string) => {
      const response = await api.social.unblockUser(userId);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate all social queries
      queryClient.invalidateQueries({ queryKey: SOCIAL_KEYS.all });

      toast.success('User unblocked successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to unblock user';
      toast.error(message);
    },
  });
}

/**
 * Report a user
 *
 * @returns Mutation hook for reporting a user
 */
export function useReportUser() {
  return useMutation<ReportUserResponse, Error, { userId: string; report: ReportUserRequest }>({
    mutationFn: async ({ userId, report }) => {
      const response = await api.social.reportUser(userId, report);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Report submitted successfully. Our team will review it.');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to submit report';
      toast.error(message);
    },
  });
}
