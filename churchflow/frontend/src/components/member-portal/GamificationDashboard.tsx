/**
 * Gamification Dashboard Widget
 *
 * Displays user's gamification profile with level progress, streaks, badges, and rank.
 * Integrated into Member Portal dashboard for engagement tracking.
 *
 * Features:
 * - Level progress bar with tier badge
 * - Current streak with flame icon
 * - Quick stats (badges earned, leaderboard rank)
 * - Points to next level
 * - Gradient purple card design
 * - Animated progress indicators
 * - Navigation to detailed views
 */

import React, { useEffect, useState } from 'react';
import { Trophy, Flame, Star, TrendingUp, Award, ChevronRight, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { API_BASE_URL } from '../../config/api-config';

interface GamificationProfile {
  user_id: string;
  organization_id: string;
  total_points: number;
  current_level: number;
  level_tier: string;
  points_to_next_level: number;
  current_streak: number;
  longest_streak: number;
  badges_earned: Array<{
    badge_id: string;
    name: string;
    icon_emoji: string;
    earned_at: string;
  }>;
  total_services_attended: number;
  leaderboard_visible: boolean;
}

interface UserRank {
  rank: number;
  total_users: number;
  percentile: number;
}

interface GamificationDashboardProps {
  organizationId: string;
  userId: string;
}

const TIER_CONFIG = {
  bronze: {
    emoji: '🥉',
    color: 'from-amber-700 to-amber-500',
    textColor: 'text-amber-700',
    bgColor: 'bg-amber-50'
  },
  silver: {
    emoji: '🥈',
    color: 'from-gray-400 to-gray-300',
    textColor: 'text-gray-600',
    bgColor: 'bg-gray-50'
  },
  gold: {
    emoji: '🥇',
    color: 'from-yellow-500 to-yellow-300',
    textColor: 'text-yellow-700',
    bgColor: 'bg-yellow-50'
  },
  platinum: {
    emoji: '💎',
    color: 'from-purple-500 to-indigo-500',
    textColor: 'text-purple-700',
    bgColor: 'bg-purple-50'
  }
};

export const GamificationDashboard: React.FC<GamificationDashboardProps> = ({
  organizationId,
  userId
}) => {
  const [profile, setProfile] = useState<GamificationProfile | null>(null);
  const [rank, setRank] = useState<UserRank | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch gamification profile with cleanup
   */
  useEffect(() => {
    const abortController = new AbortController();
    let isMounted = true;

    const fetchProfile = async () => {
      try {
        setLoading(true);
        setError(null);

        const profileResponse = await fetch(
          `${API_BASE_URL}/gamification/profile?organization_id=${organizationId}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            signal: abortController.signal
          }
        );

        if (!profileResponse.ok) {
          throw new Error('Failed to fetch gamification profile');
        }

        const profileData = await profileResponse.json();

        if (!isMounted) return;
        setProfile(profileData);

        // Fetch rank if leaderboard visible
        if (profileData.leaderboard_visible) {
          try {
            const rankResponse = await fetch(
              `${API_BASE_URL}/gamification/my-rank?organization_id=${organizationId}&type=all_time`,
              {
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                signal: abortController.signal
              }
            );

            if (rankResponse.ok && isMounted) {
              const rankData = await rankResponse.json();
              setRank(rankData);
            }
          } catch (rankError) {
            if (rankError instanceof Error && rankError.name !== 'AbortError') {
              console.warn('Failed to fetch rank:', rankError);
            }
          }
        }

      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          return; // Ignore abort errors
        }
        console.error('Error fetching gamification data:', err);
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load gamification data');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    if (organizationId && userId) {
      fetchProfile();
    }

    return () => {
      isMounted = false;
      abortController.abort();
    };
  }, [organizationId, userId]);

  /**
   * Calculate level progress percentage
   */
  const getLevelProgress = (): number => {
    if (!profile) return 0;

    const tierConfig = {
      bronze: 100,
      silver: 200,
      gold: 500,
      platinum: 1000
    };

    const pointsPerLevel = tierConfig[profile.level_tier as keyof typeof tierConfig] || 100;
    const pointsInCurrentLevel = pointsPerLevel - profile.points_to_next_level;
    return (pointsInCurrentLevel / pointsPerLevel) * 100;
  };

  /**
   * Format large numbers
   */
  const formatNumber = (num: number): string => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
  };

  // Loading state
  if (loading) {
    return (
      <div className="bg-gradient-to-br from-purple-600 to-indigo-700 rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-center h-48">
          <Loader2 className="h-8 w-8 text-white animate-spin" />
        </div>
      </div>
    );
  }

  // Error state
  if (error || !profile) {
    return (
      <div className="bg-gradient-to-br from-purple-600 to-indigo-700 rounded-xl shadow-lg p-6">
        <div className="text-center text-white">
          <Trophy className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">{error || 'Unable to load gamification data'}</p>
        </div>
      </div>
    );
  }

  const tierConfig = TIER_CONFIG[profile.level_tier as keyof typeof TIER_CONFIG] || TIER_CONFIG.bronze;
  const progressPercentage = getLevelProgress();

  return (
    <div className="bg-gradient-to-br from-purple-600 to-indigo-700 rounded-xl shadow-lg p-6 text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="bg-white/20 rounded-full p-2">
            <Trophy className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold">Your Progress</h3>
            <p className="text-sm text-purple-100">Keep up the great work!</p>
          </div>
        </div>
        <Link
          to={`/member/gamification?org=${organizationId}`}
          className="text-white hover:bg-white/10 rounded-lg p-2 transition-colors"
        >
          <ChevronRight className="h-5 w-5" />
        </Link>
      </div>

      {/* Level Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">{tierConfig.emoji}</span>
            <div>
              <p className="text-sm font-medium">Level {profile.current_level}</p>
              <p className="text-xs text-purple-100 capitalize">{profile.level_tier} Tier</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium">{formatNumber(profile.total_points)} pts</p>
            <p className="text-xs text-purple-100">
              {profile.points_to_next_level} to Level {profile.current_level + 1}
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="bg-white/20 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-yellow-400 to-yellow-200 h-full rounded-full
                       transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Streak */}
        <div className="bg-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Flame className="h-5 w-5 text-orange-300" />
            <span className="text-2xl font-bold">{profile.current_streak}</span>
          </div>
          <p className="text-xs text-purple-100">Week Streak</p>
          {profile.longest_streak > profile.current_streak && (
            <p className="text-xs text-purple-200 mt-1">
              Best: {profile.longest_streak}
            </p>
          )}
        </div>

        {/* Badges */}
        <div className="bg-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Award className="h-5 w-5 text-yellow-300" />
            <span className="text-2xl font-bold">{profile.badges_earned.length}</span>
          </div>
          <p className="text-xs text-purple-100">Badges Earned</p>
        </div>

        {/* Services Attended */}
        <div className="bg-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Star className="h-5 w-5 text-blue-300" />
            <span className="text-2xl font-bold">{profile.total_services_attended}</span>
          </div>
          <p className="text-xs text-purple-100">Services</p>
        </div>

        {/* Leaderboard Rank */}
        {rank && profile.leaderboard_visible && (
          <div className="bg-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="h-5 w-5 text-green-300" />
              <span className="text-2xl font-bold">#{rank.rank}</span>
            </div>
            <p className="text-xs text-purple-100">
              Top {Math.ceil(rank.percentile)}%
            </p>
          </div>
        )}
      </div>

      {/* Recent Badges */}
      {profile.badges_earned.length > 0 && (
        <div className="bg-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium">Recent Badges</p>
            <Link
              to={`/member/badges?org=${organizationId}`}
              className="text-xs text-purple-200 hover:text-white transition-colors"
            >
              View All
            </Link>
          </div>
          <div className="flex items-center space-x-2 overflow-x-auto">
            {profile.badges_earned.slice(-5).reverse().map((badge) => (
              <div
                key={badge.badge_id}
                className="flex-shrink-0 bg-white/20 rounded-lg p-2 min-w-[60px]"
                title={badge.name}
              >
                <div className="text-2xl text-center">{badge.icon_emoji}</div>
                <p className="text-xs text-center text-purple-100 mt-1 truncate">
                  {badge.name}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Call to Action */}
      {profile.current_streak === 0 && (
        <div className="mt-4 bg-white/10 rounded-lg p-4 text-center">
          <p className="text-sm">
            🎯 Attend a service this week to start your streak!
          </p>
        </div>
      )}
    </div>
  );
};

export default GamificationDashboard;
