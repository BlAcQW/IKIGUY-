/**
 * Automation Analytics Modal
 *
 * Displays comprehensive analytics for an automation configuration,
 * including call metrics, trends, and recent call history.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import {
  BarChart3,
  Phone,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle2,
  XCircle,
  Voicemail,
  PhoneOff,
  RefreshCw,
  Loader2,
  AlertTriangle,
  Calendar,
  Sparkles,
  DollarSign,
  Smile,
  Frown,
  Meh,
  MessageSquare
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  automationAnalyticsService,
  type AutomationAnalytics,
  type CallMetrics
} from '@/services/AutomationAnalyticsService';
import { ToolCallLogsTable } from '@/components/tool-calls/ToolCallLogsTable';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

interface AutomationAnalyticsModalProps {
  isOpen: boolean;
  onClose: () => void;
  automationId: string;
  automationName: string;
}

// Helper functions for sentiment display
const getSentimentVariant = (sentiment?: string): "default" | "destructive" | "secondary" | "outline" => {
  switch (sentiment?.toLowerCase()) {
    case 'positive': return 'default'; // green
    case 'negative': return 'destructive'; // red
    case 'mixed': return 'secondary'; // gray
    default: return 'outline'; // neutral
  }
};

const getSentimentIcon = (sentiment?: string): string => {
  switch (sentiment?.toLowerCase()) {
    case 'positive': return '😊';
    case 'negative': return '😟';
    case 'mixed': return '😐';
    default: return '😶';
  }
};

const getSentimentColor = (sentiment?: string): string => {
  switch (sentiment?.toLowerCase()) {
    case 'positive': return 'status-card-success';
    case 'negative': return 'status-card-error';
    case 'mixed': return 'status-card-warning';
    default: return 'status-card-neutral';
  }
};

export const AutomationAnalyticsModal: React.FC<AutomationAnalyticsModalProps> = ({
  isOpen,
  onClose,
  automationId,
  automationName
}) => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [analytics, setAnalytics] = useState<AutomationAnalytics | null>(null);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');
  const [error, setError] = useState<string | null>(null);

  // Fetch analytics data
  const fetchAnalytics = async (forceRefresh: boolean = false) => {
    try {
      setLoading(true);
      setError(null);
      const data = await automationAnalyticsService.getAutomationAnalytics(
        automationId,
        timeRange,
        forceRefresh
      );
      setAnalytics(data);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load analytics';
      setError(errorMessage);
      toast({
        title: 'Error loading analytics',
        description: errorMessage,
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Refresh analytics from VAPI
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAnalytics(true);
    toast({
      title: 'Analytics refreshed',
      description: 'Latest data fetched from VAPI'
    });
  };

  // Fetch analytics when modal opens or time range changes
  // Always force refresh to ensure we get the latest cost settings
  useEffect(() => {
    if (isOpen) {
      fetchAnalytics(true);
    }
  }, [isOpen, timeRange]);

  // Get metric card color based on success rate
  const getSuccessRateColor = (rate: number) => {
    if (rate >= 80) return 'status-card-success';
    if (rate >= 60) return 'status-card-warning';
    return 'status-card-error';
  };

  // Render loading state
  if (loading && !analytics) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>Loading Analytics</DialogTitle>
            <DialogDescription>
              Loading analytics data for {automationName}...
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  // Render error state
  if (error && !analytics) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>Analytics - {automationName}</DialogTitle>
            <DialogDescription>
              Error loading analytics data
            </DialogDescription>
          </DialogHeader>
          <Card className="status-card-error">
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 status-icon-error" />
                <CardTitle className="status-text-indigo-600">Failed to Load Analytics</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="status-text-indigo-600">{error}</p>
              <Button onClick={() => fetchAnalytics()} className="mt-4">
                Try Again
              </Button>
            </CardContent>
          </Card>
        </DialogContent>
      </Dialog>
    );
  }

  const metrics = analytics?.metrics;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Analytics - {automationName}
              </DialogTitle>
              <DialogDescription>
                Performance metrics and call analytics
                {analytics?.assistant_id && (
                  <span className="block text-xs mt-1">
                    Assistant ID: {analytics.assistant_id}
                  </span>
                )}
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              {/* Time Range Selector */}
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as any)}
                className="border border-border bg-background text-foreground rounded-md px-3 py-1 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20"
                disabled={loading}
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="all">All time</option>
              </select>

              {/* Refresh Button */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </DialogHeader>

        <Tabs defaultValue="overview" className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="mx-6 mt-4 grid w-auto grid-cols-2">
            <TabsTrigger value="overview">
              <BarChart3 className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="tool-logs">
              <MessageSquare className="h-4 w-4 mr-2" />
              Tool Call Logs
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="flex-1 overflow-auto mt-0">
            <div className="space-y-6 p-6 pr-4 overflow-y-auto max-h-[calc(90vh-180px)]">
            {/* Key Metrics Cards - Row 1: Target vs Actual */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Target Calls */}
              <Card className="bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-950/20 dark:to-indigo-950/20 border-purple-200 dark:border-purple-800">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">Target Calls</CardTitle>
                    <Phone className="h-4 w-4 text-purple-600" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-purple-700 dark:text-purple-300">
                    {(50000).toLocaleString()}
                  </div>
                  <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                    Campaign target
                  </p>
                </CardContent>
              </Card>

              {/* Target Cost */}
              <Card className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 border-green-200 dark:border-green-800">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">Target Cost</CardTitle>
                    <DollarSign className="h-4 w-4 text-green-600" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-700 dark:text-green-300">
                    {metrics?.cost_currency_symbol || 'GH₵'}
                    {(50000 * (metrics?.cost_rate_per_call || 1.2)).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </div>
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                    50,000 × {metrics?.cost_currency_symbol || 'GH₵'}{metrics?.cost_rate_per_call || 1.2}/call
                  </p>
                </CardContent>
              </Card>

              {/* Actual Calls */}
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">Actual Calls</CardTitle>
                    <Phone className="h-4 w-4 text-gray-600" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics?.total_calls?.toLocaleString() || 0}</div>
                  <p className="text-xs text-gray-600 mt-1">
                    {((metrics?.total_calls || 0) / 50000 * 100).toFixed(1)}% of target
                  </p>
                </CardContent>
              </Card>

              {/* Actual Cost */}
              <Card className="status-card-success">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">Actual Cost</CardTitle>
                    <DollarSign className="h-4 w-4 status-icon-success" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold card-value">
                    {metrics?.cost_currency_symbol || 'GH₵'}
                    {((metrics?.total_calls || 0) * (metrics?.cost_rate_per_call || 1.2)).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </div>
                  <p className="text-xs status-text-indigo-600 mt-1">
                    {metrics?.total_calls?.toLocaleString() || 0} × {metrics?.cost_currency_symbol || 'GH₵'}{metrics?.cost_rate_per_call || 1.2}/call
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* AI Analysis Row */}
            <div className="grid grid-cols-1 md:grid-cols-1 gap-4">
              {/* AI Enrichment */}
              <Card className="accent-card-purple">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">AI Analysis</CardTitle>
                    <Sparkles className="h-4 w-4 accent-icon-purple" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold card-value">
                    {metrics?.ai_enrichment_rate || 0}%
                  </div>
                  <p className="text-xs status-text-indigo-600 mt-1">
                    {metrics?.ai_enriched_count || 0}/{metrics?.total_calls || 0} calls analyzed
                  </p>
                  <Progress
                    value={metrics?.ai_enrichment_rate || 0}
                    className="mt-2 h-2"
                  />
                </CardContent>
              </Card>
            </div>

            {/* Call Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Call Breakdown</CardTitle>
                <CardDescription>Distribution of call outcomes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 status-icon-success" />
                    <div>
                      <div className="text-sm font-medium">{metrics?.successful_calls?.toLocaleString() || 0}</div>
                      <div className="text-xs text-gray-600">Successful</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <XCircle className="h-4 w-4 status-icon-error" />
                    <div>
                      <div className="text-sm font-medium">{metrics?.failed_calls?.toLocaleString() || 0}</div>
                      <div className="text-xs text-gray-600">Failed</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Voicemail className="h-4 w-4 status-icon-info" />
                    <div>
                      <div className="text-sm font-medium">{metrics?.voicemail_calls?.toLocaleString() || 0}</div>
                      <div className="text-xs text-gray-600">Voicemail</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <PhoneOff className="h-4 w-4 status-icon-warning" />
                    <div>
                      <div className="text-sm font-medium">{metrics?.no_answer_calls?.toLocaleString() || 0}</div>
                      <div className="text-xs text-gray-600">No Answer</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 status-icon-neutral" />
                    <div>
                      <div className="text-sm font-medium">{metrics?.call_breakdown?.other?.toLocaleString() || 0}</div>
                      <div className="text-xs text-gray-600">Other</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Stats Row: Success Rate, Connect Rate, Total Minutes */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Success Rate */}
              <Card className={metrics?.success_rate ? getSuccessRateColor(metrics.success_rate) : ''}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                    <TrendingUp className="h-4 w-4" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics?.success_rate || 0}%</div>
                  <Progress value={metrics?.success_rate || 0} className="mt-2 h-2" />
                </CardContent>
              </Card>

              {/* Connect Rate */}
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">Connect Rate</CardTitle>
                    <CheckCircle2 className="h-4 w-4 text-gray-600" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics?.connect_rate || 0}%</div>
                  <Progress value={metrics?.connect_rate || 0} className="mt-2 h-2" />
                </CardContent>
              </Card>

              {/* Total Minutes */}
              <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border-blue-200 dark:border-blue-800">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">Total Minutes</CardTitle>
                    <Clock className="h-4 w-4 text-blue-600" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                    {metrics?.total_duration_minutes?.toLocaleString(undefined, { maximumFractionDigits: 1 }) ||
                     (metrics?.total_duration ? (metrics.total_duration / 60).toLocaleString(undefined, { maximumFractionDigits: 1 }) : '0')}
                    <span className="text-sm font-normal ml-1">min</span>
                  </div>
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    {metrics?.total_duration ? `${(metrics.total_duration / 3600).toFixed(1)} hours` : '0 hours'}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Sentiment Analysis */}
            {metrics?.sentiment_breakdown && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Sentiment Analysis
                  </CardTitle>
                  <CardDescription>
                    AI-detected sentiment from call conversations
                    {metrics?.dominant_sentiment && (
                      <span className="block text-xs mt-1">
                        Dominant: <span className="font-medium capitalize">{metrics.dominant_sentiment}</span> {getSentimentIcon(metrics.dominant_sentiment)}
                      </span>
                    )}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Positive */}
                    <div className={`p-3 rounded-lg ${getSentimentColor('positive')}`}>
                      <div className="flex items-center justify-between">
                        <Smile className="h-5 w-5" />
                        <div className="text-right">
                          <div className="text-2xl font-bold">
                            {metrics.sentiment_breakdown.positive || 0}
                          </div>
                          <div className="text-xs font-medium">Positive</div>
                        </div>
                      </div>
                      {metrics.total_calls > 0 && (
                        <Progress
                          value={(metrics.sentiment_breakdown.positive / metrics.total_calls) * 100}
                          className="mt-2 h-1"
                        />
                      )}
                    </div>

                    {/* Negative */}
                    <div className={`p-3 rounded-lg ${getSentimentColor('negative')}`}>
                      <div className="flex items-center justify-between">
                        <Frown className="h-5 w-5" />
                        <div className="text-right">
                          <div className="text-2xl font-bold">
                            {metrics.sentiment_breakdown.negative || 0}
                          </div>
                          <div className="text-xs font-medium">Negative</div>
                        </div>
                      </div>
                      {metrics.total_calls > 0 && (
                        <Progress
                          value={(metrics.sentiment_breakdown.negative / metrics.total_calls) * 100}
                          className="mt-2 h-1"
                        />
                      )}
                    </div>

                    {/* Neutral */}
                    <div className={`p-3 rounded-lg ${getSentimentColor('neutral')}`}>
                      <div className="flex items-center justify-between">
                        <Meh className="h-5 w-4" />
                        <div className="text-right">
                          <div className="text-2xl font-bold">
                            {metrics.sentiment_breakdown.neutral || 0}
                          </div>
                          <div className="text-xs font-medium">Neutral</div>
                        </div>
                      </div>
                      {metrics.total_calls > 0 && (
                        <Progress
                          value={(metrics.sentiment_breakdown.neutral / metrics.total_calls) * 100}
                          className="mt-2 h-1"
                        />
                      )}
                    </div>

                    {/* Mixed */}
                    <div className={`p-3 rounded-lg ${getSentimentColor('mixed')}`}>
                      <div className="flex items-center justify-between">
                        <div className="text-lg">🤔</div>
                        <div className="text-right">
                          <div className="text-2xl font-bold">
                            {metrics.sentiment_breakdown.mixed || 0}
                          </div>
                          <div className="text-xs font-medium">Mixed</div>
                        </div>
                      </div>
                      {metrics.total_calls > 0 && (
                        <Progress
                          value={(metrics.sentiment_breakdown.mixed / metrics.total_calls) * 100}
                          className="mt-2 h-1"
                        />
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Trend Charts */}
            {analytics?.trend_data && analytics.trend_data.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Call Trends</CardTitle>
                  <CardDescription>Daily call volume and success metrics</CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="volume" className="w-full">
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="volume">Call Volume</TabsTrigger>
                      <TabsTrigger value="duration">Duration</TabsTrigger>
                    </TabsList>

                    <TabsContent value="volume" className="mt-4">
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={analytics.trend_data}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="date"
                            tick={{ fontSize: 12 }}
                            tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          />
                          <YAxis />
                          <Tooltip
                            labelFormatter={(value) => new Date(value).toLocaleDateString()}
                          />
                          <Legend />
                          <Line type="monotone" dataKey="calls" stroke="#8884d8" name="Total Calls" strokeWidth={2} />
                          <Line type="monotone" dataKey="successful" stroke="#82ca9d" name="Successful" strokeWidth={2} />
                        </LineChart>
                      </ResponsiveContainer>
                    </TabsContent>

                    <TabsContent value="duration" className="mt-4">
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={analytics.trend_data}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="date"
                            tick={{ fontSize: 12 }}
                            tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          />
                          <YAxis />
                          <Tooltip
                            labelFormatter={(value) => new Date(value).toLocaleDateString()}
                            formatter={(value: number) => [`${Math.round(value / 60)}m`, 'Duration']}
                          />
                          <Legend />
                          <Bar dataKey="duration" fill="#8884d8" name="Total Duration (min)" />
                        </BarChart>
                      </ResponsiveContainer>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            )}

            {/* Recent Calls with AI Insights */}
            {analytics?.recent_calls && analytics.recent_calls.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Phone className="h-5 w-5" />
                    Recent Calls
                    {metrics?.ai_enriched_count > 0 && (
                      <Badge variant="secondary" className="ml-2">
                        <Sparkles className="h-3 w-3 mr-1" />
                        {metrics.ai_enriched_count} AI-enriched
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription>Latest {analytics.recent_calls.length} calls with AI insights</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {analytics.recent_calls.map((call, index) => (
                      <div
                        key={call.id || index}
                        className="p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          {/* Call Info */}
                          <div className="flex items-start gap-3 flex-1">
                            {call.status === 'ended' ? (
                              <CheckCircle2 className="h-5 w-5 status-icon-success mt-0.5" />
                            ) : call.status === 'failed' ? (
                              <XCircle className="h-5 w-5 status-icon-error mt-0.5" />
                            ) : (
                              <Phone className="h-5 w-5 status-icon-info mt-0.5" />
                            )}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <div className="text-sm font-medium">
                                  {call.customer?.number || 'Unknown'}
                                </div>
                                <Badge variant={call.status === 'ended' ? 'default' : 'secondary'} className="text-xs">
                                  {call.status}
                                </Badge>
                                {call.sentiment && (
                                  <Badge variant={getSentimentVariant(call.sentiment)} className="text-xs">
                                    {getSentimentIcon(call.sentiment)} {call.sentiment}
                                  </Badge>
                                )}
                                {call.ai_enriched && (
                                  <Badge variant="outline" className="text-xs accent-card-purple">
                                    <Sparkles className="h-3 w-3 mr-1" />
                                    AI
                                  </Badge>
                                )}
                              </div>

                              {/* AI Summary */}
                              {call.ai_summary && (
                                <div className="mt-2 p-2 status-card-info rounded text-xs">
                                  <div className="flex items-start gap-1">
                                    <MessageSquare className="h-3 w-3 mt-0.5 flex-shrink-0" />
                                    <span className="line-clamp-2">{call.ai_summary}</span>
                                  </div>
                                </div>
                              )}

                              {/* Transcript Preview */}
                              {!call.ai_summary && call.transcript_preview && (
                                <div className="mt-2 text-xs text-gray-600 italic line-clamp-1">
                                  "{call.transcript_preview}"
                                </div>
                              )}

                              <div className="flex items-center gap-3 mt-2 text-xs text-gray-600">
                                <span className="flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  {call.createdAt && new Date(call.createdAt).toLocaleString()}
                                </span>
                                {call.duration > 0 && (
                                  <span className="flex items-center gap-1">
                                    <Clock className="h-3 w-3" />
                                    {Math.round(call.duration)}s
                                  </span>
                                )}
                                {call.vonage_cost !== undefined && call.vonage_cost > 0 && (
                                  <span className="flex items-center gap-1 status-icon-success">
                                    <DollarSign className="h-3 w-3" />
                                    ${call.vonage_cost.toFixed(4)}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Last Updated */}
            {analytics?.last_updated && (
              <div className="text-xs text-gray-600 text-right">
                Last updated: {new Date(analytics.last_updated).toLocaleString()}
              </div>
            )}
            </div>
          </TabsContent>

          {/* Tool Call Logs Tab */}
          <TabsContent value="tool-logs" className="flex-1 overflow-auto mt-0">
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Tool Call Logs
                  </CardTitle>
                  <CardDescription>
                    All tool calls made during this automation's execution
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ToolCallLogsTable
                    automationId={automationId}
                    showFilters={true}
                    showExport={true}
                    pageSize={50}
                    compact={false}
                  />
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

export default AutomationAnalyticsModal;
