import { useState, useEffect, useCallback } from 'react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

interface PWAState {
  isInstallable: boolean
  isInstalled: boolean
  isOnline: boolean
  hasUpdate: boolean
  promptInstall: () => Promise<boolean>
  applyUpdate: () => void
}

/**
 * Custom hook for PWA install prompt and status.
 *
 * Provides functionality to detect if the app is installable,
 * if it's already installed, and to trigger the install prompt.
 *
 * @returns PWAState object with installation status and methods
 */
export function usePWA(): PWAState {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [isInstalled, setIsInstalled] = useState(false)
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true)
  const [hasUpdate, setHasUpdate] = useState(false)

  useEffect(() => {
    // Check if app is already installed (standalone mode)
    const checkInstalled = () => {
      if (typeof window !== 'undefined') {
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches
        const isIOSStandalone = (window.navigator as any).standalone === true
        setIsInstalled(isStandalone || isIOSStandalone)
      }
    }

    checkInstalled()

    // Listen for beforeinstallprompt event
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
    }

    // Listen for appinstalled event
    const handleAppInstalled = () => {
      setIsInstalled(true)
      setDeferredPrompt(null)
    }

    // Listen for online/offline status
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    // Listen for service worker updates (custom event from main.tsx)
    const handleServiceWorkerUpdate = (event: Event) => {
      console.log('[PWA] Update available', event)
      setHasUpdate(true)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.addEventListener('appinstalled', handleAppInstalled)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    window.addEventListener('swUpdateAvailable', handleServiceWorkerUpdate)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('appinstalled', handleAppInstalled)
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('swUpdateAvailable', handleServiceWorkerUpdate)
    }
  }, [])

  const promptInstall = useCallback(async (): Promise<boolean> => {
    if (!deferredPrompt) {
      return false
    }

    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice

    if (outcome === 'accepted') {
      setDeferredPrompt(null)
      return true
    }

    return false
  }, [deferredPrompt])

  const applyUpdate = useCallback(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then(registration => {
        registration.waiting?.postMessage({ type: 'SKIP_WAITING' })
        window.location.reload()
      })
    }
  }, [])

  return {
    isInstallable: deferredPrompt !== null,
    isInstalled,
    isOnline,
    hasUpdate,
    promptInstall,
    applyUpdate,
  }
}

export default usePWA
