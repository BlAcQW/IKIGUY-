import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';
import { toast } from 'sonner';
import { useBackendAuth } from './BackendAuthContext';

export interface Notification {
  id: string;
  type: 'validation_update' | 'submission_update' | 'achievement' | 'chat' | 'system' | 'mention';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  data?: any;
  user_id?: string;
  target_user_id?: string;
}

export interface ChatMessage {
  id: string;
  channel_id: string;
  channel_name: string;
  user_id: string;
  username: string;
  user_avatar?: string;
  message: string;
  timestamp: string;
  message_type: 'text' | 'file' | 'system';
  reply_to?: string;
}

export interface UserPresence {
  user_id: string;
  username: string;
  status: 'online' | 'away' | 'offline';
  last_seen: string;
  current_channel?: string;
}

interface WebSocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  isConnecting: boolean;
  connectionError: string | null;
  notifications: Notification[];
  unreadNotificationCount: number;
  onlineUsers: UserPresence[];

  // Notification methods
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markNotificationAsRead: (id: string) => void;
  clearAllNotifications: () => void;

  // Chat methods
  joinChannel: (channelId: string) => void;
  leaveChannel: (channelId: string) => void;
  sendMessage: (channelId: string, message: string, replyTo?: string) => void;

  // Presence methods
  updateUserStatus: (status: 'online' | 'away' | 'offline') => void;

  // Connection methods
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const { user, tokens } = useBackendAuth();
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<UserPresence[]>([]);

  const WS_URL = import.meta.env.VITE_WS_URL || 'https://language-community-api.ailabsafrica.com';

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toISOString(),
      read: false
    };

    setNotifications(prev => [newNotification, ...prev.slice(0, 49)]);

    // Show toast notification if it's for the current user
    if (!notification.target_user_id || notification.target_user_id === user?.id) {
      toast(notification.title, {
        description: notification.message,
        duration: 5000,
      });
    }
  }, [user?.id]);

  const markNotificationAsRead = useCallback((id: string) => {
    setNotifications(prev =>
      prev.map(notif => notif.id === id ? { ...notif, read: true } : notif)
    );
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const connect = useCallback(() => {
    if (!user || socket) return;

    setIsConnecting(true);
    setConnectionError(null);

    const newSocket = io(WS_URL, {
      auth: {
        userId: user.id,
        token: tokens?.access_token || 'demo-token'
      },
      transports: ['websocket', 'polling'],
      timeout: 10000,
      forceNew: true
    });

    // Connection events
    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setIsConnecting(false);
      setConnectionError(null);

      // Join user to their personal notification room
      newSocket.emit('join_user_room', { user_id: user.id });
    });

    newSocket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setIsConnected(false);
      setConnectionError(reason);
    });

    newSocket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setIsConnecting(false);
      setConnectionError(error.message);
    });

    // Notification events
    newSocket.on('notification', (notification: Notification) => {
      addNotification(notification);
    });

    newSocket.on('batch_notifications', (notificationBatch: Notification[]) => {
      notificationBatch.forEach(notification => addNotification(notification));
    });

    // Chat events
    newSocket.on('new_message', (message: ChatMessage) => {
      // Handle new chat messages - could trigger notifications for mentions
      if (message.message.includes(`@${user.email}`) || message.message.includes(`@${user.id}`)) {
        addNotification({
          type: 'mention',
          title: 'You were mentioned',
          message: `${message.username} mentioned you in #${message.channel_name}`,
          data: { message, channel_id: message.channel_id }
        });
      }
    });

    // Presence events
    newSocket.on('user_presence_update', (presenceUpdate: UserPresence) => {
      setOnlineUsers(prev => {
        const filtered = prev.filter(u => u.user_id !== presenceUpdate.user_id);
        if (presenceUpdate.status !== 'offline') {
          return [...filtered, presenceUpdate];
        }
        return filtered;
      });
    });

    newSocket.on('online_users', (users: UserPresence[]) => {
      setOnlineUsers(users);
    });

    // Contribution events
    newSocket.on('contribution_validated', (data: any) => {
      if (data.contributor_id === user.id) {
        addNotification({
          type: 'validation_update',
          title: 'Contribution Validated! 🎉',
          message: `Your ${data.language_name} contribution received a quality score of ${data.quality_score}/5`,
          data
        });
      }
    });

    newSocket.on('contribution_submitted', (data: any) => {
      // Notify community about new contributions
      addNotification({
        type: 'submission_update',
        title: 'New Contribution',
        message: `${data.contributor_name} contributed "${data.title}" in ${data.language_name}`,
        data
      });
    });

    newSocket.on('achievement_unlocked', (data: any) => {
      if (data.user_id === user.id) {
        addNotification({
          type: 'achievement',
          title: 'Achievement Unlocked! 🏆',
          message: `You earned the "${data.achievement_title}" badge!`,
          data
        });
      }
    });

    // System events
    newSocket.on('system_announcement', (data: any) => {
      addNotification({
        type: 'system',
        title: 'System Announcement',
        message: data.message,
        data
      });
    });

    setSocket(newSocket);
  }, [user, socket, WS_URL, addNotification]);

  const disconnect = useCallback(() => {
    if (socket) {
      socket.disconnect();
      setSocket(null);
      setIsConnected(false);
      setOnlineUsers([]);
    }
  }, [socket]);

  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(() => {
      connect();
    }, 1000);
  }, [disconnect, connect]);

  const joinChannel = useCallback((channelId: string) => {
    if (socket && isConnected) {
      socket.emit('join_channel', { channel_id: channelId });
    }
  }, [socket, isConnected]);

  const leaveChannel = useCallback((channelId: string) => {
    if (socket && isConnected) {
      socket.emit('leave_channel', { channel_id: channelId });
    }
  }, [socket, isConnected]);

  const sendMessage = useCallback((channelId: string, message: string, replyTo?: string) => {
    if (socket && isConnected) {
      socket.emit('send_message', {
        channel_id: channelId,
        message,
        reply_to: replyTo,
        timestamp: new Date().toISOString()
      });
    }
  }, [socket, isConnected]);

  const updateUserStatus = useCallback((status: 'online' | 'away' | 'offline') => {
    if (socket && isConnected) {
      socket.emit('update_status', { status });
    }
  }, [socket, isConnected]);

  // Auto-connect when user is available
  useEffect(() => {
    if (user && !socket && !isConnecting) {
      connect();
    }
  }, [user, socket, isConnecting, connect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, [socket]);

  // Handle page visibility changes for presence
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        updateUserStatus('away');
      } else {
        updateUserStatus('online');
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [updateUserStatus]);

  const unreadNotificationCount = notifications.filter(n => !n.read).length;

  const value: WebSocketContextType = {
    socket,
    isConnected,
    isConnecting,
    connectionError,
    notifications,
    unreadNotificationCount,
    onlineUsers,
    addNotification,
    markNotificationAsRead,
    clearAllNotifications,
    joinChannel,
    leaveChannel,
    sendMessage,
    updateUserStatus,
    connect,
    disconnect,
    reconnect
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};