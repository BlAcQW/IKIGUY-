import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  MessageSquare,
  Target,
  Zap,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  AnalyticsOverview,
  ConfidenceBucket,
  TopQuery,
  EscalationAnalysis,
  SourceUsage,
  PerformanceMetrics,
} from './types';

interface RAGAnalyticsDashboardProps {
  companyName: string;
  apiBaseUrl: string;
  authToken?: string;
  organizationId?: string;
}

const RAGAnalyticsDashboard: React.FC<RAGAnalyticsDashboardProps> = ({
  companyName,
  apiBaseUrl,
  authToken,
  organizationId,
}) => {
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('30');
  const { toast } = useToast();

  // State for analytics data
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [confidenceDistribution, setConfidenceDistribution] = useState<ConfidenceBucket[]>([]);
  const [topQueries, setTopQueries] = useState<TopQuery[]>([]);
  const [escalationAnalysis, setEscalationAnalysis] = useState<EscalationAnalysis | null>(null);
  const [sourceUsage, setSourceUsage] = useState<SourceUsage[]>([]);
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);

  // Fetch all analytics data
  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const days = parseInt(timeRange);

      // Build headers with authentication
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      if (organizationId) {
        headers['X-Organization-ID'] = organizationId;
      }

      // Fetch all analytics endpoints in parallel
      const [
        overviewRes,
        confidenceRes,
        topQueriesRes,
        escalationRes,
        sourceUsageRes,
        performanceRes,
      ] = await Promise.all([
        fetch(`${apiBaseUrl}/knowledge-base/${encodeURIComponent(companyName)}/analytics/overview?days=${days}`, { headers }),
        fetch(`${apiBaseUrl}/knowledge-base/${encodeURIComponent(companyName)}/analytics/confidence-distribution?days=${days}`, { headers }),
        fetch(`${apiBaseUrl}/knowledge-base/${encodeURIComponent(companyName)}/analytics/top-queries?days=${days}&limit=10`, { headers }),
        fetch(`${apiBaseUrl}/knowledge-base/${encodeURIComponent(companyName)}/analytics/escalations?days=${days}`, { headers }),
        fetch(`${apiBaseUrl}/knowledge-base/${encodeURIComponent(companyName)}/analytics/source-usage?days=${days}&limit=10`, { headers }),
        fetch(`${apiBaseUrl}/knowledge-base/${encodeURIComponent(companyName)}/analytics/performance?days=${days}`, { headers }),
      ]);

      const [
        overviewData,
        confidenceData,
        topQueriesData,
        escalationData,
        sourceUsageData,
        performanceData,
      ] = await Promise.all([
        overviewRes.json(),
        confidenceRes.json(),
        topQueriesRes.json(),
        escalationRes.json(),
        sourceUsageRes.json(),
        performanceRes.json(),
      ]);

      setOverview(overviewData.data || overviewData);
      setConfidenceDistribution(confidenceData.data || []);
      setTopQueries(topQueriesData.data || []);
      setEscalationAnalysis(escalationData.data || escalationData);
      setSourceUsage(sourceUsageData.data || []);
      setPerformance(performanceData.data || performanceData);
    } catch (error) {
      console.error('Fetch analytics error:', error);
      toast({
        title: 'Failed to Load Analytics',
        description: error instanceof Error ? error.message : 'Could not load analytics data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Load analytics on mount and when time range changes
  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  // Format numbers
  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  const formatPercent = (num: number) => {
    return `${(num * 100).toFixed(1)}%`;
  };

  const formatMs = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  // Metric Card component
  const MetricCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ElementType;
    iconColor: string;
    trend?: { value: number; isPositive: boolean };
    subtitle?: string;
  }> = ({ title, value, icon: Icon, iconColor, trend, subtitle }) => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm text-gray-600 mb-1">{title}</p>
            <p className="text-3xl font-bold">{value}</p>
            {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
            {trend && (
              <div className={`flex items-center gap-1 mt-2 text-sm ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {trend.isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                <span>{Math.abs(trend.value)}%</span>
              </div>
            )}
          </div>
          <div className={`p-3 rounded-full ${iconColor}`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-semibold flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-blue-600" />
            RAG Analytics Dashboard
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Monitor your knowledge base performance and query insights
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="90">Last 90 days</SelectItem>
              <SelectItem value="365">Last year</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline" size="sm" onClick={fetchAnalytics} disabled={loading}>
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      {loading && !overview ? (
        <Card>
          <CardContent className="p-12 flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Overview Metrics */}
          <div className="grid grid-cols-4 gap-4">
            <MetricCard
              title="Total Queries"
              value={formatNumber(overview?.total_queries || 0)}
              icon={MessageSquare}
              iconColor="bg-blue-600"
              subtitle={`${overview?.daily_query_trend.length || 0} days tracked`}
            />
            <MetricCard
              title="Avg Confidence"
              value={formatPercent(overview?.avg_confidence_score || 0)}
              icon={Target}
              iconColor="bg-green-600"
            />
            <MetricCard
              title="Escalation Rate"
              value={formatPercent(overview?.escalation_rate || 0)}
              icon={AlertTriangle}
              iconColor="bg-orange-600"
            />
            <MetricCard
              title="Avg Response Time"
              value={formatMs(overview?.avg_processing_time_ms || 0)}
              icon={Zap}
              iconColor="bg-purple-600"
            />
          </div>

          {/* Documents Stats */}
          <div className="grid grid-cols-3 gap-4">
            <MetricCard
              title="Total Documents"
              value={formatNumber(overview?.total_documents || 0)}
              icon={FileText}
              iconColor="bg-gray-600"
            />
            <MetricCard
              title="Indexed Documents"
              value={formatNumber(overview?.indexed_documents || 0)}
              icon={CheckCircle}
              iconColor="bg-green-600"
            />
            <MetricCard
              title="Failed Documents"
              value={formatNumber(overview?.failed_documents || 0)}
              icon={AlertTriangle}
              iconColor="bg-red-600"
            />
          </div>

          {/* Confidence Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Confidence Distribution</CardTitle>
              <CardDescription>Query confidence score breakdown</CardDescription>
            </CardHeader>
            <CardContent>
              {confidenceDistribution.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No data available</p>
              ) : (
                <div className="space-y-3">
                  {confidenceDistribution.map((bucket, idx) => (
                    <div key={idx} className="flex items-center gap-4">
                      <div className="w-32 text-sm text-gray-600">{bucket.range}</div>
                      <div className="flex-1">
                        <div className="bg-gray-200 rounded-full h-8 overflow-hidden">
                          <div
                            className="bg-blue-600 h-full flex items-center justify-center text-white text-sm font-medium"
                            style={{ width: `${bucket.percentage}%` }}
                          >
                            {bucket.percentage > 10 && `${bucket.count} (${bucket.percentage.toFixed(1)}%)`}
                          </div>
                        </div>
                      </div>
                      <div className="w-24 text-right text-sm text-gray-600">
                        {bucket.count} queries
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Top Queries */}
          <Card>
            <CardHeader>
              <CardTitle>Top Queries</CardTitle>
              <CardDescription>Most frequently asked questions</CardDescription>
            </CardHeader>
            <CardContent>
              {topQueries.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No queries yet</p>
              ) : (
                <div className="space-y-4">
                  {topQueries.map((query, idx) => (
                    <div key={idx} className="border-b pb-3 last:border-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="font-medium">{query.query}</p>
                          <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                            <span className="flex items-center gap-1">
                              <MessageSquare className="h-3 w-3" />
                              {query.count} times
                            </span>
                            <span className="flex items-center gap-1">
                              <Target className="h-3 w-3" />
                              {formatPercent(query.avg_confidence)} confidence
                            </span>
                            {query.escalation_rate > 0 && (
                              <Badge variant="outline" className="text-orange-600">
                                {formatPercent(query.escalation_rate)} escalated
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Escalation Analysis & Source Usage */}
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Escalation Analysis</CardTitle>
                <CardDescription>Queries requiring human support</CardDescription>
              </CardHeader>
              <CardContent>
                {escalationAnalysis ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Total Escalations</p>
                        <p className="text-2xl font-bold">{escalationAnalysis.total_escalations}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Rate</p>
                        <p className="text-2xl font-bold">{formatPercent(escalationAnalysis.escalation_rate)}</p>
                      </div>
                    </div>
                    {escalationAnalysis.reasons && escalationAnalysis.reasons.length > 0 && (
                      <div className="space-y-2 mt-4">
                        <p className="text-sm font-medium text-gray-700">Top Reasons</p>
                        {escalationAnalysis.reasons.slice(0, 5).map((reason, idx) => (
                          <div key={idx} className="flex justify-between text-sm">
                            <span className="text-gray-600">{reason.reason || 'Unknown'}</span>
                            <span className="font-medium">{reason.count}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No escalation data</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Documents</CardTitle>
                <CardDescription>Most referenced knowledge base documents</CardDescription>
              </CardHeader>
              <CardContent>
                {sourceUsage.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No usage data</p>
                ) : (
                  <div className="space-y-3">
                    {sourceUsage.map((source, idx) => (
                      <div key={idx} className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{source.document_title}</p>
                          <p className="text-xs text-gray-500">
                            {formatPercent(source.avg_confidence)} avg confidence
                          </p>
                        </div>
                        <Badge variant="secondary">{source.reference_count} refs</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Performance Metrics */}
          {performance && (
            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
                <CardDescription>Response time statistics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-5 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Average</p>
                    <p className="text-xl font-bold">{formatMs(performance.avg_response_time_ms)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Minimum</p>
                    <p className="text-xl font-bold">{formatMs(performance.min_response_time_ms)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Maximum</p>
                    <p className="text-xl font-bold">{formatMs(performance.max_response_time_ms)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">P50</p>
                    <p className="text-xl font-bold">{formatMs(performance.p50_response_time_ms)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">P95</p>
                    <p className="text-xl font-bold">{formatMs(performance.p95_response_time_ms)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

export default RAGAnalyticsDashboard;
