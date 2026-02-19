/**
 * PWA Update Banner Component
 *
 * Displays a banner when a new version of the app is available.
 * - Appears at the top of the screen
 * - Allows user to update immediately
 * - Uses orange gradient background
 */

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePWA } from "@/hooks/usePWA";

export function PWAUpdateBanner() {
  const { hasUpdate, applyUpdate } = usePWA();

  if (!hasUpdate) {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-accent to-orange-600 text-white shadow-lg">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <RefreshCw className="h-5 w-5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium">New version available!</p>
              <p className="text-xs text-white/90 hidden sm:block">
                Click update to get the latest features and improvements
              </p>
            </div>
          </div>

          <Button
            onClick={applyUpdate}
            variant="secondary"
            size="sm"
            className="flex-shrink-0"
          >
            Update Now
          </Button>
        </div>
      </div>
    </div>
  );
}
