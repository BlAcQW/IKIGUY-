/**
 * Admin Dashboard Page.
 *
 * Overview of the admin panel with quick stats and navigation to admin sections.
 * Integrates with unified consumption tracking for real-time activity metrics.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Settings,
  Upload,
  BarChart3,
  Users,
  Cpu,
  TrendingUp,
  DollarSign,
  MessageSquare,
  Book,
  Shield,
  Headphones,
  CheckCircle,
  Clock,
  Activity
} from 'lucide-react';
import { api } from '../lib/api';
import ReportBug from '../components/ReportBug';
import Header from '../components/Header';

interface AdminStats {
  total_users: number;
  active_users: number;
  voice_qa_count: number;
  narration_minutes: number;
  total_cost_credits: number;
  total_revenue_usd: number;
}

interface ConsumptionDashboardStats {
  period_days: number;
  total_events: number;
  unique_users: number;
  unique_books: number;
  total_sessions: number;
  total_duration_hours: number;
  total_completions: number;
}

export default function AdminDashboardPage() {
  useEffect(() => {
    document.title = 'Admin Dashboard - InkWave';
  }, []);

  const [stats, setStats] = useState<AdminStats | null>(null);
  const [consumptionStats, setConsumptionStats] = useState<ConsumptionDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAllStats();
  }, []);

  const loadAllStats = async () => {
    try {
      // Load both admin stats and consumption stats in parallel
      const [adminResponse, consumptionResponse] = await Promise.all([
        api.admin.getAnalytics('week'),
        api.consumption.admin.getDashboard(7).catch(() => ({ data: null }))
      ]);
      setStats(adminResponse.data);
      if (consumptionResponse.data) {
        setConsumptionStats(consumptionResponse.data);
      }
    } catch (error) {
      console.error('Failed to load admin stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const adminSections = [
    {
      title: 'Book Creation',
      description: 'Upload PDF books and cover images for narration',
      icon: Upload,
      path: '/admin/books/upload',
      color: 'from-purple-500 to-pink-500'
    },
    {
      title: 'Book Moderation',
      description: 'Hide books, manage hidden content, view audit logs',
      icon: Shield,
      path: '/admin/books/moderation',
      color: 'from-red-500 to-orange-500'
    },
    {
      title: 'Provider Management',
      description: 'Configure STT, TTS, and LLM providers',
      icon: Cpu,
      path: '/admin/providers',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      title: 'Analytics',
      description: 'View usage stats and performance metrics',
      icon: BarChart3,
      path: '/admin/analytics',
      color: 'from-green-500 to-emerald-500'
    },
    {
      title: 'User Analytics',
      description: 'Monitor user signups, activity, and book engagement',
      icon: BarChart3,
      path: '/admin/analytics/users',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      title: 'User Management',
      description: 'Manage users and permissions',
      icon: Users,
      path: '/admin/users',
      color: 'from-orange-500 to-red-500'
    }
  ];

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Page Header */}
      <div className="border-b border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                <Settings className="w-8 h-8 text-cyan-400" />
                Admin Dashboard
              </h1>
              <p className="text-gray-400 mt-1">
                Manage your InkWave platform
              </p>
            </div>
            <Link
              to="/"
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              Back to App
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Grid */}
        {!loading && stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Total Users</p>
                  <p className="text-3xl font-bold text-white mt-1">
                    {stats.total_users}
                  </p>
                  <p className="text-green-400 text-sm mt-2">
                    {stats.active_users} active
                  </p>
                </div>
                <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <Users className="w-6 h-6 text-blue-400" />
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Voice Q&A</p>
                  <p className="text-3xl font-bold text-white mt-1">
                    {stats.voice_qa_count}
                  </p>
                  <p className="text-cyan-400 text-sm mt-2">This week</p>
                </div>
                <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center">
                  <MessageSquare className="w-6 h-6 text-cyan-400" />
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Narration Time</p>
                  <p className="text-3xl font-bold text-white mt-1">
                    {Math.round(stats.narration_minutes / 60)}h
                  </p>
                  <p className="text-purple-400 text-sm mt-2">
                    {Math.round(stats.narration_minutes)} minutes
                  </p>
                </div>
                <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                  <Book className="w-6 h-6 text-purple-400" />
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Revenue</p>
                  <p className="text-3xl font-bold text-white mt-1">
                    ${stats.total_revenue_usd.toFixed(2)}
                  </p>
                  <p className="text-green-400 text-sm mt-2">
                    {stats.total_cost_credits} credits used
                  </p>
                </div>
                <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-green-400" />
                </div>
              </div>
            </motion.div>
          </div>
        )}

        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6 animate-pulse"
              >
                <div className="h-20 bg-gray-700 rounded"></div>
              </div>
            ))}
          </div>
        )}

        {/* Consumption Activity Stats (from unified tracking) */}
        {!loading && consumptionStats && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mb-8"
          >
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-purple-400" />
              <h2 className="text-lg font-semibold text-white">
                Consumption Activity (Last 7 Days)
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 backdrop-blur-sm border border-purple-700/50 rounded-xl p-6"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-purple-300 text-sm">Active Listeners</p>
                    <p className="text-3xl font-bold text-white mt-1">
                      {consumptionStats.unique_users}
                    </p>
                    <p className="text-purple-400 text-sm mt-2">
                      {consumptionStats.total_sessions} sessions
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <Headphones className="w-6 h-6 text-purple-400" />
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 backdrop-blur-sm border border-blue-700/50 rounded-xl p-6"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-300 text-sm">Books Consumed</p>
                    <p className="text-3xl font-bold text-white mt-1">
                      {consumptionStats.unique_books}
                    </p>
                    <p className="text-blue-400 text-sm mt-2">
                      {consumptionStats.total_events} events
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <Book className="w-6 h-6 text-blue-400" />
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-gradient-to-br from-cyan-900/50 to-cyan-800/30 backdrop-blur-sm border border-cyan-700/50 rounded-xl p-6"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-cyan-300 text-sm">Listening Time</p>
                    <p className="text-3xl font-bold text-white mt-1">
                      {consumptionStats.total_duration_hours.toFixed(1)}h
                    </p>
                    <p className="text-cyan-400 text-sm mt-2">
                      Total playback
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center">
                    <Clock className="w-6 h-6 text-cyan-400" />
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-gradient-to-br from-green-900/50 to-green-800/30 backdrop-blur-sm border border-green-700/50 rounded-xl p-6"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-green-300 text-sm">Completions</p>
                    <p className="text-3xl font-bold text-white mt-1">
                      {consumptionStats.total_completions}
                    </p>
                    <p className="text-green-400 text-sm mt-2">
                      Books finished
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                    <CheckCircle className="w-6 h-6 text-green-400" />
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        )}

        {/* Admin Sections Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {adminSections.map((section, index) => (
            <motion.div
              key={section.path}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 + 0.4 }}
            >
              <Link
                to={section.path}
                className="block group"
              >
                <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-8 hover:border-cyan-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/10">
                  <div className="flex items-start gap-6">
                    <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${section.color} flex items-center justify-center group-hover:scale-110 transition-transform`}>
                      <section.icon className="w-8 h-8 text-white" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-white mb-2 group-hover:text-cyan-400 transition-colors">
                        {section.title}
                      </h3>
                      <p className="text-gray-400">
                        {section.description}
                      </p>
                    </div>
                    <TrendingUp className="w-5 h-5 text-gray-600 group-hover:text-cyan-400 transition-colors" />
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mt-8 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Link
              to="/admin/books/upload"
              className="px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg font-semibold transition-all duration-300 flex items-center justify-center gap-2"
            >
              <Upload className="w-5 h-5" />
              Upload New Book
            </Link>
            <Link
              to="/admin/analytics"
              className="px-6 py-4 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-lg font-semibold transition-all duration-300 flex items-center justify-center gap-2"
            >
              <BarChart3 className="w-5 h-5" />
              View Analytics
            </Link>
            <Link
              to="/admin/analytics/users"
              className="px-6 py-4 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white rounded-lg font-semibold transition-all duration-300 flex items-center justify-center gap-2"
            >
              <Users className="w-5 h-5" />
              User Analytics
            </Link>
            <Link
              to="/admin/providers"
              className="px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg font-semibold transition-all duration-300 flex items-center justify-center gap-2"
            >
              <Cpu className="w-5 h-5" />
              Configure Providers
            </Link>
          </div>
        </div>
      </div>
      
      {/* Report Bug Widget - Only on Admin Page */}
      <ReportBug />
      </div>
    </>
  );
}
