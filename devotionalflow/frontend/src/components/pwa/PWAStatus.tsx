/**
 * PWA Status Checker - Debug and Install Helper
 * Shows PWA installation status and provides browser-specific instructions
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, X, CheckCircle, Info, Chrome, Globe } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface PWAStatusInfo {
  isInstalled: boolean;
  isInstallable: boolean;
  browser: string;
  supportsInstallPrompt: boolean;
  serviceWorkerStatus: string;
}

export function PWAStatus() {
  const [showDialog, setShowDialog] = useState(false);
  const [status, setStatus] = useState<PWAStatusInfo>({
    isInstalled: false,
    isInstallable: false,
    browser: 'unknown',
    supportsInstallPrompt: false,
    serviceWorkerStatus: 'checking',
  });

  useEffect(() => {
    checkPWAStatus();
  }, []);

  const checkPWAStatus = async () => {
    // Check if installed
    const isInstalled = window.matchMedia('(display-mode: standalone)').matches ||
      (window.navigator as any).standalone === true;

    // Detect browser
    const userAgent = navigator.userAgent.toLowerCase();
    let browser = 'unknown';
    if (userAgent.includes('firefox')) browser = 'firefox';
    else if (userAgent.includes('chrome') && !userAgent.includes('edg')) browser = 'chrome';
    else if (userAgent.includes('edg')) browser = 'edge';
    else if (userAgent.includes('safari') && !userAgent.includes('chrome')) browser = 'safari';

    // Check service worker
    let swStatus = 'not-supported';
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.getRegistration();
        swStatus = registration ? 'active' : 'not-registered';
      } catch (e) {
        swStatus = 'error';
      }
    }

    // Check if supports install prompt
    const supportsPrompt = browser === 'chrome' || browser === 'edge';

    setStatus({
      isInstalled,
      isInstallable: !isInstalled,
      browser,
      supportsInstallPrompt: supportsPrompt,
      serviceWorkerStatus: swStatus,
    });
  };

  const getInstallInstructions = () => {
    if (status.isInstalled) {
      return (
        <div className="space-y-3 text-sm">
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <CheckCircle className="w-5 h-5" />
            <p className="font-medium">App is installed!</p>
          </div>
          <p className="text-muted-foreground">
            You're running FreshManna as an installed app. Updates will be available automatically.
          </p>
        </div>
      );
    }

    switch (status.browser) {
      case 'firefox':
        return (
          <div className="space-y-4 text-sm">
            <div className="flex items-start gap-2">
              <Info className="w-5 h-5 text-primary shrink-0 mt-0.5" />
              <div>
                <p className="font-medium mb-2">Firefox Desktop - Manual Installation:</p>
                <ol className="list-decimal list-inside space-y-2 text-muted-foreground ml-1">
                  <li>Click the browser menu (☰) in the top-right</li>
                  <li>Select "More Tools" → "Page Actions"</li>
                  <li>Look for "Install FreshManna" or similar option</li>
                </ol>
              </div>
            </div>
            <div className="bg-muted/50 p-3 rounded-lg">
              <p className="text-xs text-muted-foreground">
                <strong>Note:</strong> Firefox on Android supports PWA installation through the browser menu → "Install" option.
                Desktop installation support varies by version.
              </p>
            </div>
          </div>
        );

      case 'chrome':
      case 'edge':
        return (
          <div className="space-y-3 text-sm">
            <div className="flex items-start gap-2">
              <Chrome className="w-5 h-5 text-primary shrink-0 mt-0.5" />
              <div>
                <p className="font-medium mb-2">{status.browser === 'chrome' ? 'Chrome' : 'Edge'} Installation:</p>
                <p className="text-muted-foreground">
                  Look for an install prompt or click the install icon (⊕) in the address bar.
                </p>
              </div>
            </div>
          </div>
        );

      case 'safari':
        return (
          <div className="space-y-3 text-sm">
            <div className="flex items-start gap-2">
              <Globe className="w-5 h-5 text-primary shrink-0 mt-0.5" />
              <div>
                <p className="font-medium mb-2">Safari - Add to Home Screen:</p>
                <ol className="list-decimal list-inside space-y-2 text-muted-foreground ml-1">
                  <li>Tap the Share button (⎙) at the bottom</li>
                  <li>Scroll down and tap "Add to Home Screen"</li>
                  <li>Tap "Add" to confirm</li>
                </ol>
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div className="space-y-3 text-sm text-muted-foreground">
            <p>Your browser may support PWA installation. Check your browser menu for an "Install" option.</p>
          </div>
        );
    }
  };

  return (
    <>
      {/* Floating install button (only show if not installed and not Chrome/Edge which have native prompts) */}
      {!status.isInstalled && !status.supportsInstallPrompt && (
        <AnimatePresence>
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            onClick={() => setShowDialog(true)}
            className="fixed bottom-20 right-4 z-40 w-12 h-12 bg-primary hover:bg-primary/90 text-primary-foreground rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-110"
            title="Install App"
          >
            <Download className="w-5 h-5" />
          </motion.button>
        </AnimatePresence>
      )}

      {/* Install Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Install FreshManna</DialogTitle>
            <DialogDescription>
              Get offline access and a better experience
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {getInstallInstructions()}

            {/* Service Worker Status */}
            <div className="border-t pt-4 mt-4">
              <p className="text-xs text-muted-foreground mb-2">
                <strong>Technical Info:</strong>
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>Browser:</div>
                <div className="font-mono">{status.browser}</div>
                <div>Service Worker:</div>
                <div className="font-mono">{status.serviceWorkerStatus}</div>
                <div>Installed:</div>
                <div className="font-mono">{status.isInstalled ? 'Yes' : 'No'}</div>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Close
            </Button>
            {status.browser === 'firefox' && (
              <Button
                onClick={() => {
                  window.open('https://support.mozilla.org/en-US/kb/progressive-web-apps-firefox', '_blank');
                }}
              >
                Learn More
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
