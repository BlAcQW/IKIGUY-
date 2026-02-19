/**
 * @deprecated This component has been consolidated into UnifiedAutomationDashboard.
 * Use UnifiedAutomationDashboard instead.
 * This file will be removed in a future release.
 */
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Activity,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Users,
  Clock,
  AlertCircle,
  CheckCircle,
  Phone,
  MessageSquare,
  RefreshCw,
  Download
} from 'lucide-react';
import {
  automationOrchestrationService,
  type AnalyticsOverview,
  type AutomationStatusResponse
} from '@/services/AutomationOrchestrationService';
import { useToast } from '@/hooks/use-toast';

interface AutomationAnalyticsDashboardProps {
  configId?: string;
  className?: string;
}

const AutomationAnalyticsDashboard: React.FC<AutomationAnalyticsDashboardProps> = ({
  configId,
  className = ""
}) => {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [configStatus, setConfigStatus] = useState<AutomationStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const { toast } = useToast();

  const loadAnalytics = async () => {
    setIsLoading(true);
    try {
      const [analyticsData, statusData] = await Promise.all([
        automationOrchestrationService.getAnalyticsOverview({
          start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          end_date: new Date().toISOString()
        }),
        configId ? automationOrchestrationService.getConfigurationStatus(configId) : null
      ]);

      setAnalytics(analyticsData);
      if (statusData) {
        setConfigStatus(statusData);
      }
      setLastRefresh(new Date());
    } catch (error) {
      toast({
        title: "Failed to Load Analytics",
        description: error instanceof Error ? error.message : "Could not load analytics data",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();

    // Auto-refresh every 5 minutes
    const interval = setInterval(loadAnalytics, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [configId]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'deployed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'testing':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'draft':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'stopped':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'deployed':
        return <CheckCircle className="h-4 w-4" />;
      case 'testing':
        return <Activity className="h-4 w-4" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ${minutes % 60}m`;
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Analytics Dashboard</h2>
          <p className="text-gray-600">
            Monitor automation performance and usage metrics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={loadAnalytics}
            disabled={isLoading}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      {configStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {getStatusIcon(configStatus.status)}
              Configuration Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label className="text-sm font-medium text-gray-500">Status</Label>
                <Badge className={`${getStatusColor(configStatus.status)} mt-1`}>
                  {configStatus.status.toUpperCase()}
                </Badge>
              </div>
              <div>
                <Label className="text-sm font-medium text-gray-500">Deployed At</Label>
                <p className="text-sm font-medium">
                  {configStatus.deployed_at
                    ? new Date(configStatus.deployed_at).toLocaleString()
                    : 'Not deployed'
                  }
                </p>
              </div>
              <div>
                <Label className="text-sm font-medium text-gray-500">Health</Label>
                <p className="text-sm font-medium">
                  {configStatus.health?.overall || 'Unknown'}
                </p>
              </div>
            </div>

            {/* Metrics */}
            {configStatus.metrics && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t">
                <div>
                  <Label className="text-sm font-medium text-gray-500">Uptime</Label>
                  <p className="text-lg font-bold text-green-600">
                    {configStatus.metrics.uptime}
                  </p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-500">Requests</Label>
                  <p className="text-lg font-bold">
                    {formatNumber(configStatus.metrics.requests_handled)}
                  </p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-500">Avg Response</Label>
                  <p className="text-lg font-bold">
                    {configStatus.metrics.avg_response_time}ms
                  </p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-500">Errors</Label>
                  <p className={`text-lg font-bold ${
                    configStatus.metrics.errors > 0 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {configStatus.metrics.errors}
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Analytics Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="deployments">Deployments</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {analytics && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Templates</CardTitle>
                  <BarChart3 className="h-4 w-4 text-gray-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {analytics.summary.total_templates}
                  </div>
                  <p className="text-xs text-gray-600">
                    Available automation templates
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Configurations</CardTitle>
                  <Users className="h-4 w-4 text-gray-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {analytics.summary.total_configurations}
                  </div>
                  <p className="text-xs text-gray-600">
                    Created configurations
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Deployments</CardTitle>
                  <Activity className="h-4 w-4 text-gray-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">
                    {analytics.summary.active_deployments}
                  </div>
                  <p className="text-xs text-gray-600">
                    Currently running
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                  <TrendingUp className="h-4 w-4 text-gray-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">
                    {(analytics.summary.success_rate * 100).toFixed(1)}%
                  </div>
                  <p className="text-xs text-gray-600">
                    Deployment success rate
                  </p>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Template Usage</CardTitle>
              <CardDescription>
                Most popular automation templates
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {analytics?.templates && Object.entries(analytics.templates).map(([key, value]: [string, any]) => (
                  <div key={key} className="flex items-center justify-between p-2 rounded-lg border">
                    <span className="font-medium">{key}</span>
                    <Badge variant="outline">{value.count || 0} uses</Badge>
                  </div>
                ))}
                {(!analytics?.templates || Object.keys(analytics.templates).length === 0) && (
                  <p className="text-center text-gray-500 py-4">No template data available</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="deployments" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Deployment Statistics</CardTitle>
              <CardDescription>
                Deployment trends and patterns
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics?.deployments && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg border">
                      <h4 className="font-medium">Total Deployments</h4>
                      <p className="text-2xl font-bold text-blue-600">
                        {analytics.deployments.total || 0}
                      </p>
                    </div>
                    <div className="p-4 rounded-lg border">
                      <h4 className="font-medium">Success Rate</h4>
                      <p className="text-2xl font-bold text-green-600">
                        {((analytics.deployments.successful || 0) / (analytics.deployments.total || 1) * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
              <CardDescription>
                System performance and response times
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg border">
                    <h4 className="font-medium">Average Response Time</h4>
                    <p className="text-2xl font-bold">
                      {configStatus?.metrics?.avg_response_time || 0}ms
                    </p>
                  </div>
                  <div className="p-4 rounded-lg border">
                    <h4 className="font-medium">Total Requests</h4>
                    <p className="text-2xl font-bold">
                      {formatNumber(configStatus?.metrics?.requests_handled || 0)}
                    </p>
                  </div>
                  <div className="p-4 rounded-lg border">
                    <h4 className="font-medium">Error Rate</h4>
                    <p className={`text-2xl font-bold ${
                      (configStatus?.metrics?.errors || 0) > 0 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {(((configStatus?.metrics?.errors || 0) / (configStatus?.metrics?.requests_handled || 1)) * 100).toFixed(2)}%
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AutomationAnalyticsDashboard;