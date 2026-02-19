/**
 * PWA utility functions for AfriLang Community Platform.
 *
 * Handles service worker registration, offline functionality, and push notifications.
 */

// Service Worker Registration
export const registerServiceWorker = async (): Promise<void> => {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });

      console.log('Service Worker registered successfully:', registration);

      // Handle service worker updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker is available
              showUpdateAvailable();
            }
          });
        }
      });

    } catch (error) {
      console.error('Service Worker registration failed:', error);
    }
  }
};

// Show update notification
const showUpdateAvailable = (): void => {
  if (confirm('A new version of AfriLang Community is available. Reload to update?')) {
    window.location.reload();
  }
};

// Offline Submission Storage
interface OfflineSubmission {
  id: string;
  type: 'audio' | 'text' | 'translation';
  data: any;
  timestamp: number;
  synced: boolean;
}

export const storeOfflineSubmission = async (submissionData: any): Promise<void> => {
  const submission: OfflineSubmission = {
    id: crypto.randomUUID(),
    type: submissionData.type,
    data: submissionData,
    timestamp: Date.now(),
    synced: false
  };

  const stored = getOfflineSubmissions();
  stored.push(submission);
  localStorage.setItem('offline-submissions', JSON.stringify(stored));

  // Register for background sync if available
  if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
    try {
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register('background-sync-submissions');
    } catch (error) {
      console.error('Background sync registration failed:', error);
    }
  }
};

export const getOfflineSubmissions = (): OfflineSubmission[] => {
  const stored = localStorage.getItem('offline-submissions');
  return stored ? JSON.parse(stored) : [];
};

export const removeOfflineSubmission = (id: string): void => {
  const stored = getOfflineSubmissions();
  const filtered = stored.filter(submission => submission.id !== id);
  localStorage.setItem('offline-submissions', JSON.stringify(filtered));
};

// Network Status Detection
export const isOnline = (): boolean => {
  return navigator.onLine;
};

export const setupNetworkListeners = (onOnline: () => void, onOffline: () => void): void => {
  window.addEventListener('online', onOnline);
  window.addEventListener('offline', onOffline);
};

// Push Notifications
export const requestNotificationPermission = async (): Promise<boolean> => {
  if (!('Notification' in window)) {
    console.warn('This browser does not support notifications');
    return false;
  }

  if (Notification.permission === 'granted') {
    return true;
  }

  if (Notification.permission === 'denied') {
    return false;
  }

  const permission = await Notification.requestPermission();
  return permission === 'granted';
};

export const subscribeToPushNotifications = async (): Promise<PushSubscription | null> => {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.warn('Push messaging is not supported');
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.ready;

    // Check if already subscribed
    let subscription = await registration.pushManager.getSubscription();

    if (!subscription) {
      // Create new subscription
      const applicationServerKey = urlBase64ToUint8Array(
        'BH7qIGbNhJV-FdGFEb8iO8cPJZIKOGwqQdx_hPCE9NLEJKnV8F-VUJgJLLLX1vD3nFl2V4nJqQdFy6IzFCl-Z2o'
      );

      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey
      });
    }

    return subscription;
  } catch (error) {
    console.error('Failed to subscribe to push notifications:', error);
    return null;
  }
};

// Utility function to convert VAPID key
const urlBase64ToUint8Array = (base64String: string): Uint8Array => {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
};

// Install Prompt Handling
export const setupInstallPrompt = (): void => {
  let deferredPrompt: any;

  window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent Chrome 67 and earlier from automatically showing the prompt
    e.preventDefault();
    deferredPrompt = e;
    showInstallButton(deferredPrompt);
  });

  window.addEventListener('appinstalled', () => {
    console.log('PWA was installed');
    hideInstallButton();
  });
};

const showInstallButton = (deferredPrompt: any): void => {
  // Create install button if it doesn't exist
  let installButton = document.getElementById('install-button');
  if (!installButton) {
    installButton = document.createElement('button');
    installButton.id = 'install-button';
    installButton.textContent = 'Install App';
    installButton.className = 'fixed bottom-4 right-4 bg-primary text-primary-foreground px-4 py-2 rounded-lg shadow-lg z-50';
    document.body.appendChild(installButton);
  }

  installButton.style.display = 'block';
  installButton.onclick = async () => {
    hideInstallButton();
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`User response to the install prompt: ${outcome}`);
    deferredPrompt = null;
  };
};

const hideInstallButton = (): void => {
  const installButton = document.getElementById('install-button');
  if (installButton) {
    installButton.style.display = 'none';
  }
};

// Cache Management
export const clearCache = async (): Promise<void> => {
  if ('caches' in window) {
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(cacheName => caches.delete(cacheName))
    );
    console.log('All caches cleared');
  }
};

// Device Capabilities
export const getDeviceCapabilities = () => {
  return {
    hasCamera: 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices,
    hasMicrophone: 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices,
    hasGyroscope: 'DeviceOrientationEvent' in window,
    hasAccelerometer: 'DeviceMotionEvent' in window,
    hasPushNotifications: 'PushManager' in window,
    hasServiceWorker: 'serviceWorker' in navigator,
    hasBackgroundSync: 'serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype,
    isStandalone: window.matchMedia('(display-mode: standalone)').matches,
    isMobile: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  };
};