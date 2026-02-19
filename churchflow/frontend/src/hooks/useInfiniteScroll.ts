/**
 * Infinite Scroll Hook
 *
 * Uses Intersection Observer to detect when user scrolls near the bottom
 * and triggers loading more data.
 */

import { useEffect, useRef, useCallback, useState } from 'react';

interface UseInfiniteScrollOptions {
  /** Callback to load more data */
  onLoadMore: () => void;
  /** Whether there's more data to load */
  hasMore: boolean;
  /** Whether currently loading */
  isLoading: boolean;
  /** Root margin for intersection observer (default: '100px') */
  rootMargin?: string;
  /** Threshold for intersection (default: 0.1) */
  threshold?: number;
}

interface UseInfiniteScrollReturn {
  /** Ref to attach to the sentinel element at the bottom of the list */
  sentinelRef: React.RefObject<HTMLDivElement>;
  /** Whether the sentinel is visible (for debugging) */
  isIntersecting: boolean;
}

export function useInfiniteScroll({
  onLoadMore,
  hasMore,
  isLoading,
  rootMargin = '100px',
  threshold = 0.1,
}: UseInfiniteScrollOptions): UseInfiniteScrollReturn {
  const sentinelRef = useRef<HTMLDivElement>(null);
  const [isIntersecting, setIsIntersecting] = useState(false);

  const handleIntersection = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries;
      setIsIntersecting(entry.isIntersecting);

      if (entry.isIntersecting && hasMore && !isLoading) {
        onLoadMore();
      }
    },
    [hasMore, isLoading, onLoadMore]
  );

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(handleIntersection, {
      rootMargin,
      threshold,
    });

    observer.observe(sentinel);

    return () => {
      observer.disconnect();
    };
  }, [handleIntersection, rootMargin, threshold]);

  return {
    sentinelRef,
    isIntersecting,
  };
}

export default useInfiniteScroll;
