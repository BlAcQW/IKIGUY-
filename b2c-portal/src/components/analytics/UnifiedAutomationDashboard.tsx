import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Phone,
  TrendingUp,
  TrendingDown,
  Clock,
  Users,
  MessageSquare,
  DollarSign,
  Heart,
  BarChart3,
  PieChart,
  Loader2,
  RefreshCw,
  Download,
  FileText,
  Settings,
  Zap,
  AlertCircle,
  Play,
  Pause,
  TestTube
} from 'lucide-react';
import {
  automationOrchestrationService,
  type AnalyticsOverview,
  type AutomationStatusResponse
} from '@/services/AutomationOrchestrationService';
import type {
  VAPICallMetrics,
  AutomationHealth,
  CampaignPerformance,
  CallLogEntry,
  ToolCallHealth,
  DashboardSummary,
  TimeRange
} from '@/types/analytics';

interface UnifiedAutomationDashboardProps {
  configId?: string;
  timeRange?: TimeRange;
  className?: string;
}

const UnifiedAutomationDashboard: React.FC<UnifiedAutomationDashboardProps> = ({
  configId,
  timeRange = '7d',
  className = ""
}) => {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [configStatus, setConfigStatus] = useState<AutomationStatusResponse | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null);
  const [vapiMetrics, setVapiMetrics] = useState<VAPICallMetrics[]>([]);
  const [automationHealth, setAutomationHealth] = useState<AutomationHealth[]>([]);
  const [campaignPerformance, setCampaignPerformance] = useState<CampaignPerformance[]>([]);
  const [toolHealth, setToolHealth] = useState<ToolCallHealth[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [selectedTab, setSelectedTab] = useState('overview');
  const { toast } = useToast();
  const { user } = useMongoAuth();

  const loadAnalytics = async () => {
    setIsLoading(true);
    try {
      const [analyticsData, statusData] = await Promise.all([
        automationOrchestrationService.getAnalyticsOverview({
          start_date: new Date(Date.now() - getTimeRangeMs(timeRange)).toISOString(),
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

  const getTimeRangeMs = (range: TimeRange): number => {
    const msMap: Record<TimeRange, number> = {
      '1d': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000,
      '90d': 90 * 24 * 60 * 60 * 1000,
    };
    return msMap[range];
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'deployed':
      case 'healthy':
        return 'status-card-success';
      case 'testing':
      case 'warning':
        return 'status-card-info';
      case 'draft':
        return 'status-card-neutral';
      case 'failed':
      case 'error':
        return 'status-card-error';
      case 'stopped':
        return 'status-card-warning';
      default:
        return 'status-card-neutral';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'deployed':
      case 'healthy':
        return <CheckCircle className="h-4 w-4" />;
      case 'testing':
        return <Activity className="h-4 w-4" />;
      case 'failed':
      case 'error':
        return <XCircle className="h-4 w-4" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4" />;
      case 'stopped':
        return <Pause className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const exportData = (format: 'csv' | 'json' | 'xlsx') => {
    if (!analytics) {
      toast({
        title: "Export Error",
        description: "No data available for export",
        variant: "destructive"
      });
      return;
    }

    const exportData = {
      timeRange,
      analytics,
      configStatus,
      dashboardData,
      exportDate: new Date().toISOString()
    };

    const dataStr = format === 'json'
      ? JSON.stringify(exportData, null, 2)
      : Object.entries(analytics).map(([key, value]) => `${key},${value}`).join('\n');

    const element = document.createElement('a');
    const file = new Blob([dataStr], { type: format === 'json' ? 'application/json' : 'text/csv' });
    element.href = URL.createObjectURL(file);
    element.download = `automation-analytics-${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);

    toast({
      title: "Export Successful",
      description: `Analytics data exported as ${format.toUpperCase()}`
    });
  };

  useEffect(() => {
    loadAnalytics();
    const interval = setInterval(loadAnalytics, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [configId, timeRange]);

  if (isLoading && !analytics) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Automation Analytics</h2>
          <p className="text-gray-600">
            Comprehensive automation performance and monitoring dashboard
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => loadAnalytics()}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Select value={timeRange} onValueChange={(value) => setSelectedTab(value)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1d">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7d</SelectItem>
              <SelectItem value="30d">Last 30d</SelectItem>
              <SelectItem value="90d">Last 90d</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => exportData('json')}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      {analytics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Automations</CardTitle>
              <Zap className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.total_automations}</div>
              <p className="text-xs text-gray-600">
                {analytics.deployed_automations} deployed
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(analytics.success_rate * 100).toFixed(1)}%</div>
              <Progress value={analytics.success_rate * 100} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
              <Phone className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.total_calls}</div>
              <p className="text-xs text-gray-600">
                Avg sentiment: {analytics.avg_sentiment?.toFixed(1) || 'N/A'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
              <DollarSign className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${analytics.total_cost?.toFixed(2) || '0.00'}</div>
              <p className="text-xs text-gray-600">
                Period: {timeRange}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Configuration Status */}
      {configStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              Configuration Status
              <Badge className={`ml-2 ${getStatusColor(configStatus.status)}`}>
                {getStatusIcon(configStatus.status)}
                <span className="ml-1">{configStatus.status}</span>
              </Badge>
            </CardTitle>
            <CardDescription>
              Current automation configuration: {configStatus.config_id}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <p className="text-sm font-medium">Success Rate</p>
                <p className="text-2xl font-bold">{(configStatus.metrics.success_rate * 100).toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-sm font-medium">Total Executions</p>
                <p className="text-2xl font-bold">{configStatus.metrics.total_executions}</p>
              </div>
              <div>
                <p className="text-sm font-medium">Avg Execution Time</p>
                <p className="text-2xl font-bold">{configStatus.metrics.avg_execution_time}s</p>
              </div>
            </div>
            {configStatus.error_message && (
              <div className="mt-4 p-3 status-card-error rounded-md">
                <p className="text-sm status-text-indigo-600">{configStatus.error_message}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tabs for detailed analytics */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="health">Health</TabsTrigger>
          <TabsTrigger value="tools">Tools</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>Analytics Overview</CardTitle>
              <CardDescription>
                High-level automation performance metrics for the selected period
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <BarChart3 className="h-16 w-16 mx-auto text-gray-600 mb-4" />
                <p className="text-gray-600">
                  Detailed analytics dashboard coming soon
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance">
          <Card>
            <CardHeader>
              <CardTitle>Campaign Performance</CardTitle>
              <CardDescription>
                Detailed performance metrics for automation campaigns
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <TrendingUp className="h-16 w-16 mx-auto text-gray-600 mb-4" />
                <p className="text-gray-600">
                  Performance analytics loading...
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="health">
          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
              <CardDescription>
                Real-time health monitoring for automation components
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Heart className="h-16 w-16 mx-auto text-gray-600 mb-4" />
                <p className="text-gray-600">
                  Health monitoring dashboard loading...
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tools">
          <Card>
            <CardHeader>
              <CardTitle>Tool Analytics</CardTitle>
              <CardDescription>
                Performance and health metrics for automation tools
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Settings className="h-16 w-16 mx-auto text-gray-600 mb-4" />
                <p className="text-gray-600">
                  Tool analytics coming soon
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Last Refresh Info */}
      <div className="flex justify-between items-center text-sm text-gray-600">
        <span>Last updated: {lastRefresh.toLocaleString()}</span>
        <span>Data range: {analytics?.period_start} to {analytics?.period_end}</span>
      </div>
    </div>
  );
};

export default UnifiedAutomationDashboard;