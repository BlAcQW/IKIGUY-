import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  AlertTriangle,
  RefreshCw,
  Calendar,
  TrendingUpIcon,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { API_BASE_URL } from '@/config/api-config';
import { getAuthHeaders } from '@/lib/auth-utils';
import LineChart from '@/components/charts/LineChart';
import BarChart from '@/components/charts/BarChart';
import DonutChart from '@/components/charts/DonutChart';
import ExportDialog from '@/components/analytics/ExportDialog';

interface ProfitSummary {
  total_revenue: number;
  total_costs: number;
  total_profit: number;
  profit_margin_percentage: number;
  transaction_count: number;
  providers: string[];
  tenant_count: number;
}

interface ProviderBreakdown {
  provider: string;
  total_revenue: number;
  total_costs: number;
  total_profit: number;
  profit_margin_percentage: number;
  transaction_count: number;
}

interface ProfitAnalytics {
  profit_analytics: {
    period: {
      start_date: string;
      end_date: string;
      days: number;
    };
    summary: ProfitSummary;
    breakdown_by_provider: ProviderBreakdown[];
    generated_at: string;
  };
}

interface TrendDataPoint {
  date: string;
  overall_margin?: number;
  [key: string]: any; // For dynamic provider margins
}

interface TrendData {
  trends: TrendDataPoint[];
  providers: string[];
  period: {
    interval: string;
    data_points: number;
  };
}

export default function CostAnalytics() {
  const [analytics, setAnalytics] = useState<ProfitAnalytics | null>(null);
  const [trendData, setTrendData] = useState<TrendData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');
  const [chartInterval, setChartInterval] = useState<'daily' | 'weekly' | 'monthly'>('daily');

  const fetchAnalytics = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Calculate date range
      const endDate = new Date();
      let startDate: Date | null = null;

      if (dateRange !== 'all') {
        const days = dateRange === '7d' ? 7 : dateRange === '30d' ? 30 : 90;
        startDate = new Date();
        startDate.setDate(startDate.getDate() - days);
      }

      const params = new URLSearchParams();
      if (startDate) {
        params.append('start_date', startDate.toISOString());
      }
      params.append('end_date', endDate.toISOString());

      // Get proper auth headers
      const authHeaders = await getAuthHeaders();

      const response = await fetch(
        `${API_BASE_URL}/api/analytics/profit-margins?${params.toString()}`,
        {
          headers: {
            ...authHeaders,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication failed. Please log in again.');
        }
        if (response.status === 403) {
          throw new Error('Access denied. Admin privileges required.');
        }
        throw new Error('Failed to fetch analytics data');
      }

      const data: ProfitAnalytics = await response.json();
      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTrendData = async () => {
    try {
      // Calculate date range
      const endDate = new Date();
      let startDate: Date | null = null;

      if (dateRange !== 'all') {
        const days = dateRange === '7d' ? 7 : dateRange === '30d' ? 30 : 90;
        startDate = new Date();
        startDate.setDate(startDate.getDate() - days);
      }

      const params = new URLSearchParams();
      if (startDate) {
        params.append('start_date', startDate.toISOString());
      }
      params.append('end_date', endDate.toISOString());
      params.append('interval', chartInterval);

      // Get proper auth headers
      const authHeaders = await getAuthHeaders();

      const response = await fetch(
        `${API_BASE_URL}/api/analytics/profit-margins/trends?${params.toString()}`,
        {
          headers: {
            ...authHeaders,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          console.error('Authentication failed for trend data');
          return; // Silently fail - main analytics will show auth error
        }
        if (response.status === 403) {
          console.error('Access denied for trend data');
          return;
        }
        throw new Error('Failed to fetch trend data');
      }

      const data = await response.json();
      setTrendData(data);
    } catch (err) {
      console.error('Error fetching trend data:', err);
      // Don't set error state, just log it - charts will show empty state
    }
  };

  useEffect(() => {
    fetchAnalytics();
    fetchTrendData();
  }, [dateRange, chartInterval]);

  const formatCurrency = (amount: number) => {
    return `₵${amount.toFixed(2)}`;
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getMarginColor = (margin: number) => {
    if (margin < 0) return 'text-red-600';
    if (margin < 10) return 'text-orange-600';
    if (margin < 25) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getMarginBgColor = (margin: number) => {
    if (margin < 0) return 'bg-red-50 border-red-200';
    if (margin < 10) return 'bg-orange-50 border-orange-200';
    if (margin < 25) return 'bg-yellow-50 border-yellow-200';
    return 'bg-green-50 border-green-200';
  };

  if (error) {
    return (
      <div className="p-8">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="flex items-center justify-center p-12">
            <div className="text-center space-y-4">
              <AlertTriangle className="h-12 w-12 text-red-600 mx-auto" />
              <div>
                <h3 className="text-lg font-semibold text-red-900">Error Loading Analytics</h3>
                <p className="text-red-700 mt-2">{error}</p>
              </div>
              <Button onClick={fetchAnalytics} variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-heading">Cost & Profit Analytics</h1>
          <p className="text-gray-600 mt-1">
            Monitor revenue, costs, and profit margins across all providers
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Date Range Selector */}
          <div className="flex border rounded-lg overflow-hidden">
            {['7d', '30d', '90d', 'all'].map((range) => (
              <Button
                key={range}
                variant={dateRange === range ? 'default' : 'ghost'}
                size="sm"
                className={cn(
                  "rounded-none",
                  dateRange === range && "bg-indigo-600 text-white"
                )}
                onClick={() => setDateRange(range as typeof dateRange)}
              >
                {range === 'all' ? 'All Time' : range.toUpperCase()}
              </Button>
            ))}
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={fetchAnalytics}
            disabled={isLoading}
          >
            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
          </Button>
          {/* Export Button */}
          {analytics && (
            <ExportDialog
              startDate={(() => {
                if (dateRange === 'all') return null;
                const days = dateRange === '7d' ? 7 : dateRange === '30d' ? 30 : 90;
                const start = new Date();
                start.setDate(start.getDate() - days);
                return start;
              })()}
              endDate={new Date()}
              providers={analytics.profit_analytics.summary.providers}
            />
          )}
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-indigo-600" />
            <p className="text-gray-600">Loading profit analytics...</p>
          </div>
        </div>
      ) : analytics ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Total Revenue */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Total Revenue
                </CardTitle>
                <DollarSign className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-heading">
                  {formatCurrency(analytics.profit_analytics.summary.total_revenue)}
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  {analytics.profit_analytics.summary.transaction_count} transactions
                </p>
              </CardContent>
            </Card>

            {/* Total Costs */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Total Costs
                </CardTitle>
                <TrendingDown className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-heading">
                  {formatCurrency(analytics.profit_analytics.summary.total_costs)}
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  Paid to providers
                </p>
              </CardContent>
            </Card>

            {/* Total Profit */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Total Profit
                </CardTitle>
                {analytics.profit_analytics.summary.total_profit >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                )}
              </CardHeader>
              <CardContent>
                <div className={cn(
                  "text-2xl font-bold",
                  analytics.profit_analytics.summary.total_profit >= 0
                    ? "text-green-600"
                    : "text-red-600"
                )}>
                  {formatCurrency(analytics.profit_analytics.summary.total_profit)}
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  Revenue - Costs
                </p>
              </CardContent>
            </Card>

            {/* Profit Margin */}
            <Card className={getMarginBgColor(analytics.profit_analytics.summary.profit_margin_percentage)}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Profit Margin
                </CardTitle>
                <TrendingUpIcon className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <div className={cn(
                  "text-2xl font-bold",
                  getMarginColor(analytics.profit_analytics.summary.profit_margin_percentage)
                )}>
                  {formatPercentage(analytics.profit_analytics.summary.profit_margin_percentage)}
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  {analytics.profit_analytics.summary.profit_margin_percentage < 0
                    ? 'LOSING MONEY!'
                    : analytics.profit_analytics.summary.profit_margin_percentage < 10
                    ? 'Very low margin'
                    : analytics.profit_analytics.summary.profit_margin_percentage < 25
                    ? 'Moderate margin'
                    : 'Healthy margin'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Critical Alerts */}
          {analytics.profit_analytics.breakdown_by_provider.some(p => p.profit_margin_percentage < 0) && (
            <Card className="border-red-300 bg-red-50">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  <CardTitle className="text-red-900">Critical Alert: Money-Losing Services</CardTitle>
                </div>
                <CardDescription className="text-red-700">
                  The following providers are losing money and require immediate attention:
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analytics.profit_analytics.breakdown_by_provider
                    .filter(p => p.profit_margin_percentage < 0)
                    .map((provider) => (
                      <div key={provider.provider} className="bg-white border border-red-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-semibold text-red-900 uppercase">{provider.provider}</h4>
                            <p className="text-sm text-red-700 mt-1">
                              Losing {formatCurrency(Math.abs(provider.total_profit))} on {provider.transaction_count} transactions
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-red-600">
                              {formatPercentage(provider.profit_margin_percentage)}
                            </div>
                            <div className="text-sm text-red-700">margin</div>
                          </div>
                        </div>
                        <div className="mt-3 pt-3 border-t border-red-200 grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <div className="text-gray-600">Revenue</div>
                            <div className="font-semibold">{formatCurrency(provider.total_revenue)}</div>
                          </div>
                          <div>
                            <div className="text-gray-600">Costs</div>
                            <div className="font-semibold">{formatCurrency(provider.total_costs)}</div>
                          </div>
                          <div>
                            <div className="text-gray-600">Loss</div>
                            <div className="font-semibold text-red-600">
                              {formatCurrency(Math.abs(provider.total_profit))}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-900 font-medium">
                    💡 Recommendation: Consider switching to alternative providers or increasing pricing for these services.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Visualizations Section */}
          <div className="space-y-6">
            {/* Chart Interval Selector */}
            <div className="flex justify-end">
              <div className="flex border rounded-lg overflow-hidden">
                {['daily', 'weekly', 'monthly'].map((interval) => (
                  <Button
                    key={interval}
                    variant={chartInterval === interval ? 'default' : 'ghost'}
                    size="sm"
                    className={cn(
                      "rounded-none capitalize",
                      chartInterval === interval && "bg-indigo-600 text-white"
                    )}
                    onClick={() => setChartInterval(interval as typeof chartInterval)}
                  >
                    {interval}
                  </Button>
                ))}
              </div>
            </div>

            {/* Margin Trends Line Chart */}
            {trendData && trendData.trends.length > 0 && (
              <LineChart
                data={trendData.trends}
                providers={trendData.providers}
                title="Profit Margin Trends Over Time"
                showThresholds={true}
                height={400}
              />
            )}

            {/* Revenue Distribution & Provider Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Revenue Distribution Donut Chart */}
              <DonutChart
                data={analytics.profit_analytics.breakdown_by_provider}
                title="Revenue Distribution by Provider"
                metric="revenue"
                height={400}
              />

              {/* Profit Distribution Donut Chart */}
              <DonutChart
                data={analytics.profit_analytics.breakdown_by_provider}
                title="Profit Distribution by Provider"
                metric="profit"
                height={400}
              />
            </div>

            {/* Provider Comparison Bar Chart */}
            <BarChart
              data={analytics.profit_analytics.breakdown_by_provider}
              title="Provider Performance Comparison"
              height={450}
            />
          </div>

          {/* Provider Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Provider Breakdown</CardTitle>
              <CardDescription>
                Profit margin analysis by provider
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.profit_analytics.breakdown_by_provider
                  .sort((a, b) => b.profit_margin_percentage - a.profit_margin_percentage)
                  .map((provider) => (
                    <div
                      key={provider.provider}
                      className={cn(
                        "border rounded-lg p-4",
                        getMarginBgColor(provider.profit_margin_percentage)
                      )}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-heading uppercase text-lg">
                            {provider.provider}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">
                            {provider.transaction_count} transactions
                          </p>
                        </div>
                        <div className="text-right">
                          <div className={cn(
                            "text-3xl font-bold",
                            getMarginColor(provider.profit_margin_percentage)
                          )}>
                            {formatPercentage(provider.profit_margin_percentage)}
                          </div>
                          <div className="text-sm text-gray-600">profit margin</div>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden mb-3">
                        <div
                          className={cn(
                            "h-full",
                            provider.profit_margin_percentage >= 0
                              ? "bg-green-500"
                              : "bg-red-500"
                          )}
                          style={{
                            width: `${Math.min(Math.abs(provider.profit_margin_percentage), 100)}%`
                          }}
                        />
                      </div>

                      {/* Metrics */}
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="text-gray-600">Revenue</div>
                          <div className="font-semibold text-heading mt-1">
                            {formatCurrency(provider.total_revenue)}
                          </div>
                        </div>
                        <div>
                          <div className="text-gray-600">Costs</div>
                          <div className="font-semibold text-heading mt-1">
                            {formatCurrency(provider.total_costs)}
                          </div>
                        </div>
                        <div>
                          <div className="text-gray-600">
                            {provider.total_profit >= 0 ? 'Profit' : 'Loss'}
                          </div>
                          <div className={cn(
                            "font-semibold mt-1",
                            provider.total_profit >= 0 ? 'text-green-600' : 'text-red-600'
                          )}>
                            {formatCurrency(Math.abs(provider.total_profit))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          {/* Period Info */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>
                    Period: {new Date(analytics.profit_analytics.period.start_date).toLocaleDateString()} -
                    {' '}{new Date(analytics.profit_analytics.period.end_date).toLocaleDateString()}
                    ({analytics.profit_analytics.period.days} days)
                  </span>
                </div>
                <div className="border-l pl-4">
                  Active Providers: {analytics.profit_analytics.summary.providers.length}
                </div>
                <div className="border-l pl-4">
                  Organizations: {analytics.profit_analytics.summary.tenant_count}
                </div>
                <div className="border-l pl-4">
                  Last Updated: {new Date(analytics.profit_analytics.generated_at).toLocaleString()}
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="flex items-center justify-center h-96">
            <p className="text-gray-600">No analytics data available</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
