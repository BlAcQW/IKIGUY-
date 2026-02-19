import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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
  LineChart
} from 'lucide-react';

interface AnalyticsData {
  totalUsers: number;
  activeUsers: number;
  totalCalls: number;
  totalRevenue: number;
  revenueGrowth: number;
  callGrowth: number;
  userGrowth: number;
  recentActivity: Array<{
    id: string;
    type: string;
    description: string;
    timestamp: string;
    amount?: number;
  }>;
  monthlyRevenue: Array<{
    month: string;
    revenue: number;
  }>;
  callMetrics: {
    total: number;
    successful: number;
    failed: number;
    averageDuration: number;
  };
}

const DashboardAnalytics: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  const loadAnalytics = async () => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      // In a real implementation, you would fetch analytics from your backend
      // For now, we'll simulate the data
      const mockAnalytics: AnalyticsData = {
        totalUsers: 1247,
        activeUsers: 892,
        totalCalls: 3456,
        totalRevenue: 45678.90,
        revenueGrowth: 12.5,
        callGrowth: 8.3,
        userGrowth: 15.2,
        recentActivity: [
          {
            id: '1',
            type: 'payment',
            description: 'Payment received from John Doe',
            timestamp: new Date().toISOString(),
            amount: 150.00
          },
          {
            id: '2',
            type: 'call',
            description: 'Voice agent call completed',
            timestamp: new Date(Date.now() - 3600000).toISOString()
          },
          {
            id: '3',
            type: 'user',
            description: 'New user registration',
            timestamp: new Date(Date.now() - 7200000).toISOString()
          }
        ],
        monthlyRevenue: [
          { month: 'Jan', revenue: 12000 },
          { month: 'Feb', revenue: 15000 },
          { month: 'Mar', revenue: 18000 },
          { month: 'Apr', revenue: 22000 },
          { month: 'May', revenue: 25000 },
          { month: 'Jun', revenue: 28000 }
        ],
        callMetrics: {
          total: 3456,
          successful: 3120,
          failed: 336,
          averageDuration: 4.5
        }
      };

      setAnalytics(mockAnalytics);
    } catch (error: any) {
      console.error('Error loading analytics:', error);
      toast({
        title: "Error loading analytics",
        description: error.message || "Failed to load analytics data",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [user, timeRange]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getGrowthColor = (growth: number) => {
    return growth >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getGrowthIcon = (growth: number) => {
    return growth >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />;
  };

  const exportAnalytics = () => {
    if (!analytics) return;

    const csvContent = [
      ['Metric', 'Value', 'Growth'],
      ['Total Users', analytics.totalUsers.toString(), `${analytics.userGrowth}%`],
      ['Active Users', analytics.activeUsers.toString(), ''],
      ['Total Calls', analytics.totalCalls.toString(), `${analytics.callGrowth}%`],
      ['Total Revenue', formatCurrency(analytics.totalRevenue), `${analytics.revenueGrowth}%`],
      ['Successful Calls', analytics.callMetrics.successful.toString(), ''],
      ['Failed Calls', analytics.callMetrics.failed.toString(), ''],
      ['Average Call Duration', `${analytics.callMetrics.averageDuration} min`, '']
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    toast({
      title: "Export successful",
      description: "Analytics data has been downloaded as CSV",
    });
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Analytics Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSpinner text="Loading analytics..." />
        </CardContent>
      </Card>
    );
  }

  if (!analytics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Analytics Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No analytics data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h2>
          <p className="text-muted-foreground">
            Real-time insights into your AI Labs Africa performance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadAnalytics}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={exportAnalytics}
          >
            <Download className="h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Time Range Selector */}
      <div className="flex gap-2">
        {(['7d', '30d', '90d'] as const).map((range) => (
          <Button
            key={range}
            variant={timeRange === range ? "default" : "outline"}
            size="sm"
            onClick={() => setTimeRange(range)}
          >
            {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : '90 Days'}
          </Button>
        ))}
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(analytics.totalRevenue)}</div>
            <div className={`flex items-center text-xs ${getGrowthColor(analytics.revenueGrowth)}`}>
              {getGrowthIcon(analytics.revenueGrowth)}
              <span className="ml-1">{analytics.revenueGrowth}% from last period</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(analytics.totalUsers)}</div>
            <div className={`flex items-center text-xs ${getGrowthColor(analytics.userGrowth)}`}>
              {getGrowthIcon(analytics.userGrowth)}
              <span className="ml-1">{analytics.userGrowth}% from last period</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
            <Phone className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(analytics.totalCalls)}</div>
            <div className={`flex items-center text-xs ${getGrowthColor(analytics.callGrowth)}`}>
              {getGrowthIcon(analytics.callGrowth)}
              <span className="ml-1">{analytics.callGrowth}% from last period</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(analytics.activeUsers)}</div>
            <p className="text-xs text-muted-foreground">
              {Math.round((analytics.activeUsers / analytics.totalUsers) * 100)}% of total users
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Call Metrics */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Call Performance</CardTitle>
            <CardDescription>Voice agent call statistics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Total Calls</span>
              <span className="font-medium">{formatNumber(analytics.callMetrics.total)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Successful Calls</span>
              <span className="font-medium text-green-600">{formatNumber(analytics.callMetrics.successful)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Failed Calls</span>
              <span className="font-medium text-red-600">{formatNumber(analytics.callMetrics.failed)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Success Rate</span>
              <span className="font-medium">
                {Math.round((analytics.callMetrics.successful / analytics.callMetrics.total) * 100)}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span>Average Duration</span>
              <span className="font-medium">{analytics.callMetrics.averageDuration} min</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest system activities</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      activity.type === 'payment' ? 'bg-green-500' :
                      activity.type === 'call' ? 'bg-blue-500' : 'bg-purple-500'
                    }`} />
                    <div>
                      <p className="text-sm font-medium">{activity.description}</p>
                      <p className="text-xs text-muted-foreground">{formatDate(activity.timestamp)}</p>
                    </div>
                  </div>
                  {activity.amount && (
                    <span className="text-sm font-medium text-green-600">
                      {formatCurrency(activity.amount)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Revenue Chart Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue Trend</CardTitle>
          <CardDescription>Monthly revenue over the last 6 months</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center border-2 border-dashed border-muted-foreground/25 rounded-lg">
            <div className="text-center">
              <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">Revenue chart will be displayed here</p>
              <p className="text-sm text-muted-foreground">
                Integration with charting library (e.g., Recharts) required
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DashboardAnalytics;
