/**
 * PullToRefreshIndicator Component
 * Visual feedback for pull-to-refresh gesture
 */

import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw } from 'lucide-react';

interface PullToRefreshIndicatorProps {
  pullDistance: number;
  progress: number;
  canRelease: boolean;
  isRefreshing: boolean;
  isPulling: boolean;
}

export default function PullToRefreshIndicator({
  pullDistance,
  progress,
  canRelease,
  isRefreshing,
  isPulling,
}: PullToRefreshIndicatorProps) {
  const showIndicator = isPulling || isRefreshing || pullDistance > 0;

  return (
    <AnimatePresence>
      {showIndicator && (
        <motion.div
          initial={{ opacity: 0, y: -40 }}
          animate={{
            opacity: 1,
            y: Math.min(pullDistance - 20, 60),
          }}
          exit={{ opacity: 0, y: -40 }}
          transition={{ type: 'spring', damping: 20 }}
          className="fixed top-0 left-0 right-0 flex justify-center z-50 pointer-events-none pt-safe"
        >
          <div
            className={`flex items-center justify-center rounded-full shadow-lg backdrop-blur-sm transition-colors ${
              canRelease || isRefreshing
                ? 'bg-purple-500/90 text-white'
                : 'bg-gray-800/90 text-gray-300'
            }`}
            style={{
              width: 48,
              height: 48,
              marginTop: 16,
            }}
          >
            <motion.div
              animate={{
                rotate: isRefreshing ? 360 : progress * 180,
              }}
              transition={{
                rotate: isRefreshing
                  ? { repeat: Infinity, duration: 1, ease: 'linear' }
                  : { duration: 0.1 },
              }}
            >
              <RefreshCw
                className={`w-6 h-6 ${isRefreshing ? 'animate-spin' : ''}`}
              />
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
