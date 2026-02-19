/**
 * Admin Analytics Modal
 *
 * Displays detailed VAPI cost breakdown and usage metrics for admins.
 * Only visible to universal_admin users.
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
import {
  BarChart3,
  RefreshCw,
  Loader2,
  AlertTriangle,
  DollarSign,
  Sparkles,
  Clock,
  Phone,
  Shield
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  automationAnalyticsService,
  type AutomationAnalytics,
} from '@/services/AutomationAnalyticsService';

interface AdminAnalyticsModalProps {
  isOpen: boolean;
  onClose: () => void;
  automationId: string;
  automationName: string;
}

export const AdminAnalyticsModal: React.FC<AdminAnalyticsModalProps> = ({
  isOpen,
  onClose,
  automationId,
  automationName
}) => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [analytics, setAnalytics] = useState<AutomationAnalytics | null>(null);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('all');
  const [error, setError] = useState<string | null>(null);

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
        title: 'Error loading admin analytics',
        description: errorMessage,
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAnalytics(true);
    toast({
      title: 'Analytics refreshed',
      description: 'Latest data fetched from VAPI'
    });
  };

  useEffect(() => {
    if (isOpen) {
      fetchAnalytics();
    }
  }, [isOpen, timeRange]);

  if (loading && !analytics) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-orange-500" />
              Admin Analytics
            </DialogTitle>
            <DialogDescription>Loading admin analytics...</DialogDescription>
          </DialogHeader>
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (error && !analytics) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-orange-500" />
              Admin Analytics - {automationName}
            </DialogTitle>
          </DialogHeader>
          <Card className="border-red-200 bg-red-50">
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <CardTitle className="text-red-700">Failed to Load Analytics</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-red-600">{error}</p>
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
      <DialogContent className="max-w-4xl h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-orange-500" />
                Admin Analytics - {automationName}
              </DialogTitle>
              <DialogDescription>
                Detailed VAPI cost breakdown and usage metrics
                {analytics?.assistant_id && (
                  <span className="block text-xs mt-1">
                    Assistant ID: {analytics.assistant_id}
                  </span>
                )}
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as any)}
                className="border border-border bg-background text-foreground rounded-md px-3 py-1 text-sm"
                disabled={loading}
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="all">All time</option>
              </select>
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

        <div className="flex-1 overflow-y-auto space-y-6 p-1">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Total Calls
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {metrics?.total_calls?.toLocaleString() || 0}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Total Minutes
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {metrics?.total_duration_minutes?.toLocaleString(undefined, { maximumFractionDigits: 1 }) ||
                   (metrics?.total_duration ? (metrics.total_duration / 60).toLocaleString(undefined, { maximumFractionDigits: 1 }) : '0')}
                </div>
                <p className="text-xs text-muted-foreground">
                  {metrics?.total_duration ? `${(metrics.total_duration / 3600).toFixed(1)} hours` : '0 hours'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  VAPI Cost
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  ${metrics?.vapi_cost_breakdown?.total?.toFixed(2) || '0.00'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Avg: ${metrics?.avg_cost_per_call?.toFixed(4) || '0.0000'}/call
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-green-600" />
                  Billed Cost
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {metrics?.cost_currency_symbol || '$'}
                  {metrics?.total_cost?.toFixed(2) || '0.00'}
                  {metrics?.cost_currency && metrics.cost_currency !== 'USD' && (
                    <span className="text-sm ml-1 font-normal">{metrics.cost_currency}</span>
                  )}
                </div>
                {metrics?.cost_rate_per_minute && (
                  <p className="text-xs text-muted-foreground">
                    Rate: {metrics.cost_currency_symbol}{metrics.cost_rate_per_minute}/min
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* VAPI Cost Breakdown */}
          {metrics?.vapi_cost_breakdown && metrics.vapi_cost_breakdown.total > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5" />
                  VAPI Cost Breakdown
                </CardTitle>
                <CardDescription>Cost by service component (USD)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg text-center">
                    <div className="text-2xl font-bold text-blue-700">
                      ${metrics.vapi_cost_breakdown.llm?.toFixed(2) || '0.00'}
                    </div>
                    <div className="text-xs text-muted-foreground">LLM (AI Model)</div>
                    <div className="text-xs text-blue-600">
                      {metrics.vapi_cost_breakdown.total > 0
                        ? ((metrics.vapi_cost_breakdown.llm / metrics.vapi_cost_breakdown.total) * 100).toFixed(1)
                        : 0}%
                    </div>
                  </div>

                  <div className="p-4 bg-purple-50 dark:bg-purple-950/20 rounded-lg text-center">
                    <div className="text-2xl font-bold text-purple-700">
                      ${metrics.vapi_cost_breakdown.tts?.toFixed(2) || '0.00'}
                    </div>
                    <div className="text-xs text-muted-foreground">TTS (Voice)</div>
                    <div className="text-xs text-purple-600">
                      {metrics.vapi_cost_breakdown.total > 0
                        ? ((metrics.vapi_cost_breakdown.tts / metrics.vapi_cost_breakdown.total) * 100).toFixed(1)
                        : 0}%
                    </div>
                  </div>

                  <div className="p-4 bg-green-50 dark:bg-green-950/20 rounded-lg text-center">
                    <div className="text-2xl font-bold text-green-700">
                      ${metrics.vapi_cost_breakdown.stt?.toFixed(2) || '0.00'}
                    </div>
                    <div className="text-xs text-muted-foreground">STT (Transcription)</div>
                    <div className="text-xs text-green-600">
                      {metrics.vapi_cost_breakdown.total > 0
                        ? ((metrics.vapi_cost_breakdown.stt / metrics.vapi_cost_breakdown.total) * 100).toFixed(1)
                        : 0}%
                    </div>
                  </div>

                  <div className="p-4 bg-orange-50 dark:bg-orange-950/20 rounded-lg text-center">
                    <div className="text-2xl font-bold text-orange-700">
                      ${metrics.vapi_cost_breakdown.transport?.toFixed(2) || '0.00'}
                    </div>
                    <div className="text-xs text-muted-foreground">Transport (Phone)</div>
                    <div className="text-xs text-orange-600">
                      {metrics.vapi_cost_breakdown.total > 0
                        ? ((metrics.vapi_cost_breakdown.transport / metrics.vapi_cost_breakdown.total) * 100).toFixed(1)
                        : 0}%
                    </div>
                  </div>

                  <div className="p-4 bg-gray-50 dark:bg-gray-950/20 rounded-lg text-center">
                    <div className="text-2xl font-bold text-gray-700">
                      ${metrics.vapi_cost_breakdown.vapi?.toFixed(2) || '0.00'}
                    </div>
                    <div className="text-xs text-muted-foreground">VAPI Platform</div>
                    <div className="text-xs text-gray-600">
                      {metrics.vapi_cost_breakdown.total > 0
                        ? ((metrics.vapi_cost_breakdown.vapi / metrics.vapi_cost_breakdown.total) * 100).toFixed(1)
                        : 0}%
                    </div>
                  </div>
                </div>

                <div className="mt-4 p-4 bg-indigo-50 dark:bg-indigo-950/20 rounded-lg">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Total VAPI Cost</span>
                    <span className="text-2xl font-bold text-indigo-700">
                      ${metrics.vapi_cost_breakdown.total?.toFixed(2) || '0.00'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Usage Metrics */}
          {metrics?.usage && (metrics.usage.total_tokens > 0 || metrics.usage.tts_characters > 0) && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  Usage Metrics
                </CardTitle>
                <CardDescription>Token and character consumption</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg text-center">
                    <div className="text-2xl font-bold text-blue-700">
                      {metrics.usage.prompt_tokens?.toLocaleString() || '0'}
                    </div>
                    <div className="text-xs text-muted-foreground">Prompt Tokens</div>
                  </div>

                  <div className="p-4 bg-green-50 dark:bg-green-950/20 rounded-lg text-center">
                    <div className="text-2xl font-bold text-green-700">
                      {metrics.usage.completion_tokens?.toLocaleString() || '0'}
                    </div>
                    <div className="text-xs text-muted-foreground">Completion Tokens</div>
                  </div>

                  <div className="p-4 bg-indigo-50 dark:bg-indigo-950/20 rounded-lg text-center">
                    <div className="text-2xl font-bold text-indigo-700">
                      {metrics.usage.total_tokens?.toLocaleString() || '0'}
                    </div>
                    <div className="text-xs text-muted-foreground">Total Tokens</div>
                  </div>

                  <div className="p-4 bg-purple-50 dark:bg-purple-950/20 rounded-lg text-center">
                    <div className="text-2xl font-bold text-purple-700">
                      {metrics.usage.tts_characters?.toLocaleString() || '0'}
                    </div>
                    <div className="text-xs text-muted-foreground">TTS Characters</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Duration Statistics */}
          {(metrics?.min_duration !== undefined || metrics?.max_duration !== undefined) && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Duration Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="p-4 bg-green-50 dark:bg-green-950/20 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {metrics.min_duration ? `${Math.round(metrics.min_duration)}s` : '0s'}
                    </div>
                    <div className="text-xs text-muted-foreground">Shortest Call</div>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-gray-950/20 rounded-lg">
                    <div className="text-2xl font-bold">
                      {metrics.avg_duration ? `${Math.round(metrics.avg_duration)}s` : '0s'}
                    </div>
                    <div className="text-xs text-muted-foreground">Average</div>
                  </div>
                  <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {metrics.max_duration ? `${Math.round(metrics.max_duration)}s` : '0s'}
                    </div>
                    <div className="text-xs text-muted-foreground">Longest Call</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Last Updated */}
          {analytics?.last_updated && (
            <div className="text-xs text-muted-foreground text-right">
              Last updated: {new Date(analytics.last_updated).toLocaleString()}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AdminAnalyticsModal;
