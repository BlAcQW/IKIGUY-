import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Cpu,
  Server,
  Shield,
  TrendingDown,
  TrendingUp,
  Wifi,
  WifiOff,
  XCircle,
  Zap
} from 'lucide-react';

interface DeploymentMetrics {
  summary: {
    total_automations: number;
    deployed_automations: number;
    failed_deployments: number;
    success_rate: number;
    avg_deployment_time: number;
  };
  realtime_status: {
    connected_automations: number;
    disconnected_automations: number;
    last_sync: string;
  };
}

interface DeploymentMetricsCardsProps {
  analytics: DeploymentMetrics | null;
  isLoading: boolean;
  isConnected: boolean;
}

const DeploymentMetricsCards: React.FC<DeploymentMetricsCardsProps> = ({
  analytics,
  isLoading,
  isConnected
}) => {
  if (isLoading || !analytics) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="pb-2">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const getStatusColor = (rate: number) => {
    if (rate >= 0.9) return 'text-green-600';
    if (rate >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Automations</CardTitle>
          <Zap className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{analytics.summary.total_automations}</div>
          <p className="text-xs text-muted-foreground">
            {analytics.summary.deployed_automations} deployed
          </p>
          <Progress
            value={(analytics.summary.deployed_automations / analytics.summary.total_automations) * 100}
            className="mt-2"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          <TrendingUp className={`h-4 w-4 ${getStatusColor(analytics.summary.success_rate)}`} />
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${getStatusColor(analytics.summary.success_rate)}`}>
            {(analytics.summary.success_rate * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground">
            {analytics.summary.failed_deployments} failed deployments
          </p>
          <Progress
            value={analytics.summary.success_rate * 100}
            className="mt-2"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Deploy Time</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {analytics.summary.avg_deployment_time.toFixed(1)}m
          </div>
          <p className="text-xs text-muted-foreground">
            Average deployment duration
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Real-time Status</CardTitle>
          {isConnected ? (
            <Wifi className="h-4 w-4 text-green-600" />
          ) : (
            <WifiOff className="h-4 w-4 text-red-600" />
          )}
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {analytics.realtime_status.connected_automations}
          </div>
          <p className="text-xs text-muted-foreground">
            Connected / {analytics.realtime_status.connected_automations + analytics.realtime_status.disconnected_automations} total
          </p>
          <Badge variant={isConnected ? "default" : "destructive"} className="mt-2">
            {isConnected ? "Connected" : "Disconnected"}
          </Badge>
        </CardContent>
      </Card>
    </div>
  );
};

export default DeploymentMetricsCards;