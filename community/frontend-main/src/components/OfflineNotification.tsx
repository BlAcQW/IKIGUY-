import { useState, useEffect } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Wifi, WifiOff, Upload, RotateCw } from 'lucide-react';
import { isOnline, setupNetworkListeners, getOfflineSubmissions } from '@/utils/pwa';

const OfflineNotification = () => {
  const [online, setOnline] = useState(isOnline());
  const [offlineSubmissions, setOfflineSubmissions] = useState(0);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    // Set up network status listeners
    const handleOnline = () => {
      setOnline(true);
      syncOfflineSubmissions();
    };

    const handleOffline = () => {
      setOnline(false);
    };

    setupNetworkListeners(handleOnline, handleOffline);

    // Check for offline submissions on load
    updateOfflineCount();

    // Set up periodic check for offline submissions
    const interval = setInterval(updateOfflineCount, 30000); // Check every 30 seconds

    return () => {
      clearInterval(interval);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const updateOfflineCount = () => {
    const submissions = getOfflineSubmissions();
    setOfflineSubmissions(submissions.filter(s => !s.synced).length);
  };

  const syncOfflineSubmissions = async () => {
    if (!online || syncing) return;

    setSyncing(true);
    try {
      // Trigger background sync if available
      if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('background-sync-submissions');
      }

      // Update count after sync attempt
      setTimeout(() => {
        updateOfflineCount();
        setSyncing(false);
      }, 2000);
    } catch (error) {
      console.error('Sync failed:', error);
      setSyncing(false);
    }
  };

  if (online && offlineSubmissions === 0) {
    return null; // Don't show anything when online with no pending submissions
  }

  return (
    <div className="fixed top-20 left-4 right-4 z-50 max-w-md mx-auto">
      {!online ? (
        <Alert className="bg-orange-50 border-orange-200">
          <WifiOff className="h-4 w-4 text-orange-600" />
          <AlertDescription className="text-orange-800">
            <div className="flex items-center justify-between">
              <span>You're offline. Submissions will be saved locally.</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.reload()}
                className="ml-2"
              >
                Retry
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      ) : offlineSubmissions > 0 ? (
        <Alert className="bg-blue-50 border-blue-200">
          <Upload className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800">
            <div className="flex items-center justify-between">
              <span>
                {offlineSubmissions} submission{offlineSubmissions !== 1 ? 's' : ''} ready to sync
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={syncOfflineSubmissions}
                disabled={syncing}
                className="ml-2"
              >
                {syncing ? (
                  <>
                    <RotateCw className="h-3 w-3 mr-1 animate-spin" />
                    Syncing...
                  </>
                ) : (
                  <>
                    <Wifi className="h-3 w-3 mr-1" />
                    Sync Now
                  </>
                )}
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
};

export default OfflineNotification;