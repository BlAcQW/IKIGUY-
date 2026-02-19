/**
 * usePullToRefresh Hook
 * Provides native-like pull-to-refresh functionality for mobile devices
 */

import { useRef, useCallback, useState, useEffect } from 'react';

interface PullToRefreshOptions {
  onRefresh: () => Promise<void>;
  threshold?: number; // Pull distance to trigger refresh (default: 80px)
  maxPull?: number; // Maximum pull distance (default: 120px)
  disabled?: boolean;
}

interface PullToRefreshState {
  isPulling: boolean;
  pullDistance: number;
  isRefreshing: boolean;
}

export function usePullToRefresh({
  onRefresh,
  threshold = 80,
  maxPull = 120,
  disabled = false,
}: PullToRefreshOptions) {
  const [state, setState] = useState<PullToRefreshState>({
    isPulling: false,
    pullDistance: 0,
    isRefreshing: false,
  });

  const touchStartY = useRef<number>(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const canPull = useRef<boolean>(false);

  const handleTouchStart = useCallback(
    (e: React.TouchEvent) => {
      if (disabled || state.isRefreshing) return;

      // Only enable pull if at the top of the scrollable area
      const container = containerRef.current;
      const scrollTop = container?.scrollTop ?? window.scrollY;

      if (scrollTop <= 0) {
        touchStartY.current = e.touches[0].clientY;
        canPull.current = true;
      }
    },
    [disabled, state.isRefreshing]
  );

  const handleTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (!canPull.current || disabled || state.isRefreshing) return;

      const touchY = e.touches[0].clientY;
      const diff = touchY - touchStartY.current;

      // Only pull down, not up
      if (diff > 0) {
        // Apply resistance to make it feel more natural
        const resistance = 0.5;
        const pullDistance = Math.min(diff * resistance, maxPull);

        setState((prev) => ({
          ...prev,
          isPulling: true,
          pullDistance,
        }));

        // Prevent default scroll when pulling
        if (pullDistance > 10) {
          e.preventDefault();
        }
      }
    },
    [disabled, maxPull, state.isRefreshing]
  );

  const handleTouchEnd = useCallback(async () => {
    if (!canPull.current || disabled) return;

    canPull.current = false;

    if (state.pullDistance >= threshold && !state.isRefreshing) {
      // Trigger refresh
      setState((prev) => ({
        ...prev,
        isPulling: false,
        isRefreshing: true,
        pullDistance: threshold, // Keep indicator visible during refresh
      }));

      try {
        await onRefresh();
      } catch (error) {
        console.error('Pull to refresh error:', error);
      } finally {
        setState({
          isPulling: false,
          pullDistance: 0,
          isRefreshing: false,
        });
      }
    } else {
      // Reset without refresh
      setState({
        isPulling: false,
        pullDistance: 0,
        isRefreshing: false,
      });
    }
  }, [disabled, onRefresh, state.pullDistance, state.isRefreshing, threshold]);

  // Calculate progress (0 to 1)
  const progress = Math.min(state.pullDistance / threshold, 1);

  return {
    containerRef,
    handlers: {
      onTouchStart: handleTouchStart,
      onTouchMove: handleTouchMove,
      onTouchEnd: handleTouchEnd,
    },
    state: {
      ...state,
      progress,
      canRelease: state.pullDistance >= threshold,
    },
  };
}
