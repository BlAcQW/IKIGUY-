/**
 * React Query hooks for leaderboard functionality
 * Provides type-safe hooks for top listeners and user ranking
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { api } from '../lib/api';
import type {
  LeaderboardResponse,
  LeaderboardPeriod,
  UserRankResponse,
} from '../types/social';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const LEADERBOARD_KEYS = {
  all: ['leaderboard'] as const,
  list: (period: LeaderboardPeriod, limit: number, search?: string) =>
    ['leaderboard', period, limit, search] as const,
  rank: (period: LeaderboardPeriod) => ['leaderboard', 'rank', period] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

/**
 * Fetch top listeners leaderboard
 *
 * @param period - Time period ('week', 'month', 'all_time')
 * @param limit - Number of entries to fetch (default: 20)
 * @param search - Optional search query to filter by username/display name
 * @returns Query result with leaderboard entries
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useLeaderboard('week', 10);
 * const { data: searchData } = useLeaderboard('week', 10, 'john');
 * ```
 */
export function useLeaderboard(
  period: LeaderboardPeriod = 'week',
  limit: number = 20,
  search?: string,
  options?: UseQueryOptions<LeaderboardResponse>
) {
  return useQuery<LeaderboardResponse>({
    queryKey: LEADERBOARD_KEYS.list(period, limit, search),
    queryFn: async () => {
      const response = await api.leaderboard.getTopListeners(period, limit, search);
      return response.data;
    },
    staleTime: 1000 * 60 * 15, // 15 minutes (matches backend cache duration)
    ...options,
  });
}

/**
 * Fetch current user's rank on the leaderboard
 *
 * @param period - Time period ('week', 'month', 'all_time')
 * @returns Query result with user's rank
 *
 * @example
 * ```tsx
 * const { data: rankData } = useUserRank('week');
 * if (rankData?.on_leaderboard) {
 *   console.log(`You're rank #${rankData.rank}!`);
 * }
 * ```
 */
export function useUserRank(
  period: LeaderboardPeriod = 'week',
  options?: UseQueryOptions<UserRankResponse>
) {
  return useQuery<UserRankResponse>({
    queryKey: LEADERBOARD_KEYS.rank(period),
    queryFn: async () => {
      const response = await api.leaderboard.getUserRank(period);
      return response.data;
    },
    staleTime: 1000 * 60 * 15, // 15 minutes
    ...options,
  });
}
