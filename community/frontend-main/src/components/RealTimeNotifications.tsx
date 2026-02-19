import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Bell, CheckCircle, MessageCircle, Trophy, X, Users, Wifi, WifiOff, RotateCcw } from "lucide-react";
import { useWebSocket, Notification } from "@/contexts/WebSocketContext";

interface RealTimeNotificationsProps {
  showConnectionStatus?: boolean;
}

export default function RealTimeNotifications({ showConnectionStatus = false }: RealTimeNotificationsProps) {
  const [showNotifications, setShowNotifications] = useState(false);
  const {
    notifications,
    unreadNotificationCount,
    isConnected,
    isConnecting,
    connectionError,
    markNotificationAsRead,
    clearAllNotifications,
    reconnect
  } = useWebSocket();

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'validation_update':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'submission_update':
        return <Users className="w-5 h-5 text-orange-600" />;
      case 'achievement':
        return <Trophy className="w-5 h-5 text-yellow-600" />;
      case 'chat':
      case 'mention':
        return <MessageCircle className="w-5 h-5 text-blue-600" />;
      case 'system':
        return <Bell className="w-5 h-5 text-purple-600" />;
      default:
        return <Bell className="w-5 h-5 text-gray-600" />;
    }
  };

  const getConnectionIcon = () => {
    if (isConnecting) {
      return <RotateCcw className="w-4 h-4 animate-spin" />;
    }
    return isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />;
  };

  const getConnectionStatus = () => {
    if (isConnecting) return 'Connecting...';
    if (connectionError) return `Error: ${connectionError}`;
    return isConnected ? 'Live' : 'Offline';
  };

  const getConnectionColor = () => {
    if (isConnecting) return 'text-yellow-500';
    if (connectionError) return 'text-red-500';
    return isConnected ? 'text-green-500' : 'text-red-500';
  };

  return (
    <div className="relative">
      {/* Notification Bell */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setShowNotifications(!showNotifications)}
        className="relative"
      >
        <Bell className="w-5 h-5" />
        {unreadNotificationCount > 0 && (
          <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs">
            {unreadNotificationCount > 9 ? '9+' : unreadNotificationCount}
          </Badge>
        )}
      </Button>

      {/* Connection Status Indicator */}
      <div className={`absolute top-1 right-1 w-2 h-2 rounded-full ${
        isConnected ? 'bg-green-400' : isConnecting ? 'bg-yellow-400' : 'bg-red-400'
      }`} />

      {/* Notifications Panel */}
      {showNotifications && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowNotifications(false)}
          />

          {/* Notifications Panel */}
          <Card className="absolute right-0 mt-2 w-96 z-50 max-h-96 overflow-hidden">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="font-semibold">
                Notifications {unreadNotificationCount > 0 && `(${unreadNotificationCount})`}
              </h3>

              <div className="flex items-center space-x-2">
                {notifications.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearAllNotifications}
                  >
                    Clear all
                  </Button>
                )}
                {connectionError && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={reconnect}
                    className="text-orange-600"
                  >
                    <RotateCcw className="w-3 h-3 mr-1" />
                    Retry
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowNotifications(false)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                  <Bell className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
                  <p>No notifications yet</p>
                  <p className="text-sm">We'll notify you of important updates</p>
                </div>
              ) : (
                <div className="divide-y">
                  {notifications.slice(0, 10).map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 hover:bg-accent cursor-pointer transition-colors ${
                        !notification.read ? 'bg-accent/50 border-l-4 border-l-primary' : ''
                      }`}
                      onClick={() => markNotificationAsRead(notification.id)}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 mt-0.5">
                          {getNotificationIcon(notification.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-medium ${
                            !notification.read ? 'font-semibold' : ''
                          }`}>
                            {notification.title}
                          </p>
                          <p className="text-sm text-muted-foreground mt-1">
                            {notification.message}
                          </p>
                          <p className="text-xs text-muted-foreground mt-2">
                            {new Date(notification.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                        {!notification.read && (
                          <div className="w-2 h-2 bg-primary rounded-full flex-shrink-0 mt-2" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Connection Status */}
            <div className="px-4 py-2 bg-muted border-t flex items-center justify-between">
              <div className={`flex items-center space-x-2 text-xs ${getConnectionColor()}`}>
                {getConnectionIcon()}
                <span>{getConnectionStatus()}</span>
              </div>
              {showConnectionStatus && connectionError && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={reconnect}
                  className="text-xs h-6"
                >
                  Reconnect
                </Button>
              )}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}