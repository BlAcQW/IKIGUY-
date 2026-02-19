import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App.tsx'
import './styles/index.css'
import './lib/axios-config' // Configure axios interceptors globally

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
)

// Register service worker with enhanced update detection
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js', { scope: '/' })
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

        // Helper function to safely check for updates
        const checkForUpdates = async () => {
          try {
            // Get fresh registration to avoid stale references
            const currentRegistration = await navigator.serviceWorker.getRegistration();
            if (currentRegistration) {
              await currentRegistration.update();
            }
          } catch (err) {
            // Silently ignore errors - they're usually harmless
            // (e.g., network issues, service worker not ready)
            console.debug('[App] Update check skipped:', err);
          }
        };

        // Check for updates periodically (every 5 minutes)
        setInterval(() => {
          console.log('[App] Checking for service worker updates...');
          checkForUpdates();
        }, 5 * 60 * 1000);

        // Check for updates when page becomes visible
        document.addEventListener('visibilitychange', () => {
          if (!document.hidden) {
            console.log('[App] Page visible, checking for updates...');
            checkForUpdates();
          }
        });

        // Check for updates on page focus
        window.addEventListener('focus', () => {
          console.log('[App] Page focused, checking for updates...');
          checkForUpdates();
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
