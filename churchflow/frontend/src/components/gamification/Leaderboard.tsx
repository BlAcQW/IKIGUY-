/**
 * Leaderboard Component
 *
 * Displays gamification rankings with multiple views and user highlighting.
 *
 * Features:
 * - Tabbed interface (Weekly, Monthly, All-Time, Streak)
 * - User's rank banner with highlight
 * - Top 3 podium with medals
 * - Pagination for large lists
 * - Avatar placeholders
 * - Privacy controls
 * - Responsive design
 * - Loading and error states
 */

import React, { useEffect, useState } from 'react';
import { Trophy, Medal, Crown, Flame, TrendingUp, ChevronLeft, ChevronRight, Eye, EyeOff } from 'lucide-react';
import { API_BASE_URL } from '../../config/api-config';

interface LeaderboardEntry {
  user_id: string;
  display_name: string;
  total_points: number;
  current_level: number;
  level_tier: string;
  current_streak?: number;
  rank: number;
  points_this_period?: number;
}

interface LeaderboardData {
  rankings: LeaderboardEntry[];
  total_count: number;
  page: number;
  page_size: number;
  period: string;
  calculated_at: string;
}

interface UserRank {
  rank: number;
  total_users: number;
  percentile: number;
  user_entry: LeaderboardEntry;
}

interface LeaderboardProps {
  organizationId: string;
  userId: string;
}

type LeaderboardType = 'weekly' | 'monthly' | 'all_time' | 'streak';

const TIER_EMOJIS = {
  bronze: '🥉',
  silver: '🥈',
  gold: '🥇',
  platinum: '💎'
};

const TIER_COLORS = {
  bronze: 'text-amber-600',
  silver: 'text-gray-500',
  gold: 'text-yellow-500',
  platinum: 'text-purple-600'
};

export const Leaderboard: React.FC<LeaderboardProps> = ({
  organizationId,
  userId
}) => {
  const [leaderboardData, setLeaderboardData] = useState<LeaderboardData | null>(null);
  const [userRank, setUserRank] = useState<UserRank | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeType, setActiveType] = useState<LeaderboardType>('all_time');
  const [currentPage, setCurrentPage] = useState(1);
  const [isVisible, setIsVisible] = useState(true);

  const pageSize = 50;

  /**
   * Fetch leaderboard data
   */
  const fetchLeaderboard = async (type: LeaderboardType, page: number) => {
    try {
      setLoading(true);
      setError(null);

      // Fetch leaderboard rankings
      const leaderboardResponse = await fetch(
        `${API_BASE_URL}/gamification/leaderboard/${type}?` +
        `organization_id=${organizationId}&page=${page}&page_size=${pageSize}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (!leaderboardResponse.ok) {
        throw new Error('Failed to fetch leaderboard');
      }

      const leaderboardJson = await leaderboardResponse.json();
      setLeaderboardData(leaderboardJson);

      // Fetch user's rank
      try {
        const rankResponse = await fetch(
          `${API_BASE_URL}/gamification/my-rank?organization_id=${organizationId}&type=${type}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );

        if (rankResponse.ok) {
          const rankData = await rankResponse.json();
          setUserRank(rankData);
        }
      } catch (rankError) {
        console.warn('Failed to fetch user rank:', rankError);
      }

    } catch (err) {
      console.error('Error fetching leaderboard:', err);
      setError(err instanceof Error ? err.message : 'Failed to load leaderboard');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Fetch leaderboard on mount and when type/page changes
   */
  useEffect(() => {
    if (organizationId && userId) {
      fetchLeaderboard(activeType, currentPage);
    }
  }, [organizationId, userId, activeType, currentPage]);

  /**
   * Toggle leaderboard visibility
   */
  const toggleVisibility = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/gamification/preferences`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify({
            organization_id: organizationId,
            leaderboard_visible: !isVisible
          })
        }
      );

      if (response.ok) {
        setIsVisible(!isVisible);
      }
    } catch (error) {
      console.error('Failed to update visibility:', error);
    }
  };

  /**
   * Get medal icon for top 3
   */
  const getMedalIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Crown className="h-8 w-8 text-yellow-500" />;
      case 2:
        return <Medal className="h-7 w-7 text-gray-400" />;
      case 3:
        return <Medal className="h-6 w-6 text-amber-600" />;
      default:
        return null;
    }
  };

  /**
   * Check if entry is current user
   */
  const isCurrentUser = (entry: LeaderboardEntry): boolean => {
    return entry.user_id === userId;
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4" />
              <p className="text-gray-600">Loading leaderboard...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <Trophy className="h-12 w-12 text-red-400 mx-auto mb-3" />
            <p className="text-red-600">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!leaderboardData) return null;

  const totalPages = Math.ceil(leaderboardData.total_count / pageSize);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Leaderboard</h1>
              <p className="text-gray-600">See how you rank among members</p>
            </div>
            <button
              onClick={toggleVisibility}
              className="flex items-center space-x-2 px-4 py-2 rounded-lg
                       bg-white border border-gray-300 hover:bg-gray-50
                       transition-colors"
            >
              {isVisible ? (
                <>
                  <Eye className="h-4 w-4" />
                  <span className="text-sm">Visible</span>
                </>
              ) : (
                <>
                  <EyeOff className="h-4 w-4" />
                  <span className="text-sm">Hidden</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* User Rank Banner */}
        {userRank && isVisible && (
          <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl shadow-lg p-6 mb-6 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="bg-white/20 rounded-full p-3">
                  <TrendingUp className="h-8 w-8" />
                </div>
                <div>
                  <p className="text-sm text-purple-100">Your Rank</p>
                  <p className="text-3xl font-bold">#{userRank.rank}</p>
                  <p className="text-sm text-purple-100">
                    Top {Math.ceil(userRank.percentile)}% • Level {userRank.user_entry.current_level}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">
                  {userRank.user_entry.total_points.toLocaleString()}
                </p>
                <p className="text-sm text-purple-100">Total Points</p>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="flex border-b overflow-x-auto">
            {(['all_time', 'weekly', 'monthly', 'streak'] as LeaderboardType[]).map((type) => (
              <button
                key={type}
                onClick={() => {
                  setActiveType(type);
                  setCurrentPage(1);
                }}
                className={`flex-1 min-w-[120px] px-6 py-4 font-medium transition-colors capitalize
                  ${activeType === type
                    ? 'text-purple-600 border-b-2 border-purple-600'
                    : 'text-gray-600 hover:text-gray-900'
                  }`}
              >
                {type === 'all_time' ? 'All Time' : type}
              </button>
            ))}
          </div>
        </div>

        {/* Leaderboard List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {leaderboardData.rankings.length === 0 ? (
            <div className="text-center py-12">
              <Trophy className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600">No rankings available yet</p>
              <p className="text-sm text-gray-500 mt-2">
                Be the first to earn points and climb the leaderboard!
              </p>
            </div>
          ) : (
            <>
              {leaderboardData.rankings.map((entry, index) => {
                const isUser = isCurrentUser(entry);
                const isTopThree = entry.rank <= 3 && currentPage === 1;

                return (
                  <div
                    key={entry.user_id}
                    className={`
                      flex items-center justify-between p-4 border-b last:border-b-0
                      transition-colors
                      ${isUser ? 'bg-purple-50 border-purple-200' : 'hover:bg-gray-50'}
                      ${isTopThree ? 'bg-gradient-to-r from-yellow-50 to-transparent' : ''}
                    `}
                  >
                    {/* Rank and Avatar */}
                    <div className="flex items-center space-x-4 flex-1">
                      <div className="w-12 text-center">
                        {isTopThree && currentPage === 1 ? (
                          getMedalIcon(entry.rank)
                        ) : (
                          <span className={`text-lg font-bold ${isUser ? 'text-purple-600' : 'text-gray-600'}`}>
                            #{entry.rank}
                          </span>
                        )}
                      </div>

                      {/* Avatar Placeholder */}
                      <div className={`
                        w-12 h-12 rounded-full flex items-center justify-center font-bold text-white
                        ${isUser ? 'bg-purple-600' : 'bg-gray-400'}
                      `}>
                        {entry.display_name.charAt(0).toUpperCase()}
                      </div>

                      {/* Name and Level */}
                      <div className="flex-1">
                        <p className={`font-semibold ${isUser ? 'text-purple-600' : 'text-gray-900'}`}>
                          {entry.display_name}
                          {isUser && <span className="ml-2 text-sm text-purple-500">(You)</span>}
                        </p>
                        <div className="flex items-center space-x-2 text-sm text-gray-600">
                          <span className={TIER_COLORS[entry.level_tier as keyof typeof TIER_COLORS]}>
                            {TIER_EMOJIS[entry.level_tier as keyof typeof TIER_EMOJIS]} Level {entry.current_level}
                          </span>
                          {activeType === 'streak' && entry.current_streak !== undefined && (
                            <>
                              <span>•</span>
                              <span className="flex items-center space-x-1">
                                <Flame className="h-4 w-4 text-orange-500" />
                                <span>{entry.current_streak} weeks</span>
                              </span>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Points */}
                      <div className="text-right">
                        <p className={`text-xl font-bold ${isUser ? 'text-purple-600' : 'text-gray-900'}`}>
                          {activeType === 'streak' && entry.current_streak !== undefined
                            ? entry.current_streak
                            : (entry.points_this_period || entry.total_points).toLocaleString()
                          }
                        </p>
                        <p className="text-xs text-gray-500">
                          {activeType === 'streak' ? 'weeks' : 'points'}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center space-x-4 mt-6">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-2 rounded-lg border border-gray-300 disabled:opacity-50
                       disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <span className="text-sm text-gray-600">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-2 rounded-lg border border-gray-300 disabled:opacity-50
                       disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        )}

        {/* Footer Info */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Rankings updated every 30 minutes</p>
          <p className="mt-1">
            Last updated: {new Date(leaderboardData.calculated_at).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Leaderboard;
