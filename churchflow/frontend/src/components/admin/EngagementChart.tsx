/**
 * EngagementChart Component - Phase 7
 *
 * Displays member engagement score visualization with gauge chart.
 */

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { EngagementLevel } from '../../hooks/useAnalytics';

export interface EngagementChartProps {
  engagementScore: number;
  engagementLevel: EngagementLevel;
  activeMembers: number;
  inactiveMembers: number;
  loading?: boolean;
}

const ENGAGEMENT_COLORS: Record<EngagementLevel, string> = {
  very_high: '#10b981', // green-500
  high: '#3b82f6', // blue-500
  medium: '#f59e0b', // amber-500
  low: '#ef4444', // red-500
  very_low: '#dc2626', // red-600
};

const ENGAGEMENT_LABELS: Record<EngagementLevel, string> = {
  very_high: 'Very High',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  very_low: 'Very Low',
};

export const EngagementChart: React.FC<EngagementChartProps> = ({
  engagementScore,
  engagementLevel,
  activeMembers,
  inactiveMembers,
  loading = false,
}) => {
  const memberData = [
    { name: 'Active Members', value: activeMembers, color: '#10b981' },
    { name: 'Inactive Members', value: inactiveMembers, color: '#ef4444' },
  ];

  const scoreColor = ENGAGEMENT_COLORS[engagementLevel];
  const levelLabel = ENGAGEMENT_LABELS[engagementLevel];

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Member Engagement</h3>

      {/* Engagement Score */}
      <div className="text-center mb-6">
        <div className="inline-flex items-baseline gap-2">
          <span className="text-5xl font-bold" style={{ color: scoreColor }}>
            {engagementScore.toFixed(1)}
          </span>
          <span className="text-2xl text-gray-500">/ 100</span>
        </div>
        <p className="mt-2 text-sm font-medium" style={{ color: scoreColor }}>
          {levelLabel} Engagement
        </p>
      </div>

      {/* Member Distribution Chart */}
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={memberData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {memberData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => value.toLocaleString()}
            contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>

      {/* Member Stats */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <p className="text-2xl font-bold text-green-600">{activeMembers.toLocaleString()}</p>
          <p className="text-sm text-gray-600">Active</p>
        </div>
        <div className="text-center p-3 bg-red-50 rounded-lg">
          <p className="text-2xl font-bold text-red-600">{inactiveMembers.toLocaleString()}</p>
          <p className="text-sm text-gray-600">Inactive</p>
        </div>
      </div>
    </div>
  );
};

export default EngagementChart;
