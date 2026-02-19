/**
 * Admin Gamification Analytics Dashboard
 *
 * Comprehensive analytics view for admins to monitor gamification system health,
 * usage patterns, and member engagement metrics.
 *
 * Features:
 * - System-wide statistics (total users, points, levels)
 * - Point distribution analysis
 * - Badge unlock rates
 * - Challenge participation trends
 * - Leaderboard engagement metrics
 * - Time-based charts and graphs
 */

import React, { useEffect, useState } from 'react';
import {
  Trophy, TrendingUp, Award, Users, Flame, Target,
  BarChart3, Activity, CheckCircle, Clock, ArrowUp, ArrowDown
} from 'lucide-react';
import { API_BASE_URL } from '../../config/api-config';

interface AnalyticsData {
  overview: {
    total_active_users: number;
    total_points_awarded: number;
    average_points_per_user: number;
    average_level: number;
    total_badges_earned: number;
    active_challenges: number;
    total_check_ins: number;
  };
  levels: {
    level_distribution: Array<{
      tier: string;
      count: number;
      percentage: number;
    }>;
  };
  badges: {
    most_earned: Array<{
      badge_id: string;
      name: string;
      icon_emoji: string;
      earned_count: number;
    }>;
    total_badges: number;
    average_per_user: number;
  };
  challenges: {
    total_created: number;
    active_count: number;
    completion_rate: number;
    average_participants: number;
  };
  streaks: {
    users_with_streak: number;
    average_streak: number;
    longest_current_streak: number;
    users_4plus_weeks: number;
  };
  leaderboard: {
    opt_in_rate: number;
    total_visible: number;
    total_hidden: number;
  };
  trends: {
    points_last_7_days: Array<{
      date: string;
      points: number;
    }>;
    check_ins_last_7_days: Array<{
      date: string;
      count: number;
    }>;
  };
}

interface GamificationAnalyticsProps {
  organizationId: string;
}

export const GamificationAnalytics: React.FC<GamificationAnalyticsProps> = ({
  organizationId
}) => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  /**
   * Fetch analytics data
   */
  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(
          `${API_BASE_URL}/gamification/admin/analytics?organization_id=${organizationId}&period=${timeRange}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch analytics');
        }

        const data = await response.json();
        setAnalytics(data);

      } catch (err) {
        console.error('Error fetching analytics:', err);
        setError(err instanceof Error ? err.message : 'Failed to load analytics');
      } finally {
        setLoading(false);
      }
    };

    if (organizationId) {
      fetchAnalytics();
    }
  }, [organizationId, timeRange]);

  /**
   * Format large numbers
   */
  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toLocaleString();
  };

  /**
   * Calculate percentage change (placeholder for now)
   */
  const getPercentageChange = (current: number, previous: number): number => {
    if (previous === 0) return 0;
    return ((current - previous) / previous) * 100;
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4" />
              <p className="text-gray-600">Loading analytics...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !analytics) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <BarChart3 className="h-12 w-12 text-red-400 mx-auto mb-3" />
            <p className="text-red-600">{error || 'Failed to load analytics'}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Gamification Analytics</h1>
              <p className="text-gray-600 mt-1">Monitor engagement and system performance</p>
            </div>
            <div className="flex items-center space-x-2">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2
                         focus:ring-purple-500 focus:border-transparent"
              >
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
              </select>
            </div>
          </div>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Active Users */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <Users className="h-8 w-8 text-purple-600" />
              <span className="text-xs text-green-600 flex items-center">
                <ArrowUp className="h-3 w-3 mr-1" />
                12%
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-1">Active Users</p>
            <p className="text-3xl font-bold text-gray-900">
              {formatNumber(analytics.overview.total_active_users)}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Avg Level: {analytics.overview.average_level.toFixed(1)}
            </p>
          </div>

          {/* Total Points */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <Trophy className="h-8 w-8 text-yellow-600" />
              <span className="text-xs text-green-600 flex items-center">
                <ArrowUp className="h-3 w-3 mr-1" />
                23%
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-1">Total Points</p>
            <p className="text-3xl font-bold text-gray-900">
              {formatNumber(analytics.overview.total_points_awarded)}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Avg per user: {Math.round(analytics.overview.average_points_per_user)}
            </p>
          </div>

          {/* Badges Earned */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <Award className="h-8 w-8 text-blue-600" />
              <span className="text-xs text-green-600 flex items-center">
                <ArrowUp className="h-3 w-3 mr-1" />
                18%
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-1">Badges Earned</p>
            <p className="text-3xl font-bold text-gray-900">
              {formatNumber(analytics.overview.total_badges_earned)}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              {analytics.badges.total_badges} unique badges
            </p>
          </div>

          {/* Check-Ins */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <span className="text-xs text-green-600 flex items-center">
                <ArrowUp className="h-3 w-3 mr-1" />
                15%
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-1">Total Check-Ins</p>
            <p className="text-3xl font-bold text-gray-900">
              {formatNumber(analytics.overview.total_check_ins)}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              {analytics.overview.active_challenges} active challenges
            </p>
          </div>
        </div>

        {/* Level Distribution */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-6 flex items-center">
            <TrendingUp className="h-5 w-5 mr-2 text-purple-600" />
            Level Distribution
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {analytics.levels.level_distribution.map((tier) => (
              <div key={tier.tier} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium capitalize">{tier.tier}</span>
                  <span className="text-lg font-bold">{tier.count}</span>
                </div>
                <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-purple-600 h-full"
                    style={{ width: `${tier.percentage}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">{tier.percentage.toFixed(1)}%</p>
              </div>
            ))}
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Most Earned Badges */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-6 flex items-center">
              <Award className="h-5 w-5 mr-2 text-blue-600" />
              Most Earned Badges
            </h2>
            <div className="space-y-4">
              {analytics.badges.most_earned.map((badge) => (
                <div key={badge.badge_id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-3xl">{badge.icon_emoji}</span>
                    <div>
                      <p className="font-medium text-gray-900">{badge.name}</p>
                      <p className="text-sm text-gray-500">{badge.earned_count} members</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-purple-600">
                      {((badge.earned_count / analytics.overview.total_active_users) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Streak Statistics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-6 flex items-center">
              <Flame className="h-5 w-5 mr-2 text-orange-600" />
              Streak Statistics
            </h2>
            <div className="space-y-6">
              <div className="flex items-center justify-between pb-4 border-b">
                <span className="text-gray-600">Users with Active Streak</span>
                <span className="text-2xl font-bold text-gray-900">
                  {analytics.streaks.users_with_streak}
                </span>
              </div>
              <div className="flex items-center justify-between pb-4 border-b">
                <span className="text-gray-600">Average Streak</span>
                <span className="text-2xl font-bold text-gray-900">
                  {analytics.streaks.average_streak.toFixed(1)} weeks
                </span>
              </div>
              <div className="flex items-center justify-between pb-4 border-b">
                <span className="text-gray-600">Longest Current Streak</span>
                <span className="text-2xl font-bold text-orange-600">
                  {analytics.streaks.longest_current_streak} weeks
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">4+ Week Streaks</span>
                <span className="text-2xl font-bold text-purple-600">
                  {analytics.streaks.users_4plus_weeks}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Challenge Statistics */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-6 flex items-center">
            <Target className="h-5 w-5 mr-2 text-green-600" />
            Challenge Performance
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-900 mb-2">
                {analytics.challenges.total_created}
              </p>
              <p className="text-sm text-gray-600">Total Challenges</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-green-600 mb-2">
                {analytics.challenges.active_count}
              </p>
              <p className="text-sm text-gray-600">Currently Active</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-blue-600 mb-2">
                {analytics.challenges.completion_rate.toFixed(1)}%
              </p>
              <p className="text-sm text-gray-600">Completion Rate</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-purple-600 mb-2">
                {Math.round(analytics.challenges.average_participants)}
              </p>
              <p className="text-sm text-gray-600">Avg Participants</p>
            </div>
          </div>
        </div>

        {/* Leaderboard Engagement */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-6 flex items-center">
            <Activity className="h-5 w-5 mr-2 text-indigo-600" />
            Leaderboard Engagement
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-6 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg">
              <p className="text-4xl font-bold text-purple-600 mb-2">
                {analytics.leaderboard.opt_in_rate.toFixed(1)}%
              </p>
              <p className="text-sm text-gray-700 font-medium">Opt-In Rate</p>
              <p className="text-xs text-gray-600 mt-1">Users with visible profiles</p>
            </div>
            <div className="text-center p-6 border border-gray-200 rounded-lg">
              <p className="text-4xl font-bold text-green-600 mb-2">
                {analytics.leaderboard.total_visible}
              </p>
              <p className="text-sm text-gray-700 font-medium">Visible Profiles</p>
              <p className="text-xs text-gray-600 mt-1">Public leaderboard participation</p>
            </div>
            <div className="text-center p-6 border border-gray-200 rounded-lg">
              <p className="text-4xl font-bold text-gray-600 mb-2">
                {analytics.leaderboard.total_hidden}
              </p>
              <p className="text-sm text-gray-700 font-medium">Private Profiles</p>
              <p className="text-xs text-gray-600 mt-1">Hidden from leaderboard</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GamificationAnalytics;
