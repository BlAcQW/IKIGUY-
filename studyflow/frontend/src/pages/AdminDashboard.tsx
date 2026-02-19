/**
 * Admin Dashboard - Enhanced Modern Design
 *
 * Comprehensive analytics dashboard with modern visuals and animations.
 */

import React, { useEffect, useState, useRef } from 'react';
import {
  Users,
  BookOpen,
  MessageSquare,
  TrendingUp,
  Activity,
  DollarSign,
  Award,
  AlertCircle,
  Home,
  Settings,
  BarChart2,
  FileText,
  LogOut,
  Menu,
  X,
  ArrowUp,
  ArrowDown,
  Clock,
  Target,
  Zap,
  Star,
  Building2,
  CreditCard,
  UserCog,
  ChevronDown,
  User as UserCircle,
  Volume2
} from 'lucide-react';
import { analyticsApi } from '../lib/api';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth-context';
import OrganizationSwitcher from '../components/OrganizationSwitcher';

interface DashboardStats {
  users: {
    total: number;
    new_in_period: number;
    by_role: Record<string, number>;
  };
  sessions: {
    total: number;
    in_period: number;
    avg_duration_minutes: number;
    total_learning_time_hours: number;
  };
  questions: {
    total: number;
    in_period: number;
    avg_confidence_score: number;
  };
  materials: {
    total: number;
    new_in_period: number;
    by_subject: Array<{ subject: string; count: number }>;
  };
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(30);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadDashboardStats();
  }, [timeRange]);

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu]);

  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const loadDashboardStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await analyticsApi.getDashboardStats(timeRange);
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard stats');
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({
    icon: Icon,
    title,
    value,
    change,
    subtitle,
    color,
    trend
  }: {
    icon: any;
    title: string;
    value: string | number;
    change?: string;
    subtitle?: string;
    color: string;
    trend?: 'up' | 'down';
  }) => {
    const colorClasses = {
      blue: 'from-blue-500 to-blue-600',
      green: 'from-green-500 to-green-600',
      purple: 'from-purple-500 to-purple-600',
      orange: 'from-orange-500 to-orange-600',
      pink: 'from-pink-500 to-pink-600',
      indigo: 'from-indigo-500 to-indigo-600',
    };

    return (
      <div className="group relative bg-white rounded-2xl p-6 shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border border-gray-100 overflow-hidden">
        {/* Animated Background Gradient */}
        <div className={`absolute inset-0 bg-gradient-to-br ${colorClasses[color as keyof typeof colorClasses]} opacity-0 group-hover:opacity-5 transition-opacity duration-300`}></div>

        <div className="relative z-10">
          <div className="flex items-center justify-between mb-4">
            <div className={`bg-gradient-to-br ${colorClasses[color as keyof typeof colorClasses]} p-3 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300`}>
              <Icon className="w-6 h-6 text-white" />
            </div>
            {change && (
              <div className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${
                trend === 'up' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
              }`}>
                {trend === 'up' ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
                {change}
              </div>
            )}
          </div>

          <h3 className="text-3xl font-bold text-gray-900 mb-1 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-gray-900 group-hover:to-gray-600 transition-all duration-300">
            {value}
          </h3>
          <p className="text-gray-600 text-sm font-medium">{title}</p>
          {subtitle && (
            <p className="text-gray-500 text-xs mt-2 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {subtitle}
            </p>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="text-center">
          <div className="relative">
            <div className="animate-spin rounded-full h-20 w-20 border-4 border-gray-200 mx-auto mb-6"></div>
            <div className="animate-spin rounded-full h-20 w-20 border-t-4 border-blue-600 absolute top-0 left-1/2 -ml-10"></div>
          </div>
          <p className="text-gray-700 font-semibold text-lg animate-pulse">Loading your dashboard...</p>
          <p className="text-gray-500 text-sm mt-2">Fetching latest analytics</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-red-50 to-orange-50 p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md border-t-4 border-red-500 transform hover:scale-105 transition-transform duration-300">
          <div className="flex items-center gap-4 mb-4">
            <div className="bg-red-100 p-4 rounded-full">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-red-900">Oops! Something went wrong</h3>
              <p className="text-red-600 text-sm">Unable to load dashboard</p>
            </div>
          </div>
          <p className="text-gray-700 mb-6 bg-red-50 p-3 rounded-lg">{error}</p>
          <button
            onClick={loadDashboardStats}
            className="w-full bg-gradient-to-r from-red-600 to-red-700 text-white px-6 py-3 rounded-xl hover:from-red-700 hover:to-red-800 transition-all duration-300 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  const calculateTrend = (newCount: number, total: number): number => {
    if (total === 0) return 0;
    return ((newCount / total) * 100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-full bg-gradient-to-b from-gray-900 to-gray-800 text-white transition-all duration-300 z-50 ${
        sidebarOpen ? 'w-64' : 'w-20'
      }`}>
        <div className="p-6">
          <div className="flex items-center justify-between mb-8">
            <h2 className={`font-bold text-xl bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent ${sidebarOpen ? 'block' : 'hidden'}`}>
              StudyFlow
            </h2>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>

          <nav className="space-y-2">
            {[
              { icon: Home, label: 'Dashboard', active: true, path: '/dashboard' },
              { icon: BookOpen, label: 'Materials', active: false, path: '/materials' },
              { icon: FileText, label: 'Upload', active: false, path: '/materials/upload' },
              { icon: DollarSign, label: 'Wallet', active: false, path: '/wallet' },
              { icon: BarChart2, label: 'Analytics', active: false, path: '/analytics' },
              { icon: Volume2, label: 'Voice Settings', active: false, path: '/voice-settings' },
              { icon: Settings, label: 'Settings', active: false, path: '/settings' },
              { icon: Building2, label: 'Admin', active: false, path: '/admin/organizations' },
            ].map((item) => (
              <button
                key={item.label}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  item.active
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 shadow-lg'
                    : 'hover:bg-gray-700'
                }`}
              >
                <item.icon className="w-5 h-5" />
                {sidebarOpen && <span className="font-medium">{item.label}</span>}
              </button>
            ))}
          </nav>

          <div className="absolute bottom-6 left-6 right-6">
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-red-600 hover:bg-opacity-20 transition-colors"
            >
              <LogOut className="w-5 h-5 text-red-400" />
              {sidebarOpen && <span className="font-medium text-red-400">Logout</span>}
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-20'}`}>
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-lg border-b border-gray-200 sticky top-0 z-40 shadow-sm">
          <div className="px-8 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent mb-2">
                  Analytics Dashboard
                </h1>
                <p className="text-gray-600 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-yellow-500" />
                  Real-time system insights and performance metrics
                </p>
              </div>
              <div className="flex items-center gap-4">
                <OrganizationSwitcher />
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(Number(e.target.value))}
                  className="px-5 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white font-medium shadow-sm hover:shadow-md transition-shadow duration-200"
                >
                  <option value={7}>Last 7 days</option>
                  <option value={30}>Last 30 days</option>
                  <option value={90}>Last 90 days</option>
                </select>

                {/* User Menu */}
                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center gap-2 px-4 py-2.5 bg-white border-2 border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-md transition-all duration-200"
                  >
                    <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
                      <UserCircle className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-sm font-semibold text-gray-900 hidden md:block">
                      {user?.email?.split('@')[0] || 'User'}
                    </span>
                    <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${showUserMenu ? 'rotate-180' : ''}`} />
                  </button>

                  {showUserMenu && (
                    <div className="absolute right-0 top-full mt-2 w-64 bg-white border border-gray-200 rounded-xl shadow-xl z-50 overflow-hidden">
                      <div className="p-4 border-b border-gray-100 bg-gray-50">
                        <p className="text-sm font-semibold text-gray-900">{user?.email}</p>
                        <p className="text-xs text-gray-500 mt-1">Signed in</p>
                      </div>
                      <div className="p-2">
                        <button
                          onClick={() => navigate('/settings')}
                          className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 rounded-lg transition-colors text-left"
                        >
                          <Settings className="w-5 h-5 text-gray-600" />
                          <span className="text-sm text-gray-900">Settings</span>
                        </button>
                        <button
                          onClick={handleLogout}
                          className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-red-50 rounded-lg transition-colors text-left"
                        >
                          <LogOut className="w-5 h-5 text-red-600" />
                          <span className="text-sm text-red-600 font-medium">Logout</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="px-8 py-8">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              icon={Users}
              title="Total Users"
              value={stats.users.total.toLocaleString()}
              change={`+${stats.users.new_in_period}`}
              subtitle={`${calculateTrend(stats.users.new_in_period, stats.users.total).toFixed(1)}% growth`}
              color="blue"
              trend="up"
            />
            <StatCard
              icon={Activity}
              title="Study Sessions"
              value={stats.sessions.total.toLocaleString()}
              change={`+${stats.sessions.in_period}`}
              subtitle={`Avg: ${stats.sessions.avg_duration_minutes.toFixed(1)} min`}
              color="green"
              trend="up"
            />
            <StatCard
              icon={MessageSquare}
              title="Questions Asked"
              value={stats.questions.total.toLocaleString()}
              change={`+${stats.questions.in_period}`}
              subtitle={`${(stats.questions.avg_confidence_score * 100).toFixed(1)}% confidence`}
              color="purple"
              trend="up"
            />
            <StatCard
              icon={BookOpen}
              title="Study Materials"
              value={stats.materials.total.toLocaleString()}
              change={`+${stats.materials.new_in_period}`}
              subtitle={`${stats.materials.by_subject.length} subjects`}
              color="orange"
              trend="up"
            />
          </div>

          {/* Secondary Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Learning Activity - Takes 2 columns */}
            <div className="lg:col-span-2 bg-white rounded-2xl p-8 shadow-lg border border-gray-100 hover:shadow-2xl transition-shadow duration-300">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                  <Target className="w-6 h-6 text-blue-600" />
                  Learning Activity
                </h3>
                <div className="flex items-center gap-2 bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-2 rounded-full">
                  <TrendingUp className="w-4 h-4 text-blue-600" />
                  <span className="text-blue-700 font-semibold text-sm">Trending Up</span>
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-gray-700 font-semibold">Total Learning Time</span>
                    <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                      {stats.sessions.total_learning_time_hours.toFixed(1)} hours
                    </span>
                  </div>
                  <div className="relative w-full bg-gray-100 rounded-full h-4 overflow-hidden">
                    <div
                      className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full shadow-lg animate-pulse"
                      style={{ width: '75%' }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">75% of monthly goal achieved</p>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-gray-700 font-semibold">Avg Session Duration</span>
                    <span className="text-2xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                      {stats.sessions.avg_duration_minutes.toFixed(1)} min
                    </span>
                  </div>
                  <div className="relative w-full bg-gray-100 rounded-full h-4 overflow-hidden">
                    <div
                      className="absolute top-0 left-0 h-full bg-gradient-to-r from-green-500 to-emerald-600 rounded-full shadow-lg"
                      style={{ width: `${Math.min((stats.sessions.avg_duration_minutes / 60) * 100, 100)}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Optimal range: 30-60 minutes</p>
                </div>

                <div className="grid grid-cols-3 gap-4 pt-4">
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
                    <div className="text-blue-600 text-xs font-semibold mb-1">Active Today</div>
                    <div className="text-2xl font-bold text-blue-900">{Math.floor(stats.sessions.in_period / timeRange)}</div>
                  </div>
                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100">
                    <div className="text-green-600 text-xs font-semibold mb-1">Completion</div>
                    <div className="text-2xl font-bold text-green-900">89%</div>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-100">
                    <div className="text-purple-600 text-xs font-semibold mb-1">Engagement</div>
                    <div className="text-2xl font-bold text-purple-900">High</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Users by Role */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 hover:shadow-2xl transition-shadow duration-300">
              <h3 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <Star className="w-6 h-6 text-yellow-500" />
                Users by Role
              </h3>
              <div className="space-y-4">
                {Object.entries(stats.users.by_role).map(([role, count], index) => {
                  const colors = ['blue', 'green', 'purple', 'orange', 'pink'];
                  const color = colors[index % colors.length];
                  const percentage = (count / stats.users.total) * 100;

                  return (
                    <div key={role} className="group">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded-full bg-${color}-500 group-hover:scale-125 transition-transform duration-200`}></div>
                          <span className="text-gray-700 font-semibold capitalize">{role}</span>
                        </div>
                        <span className="font-bold text-gray-900">{count}</span>
                      </div>
                      <div className="relative w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                        <div
                          className={`absolute top-0 left-0 h-full bg-gradient-to-r from-${color}-400 to-${color}-600 rounded-full transition-all duration-500 ease-out group-hover:opacity-80`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{percentage.toFixed(1)}% of total</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Materials by Subject */}
          {stats.materials.by_subject.length > 0 && (
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 mb-8 hover:shadow-2xl transition-shadow duration-300">
              <h3 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <BookOpen className="w-6 h-6 text-indigo-600" />
                Materials by Subject
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.materials.by_subject.map((item, index) => {
                  const colors = [
                    'from-blue-500 to-blue-600',
                    'from-green-500 to-green-600',
                    'from-purple-500 to-purple-600',
                    'from-orange-500 to-orange-600',
                    'from-pink-500 to-pink-600',
                    'from-indigo-500 to-indigo-600',
                  ];
                  const colorClass = colors[index % colors.length];

                  return (
                    <div
                      key={item.subject}
                      className="group relative overflow-hidden bg-gradient-to-br from-gray-50 to-white p-6 rounded-xl border-2 border-gray-100 hover:border-transparent hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
                    >
                      <div className={`absolute inset-0 bg-gradient-to-br ${colorClass} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}></div>
                      <div className="relative z-10">
                        <div className="text-gray-700 font-bold mb-3 text-lg">{item.subject}</div>
                        <div className="flex items-center justify-between">
                          <span className={`text-3xl font-bold bg-gradient-to-r ${colorClass} bg-clip-text text-transparent`}>
                            {item.count}
                          </span>
                          <div className={`bg-gradient-to-r ${colorClass} p-2 rounded-lg shadow-lg`}>
                            <FileText className="w-5 h-5 text-white" />
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => navigate('/materials')}
              className="group relative overflow-hidden bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-6 rounded-2xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 font-bold text-lg shadow-xl hover:shadow-2xl transform hover:-translate-y-1"
            >
              <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-10 transition-opacity duration-300"></div>
              <div className="relative z-10 flex items-center justify-center gap-3">
                <Users className="w-6 h-6" />
                Browse Materials
              </div>
            </button>
            <button
              onClick={() => navigate('/materials/upload')}
              className="group relative overflow-hidden bg-gradient-to-r from-green-600 to-emerald-600 text-white px-8 py-6 rounded-2xl hover:from-green-700 hover:to-emerald-700 transition-all duration-300 font-bold text-lg shadow-xl hover:shadow-2xl transform hover:-translate-y-1"
            >
              <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-10 transition-opacity duration-300"></div>
              <div className="relative z-10 flex items-center justify-center gap-3">
                <TrendingUp className="w-6 h-6" />
                Upload Content
              </div>
            </button>
            <button className="group relative overflow-hidden bg-gradient-to-r from-purple-600 to-pink-600 text-white px-8 py-6 rounded-2xl hover:from-purple-700 hover:to-pink-700 transition-all duration-300 font-bold text-lg shadow-xl hover:shadow-2xl transform hover:-translate-y-1">
              <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-10 transition-opacity duration-300"></div>
              <div className="relative z-10 flex items-center justify-center gap-3">
                <BarChart2 className="w-6 h-6" />
                System Health
              </div>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
