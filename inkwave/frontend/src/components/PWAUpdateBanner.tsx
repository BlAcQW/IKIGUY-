/**
 * PWA Update Banner Component
 * Shows notification when a new version is available
 */

import { RefreshCw, X } from 'lucide-react';
import { useState } from 'react';
import { usePWA } from '../hooks/usePWA';

export function PWAUpdateBanner() {
  const { hasUpdate, applyUpdate } = usePWA();
  const [dismissed, setDismissed] = useState(false);

  // Don't show if no update or dismissed
  if (!hasUpdate || dismissed) {
    return null;
  }

  const handleUpdate = () => {
    applyUpdate();
  };

  return (
    <div className="fixed top-0 left-0 right-0 z-50 animate-slide-down" role="status" aria-live="polite" aria-atomic="true">
      <div className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-4 py-3 shadow-lg">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
          <div className="flex items-center gap-3 flex-1">
            <RefreshCw className="w-5 h-5 flex-shrink-0" />
            <div>
              <p className="font-medium">New version available!</p>
              <p className="text-sm text-white/90">
                Update now to get the latest features and improvements.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              onClick={handleUpdate}
              className="bg-white text-blue-600 px-4 py-2 rounded-lg font-medium hover:bg-blue-50 transition-colors whitespace-nowrap"
            >
              Update Now
            </button>
            <button
              onClick={() => setDismissed(true)}
              className="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-white/20 rounded-lg transition-colors"
              aria-label="Dismiss update notification"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
