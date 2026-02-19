/**
 * PWA Install Prompt Component
 *
 * Displays a prompt to install the app as a PWA.
 * - Shows after 30 seconds on first visit
 * - Can be dismissed for 7 days
 * - Bottom-left position on desktop, full-width on mobile
 */

import { useState, useEffect } from "react";
import { X, Download } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { usePWA } from "@/hooks/usePWA";

const DISMISSED_KEY = "pwa-install-dismissed";
const DISMISS_DURATION = 7 * 24 * 60 * 60 * 1000; // 7 days in milliseconds
const SHOW_DELAY = 30 * 1000; // 30 seconds

export function PWAInstallPrompt() {
  const { isInstallable, isInstalled, promptInstall } = usePWA();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Don't show if already installed or not installable
    if (isInstalled || !isInstallable) {
      return;
    }

    // Check if previously dismissed
    const dismissedTime = localStorage.getItem(DISMISSED_KEY);
    if (dismissedTime) {
      const elapsed = Date.now() - parseInt(dismissedTime, 10);
      if (elapsed < DISMISS_DURATION) {
        return; // Still within dismiss period
      }
    }

    // Show prompt after delay
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, SHOW_DELAY);

    return () => clearTimeout(timer);
  }, [isInstallable, isInstalled]);

  const handleInstall = async () => {
    const success = await promptInstall();
    if (success) {
      setIsVisible(false);
    }
  };

  const handleDismiss = () => {
    localStorage.setItem(DISMISSED_KEY, Date.now().toString());
    setIsVisible(false);
  };

  if (!isVisible) {
    return null;
  }

  return (
    <Card className="fixed bottom-4 left-4 z-50 w-full max-w-sm shadow-lg md:w-96">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Download className="h-5 w-5 text-accent" />
            <div>
              <CardTitle className="text-base">Install Diaserve Properties</CardTitle>
              <CardDescription className="text-xs">Add to your home screen</CardDescription>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDismiss}
            className="h-6 w-6 -mr-2 -mt-1"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pb-4">
        <p className="text-sm text-muted-foreground">
          Install our app for faster access, offline support, and a native experience.
        </p>

        <div className="flex gap-2">
          <Button onClick={handleInstall} className="flex-1" size="sm">
            Install App
          </Button>
          <Button onClick={handleDismiss} variant="outline" size="sm">
            Not Now
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
