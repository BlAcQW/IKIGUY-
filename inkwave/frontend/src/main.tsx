import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './styles/index.css'
import { initializeGlobalErrorTracking } from './lib/tracking'

// Initialize global error tracking
initializeGlobalErrorTracking();

// Register service worker for PWA support
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then((registration) => {
        console.log('[App] Service worker registered:', registration.scope);

        // Listen for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          console.log('[App] New service worker found, installing...');

          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New service worker is installed but waiting
                console.log('[App] New service worker installed, update available');
                // Dispatch custom event for React components to listen
                window.dispatchEvent(new CustomEvent('swUpdateAvailable', { detail: registration }));
              }
            });
          }
        });

        // Check for updates periodically (every 5 minutes) - only when online
        setInterval(() => {
          if (navigator.onLine) {
            console.log('[App] Checking for service worker updates...');
            registration.update().catch(err => {
              console.log('[App] Update check failed (likely offline):', err.message);
            });
          }
        }, 5 * 60 * 1000);

        // Check for updates when page becomes visible - only when online
        document.addEventListener('visibilitychange', () => {
          if (!document.hidden && navigator.onLine) {
            console.log('[App] Page visible, checking for updates...');
            registration.update().catch(err => {
              console.log('[App] Update check failed (likely offline):', err.message);
            });
          }
        });

        // Check for updates on page focus - only when online
        window.addEventListener('focus', () => {
          if (navigator.onLine) {
            console.log('[App] Page focused, checking for updates...');
            registration.update().catch(err => {
              console.log('[App] Update check failed (likely offline):', err.message);
            });
          }
        });
      })
      .catch((error) => {
        console.log('[App] Service worker registration failed:', error);
      });

    // Listen for controller change (new service worker activated)
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      console.log('[App] Service worker controller changed, reloading page...');
      // Reload the page to get the latest version
      window.location.reload();
    });
  });
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
