/**
 * Analytics Dashboard Page - Phase 7
 *
 * Main analytics dashboard for church admins.
 * Displays comprehensive metrics, charts, insights, and alerts.
 */

import React, { useState, useEffect } from 'react';
import { useDashboardMetrics, MetricPeriod } from '../../hooks/useAnalytics';
import MetricCard from '../../components/admin/MetricCard';
import EngagementChart from '../../components/admin/EngagementChart';
import AttendanceChart from '../../components/admin/AttendanceChart';
import InsightsPanel from '../../components/admin/InsightsPanel';
import {
  UserGroupIcon,
  CalendarIcon,
  EnvelopeIcon,
  ChatBubbleLeftRightIcon,
  ArrowTrendingUpIcon,
  BanknotesIcon,
} from '@heroicons/react/24/outline';

const PERIOD_OPTIONS: { value: MetricPeriod; label: string }[] = [
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: '90d', label: 'Last 90 Days' },
  { value: '1y', label: 'Last Year' },
];

export const AnalyticsPage: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<MetricPeriod>('30d');
  const [token, setToken] = useState<string | null>(null);
  const [organizationId, setOrganizationId] = useState<string | null>(null);

  useEffect(() => {
    // Get token and organization from localStorage
    const accessToken = localStorage.getItem('access_token');
    const orgId = localStorage.getItem('current_organization_id');
    setToken(accessToken);
    setOrganizationId(orgId);
  }, []);

  // Fetch dashboard metrics
  const {
    data: metrics,
    isLoading,
    error,
    refetch,
  } = useDashboardMetrics(token, organizationId, selectedPeriod);

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-2 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-1/3 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <MetricCard key={i} title="" value="" loading={true} />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-900 mb-2">Error Loading Analytics</h2>
          <p className="text-red-700 mb-4">{error.message}</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // No data state
  if (!metrics) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <p className="text-gray-600">No analytics data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
            <p className="text-gray-600 mt-1">{metrics.organization_name}</p>
          </div>

          {/* Period Selector */}
          <div className="flex items-center gap-2">
            <label htmlFor="period" className="text-sm font-medium text-gray-700">
              Period:
            </label>
            <select
              id="period"
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value as MetricPeriod)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {PERIOD_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Events"
          value={metrics.total_events}
          subtitle={`${metrics.upcoming_events} upcoming`}
          trend={metrics.attendance_trend}
          trendLabel="vs previous period"
          icon={<CalendarIcon className="w-6 h-6" />}
          format="number"
        />

        <MetricCard
          title="Total Attendees"
          value={metrics.total_attendees}
          subtitle={`Avg: ${Math.round(metrics.avg_attendance_per_event)} per event`}
          trend={metrics.attendance_trend}
          trendLabel="vs previous period"
          icon={<UserGroupIcon className="w-6 h-6" />}
          format="number"
        />

        <MetricCard
          title="Engagement Score"
          value={metrics.engagement_score}
          trend={metrics.engagement_trend}
          trendLabel="vs previous period"
          icon={<ArrowTrendingUpIcon className="w-6 h-6" />}
          format="number"
        />

        <MetricCard
          title="Member Retention"
          value={metrics.member_retention_rate * 100}
          subtitle={`${metrics.new_members} new members`}
          icon={<UserGroupIcon className="w-6 h-6" />}
          format="percentage"
        />
      </div>

      {/* Communication Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <MetricCard
          title="SMS Sent"
          value={metrics.sms_sent}
          subtitle={`${(metrics.sms_delivery_rate * 100).toFixed(1)}% delivery rate`}
          trend={metrics.communication_trend}
          trendLabel="vs previous period"
          icon={<ChatBubbleLeftRightIcon className="w-6 h-6" />}
          format="number"
        />

        <MetricCard
          title="Emails Sent"
          value={metrics.email_sent}
          subtitle={`${(metrics.email_open_rate * 100).toFixed(1)}% open rate`}
          trend={metrics.communication_trend}
          trendLabel="vs previous period"
          icon={<EnvelopeIcon className="w-6 h-6" />}
          format="number"
        />
      </div>

      {/* Giving Metrics (if available) */}
      {metrics.total_giving !== undefined && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <MetricCard
            title="Total Giving"
            value={metrics.total_giving}
            trend={metrics.giving_trend}
            trendLabel="vs previous period"
            icon={<BanknotesIcon className="w-6 h-6" />}
            format="currency"
          />

          <MetricCard
            title="Average per Member"
            value={metrics.avg_giving_per_member || 0}
            trend={metrics.giving_trend}
            trendLabel="vs previous period"
            icon={<BanknotesIcon className="w-6 h-6" />}
            format="currency"
          />

          <MetricCard
            title="Giving Growth"
            value={metrics.giving_growth_rate || 0}
            icon={<ArrowTrendingUpIcon className="w-6 h-6" />}
            format="percentage"
          />
        </div>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Engagement Chart */}
        <EngagementChart
          engagementScore={metrics.engagement_score}
          engagementLevel="medium" // TODO: Get from backend
          activeMembers={metrics.total_attendees}
          inactiveMembers={Math.max(0, metrics.total_attendees - metrics.returning_members)}
        />

        {/* Attendance Trends - placeholder for now */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Stats</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
              <div>
                <p className="text-sm text-gray-600">New Members</p>
                <p className="text-2xl font-bold text-blue-600">{metrics.new_members}</p>
              </div>
              <UserGroupIcon className="w-8 h-8 text-blue-400" />
            </div>

            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
              <div>
                <p className="text-sm text-gray-600">Returning Members</p>
                <p className="text-2xl font-bold text-green-600">{metrics.returning_members}</p>
              </div>
              <UserGroupIcon className="w-8 h-8 text-green-400" />
            </div>

            <div className="flex items-center justify-between p-4 bg-amber-50 rounded-lg">
              <div>
                <p className="text-sm text-gray-600">Upcoming Events</p>
                <p className="text-2xl font-bold text-amber-600">{metrics.upcoming_events}</p>
              </div>
              <CalendarIcon className="w-8 h-8 text-amber-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Insights and Alerts */}
      <InsightsPanel insights={metrics.insights} alerts={metrics.alerts} />

      {/* Footer Info */}
      <div className="mt-8 text-center text-sm text-gray-500">
        <p>
          Last updated: {new Date(metrics.calculated_at).toLocaleString()}
        </p>
      </div>
    </div>
  );
};

export default AnalyticsPage;
