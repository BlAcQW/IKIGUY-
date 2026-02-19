import React from 'react';
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  TooltipProps,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface MarginTrendData {
  date: string;
  overall_margin?: number;
  [key: string]: any; // For dynamic provider margins (vapi_margin, twilio_margin, etc.)
}

interface LineChartProps {
  data: MarginTrendData[];
  providers: string[];
  title?: string;
  showThresholds?: boolean;
  height?: number;
}

// Color palette for providers
const PROVIDER_COLORS: Record<string, string> = {
  vapi: '#8b5cf6', // Purple
  twilio: '#3b82f6', // Blue
  n8n: '#10b981', // Green
  openai: '#f59e0b', // Amber
  overall: '#6b7280', // Gray
};

// Threshold lines configuration
const THRESHOLDS = [
  { value: 0, label: '0% (Break-even)', color: '#ef4444', strokeDasharray: '5 5' },
  { value: 10, label: '10% (Target)', color: '#f59e0b', strokeDasharray: '3 3' },
  { value: 25, label: '25% (Excellent)', color: '#10b981', strokeDasharray: '3 3' },
];

/**
 * Custom tooltip component for the line chart
 */
const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload, label }) => {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
      <p className="font-semibold text-sm mb-2">{label}</p>
      {payload.map((entry, index) => {
        const value = entry.value as number;
        const isNegative = value < 0;
        const isLow = value < 10 && value >= 0;

        return (
          <div key={`item-${index}`} className="flex items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-gray-600 dark:text-gray-300">{entry.name}:</span>
            </div>
            <span
              className={`font-semibold ${
                isNegative
                  ? 'text-red-600 dark:text-red-400'
                  : isLow
                  ? 'text-yellow-600 dark:text-yellow-400'
                  : 'text-green-600 dark:text-green-400'
              }`}
            >
              {value.toFixed(2)}%
            </span>
          </div>
        );
      })}
    </div>
  );
};

/**
 * LineChart component for displaying profit margin trends over time
 *
 * Features:
 * - Multiple provider lines with color coding
 * - Threshold reference lines (0%, 10%, 25%)
 * - Interactive tooltips with exact values
 * - Responsive sizing
 * - Legend for easy identification
 */
export default function LineChart({
  data,
  providers,
  title = 'Profit Margin Trends',
  showThresholds = true,
  height = 400,
}: LineChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-gray-500">
            No trend data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Format provider names for display
  const formatProviderName = (provider: string): string => {
    if (provider === 'overall') return 'Overall Margin';
    return `${provider.charAt(0).toUpperCase() + provider.slice(1)} Margin`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <RechartsLineChart
            data={data}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />

            <XAxis
              dataKey="date"
              tick={{ fill: 'currentColor', fontSize: 12 }}
              tickLine={{ stroke: 'currentColor' }}
            />

            <YAxis
              label={{ value: 'Margin (%)', angle: -90, position: 'insideLeft' }}
              tick={{ fill: 'currentColor', fontSize: 12 }}
              tickLine={{ stroke: 'currentColor' }}
              domain={['auto', 'auto']}
            />

            <Tooltip content={<CustomTooltip />} />

            <Legend
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="line"
            />

            {/* Threshold reference lines */}
            {showThresholds && THRESHOLDS.map((threshold) => (
              <ReferenceLine
                key={threshold.value}
                y={threshold.value}
                stroke={threshold.color}
                strokeDasharray={threshold.strokeDasharray}
                label={{
                  value: threshold.label,
                  position: 'right',
                  fill: threshold.color,
                  fontSize: 11,
                }}
              />
            ))}

            {/* Overall margin line (if present) */}
            {data.some((d) => d.overall_margin !== undefined) && (
              <Line
                type="monotone"
                dataKey="overall_margin"
                name="Overall Margin"
                stroke={PROVIDER_COLORS.overall}
                strokeWidth={3}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            )}

            {/* Individual provider lines */}
            {providers.map((provider) => {
              const dataKey = `${provider}_margin`;
              const hasData = data.some((d) => d[dataKey] !== undefined);

              if (!hasData) return null;

              return (
                <Line
                  key={provider}
                  type="monotone"
                  dataKey={dataKey}
                  name={formatProviderName(provider)}
                  stroke={PROVIDER_COLORS[provider] || '#94a3b8'}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              );
            })}
          </RechartsLineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
