/**
 * @deprecated This component has been consolidated into UnifiedAutomationDashboard.
 * Use UnifiedAutomationDashboard instead.
 * This file will be removed in a future release.
 *
 * Original description:
 * Comprehensive Automation Monitoring Dashboard
 * This component provides real-time monitoring of automation health,
 * VAPI call analytics, and campaign performance metrics.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';

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

interface VAPICallMetrics {
  id: string;
  automation_id: string;
  campaign_id?: string;
  call_duration: number;
  call_status: string;
  sentiment_score?: number;
  cost?: number;
  created_at: string;
  metadata: Record<string, any>;
}

interface AutomationHealth {
  id: string;
  automation_id: string;
  campaign_id?: string;
  status: string;
  error_count: number;
  success_rate: number;
  last_execution: string;
  performance_metrics: Record<string, any>;
}

interface CampaignPerformance {
  id: string;
  campaign_id: string;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  total_cost: number;
  avg_call_duration: number;
  avg_sentiment_score?: number;
  success_rate: number;
  total_conversions: number;
  conversion_rate: number;
}

interface CallLogEntry {
  id: string;
  call_id: string;
  assistant_id?: string;
  automation_id?: string;
  campaign_id?: string;
  phone_number?: string;
  call_status: string;
  call_duration?: number;
  cost?: number;
  transcript?: string;
  summary?: string;
  sentiment_score?: number;
  tool_calls?: any[];
  webhook_data?: any;
  metadata?: any;
  created_at: string;
  updated_at?: string;
}

interface ToolCallHealth {
  tool_name: string;
  total_calls: number;
  success_rate: number;
  avg_execution_time?: number;
  error_rate: number;
  common_errors: string[];
  last_called: string;
  status: 'healthy' | 'warning' | 'error';
}

interface VAPITestResult {
  test_id: string;
  test_type: string;
  success: boolean;
  duration: number;
  details: any;
  error?: string;
  timestamp: string;
}

interface DashboardSummary {
  period: {
    start_date: string;
    end_date: string;
  };
  vapi_metrics: {
    total_calls: number;
    total_cost: number;
    avg_call_duration: number;
    avg_sentiment_score: number;
  };
  automation_health: {
    total_automations: number;
    healthy_automations: number;
    health_percentage: number;
  };
  campaign_performance: {
    total_campaigns: number;
    avg_success_rate: number;
    total_conversions: number;
  };
}

interface AutomationMonitoringDashboardProps {
  timeRange?: string;
}

const AutomationMonitoringDashboard: React.FC<AutomationMonitoringDashboardProps> = ({
  timeRange = '7d'
}) => {
  const [selectedTab, setSelectedTab] = useState('overview');
  const [selectedAutomation, setSelectedAutomation] = useState('all');
  const [selectedCampaign, setSelectedCampaign] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const { toast } = useToast();
  const { user, getTenantId } = useMongoAuth();

  // State for monitoring data
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
  const [vapiCallMetrics, setVapiCallMetrics] = useState<VAPICallMetrics[]>([]);
  const [automationHealth, setAutomationHealth] = useState<AutomationHealth[]>([]);
  const [campaignPerformance, setCampaignPerformance] = useState<CampaignPerformance[]>([]);
  const [callLogs, setCallLogs] = useState<CallLogEntry[]>([]);
  const [toolCallHealth, setToolCallHealth] = useState<ToolCallHealth[]>([]);
  const [testResults, setTestResults] = useState<VAPITestResult[]>([]);
  const [isRunningTest, setIsRunningTest] = useState(false);

  // Using API_BASE_URL from api-config;

  // Fetch monitoring data
  const fetchMonitoringData = async (showLoader = true) => {
    if (showLoader) setIsLoading(true);

    try {
      const token = localStorage.getItem('auth_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };

      // Calculate date range
      const endDate = new Date();
      const startDate = new Date();
      switch (timeRange) {
        case '1d':
          startDate.setDate(endDate.getDate() - 1);
          break;
        case '7d':
          startDate.setDate(endDate.getDate() - 7);
          break;
        case '30d':
          startDate.setDate(endDate.getDate() - 30);
          break;
        case '90d':
          startDate.setDate(endDate.getDate() - 90);
          break;
        default:
          startDate.setDate(endDate.getDate() - 7);
      }

      // Fetch dashboard summary
      const summaryResponse = await fetch(`${API_BASE_URL}/api/monitoring/dashboard-summary`, {
        headers
      });

      if (summaryResponse.ok) {
        const summary = await summaryResponse.json();
        setDashboardSummary(summary);
      }

      // Fetch VAPI call metrics
      const vapiParams = new URLSearchParams({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        limit: '100'
      });

      if (selectedAutomation !== 'all') {
        vapiParams.set('automation_id', selectedAutomation);
      }

      if (selectedCampaign !== 'all') {
        vapiParams.set('campaign_id', selectedCampaign);
      }

      const vapiResponse = await fetch(`${API_BASE_URL}/api/monitoring/vapi-calls?${vapiParams}`, {
        headers
      });

      if (vapiResponse.ok) {
        const metrics = await vapiResponse.json();
        setVapiCallMetrics(metrics);
      }

      // Fetch automation health
      const healthParams = new URLSearchParams();
      if (selectedAutomation !== 'all') {
        healthParams.set('automation_id', selectedAutomation);
      }
      if (selectedCampaign !== 'all') {
        healthParams.set('campaign_id', selectedCampaign);
      }

      const healthResponse = await fetch(`${API_BASE_URL}/api/monitoring/automation-health?${healthParams}`, {
        headers
      });

      if (healthResponse.ok) {
        const health = await healthResponse.json();
        setAutomationHealth(health);
      }

      // Fetch campaign performance
      const perfParams = new URLSearchParams({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
      });

      if (selectedCampaign !== 'all') {
        perfParams.set('campaign_id', selectedCampaign);
      }

      const perfResponse = await fetch(`${API_BASE_URL}/api/monitoring/campaign-performance?${perfParams}`, {
        headers
      });

      if (perfResponse.ok) {
        const performance = await perfResponse.json();
        setCampaignPerformance(performance);
      }

      // Fetch call logs
      const logParams = new URLSearchParams({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        page: '1',
        per_page: '100'
      });

      if (selectedAutomation !== 'all') {
        logParams.set('automation_id', selectedAutomation);
      }

      const logsResponse = await fetch(`${API_BASE_URL}/api/call-logs?${logParams}`, {
        headers
      });

      if (logsResponse.ok) {
        const logsData = await logsResponse.json();
        setCallLogs(logsData.data || []);
      }

      // Fetch tool call health analysis
      const toolParams = new URLSearchParams({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
      });

      if (selectedAutomation !== 'all') {
        toolParams.set('automation_id', selectedAutomation);
      }

      const toolResponse = await fetch(`${API_BASE_URL}/api/call-logs/tool-analysis?${toolParams}`, {
        headers
      });

      if (toolResponse.ok) {
        const toolData = await toolResponse.json();
        const enhancedToolHealth = (toolData.data || []).map((tool: any) => ({
          ...tool,
          status: tool.success_rate > 90 ? 'healthy' : tool.success_rate > 70 ? 'warning' : 'error',
          last_called: new Date().toISOString() // Would come from actual data
        }));
        setToolCallHealth(enhancedToolHealth);
      }

      // Fetch recent test results
      const testResponse = await fetch(`${API_BASE_URL}/api/vapi-testing/test-results?limit=50`, {
        headers
      });

      if (testResponse.ok) {
        const testData = await testResponse.json();
        setTestResults(testData.data || []);
      }

      setLastRefresh(new Date());

    } catch (error) {
      console.error('Error fetching monitoring data:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch monitoring data',
        variant: 'destructive'
      });
    } finally {
      if (showLoader) setIsLoading(false);
    }
  };

  // Auto-refresh data every 30 seconds
  useEffect(() => {
    fetchMonitoringData(true);
    const interval = setInterval(() => fetchMonitoringData(false), 30000);
    return () => clearInterval(interval);
  }, [timeRange, selectedAutomation, selectedCampaign]);

  const getHealthStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSentimentColor = (score?: number) => {
    if (!score) return 'bg-gray-200';
    if (score > 0.6) return 'bg-green-500';
    if (score > 0.3) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getToolHealthIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const runVAPITest = async (assistantId: string, testType: string = 'health') => {
    if (!assistantId) {
      toast({
        title: 'Error',
        description: 'No assistant ID selected for testing',
        variant: 'destructive'
      });
      return;
    }

    setIsRunningTest(true);

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/api/vapi-testing/test-assistant`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          assistant_id: assistantId,
          test_type: testType,
          timeout: 60
        })
      });

      if (response.ok) {
        const result = await response.json();

        // Refresh test results
        const testResponse = await fetch(`${API_BASE_URL}/api/vapi-testing/test-results?limit=50`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (testResponse.ok) {
          const testData = await testResponse.json();
          setTestResults(testData.data || []);
        }

        toast({
          title: 'Test Completed',
          description: `${testType} test ${result.data.success ? 'passed' : 'failed'}: ${result.message}`,
          variant: result.data.success ? 'default' : 'destructive'
        });
      } else {
        throw new Error('Test request failed');
      }
    } catch (error) {
      toast({
        title: 'Test Failed',
        description: 'Failed to run VAPI test',
        variant: 'destructive'
      });
    } finally {
      setIsRunningTest(false);
    }
  };

  const exportData = async (format: 'csv' | 'json' | 'xlsx') => {
    try {
      const exportData = {
        summary: dashboardSummary,
        vapi_metrics: vapiCallMetrics,
        automation_health: automationHealth,
        campaign_performance: campaignPerformance,
        filters: {
          timeRange,
          selectedAutomation,
          selectedCampaign
        },
        exported_at: new Date().toISOString()
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json'
      });

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `automation-monitoring-${timeRange}-${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: 'Export Successful',
        description: `Data exported as ${format.toUpperCase()}`,
      });
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: 'Failed to export monitoring data',
        variant: 'destructive'
      });
    }
  };

  if (isLoading && !dashboardSummary) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading monitoring data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Automation Monitoring</h2>
          <p className="text-gray-600">
            Real-time monitoring of automation health and performance
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchMonitoringData(true)}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Select onValueChange={(value) => exportData(value as any)}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Export" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="json">JSON</SelectItem>
              <SelectItem value="csv">CSV</SelectItem>
              <SelectItem value="xlsx">Excel</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Summary Cards */}
      {dashboardSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
              <Phone className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {dashboardSummary.vapi_metrics.total_calls.toLocaleString()}
              </div>
              <p className="text-xs text-gray-600">
                Avg duration: {Math.round(dashboardSummary.vapi_metrics.avg_call_duration)}s
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
              <DollarSign className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${dashboardSummary.vapi_metrics.total_cost.toFixed(2)}
              </div>
              <p className="text-xs text-gray-600">
                Avg per call: ${(dashboardSummary.vapi_metrics.total_cost / Math.max(dashboardSummary.vapi_metrics.total_calls, 1)).toFixed(2)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Automation Health</CardTitle>
              <Heart className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {dashboardSummary.automation_health.health_percentage}%
              </div>
              <p className="text-xs text-gray-600">
                {dashboardSummary.automation_health.healthy_automations} of {dashboardSummary.automation_health.total_automations} healthy
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Conversions</CardTitle>
              <TrendingUp className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {dashboardSummary.campaign_performance.total_conversions.toLocaleString()}
              </div>
              <p className="text-xs text-gray-600">
                Avg success rate: {dashboardSummary.campaign_performance.avg_success_rate.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <Select value={selectedAutomation} onValueChange={setSelectedAutomation}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Select Automation" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Automations</SelectItem>
            {automationHealth.map((health) => (
              <SelectItem key={health.automation_id} value={health.automation_id}>
                {health.automation_id}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedCampaign} onValueChange={setSelectedCampaign}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Select Campaign" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Campaigns</SelectItem>
            {campaignPerformance.map((campaign) => (
              <SelectItem key={campaign.campaign_id} value={campaign.campaign_id}>
                {campaign.campaign_id}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Detailed Analytics Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="vapi-calls">VAPI Calls</TabsTrigger>
          <TabsTrigger value="automation-health">Health</TabsTrigger>
          <TabsTrigger value="campaign-performance">Campaigns</TabsTrigger>
          <TabsTrigger value="call-logs">Call Logs</TabsTrigger>
          <TabsTrigger value="tool-health">Tool Health</TabsTrigger>
          <TabsTrigger value="vapi-testing">Testing</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Automation Health Overview */}
            <Card>
              <CardHeader>
                <CardTitle>Automation Health Status</CardTitle>
                <CardDescription>
                  Current health status of all automations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {automationHealth.slice(0, 5).map((health) => (
                    <div key={health.id} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {getHealthStatusIcon(health.status)}
                        <span className="text-sm font-medium">
                          {health.automation_id}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant={health.status === 'healthy' ? 'default' : 'destructive'}>
                          {health.success_rate.toFixed(1)}%
                        </Badge>
                        <span className="text-xs text-gray-500">
                          {health.error_count} errors
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recent VAPI Calls */}
            <Card>
              <CardHeader>
                <CardTitle>Recent VAPI Calls</CardTitle>
                <CardDescription>
                  Latest voice API interactions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {vapiCallMetrics.slice(0, 5).map((call) => (
                    <div key={call.id} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Phone className="h-4 w-4" />
                        <div>
                          <div className="text-sm font-medium">
                            {call.automation_id}
                          </div>
                          <div className="text-xs text-gray-500">
                            {Math.round(call.call_duration)}s duration
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {call.sentiment_score && (
                          <div className="flex items-center space-x-1">
                            <div
                              className={`h-2 w-8 rounded ${getSentimentColor(call.sentiment_score)}`}
                            />
                            <span className="text-xs">
                              {(call.sentiment_score * 100).toFixed(0)}%
                            </span>
                          </div>
                        )}
                        <Badge variant={call.call_status === 'completed' ? 'default' : 'secondary'}>
                          {call.call_status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="vapi-calls" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>VAPI Call Analytics</CardTitle>
              <CardDescription>
                Detailed analysis of voice API interactions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {vapiCallMetrics.length === 0 ? (
                  <p className="text-center text-gray-500">No VAPI call data available</p>
                ) : (
                  <div className="space-y-2">
                    {vapiCallMetrics.map((call) => (
                      <div key={call.id} className="border rounded p-3">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h4 className="font-medium">{call.automation_id}</h4>
                            {call.campaign_id && (
                              <p className="text-sm text-gray-500">Campaign: {call.campaign_id}</p>
                            )}
                          </div>
                          <Badge variant={call.call_status === 'completed' ? 'default' : 'secondary'}>
                            {call.call_status}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Duration:</span>
                            <div className="font-medium">{Math.round(call.call_duration)}s</div>
                          </div>
                          {call.cost && (
                            <div>
                              <span className="text-gray-500">Cost:</span>
                              <div className="font-medium">${call.cost.toFixed(3)}</div>
                            </div>
                          )}
                          {call.sentiment_score && (
                            <div>
                              <span className="text-gray-500">Sentiment:</span>
                              <div className="font-medium">{(call.sentiment_score * 100).toFixed(0)}%</div>
                            </div>
                          )}
                          <div>
                            <span className="text-gray-500">Time:</span>
                            <div className="font-medium">
                              {new Date(call.created_at).toLocaleTimeString()}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="automation-health" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Automation Health Details</CardTitle>
              <CardDescription>
                Comprehensive health monitoring for all automations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {automationHealth.length === 0 ? (
                  <p className="text-center text-gray-500">No automation health data available</p>
                ) : (
                  <div className="space-y-3">
                    {automationHealth.map((health) => (
                      <div key={health.id} className="border rounded p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex items-center space-x-2">
                            {getHealthStatusIcon(health.status)}
                            <h4 className="font-medium">{health.automation_id}</h4>
                          </div>
                          <Badge variant={health.status === 'healthy' ? 'default' : 'destructive'}>
                            {health.status}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Success Rate:</span>
                            <div className="flex items-center space-x-2">
                              <Progress value={health.success_rate} className="h-2 w-16" />
                              <span className="font-medium">{health.success_rate.toFixed(1)}%</span>
                            </div>
                          </div>
                          <div>
                            <span className="text-gray-500">Error Count:</span>
                            <div className="font-medium text-red-600">{health.error_count}</div>
                          </div>
                          <div>
                            <span className="text-gray-500">Last Execution:</span>
                            <div className="font-medium">
                              {new Date(health.last_execution).toLocaleString()}
                            </div>
                          </div>
                          {health.campaign_id && (
                            <div>
                              <span className="text-gray-500">Campaign:</span>
                              <div className="font-medium">{health.campaign_id}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="campaign-performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Campaign Performance Metrics</CardTitle>
              <CardDescription>
                Detailed performance analysis by campaign
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {campaignPerformance.length === 0 ? (
                  <p className="text-center text-gray-500">No campaign performance data available</p>
                ) : (
                  <div className="space-y-3">
                    {campaignPerformance.map((campaign) => (
                      <div key={campaign.id} className="border rounded p-4">
                        <div className="flex justify-between items-start mb-3">
                          <h4 className="font-medium">{campaign.campaign_id}</h4>
                          <Badge variant="default">
                            {campaign.success_rate.toFixed(1)}% success
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Total Calls:</span>
                            <div className="font-medium">{campaign.total_calls}</div>
                          </div>
                          <div>
                            <span className="text-gray-500">Successful:</span>
                            <div className="font-medium text-green-600">{campaign.successful_calls}</div>
                          </div>
                          <div>
                            <span className="text-gray-500">Failed:</span>
                            <div className="font-medium text-red-600">{campaign.failed_calls}</div>
                          </div>
                          <div>
                            <span className="text-gray-500">Total Cost:</span>
                            <div className="font-medium">${campaign.total_cost.toFixed(2)}</div>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm mt-3">
                          <div>
                            <span className="text-gray-500">Avg Duration:</span>
                            <div className="font-medium">{Math.round(campaign.avg_call_duration)}s</div>
                          </div>
                          <div>
                            <span className="text-gray-500">Conversions:</span>
                            <div className="font-medium">{campaign.total_conversions}</div>
                          </div>
                          <div>
                            <span className="text-gray-500">Conversion Rate:</span>
                            <div className="font-medium">{campaign.conversion_rate.toFixed(1)}%</div>
                          </div>
                        </div>
                        {campaign.avg_sentiment_score && (
                          <div className="mt-3">
                            <span className="text-gray-500 text-sm">Avg Sentiment:</span>
                            <div className="flex items-center space-x-2 mt-1">
                              <div className={`h-2 w-24 rounded ${getSentimentColor(campaign.avg_sentiment_score)}`} />
                              <span className="text-sm font-medium">
                                {(campaign.avg_sentiment_score * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="call-logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Call Logs
              </CardTitle>
              <CardDescription>
                Detailed logs of all VAPI calls with transcripts and analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {callLogs.length === 0 ? (
                  <p className="text-center text-gray-500">No call logs available</p>
                ) : (
                  <div className="space-y-3">
                    {callLogs.slice(0, 20).map((log) => (
                      <div key={log.id} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h4 className="font-medium flex items-center gap-2">
                              <Phone className="h-4 w-4" />
                              {log.call_id}
                            </h4>
                            <p className="text-sm text-gray-500">
                              {log.phone_number} • {new Date(log.created_at).toLocaleString()}
                            </p>
                          </div>
                          <Badge variant={log.call_status === 'completed' ? 'default' : 'destructive'}>
                            {log.call_status}
                          </Badge>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-3">
                          <div>
                            <span className="text-gray-500">Duration:</span>
                            <div className="font-medium">
                              {log.call_duration ? `${Math.round(log.call_duration)}s` : 'N/A'}
                            </div>
                          </div>
                          <div>
                            <span className="text-gray-500">Cost:</span>
                            <div className="font-medium">
                              {log.cost ? `$${log.cost.toFixed(3)}` : 'N/A'}
                            </div>
                          </div>
                          <div>
                            <span className="text-gray-500">Tools Used:</span>
                            <div className="font-medium">
                              {log.tool_calls ? log.tool_calls.length : 0}
                            </div>
                          </div>
                          {log.sentiment_score && (
                            <div>
                              <span className="text-gray-500">Sentiment:</span>
                              <div className="flex items-center gap-2">
                                <div className={`h-2 w-8 rounded ${getSentimentColor(log.sentiment_score)}`} />
                                <span className="text-sm">{(log.sentiment_score * 100).toFixed(0)}%</span>
                              </div>
                            </div>
                          )}
                        </div>

                        {log.summary && (
                          <div className="mb-3">
                            <span className="text-gray-500 text-sm">Summary:</span>
                            <p className="text-sm mt-1">{log.summary}</p>
                          </div>
                        )}

                        {log.tool_calls && log.tool_calls.length > 0 && (
                          <div>
                            <span className="text-gray-500 text-sm">Tool Calls:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {log.tool_calls.map((tool, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {tool.tool_name || `Tool ${index + 1}`}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tool-health" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Tool Call Health Monitoring
              </CardTitle>
              <CardDescription>
                Performance and reliability metrics for VAPI tool calls
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {toolCallHealth.length === 0 ? (
                  <p className="text-center text-gray-500">No tool health data available</p>
                ) : (
                  <div className="space-y-3">
                    {toolCallHealth.map((tool, index) => (
                      <div key={index} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex items-center gap-2">
                            {getToolHealthIcon(tool.status)}
                            <h4 className="font-medium">{tool.tool_name}</h4>
                          </div>
                          <Badge variant={tool.status === 'healthy' ? 'default' :
                                        tool.status === 'warning' ? 'secondary' : 'destructive'}>
                            {tool.status}
                          </Badge>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Total Calls:</span>
                            <div className="font-medium">{tool.total_calls}</div>
                          </div>
                          <div>
                            <span className="text-gray-500">Success Rate:</span>
                            <div className="flex items-center gap-2">
                              <Progress value={tool.success_rate} className="h-2 w-16" />
                              <span className="font-medium">{tool.success_rate.toFixed(1)}%</span>
                            </div>
                          </div>
                          <div>
                            <span className="text-gray-500">Error Rate:</span>
                            <div className="font-medium text-red-600">{tool.error_rate.toFixed(1)}%</div>
                          </div>
                          {tool.avg_execution_time && (
                            <div>
                              <span className="text-gray-500">Avg Time:</span>
                              <div className="font-medium">{tool.avg_execution_time.toFixed(2)}s</div>
                            </div>
                          )}
                        </div>

                        {tool.common_errors.length > 0 && (
                          <div className="mt-3">
                            <span className="text-gray-500 text-sm">Common Errors:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {tool.common_errors.slice(0, 3).map((error, errorIndex) => (
                                <Badge key={errorIndex} variant="destructive" className="text-xs">
                                  {error.length > 30 ? `${error.substring(0, 30)}...` : error}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="vapi-testing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TestTube className="h-5 w-5" />
                VAPI Testing & Monitoring
              </CardTitle>
              <CardDescription>
                Run tests on VAPI assistants and monitor test results
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Test Controls */}
                <div className="flex gap-2 p-3 bg-gray-50 rounded-lg">
                  <Button
                    onClick={() => runVAPITest(selectedAutomation !== 'all' ? selectedAutomation : '', 'health')}
                    disabled={isRunningTest || selectedAutomation === 'all'}
                    size="sm"
                  >
                    {isRunningTest ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Play className="h-4 w-4 mr-2" />
                    )}
                    Health Test
                  </Button>
                  <Button
                    onClick={() => runVAPITest(selectedAutomation !== 'all' ? selectedAutomation : '', 'webhook')}
                    disabled={isRunningTest || selectedAutomation === 'all'}
                    variant="outline"
                    size="sm"
                  >
                    <Zap className="h-4 w-4 mr-2" />
                    Webhook Test
                  </Button>
                  {selectedAutomation === 'all' && (
                    <div className="text-sm text-gray-500 flex items-center">
                      <AlertCircle className="h-4 w-4 mr-1" />
                      Select an automation to run tests
                    </div>
                  )}
                </div>

                {/* Test Results */}
                <div className="space-y-3">
                  <h4 className="font-medium">Recent Test Results</h4>
                  {testResults.length === 0 ? (
                    <p className="text-center text-gray-500">No test results available</p>
                  ) : (
                    <div className="space-y-2">
                      {testResults.slice(0, 10).map((test) => (
                        <div key={test.test_id} className="border rounded p-3">
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex items-center gap-2">
                              {test.success ? (
                                <CheckCircle className="h-4 w-4 text-green-500" />
                              ) : (
                                <XCircle className="h-4 w-4 text-red-500" />
                              )}
                              <span className="font-medium">{test.test_type} Test</span>
                            </div>
                            <div className="text-right">
                              <Badge variant={test.success ? 'default' : 'destructive'}>
                                {test.success ? 'Passed' : 'Failed'}
                              </Badge>
                              <div className="text-xs text-gray-500 mt-1">
                                {test.duration.toFixed(2)}s
                              </div>
                            </div>
                          </div>

                          <div className="text-sm text-gray-600 mb-2">
                            {new Date(test.timestamp).toLocaleString()}
                          </div>

                          {test.error && (
                            <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                              Error: {test.error}
                            </div>
                          )}

                          {test.details && Object.keys(test.details).length > 0 && (
                            <div className="text-xs text-gray-500 mt-2">
                              <details>
                                <summary className="cursor-pointer">View Details</summary>
                                <pre className="mt-1 bg-gray-100 p-2 rounded text-xs overflow-auto">
                                  {JSON.stringify(test.details, null, 2)}
                                </pre>
                              </details>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Footer */}
      <div className="text-center text-sm text-gray-500">
        Last updated: {lastRefresh.toLocaleString()} | Auto-refresh every 30 seconds
      </div>
    </div>
  );
};

export default AutomationMonitoringDashboard;