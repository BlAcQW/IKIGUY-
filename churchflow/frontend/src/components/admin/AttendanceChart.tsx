/**
 * AttendanceChart Component - Phase 7
 *
 * Displays attendance trends over time with line/area chart.
 */

import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { format, parseISO } from 'date-fns';

export interface AttendanceDataPoint {
  date: string;
  count: number;
}

export interface AttendanceChartProps {
  data: AttendanceDataPoint[];
  title?: string;
  chartType?: 'line' | 'area';
  loading?: boolean;
  height?: number;
}

export const AttendanceChart: React.FC<AttendanceChartProps> = ({
  data,
  title = 'Attendance Trends',
  chartType = 'area',
  loading = false,
  height = 300,
}) => {
  // Format data for recharts
  const chartData = data.map((point) => ({
    ...point,
    formattedDate: format(parseISO(point.date), 'MMM dd'),
  }));

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className={`bg-gray-200 rounded`} style={{ height: `${height}px` }}></div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div
          className="flex items-center justify-center text-gray-500"
          style={{ height: `${height}px` }}
        >
          <p>No attendance data available</p>
        </div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900">{payload[0].payload.formattedDate}</p>
          <p className="text-sm text-gray-600">
            Attendees: <span className="font-semibold text-blue-600">{payload[0].value}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>

      <ResponsiveContainer width="100%" height={height}>
        {chartType === 'area' ? (
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="formattedDate"
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="count"
              stroke="#3b82f6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorCount)"
            />
          </AreaChart>
        ) : (
          <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="formattedDate"
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="count"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: '#3b82f6', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        )}
      </ResponsiveContainer>

      {/* Summary Stats */}
      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <p className="text-lg font-bold text-blue-600">
            {Math.max(...chartData.map((d) => d.count))}
          </p>
          <p className="text-xs text-gray-600">Peak</p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-lg font-bold text-gray-600">
            {Math.round(chartData.reduce((sum, d) => sum + d.count, 0) / chartData.length)}
          </p>
          <p className="text-xs text-gray-600">Average</p>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <p className="text-lg font-bold text-green-600">
            {chartData.reduce((sum, d) => sum + d.count, 0).toLocaleString()}
          </p>
          <p className="text-xs text-gray-600">Total</p>
        </div>
      </div>
    </div>
  );
};

export default AttendanceChart;
