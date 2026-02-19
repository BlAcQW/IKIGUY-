import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Phone, 
  DollarSign, 
  Activity,
  Calendar,
  RefreshCw,
  Download,
  BarChart3,
  PieChart,
  LineChart,
  Target,
  Zap,
  Clock,
  Eye,
  MousePointer,
  UserCheck,
  Settings,
  Filter,
  Search
} from 'lucide-react';
import {
  LineChart as RechartsLineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface UsageMetrics {
  totalSessions: number;
  activeUsers: number;
  featureUsage: {
    demos: number;
    voiceAgents: number;
    payments: number;
    analytics: number;
  };
  userEngagement: {
    avgSessionDuration: number;
    pagesPerSession: number;
    bounceRate: number;
  };
  deviceBreakdown: {
    desktop: number;
    mobile: number;
    tablet: number;
  };
}

interface PerformanceMetrics {
  avgResponseTime: number;
  errorRate: number;
  uptime: number;
  apiCalls: {
    total: number;
    successful: number;
    failed: number;
  };
  pageLoadTimes: {
    dashboard: number;
    demos: number;
    voiceAgents: number;
    analytics: number;
  };
}

interface ConversionMetrics {
  demoViews: number;
  demoInteractions: number;
  demoConversions: number;
  conversionRate: number;
  conversionFunnel: {
    views: number;
    interactions: number;
    shares: number;
    embeds: number;
    conversions: number;
  };
  topConvertingDemos: Array<{
    demoId: string;
    demoName: string;
    views: number;
    conversions: number;
    conversionRate: number;
  }>;
}

interface CustomReport {
  id: string;
  name: string;
  description: string;
  metrics: string[];
  timeRange: string;
  createdAt: string;
  lastRun: string;
}

interface AdvancedAnalyticsData {
  usageMetrics: UsageMetrics;
  performanceMetrics: PerformanceMetrics;
  conversionMetrics: ConversionMetrics;
  timeSeriesData: Array<{
    date: string;
    sessions: number;
    users: number;
    conversions: number;
    responseTime: number;
  }>;
  customReports: CustomReport[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FF6B6B', '#4ECDC4'];

const AdvancedAnalytics: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [analyticsData, setAnalyticsData] = useState<AdvancedAnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>('30d');
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['sessions', 'users', 'conversions']);

  const loadAdvancedAnalytics = async () => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      // Calculate date range
      const now = new Date();
      const daysAgo = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : timeRange === '90d' ? 90 : 365;
      const startDate = new Date(now.getTime() - (daysAgo * 24 * 60 * 60 * 1000));

      // Fetch demo analytics
      const { data: demoAnalytics, error: demoError } = await supabase
        .from('demo_analytics')
        .select('*')
        .gte('started_at', startDate.toISOString());

      if (demoError) throw demoError;

      // Fetch demo sessions
      const { data: demoSessions, error: sessionError } = await supabase
        .from('demo_sessions')
        .select('*')
        .gte('started_at', startDate.toISOString());

      if (sessionError) throw sessionError;

      // Fetch custom demos
      const { data: demos, error: demosError } = await supabase
        .from('custom_demos')
        .select('*')
        .eq('user_id', user.id);

      if (demosError) throw demosError;

      // Calculate usage metrics
      const totalSessions = demoSessions?.length || 0;
      const uniqueUsers = new Set(demoSessions?.map(s => s.user_agent) || []).size;
      
      const usageMetrics: UsageMetrics = {
        totalSessions,
        activeUsers: uniqueUsers,
        featureUsage: {
          demos: demos?.length || 0,
          voiceAgents: demos?.filter(d => d.assistant_id).length || 0,
          payments: 0, // Would come from payment analytics
          analytics: 1 // This page
        },
        userEngagement: {
          avgSessionDuration: demoSessions?.reduce((sum, s) => sum + (s.duration || 0), 0) / totalSessions || 0,
          pagesPerSession: 2.5, // Simulated
          bounceRate: 35.2 // Simulated
        },
        deviceBreakdown: {
          desktop: 65,
          mobile: 30,
          tablet: 5
        }
      };

      // Calculate performance metrics (simulated)
      const performanceMetrics: PerformanceMetrics = {
        avgResponseTime: 245, // ms
        errorRate: 0.8, // %
        uptime: 99.9, // %
        apiCalls: {
          total: 1247,
          successful: 1238,
          failed: 9
        },
        pageLoadTimes: {
          dashboard: 1.2,
          demos: 0.8,
          voiceAgents: 1.5,
          analytics: 0.9
        }
      };

      // Calculate conversion metrics
      const totalViews = demoAnalytics?.reduce((sum, a) => sum + (a.views || 0), 0) || 0;
      const totalInteractions = demoAnalytics?.reduce((sum, a) => sum + (a.interactions || 0), 0) || 0;
      const totalConversions = demoAnalytics?.reduce((sum, a) => sum + (a.conversions || 0), 0) || 0;
      const conversionRate = totalViews > 0 ? (totalConversions / totalViews) * 100 : 0;

      const conversionMetrics: ConversionMetrics = {
        demoViews: totalViews,
        demoInteractions: totalInteractions,
        demoConversions: totalConversions,
        conversionRate,
        conversionFunnel: {
          views: totalViews,
          interactions: totalInteractions,
          shares: demoAnalytics?.reduce((sum, a) => sum + (a.shares || 0), 0) || 0,
          embeds: demoAnalytics?.reduce((sum, a) => sum + (a.embeds || 0), 0) || 0,
          conversions: totalConversions
        },
        topConvertingDemos: demos?.map(demo => {
          const demoAnalytics = demoAnalytics?.find(a => a.demo_id === demo.id);
          const views = demoAnalytics?.views || 0;
          const conversions = demoAnalytics?.conversions || 0;
          return {
            demoId: demo.id,
            demoName: demo.name,
            views,
            conversions,
            conversionRate: views > 0 ? (conversions / views) * 100 : 0
          };
        }).sort((a, b) => b.conversionRate - a.conversionRate).slice(0, 5) || []
      };

      // Generate time series data
      const timeSeriesData = [];
      for (let i = daysAgo - 1; i >= 0; i--) {
        const date = new Date(now.getTime() - (i * 24 * 60 * 60 * 1000));
        const daySessions = demoSessions?.filter(s => 
          new Date(s.started_at).toDateString() === date.toDateString()
        ).length || 0;
        const dayUsers = new Set(demoSessions?.filter(s => 
          new Date(s.started_at).toDateString() === date.toDateString()
        ).map(s => s.user_agent) || []).size;
        const dayConversions = demoAnalytics?.filter(a => 
          new Date(a.started_at).toDateString() === date.toDateString()
        ).reduce((sum, a) => sum + (a.conversions || 0), 0) || 0;

        timeSeriesData.push({
          date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          sessions: daySessions,
          users: dayUsers,
          conversions: dayConversions,
          responseTime: 200 + Math.random() * 100
        });
      }

      // Mock custom reports
      const customReports: CustomReport[] = [
        {
          id: '1',
          name: 'Weekly Performance Report',
          description: 'Comprehensive weekly performance metrics',
          metrics: ['sessions', 'users', 'conversions', 'responseTime'],
          timeRange: '7d',
          createdAt: new Date().toISOString(),
          lastRun: new Date().toISOString()
        },
        {
          id: '2',
          name: 'Demo Conversion Analysis',
          description: 'Detailed demo conversion tracking',
          metrics: ['demoViews', 'demoInteractions', 'conversionRate'],
          timeRange: '30d',
          createdAt: new Date().toISOString(),
          lastRun: new Date().toISOString()
        }
      ];

      setAnalyticsData({
        usageMetrics,
        performanceMetrics,
        conversionMetrics,
        timeSeriesData,
        customReports
      });

    } catch (error: any) {
      console.error('Error loading advanced analytics:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to load advanced analytics",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAdvancedAnalytics();
  }, [timeRange, user]);

  const exportReport = async (reportType: string) => {
    try {
      const { data, error } = await supabase.functions.invoke('export-analytics', {
        body: {
          reportType,
          timeRange,
          userId: user?.id
        }
      });

      if (error) throw error;

      // Create and download CSV
      const csvContent = data.csvContent;
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportType}_${timeRange}_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      toast({
        title: "Success",
        description: `${reportType} report exported successfully`,
      });
    } catch (error: any) {
      console.error('Error exporting report:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to export report",
        variant: "destructive"
      });
    }
  };

  const createCustomReport = async () => {
    // This would open a dialog to create a custom report
    toast({
      title: "Coming Soon",
      description: "Custom report creation will be available in the next update",
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No analytics data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Advanced Analytics</h2>
          <p className="text-muted-foreground">
            Comprehensive insights into usage, performance, and conversions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={timeRange} onValueChange={(value: any) => setTimeRange(value)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="1y">Last year</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={loadAdvancedAnalytics} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="usage">Usage Analytics</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="conversions">Conversions</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Key Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Sessions</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analyticsData.usageMetrics.totalSessions.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">
                  +12% from last period
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analyticsData.usageMetrics.activeUsers.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">
                  +8% from last period
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analyticsData.conversionMetrics.conversionRate.toFixed(1)}%</div>
                <p className="text-xs text-muted-foreground">
                  +2.1% from last period
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analyticsData.performanceMetrics.avgResponseTime}ms</div>
                <p className="text-xs text-muted-foreground">
                  -15ms from last period
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Time Series Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Trends</CardTitle>
              <CardDescription>
                Key metrics over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={analyticsData.timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="sessions" stroke="#0088FE" strokeWidth={2} />
                  <Line type="monotone" dataKey="users" stroke="#00C49F" strokeWidth={2} />
                  <Line type="monotone" dataKey="conversions" stroke="#FFBB28" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Conversion Funnel */}
          <Card>
            <CardHeader>
              <CardTitle>Conversion Funnel</CardTitle>
              <CardDescription>
                User journey from demo views to conversions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between space-x-4">
                {Object.entries(analyticsData.conversionMetrics.conversionFunnel).map(([key, value], index) => (
                  <div key={key} className="flex-1 text-center">
                    <div className="text-2xl font-bold">{value.toLocaleString()}</div>
                    <div className="text-sm text-muted-foreground capitalize">{key}</div>
                    {index < Object.keys(analyticsData.conversionMetrics.conversionFunnel).length - 1 && (
                      <div className="text-muted-foreground mt-2">↓</div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Usage Analytics Tab */}
        <TabsContent value="usage" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Feature Usage */}
            <Card>
              <CardHeader>
                <CardTitle>Feature Usage</CardTitle>
                <CardDescription>How users interact with different features</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Object.entries(analyticsData.usageMetrics.featureUsage).map(([key, value]) => ({
                        name: key.charAt(0).toUpperCase() + key.slice(1),
                        value
                      }))}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {Object.entries(analyticsData.usageMetrics.featureUsage).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Device Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Device Breakdown</CardTitle>
                <CardDescription>User devices and platforms</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={Object.entries(analyticsData.usageMetrics.deviceBreakdown).map(([key, value]) => ({
                    device: key.charAt(0).toUpperCase() + key.slice(1),
                    percentage: value
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="device" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="percentage" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* User Engagement */}
          <Card>
            <CardHeader>
              <CardTitle>User Engagement Metrics</CardTitle>
              <CardDescription>Detailed engagement analytics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="text-center">
                  <div className="text-3xl font-bold">{analyticsData.usageMetrics.userEngagement.avgSessionDuration.toFixed(1)}s</div>
                  <div className="text-sm text-muted-foreground">Avg Session Duration</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold">{analyticsData.usageMetrics.userEngagement.pagesPerSession}</div>
                  <div className="text-sm text-muted-foreground">Pages per Session</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold">{analyticsData.usageMetrics.userEngagement.bounceRate}%</div>
                  <div className="text-sm text-muted-foreground">Bounce Rate</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* API Performance */}
            <Card>
              <CardHeader>
                <CardTitle>API Performance</CardTitle>
                <CardDescription>API call statistics and error rates</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total API Calls</span>
                    <span className="font-bold">{analyticsData.performanceMetrics.apiCalls.total.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Successful</span>
                    <span className="font-bold text-green-600">{analyticsData.performanceMetrics.apiCalls.successful.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Failed</span>
                    <span className="font-bold text-red-600">{analyticsData.performanceMetrics.apiCalls.failed.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Error Rate</span>
                    <span className="font-bold">{analyticsData.performanceMetrics.errorRate}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Page Load Times */}
            <Card>
              <CardHeader>
                <CardTitle>Page Load Times</CardTitle>
                <CardDescription>Average load times for key pages</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={Object.entries(analyticsData.performanceMetrics.pageLoadTimes).map(([page, time]) => ({
                    page: page.charAt(0).toUpperCase() + page.slice(1),
                    time
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="page" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="time" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* System Health */}
          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
              <CardDescription>Overall system performance metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="text-center">
                  <div className="text-3xl font-bold">{analyticsData.performanceMetrics.uptime}%</div>
                  <div className="text-sm text-muted-foreground">Uptime</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold">{analyticsData.performanceMetrics.avgResponseTime}ms</div>
                  <div className="text-sm text-muted-foreground">Avg Response Time</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold">{analyticsData.performanceMetrics.errorRate}%</div>
                  <div className="text-sm text-muted-foreground">Error Rate</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Conversions Tab */}
        <TabsContent value="conversions" className="space-y-6">
          {/* Top Converting Demos */}
          <Card>
            <CardHeader>
              <CardTitle>Top Converting Demos</CardTitle>
              <CardDescription>Demos with the highest conversion rates</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analyticsData.conversionMetrics.topConvertingDemos.map((demo, index) => (
                  <div key={demo.demoId} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium">{demo.demoName}</div>
                        <div className="text-sm text-muted-foreground">
                          {demo.views} views, {demo.conversions} conversions
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold">{demo.conversionRate.toFixed(1)}%</div>
                      <div className="text-sm text-muted-foreground">Conversion Rate</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Conversion Trends */}
          <Card>
            <CardHeader>
              <CardTitle>Conversion Trends</CardTitle>
              <CardDescription>Conversion rate over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={analyticsData.timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="conversions" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Export and Custom Reports */}
      <Card>
        <CardHeader>
          <CardTitle>Reports & Export</CardTitle>
          <CardDescription>Generate and export custom reports</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <h4 className="font-medium">Quick Export</h4>
              <div className="flex gap-2">
                <Button onClick={() => exportReport('usage')} variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Usage Report
                </Button>
                <Button onClick={() => exportReport('performance')} variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Performance Report
                </Button>
                <Button onClick={() => exportReport('conversions')} variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Conversion Report
                </Button>
              </div>
            </div>
            <Button onClick={createCustomReport} className="ml-4">
              <Settings className="h-4 w-4 mr-2" />
              Create Custom Report
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdvancedAnalytics;

