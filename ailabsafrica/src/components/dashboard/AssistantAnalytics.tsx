import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend,
  AreaChart,
  Area
} from 'recharts';
import { 
  TrendingUp, 
  TrendingDown, 
  Phone, 
  Clock, 
  Calendar,
  Download,
  RefreshCw,
  BarChart3,
  PieChart as PieChartIcon,
  Users,
  Activity,
  Zap,
  Target
} from 'lucide-react';

interface VoiceAgent {
  id: string;
  assistant_name: string;
  assistant_type: string;
  demo_url: string;
  created_at: string;
  status: string;
  assistant_id: string;
  voice_id?: string;
  total_calls?: number;
  total_duration?: number;
  last_call_at?: string;
  success_rate?: number;
  average_duration?: number;
}

interface CallMetrics {
  agent_id: string;
  agent_name: string;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  total_duration: number;
  average_duration: number;
  success_rate: number;
  last_call_at?: string;
}

interface AnalyticsData {
  totalAgents: number;
  activeAgents: number;
  totalCalls: number;
  totalDuration: number;
  averageSuccessRate: number;
  averageCallDuration: number;
  monthlyCallTrends: Array<{
    month: string;
    calls: number;
    duration: number;
    success_rate: number;
  }>;
  agentPerformance: CallMetrics[];
  callStatusDistribution: Array<{
    status: string;
    count: number;
    percentage: number;
  }>;
  topPerformingAgents: CallMetrics[];
  recentActivity: Array<{
    agent_name: string;
    call_count: number;
    duration: number;
    success_rate: number;
    last_call: string;
  }>;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const AssistantAnalytics: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>('30d');
  const [chartType, setChartType] = useState<'bar' | 'line' | 'area'>('bar');

  const loadAnalytics = async () => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      // Calculate date range
      const now = new Date();
      const daysAgo = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : timeRange === '90d' ? 90 : 365;
      const startDate = new Date(now.getTime() - (daysAgo * 24 * 60 * 60 * 1000));

      // Fetch voice agents
      const { data: agents, error: agentsError } = await supabase.functions.invoke("list-custom-demos");
      
      if (agentsError) throw agentsError;

      const agentsData = (agents?.demos as VoiceAgent[]) || [];
      
      // Simulate call metrics (in a real implementation, this would come from Vapi API)
      const callMetrics: CallMetrics[] = agentsData.map(agent => {
        const totalCalls = Math.floor(Math.random() * 100) + 10; // Simulated data
        const successfulCalls = Math.floor(totalCalls * (0.7 + Math.random() * 0.3)); // 70-100% success rate
        const failedCalls = totalCalls - successfulCalls;
        const totalDuration = Math.floor(Math.random() * 3600) + 300; // 5-65 minutes
        const averageDuration = totalDuration / totalCalls;
        const successRate = (successfulCalls / totalCalls) * 100;
        
        return {
          agent_id: agent.id,
          agent_name: agent.assistant_name,
          total_calls: totalCalls,
          successful_calls: successfulCalls,
          failed_calls: failedCalls,
          total_duration: totalDuration,
          average_duration: averageDuration,
          success_rate: successRate,
          last_call_at: new Date(Date.now() - Math.random() * daysAgo * 24 * 60 * 60 * 1000).toISOString()
        };
      });

      // Calculate analytics
      const totalAgents = agentsData.length;
      const activeAgents = agentsData.filter(agent => agent.status === 'active').length;
      const totalCalls = callMetrics.reduce((sum, metric) => sum + metric.total_calls, 0);
      const totalDuration = callMetrics.reduce((sum, metric) => sum + metric.total_duration, 0);
      const averageSuccessRate = callMetrics.length > 0 
        ? callMetrics.reduce((sum, metric) => sum + metric.success_rate, 0) / callMetrics.length 
        : 0;
      const averageCallDuration = totalCalls > 0 ? totalDuration / totalCalls : 0;

      // Monthly trends (simulated)
      const monthlyCallTrends = [];
      for (let i = 0; i < 6; i++) {
        const date = new Date(now.getTime() - (i * 30 * 24 * 60 * 60 * 1000));
        const monthKey = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        const calls = Math.floor(Math.random() * 50) + 10;
        const duration = Math.floor(Math.random() * 1800) + 300;
        const success_rate = 70 + Math.random() * 30;
        
        monthlyCallTrends.unshift({
          month: monthKey,
          calls,
          duration,
          success_rate: Math.round(success_rate)
        });
      }

      // Call status distribution
      const totalSuccessful = callMetrics.reduce((sum, metric) => sum + metric.successful_calls, 0);
      const totalFailed = callMetrics.reduce((sum, metric) => sum + metric.failed_calls, 0);
      const callStatusDistribution = [
        { status: 'Successful', count: totalSuccessful, percentage: totalCalls > 0 ? (totalSuccessful / totalCalls) * 100 : 0 },
        { status: 'Failed', count: totalFailed, percentage: totalCalls > 0 ? (totalFailed / totalCalls) * 100 : 0 }
      ];

      // Top performing agents (by success rate)
      const topPerformingAgents = [...callMetrics]
        .sort((a, b) => b.success_rate - a.success_rate)
        .slice(0, 5);

      // Recent activity
      const recentActivity = callMetrics
        .filter(metric => metric.last_call_at)
        .sort((a, b) => new Date(b.last_call_at!).getTime() - new Date(a.last_call_at!).getTime())
        .slice(0, 10)
        .map(metric => ({
          agent_name: metric.agent_name,
          call_count: metric.total_calls,
          duration: metric.total_duration,
          success_rate: metric.success_rate,
          last_call: metric.last_call_at!
        }));

      setAnalyticsData({
        totalAgents,
        activeAgents,
        totalCalls,
        totalDuration,
        averageSuccessRate,
        averageCallDuration,
        monthlyCallTrends,
        agentPerformance: callMetrics,
        callStatusDistribution,
        topPerformingAgents,
        recentActivity
      });

    } catch (error: any) {
      console.error('Error loading analytics:', error);
      toast({
        title: "Error loading analytics",
        description: error.message || "Failed to load assistant analytics",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [user, timeRange]);

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const formatPercentage = (value: number) => {
    return Math.round(value);
  };

  const exportAnalytics = () => {
    if (!analyticsData) return;

    const csvContent = [
      'Assistant Analytics Report',
      `Generated: ${new Date().toLocaleDateString()}`,
      `Time Range: ${timeRange}`,
      '',
      'Summary',
      `Total Agents,${analyticsData.totalAgents}`,
      `Active Agents,${analyticsData.activeAgents}`,
      `Total Calls,${analyticsData.totalCalls}`,
      `Total Duration,${formatDuration(analyticsData.totalDuration)}`,
      `Average Success Rate,${formatPercentage(analyticsData.averageSuccessRate)}%`,
      `Average Call Duration,${formatDuration(analyticsData.averageCallDuration)}`,
      '',
      'Monthly Call Trends',
      'Month,Calls,Duration (seconds),Success Rate (%)',
      ...analyticsData.monthlyCallTrends.map(trend => 
        `${trend.month},${trend.calls},${trend.duration},${trend.success_rate}`
      ),
      '',
      'Agent Performance',
      'Agent Name,Total Calls,Successful Calls,Failed Calls,Total Duration,Average Duration,Success Rate (%)',
      ...analyticsData.agentPerformance.map(agent => 
        `${agent.agent_name},${agent.total_calls},${agent.successful_calls},${agent.failed_calls},${agent.total_duration},${Math.round(agent.average_duration)},${formatPercentage(agent.success_rate)}`
      ),
      '',
      'Call Status Distribution',
      'Status,Count,Percentage (%)',
      ...analyticsData.callStatusDistribution.map(status => 
        `${status.status},${status.count},${formatPercentage(status.percentage)}`
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `assistant-analytics-${timeRange}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);

    toast({
      title: "Analytics exported",
      description: "Assistant analytics data has been downloaded as CSV",
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner />
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="text-center p-8">
        <p className="text-muted-foreground">No analytics data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Assistant Analytics</h2>
          <p className="text-muted-foreground">
            Insights and performance metrics for your voice agents
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadAnalytics}
            disabled={isLoading}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={exportAnalytics}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Time Range Selector */}
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">Time Range:</span>
        {(['7d', '30d', '90d', '1y'] as const).map((range) => (
          <Button
            key={range}
            variant={timeRange === range ? "default" : "outline"}
            size="sm"
            onClick={() => setTimeRange(range)}
          >
            {range}
          </Button>
        ))}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.totalAgents}</div>
            <p className="text-xs text-muted-foreground">
              {analyticsData.activeAgents} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
            <Phone className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.totalCalls}</div>
            <p className="text-xs text-muted-foreground">
              {formatDuration(analyticsData.totalDuration)} total duration
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatPercentage(analyticsData.averageSuccessRate)}%</div>
            <p className="text-xs text-muted-foreground">
              average across all agents
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Call Duration</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatDuration(analyticsData.averageCallDuration)}</div>
            <p className="text-xs text-muted-foreground">
              per call
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Call Trends */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Call Trends
            </CardTitle>
            <CardDescription>
              Monthly call volume and success rates
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 mb-4">
              <Button
                variant={chartType === 'bar' ? "default" : "outline"}
                size="sm"
                onClick={() => setChartType('bar')}
              >
                <BarChart3 className="h-4 w-4 mr-2" />
                Bar
              </Button>
              <Button
                variant={chartType === 'line' ? "default" : "outline"}
                size="sm"
                onClick={() => setChartType('line')}
              >
                <TrendingUp className="h-4 w-4 mr-2" />
                Line
              </Button>
              <Button
                variant={chartType === 'area' ? "default" : "outline"}
                size="sm"
                onClick={() => setChartType('area')}
              >
                <Activity className="h-4 w-4 mr-2" />
                Area
              </Button>
            </div>
            
            <ResponsiveContainer width="100%" height={300}>
              {chartType === 'bar' ? (
                <BarChart data={analyticsData.monthlyCallTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value: any, name: string) => [
                      name === 'calls' ? value : name === 'duration' ? formatDuration(value) : `${value}%`,
                      name === 'calls' ? 'Calls' : name === 'duration' ? 'Duration' : 'Success Rate'
                    ]}
                  />
                  <Bar dataKey="calls" fill="#0088FE" name="Calls" />
                </BarChart>
              ) : chartType === 'line' ? (
                <LineChart data={analyticsData.monthlyCallTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value: any, name: string) => [
                      name === 'calls' ? value : name === 'duration' ? formatDuration(value) : `${value}%`,
                      name === 'calls' ? 'Calls' : name === 'duration' ? 'Duration' : 'Success Rate'
                    ]}
                  />
                  <Line type="monotone" dataKey="calls" stroke="#0088FE" strokeWidth={2} />
                  <Line type="monotone" dataKey="success_rate" stroke="#00C49F" strokeWidth={2} />
                </LineChart>
              ) : (
                <AreaChart data={analyticsData.monthlyCallTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value: any, name: string) => [
                      name === 'calls' ? value : name === 'duration' ? formatDuration(value) : `${value}%`,
                      name === 'calls' ? 'Calls' : name === 'duration' ? 'Duration' : 'Success Rate'
                    ]}
                  />
                  <Area type="monotone" dataKey="calls" stroke="#0088FE" fill="#0088FE" fillOpacity={0.3} />
                </AreaChart>
              )}
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Call Status Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChartIcon className="h-5 w-5" />
              Call Status
            </CardTitle>
            <CardDescription>
              Distribution of successful vs failed calls
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analyticsData.callStatusDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ status, percent }) => `${status} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {analyticsData.callStatusDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: any, name: string) => [value, 'Count']}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Top Performing Agents */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Top Performing Agents
          </CardTitle>
          <CardDescription>
            Agents with the highest success rates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {analyticsData.topPerformingAgents.map((agent, index) => (
              <div key={agent.agent_id} className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">{agent.agent_name}</p>
                  <p className="text-sm text-muted-foreground">
                    {agent.total_calls} calls
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-green-600">{formatPercentage(agent.success_rate)}%</p>
                  <p className="text-xs text-muted-foreground">
                    {formatDuration(agent.average_duration)} avg
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>
            Latest call activity by agent
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {analyticsData.recentActivity.map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="font-medium">{activity.agent_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {activity.call_count} calls • {formatDuration(activity.duration)} total
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold">{formatPercentage(activity.success_rate)}%</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(activity.last_call).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AssistantAnalytics;
