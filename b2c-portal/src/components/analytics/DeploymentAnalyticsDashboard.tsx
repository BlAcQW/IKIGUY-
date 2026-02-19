import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import {
  useDeploymentAnalytics,
  useAllDeployments,
  useRealTimeDeploymentUpdates
} from '@/hooks/useDeploymentTracking';
import { Download, RefreshCw, AlertCircle } from 'lucide-react';
// import DeploymentMetricsCards from './deployment/DeploymentMetricsCards'; // File not found
// import DeploymentTrendsChart from './deployment/DeploymentTrendsChart'; // File not found
import type { TimeRange } from '@/types/analytics';

interface DeploymentAnalyticsDashboardProps {
  tenantId?: string;
}

const DeploymentAnalyticsDashboard: React.FC<DeploymentAnalyticsDashboardProps> = ({
  tenantId: propTenantId
}) => {
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');
  const [selectedAutomation, setSelectedAutomation] = useState<string>('all');
  const [selectedTab, setSelectedTab] = useState('overview');
  const { toast } = useToast();
  const { user } = useMongoAuth();

  const tenantId = propTenantId || user?.user_metadata?.tenant_id || user?.id || '';

  const {
    analytics,
    isLoading: analyticsLoading,
    error: analyticsError,
    refetch: refetchAnalytics
  } = useDeploymentAnalytics(tenantId, timeRange);

  const {
    deployments,
    isLoading: deploymentsLoading,
    error: deploymentsError,
    refetch: refetchDeployments
  } = useAllDeployments(tenantId);

  const { isConnected, lastUpdate } = useRealTimeDeploymentUpdates(
    selectedAutomation !== 'all' ? selectedAutomation : ''
  );

  const exportAnalytics = (format: 'csv' | 'json') => {
    if (!analytics || !deployments) {
      toast({
        title: "Export Error",
        description: "No data available for export",
        variant: "destructive"
      });
      return;
    }

    const exportData = {
      timeRange,
      selectedAutomation,
      analytics,
      deployments,
      exportDate: new Date().toISOString()
    };

    const content = format === 'json'
      ? JSON.stringify(exportData, null, 2)
      : Object.entries(analytics.summary)
          .map(([key, value]) => `${key},${value}`)
          .join('\n');

    const element = document.createElement('a');
    const file = new Blob([content], {
      type: format === 'json' ? 'application/json' : 'text/csv'
    });
    element.href = URL.createObjectURL(file);
    element.download = `deployment-analytics-${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);

    toast({
      title: "Export Successful",
      description: `Analytics data exported as ${format.toUpperCase()}`
    });
  };

  const handleRefresh = async () => {
    try {
      await Promise.all([refetchAnalytics(), refetchDeployments()]);
      toast({
        title: "Data Refreshed",
        description: "Analytics data has been updated"
      });
    } catch (error) {
      toast({
        title: "Refresh Failed",
        description: "Could not refresh analytics data",
        variant: "destructive"
      });
    }
  };

  const isLoading = analyticsLoading || deploymentsLoading;
  const hasError = analyticsError || deploymentsError;

  if (hasError) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="h-16 w-16 status-icon-error mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Failed to Load Analytics</h3>
            <p className="text-gray-600 mb-4">
              {analyticsError?.message || deploymentsError?.message || 'Unknown error occurred'}
            </p>
            <Button onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Deployment Analytics</h2>
          <p className="text-gray-600">
            Monitor automation deployment performance and trends
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Select value={timeRange} onValueChange={(value) => setTimeRange(value as TimeRange)}>
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
            onClick={() => exportAnalytics('json')}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      {/* <DeploymentMetricsCards
        analytics={analytics}
        isLoading={isLoading}
        isConnected={isConnected}
      /> */}

      {/* Detailed Analytics */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="deployments">Deployments</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* <DeploymentTrendsChart
            trends={analytics?.deployment_trends || []}
            isLoading={isLoading}
          /> */}
          <div>Trends chart component not found</div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Trends</CardTitle>
              <CardDescription>
                Detailed trend analysis and forecasting
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-gray-600">
                <p>Advanced trend analysis coming soon</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="deployments" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Individual Deployments</CardTitle>
              <CardDescription>
                Detailed view of individual deployment status and metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              {deployments && deployments.length > 0 ? (
                <div className="space-y-4">
                  {deployments.slice(0, 10).map((deployment: any) => (
                    <div
                      key={deployment.id}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div>
                        <p className="font-medium">{deployment.automation_name || 'Unnamed Automation'}</p>
                        <p className="text-sm text-gray-600">
                          Deployed: {deployment.deployed_at ? new Date(deployment.deployed_at).toLocaleString() : 'N/A'}
                        </p>
                      </div>
                      <div className="text-right">
                        <span className={`status-badge ${
                          deployment.status === 'active'
                            ? 'success'
                            : 'neutral'
                        }`}>
                          {deployment.status || 'Unknown'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-600">
                  <p>No deployments found</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Footer */}
      {lastUpdate && (
        <div className="text-sm text-gray-600 text-center">
          Last updated: {new Date(lastUpdate).toLocaleString()}
        </div>
      )}
    </div>
  );
};

export default DeploymentAnalyticsDashboard;