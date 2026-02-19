/**
 * Custom hook for PWA functionality
 * Handles install prompts, service worker updates, and offline detection
 */

import { useState, useEffect, useCallback } from 'react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

interface PWAState {
  isInstallable: boolean;
  isInstalled: boolean;
  isOffline: boolean;
  hasUpdate: boolean;
}

export function usePWA() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [pwaState, setPwaState] = useState<PWAState>({
    isInstallable: false,
    isInstalled: false,
    isOffline: !navigator.onLine,
    hasUpdate: false,
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
  const promptInstall = useCallback(async () => {
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
  }, [deferredPrompt]);

  // Reload to apply update
  const applyUpdate = useCallback(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then(registration => {
        registration.waiting?.postMessage({ type: 'SKIP_WAITING' });
        window.location.reload();
      });
    }
  }, []);

  return {
    ...pwaState,
    promptInstall,
    applyUpdate,
  };
}
