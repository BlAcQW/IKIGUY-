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
  Legend
} from 'recharts';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  CreditCard, 
  Calendar,
  Download,
  RefreshCw,
  BarChart3,
  PieChart as PieChartIcon
} from 'lucide-react';

interface PaymentTransaction {
  id: string;
  transaction_id: string;
  amount: number;
  currency: string;
  payment_method: string;
  status: 'pending' | 'completed' | 'failed' | 'cancelled' | 'refunded';
  created_at: string;
  completed_at?: string;
}

interface AnalyticsData {
  totalAmount: number;
  totalTransactions: number;
  successfulTransactions: number;
  failedTransactions: number;
  averageAmount: number;
  monthlyTrends: Array<{
    month: string;
    amount: number;
    count: number;
  }>;
  paymentMethodDistribution: Array<{
    method: string;
    count: number;
    amount: number;
  }>;
  statusDistribution: Array<{
    status: string;
    count: number;
    amount: number;
  }>;
  recentActivity: PaymentTransaction[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const PaymentAnalytics: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>('30d');
  const [chartType, setChartType] = useState<'bar' | 'line' | 'pie'>('bar');

  const loadAnalytics = async () => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      // Calculate date range
      const now = new Date();
      const daysAgo = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : timeRange === '90d' ? 90 : 365;
      const startDate = new Date(now.getTime() - (daysAgo * 24 * 60 * 60 * 1000));

      // Fetch transactions
      const { data: transactions, error } = await supabase
        .from('payment_transactions')
        .select('*')
        .eq('user_id', user.id)
        .gte('created_at', startDate.toISOString())
        .order('created_at', { ascending: false });

      if (error) throw error;

      const transactionsData = transactions || [];
      
      // Calculate analytics
      const totalAmount = transactionsData.reduce((sum, t) => sum + Number(t.amount), 0);
      const totalTransactions = transactionsData.length;
      const successfulTransactions = transactionsData.filter(t => 
        t.status === 'completed' || t.status === 'successful'
      ).length;
      const failedTransactions = transactionsData.filter(t => 
        t.status === 'failed' || t.status === 'cancelled'
      ).length;
      const averageAmount = totalTransactions > 0 ? totalAmount / totalTransactions : 0;

      // Monthly trends
      const monthlyData = new Map<string, { amount: number; count: number }>();
      transactionsData.forEach(transaction => {
        const date = new Date(transaction.created_at);
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        const monthName = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        
        if (!monthlyData.has(monthKey)) {
          monthlyData.set(monthKey, { amount: 0, count: 0, monthName });
        }
        
        const monthData = monthlyData.get(monthKey)!;
        monthData.amount += Number(transaction.amount);
        monthData.count += 1;
      });

      const monthlyTrends = Array.from(monthlyData.entries())
        .map(([key, data]) => ({
          month: data.monthName,
          amount: Math.round(data.amount * 100) / 100,
          count: data.count
        }))
        .sort((a, b) => new Date(a.month).getTime() - new Date(b.month).getTime());

      // Payment method distribution
      const methodData = new Map<string, { count: number; amount: number }>();
      transactionsData.forEach(transaction => {
        const method = transaction.payment_method;
        if (!methodData.has(method)) {
          methodData.set(method, { count: 0, amount: 0 });
        }
        
        const methodInfo = methodData.get(method)!;
        methodInfo.count += 1;
        methodInfo.amount += Number(transaction.amount);
      });

      const paymentMethodDistribution = Array.from(methodData.entries())
        .map(([method, data]) => ({
          method: method.charAt(0).toUpperCase() + method.slice(1),
          count: data.count,
          amount: Math.round(data.amount * 100) / 100
        }))
        .sort((a, b) => b.amount - a.amount);

      // Status distribution
      const statusData = new Map<string, { count: number; amount: number }>();
      transactionsData.forEach(transaction => {
        const status = transaction.status;
        if (!statusData.has(status)) {
          statusData.set(status, { count: 0, amount: 0 });
        }
        
        const statusInfo = statusData.get(status)!;
        statusInfo.count += 1;
        statusInfo.amount += Number(transaction.amount);
      });

      const statusDistribution = Array.from(statusData.entries())
        .map(([status, data]) => ({
          status: status.charAt(0).toUpperCase() + status.slice(1),
          count: data.count,
          amount: Math.round(data.amount * 100) / 100
        }))
        .sort((a, b) => b.count - a.count);

      // Recent activity (last 10 transactions)
      const recentActivity = transactionsData.slice(0, 10);

      setAnalyticsData({
        totalAmount,
        totalTransactions,
        successfulTransactions,
        failedTransactions,
        averageAmount,
        monthlyTrends,
        paymentMethodDistribution,
        statusDistribution,
        recentActivity
      });

    } catch (error: any) {
      console.error('Error loading analytics:', error);
      toast({
        title: "Error loading analytics",
        description: error.message || "Failed to load payment analytics",
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
      currency: 'USD',
    }).format(amount);
  };

  const formatPercentage = (value: number, total: number) => {
    return total > 0 ? Math.round((value / total) * 100) : 0;
  };

  const exportAnalytics = () => {
    if (!analyticsData) return;

    const csvContent = [
      'Payment Analytics Report',
      `Generated: ${new Date().toLocaleDateString()}`,
      `Time Range: ${timeRange}`,
      '',
      'Summary',
      `Total Amount,${formatCurrency(analyticsData.totalAmount)}`,
      `Total Transactions,${analyticsData.totalTransactions}`,
      `Successful Transactions,${analyticsData.successfulTransactions}`,
      `Failed Transactions,${analyticsData.failedTransactions}`,
      `Average Amount,${formatCurrency(analyticsData.averageAmount)}`,
      '',
      'Monthly Trends',
      'Month,Amount,Count',
      ...analyticsData.monthlyTrends.map(trend => 
        `${trend.month},${formatCurrency(trend.amount)},${trend.count}`
      ),
      '',
      'Payment Method Distribution',
      'Method,Count,Amount',
      ...analyticsData.paymentMethodDistribution.map(method => 
        `${method.method},${method.count},${formatCurrency(method.amount)}`
      ),
      '',
      'Status Distribution',
      'Status,Count,Amount',
      ...analyticsData.statusDistribution.map(status => 
        `${status.status},${status.count},${formatCurrency(status.amount)}`
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `payment-analytics-${timeRange}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);

    toast({
      title: "Analytics exported",
      description: "Payment analytics data has been downloaded as CSV",
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
          <h2 className="text-2xl font-bold">Payment Analytics</h2>
          <p className="text-muted-foreground">
            Insights and trends from your payment transactions
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
            <CardTitle className="text-sm font-medium">Total Amount</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(analyticsData.totalAmount)}</div>
            <p className="text-xs text-muted-foreground">
              {analyticsData.totalTransactions} transactions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatPercentage(analyticsData.successfulTransactions, analyticsData.totalTransactions)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {analyticsData.successfulTransactions} successful
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Amount</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(analyticsData.averageAmount)}</div>
            <p className="text-xs text-muted-foreground">
              per transaction
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed Transactions</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.failedTransactions}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(analyticsData.failedTransactions, analyticsData.totalTransactions)}% of total
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Trends */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Monthly Trends
            </CardTitle>
            <CardDescription>
              Payment amount and transaction count over time
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
            </div>
            
            <ResponsiveContainer width="100%" height={300}>
              {chartType === 'bar' ? (
                <BarChart data={analyticsData.monthlyTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value: any, name: string) => [
                      name === 'amount' ? formatCurrency(value) : value,
                      name === 'amount' ? 'Amount' : 'Count'
                    ]}
                  />
                  <Bar dataKey="amount" fill="#0088FE" name="Amount" />
                </BarChart>
              ) : (
                <LineChart data={analyticsData.monthlyTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value: any, name: string) => [
                      name === 'amount' ? formatCurrency(value) : value,
                      name === 'amount' ? 'Amount' : 'Count'
                    ]}
                  />
                  <Line type="monotone" dataKey="amount" stroke="#0088FE" strokeWidth={2} />
                </LineChart>
              )}
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Payment Method Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChartIcon className="h-5 w-5" />
              Payment Methods
            </CardTitle>
            <CardDescription>
              Distribution by payment method
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analyticsData.paymentMethodDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ method, percent }) => `${method} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="amount"
                >
                  {analyticsData.paymentMethodDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: any) => [formatCurrency(value), 'Amount']}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Status Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction Status Distribution</CardTitle>
          <CardDescription>
            Breakdown of transactions by status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {analyticsData.statusDistribution.map((status, index) => (
              <div key={status.status} className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">{status.status}</p>
                  <p className="text-sm text-muted-foreground">
                    {status.count} transactions
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-bold">{formatCurrency(status.amount)}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatPercentage(status.count, analyticsData.totalTransactions)}%
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
            Latest payment transactions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {analyticsData.recentActivity.map((transaction) => (
              <div key={transaction.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="font-medium">Transaction {transaction.transaction_id.slice(-8)}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(transaction.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold">{formatCurrency(transaction.amount)}</p>
                  <Badge variant={
                    transaction.status === 'completed' || transaction.status === 'successful' ? 'default' :
                    transaction.status === 'pending' ? 'secondary' :
                    transaction.status === 'refunded' ? 'outline' : 'destructive'
                  }>
                    {transaction.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PaymentAnalytics;
