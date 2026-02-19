import { useEffect, useState } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';

interface ServiceWorkerRegistrationProps {
  children: React.ReactNode;
}

export default function ServiceWorkerRegistration({ children }: ServiceWorkerRegistrationProps) {
  const [isUpdateAvailable, setIsUpdateAvailable] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      registerServiceWorker();
    }
  }, []);

  const registerServiceWorker = async () => {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      });

      // Handle service worker updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              setIsUpdateAvailable(true);
              toast({
                title: "Update Available",
                description: "A new version of the app is available. Click to update.",
                action: (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={updateServiceWorker}
                    disabled={isUpdating}
                  >
                    {isUpdating ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Updating...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Update Now
                      </>
                    )}
                  </Button>
                ),
              });
            }
          });
        }
      });

      // Handle service worker success
      registration.addEventListener('success', () => {
        console.log('Service Worker registered successfully');
        toast({
          title: "App Ready",
          description: "The app is now available offline",
          icon: <CheckCircle className="h-4 w-4 text-green-500" />,
        });
      });

      // Handle service worker errors
      registration.addEventListener('error', (error) => {
        console.error('Service Worker registration failed:', error);
        toast({
          title: "Service Worker Error",
          description: "Failed to register service worker",
          variant: "destructive",
          icon: <AlertCircle className="h-4 w-4" />,
        });
      });

    } catch (error) {
      console.error('Service Worker registration failed:', error);
    }
  };

  const updateServiceWorker = async () => {
    setIsUpdating(true);
    
    try {
      const registration = await navigator.serviceWorker.getRegistration();
      if (registration && registration.waiting) {
        // Send message to service worker to skip waiting
        registration.waiting.postMessage({ type: 'SKIP_WAITING' });
        
        // Reload the page after a short delay
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      }
    } catch (error) {
      console.error('Failed to update service worker:', error);
      setIsUpdating(false);
      toast({
        title: "Update Failed",
        description: "Failed to update the app. Please refresh manually.",
        variant: "destructive",
      });
    }
  };

  // Listen for service worker controller change
  useEffect(() => {
    const handleControllerChange = () => {
      if (navigator.serviceWorker.controller) {
        setIsUpdateAvailable(false);
        toast({
          title: "App Updated",
          description: "The app has been updated successfully",
          icon: <CheckCircle className="h-4 w-4 text-green-500" />,
        });
      }
    };

    navigator.serviceWorker.addEventListener('controllerchange', handleControllerChange);
    
    return () => {
      navigator.serviceWorker.removeEventListener('controllerchange', handleControllerChange);
    };
  }, [toast]);

  return <>{children}</>;
}

// Hook to check if app is online/offline
export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

