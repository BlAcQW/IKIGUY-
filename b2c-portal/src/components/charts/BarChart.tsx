import React, { useState, useMemo } from 'react';
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  TooltipProps,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowUpDown } from 'lucide-react';

interface ProviderData {
  provider: string;
  total_revenue: number;
  total_costs: number;
  profit: number;
  margin_percentage: number;
  transaction_count: number;
}

interface BarChartProps {
  data: ProviderData[];
  title?: string;
  height?: number;
  onProviderClick?: (provider: string) => void;
}

type SortField = 'provider' | 'total_revenue' | 'profit' | 'margin_percentage';
type SortDirection = 'asc' | 'desc';

/**
 * Get bar color based on margin percentage
 */
const getMarginColor = (margin: number): string => {
  if (margin < 0) return '#ef4444'; // Red - losing money
  if (margin < 5) return '#f97316'; // Orange - very low margin
  if (margin < 10) return '#f59e0b'; // Amber - low margin
  if (margin < 20) return '#10b981'; // Green - good margin
  return '#059669'; // Dark green - excellent margin
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
 * Custom tooltip for bar chart
 */
const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload }) => {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const data = payload[0].payload as ProviderData;

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4">
      <p className="font-semibold text-sm mb-3 capitalize">{data.provider}</p>

      <div className="space-y-2 text-xs">
        <div className="flex justify-between gap-6">
          <span className="text-gray-600 dark:text-gray-300">Revenue:</span>
          <span className="font-semibold text-green-600 dark:text-green-400">
            {formatCurrency(data.total_revenue)}
          </span>
        </div>

        <div className="flex justify-between gap-6">
          <span className="text-gray-600 dark:text-gray-300">Costs:</span>
          <span className="font-semibold text-red-600 dark:text-red-400">
            {formatCurrency(data.total_costs)}
          </span>
        </div>

        <div className="flex justify-between gap-6">
          <span className="text-gray-600 dark:text-gray-300">Profit:</span>
          <span
            className={`font-semibold ${
              data.profit >= 0
                ? 'text-green-600 dark:text-green-400'
                : 'text-red-600 dark:text-red-400'
            }`}
          >
            {formatCurrency(data.profit)}
          </span>
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700 my-2" />

        <div className="flex justify-between gap-6">
          <span className="text-gray-600 dark:text-gray-300">Margin:</span>
          <span
            className={`font-semibold ${
              data.margin_percentage >= 10
                ? 'text-green-600 dark:text-green-400'
                : data.margin_percentage >= 0
                ? 'text-yellow-600 dark:text-yellow-400'
                : 'text-red-600 dark:text-red-400'
            }`}
          >
            {data.margin_percentage.toFixed(2)}%
          </span>
        </div>

        <div className="flex justify-between gap-6">
          <span className="text-gray-600 dark:text-gray-300">Transactions:</span>
          <span className="font-semibold text-gray-800 dark:text-gray-200">
            {data.transaction_count.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
};

/**
 * BarChart component for provider comparison
 *
 * Features:
 * - Side-by-side comparison of revenue, costs, and profit
 * - Color-coded bars based on margin percentage
 * - Sortable by different metrics
 * - Interactive tooltips with detailed breakdown
 * - Click handlers for drill-down capability
 */
export default function BarChart({
  data,
  title = 'Provider Comparison',
  height = 400,
  onProviderClick,
}: BarChartProps) {
  const [sortField, setSortField] = useState<SortField>('total_revenue');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Sort data based on current sort field and direction
  const sortedData = useMemo(() => {
    const sorted = [...data].sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];

      // For string comparison (provider name)
      if (typeof aValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue as string)
          : (bValue as string).localeCompare(aValue);
      }

      // For numeric comparison
      return sortDirection === 'asc'
        ? (aValue as number) - (bValue as number)
        : (bValue as number) - (aValue as number);
    });

    return sorted;
  }, [data, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Toggle direction if same field
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new field with default descending
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const handleBarClick = (data: any) => {
    if (onProviderClick && data.provider) {
      onProviderClick(data.provider);
    }
  };

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-gray-500">
            No provider data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{title}</CardTitle>
          <div className="flex gap-2">
            <Button
              variant={sortField === 'total_revenue' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleSort('total_revenue')}
            >
              Revenue <ArrowUpDown className="ml-1 h-3 w-3" />
            </Button>
            <Button
              variant={sortField === 'profit' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleSort('profit')}
            >
              Profit <ArrowUpDown className="ml-1 h-3 w-3" />
            </Button>
            <Button
              variant={sortField === 'margin_percentage' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleSort('margin_percentage')}
            >
              Margin <ArrowUpDown className="ml-1 h-3 w-3" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <RechartsBarChart
            data={sortedData}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />

            <XAxis
              dataKey="provider"
              tick={{ fill: 'currentColor', fontSize: 12 }}
              tickLine={{ stroke: 'currentColor' }}
              tickFormatter={(value) => value.charAt(0).toUpperCase() + value.slice(1)}
            />

            <YAxis
              label={{ value: 'Amount (GHS)', angle: -90, position: 'insideLeft' }}
              tick={{ fill: 'currentColor', fontSize: 12 }}
              tickLine={{ stroke: 'currentColor' }}
              tickFormatter={(value) => `₵${(value / 1000).toFixed(0)}k`}
            />

            <Tooltip content={<CustomTooltip />} />

            <Legend
              wrapperStyle={{ paddingTop: '20px' }}
            />

            <Bar
              dataKey="total_revenue"
              name="Revenue"
              fill="#10b981"
              onClick={handleBarClick}
              cursor={onProviderClick ? 'pointer' : 'default'}
            />

            <Bar
              dataKey="total_costs"
              name="Costs"
              fill="#ef4444"
              onClick={handleBarClick}
              cursor={onProviderClick ? 'pointer' : 'default'}
            />

            <Bar
              dataKey="profit"
              name="Profit"
              onClick={handleBarClick}
              cursor={onProviderClick ? 'pointer' : 'default'}
            >
              {sortedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getMarginColor(entry.margin_percentage)} />
              ))}
            </Bar>
          </RechartsBarChart>
        </ResponsiveContainer>

        {/* Legend for margin colors */}
        <div className="flex items-center justify-center gap-4 mt-4 text-xs text-gray-600 dark:text-gray-400">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span>&lt; 0%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-orange-500" />
            <span>0-5%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <span>5-10%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span>10-20%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-green-600" />
            <span>&gt; 20%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
