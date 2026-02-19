import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  ExternalLink,
  RefreshCw,
  XCircle,
  Zap
} from 'lucide-react';

interface ActivityEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  component: string;
  message: string;
  details?: any;
}

interface ActivityLogProps {
  activities: ActivityEntry[];
  isLoading: boolean;
  maxHeight?: string;
  showTimestamp?: boolean;
}

const ActivityLog: React.FC<ActivityLogProps> = ({
  activities,
  isLoading,
  maxHeight = "300px",
  showTimestamp = true
}) => {
  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'info':
      default:
        return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level.toLowerCase()) {
      case 'success':
        return <CheckCircle className="h-3 w-3" />;
      case 'warning':
        return <AlertTriangle className="h-3 w-3" />;
      case 'error':
        return <XCircle className="h-3 w-3" />;
      case 'info':
      default:
        return <Activity className="h-3 w-3" />;
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <CardTitle>Activity Log</CardTitle>
          </div>
          <CardDescription>Loading recent activity...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center">
              <Clock className="h-4 w-4 mr-2" />
              Activity Log
            </CardTitle>
            <CardDescription>
              Real-time automation activity and events
            </CardDescription>
          </div>
          <Badge variant="outline">
            {activities.length} entries
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-full" style={{ maxHeight }}>
          {activities.length > 0 ? (
            <div className="space-y-3">
              {activities.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className={`p-1 rounded-full ${getLevelColor(activity.level).replace('text-', 'bg-').replace('bg-', 'bg-opacity-20 text-')}`}>
                    {getLevelIcon(activity.level)}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-sm">{activity.component}</span>
                        <Badge
                          variant="outline"
                          className={`text-xs ${getLevelColor(activity.level)}`}
                        >
                          {activity.level.toUpperCase()}
                        </Badge>
                      </div>
                      {showTimestamp && (
                        <span className="text-xs text-gray-600">
                          {new Date(activity.timestamp).toLocaleTimeString()}
                        </span>
                      )}
                    </div>

                    <p className="text-sm text-gray-700 mt-1">
                      {activity.message}
                    </p>

                    {activity.details && (
                      <div className="mt-2 p-2 bg-gray-50 border rounded text-xs">
                        {typeof activity.details === 'string' ? (
                          <p>{activity.details}</p>
                        ) : (
                          <pre className="whitespace-pre-wrap">
                            {JSON.stringify(activity.details, null, 2)}
                          </pre>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Activity className="h-16 w-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-600">No recent activity</p>
              <p className="text-sm text-gray-600 mt-1">
                Activity will appear here when automation components perform actions
              </p>
            </div>
          )}
        </ScrollArea>

        {activities.length > 0 && (
          <div className="mt-4 pt-3 border-t flex items-center justify-between text-sm text-gray-600">
            <span>Showing latest {activities.length} activities</span>
            <button
              className="flex items-center hover:text-foreground transition-colors"
              onClick={() => window.open('/logs', '_blank')}
            >
              View all logs
              <ExternalLink className="h-3 w-3 ml-1" />
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ActivityLog;