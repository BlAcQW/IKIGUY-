/**
 * Members Dashboard Page - Admin Only
 *
 * Comprehensive member statistics dashboard showing demographics,
 * activity, financial metrics, and growth trends.
 */

import React, { useState } from 'react';
import { Users, TrendingUp, DollarSign, Activity, UserPlus } from 'lucide-react';
import { BarChart, Bar, PieChart, Pie, LineChart, Line, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import MetricCard from '../../components/admin/MetricCard';
import { useMemberDashboardMetrics, formatCurrency, formatNumber, formatPercentage } from '../../hooks/useMemberAnalytics';
import { useOrganization } from '../../contexts/OrganizationContext';
import RegisterExistingMemberModal from '../../components/members/RegisterExistingMemberModal';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function MembersDashboardPage() {
  const [period, setPeriod] = useState('30d');
  const [branchFilter, setBranchFilter] = useState<string | null>(null);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const { currentOrganization, currentRole, isUniversalAdmin } = useOrganization();

  const token = localStorage.getItem('access_token');
  // Use localStorage directly as fallback if OrganizationContext is not loaded
  const organizationId = currentOrganization?.id || localStorage.getItem('current_organization_id');

  const { data: metrics, isLoading, error } = useMemberDashboardMetrics(
    token,
    organizationId,
    period,
    branchFilter
  );

  // Check admin access
  const isAdmin = currentRole === 'admin' || currentRole === 'owner' || isUniversalAdmin;

  if (!isAdmin) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Access Denied: Admin access required</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-2">Error loading member statistics</p>
        <p className="text-gray-500 text-sm">{error.message}</p>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  // Prepare age distribution data for chart
  const ageData = [
    { name: '0-18', value: metrics.age_distribution.age_0_18 },
    { name: '19-25', value: metrics.age_distribution.age_19_25 },
    { name: '26-35', value: metrics.age_distribution.age_26_35 },
    { name: '36-50', value: metrics.age_distribution.age_36_50 },
    { name: '51-65', value: metrics.age_distribution.age_51_65 },
    { name: '65+', value: metrics.age_distribution.age_65_plus },
  ].filter(item => item.value > 0);

  // Prepare gender distribution data for chart
  const genderData = [
    { name: 'Male', value: metrics.gender_distribution.male },
    { name: 'Female', value: metrics.gender_distribution.female },
    { name: 'Other', value: metrics.gender_distribution.other },
  ].filter(item => item.value > 0);

  // Prepare visit frequency data
  const visitFreqData = Object.entries(metrics.visit_frequency).map(([key, value]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    value: value as number
  }));

  // Prepare spiritual stages data
  const spiritualStagesData = Object.entries(metrics.spiritual_stages).map(([key, value]) => ({
    name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value: value as number
  }));

  return (
    <div className="space-y-6">
        {/* Header with filters */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-2xl font-bold text-gray-900">Member Analytics</h1>

          <div className="flex flex-wrap gap-4">
            {/* Register Existing Member Button */}
            <button
              onClick={() => setShowRegisterModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-lg font-medium transition-all shadow-sm"
            >
              <UserPlus className="w-4 h-4" />
              <span className="hidden sm:inline">Register Member</span>
              <span className="sm:hidden">Add</span>
            </button>
            {/* Period selector */}
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="bg-white text-gray-900 px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-purple-500"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="1y">Last Year</option>
            </select>

            {/* Branch filter */}
            {metrics.branch_distribution.length > 1 && (
              <select
                value={branchFilter || ''}
                onChange={(e) => setBranchFilter(e.target.value || null)}
                className="bg-white text-gray-900 px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-purple-500"
              >
                <option value="">All Branches</option>
                {metrics.branch_distribution.map(branch => (
                  <option key={branch.branch_id} value={branch.branch_id}>
                    {branch.branch_name}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Overview Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard
            title="Total Members"
            value={metrics.total_members}
            subtitle={`${metrics.active_members} active`}
            trend={metrics.growth_rate}
            icon={<Users className="w-6 h-6" />}
            format="number"
          />

          <MetricCard
            title="New Members"
            value={metrics.new_members_count}
            subtitle={`${period.replace('d', ' days').replace('y', ' year')}`}
            trend={metrics.growth_rate}
            icon={<TrendingUp className="w-6 h-6" />}
            format="number"
          />

          <MetricCard
            title="Total Donations"
            value={metrics.total_donations}
            subtitle={`${metrics.total_donors} donors`}
            icon={<DollarSign className="w-6 h-6" />}
            format="currency"
          />

          <MetricCard
            title="Avg Donation"
            value={metrics.average_donation}
            subtitle={`${metrics.donor_percentage.toFixed(1)}% donor rate`}
            icon={<Activity className="w-6 h-6" />}
            format="currency"
          />
        </div>

        {/* Demographics Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Age Distribution */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Age Distribution</h2>
            {ageData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={ageData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="name" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#fff' }}
                  />
                  <Bar dataKey="value" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-center py-12">No age data available</p>
            )}
          </div>

          {/* Gender Distribution */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Gender Distribution</h2>
            {genderData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={genderData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {genderData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#fff' }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-center py-12">No gender data available</p>
            )}
          </div>
        </div>

        {/* Member Trend */}
        {metrics.member_trend.length > 0 && (
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Member Growth Trend</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics.member_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#fff' }}
                />
                <Legend />
                <Line type="monotone" dataKey="count" stroke="#10b981" strokeWidth={2} name="Total Members" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Activity & Engagement */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Visit Frequency */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Visit Frequency</h2>
            <div className="space-y-3">
              {visitFreqData.map((item, index) => (
                <div key={item.name} className="flex items-center justify-between">
                  <span className="text-gray-300">{item.name}</span>
                  <div className="flex items-center gap-3">
                    <div className="w-32 bg-gray-700 rounded-full h-2">
                      <div
                        className="h-2 rounded-full"
                        style={{
                          width: `${(item.value / metrics.total_members) * 100}%`,
                          backgroundColor: COLORS[index % COLORS.length]
                        }}
                      />
                    </div>
                    <span className="text-gray-900 font-medium w-16 text-right">{item.value}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-gray-700">
              <p className="text-sm text-gray-400">
                Average visits: <span className="text-gray-900 font-medium">{metrics.average_visit_count.toFixed(1)}</span>
              </p>
            </div>
          </div>

          {/* Spiritual Stages */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Spiritual Journey Stages</h2>
            <div className="space-y-3">
              {spiritualStagesData.map((item, index) => (
                <div key={item.name} className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm">{item.name}</span>
                  <div className="flex items-center gap-3">
                    <div className="w-32 bg-gray-700 rounded-full h-2">
                      <div
                        className="h-2 rounded-full"
                        style={{
                          width: `${(item.value / metrics.total_members) * 100}%`,
                          backgroundColor: COLORS[index % COLORS.length]
                        }}
                      />
                    </div>
                    <span className="text-gray-900 font-medium w-16 text-right">{item.value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Branch Distribution Table */}
        {metrics.branch_distribution.length > 0 && (
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Branch Distribution</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-700">
                <thead>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Branch
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Members
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Percentage
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {metrics.branch_distribution.map((branch) => (
                    <tr key={branch.branch_id} className="hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {branch.branch_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                        {formatNumber(branch.member_count)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300 text-right">
                        {((branch.member_count / metrics.total_members) * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Additional Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-400 mb-2">First Timers</h3>
            <p className="text-3xl font-bold text-gray-900">{formatNumber(metrics.first_timers)}</p>
            <p className="text-sm text-gray-400 mt-1">New visitors in period</p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Returning Visitors</h3>
            <p className="text-3xl font-bold text-gray-900">{formatNumber(metrics.returning_visitors)}</p>
            <p className="text-sm text-gray-400 mt-1">Visitors who came back</p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Inactive Members</h3>
            <p className="text-3xl font-bold text-gray-900">{formatNumber(metrics.inactive_members)}</p>
            <p className="text-sm text-gray-400 mt-1">
              {((metrics.inactive_members / metrics.total_members) * 100).toFixed(1)}% of total
            </p>
          </div>
        </div>

        {/* Register Existing Member Modal */}
        <RegisterExistingMemberModal
          isOpen={showRegisterModal}
          onClose={() => setShowRegisterModal(false)}
          onSuccess={() => {
            setShowRegisterModal(false);
            // Refresh the metrics after registration
            window.location.reload();
          }}
        />
      </div>
  );
}
