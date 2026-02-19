/**
 * PWA Install Prompt
 * Shows a banner prompting users to install the app
 * Appears after user has engaged with the app
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, X, Smartphone } from 'lucide-react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export default function PWAInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Check if already installed (standalone mode)
    const standalone = window.matchMedia('(display-mode: standalone)').matches
      || (window.navigator as any).standalone === true;
    setIsStandalone(standalone);

    // Check if iOS
    const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as any).MSStream;
    setIsIOS(iOS);

    // Listen for beforeinstallprompt event (Chrome, Edge, etc.)
    const handler = (e: Event) => {
      // Prevent the mini-infobar from appearing on mobile
      e.preventDefault();
      const promptEvent = e as BeforeInstallPromptEvent;

      // Store the event so we can trigger it later
      setDeferredPrompt(promptEvent);
      console.log('[PWA] Install prompt available');

      // Show our custom prompt after a delay (user engagement)
      setTimeout(() => {
        // Only show if user hasn't dismissed before
        const dismissed = localStorage.getItem('pwa-prompt-dismissed');
        if (!dismissed) {
          setShowPrompt(true);
        }
      }, 3000); // Show after 3 seconds
    };

    window.addEventListener('beforeinstallprompt', handler);

    // For iOS, show custom instructions after delay
    if (iOS && !standalone) {
      const dismissed = localStorage.getItem('pwa-prompt-dismissed');
      if (!dismissed) {
        setTimeout(() => setShowPrompt(true), 5000); // 5 seconds for iOS
      }
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) {
      console.warn('[PWA] No deferred prompt available');
      return;
    }

    try {
      // Show the browser's install prompt
      await deferredPrompt.prompt();

      // Wait for the user's response
      const { outcome } = await deferredPrompt.userChoice;
      console.log(`[PWA] User ${outcome} the install prompt`);

      if (outcome === 'accepted') {
        setShowPrompt(false);
        setDeferredPrompt(null);
      }
    } catch (error) {
      console.error('[PWA] Error showing install prompt:', error);
    }
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa-prompt-dismissed', 'true');
  };

  // Don't show if already installed
  if (isStandalone) {
    return null;
  }

  return (
    <AnimatePresence>
      {showPrompt && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          className="fixed bottom-20 md:bottom-4 left-4 right-4 z-50 md:left-auto md:right-4 md:w-80"
          role="dialog"
          aria-labelledby="pwa-install-title"
          aria-describedby="pwa-install-description"
        >
          <div className="bg-gradient-to-br from-purple-900/95 to-gray-900/95 backdrop-blur-lg rounded-2xl shadow-2xl border border-purple-500/30 p-4 safe-bottom">
            <button
              onClick={handleDismiss}
              className="absolute top-2 right-2 p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-white transition touch-feedback"
              aria-label="Close install prompt"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-start gap-3">
              <div className="p-2 bg-purple-500/20 rounded-xl">
                <Smartphone className="w-6 h-6 text-purple-400" />
              </div>

              <div className="flex-1">
                <h3 id="pwa-install-title" className="font-semibold text-white text-sm">
                  Install InkWave
                </h3>
                <p id="pwa-install-description" className="text-gray-400 text-xs mt-1">
                  {isIOS
                    ? 'Tap the share button and "Add to Home Screen"'
                    : 'Install for offline access & a better experience'}
                </p>
              </div>
            </div>

            {!isIOS && deferredPrompt && (
              <button
                onClick={handleInstall}
                className="w-full mt-3 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold rounded-xl transition flex items-center justify-center gap-2 touch-feedback"
              >
                <Download className="w-4 h-4" />
                Install App
              </button>
            )}

            {isIOS && (
              <div className="mt-3 p-2 bg-gray-800/50 rounded-lg">
                <p className="text-xs text-gray-300 text-center">
                  Tap <span className="inline-block px-1 py-0.5 bg-gray-700 rounded text-white">Share</span> then{' '}
                  <span className="inline-block px-1 py-0.5 bg-gray-700 rounded text-white">Add to Home Screen</span>
                </p>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
