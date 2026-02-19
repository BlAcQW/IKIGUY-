/**
 * PWA Update Banner Component
 * Shows notification when a new version is available
 */

import { RefreshCw, X, Sparkles } from 'lucide-react';
import { useState, useEffect } from 'react';
import { usePWA } from '../hooks/usePWA';

export default function PWAUpdateBanner() {
  const { hasUpdate, applyUpdate } = usePWA();
  const [dismissed, setDismissed] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  // Reset dismissed state when a new update becomes available
  useEffect(() => {
    if (hasUpdate) {
      setDismissed(false);
    }
  }, [hasUpdate]);

  // Don't show if no update or dismissed
  if (!hasUpdate || dismissed) {
    return null;
  }

  const handleUpdate = () => {
    setIsUpdating(true);
    // Add slight delay for better UX
    setTimeout(() => {
      applyUpdate();
    }, 300);
  };

  return (
    <div
      className="fixed top-0 left-0 right-0 z-[9999] animate-slide-down shadow-2xl"
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="bg-gradient-to-r from-purple-600 via-violet-600 to-blue-600 text-white px-4 py-4 shadow-lg border-b-2 border-white/20">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative">
              <RefreshCw className={`w-6 h-6 flex-shrink-0 ${isUpdating ? 'animate-spin' : ''}`} />
              {!isUpdating && (
                <Sparkles className="w-3 h-3 absolute -top-1 -right-1 text-yellow-300 animate-pulse" />
              )}
            </div>
            <div>
              <p className="font-semibold text-base flex items-center gap-2">
                New Version Available!
                <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full">v1.1</span>
              </p>
              <p className="text-sm text-white/95 mt-0.5">
                Enhanced time picker, bug fixes, and performance improvements are ready.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              onClick={handleUpdate}
              disabled={isUpdating}
              className={`
                bg-white text-purple-600 px-5 py-2.5 rounded-lg font-semibold
                hover:bg-purple-50 transition-all whitespace-nowrap
                shadow-lg hover:shadow-xl transform hover:scale-105
                disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none
                min-w-[120px] flex items-center justify-center gap-2
              `}
            >
              {isUpdating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Updating...
                </>
              ) : (
                'Update Now'
              )}
            </button>
            <button
              onClick={() => setDismissed(true)}
              disabled={isUpdating}
              className="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-white/20 rounded-lg transition-colors disabled:opacity-50"
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
