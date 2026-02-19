/**
 * Offline Indicator Component
 *
 * Displays a subtle offline status indicator.
 * - Small icon with "Offline" text
 * - Bottom-right corner on mobile
 * - Header integration on desktop
 * - Only visible when offline
 */

import { CloudOff } from "lucide-react";
import { usePWA } from "@/hooks/usePWA";

export function OfflineIndicator() {
  const { isOffline } = usePWA();

  if (!isOffline) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-40 lg:hidden">
      <div className="flex items-center gap-2 rounded-full bg-muted px-3 py-2 text-sm shadow-md">
        <CloudOff className="h-4 w-4 text-muted-foreground" />
        <span className="text-muted-foreground">Offline</span>
      </div>
    </div>
  );
}

/**
 * Offline Indicator for Header (Desktop)
 *
 * Inline version for use in the Header component on desktop.
 */
export function OfflineIndicatorHeader() {
  const { isOffline } = usePWA();

  if (!isOffline) {
    return null;
  }

  return (
    <div className="hidden lg:flex items-center gap-2 text-sm text-muted-foreground">
      <CloudOff className="h-4 w-4" />
      <span>Offline</span>
    </div>
  );
}
