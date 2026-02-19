/**
 * Leaderboard Component
 * Displays top listeners with listening hours
 * Supports week/month/all-time periods
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useLeaderboard } from '../hooks/useLeaderboard';
import type { LeaderboardEntry, LeaderboardPeriod } from '../types/social';
import toast from 'react-hot-toast';

interface LeaderboardProps {
  period?: 'week' | 'month' | 'all_time';
  limit?: number;
  className?: string;
}

export default function Leaderboard({
  period = 'week',
  limit = 10,
  className = '',
}: LeaderboardProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<LeaderboardPeriod>(period);

  // React Query hook - automatically refetches when selectedPeriod or limit changes
  const { data, isLoading, error } = useLeaderboard(selectedPeriod, limit);

  const entries = data?.entries || [];
  const loading = isLoading;

  // Show error toast if fetch fails
  if (error) {
    toast.error('Failed to load leaderboard. Please try again.');
  }

  const getMedalIcon = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  const getMedalColor = (rank: number) => {
    if (rank === 1) return 'from-yellow-400 to-yellow-600';
    if (rank === 2) return 'from-gray-300 to-gray-500';
    if (rank === 3) return 'from-orange-400 to-orange-600';
    return 'from-purple-500 to-pink-500';
  };

  const getPeriodLabel = (p: string) => {
    if (p === 'week') return 'This Week';
    if (p === 'month') return 'This Month';
    if (p === 'all_time') return 'All Time';
    return p;
  };

  if (loading && entries.length === 0) {
    return (
      <div className={`bg-gray-800 rounded-lg p-6 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
        </div>
      </div>
    );
  }

  if (entries.length === 0 && !loading) {
    return null; // Don't show empty leaderboard
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 shadow-xl ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="text-3xl">🏆</div>
          <div>
            <h2 className="text-2xl font-bold text-white">Top Listeners</h2>
            <p className="text-gray-400 text-sm">Listen more, grow more</p>
          </div>
        </div>

        {/* Period Selector */}
        <div className="flex bg-gray-700 rounded-lg p-1">
          {(['week', 'month', 'all_time'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setSelectedPeriod(p)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                selectedPeriod === p
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              {getPeriodLabel(p)}
            </button>
          ))}
        </div>
      </div>

      {/* Leaderboard Entries */}
      <div className="space-y-3">
        {entries.map((entry, index) => {
          const isTopThree = entry.rank <= 3;
          const isAnonymous = entry.display_mode === 'anonymous';

          return (
            <motion.div
              key={entry.user_id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className={`flex items-center space-x-4 p-4 rounded-lg transition-all ${
                isTopThree
                  ? 'bg-gradient-to-r ' + getMedalColor(entry.rank) + ' bg-opacity-10'
                  : 'bg-gray-700 hover:bg-gray-650'
              }`}
            >
              {/* Rank */}
              <div
                className={`flex items-center justify-center w-12 h-12 rounded-full font-bold text-lg ${
                  isTopThree
                    ? 'bg-gradient-to-br ' + getMedalColor(entry.rank) + ' text-white'
                    : 'bg-gray-600 text-gray-300'
                }`}
              >
                {getMedalIcon(entry.rank)}
              </div>

              {/* User Info */}
              {isAnonymous ? (
                <div className="flex-1 flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full bg-gray-600 flex items-center justify-center">
                    <span className="text-gray-400">👤</span>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-300">{entry.display_name}</p>
                    <p className="text-sm text-gray-500">Anonymous Listener</p>
                  </div>
                </div>
              ) : (
                <Link
                  to={`/user/${entry.user_id}`}
                  className="flex-1 flex items-center space-x-3 hover:opacity-80 transition-opacity"
                >
                  {/* Avatar */}
                  <div className="relative">
                    {entry.avatar_url ? (
                      <img
                        src={entry.avatar_url}
                        alt={entry.display_name || entry.username || 'User'}
                        className="w-10 h-10 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                        <span className="text-white font-bold text-lg">
                          {(entry.display_name || entry.username || '?')[0].toUpperCase()}
                        </span>
                      </div>
                    )}
                    {isTopThree && (
                      <div className="absolute -top-1 -right-1 text-xs">
                        {getMedalIcon(entry.rank)}
                      </div>
                    )}
                  </div>

                  {/* Name */}
                  <div className="flex-1">
                    <p className="font-medium text-white">
                      {entry.display_name || entry.username}
                    </p>
                    {entry.username && entry.display_name && (
                      <p className="text-sm text-gray-400">@{entry.username}</p>
                    )}
                  </div>
                </Link>
              )}

              {/* Listening Hours */}
              <div className="text-right">
                <p className="text-lg font-bold text-white">
                  {entry.listening_hours.toFixed(1)}h
                </p>
                <p className="text-xs text-gray-400">listened</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* View Full Leaderboard Link */}
      {entries.length >= limit && (
        <Link
          to="/leaderboard"
          className="mt-6 block text-center text-purple-400 hover:text-purple-300 font-medium transition-colors"
        >
          View Full Leaderboard →
        </Link>
      )}
    </motion.div>
  );
}
