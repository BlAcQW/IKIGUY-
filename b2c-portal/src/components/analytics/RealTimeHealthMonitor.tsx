import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import {
  useDeploymentStatus,
  useActivityLog,
  useRealTimeDeploymentUpdates
} from '@/hooks/useDeploymentTracking';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Heart,
  RefreshCw,
  Shield,
  Wifi,
  WifiOff,
  XCircle,
  Zap
} from 'lucide-react';
import HealthStatusCard from './health/HealthStatusCard';
import ActivityLog from './health/ActivityLog';

interface RealTimeHealthMonitorProps {
  automationId: string;
  compactMode?: boolean;
  showActivityLog?: boolean;
  refreshInterval?: number;
}

const RealTimeHealthMonitor: React.FC<RealTimeHealthMonitorProps> = ({
  automationId,
  compactMode = false,
  showActivityLog = true,
  refreshInterval = 30000
}) => {
  const { toast } = useToast();
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [previousHealth, setPreviousHealth] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState('overview');

  const {
    deploymentStatus,
    isLoading,
    error,
    refetch,
    triggerHealthCheck,
    isTriggering
  } = useDeploymentStatus(automationId);

  const {
    activityLog,
    isLoading: activityLoading,
    refetch: refetchActivity
  } = useActivityLog(automationId, 20);

  const { isConnected, lastUpdate } = useRealTimeDeploymentUpdates(automationId);

  const getOverallHealth = (status: any) => {
    if (!status) return 'UNKNOWN';

    const components = [
      status.components?.vapi_agent,
      status.components?.n8n_workflow,
      ...(status.components?.integrations || []),
      ...(status.components?.custom_tools || []),
      status.components?.demo_page
    ].filter(Boolean);

    const healthStatuses = components.map(comp => comp.health_status);

    if (healthStatuses.includes('DOWN')) return 'DOWN';
    if (healthStatuses.includes('DEGRADED')) return 'DEGRADED';
    if (healthStatuses.every(status => status === 'HEALTHY')) return 'HEALTHY';
    return 'UNKNOWN';
  };

  const getHealthScore = (status: any) => {
    if (!status) return 0;

    const components = [
      status.components?.vapi_agent,
      status.components?.n8n_workflow,
      ...(status.components?.integrations || []),
      ...(status.components?.custom_tools || []),
      status.components?.demo_page
    ].filter(Boolean);

    const healthyCount = components.filter(comp => comp.health_status === 'HEALTHY').length;
    return components.length > 0 ? (healthyCount / components.length) * 100 : 0;
  };

  const getOverallHealthColor = (health: string) => {
    switch (health) {
      case 'HEALTHY':
        return 'status-card-success';
      case 'DEGRADED':
        return 'status-card-warning';
      case 'DOWN':
        return 'status-card-error';
      default:
        return 'status-card-neutral';
    }
  };

  useEffect(() => {
    if (deploymentStatus && alertsEnabled) {
      const currentOverallHealth = getOverallHealth(deploymentStatus);

      if (previousHealth && previousHealth !== currentOverallHealth) {
        if (currentOverallHealth === 'DOWN' || currentOverallHealth === 'DEGRADED') {
          toast({
            title: "Health Alert",
            description: `Automation health changed from ${previousHealth} to ${currentOverallHealth}`,
            variant: "destructive",
          });
        } else if (currentOverallHealth === 'HEALTHY' && previousHealth !== 'HEALTHY') {
          toast({
            title: "Health Restored",
            description: "Automation health has been restored",
          });
        }
      }

      setPreviousHealth(currentOverallHealth);
    }
  }, [deploymentStatus, previousHealth, alertsEnabled, toast]);

  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(() => {
        refetch();
        if (showActivityLog) {
          refetchActivity();
        }
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [refetch, refetchActivity, refreshInterval, showActivityLog]);

  const handleRefresh = async () => {
    try {
      await refetch();
      if (showActivityLog) {
        await refetchActivity();
      }
      toast({
        title: "Data Refreshed",
        description: "Health monitor data has been updated"
      });
    } catch (error) {
      toast({
        title: "Refresh Failed",
        description: "Could not refresh health data",
        variant: "destructive"
      });
    }
  };

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Failed to load health monitoring data: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (compactMode) {
    const overallHealth = getOverallHealth(deploymentStatus);
    const healthScore = getHealthScore(deploymentStatus);

    return (
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Heart className="h-5 w-5 status-icon-error" />
              <div>
                <p className="font-medium">Health Monitor</p>
                <p className="text-sm text-gray-600">
                  {healthScore.toFixed(1)}% healthy
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge className={getOverallHealthColor(overallHealth)}>
                {overallHealth}
              </Badge>
              {isConnected ? (
                <Wifi className="h-4 w-4 status-icon-success" />
              ) : (
                <WifiOff className="h-4 w-4 status-icon-error" />
              )}
            </div>
          </div>
          <Progress value={healthScore} className="mt-3" />
        </CardContent>
      </Card>
    );
  }

  const overallHealth = getOverallHealth(deploymentStatus);
  const healthScore = getHealthScore(deploymentStatus);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center">
            <Heart className="h-8 w-8 status-icon-error mr-3" />
            Health Monitor
          </h2>
          <p className="text-gray-600">
            Real-time automation health and performance monitoring
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
          <Button
            variant="outline"
            size="sm"
            onClick={triggerHealthCheck}
            disabled={isTriggering}
          >
            <Shield className={`h-4 w-4 mr-2 ${isTriggering ? 'animate-spin' : ''}`} />
            Health Check
          </Button>
        </div>
      </div>

      {/* Overall Health Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center">
              Overall System Health
              <Badge className={`ml-2 ${getOverallHealthColor(overallHealth)}`}>
                {overallHealth}
              </Badge>
            </CardTitle>
            <div className="flex items-center space-x-2">
              {isConnected ? (
                <Badge variant="outline" className="status-icon-success">
                  <Wifi className="h-3 w-3 mr-1" />
                  Connected
                </Badge>
              ) : (
                <Badge variant="outline" className="status-icon-error">
                  <WifiOff className="h-3 w-3 mr-1" />
                  Disconnected
                </Badge>
              )}
            </div>
          </div>
          <CardDescription>
            Automation ID: {automationId}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Health Score</span>
                <span className="text-2xl font-bold">{healthScore.toFixed(1)}%</span>
              </div>
              <Progress value={healthScore} className="h-3" />
            </div>

            {lastUpdate && (
              <div className="text-sm text-gray-600">
                Last update: {new Date(lastUpdate).toLocaleString()}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Detailed Health Information */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="overview">Components</TabsTrigger>
          <TabsTrigger value="activity">Activity Log</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {deploymentStatus?.components ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {deploymentStatus.components.vapi_agent && (
                <HealthStatusCard
                  component={deploymentStatus.components.vapi_agent}
                  isConnected={isConnected}
                />
              )}
              {deploymentStatus.components.n8n_workflow && (
                <HealthStatusCard
                  component={deploymentStatus.components.n8n_workflow}
                  isConnected={isConnected}
                />
              )}
              {deploymentStatus.components.integrations?.map((integration: any, index: number) => (
                <HealthStatusCard
                  key={index}
                  component={integration}
                  isConnected={isConnected}
                />
              ))}
              {deploymentStatus.components.custom_tools?.map((tool: any, index: number) => (
                <HealthStatusCard
                  key={index}
                  component={tool}
                  isConnected={isConnected}
                />
              ))}
              {deploymentStatus.components.demo_page && (
                <HealthStatusCard
                  component={deploymentStatus.components.demo_page}
                  isConnected={isConnected}
                />
              )}
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <Activity className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-600">No component data available</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="activity">
          {showActivityLog && (
            <ActivityLog
              activities={activityLog || []}
              isLoading={activityLoading}
            />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default RealTimeHealthMonitor;