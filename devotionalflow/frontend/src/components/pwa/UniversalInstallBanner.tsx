/**
 * Universal Install Banner
 * Works across all browsers with browser-specific messaging
 * Best UX practices: non-blocking, dismissible, smart timing
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, X, BookOpen, Smartphone, Chrome } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function UniversalInstallBanner() {
  const [show, setShow] = useState(false);
  const [browser, setBrowser] = useState<'chrome' | 'firefox' | 'safari' | 'other'>('other');
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);

  useEffect(() => {
    // Don't show if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      return;
    }

    // Check if dismissed permanently
    const dismissed = localStorage.getItem('install_banner_dismissed_permanent');
    if (dismissed === 'true') {
      return;
    }

    // Check if dismissed recently (3 days)
    const dismissedTemp = localStorage.getItem('install_banner_dismissed_temp');
    if (dismissedTemp) {
      const dismissedTime = parseInt(dismissedTemp);
      if (Date.now() - dismissedTime < 3 * 24 * 60 * 60 * 1000) {
        return;
      }
    }

    // Detect browser
    const userAgent = navigator.userAgent.toLowerCase();
    if (userAgent.includes('firefox')) setBrowser('firefox');
    else if (userAgent.includes('chrome') && !userAgent.includes('edg')) setBrowser('chrome');
    else if (userAgent.includes('safari') && !userAgent.includes('chrome')) setBrowser('safari');
    else setBrowser('other');

    // Listen for Chrome/Edge install prompt
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };
    window.addEventListener('beforeinstallprompt', handler);

    // Show on first visit with a delay for smooth UX
    setTimeout(() => setShow(true), 3000); // 3 second delay for smooth experience

    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (deferredPrompt && (browser === 'chrome' || browser === 'other')) {
      // Chrome/Edge - trigger native prompt
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log(`Install prompt outcome: ${outcome}`);
      setShow(false);
      if (outcome === 'accepted') {
        localStorage.setItem('install_banner_dismissed_permanent', 'true');
      }
    } else {
      // For Firefox/Safari, the banner itself provides instructions
      // Just track that user clicked
      console.log('User wants to install on', browser);
    }
  };

  const handleDismissTemporary = () => {
    localStorage.setItem('install_banner_dismissed_temp', Date.now().toString());
    setShow(false);
  };

  const handleDismissPermanent = () => {
    localStorage.setItem('install_banner_dismissed_permanent', 'true');
    setShow(false);
  };

  const getBrowserContent = () => {
    switch (browser) {
      case 'chrome':
        return {
          icon: <Chrome className="w-5 h-5 text-primary" />,
          title: "Install FreshManna",
          description: "Get the full app experience with offline access and faster performance.",
          ctaText: "Install Now",
          showNativeButton: true,
        };

      case 'firefox':
        return {
          icon: <Download className="w-5 h-5 text-primary" />,
          title: "Install FreshManna",
          description: "Firefox: Tap the menu (☰) → Install to add to your home screen.",
          ctaText: "Got It",
          showNativeButton: false,
        };

      case 'safari':
        return {
          icon: <Smartphone className="w-5 h-5 text-primary" />,
          title: "Add to Home Screen",
          description: "Tap the Share button (⎙) → Add to Home Screen for the best experience.",
          ctaText: "Got It",
          showNativeButton: false,
        };

      default:
        return {
          icon: <BookOpen className="w-5 h-5 text-primary" />,
          title: "Install FreshManna",
          description: "Check your browser menu for an Install or Add to Home Screen option.",
          ctaText: "Got It",
          showNativeButton: false,
        };
    }
  };

  if (!show) return null;

  const content = getBrowserContent();

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: -100, opacity: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-primary/95 to-primary text-primary-foreground shadow-lg backdrop-blur-sm"
      >
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center gap-3 md:gap-4">
            {/* Icon */}
            <div className="shrink-0 w-10 h-10 md:w-12 md:h-12 bg-white/20 rounded-xl flex items-center justify-center">
              {content.icon}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-sm md:text-base leading-tight mb-0.5">
                {content.title}
              </h3>
              <p className="text-xs md:text-sm text-primary-foreground/90 line-clamp-1 md:line-clamp-none">
                {content.description}
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 shrink-0">
              {/* Primary CTA */}
              <Button
                onClick={content.showNativeButton ? handleInstall : handleDismissTemporary}
                size="sm"
                className="bg-white text-primary hover:bg-white/90 font-medium text-xs md:text-sm"
              >
                <Download className="w-3.5 h-3.5 md:w-4 md:h-4 mr-1.5" />
                {content.ctaText}
              </Button>

              {/* Dismiss Options */}
              <button
                onClick={handleDismissTemporary}
                className="text-xs md:text-sm text-primary-foreground/80 hover:text-primary-foreground underline hidden md:inline"
                title="Remind me in 3 days"
              >
                Later
              </button>

              {/* Close Button */}
              <button
                onClick={handleDismissPermanent}
                className="p-1 text-primary-foreground/60 hover:text-primary-foreground transition-colors"
                title="Don't show again"
              >
                <X className="w-4 h-4 md:w-5 md:h-5" />
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
