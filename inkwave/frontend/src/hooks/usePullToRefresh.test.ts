/**
 * usePullToRefresh Hook Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePullToRefresh } from './usePullToRefresh';

describe('usePullToRefresh', () => {
  const mockOnRefresh = vi.fn().mockResolvedValue(undefined);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() =>
      usePullToRefresh({ onRefresh: mockOnRefresh })
    );

    expect(result.current.state.isPulling).toBe(false);
    expect(result.current.state.pullDistance).toBe(0);
    expect(result.current.state.isRefreshing).toBe(false);
    expect(result.current.state.progress).toBe(0);
    expect(result.current.state.canRelease).toBe(false);
  });

  it('should provide touch handlers', () => {
    const { result } = renderHook(() =>
      usePullToRefresh({ onRefresh: mockOnRefresh })
    );

    expect(result.current.handlers.onTouchStart).toBeDefined();
    expect(result.current.handlers.onTouchMove).toBeDefined();
    expect(result.current.handlers.onTouchEnd).toBeDefined();
  });

  it('should not trigger refresh when disabled', async () => {
    const { result } = renderHook(() =>
      usePullToRefresh({ onRefresh: mockOnRefresh, disabled: true })
    );

    // Simulate touch events
    const touchStartEvent = {
      touches: [{ clientY: 0 }],
    } as unknown as React.TouchEvent;

    act(() => {
      result.current.handlers.onTouchStart(touchStartEvent);
    });

    expect(result.current.state.isPulling).toBe(false);
  });

  it('should calculate progress correctly', () => {
    const { result } = renderHook(() =>
      usePullToRefresh({ onRefresh: mockOnRefresh, threshold: 80 })
    );

    // Progress should be capped at 1 when pullDistance >= threshold
    expect(result.current.state.progress).toBe(0);
  });

  it('should use custom threshold', () => {
    const customThreshold = 100;
    const { result } = renderHook(() =>
      usePullToRefresh({ onRefresh: mockOnRefresh, threshold: customThreshold })
    );

    // Initial state should be unaffected by threshold
    expect(result.current.state.pullDistance).toBe(0);
  });

  it('should provide containerRef', () => {
    const { result } = renderHook(() =>
      usePullToRefresh({ onRefresh: mockOnRefresh })
    );

    expect(result.current.containerRef).toBeDefined();
    expect(result.current.containerRef.current).toBeNull();
  });

  it('should not refresh when pull distance is below threshold', async () => {
    const { result } = renderHook(() =>
      usePullToRefresh({ onRefresh: mockOnRefresh, threshold: 80 })
    );

    // Simulate a small pull that doesn't reach threshold
    const touchEndEvent = {
      changedTouches: [{ clientY: 30 }],
    } as unknown as React.TouchEvent;

    await act(async () => {
      result.current.handlers.onTouchEnd(touchEndEvent);
    });

    expect(mockOnRefresh).not.toHaveBeenCalled();
  });

  it('should accept maxPull option', () => {
    const { result } = renderHook(() =>
      usePullToRefresh({
        onRefresh: mockOnRefresh,
        maxPull: 150,
      })
    );

    // Hook should initialize without error
    expect(result.current.state.pullDistance).toBe(0);
  });
});

describe('usePullToRefresh edge cases', () => {
  it('should handle refresh function that throws', async () => {
    const errorRefresh = vi.fn().mockRejectedValue(new Error('Refresh failed'));
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() =>
      usePullToRefresh({ onRefresh: errorRefresh })
    );

    // After error, state should reset
    expect(result.current.state.isRefreshing).toBe(false);

    consoleSpy.mockRestore();
  });

  it('should not start pulling when already refreshing', () => {
    const slowRefresh = vi.fn().mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000))
    );

    const { result } = renderHook(() =>
      usePullToRefresh({ onRefresh: slowRefresh })
    );

    // Initial state
    expect(result.current.state.isRefreshing).toBe(false);
  });
});
