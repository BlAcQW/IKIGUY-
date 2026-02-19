import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { API_ENDPOINTS } from '@/config/api-config';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  RefreshCw,
  Bell,
  BellOff,
} from 'lucide-react';

interface SystemAlert {
  id: string;
  severity: 'info' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
}

interface AlertsPanelProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const AlertsPanel: React.FC<AlertsPanelProps> = ({
  autoRefresh = true,
  refreshInterval = 30000,
}) => {
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  const fetchAlerts = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.asterisk.alerts);
      if (!response.ok) throw new Error('Failed to fetch alerts');
      const data = await response.json();

      // Check for new critical alerts
      if (notificationsEnabled && data.alerts.length > alerts.length) {
        const newAlerts = data.alerts.filter(
          (alert: SystemAlert) => alert.severity === 'error' &&
          !alerts.find(a => a.id === alert.id)
        );

        // Show browser notification for critical alerts
        if (newAlerts.length > 0 && 'Notification' in window && Notification.permission === 'granted') {
          new Notification('Asterisk Alert', {
            body: newAlerts[0].message,
            icon: '/favicon.ico',
          });
        }
      }

      setAlerts(data.alerts);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();

    if (autoRefresh) {
      const interval = setInterval(fetchAlerts, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  // Request notification permission
  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission();
    }
  };

  useEffect(() => {
    if (notificationsEnabled) {
      requestNotificationPermission();
    }
  }, [notificationsEnabled]);

  const getSeverityIcon = (severity: SystemAlert['severity']) => {
    switch (severity) {
      case 'error':
        return <AlertCircle className="h-4 w-4" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4" />;
      case 'info':
        return <Info className="h-4 w-4" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const getSeverityVariant = (severity: SystemAlert['severity']) => {
    switch (severity) {
      case 'error':
        return 'destructive';
      case 'warning':
        return 'default';
      case 'info':
        return 'default';
      default:
        return 'default';
    }
  };

  const getSeverityColor = (severity: SystemAlert['severity']) => {
    switch (severity) {
      case 'error':
        return 'text-red-500';
      case 'warning':
        return 'text-yellow-500';
      case 'info':
        return 'text-blue-500';
      default:
        return 'text-gray-500';
    }
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              System Alerts
            </CardTitle>
            <CardDescription>
              Active warnings and notifications
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setNotificationsEnabled(!notificationsEnabled)}
            >
              {notificationsEnabled ? (
                <Bell className="h-4 w-4" />
              ) : (
                <BellOff className="h-4 w-4" />
              )}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchAlerts}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading && alerts.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500 opacity-50" />
            <p className="text-sm font-medium">All systems operational</p>
            <p className="text-xs text-muted-foreground mt-1">
              No active alerts or warnings
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <Alert key={alert.id} variant={getSeverityVariant(alert.severity)}>
                <div className="flex items-start gap-3">
                  <div className={getSeverityColor(alert.severity)}>
                    {getSeverityIcon(alert.severity)}
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-start justify-between">
                      <AlertTitle className="text-sm font-semibold">
                        {alert.title}
                      </AlertTitle>
                      <Badge variant="outline" className="ml-2">
                        {alert.severity.toUpperCase()}
                      </Badge>
                    </div>
                    <AlertDescription className="text-sm">
                      {alert.message}
                    </AlertDescription>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatTimestamp(alert.timestamp)}
                    </p>
                  </div>
                </div>
              </Alert>
            ))}
          </div>
        )}

        <p className="text-xs text-muted-foreground text-center mt-4">
          Last checked: {lastRefresh.toLocaleTimeString()}
        </p>
      </CardContent>
    </Card>
  );
};
