/**
 * useOfflineStatus Hook
 * Tracks online/offline status and service worker messages
 */

import { useState, useEffect, useCallback } from 'react';

interface OfflineStatus {
  isOnline: boolean;
  wasOffline: boolean; // True if user was recently offline
}

export function useOfflineStatus() {
  const [status, setStatus] = useState<OfflineStatus>({
    isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
    wasOffline: false,
  });

  const handleOnline = useCallback(() => {
    setStatus((prev) => ({
      isOnline: true,
      wasOffline: !prev.isOnline, // Mark if coming back online
    }));
  }, []);

  const handleOffline = useCallback(() => {
    setStatus({
      isOnline: false,
      wasOffline: false,
    });
  }, []);

  // Clear wasOffline flag after a delay
  useEffect(() => {
    if (status.wasOffline) {
      const timer = setTimeout(() => {
        setStatus((prev) => ({ ...prev, wasOffline: false }));
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [status.wasOffline]);

  // Listen for browser online/offline events
  useEffect(() => {
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [handleOnline, handleOffline]);

  // Listen for service worker messages
  useEffect(() => {
    const handleSWMessage = (event: MessageEvent) => {
      if (event.data?.type === 'ONLINE') {
        handleOnline();
      } else if (event.data?.type === 'OFFLINE') {
        handleOffline();
      }
    };

    navigator.serviceWorker?.addEventListener('message', handleSWMessage);

    return () => {
      navigator.serviceWorker?.removeEventListener('message', handleSWMessage);
    };
  }, [handleOnline, handleOffline]);

  return status;
}
