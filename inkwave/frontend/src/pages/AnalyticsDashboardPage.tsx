/**
 * Analytics Dashboard Page.
 *
 * Comprehensive analytics for admin monitoring:
 * - User engagement metrics
 * - Provider usage and costs
 * - Revenue tracking
 * - Top books performance
 * - Time series visualizations
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Users,
  DollarSign,
  MessageSquare,
  Book,
  Clock,
  Activity,
  Download,
  Calendar
} from 'lucide-react';
import { api } from '../lib/api';

interface AnalyticsData {
  period_start: string;
  period_end: string;
  total_users: number;
  active_users: number;
  new_users: number;
  total_events: number;
  voice_qa_count: number;
  narration_minutes: number;
  books_viewed: number;
  books_played: number;
  total_cost_credits: number;
  total_revenue_usd: number;
  avg_cost_per_user: number;
  top_books: Array<{
    book_id: string;
    title: string;
    plays: number;
    qa_count: number;
    avg_rating?: number;
  }>;
  provider_stats: {
    stt: { [key: string]: number };
    tts: { [key: string]: number };
    llm: { [key: string]: number };
  };
  time_series: Array<{
    date: string;
    users: number;
    events: number;
    cost: number;
    revenue: number;
  }>;
}

export default function AnalyticsDashboardPage() {
  useEffect(() => {
    document.title = 'Analytics Dashboard - InkWave';
  }, []);

  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<string>('week');

  useEffect(() => {
    loadAnalytics();
  }, [period]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const response = await api.admin.getAnalytics(period);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportData = () => {
    if (!analytics) return;

    const dataStr = JSON.stringify(analytics, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `inkwave-analytics-${period}-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  const calculateGrowth = (current: number, total: number) => {
    if (total === 0) return 0;
    return ((current / total) * 100).toFixed(1);
  };

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
                  <BarChart3 className="w-8 h-8 text-green-400" />
                  Analytics Dashboard
                </h1>
                <p className="text-gray-400 mt-1">
                  Monitor usage, performance, and revenue metrics
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Period Selector */}
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:border-green-500"
              >
                <option value="day">Last 24 Hours</option>
                <option value="week">Last 7 Days</option>
                <option value="month">Last 30 Days</option>
                <option value="year">Last Year</option>
                <option value="all">All Time</option>
              </select>

              <button
                onClick={exportData}
                disabled={!analytics}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading analytics...</p>
            </div>
          </div>
        ) : analytics ? (
          <div className="space-y-8">
            {/* Key Metrics Grid */}
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
                  <span className="text-green-400 text-sm font-semibold flex items-center gap-1">
                    <TrendingUp className="w-4 h-4" />
                    {calculateGrowth(analytics.new_users, analytics.total_users)}%
                  </span>
                </div>
                <h3 className="text-gray-400 text-sm mb-1">Total Users</h3>
                <p className="text-3xl font-bold text-white">{analytics.total_users}</p>
                <p className="text-sm text-gray-500 mt-2">
                  {analytics.active_users} active • {analytics.new_users} new
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center">
                    <MessageSquare className="w-6 h-6 text-cyan-400" />
                  </div>
                  <span className="text-cyan-400 text-sm font-semibold flex items-center gap-1">
                    <Activity className="w-4 h-4" />
                    {analytics.voice_qa_count}
                  </span>
                </div>
                <h3 className="text-gray-400 text-sm mb-1">Voice Q&A</h3>
                <p className="text-3xl font-bold text-white">{analytics.total_events}</p>
                <p className="text-sm text-gray-500 mt-2">Total interactions</p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <Clock className="w-6 h-6 text-purple-400" />
                  </div>
                  <span className="text-purple-400 text-sm font-semibold flex items-center gap-1">
                    <Book className="w-4 h-4" />
                    {analytics.books_played}
                  </span>
                </div>
                <h3 className="text-gray-400 text-sm mb-1">Narration Time</h3>
                <p className="text-3xl font-bold text-white">
                  {Math.round(analytics.narration_minutes / 60)}h
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  {Math.round(analytics.narration_minutes)} minutes total
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-green-400" />
                  </div>
                  <span className="text-green-400 text-sm font-semibold flex items-center gap-1">
                    <TrendingUp className="w-4 h-4" />
                    ${analytics.total_revenue_usd.toFixed(0)}
                  </span>
                </div>
                <h3 className="text-gray-400 text-sm mb-1">Revenue</h3>
                <p className="text-3xl font-bold text-white">
                  ${analytics.total_revenue_usd.toFixed(2)}
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  ${(analytics.total_revenue_usd / Math.max(analytics.active_users, 1)).toFixed(2)} per active user
                </p>
              </motion.div>
            </div>

            {/* Time Series Chart */}
            {analytics.time_series && analytics.time_series.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
              >
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <Activity className="w-6 h-6 text-green-400" />
                    Activity Over Time
                  </h2>
                  <Calendar className="w-5 h-5 text-gray-400" />
                </div>

                <div className="space-y-4">
                  {analytics.time_series.map((dataPoint, index) => {
                    const maxEvents = Math.max(...analytics.time_series.map(d => d.events));
                    const maxRevenue = Math.max(...analytics.time_series.map(d => d.revenue));

                    return (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-400">{formatDate(dataPoint.date)}</span>
                          <div className="flex items-center gap-4">
                            <span className="text-cyan-400">{dataPoint.events} events</span>
                            <span className="text-green-400">${dataPoint.revenue.toFixed(2)}</span>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <div className="flex-1">
                            <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                              <div
                                className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full transition-all duration-300"
                                style={{ width: `${(dataPoint.events / maxEvents) * 100}%` }}
                              />
                            </div>
                          </div>
                          <div className="flex-1">
                            <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                              <div
                                className="bg-gradient-to-r from-green-500 to-emerald-500 h-full transition-all duration-300"
                                style={{ width: `${(dataPoint.revenue / maxRevenue) * 100}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </motion.div>
            )}

            {/* Provider Usage */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* STT */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
              >
                <h3 className="text-lg font-bold text-white mb-4">STT Usage</h3>
                <div className="space-y-3">
                  {Object.entries(analytics.provider_stats.stt || {}).map(([provider, count]) => {
                    const total = Object.values(analytics.provider_stats.stt || {}).reduce((a, b) => a + b, 0);
                    const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : 0;

                    return (
                      <div key={provider}>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-gray-300 font-medium">{provider}</span>
                          <span className="text-cyan-400 font-semibold">{percentage}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full transition-all duration-300"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </motion.div>

              {/* TTS */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
              >
                <h3 className="text-lg font-bold text-white mb-4">TTS Usage</h3>
                <div className="space-y-3">
                  {Object.entries(analytics.provider_stats.tts || {}).map(([provider, count]) => {
                    const total = Object.values(analytics.provider_stats.tts || {}).reduce((a, b) => a + b, 0);
                    const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : 0;

                    return (
                      <div key={provider}>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-gray-300 font-medium">{provider}</span>
                          <span className="text-purple-400 font-semibold">{percentage}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-purple-500 to-pink-500 h-full transition-all duration-300"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </motion.div>

              {/* LLM */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 }}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
              >
                <h3 className="text-lg font-bold text-white mb-4">LLM Usage</h3>
                <div className="space-y-3">
                  {Object.entries(analytics.provider_stats.llm || {}).map(([provider, count]) => {
                    const total = Object.values(analytics.provider_stats.llm || {}).reduce((a, b) => a + b, 0);
                    const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : 0;

                    return (
                      <div key={provider}>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-gray-300 font-medium">{provider}</span>
                          <span className="text-green-400 font-semibold">{percentage}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-green-500 to-emerald-500 h-full transition-all duration-300"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </motion.div>
            </div>

            {/* Top Books */}
            {analytics.top_books && analytics.top_books.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 }}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
              >
                <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                  <TrendingUp className="w-6 h-6 text-yellow-400" />
                  Top Performing Books
                </h2>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
                        <th className="pb-3">Rank</th>
                        <th className="pb-3">Title</th>
                        <th className="pb-3">Plays</th>
                        <th className="pb-3">Q&A Count</th>
                        <th className="pb-3">Rating</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analytics.top_books.map((book, index) => (
                        <tr
                          key={book.book_id}
                          className="text-white border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors"
                        >
                          <td className="py-4">
                            <div className="flex items-center gap-2">
                              <span className={`font-bold ${
                                index === 0
                                  ? 'text-yellow-400'
                                  : index === 1
                                  ? 'text-gray-400'
                                  : index === 2
                                  ? 'text-orange-400'
                                  : 'text-gray-500'
                              }`}>
                                #{index + 1}
                              </span>
                            </div>
                          </td>
                          <td className="py-4 font-semibold">{book.title}</td>
                          <td className="py-4">
                            <span className="text-purple-400">{book.plays}</span>
                          </td>
                          <td className="py-4">
                            <span className="text-cyan-400">{book.qa_count}</span>
                          </td>
                          <td className="py-4">
                            <span className="text-yellow-400">
                              ⭐ {book.avg_rating ? book.avg_rating.toFixed(1) : 'N/A'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}
          </div>
        ) : (
          <div className="text-center py-20">
            <BarChart3 className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No analytics data available</p>
          </div>
        )}
      </div>
    </div>
  );
}
