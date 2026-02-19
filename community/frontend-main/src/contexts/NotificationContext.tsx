import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { toast } from 'sonner';

export type NotificationType = 'success' | 'info' | 'warning' | 'error' | 'loading' | 'achievement';

export interface AppNotification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  duration?: number;
  persistent?: boolean;
  timestamp: Date;
  action?: {
    label: string;
    onClick: () => void;
  };
  icon?: React.ReactNode;
  data?: any;
}

interface NotificationContextType {
  notifications: AppNotification[];
  showNotification: (notification: Omit<AppNotification, 'id' | 'timestamp'>) => string;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
  showSuccess: (title: string, message?: string, options?: Partial<AppNotification>) => string;
  showError: (title: string, message?: string, options?: Partial<AppNotification>) => string;
  showWarning: (title: string, message?: string, options?: Partial<AppNotification>) => string;
  showInfo: (title: string, message?: string, options?: Partial<AppNotification>) => string;
  showLoading: (title: string, message?: string, options?: Partial<AppNotification>) => string;
  showAchievement: (title: string, message?: string, options?: Partial<AppNotification>) => string;
  updateNotification: (id: string, updates: Partial<AppNotification>) => void;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);

  const generateId = () => Date.now().toString() + Math.random().toString(36).substr(2, 9);

  const showNotification = useCallback((notificationData: Omit<AppNotification, 'id' | 'timestamp'>) => {
    const notification: AppNotification = {
      ...notificationData,
      id: generateId(),
      timestamp: new Date(),
      duration: notificationData.duration || getDefaultDuration(notificationData.type),
    };

    setNotifications(prev => [notification, ...prev.slice(0, 99)]); // Keep max 100 notifications

    // Show toast
    showToast(notification);

    // Auto-remove non-persistent notifications
    if (!notification.persistent && notification.duration && notification.duration > 0) {
      setTimeout(() => {
        removeNotification(notification.id);
      }, notification.duration);
    }

    return notification.id;
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const updateNotification = useCallback((id: string, updates: Partial<AppNotification>) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id ? { ...notification, ...updates } : notification
      )
    );
  }, []);

  const getDefaultDuration = (type: NotificationType): number => {
    switch (type) {
      case 'success':
        return 4000;
      case 'info':
        return 5000;
      case 'warning':
        return 6000;
      case 'error':
        return 8000;
      case 'loading':
        return 0; // Persistent until manually dismissed
      case 'achievement':
        return 7000;
      default:
        return 5000;
    }
  };

  const showToast = (notification: AppNotification) => {
    const toastOptions = {
      duration: notification.duration || undefined,
      action: notification.action ? {
        label: notification.action.label,
        onClick: notification.action.onClick,
      } : undefined,
    };

    switch (notification.type) {
      case 'success':
        toast.success(notification.title, {
          description: notification.message,
          ...toastOptions,
        });
        break;
      case 'error':
        toast.error(notification.title, {
          description: notification.message,
          ...toastOptions,
        });
        break;
      case 'warning':
        toast.warning(notification.title, {
          description: notification.message,
          ...toastOptions,
        });
        break;
      case 'info':
        toast.info ? toast.info(notification.title, {
          description: notification.message,
          ...toastOptions,
        }) : toast(notification.title, {
          description: notification.message,
          ...toastOptions,
        });
        break;
      case 'loading':
        toast.loading(notification.title, {
          description: notification.message,
          ...toastOptions,
        });
        break;
      case 'achievement':
        toast.success(`🏆 ${notification.title}`, {
          description: notification.message,
          ...toastOptions,
        });
        break;
      default:
        toast(notification.title, {
          description: notification.message,
          ...toastOptions,
        });
    }
  };

  // Helper methods for common notification types
  const showSuccess = useCallback((title: string, message = '', options?: Partial<AppNotification>) => {
    return showNotification({
      type: 'success',
      title,
      message,
      ...options,
    });
  }, [showNotification]);

  const showError = useCallback((title: string, message = '', options?: Partial<AppNotification>) => {
    return showNotification({
      type: 'error',
      title,
      message,
      ...options,
    });
  }, [showNotification]);

  const showWarning = useCallback((title: string, message = '', options?: Partial<AppNotification>) => {
    return showNotification({
      type: 'warning',
      title,
      message,
      ...options,
    });
  }, [showNotification]);

  const showInfo = useCallback((title: string, message = '', options?: Partial<AppNotification>) => {
    return showNotification({
      type: 'info',
      title,
      message,
      ...options,
    });
  }, [showNotification]);

  const showLoading = useCallback((title: string, message = '', options?: Partial<AppNotification>) => {
    return showNotification({
      type: 'loading',
      title,
      message,
      persistent: true,
      ...options,
    });
  }, [showNotification]);

  const showAchievement = useCallback((title: string, message = '', options?: Partial<AppNotification>) => {
    return showNotification({
      type: 'achievement',
      title,
      message,
      duration: 7000,
      ...options,
    });
  }, [showNotification]);

  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () => {
      showSuccess('Connection restored', 'You are back online');
    };

    const handleOffline = () => {
      showWarning('Connection lost', 'You are currently offline');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [showSuccess, showWarning]);

  // Handle visibility change to pause/resume notifications
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden, you might want to queue notifications
      } else {
        // Page is visible, show queued notifications
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  const value: NotificationContextType = {
    notifications,
    showNotification,
    removeNotification,
    clearAllNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showLoading,
    showAchievement,
    updateNotification,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};