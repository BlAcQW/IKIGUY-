/**
 * Offline Indicator Component
 * Shows a banner when the app is offline
 */

import { WifiOff, Wifi } from 'lucide-react';
import { usePWA } from '../hooks/usePWA';
import { useEffect, useState } from 'react';

export function OfflineIndicator() {
  const { isOffline } = usePWA();
  const [show, setShow] = useState(false);
  const [wasOffline, setWasOffline] = useState(false);

  useEffect(() => {
    if (isOffline) {
      setShow(true);
      setWasOffline(true);
    } else if (wasOffline) {
      // Show "back online" message briefly
      setShow(true);
      setTimeout(() => {
        setShow(false);
        setWasOffline(false);
      }, 3000);
    }
  }, [isOffline, wasOffline]);

  if (!show) {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 pointer-events-none">
      <div
        className={`${
          isOffline
            ? 'bg-gradient-to-r from-orange-600 to-red-600'
            : 'bg-gradient-to-r from-green-600 to-emerald-600'
        } text-white px-4 py-2 shadow-lg transition-all duration-300`}
      >
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-2">
          {isOffline ? (
            <>
              <WifiOff className="w-4 h-4" />
              <span className="text-sm font-medium">
                You're offline - some features may be limited
              </span>
            </>
          ) : (
            <>
              <Wifi className="w-4 h-4" />
              <span className="text-sm font-medium">Back online!</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
