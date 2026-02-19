import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, X, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * InstallPromptBanner - Beautiful install prompt for PWA
 * Shows after 3 page views and can be triggered manually
 */
export function InstallPromptBanner() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    // Check if iOS
    const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    setIsIOS(iOS);

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      return;
    }

    // Check if dismissed recently (within 7 days)
    const dismissed = localStorage.getItem('install_prompt_dismissed');
    if (dismissed) {
      const dismissedTime = parseInt(dismissed);
      if (Date.now() - dismissedTime < 7 * 24 * 60 * 60 * 1000) {
        return;
      }
    }

    // Listen for beforeinstallprompt (Android/Chrome)
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);

      // Show prompt after 3 page views
      const pageViews = parseInt(localStorage.getItem('page_views') || '0');
      localStorage.setItem('page_views', (pageViews + 1).toString());

      if (pageViews >= 2) {
        // Delay showing prompt for better UX
        setTimeout(() => setShowPrompt(true), 3000);
      }
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('User accepted install');
    }

    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    localStorage.setItem('install_prompt_dismissed', Date.now().toString());
    setShowPrompt(false);
  };

  // Don't show if no prompt available or on iOS without prompt
  if (!showPrompt || (isIOS && !deferredPrompt)) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 100, opacity: 0 }}
        transition={{ type: "spring", stiffness: 260, damping: 20 }}
        className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:max-w-md z-50"
      >
        <div className="bg-gradient-to-br from-navy to-navy-light p-6 rounded-2xl shadow-elevated border border-gold/20 backdrop-blur-sm">
          <button
            onClick={handleDismiss}
            className="absolute top-3 right-3 text-cream/60 hover:text-cream transition-colors"
          >
            <X className="w-4 h-4" />
          </button>

          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-gold/20 flex items-center justify-center shrink-0">
              <BookOpen className="w-6 h-6 text-gold" />
            </div>
            <div className="flex-1">
              <h3 className="font-serif text-lg font-bold text-cream mb-1">
                Keep God's Word With You
              </h3>
              <p className="text-sm text-cream/80 mb-4">
                Install FreshManna for offline access to daily devotionals, anytime, anywhere.
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={handleInstall}
                  className="bg-gold hover:bg-gold-dark text-navy font-medium"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Install App
                </Button>
                <Button
                  onClick={handleDismiss}
                  variant="ghost"
                  className="text-cream/80 hover:text-cream hover:bg-white/10"
                >
                  Not Now
                </Button>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
