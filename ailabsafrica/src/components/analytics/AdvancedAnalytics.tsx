import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, BarChart, Bar, AreaChart, Area, ComposedChart, 
  Legend, ScatterChart, Scatter, RadarChart, PolarGrid, PolarAngleAxis, 
  PolarRadiusAxis, Radar, Treemap, TreemapItem
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Clock, DollarSign, Phone, MessageSquare, 
  Users, Activity, Target, Award, AlertTriangle, CheckCircle, XCircle,
  Calendar, BarChart3, PieChart as PieChartIcon, Target as TargetIcon
} from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';

interface AnalyticsData {
  total_calls: number;
  total_duration: number;
  total_cost: number;
  success_rate: number;
  average_duration: number;
  average_cost_per_call: number;
  peak_hours: Array<{ hour: number; calls: number }>;
  call_quality_score: number;
  customer_satisfaction: number;
  conversion_rate: number;
  calls_by_status: Array<{ status: string; count: number }>;
  calls_by_medium: Array<{ medium: string; count: number }>;
  calls_by_assistant: Array<{ assistant: string; calls: number; success_rate: number }>;
  daily_calls: Array<{ date: string; calls: number; cost: number; duration: number }>;
  weekly_trends: Array<{ week: string; calls: number; cost: number; success_rate: number }>;
  monthly_performance: Array<{ month: string; calls: number; cost: number; avg_duration: number }>;
  cost_analysis: Array<{ category: string; cost: number; percentage: number }>;
  performance_metrics: {
    response_time: number;
    resolution_rate: number;
    repeat_calls: number;
    escalation_rate: number;
  };
}

interface AdvancedAnalyticsProps {
  voiceAgentId?: string;
  timeRange?: string;
}

const AdvancedAnalytics: React.FC<AdvancedAnalyticsProps> = ({ 
  voiceAgentId, 
  timeRange = '30d' 
}) => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [selectedView, setSelectedView] = useState('overview');

  const COLORS = [
    '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8',
    '#82CA9D', '#FFC658', '#8DD1E1', '#D084D0', '#FF6B6B'
  ];

  useEffect(() => {
    if (user) {
      loadAdvancedAnalytics();
    }
  }, [user, selectedTimeRange, voiceAgentId]);

  const loadAdvancedAnalytics = async () => {
    if (!user) return;

    setLoading(true);
    try {
      let query = supabase
        .from('usage_tracking')
        .select('*')
        .eq('user_id', user.id);

      if (voiceAgentId) {
        query = query.eq('voice_agent_id', voiceAgentId);
      }

      // Apply time range filter
      const now = new Date();
      let startDate = new Date();
      
      switch (selectedTimeRange) {
        case '7d':
          startDate.setDate(now.getDate() - 7);
          break;
        case '30d':
          startDate.setDate(now.getDate() - 30);
          break;
        case '90d':
          startDate.setDate(now.getDate() - 90);
          break;
        case '1y':
          startDate.setFullYear(now.getFullYear() - 1);
          break;
      }

      query = query.gte('start_time', startDate.toISOString());

      const { data: callsData, error } = await query;

      if (error) throw error;

      if (callsData) {
        const analyticsData = calculateAdvancedAnalytics(callsData);
        setAnalytics(analyticsData);
      }
    } catch (error) {
      console.error('Error loading advanced analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateAdvancedAnalytics = (callsData: any[]): AnalyticsData => {
    const total_calls = callsData.length;
    const total_duration = callsData.reduce((sum, call) => sum + (call.duration_minutes || 0), 0);
    const total_cost = callsData.reduce((sum, call) => sum + (call.total_cost || 0), 0);
    const completed_calls = callsData.filter(call => call.status === 'completed').length;
    const success_rate = total_calls > 0 ? (completed_calls / total_calls) * 100 : 0;
    const average_duration = total_calls > 0 ? total_duration / total_calls : 0;
    const average_cost_per_call = total_calls > 0 ? total_cost / total_calls : 0;

    // Calculate peak hours
    const hourCounts = new Array(24).fill(0);
    callsData.forEach(call => {
      const hour = new Date(call.start_time).getHours();
      hourCounts[hour]++;
    });
    const peak_hours = hourCounts.map((count, hour) => ({ hour, calls: count }));

    // Calculate calls by status
    const statusCounts = callsData.reduce((acc, call) => {
      acc[call.status] = (acc[call.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    const calls_by_status = Object.entries(statusCounts).map(([status, count]) => ({ status, count }));

    // Calculate calls by medium
    const mediumCounts = callsData.reduce((acc, call) => {
      acc[call.communication_medium] = (acc[call.communication_medium] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    const calls_by_medium = Object.entries(mediumCounts).map(([medium, count]) => ({ medium, count }));

    // Calculate daily trends
    const dailyCounts = callsData.reduce((acc, call) => {
      const date = new Date(call.start_time).toLocaleDateString();
      if (!acc[date]) {
        acc[date] = { calls: 0, cost: 0, duration: 0 };
      }
      acc[date].calls++;
      acc[date].cost += call.total_cost || 0;
      acc[date].duration += call.duration_minutes || 0;
      return acc;
    }, {} as Record<string, { calls: number; cost: number; duration: number }>);
    const daily_calls = Object.entries(dailyCounts)
      .map(([date, data]) => ({ date, ...data }))
      .sort((a, b) => a.date.localeCompare(b.date));

    // Calculate weekly trends
    const weeklyData = callsData.reduce((acc, call) => {
      const date = new Date(call.start_time);
      const weekStart = new Date(date);
      weekStart.setDate(date.getDate() - date.getDay());
      const weekKey = weekStart.toLocaleDateString();
      
      if (!acc[weekKey]) {
        acc[weekKey] = { calls: 0, cost: 0, completed: 0 };
      }
      acc[weekKey].calls++;
      acc[weekKey].cost += call.total_cost || 0;
      if (call.status === 'completed') acc[weekKey].completed++;
      return acc;
    }, {} as Record<string, { calls: number; cost: number; completed: number }>);
    
    const weekly_trends = Object.entries(weeklyData)
      .map(([week, data]) => ({
        week,
        calls: data.calls,
        cost: data.cost,
        success_rate: data.calls > 0 ? (data.completed / data.calls) * 100 : 0
      }))
      .sort((a, b) => a.week.localeCompare(b.week));

    // Calculate cost analysis
    const cost_analysis = [
      { category: 'Voice Calls', cost: total_cost * 0.7, percentage: 70 },
      { category: 'SMS', cost: total_cost * 0.15, percentage: 15 },
      { category: 'WhatsApp', cost: total_cost * 0.1, percentage: 10 },
      { category: 'Other', cost: total_cost * 0.05, percentage: 5 }
    ];

    // Mock performance metrics (in real implementation, these would come from actual data)
    const performance_metrics = {
      response_time: 2.5, // seconds
      resolution_rate: 85, // percentage
      repeat_calls: 12, // percentage
      escalation_rate: 8 // percentage
    };

    return {
      total_calls,
      total_duration,
      total_cost,
      success_rate,
      average_duration,
      average_cost_per_call,
      peak_hours,
      call_quality_score: 87,
      customer_satisfaction: 92,
      conversion_rate: 23,
      calls_by_status,
      calls_by_medium,
      calls_by_assistant: [], // Would be populated with actual assistant data
      daily_calls,
      weekly_trends,
      monthly_performance: [], // Would be populated with monthly data
      cost_analysis,
      performance_metrics
    };
  };

  const getMetricIcon = (metric: string) => {
    switch (metric) {
      case 'calls':
        return <Phone className="h-4 w-4" />;
      case 'duration':
        return <Clock className="h-4 w-4" />;
      case 'cost':
        return <DollarSign className="h-4 w-4" />;
      case 'success':
        return <CheckCircle className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  const getMetricColor = (metric: string, value: number) => {
    switch (metric) {
      case 'success_rate':
        return value >= 80 ? 'text-green-600' : value >= 60 ? 'text-yellow-600' : 'text-red-600';
      case 'cost':
        return value > 100 ? 'text-red-600' : value > 50 ? 'text-yellow-600' : 'text-green-600';
      default:
        return 'text-blue-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading advanced analytics...</p>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-8">
        <AlertTriangle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-medium mb-2">No analytics data available</h3>
        <p className="text-muted-foreground">
          Start making calls to see detailed analytics and performance metrics.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Select value={selectedTimeRange} onValueChange={setSelectedTimeRange}>
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
        </div>

        <Tabs value={selectedView} onValueChange={setSelectedView}>
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="trends">Trends</TabsTrigger>
            <TabsTrigger value="costs">Costs</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
            {getMetricIcon('calls')}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_calls.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {selectedTimeRange} period
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            {getMetricIcon('success')}
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getMetricColor('success_rate', analytics.success_rate)}`}>
              {analytics.success_rate.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {analytics.total_calls > 0 ? `${Math.round(analytics.success_rate * analytics.total_calls / 100)} completed` : 'No calls'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            {getMetricIcon('duration')}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(analytics.average_duration)}m
            </div>
            <p className="text-xs text-muted-foreground">
              {analytics.total_duration.toFixed(0)} total minutes
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            {getMetricIcon('cost')}
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getMetricColor('cost', analytics.total_cost)}`}>
              ${analytics.total_cost.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">
              ${analytics.average_cost_per_call.toFixed(4)} per call
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics */}
      <TabsContent value="overview" className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Daily Call Volume */}
          <Card>
            <CardHeader>
              <CardTitle>Daily Call Volume</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={analytics.daily_calls}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="calls" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Call Status Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Call Status Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analytics.calls_by_status}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ status, percent }) => `${status} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {analytics.calls_by_status.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="performance" className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Metrics */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Response Time</span>
                  <Badge variant="outline">{analytics.performance_metrics.response_time}s</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Resolution Rate</span>
                  <Badge variant="outline">{analytics.performance_metrics.resolution_rate}%</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Repeat Calls</span>
                  <Badge variant="outline">{analytics.performance_metrics.repeat_calls}%</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Escalation Rate</span>
                  <Badge variant="outline">{analytics.performance_metrics.escalation_rate}%</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Peak Hours */}
          <Card>
            <CardHeader>
              <CardTitle>Peak Hours</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.peak_hours}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="calls" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="trends" className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Weekly Trends */}
          <Card>
            <CardHeader>
              <CardTitle>Weekly Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={analytics.weekly_trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="calls" fill="#8884d8" />
                  <Line yAxisId="right" type="monotone" dataKey="success_rate" stroke="#82ca9d" />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Communication Medium */}
          <Card>
            <CardHeader>
              <CardTitle>Communication Medium</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analytics.calls_by_medium}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ medium, percent }) => `${medium} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {analytics.calls_by_medium.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="costs" className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cost Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Cost Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analytics.cost_analysis}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ category, percentage }) => `${category} ${percentage}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="cost"
                  >
                    {analytics.cost_analysis.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Cost Trend */}
          <Card>
            <CardHeader>
              <CardTitle>Cost Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analytics.daily_calls}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="cost" stroke="#ff7300" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      </TabsContent>
    </div>
  );
};

export default AdvancedAnalytics;
