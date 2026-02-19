/**
 * LeaderboardPage Component
 * Full leaderboard rankings with period selector and user's rank
 * Route: /leaderboard
 */

import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Trophy,
  Medal,
  Clock,
  TrendingUp,
  Users,
  Loader,
  ArrowLeft,
  Crown,
  Search,
  X,
  Shield,
} from 'lucide-react';
import { useLeaderboard, useUserRank } from '../hooks/useLeaderboard';
import { useAuthStore } from '../store/authStore';
import { LeaderboardPeriod } from '../types/social';
import UserListeningHistoryModal from '../components/UserListeningHistoryModal';
import { api } from '../lib/api';

const PERIODS: { value: LeaderboardPeriod; label: string }[] = [
  { value: 'week', label: 'This Week' },
  { value: 'month', label: 'This Month' },
  { value: 'all_time', label: 'All Time' },
];

export default function LeaderboardPage() {
	useEffect(() => {
		document.title = 'Leaderboard - InkWave';
	}, []);

  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [period, setPeriod] = useState<LeaderboardPeriod>('week');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const userRankRef = useRef<HTMLDivElement>(null);

  // Fetch leaderboard data (top 100) with optional search
  const { data: leaderboardData, isLoading } = useLeaderboard(period, 100, searchQuery || undefined);
  const { data: userRankData } = useUserRank(period);

  const entries = leaderboardData?.entries || [];
  const userRank = userRankData?.rank || null;
  const onLeaderboard = userRankData?.on_leaderboard || false;

  // Fetch profile to check admin status
  useEffect(() => {
    const fetchProfile = async () => {
      if (!user) return;
      try {
        const response = await api.profile.get();
        setIsAdmin(response.data.is_admin || false);
      } catch (error) {
        console.error('Failed to fetch profile:', error);
      }
    };
    fetchProfile();
  }, [user]);

  // Auto-scroll to user's position on load
  useEffect(() => {
    if (userRankRef.current && userRank && userRank <= 100) {
      setTimeout(() => {
        userRankRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 500);
    }
  }, [userRank, period]);

  // Get medal emoji for top 3
  const getMedal = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return null;
  };

  // Get rank badge color
  const getRankBadgeColor = (rank: number) => {
    if (rank === 1) return 'from-yellow-500 to-yellow-600';
    if (rank === 2) return 'from-gray-400 to-gray-500';
    if (rank === 3) return 'from-orange-600 to-orange-700';
    return 'from-gray-700 to-gray-800';
  };

  // Format listening hours
  const formatHours = (hours: number) => {
    if (hours < 1) return `${Math.round(hours * 60)} min`;
    return `${hours.toFixed(1)} hrs`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      {/* Header */}
      <div className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-800 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <ArrowLeft size={20} className="text-gray-400" />
              </button>
              <div className="flex items-center gap-2">
                <Trophy size={24} className="text-yellow-500" />
                <h1 className="text-xl font-bold text-white">Leaderboard</h1>
              </div>
            </div>

            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Users size={16} />
              <span>{entries.length} Listeners</span>
            </div>
          </div>

          {/* Period Selector */}
          <div className="flex gap-2 mt-4">
            {PERIODS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => setPeriod(value)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  period === value
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-300'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="relative mt-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search listeners by name..."
              className="w-full px-4 py-2 pl-10 pr-10 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                aria-label="Clear search"
              >
                <X size={18} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* User's Rank Card */}
        {user && onLeaderboard && userRank && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-4 mb-6 shadow-xl"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="bg-white/20 backdrop-blur-sm rounded-full p-3">
                  <Crown size={24} className="text-white" />
                </div>
                <div>
                  <p className="text-white/80 text-sm font-medium">Your Rank</p>
                  <p className="text-white text-2xl font-bold">#{userRank}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  if (userRank <= 100 && userRankRef.current) {
                    userRankRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  }
                }}
                className="bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                View Position
              </button>
            </div>
          </motion.div>
        )}

        {/* Not on Leaderboard Message */}
        {user && !onLeaderboard && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 mb-6"
          >
            <div className="flex items-center gap-3">
              <TrendingUp size={20} className="text-gray-400" />
              <p className="text-gray-300 text-sm">
                Start listening to books to appear on the leaderboard!
              </p>
            </div>
          </motion.div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader className="animate-spin text-blue-500" size={32} />
          </div>
        )}

        {/* Leaderboard Entries */}
        {!isLoading && entries.length === 0 && (
          <div className="text-center py-20">
            {searchQuery ? (
              <>
                <Search size={48} className="text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg">No listeners found matching "{searchQuery}"</p>
                <p className="text-gray-500 text-sm mt-2">Try a different search term</p>
                <button
                  onClick={() => setSearchQuery('')}
                  className="mt-4 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition-colors"
                >
                  Clear Search
                </button>
              </>
            ) : (
              <>
                <Trophy size={48} className="text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg">No listeners yet for this period</p>
                <p className="text-gray-500 text-sm mt-2">Be the first to start listening!</p>
              </>
            )}
          </div>
        )}

        {!isLoading && entries.length > 0 && (
          <>
            {/* Search Results Indicator */}
            {searchQuery && (
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-3 mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-gray-300">
                    <Search size={16} className="text-gray-400" />
                    <span>
                      Found <span className="font-semibold text-white">{entries.length}</span> listener
                      {entries.length !== 1 ? 's' : ''} matching "{searchQuery}"
                    </span>
                  </div>
                  <button
                    onClick={() => setSearchQuery('')}
                    className="text-gray-400 hover:text-white text-sm transition-colors flex items-center gap-1"
                  >
                    <X size={14} />
                    Clear
                  </button>
                </div>
              </div>
            )}

            <div className="space-y-2">
              {entries.map((entry, index) => {
              const isCurrentUser = user?.id === entry.user_id;
              const medal = getMedal(entry.rank);
              const isTopThree = entry.rank <= 3;

              return (
                <motion.div
                  key={entry.user_id}
                  ref={isCurrentUser ? userRankRef : null}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.02 }}
                  className={`relative overflow-hidden rounded-xl transition-all ${
                    isCurrentUser
                      ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-2 border-blue-500 shadow-lg'
                      : isTopThree
                      ? 'bg-gradient-to-r from-gray-800 to-gray-850 border border-gray-700'
                      : 'bg-gray-800/30 border border-gray-800 hover:bg-gray-800/50'
                  }`}
                >
                  <div className="p-4">
                    <div className="flex items-center gap-4">
                      {/* Rank Badge */}
                      <div
                        className={`flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br ${getRankBadgeColor(
                          entry.rank
                        )} flex items-center justify-center shadow-lg`}
                      >
                        {medal ? (
                          <span className="text-2xl">{medal}</span>
                        ) : (
                          <span className="text-white font-bold text-lg">
                            {entry.rank}
                          </span>
                        )}
                      </div>

                      {/* User Info */}
                      <div className="flex-1 min-w-0">
                        {entry.display_mode === 'anonymous' ? (
                          <div>
                            <p className="text-gray-300 font-medium truncate">
                              {entry.display_name || entry.username || `Listener #${entry.user_id.slice(-4)}`}
                            </p>
                            <p className="text-gray-500 text-sm">Anonymous</p>
                          </div>
                        ) : (
                          <div>
                            <button
                              onClick={() => navigate(`/user/${entry.user_id}`)}
                              className="text-left hover:text-blue-400 transition-colors"
                            >
                              <p className="text-white font-medium truncate">
                                {entry.display_name || entry.username || 'User'}
                              </p>
                              {entry.username && entry.display_name && (
                                <p className="text-gray-400 text-sm">@{entry.username}</p>
                              )}
                            </button>
                          </div>
                        )}
                      </div>

                      {/* Admin View History Button */}
                      {isAdmin && (
                        <button
                          onClick={() => setSelectedUserId(entry.user_id)}
                          className="flex-shrink-0 p-2 hover:bg-gray-700 rounded-lg transition-colors group"
                          title="View listening history (Admin)"
                        >
                          <Shield size={16} className="text-gray-500 group-hover:text-blue-400" />
                        </button>
                      )}

                      {/* Listening Hours */}
                      <div className="flex items-center gap-2 text-right">
                        <Clock size={16} className="text-gray-400" />
                        <div>
                          <p className="text-white font-bold text-lg">
                            {formatHours(entry.listening_hours)}
                          </p>
                          <p className="text-gray-400 text-xs">listened</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Current User Indicator */}
                  {isCurrentUser && (
                    <div className="absolute top-2 right-2">
                      <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full font-medium">
                        You
                      </span>
                    </div>
                  )}
                </motion.div>
              );
            })}
            </div>
          </>
        )}

        {/* Footer Info */}
        {!isLoading && entries.length > 0 && (
          <div className="mt-8 text-center text-gray-500 text-sm">
            <p>
              Leaderboard updates every 15 minutes • Only showing users who opted in
            </p>
          </div>
        )}
      </div>

      {/* User Listening History Modal (Admin Only) */}
      {selectedUserId && (
        <UserListeningHistoryModal
          userId={selectedUserId}
          onClose={() => setSelectedUserId(null)}
        />
      )}
    </div>
  );
}
