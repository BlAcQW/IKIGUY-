import React, { useState } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
  TooltipProps,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface ProviderData {
  provider: string;
  total_revenue: number;
  total_costs: number;
  profit: number;
  margin_percentage: number;
  transaction_count: number;
}

interface DonutChartProps {
  data: ProviderData[];
  title?: string;
  height?: number;
  metric?: 'revenue' | 'costs' | 'profit';
  onProviderClick?: (provider: string) => void;
}

// Color palette for providers
const PROVIDER_COLORS: Record<string, string> = {
  vapi: '#8b5cf6', // Purple
  twilio: '#3b82f6', // Blue
  n8n: '#10b981', // Green
  openai: '#f59e0b', // Amber
  anthropic: '#ec4899', // Pink
  elevenlabs: '#06b6d4', // Cyan
  default: '#94a3b8', // Slate
};

/**
 * Format currency values
 */
const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-GH', {
    style: 'currency',
    currency: 'GHS',
    minimumFractionDigits: 2,
  }).format(value);
};

/**
 * Custom tooltip for donut chart
 */
const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload }) => {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const data = payload[0];
  const name = data.name as string;
  const value = data.value as number;
  const percentage = data.payload.percentage as number;

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
      <p className="font-semibold text-sm mb-2 capitalize">{name}</p>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between gap-4">
          <span className="text-gray-600 dark:text-gray-300">Amount:</span>
          <span className="font-semibold text-gray-800 dark:text-gray-200">
            {formatCurrency(value)}
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-600 dark:text-gray-300">Share:</span>
          <span className="font-semibold text-gray-800 dark:text-gray-200">
            {percentage.toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
};

/**
 * Custom label for pie chart showing percentage
 */
const renderCustomLabel = ({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
}: any) => {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * (Math.PI / 180));
  const y = cy + radius * Math.sin(-midAngle * (Math.PI / 180));

  // Only show label if percentage is > 5%
  if (percent < 0.05) return null;

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      className="text-xs font-semibold"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

/**
 * Custom legend component with better formatting
 */
const CustomLegend = ({ payload }: any) => {
  return (
    <div className="flex flex-wrap gap-3 justify-center mt-4">
      {payload.map((entry: any, index: number) => (
        <div key={`legend-${index}`} className="flex items-center gap-2 text-xs">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="capitalize text-gray-700 dark:text-gray-300">
            {entry.value}
          </span>
          <span className="text-gray-500 dark:text-gray-400">
            ({entry.payload.percentage.toFixed(1)}%)
          </span>
        </div>
      ))}
    </div>
  );
};

/**
 * DonutChart component for revenue/cost/profit distribution visualization
 *
 * Features:
 * - Interactive donut chart with provider breakdown
 * - Click to highlight specific providers
 * - Center label showing total value
 * - Legend with percentages
 * - Supports revenue, costs, or profit metrics
 */
export default function DonutChart({
  data,
  title = 'Revenue Distribution',
  height = 400,
  metric = 'revenue',
  onProviderClick,
}: DonutChartProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-gray-500">
            No distribution data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare chart data based on selected metric
  const getMetricValue = (item: ProviderData): number => {
    switch (metric) {
      case 'costs':
        return item.total_costs;
      case 'profit':
        return item.profit;
      case 'revenue':
      default:
        return item.total_revenue;
    }
  };

  // Calculate total
  const total = data.reduce((sum, item) => sum + getMetricValue(item), 0);

  // Prepare data for chart
  const chartData = data
    .map((item) => ({
      name: item.provider,
      value: getMetricValue(item),
      percentage: total > 0 ? (getMetricValue(item) / total) * 100 : 0,
    }))
    .filter((item) => item.value > 0) // Only show providers with positive values
    .sort((a, b) => b.value - a.value); // Sort by value descending

  const handlePieClick = (_: any, index: number) => {
    setActiveIndex(activeIndex === index ? null : index);
    if (onProviderClick && chartData[index]) {
      onProviderClick(chartData[index].name);
    }
  };

  const getMetricLabel = (): string => {
    switch (metric) {
      case 'costs':
        return 'Total Costs';
      case 'profit':
        return 'Total Profit';
      case 'revenue':
      default:
        return 'Total Revenue';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderCustomLabel}
                outerRadius={120}
                innerRadius={70}
                fill="#8884d8"
                dataKey="value"
                onClick={handlePieClick}
                cursor={onProviderClick ? 'pointer' : 'default'}
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={PROVIDER_COLORS[entry.name] || PROVIDER_COLORS.default}
                    opacity={activeIndex === null || activeIndex === index ? 1 : 0.4}
                    strokeWidth={activeIndex === index ? 3 : 1}
                    stroke={activeIndex === index ? '#fff' : '#fff'}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend content={<CustomLegend />} />
            </PieChart>
          </ResponsiveContainer>

          {/* Center label showing total */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
              {getMetricLabel()}
            </div>
            <div className="text-2xl font-bold text-gray-800 dark:text-gray-200">
              {formatCurrency(total)}
            </div>
            {chartData.length > 0 && (
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {chartData.length} provider{chartData.length !== 1 ? 's' : ''}
              </div>
            )}
          </div>
        </div>

        {/* Active provider info */}
        {activeIndex !== null && chartData[activeIndex] && (
          <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="text-sm">
              <span className="font-semibold capitalize">{chartData[activeIndex].name}:</span>
              <span className="ml-2">{formatCurrency(chartData[activeIndex].value)}</span>
              <span className="ml-2 text-gray-500">
                ({chartData[activeIndex].percentage.toFixed(1)}% of total)
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
