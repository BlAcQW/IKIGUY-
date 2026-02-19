import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Phone, 
  Clock, 
  TrendingUp, 
  DollarSign, 
  Users, 
  CheckCircle, 
  XCircle, 
  BarChart3,
  Calendar,
  Mail,
  Database,
  RefreshCw,
  Download,
  AlertCircle
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface VapiAnalyticsProps {
  agentId: string;
  tenantId?: string;
  apiBaseUrl: string;
}

interface Analytics {
  agent_id: string;
  tenant_id: string;
  period: string;
  calls: {
    total: number;
    successful: number;
    failed: number;
    average_duration: number;
    total_duration: number;
  };
  costs: {
    total: number;
    breakdown: {
      voice_minutes: number;
      ai_processing: number;
      phone_charges: number;
    };
  };
  integration_usage: Record<string, number>;
  quality_metrics: {
    completion_rate: number;
    success_rate: number;
  };
}

const integrationIcons: Record<string, string> = {
  calendar: '📅',
  email: '📧',
  database: '🗃️',
  crm: '🏢',
  sms: '📱',
  webhook: '🔗'
};

export const VapiAnalyticsDashboard: React.FC<VapiAnalyticsProps> = ({
  agentId,
  tenantId = 'default',
  apiBaseUrl
}) => {
  const { toast } = useToast();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('30');

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${apiBaseUrl}/vapi/agents/${agentId}/analytics?tenant_id=${tenantId}&days=${period}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch analytics');
      }

      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      toast({
        title: "Failed to load analytics",
        description: "Could not fetch agent analytics data.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (agentId) {
      fetchAnalytics();
    }
  }, [agentId, period]);

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Analytics Dashboard</h3>
          <div className="animate-spin">
            <RefreshCw className="h-4 w-4" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-muted rounded w-3/4"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-muted rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <AlertCircle className="h-8 w-8 text-gray-600 mx-auto mb-2" />
          <p className="text-gray-600">Unable to load analytics data</p>
          <Button variant="outline" onClick={fetchAnalytics} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Analytics Dashboard</h3>
          <p className="text-sm text-gray-600">
            Performance metrics for the {analytics.period.replace('_', ' ')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="90">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={fetchAnalytics}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
            <Phone className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.calls.total}</div>
            <p className="text-xs text-gray-600">
              {analytics.calls.successful} successful, {analytics.calls.failed} failed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            <Clock className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatDuration(analytics.calls.average_duration)}
            </div>
            <p className="text-xs text-gray-600">
              {formatDuration(analytics.calls.total_duration)} total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(analytics.quality_metrics.success_rate * 100)}%
            </div>
            <p className="text-xs text-gray-600">
              Completion rate: {Math.round(analytics.quality_metrics.completion_rate * 100)}%
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
              {formatCurrency(analytics.costs.total)}
            </div>
            <p className="text-xs text-gray-600">
              ${(analytics.costs.total / Math.max(1, analytics.calls.total)).toFixed(3)} per call
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Call Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Call Performance
            </CardTitle>
            <CardDescription>
              Breakdown of call success and failure rates
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-sm">Successful Calls</span>
              </div>
              <div className="text-right">
                <div className="font-medium">{analytics.calls.successful}</div>
                <div className="text-xs text-gray-600">
                  {analytics.calls.total > 0 ? Math.round((analytics.calls.successful / analytics.calls.total) * 100) : 0}%
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-500" />
                <span className="text-sm">Failed Calls</span>
              </div>
              <div className="text-right">
                <div className="font-medium">{analytics.calls.failed}</div>
                <div className="text-xs text-gray-600">
                  {analytics.calls.total > 0 ? Math.round((analytics.calls.failed / analytics.calls.total) * 100) : 0}%
                </div>
              </div>
            </div>

            <div className="pt-2 border-t">
              <div className="flex justify-between text-sm">
                <span>Average call duration:</span>
                <span className="font-medium">
                  {formatDuration(analytics.calls.average_duration)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Cost Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Cost Breakdown
            </CardTitle>
            <CardDescription>
              Detailed cost analysis by service type
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm">Voice Minutes</span>
              <span className="font-medium">
                {formatCurrency(analytics.costs.breakdown.voice_minutes)}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm">AI Processing</span>
              <span className="font-medium">
                {formatCurrency(analytics.costs.breakdown.ai_processing)}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm">Phone Charges</span>
              <span className="font-medium">
                {formatCurrency(analytics.costs.breakdown.phone_charges)}
              </span>
            </div>

            <div className="pt-2 border-t flex items-center justify-between">
              <span className="text-sm font-medium">Total Cost</span>
              <span className="font-bold">
                {formatCurrency(analytics.costs.total)}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Integration Usage */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Integration Usage
            </CardTitle>
            <CardDescription>
              How often different integrations were used during calls
            </CardDescription>
          </CardHeader>
          <CardContent>
            {Object.keys(analytics.integration_usage).length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {Object.entries(analytics.integration_usage).map(([integration, count]) => (
                  <div
                    key={integration}
                    className="flex items-center gap-3 p-3 border rounded-lg"
                  >
                    <span className="text-2xl">
                      {integrationIcons[integration] || '🔧'}
                    </span>
                    <div>
                      <div className="font-medium capitalize">{integration}</div>
                      <div className="text-sm text-gray-600">
                        {count} calls
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Users className="h-8 w-8 text-gray-600 mx-auto mb-2" />
                <p className="text-gray-600">
                  No integration usage data available for this period
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Export Options */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export Data
          </CardTitle>
          <CardDescription>
            Download analytics data for further analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              CSV Report
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              PDF Summary
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VapiAnalyticsDashboard;