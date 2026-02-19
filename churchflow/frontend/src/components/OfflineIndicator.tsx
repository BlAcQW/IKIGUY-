import { motion, AnimatePresence } from 'framer-motion'
import { WifiOff, RefreshCw } from 'lucide-react'
import { usePWA } from '../hooks/usePWA'

/**
 * Shows a banner when the user is offline.
 * Automatically hides when back online.
 */
export default function OfflineIndicator() {
  const { isOnline } = usePWA()

  return (
    <AnimatePresence>
      {!isOnline && (
        <motion.div
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -100, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="fixed top-0 left-0 right-0 bg-yellow-500 text-yellow-900 z-50 safe-area-top"
        >
          <div className="flex items-center justify-center gap-2 py-2 px-4">
            <WifiOff className="w-4 h-4" />
            <span className="text-sm font-medium">You're offline</span>
            <button
              onClick={() => window.location.reload()}
              className="ml-2 p-1 rounded-full hover:bg-yellow-400 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
