/**
 * Analytics Page - Detailed Analytics & Reporting
 *
 * Comprehensive analytics dashboard with charts, graphs, and detailed metrics
 */

import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  Users,
  BookOpen,
  MessageSquare,
  Clock,
  Target,
  Award,
  BarChart2,
  PieChart,
  Activity,
  Download,
  Calendar,
  Filter
} from 'lucide-react';
import { analyticsApi } from '../lib/api';
import { useNavigate } from 'react-router-dom';

interface AnalyticsData {
  users: {
    total: number;
    by_role: Record<string, number>;
    growth_rate: number;
  };
  sessions: {
    total: number;
    avg_duration_minutes: number;
    by_subject: Array<{ subject: string; count: number; avg_duration: number }>;
  };
  questions: {
    total: number;
    avg_confidence: number;
    by_subject: Array<{ subject: string; count: number }>;
  };
  materials: {
    total: number;
    by_subject: Array<{ subject: string; count: number }>;
  };
}

export default function Analytics() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);
  const navigate = useNavigate();

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const stats = await analyticsApi.getDashboardStats(timeRange);

      // Transform the data
      setData({
        users: {
          total: stats.users.total,
          by_role: stats.users.by_role,
          growth_rate: (stats.users.new_in_period / stats.users.total) * 100
        },
        sessions: {
          total: stats.sessions.total,
          avg_duration_minutes: stats.sessions.avg_duration_minutes,
          by_subject: []  // Will be populated from detailed analytics
        },
        questions: {
          total: stats.questions.total,
          avg_confidence: stats.questions.avg_confidence_score,
          by_subject: []  // Will be populated from detailed analytics
        },
        materials: {
          total: stats.materials.total,
          by_subject: stats.materials.by_subject
        }
      });
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Failed to load analytics data</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Advanced Analytics</h1>
              <p className="text-gray-600 mt-1">Detailed insights and performance metrics</p>
            </div>
            <div className="flex items-center gap-4">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(Number(e.target.value))}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={365}>Last year</option>
              </select>
              <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                <Download className="w-4 h-4" />
                Export Report
              </button>
              <button
                onClick={() => navigate('/dashboard')}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Key Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <span className="text-sm font-medium text-green-600">+{data.users.growth_rate.toFixed(1)}%</span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{data.users.total.toLocaleString()}</h3>
            <p className="text-gray-600 text-sm">Total Users</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <Activity className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{data.sessions.total.toLocaleString()}</h3>
            <p className="text-gray-600 text-sm">Study Sessions</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <MessageSquare className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{data.questions.total.toLocaleString()}</h3>
            <p className="text-gray-600 text-sm">Questions Asked</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-orange-100 rounded-lg">
                <BookOpen className="w-6 h-6 text-orange-600" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{data.materials.total.toLocaleString()}</h3>
            <p className="text-gray-600 text-sm">Study Materials</p>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* User Distribution */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">User Distribution</h3>
              <PieChart className="w-5 h-5 text-gray-400" />
            </div>
            <div className="space-y-4">
              {Object.entries(data.users.by_role).map(([role, count]) => {
                const percentage = (count / data.users.total) * 100;
                return (
                  <div key={role}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700 capitalize">{role}</span>
                      <span className="text-sm font-semibold text-gray-900">{count} ({percentage.toFixed(1)}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Materials by Subject */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Materials by Subject</h3>
              <BarChart2 className="w-5 h-5 text-gray-400" />
            </div>
            <div className="space-y-4">
              {data.materials.by_subject.slice(0, 5).map((item, index) => {
                const maxCount = Math.max(...data.materials.by_subject.map(s => s.count));
                const percentage = (item.count / maxCount) * 100;
                const colors = ['from-blue-500 to-blue-600', 'from-purple-500 to-purple-600', 'from-green-500 to-green-600', 'from-orange-500 to-orange-600', 'from-pink-500 to-pink-600'];

                return (
                  <div key={item.subject}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">{item.subject}</span>
                      <span className="text-sm font-semibold text-gray-900">{item.count}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`bg-gradient-to-r ${colors[index % colors.length]} h-2 rounded-full transition-all duration-500`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Performance Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-3">
                <Clock className="w-8 h-8 text-blue-600" />
              </div>
              <h4 className="text-3xl font-bold text-gray-900 mb-1">{data.sessions.avg_duration_minutes.toFixed(1)}</h4>
              <p className="text-gray-600 text-sm">Avg Session Duration (min)</p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-3">
                <Target className="w-8 h-8 text-purple-600" />
              </div>
              <h4 className="text-3xl font-bold text-gray-900 mb-1">{(data.questions.avg_confidence * 100).toFixed(1)}%</h4>
              <p className="text-gray-600 text-sm">Avg Confidence Score</p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-3">
                <Award className="w-8 h-8 text-green-600" />
              </div>
              <h4 className="text-3xl font-bold text-gray-900 mb-1">{(data.sessions.total / data.users.total).toFixed(1)}</h4>
              <p className="text-gray-600 text-sm">Sessions per User</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
