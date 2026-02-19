/**
 * @deprecated This component's functionality has been moved to RealTimeHealthMonitor.
 * Use RealTimeHealthMonitor or the new health subcomponents instead.
 * This file will be removed in a future release.
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { useDeploymentStatus } from '@/hooks/useDeploymentTracking';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  ExternalLink,
  Heart,
  RefreshCw,
  Shield,
  Wifi,
  WifiOff,
  XCircle
} from 'lucide-react';

interface AutomationHealthCardProps {
  automationId: string;
  automationName?: string;
  onViewDetails?: (automationId: string) => void;
  className?: string;
  showActions?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const AutomationHealthCard: React.FC<AutomationHealthCardProps> = ({
  automationId,
  automationName,
  onViewDetails,
  className = '',
  showActions = true,
  size = 'md'
}) => {
  const { toast } = useToast();

  const {
    deploymentStatus,
    isLoading,
    error,
    refetch,
    triggerHealthCheck,
    isTriggering
  } = useDeploymentStatus(automationId);

  const getOverallHealth = () => {
    if (!deploymentStatus) return 'UNKNOWN';

    const components = [
      deploymentStatus.components.vapi_agent,
      deploymentStatus.components.n8n_workflow,
      ...deploymentStatus.components.integrations,
      ...deploymentStatus.components.custom_tools,
      deploymentStatus.components.demo_page
    ].filter(Boolean);

    const healthStatuses = components.map(comp => comp.health_status);

    if (healthStatuses.includes('DOWN')) return 'DOWN';
    if (healthStatuses.includes('DEGRADED')) return 'DEGRADED';
    if (healthStatuses.every(status => status === 'HEALTHY')) return 'HEALTHY';
    return 'UNKNOWN';
  };

  const getHealthIcon = (health: string, iconSize: string = 'h-4 w-4') => {
    switch (health) {
      case 'HEALTHY':
        return <Shield className={`${iconSize} text-green-500`} />;
      case 'DEGRADED':
        return <AlertTriangle className={`${iconSize} text-yellow-500`} />;
      case 'DOWN':
        return <XCircle className={`${iconSize} text-red-500`} />;
      default:
        return <AlertTriangle className={`${iconSize} text-gray-500`} />;
    }
  };

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'HEALTHY': return 'text-green-600';
      case 'DEGRADED': return 'text-yellow-600';
      case 'DOWN': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string, iconSize: string = 'h-4 w-4') => {
    switch (status) {
      case 'DEPLOYED':
        return <CheckCircle className={`${iconSize} text-green-500`} />;
      case 'DEPLOYING':
        return <Clock className={`${iconSize} text-yellow-500`} />;
      case 'FAILED':
        return <XCircle className={`${iconSize} text-red-500`} />;
      case 'STOPPED':
        return <AlertTriangle className={`${iconSize} text-orange-500`} />;
      default:
        return <Clock className={`${iconSize} text-gray-500`} />;
    }
  };

  const formatUptime = (percentage: number) => {
    if (percentage >= 99.9) return '99.9%+';
    return `${percentage.toFixed(1)}%`;
  };

  const handleHealthCheck = () => {
    triggerHealthCheck();
    toast({
      title: "Health Check Triggered",
      description: "Checking component health...",
    });
  };

  const sizeClasses = {
    sm: 'h-32',
    md: 'h-40',
    lg: 'h-48'
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  };

  const textSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  };

  if (isLoading) {
    return (
      <Card className={`${sizeClasses[size]} ${className}`}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <p className={`${textSizes[size]} text-gray-600`}>Loading...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`${sizeClasses[size]} ${className} border-red-200`}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <AlertTriangle className={`${iconSizes[size]} text-destructive mx-auto mb-2`} />
            <p className={`${textSizes[size]} text-gray-600 mb-2`}>Error loading</p>
            {showActions && (
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-3 w-3" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!deploymentStatus) {
    return (
      <Card className={`${sizeClasses[size]} ${className}`}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <AlertTriangle className={`${iconSizes[size]} text-gray-600 mx-auto mb-2`} />
            <p className={`${textSizes[size]} text-gray-600`}>No data</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const overallHealth = getOverallHealth();

  return (
    <Card className={`${sizeClasses[size]} ${className} hover:shadow-md transition-shadow cursor-pointer`}
          onClick={() => onViewDetails?.(automationId)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className={`${textSizes[size]} truncate`}>
            {automationName || `Automation ${automationId.slice(-8)}`}
          </CardTitle>
          <div className="flex items-center gap-1">
            {getHealthIcon(overallHealth, iconSizes[size])}
            {getStatusIcon(deploymentStatus.status, iconSizes[size])}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Status and Health */}
        <div className="flex items-center justify-between">
          <span className={`${textSizes[size]} text-gray-600`}>Status</span>
          <Badge
            variant={deploymentStatus.status === 'DEPLOYED' ? 'success' : deploymentStatus.status === 'FAILED' ? 'destructive' : 'secondary'}
            className={size === 'sm' ? 'text-xs px-1 py-0' : ''}
          >
            {deploymentStatus.status}
          </Badge>
        </div>

        <div className="flex items-center justify-between">
          <span className={`${textSizes[size]} text-gray-600`}>Health</span>
          <span className={`${textSizes[size]} font-medium ${getHealthColor(overallHealth)}`}>
            {overallHealth}
          </span>
        </div>

        {/* Uptime Progress */}
        <div className="space-y-1">
          <div className="flex justify-between">
            <span className={`${textSizes[size]} text-gray-600`}>Uptime</span>
            <span className={`${textSizes[size]} font-medium`}>
              {formatUptime(deploymentStatus.health_metrics.uptime_percentage)}
            </span>
          </div>
          <Progress
            value={deploymentStatus.health_metrics.uptime_percentage}
            className={size === 'sm' ? 'h-1' : 'h-2'}
          />
        </div>

        {/* Metrics Row */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-gray-600">Response:</span>
            <span className="ml-1 font-medium">{deploymentStatus.health_metrics.response_time}ms</span>
          </div>
          <div>
            <span className="text-gray-600">Errors:</span>
            <span className="ml-1 font-medium">{(deploymentStatus.health_metrics.error_rate * 100).toFixed(1)}%</span>
          </div>
        </div>

        {/* Component Count */}
        <div className="flex items-center justify-between">
          <span className={`${textSizes[size]} text-gray-600`}>Components</span>
          <span className={`${textSizes[size]} font-medium`}>
            {deploymentStatus.deployment_summary.deployed_components}/
            {deploymentStatus.deployment_summary.total_components}
          </span>
        </div>

        {/* Actions */}
        {showActions && (
          <div className="flex justify-between gap-1 pt-1">
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                refetch();
              }}
              className={size === 'sm' ? 'h-6 px-2' : ''}
            >
              <RefreshCw className={size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} />
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleHealthCheck();
              }}
              disabled={isTriggering}
              className={size === 'sm' ? 'h-6 px-2' : ''}
            >
              {isTriggering ? (
                <RefreshCw className={`${size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} animate-spin`} />
              ) : (
                <Heart className={size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} />
              )}
            </Button>

            {onViewDetails && (
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onViewDetails(automationId);
                }}
                className={size === 'sm' ? 'h-6 px-2' : ''}
              >
                <ExternalLink className={size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} />
              </Button>
            )}
          </div>
        )}

        {/* Last Update */}
        <div className="text-xs text-gray-600 text-center border-t pt-1">
          Last: {new Date(deploymentStatus.health_metrics.last_check).toLocaleTimeString()}
        </div>
      </CardContent>
    </Card>
  );
};

export default AutomationHealthCard;