/**
 * OfflineBanner Component
 * Shows offline status notification to users
 */

import { motion, AnimatePresence } from 'framer-motion';
import { WifiOff, Wifi } from 'lucide-react';
import { useOfflineStatus } from '../hooks/useOfflineStatus';

export default function OfflineBanner() {
  const { isOnline, wasOffline } = useOfflineStatus();

  return (
    <AnimatePresence>
      {!isOnline && (
        <motion.div
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -100, opacity: 0 }}
          transition={{ type: 'spring', damping: 20 }}
          className="fixed top-0 left-0 right-0 z-[100] bg-amber-600 text-white py-2 px-4 flex items-center justify-center gap-2 shadow-lg safe-top"
        >
          <WifiOff className="h-4 w-4" />
          <span className="text-sm font-medium">
            You're offline. Cached content is still available.
          </span>
        </motion.div>
      )}

      {wasOffline && isOnline && (
        <motion.div
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -100, opacity: 0 }}
          transition={{ type: 'spring', damping: 20 }}
          className="fixed top-0 left-0 right-0 z-[100] bg-green-600 text-white py-2 px-4 flex items-center justify-center gap-2 shadow-lg safe-top"
        >
          <Wifi className="h-4 w-4" />
          <span className="text-sm font-medium">
            You're back online!
          </span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
