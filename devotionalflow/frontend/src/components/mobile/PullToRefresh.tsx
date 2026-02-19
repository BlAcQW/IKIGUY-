import { useState, useRef, ReactNode } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw } from 'lucide-react';

interface PullToRefreshProps {
  onRefresh: () => Promise<void>;
  children: ReactNode;
}

/**
 * PullToRefresh - Mobile pull-to-refresh component
 * Triggers refresh callback when user pulls down from top of page
 */
export function PullToRefresh({ onRefresh, children }: PullToRefreshProps) {
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const startY = useRef(0);
  const threshold = 80;

  const handleTouchStart = (e: React.TouchEvent) => {
    // Only activate if at top of page
    if (window.scrollY === 0) {
      startY.current = e.touches[0].clientY;
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (isRefreshing || window.scrollY > 0) return;

    const currentY = e.touches[0].clientY;
    const diff = currentY - startY.current;

    // Only pull down (positive diff)
    if (diff > 0) {
      // Rubber band effect - pull becomes harder the more you pull
      setPullDistance(Math.min(diff * 0.5, 100));
    }
  };

  const handleTouchEnd = async () => {
    if (pullDistance > threshold && !isRefreshing) {
      setIsRefreshing(true);
      try {
        await onRefresh();
      } catch (error) {
        console.error('Refresh failed:', error);
      } finally {
        setIsRefreshing(false);
      }
    }
    setPullDistance(0);
  };

  // Calculate rotation for spinner (full 360 at threshold)
  const rotation = Math.min((pullDistance / threshold) * 360, 360);
  // Calculate opacity (fully visible at threshold)
  const opacity = Math.min(pullDistance / threshold, 1);

  return (
    <div
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      className="relative"
    >
      {/* Pull indicator */}
      <motion.div
        initial={{ opacity: 0, y: -40 }}
        animate={{
          opacity: isRefreshing ? 1 : opacity,
          y: isRefreshing ? 10 : Math.min(pullDistance * 0.5, 40) - 40
        }}
        className="absolute top-0 left-1/2 -translate-x-1/2 z-10"
      >
        <div className="bg-gold/90 backdrop-blur-sm rounded-full p-3 shadow-elevated">
          <motion.div
            animate={isRefreshing ? { rotate: 360 } : {}}
            transition={isRefreshing ? { duration: 1, repeat: Infinity, ease: "linear" } : {}}
          >
            <RefreshCw
              className="w-5 h-5 text-navy"
              style={{
                transform: isRefreshing ? undefined : `rotate(${rotation}deg)`,
                transition: isRefreshing ? 'none' : 'transform 0.1s'
              }}
            />
          </motion.div>
        </div>
      </motion.div>

      {/* Content */}
      <motion.div
        animate={{
          y: isRefreshing ? 0 : Math.min(pullDistance * 0.3, 30)
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        {children}
      </motion.div>
    </div>
  );
}
