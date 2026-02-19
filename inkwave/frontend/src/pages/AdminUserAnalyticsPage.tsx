/**
 * Admin User Analytics Page.
 *
 * Comprehensive user analytics for admin monitoring:
 * - Number of signed up users
 * - Number of logged in users
 * - Where most users spend most of their time
 * - How much of what book each user has played
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Users,
  UserCheck,
  Clock,
  Book,
  TrendingUp,
  Activity,
  BarChart3,
  Search,
  Filter,
  MessageSquare
} from 'lucide-react';
import { api } from '../lib/api';

interface UserStats {
  total_signed_up: number;
  total_logged_in: number;
  active_users_30d: number;
  active_users_7d: number;
}

interface UserActivity {
  total_reading_time_minutes: number;
  total_interactions: number;
  unique_books_accessed: number;
  total_sessions: number;
  average_session_duration_minutes: number;
  primary_activity: string;
}

interface CurrentlyLoggedInUser {
  user_id: string;
  email: string;
  display_name?: string;
  last_active: string;
  minutes_ago: number;
}

interface CurrentlyListeningUser {
  user_id: string;
  email: string;
  display_name?: string;
  book_id: string;
  book_title: string;
  book_author: string;
  book_cover_url?: string;
  current_chunk_index: number;
  total_chunks: number;
  progress_percentage: number;
  last_accessed: string;
  seconds_ago: number;
}

interface UserBookProgress {
  user_id: string;
  user_email: string;
  user_display_name?: string;
  book_id: string;
  book_title: string;
  book_author: string;
  current_chunk_index: number;
  total_chunks: number;
  progress_percentage: number;
  time_spent_minutes: number;
  is_completed: boolean;
  last_accessed: string;
  progress_quality?: string;
}

interface UserAnalytics {
  user_id: string;
  email: string;
  display_name?: string;
  signup_date: string;
  last_active: string;
  total_listening_minutes: number;
  unique_books_count: number;
  sessions_count: number;
  wallet_balance: number;
}

export default function AdminUserAnalyticsPage() {
  useEffect(() => {
    document.title = 'User Analytics - InkWave';
  }, []);

  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [userActivity, setUserActivity] = useState<UserActivity | null>(null);
  const [userAnalytics, setUserAnalytics] = useState<UserAnalytics[]>([]);
  const [bookProgress, setBookProgress] = useState<UserBookProgress[]>([]);
  const [currentlyLoggedIn, setCurrentlyLoggedIn] = useState<{ count: number; users: CurrentlyLoggedInUser[] } | null>(null);
  const [currentlyListening, setCurrentlyListening] = useState<{ count: number; users: CurrentlyListeningUser[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'books'>('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'usage' | 'signup_date' | 'revenue'>('usage');
  const [showLoggedInModal, setShowLoggedInModal] = useState(false);
  const [showListeningModal, setShowListeningModal] = useState(false);

  useEffect(() => {
    loadAllData();
  }, [sortBy]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      // Load all analytics in parallel
      const [statsRes, activityRes, usersRes, progressRes, loggedInRes, listeningRes] = await Promise.all([
        api.admin.getUserStats(),
        api.admin.getUserActivity(),
        api.admin.getUserAnalytics(100, sortBy),
        api.admin.getUserBookProgress(undefined, 100),
        api.admin.getCurrentlyLoggedIn(),
        api.admin.getCurrentlyListening()
      ]);

      setUserStats(statsRes.data);
      setUserActivity(activityRes.data);
      setUserAnalytics(usersRes.data.users || []);
      setBookProgress(progressRes.data.progress_records || []);
      setCurrentlyLoggedIn(loggedInRes.data);
      setCurrentlyListening(listeningRes.data);
    } catch (error) {
      console.error('Failed to load user analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatMinutes = (minutes: number) => {
    if (minutes < 60) {
      return `${Math.round(minutes)}m`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'Never';
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const filteredUsers = userAnalytics.filter(user =>
    user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (user.display_name && user.display_name.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const filteredBookProgress = bookProgress.filter(progress =>
    progress.user_email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    progress.book_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    progress.book_author.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <div className="border-b border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/admin"
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-6 h-6 text-gray-400" />
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                  <Users className="w-8 h-8 text-blue-400" />
                  User Analytics
                </h1>
                <p className="text-gray-400 mt-1">
                  Monitor user signups, activity, and book engagement
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading analytics...</p>
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Tabs */}
            <div className="flex items-center gap-2 border-b border-gray-700">
              <button
                onClick={() => setActiveTab('overview')}
                className={`px-6 py-3 font-semibold transition-colors ${
                  activeTab === 'overview'
                    ? 'text-blue-400 border-b-2 border-blue-400'
                    : 'text-gray-400 hover:text-gray-300'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab('users')}
                className={`px-6 py-3 font-semibold transition-colors ${
                  activeTab === 'users'
                    ? 'text-blue-400 border-b-2 border-blue-400'
                    : 'text-gray-400 hover:text-gray-300'
                }`}
              >
                Users ({userAnalytics.length})
              </button>
              <button
                onClick={() => setActiveTab('books')}
                className={`px-6 py-3 font-semibold transition-colors ${
                  activeTab === 'books'
                    ? 'text-blue-400 border-b-2 border-blue-400'
                    : 'text-gray-400 hover:text-gray-300'
                }`}
              >
                Book Progress ({bookProgress.length})
              </button>
            </div>

            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Real-time Activity Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    onClick={() => setShowLoggedInModal(true)}
                    className="bg-gradient-to-br from-emerald-900/50 to-emerald-800/30 backdrop-blur-sm border border-emerald-700/50 rounded-xl p-6 cursor-pointer hover:border-emerald-500 transition-all hover:shadow-lg hover:shadow-emerald-500/20"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
                        <UserCheck className="w-6 h-6 text-emerald-400" />
                      </div>
                      <div className="text-xs text-emerald-400 font-semibold">LIVE</div>
                    </div>
                    <h3 className="text-emerald-400 text-sm mb-1 font-semibold">Currently Logged In</h3>
                    <p className="text-4xl font-bold text-white">{currentlyLoggedIn?.count || 0}</p>
                    <p className="text-sm text-emerald-300/70 mt-2">
                      Active in last 15 minutes • Click to view
                    </p>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    onClick={() => setShowListeningModal(true)}
                    className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 backdrop-blur-sm border border-purple-700/50 rounded-xl p-6 cursor-pointer hover:border-purple-500 transition-all hover:shadow-lg hover:shadow-purple-500/20"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                        <Book className="w-6 h-6 text-purple-400" />
                      </div>
                      <div className="text-xs text-purple-400 font-semibold">LIVE</div>
                    </div>
                    <h3 className="text-purple-400 text-sm mb-1 font-semibold">Currently Listening</h3>
                    <p className="text-4xl font-bold text-white">{currentlyListening?.count || 0}</p>
                    <p className="text-sm text-purple-300/70 mt-2">
                      Active in last 3 minutes • Click to view
                    </p>
                  </motion.div>
                </div>

                {/* User Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                        <Users className="w-6 h-6 text-blue-400" />
                      </div>
                    </div>
                    <h3 className="text-gray-400 text-sm mb-1">Total Signed Up</h3>
                    <p className="text-3xl font-bold text-white">{userStats?.total_signed_up || 0}</p>
                    <p className="text-sm text-gray-500 mt-2">
                      All registered users
                    </p>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                        <UserCheck className="w-6 h-6 text-green-400" />
                      </div>
                    </div>
                    <h3 className="text-gray-400 text-sm mb-1">Total Logged In</h3>
                    <p className="text-3xl font-bold text-white">{userStats?.total_logged_in || 0}</p>
                    <p className="text-sm text-gray-500 mt-2">
                      Users who have logged in
                    </p>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                        <Activity className="w-6 h-6 text-purple-400" />
                      </div>
                    </div>
                    <h3 className="text-gray-400 text-sm mb-1">Active (30 days)</h3>
                    <p className="text-3xl font-bold text-white">{userStats?.active_users_30d || 0}</p>
                    <p className="text-sm text-gray-500 mt-2">
                      {userStats?.active_users_7d || 0} active in last 7 days
                    </p>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center">
                        <Clock className="w-6 h-6 text-cyan-400" />
                      </div>
                    </div>
                    <h3 className="text-gray-400 text-sm mb-1">Total Reading Time</h3>
                    <p className="text-3xl font-bold text-white">
                      {userActivity ? formatMinutes(userActivity.total_reading_time_minutes) : '0m'}
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      Across all users
                    </p>
                  </motion.div>
                </div>

                {/* User Activity Section */}
                {userActivity && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
                  >
                    <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                      <Activity className="w-6 h-6 text-purple-400" />
                      Where Users Spend Their Time
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      <div className="bg-gray-700/30 rounded-lg p-4">
                        <div className="flex items-center gap-3 mb-2">
                          <Book className="w-5 h-5 text-purple-400" />
                          <h3 className="font-semibold text-white">Reading Sessions</h3>
                        </div>
                        <p className="text-2xl font-bold text-purple-400">{userActivity.total_sessions}</p>
                        <p className="text-sm text-gray-400 mt-1">
                          Avg: {formatMinutes(userActivity.average_session_duration_minutes)} per session
                        </p>
                      </div>

                      <div className="bg-gray-700/30 rounded-lg p-4">
                        <div className="flex items-center gap-3 mb-2">
                          <MessageSquare className="w-5 h-5 text-cyan-400" />
                          <h3 className="font-semibold text-white">Q&A Interactions</h3>
                        </div>
                        <p className="text-2xl font-bold text-cyan-400">{userActivity.total_interactions}</p>
                        <p className="text-sm text-gray-400 mt-1">
                          Total questions asked
                        </p>
                      </div>

                      <div className="bg-gray-700/30 rounded-lg p-4">
                        <div className="flex items-center gap-3 mb-2">
                          <TrendingUp className="w-5 h-5 text-green-400" />
                          <h3 className="font-semibold text-white">Activity Breakdown</h3>
                        </div>
                        <p className="text-base font-bold text-green-400">{userActivity.primary_activity}</p>
                        <p className="text-sm text-gray-400 mt-1">
                          {userActivity.unique_books_accessed} unique books accessed
                        </p>
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
              <div className="space-y-6">
                {/* Search and Filter */}
                <div className="flex items-center gap-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search users by email or name..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <Filter className="w-5 h-5 text-gray-400" />
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value as any)}
                      className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="usage">Sort by Usage</option>
                      <option value="signup_date">Sort by Signup Date</option>
                      <option value="revenue">Sort by Balance</option>
                    </select>
                  </div>
                </div>

                {/* Users Table */}
                <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-700/50">
                        <tr>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">User</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Signup Date</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Last Active</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Listening Time</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Books</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Sessions</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Balance</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-700">
                        {filteredUsers.map((user) => (
                          <tr key={user.user_id} className="hover:bg-gray-700/30 transition-colors">
                            <td className="px-6 py-4">
                              <div>
                                <p className="text-white font-medium">{user.display_name || user.email}</p>
                                <p className="text-sm text-gray-400">{user.email}</p>
                              </div>
                            </td>
                            <td className="px-6 py-4 text-gray-300">{formatDate(user.signup_date)}</td>
                            <td className="px-6 py-4 text-gray-300">{formatDate(user.last_active)}</td>
                            <td className="px-6 py-4">
                              <span className="text-purple-400 font-semibold">
                                {formatMinutes(user.total_listening_minutes)}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              <span className="text-blue-400 font-semibold">{user.unique_books_count}</span>
                            </td>
                            <td className="px-6 py-4">
                              <span className="text-cyan-400 font-semibold">{user.sessions_count}</span>
                            </td>
                            <td className="px-6 py-4">
                              <span className="text-green-400 font-semibold">${(user.wallet_balance / 100).toFixed(2)}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Books Tab */}
            {activeTab === 'books' && (
              <div className="space-y-6">
                {/* Search */}
                <div className="flex items-center gap-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search by user, book title, or author..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                {/* Book Progress Table */}
                <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-700/50">
                        <tr>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">User</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Book</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Progress</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Time Spent</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Status</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Last Accessed</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-700">
                        {filteredBookProgress.map((progress, index) => (
                          <tr key={`${progress.user_id}-${progress.book_id}-${index}`} className="hover:bg-gray-700/30 transition-colors">
                            <td className="px-6 py-4">
                              <div>
                                <p className="text-white font-medium">{progress.user_display_name || progress.user_email}</p>
                                <p className="text-sm text-gray-400">{progress.user_email}</p>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div>
                                <p className="text-white font-medium">{progress.book_title}</p>
                                <p className="text-sm text-gray-400">{progress.book_author}</p>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-3">
                                <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden min-w-[100px]">
                                  <div
                                    className="bg-gradient-to-r from-blue-500 to-purple-500 h-full transition-all"
                                    style={{ width: `${Math.min(progress.progress_percentage, 100)}%` }}
                                  />
                                </div>
                                <span className="text-sm text-gray-300 font-semibold min-w-[50px]">
                                  {progress.progress_percentage.toFixed(1)}%
                                </span>
                              </div>
                              <p className="text-xs text-gray-500 mt-1">
                                {progress.current_chunk_index} / {progress.total_chunks} chunks
                              </p>
                            </td>
                            <td className="px-6 py-4">
                              <span className="text-purple-400 font-semibold">
                                {formatMinutes(progress.time_spent_minutes)}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex flex-col gap-1">
                                {progress.is_completed ? (
                                  <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-sm font-semibold inline-block">
                                    Completed
                                  </span>
                                ) : (
                                  <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-sm font-semibold inline-block">
                                    In Progress
                                  </span>
                                )}
                                {progress.progress_quality === 'likely_skipped' && (
                                  <span className="px-2 py-1 bg-orange-500/20 text-orange-400 rounded text-xs font-medium inline-block">
                                    ⚠️ Likely Skipped
                                  </span>
                                )}
                                {progress.progress_quality === 'suspicious' && (
                                  <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs font-medium inline-block">
                                    ⚠️ Fast Progress
                                  </span>
                                )}
                                {progress.progress_quality === 'sequential' && (
                                  <span className="px-2 py-1 bg-green-500/10 text-green-400 rounded text-xs font-medium inline-block">
                                    ✓ Sequential
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 text-gray-300 text-sm">
                              {formatDate(progress.last_accessed)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Currently Logged In Modal */}
      {showLoggedInModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gray-800 border border-gray-700 rounded-xl max-w-3xl w-full max-h-[80vh] overflow-hidden"
          >
            <div className="p-6 border-b border-gray-700 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <UserCheck className="w-6 h-6 text-emerald-400" />
                  Currently Logged In
                </h2>
                <p className="text-gray-400 mt-1">
                  {currentlyLoggedIn?.count || 0} users active in last 15 minutes
                </p>
              </div>
              <button
                onClick={() => setShowLoggedInModal(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
              {currentlyLoggedIn && currentlyLoggedIn.users.length > 0 ? (
                <div className="space-y-3">
                  {currentlyLoggedIn.users.map((user) => (
                    <div
                      key={user.user_id}
                      className="bg-gray-700/50 rounded-lg p-4 hover:bg-gray-700 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-semibold">{user.display_name || user.email}</p>
                          <p className="text-sm text-gray-400">{user.email}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-emerald-400 font-semibold">
                            {user.minutes_ago === 0 ? 'Just now' : `${user.minutes_ago}m ago`}
                          </p>
                          <p className="text-xs text-gray-500">Last active</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-8">No users currently logged in</p>
              )}
            </div>
          </motion.div>
        </div>
      )}

      {/* Currently Listening Modal */}
      {showListeningModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gray-800 border border-gray-700 rounded-xl max-w-4xl w-full max-h-[80vh] overflow-hidden"
          >
            <div className="p-6 border-b border-gray-700 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <Book className="w-6 h-6 text-purple-400" />
                  Currently Listening
                </h2>
                <p className="text-gray-400 mt-1">
                  {currentlyListening?.count || 0} users listening in last 3 minutes
                </p>
              </div>
              <button
                onClick={() => setShowListeningModal(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
              {currentlyListening && currentlyListening.users.length > 0 ? (
                <div className="space-y-4">
                  {currentlyListening.users.map((user) => (
                    <div
                      key={`${user.user_id}-${user.book_id}`}
                      className="bg-gray-700/50 rounded-lg p-4 hover:bg-gray-700 transition-colors"
                    >
                      <div className="flex gap-4">
                        {user.book_cover_url && (
                          <img
                            src={user.book_cover_url}
                            alt={user.book_title}
                            className="w-16 h-20 object-cover rounded"
                          />
                        )}
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <p className="text-white font-semibold">{user.display_name || user.email}</p>
                              <p className="text-sm text-gray-400">{user.email}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-purple-400 font-semibold">
                                {user.seconds_ago < 60 ? `${user.seconds_ago}s ago` : `${Math.floor(user.seconds_ago / 60)}m ago`}
                              </p>
                              <p className="text-xs text-gray-500">Last activity</p>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div>
                              <p className="text-white font-medium">{user.book_title}</p>
                              <p className="text-sm text-gray-400">{user.book_author}</p>
                            </div>
                            <div>
                              <div className="flex items-center gap-3">
                                <div className="flex-1 bg-gray-600 rounded-full h-2 overflow-hidden">
                                  <div
                                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-full transition-all"
                                    style={{ width: `${Math.min(user.progress_percentage, 100)}%` }}
                                  />
                                </div>
                                <span className="text-sm text-gray-300 font-semibold min-w-[50px]">
                                  {user.progress_percentage.toFixed(1)}%
                                </span>
                              </div>
                              <p className="text-xs text-gray-500 mt-1">
                                Chunk {user.current_chunk_index + 1} / {user.total_chunks}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-8">No users currently listening</p>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
