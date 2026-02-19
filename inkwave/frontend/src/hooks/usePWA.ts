/**
 * Custom hook for PWA functionality
 * Handles install prompts, service worker updates, and offline detection
 */

import { useState, useEffect } from 'react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

interface PWAState {
  isInstallable: boolean;
  isInstalled: boolean;
  isOffline: boolean;
  hasUpdate: boolean;
  cacheStatus: {
    audioFiles: number;
    audioSize: number;
    staticFiles: number;
    staticSize: number;
  } | null;
}

export function usePWA() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [pwaState, setPwaState] = useState<PWAState>({
    isInstallable: false,
    isInstalled: false,
    isOffline: !navigator.onLine,
    hasUpdate: false,
    cacheStatus: null,
  });

  useEffect(() => {
    // Check if already installed
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    setPwaState(prev => ({ ...prev, isInstalled: isStandalone }));

    // Listen for beforeinstallprompt event
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      const promptEvent = e as BeforeInstallPromptEvent;
      setDeferredPrompt(promptEvent);
      setPwaState(prev => ({ ...prev, isInstallable: true }));
      console.log('[PWA] Install prompt available');
    };

    // Listen for app installed event
    const handleAppInstalled = () => {
      console.log('[PWA] App installed');
      setPwaState(prev => ({
        ...prev,
        isInstalled: true,
        isInstallable: false
      }));
      setDeferredPrompt(null);
    };

    // Listen for online/offline events
    const handleOnline = () => {
      console.log('[PWA] Online');
      setPwaState(prev => ({ ...prev, isOffline: false }));
    };

    const handleOffline = () => {
      console.log('[PWA] Offline');
      setPwaState(prev => ({ ...prev, isOffline: true }));
    };

    // Listen for service worker updates (custom event from main.tsx)
    const handleServiceWorkerUpdate = (event: Event) => {
      console.log('[PWA] Update available', event);
      setPwaState(prev => ({ ...prev, hasUpdate: true }));
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('swUpdateAvailable', handleServiceWorkerUpdate);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('swUpdateAvailable', handleServiceWorkerUpdate);
    };
  }, []);

  // Show install prompt
  const promptInstall = async () => {
    if (!deferredPrompt) {
      console.warn('[PWA] Install prompt not available');
      return false;
    }

    try {
      await deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log(`[PWA] User response: ${outcome}`);

      if (outcome === 'accepted') {
        setDeferredPrompt(null);
        setPwaState(prev => ({ ...prev, isInstallable: false }));
        return true;
      }
      return false;
    } catch (error) {
      console.error('[PWA] Install prompt error:', error);
      return false;
    }
  };

  // Reload to apply update
  const applyUpdate = () => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then(registration => {
        registration.waiting?.postMessage({ type: 'SKIP_WAITING' });
        window.location.reload();
      });
    }
  };

  // Get cache status
  const getCacheStatus = async () => {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      const messageChannel = new MessageChannel();

      return new Promise<PWAState['cacheStatus']>((resolve) => {
        messageChannel.port1.onmessage = (event) => {
          const status = event.data;
          setPwaState(prev => ({ ...prev, cacheStatus: status }));
          resolve(status);
        };

        navigator.serviceWorker.controller.postMessage(
          { type: 'GET_CACHE_STATUS' },
          [messageChannel.port2]
        );
      });
    }
    return null;
  };

  // Clear all caches
  const clearCache = async () => {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: 'CLEAR_CACHE' });
      console.log('[PWA] Cache cleared');
    }
  };

  // Check if specific URL is cached
  const isCached = async (url: string): Promise<boolean> => {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      const messageChannel = new MessageChannel();

      return new Promise<boolean>((resolve) => {
        messageChannel.port1.onmessage = (event) => {
          resolve(event.data.cached);
        };

        navigator.serviceWorker.controller.postMessage(
          { type: 'IS_CACHED', url },
          [messageChannel.port2]
        );
      });
    }
    return false;
  };

  // Cache audio file for offline playback
  const cacheAudio = async (url: string, bookId: string) => {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({
        type: 'CACHE_AUDIO',
        url,
        bookId
      });
      console.log('[PWA] Caching audio:', url);
    }
  };

  return {
    ...pwaState,
    promptInstall,
    applyUpdate,
    getCacheStatus,
    clearCache,
    isCached,
    cacheAudio,
  };
}

// Format bytes to human-readable size
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
