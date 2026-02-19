import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Heart,
  Shield,
  Wifi,
  WifiOff,
  XCircle,
  Zap
} from 'lucide-react';

interface HealthComponent {
  name: string;
  health_status: 'HEALTHY' | 'DEGRADED' | 'DOWN' | 'UNKNOWN';
  last_check: string;
  details: any;
}

interface HealthStatusCardProps {
  component: HealthComponent;
  isConnected?: boolean;
  compactMode?: boolean;
}

const HealthStatusCard: React.FC<HealthStatusCardProps> = ({
  component,
  isConnected = true,
  compactMode = false
}) => {
  const getHealthColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'down':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4" />;
      case 'down':
        return <XCircle className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  const getHealthScore = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 100;
      case 'degraded':
        return 65;
      case 'down':
        return 0;
      default:
        return 50;
    }
  };

  if (compactMode) {
    return (
      <div className="flex items-center justify-between p-3 border rounded-lg">
        <div className="flex items-center space-x-3">
          {getHealthIcon(component.health_status)}
          <div>
            <p className="font-medium text-sm">{component.name}</p>
            <p className="text-xs text-gray-600">
              Last check: {new Date(component.last_check).toLocaleTimeString()}
            </p>
          </div>
        </div>
        <Badge className={getHealthColor(component.health_status)}>
          {component.health_status}
        </Badge>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center">
            {getHealthIcon(component.health_status)}
            <span className="ml-2">{component.name}</span>
          </CardTitle>
          {isConnected ? (
            <Wifi className="h-4 w-4 text-green-600" />
          ) : (
            <WifiOff className="h-4 w-4 text-red-600" />
          )}
        </div>
        <CardDescription>
          Component health monitoring
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Health Status</span>
            <Badge className={getHealthColor(component.health_status)}>
              {getHealthIcon(component.health_status)}
              <span className="ml-1">{component.health_status}</span>
            </Badge>
          </div>

          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span>Health Score</span>
              <span className="font-medium">{getHealthScore(component.health_status)}%</span>
            </div>
            <Progress value={getHealthScore(component.health_status)} className="h-2" />
          </div>

          <div className="text-xs text-gray-600 space-y-1">
            <div className="flex justify-between">
              <span>Last Check:</span>
              <span>{new Date(component.last_check).toLocaleString()}</span>
            </div>
            {component.details && (
              <>
                {component.details.response_time && (
                  <div className="flex justify-between">
                    <span>Response Time:</span>
                    <span>{component.details.response_time}ms</span>
                  </div>
                )}
                {component.details.uptime && (
                  <div className="flex justify-between">
                    <span>Uptime:</span>
                    <span>{component.details.uptime}%</span>
                  </div>
                )}
                {component.details.error_message && (
                  <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-600">
                    <p className="text-xs">{component.details.error_message}</p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default HealthStatusCard;