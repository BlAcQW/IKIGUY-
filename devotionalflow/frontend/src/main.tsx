import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { registerSW } from 'virtual:pwa-register';
import { logger } from './lib/logger';

// Register service worker
if ('serviceWorker' in navigator) {
  const updateSW = registerSW({
    immediate: true,
    onNeedRefresh() {
      // Dispatch custom event for update notification
      logger.info('[FreshManna] New version available!');
      window.dispatchEvent(new CustomEvent('swUpdateAvailable', {
        detail: { updateSW }
      }));
    },
    onOfflineReady() {
      logger.info('[FreshManna] App ready to work offline');
    },
    onRegistered(registration) {
      logger.info('[FreshManna] Service worker registered');

      // Check for updates every 5 minutes
      if (registration) {
        setInterval(() => {
          // Check if registration is still valid before updating
          if (registration && registration.active) {
            logger.debug('[FreshManna] Checking for updates...');
            registration.update().catch(err => {
              // Silently handle DOMException errors from update checks
              if (err.name !== 'DOMException') {
                logger.error('[FreshManna] Update check failed:', err);
              }
            });
          }
        }, 5 * 60 * 1000); // Check every 5 minutes instead of 1
      }
    },
    onRegisterError(error) {
      logger.error('[FreshManna] SW registration error:', error);
    }
  });

  // Also check for updates when page gains focus
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && 'serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistration().then(registration => {
        if (registration && registration.active) {
          logger.debug('[FreshManna] Page visible - checking for updates');
          registration.update().catch(err => {
            // Silently handle DOMException errors
            if (err.name !== 'DOMException') {
              logger.error('[FreshManna] Visibility update check failed:', err);
            }
          });
        }
      }).catch(err => {
        logger.error('[FreshManna] Failed to get registration:', err);
      });
    }
  });
}

createRoot(document.getElementById("root")!).render(<App />);
