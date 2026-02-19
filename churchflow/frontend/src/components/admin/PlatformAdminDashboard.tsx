/**
 * Platform Admin Dashboard - ChurchFlow SaaS
 *
 * Dashboard for platform owners to manage all churches,
 * monitor revenue, usage, and provide support.
 */

import { useState, useEffect } from 'react';
import {
  TrendingUp,
  Users,
  DollarSign,
  Building2,
  Search,
  Filter,
  ChevronDown,
  ExternalLink,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { ResponsiveTable } from '../common';

// ==================== Types ====================

interface DashboardMetrics {
  overview: {
    total_churches: number;
    active_subscriptions: number;
    mrr: number;
    arr: number;
  };
  subscriptions_by_plan: {
    free: number;
    standard: number;
    premium: number;
  };
  recent_signups: number;
}

interface ChurchSummary {
  organization_id: string;
  name: string;
  email: string;
  phone?: string;
  created_at: string;
  subscription_plan: string;
  subscription_status: string;
  members_count: number;
  sms_credits: number;
  storage_mb: number;
}

interface RevenueMetrics {
  mrr: number;
  arr: number;
  total_subscriptions: number;
  active_subscriptions: number;
  churned_this_month: number;
  new_this_month: number;
  revenue_by_plan: {
    free: number;
    standard: number;
    premium: number;
  };
}

interface UsageMetrics {
  total_churches: number;
  total_members: number;
  total_sms_sent: number;
  total_storage_gb: number;
  active_churches_30d: number;
  churches_by_plan: {
    free: number;
    standard: number;
    premium: number;
  };
}

export interface PlatformAdminDashboardProps {
  apiBaseUrl: string;
  onError: (message: string) => void;
}

// ==================== Main Component ====================

export default function PlatformAdminDashboard({
  apiBaseUrl,
  onError,
}: PlatformAdminDashboardProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'churches' | 'revenue' | 'usage'>(
    'overview'
  );
  const [loading, setLoading] = useState(true);
  const [dashboardMetrics, setDashboardMetrics] = useState<DashboardMetrics | null>(null);
  const [churches, setChurches] = useState<ChurchSummary[]>([]);
  const [revenueMetrics, setRevenueMetrics] = useState<RevenueMetrics | null>(null);
  const [usageMetrics, setUsageMetrics] = useState<UsageMetrics | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [planFilter, setPlanFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    loadDashboardData();
  }, []);

  useEffect(() => {
    if (activeTab === 'churches' && churches.length === 0) {
      loadChurches();
    } else if (activeTab === 'revenue' && !revenueMetrics) {
      loadRevenueMetrics();
    } else if (activeTab === 'usage' && !usageMetrics) {
      loadUsageMetrics();
    }
  }, [activeTab]);

  // ==================== API Calls ====================

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${apiBaseUrl}/api/v1/platform-admin/dashboard`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load dashboard data');
      }

      const data = await response.json();
      setDashboardMetrics(data);
    } catch (error: any) {
      onError(error.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadChurches = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams();
      if (planFilter !== 'all') params.append('plan', planFilter);
      if (statusFilter !== 'all') params.append('status', statusFilter);

      const response = await fetch(
        `${apiBaseUrl}/api/v1/platform-admin/churches?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to load churches');
      }

      const data = await response.json();
      setChurches(data);
    } catch (error: any) {
      onError(error.message || 'Failed to load churches');
    } finally {
      setLoading(false);
    }
  };

  const loadRevenueMetrics = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${apiBaseUrl}/api/v1/platform-admin/revenue`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load revenue metrics');
      }

      const data = await response.json();
      setRevenueMetrics(data);
    } catch (error: any) {
      onError(error.message || 'Failed to load revenue metrics');
    } finally {
      setLoading(false);
    }
  };

  const loadUsageMetrics = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${apiBaseUrl}/api/v1/platform-admin/usage`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load usage metrics');
      }

      const data = await response.json();
      setUsageMetrics(data);
    } catch (error: any) {
      onError(error.message || 'Failed to load usage metrics');
    } finally {
      setLoading(false);
    }
  };

  // ==================== Filtering ====================

  const filteredChurches = churches.filter((church) => {
    const matchesSearch =
      church.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      church.email.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  // ==================== Formatters ====================

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // ==================== Render ====================

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Platform Admin</h1>
          <p className="text-gray-600 mt-1">Manage all churches and monitor platform health</p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {[
                { id: 'overview', label: 'Overview', icon: TrendingUp },
                { id: 'churches', label: 'Churches', icon: Building2 },
                { id: 'revenue', label: 'Revenue', icon: DollarSign },
                { id: 'usage', label: 'Usage', icon: Users },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <tab.icon className="w-5 h-5 mr-2" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <>
            {/* Overview Tab */}
            {activeTab === 'overview' && dashboardMetrics && (
              <div className="space-y-6">
                {/* Key Metrics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-600">Total Churches</span>
                      <Building2 className="w-5 h-5 text-blue-600" />
                    </div>
                    <div className="text-3xl font-bold text-gray-900">
                      {dashboardMetrics.overview.total_churches}
                    </div>
                    <div className="text-sm text-green-600 mt-2">
                      +{dashboardMetrics.recent_signups} this month
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-600">Active Subscriptions</span>
                      <Users className="w-5 h-5 text-green-600" />
                    </div>
                    <div className="text-3xl font-bold text-gray-900">
                      {dashboardMetrics.overview.active_subscriptions}
                    </div>
                    <div className="text-sm text-gray-500 mt-2">Paying customers</div>
                  </div>

                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-600">Monthly Recurring Revenue</span>
                      <DollarSign className="w-5 h-5 text-yellow-600" />
                    </div>
                    <div className="text-3xl font-bold text-gray-900">
                      {formatCurrency(dashboardMetrics.overview.mrr)}
                    </div>
                    <div className="text-sm text-gray-500 mt-2">MRR</div>
                  </div>

                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-600">Annual Recurring Revenue</span>
                      <TrendingUp className="w-5 h-5 text-purple-600" />
                    </div>
                    <div className="text-3xl font-bold text-gray-900">
                      {formatCurrency(dashboardMetrics.overview.arr)}
                    </div>
                    <div className="text-sm text-gray-500 mt-2">ARR</div>
                  </div>
                </div>

                {/* Plan Distribution */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold mb-4">Subscriptions by Plan</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-gray-900">
                        {dashboardMetrics.subscriptions_by_plan.free}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Free Plan</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-600">
                        {dashboardMetrics.subscriptions_by_plan.standard}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Standard Plan</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-purple-600">
                        {dashboardMetrics.subscriptions_by_plan.premium}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Premium Plan</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Churches Tab */}
            {activeTab === 'churches' && (
              <div>
                {/* Filters */}
                <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
                  <div className="flex flex-col md:flex-row md:items-center md:space-x-4 space-y-4 md:space-y-0">
                    <div className="flex-1 relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                      <input
                        type="text"
                        placeholder="Search churches..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <select
                      value={planFilter}
                      onChange={(e) => {
                        setPlanFilter(e.target.value);
                        loadChurches();
                      }}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Plans</option>
                      <option value="free">Free</option>
                      <option value="standard">Standard</option>
                      <option value="premium">Premium</option>
                    </select>
                    <select
                      value={statusFilter}
                      onChange={(e) => {
                        setStatusFilter(e.target.value);
                        loadChurches();
                      }}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Statuses</option>
                      <option value="active">Active</option>
                      <option value="trialing">Trialing</option>
                      <option value="canceled">Canceled</option>
                    </select>
                  </div>
                </div>

                {/* Churches Table */}
                <ResponsiveTable
                  columns={[
                    {
                      key: 'name',
                      label: 'Church',
                      render: (value, church) => (
                        <div>
                          <div className="text-sm font-medium text-gray-900">{church.name}</div>
                          <div className="text-sm text-gray-500">{church.email}</div>
                        </div>
                      ),
                    },
                    {
                      key: 'subscription_plan',
                      label: 'Plan',
                      render: (value) => (
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            value === 'premium'
                              ? 'bg-purple-100 text-purple-800'
                              : value === 'standard'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {value.toUpperCase()}
                        </span>
                      ),
                    },
                    {
                      key: 'subscription_status',
                      label: 'Status',
                      render: (value) => (
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            value === 'active'
                              ? 'bg-green-100 text-green-800'
                              : value === 'trialing'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {value}
                        </span>
                      ),
                    },
                    {
                      key: 'members_count',
                      label: 'Members',
                    },
                    {
                      key: 'created_at',
                      label: 'Created',
                      render: (value) => formatDate(value),
                    },
                    {
                      key: 'organization_id',
                      label: 'Actions',
                      render: (value, church) => (
                        <button
                          onClick={() =>
                            (window.location.href = `/admin/platform/churches/${church.organization_id}`)
                          }
                          className="text-blue-600 hover:text-blue-900 flex items-center"
                        >
                          View Details
                          <ExternalLink className="w-4 h-4 ml-1" />
                        </button>
                      ),
                    },
                  ]}
                  data={filteredChurches}
                  keyField="organization_id"
                  emptyMessage="No churches found"
                />
              </div>
            )}

            {/* Revenue Tab */}
            {activeTab === 'revenue' && revenueMetrics && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="text-sm font-medium text-gray-600 mb-2">Monthly Recurring Revenue</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {formatCurrency(revenueMetrics.mrr)}
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="text-sm font-medium text-gray-600 mb-2">Annual Recurring Revenue</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {formatCurrency(revenueMetrics.arr)}
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="text-sm font-medium text-gray-600 mb-2">Active Subscriptions</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {revenueMetrics.active_subscriptions}
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="text-sm font-medium text-gray-600 mb-2">New This Month</div>
                    <div className="text-3xl font-bold text-green-600">
                      +{revenueMetrics.new_this_month}
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="text-sm font-medium text-gray-600 mb-2">Churned This Month</div>
                    <div className="text-3xl font-bold text-red-600">
                      -{revenueMetrics.churned_this_month}
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold mb-4">Revenue by Plan</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {formatCurrency(revenueMetrics.revenue_by_plan.standard)}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Standard</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {formatCurrency(revenueMetrics.revenue_by_plan.premium)}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Premium</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {formatCurrency(revenueMetrics.mrr)}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Total MRR</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Usage Tab */}
            {activeTab === 'usage' && usageMetrics && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="text-sm font-medium text-gray-600 mb-2">Total Churches</div>
                    <div className="text-3xl font-bold text-gray-900">{usageMetrics.total_churches}</div>
                  </div>
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="text-sm font-medium text-gray-600 mb-2">Total Members</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {usageMetrics.total_members.toLocaleString()}
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="text-sm font-medium text-gray-600 mb-2">SMS Sent</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {usageMetrics.total_sms_sent.toLocaleString()}
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="text-sm font-medium text-gray-600 mb-2">Total Storage</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {usageMetrics.total_storage_gb.toFixed(2)} GB
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="text-sm font-medium text-gray-600 mb-2">Active Last 30 Days</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {usageMetrics.active_churches_30d}
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold mb-4">Churches by Plan</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-gray-900">
                        {usageMetrics.churches_by_plan.free}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Free</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-600">
                        {usageMetrics.churches_by_plan.standard}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Standard</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-purple-600">
                        {usageMetrics.churches_by_plan.premium}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Premium</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
