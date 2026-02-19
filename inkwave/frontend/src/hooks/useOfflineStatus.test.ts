/**
 * useOfflineStatus Hook Tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useOfflineStatus } from './useOfflineStatus';

describe('useOfflineStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();

    // Mock navigator.onLine - use defineProperty on existing navigator
    Object.defineProperty(navigator, 'onLine', {
      value: true,
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should initialize with online status from navigator', () => {
    const { result } = renderHook(() => useOfflineStatus());

    expect(result.current.isOnline).toBe(true);
    expect(result.current.wasOffline).toBe(false);
  });

  it('should detect offline status', () => {
    Object.defineProperty(navigator, 'onLine', {
      value: false,
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useOfflineStatus());

    expect(result.current.isOnline).toBe(false);
  });

  it('should update when going offline', () => {
    const { result } = renderHook(() => useOfflineStatus());

    expect(result.current.isOnline).toBe(true);

    // Simulate offline event
    act(() => {
      window.dispatchEvent(new Event('offline'));
    });

    expect(result.current.isOnline).toBe(false);
    expect(result.current.wasOffline).toBe(false);
  });

  it('should update when coming back online', () => {
    const { result } = renderHook(() => useOfflineStatus());

    // Go offline first
    act(() => {
      window.dispatchEvent(new Event('offline'));
    });

    expect(result.current.isOnline).toBe(false);

    // Come back online
    act(() => {
      window.dispatchEvent(new Event('online'));
    });

    expect(result.current.isOnline).toBe(true);
    expect(result.current.wasOffline).toBe(true);
  });

  it('should clear wasOffline flag after delay', () => {
    const { result } = renderHook(() => useOfflineStatus());

    // Go offline then online
    act(() => {
      window.dispatchEvent(new Event('offline'));
    });
    act(() => {
      window.dispatchEvent(new Event('online'));
    });

    expect(result.current.wasOffline).toBe(true);

    // Advance timers
    act(() => {
      vi.advanceTimersByTime(5000);
    });

    expect(result.current.wasOffline).toBe(false);
  });

  it('should add and remove event listeners', () => {
    const addEventListenerSpy = vi.spyOn(window, 'addEventListener');
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

    const { unmount } = renderHook(() => useOfflineStatus());

    expect(addEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
    expect(addEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));

    unmount();

    expect(removeEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
    expect(removeEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));

    addEventListenerSpy.mockRestore();
    removeEventListenerSpy.mockRestore();
  });
});

describe('useOfflineStatus edge cases', () => {
  it('should handle multiple offline/online cycles', () => {
    const { result } = renderHook(() => useOfflineStatus());

    // Multiple cycles
    for (let i = 0; i < 3; i++) {
      act(() => {
        window.dispatchEvent(new Event('offline'));
      });
      expect(result.current.isOnline).toBe(false);

      act(() => {
        window.dispatchEvent(new Event('online'));
      });
      expect(result.current.isOnline).toBe(true);
    }
  });

  it('should handle rapid status changes', () => {
    const { result } = renderHook(() => useOfflineStatus());

    act(() => {
      window.dispatchEvent(new Event('offline'));
      window.dispatchEvent(new Event('online'));
      window.dispatchEvent(new Event('offline'));
      window.dispatchEvent(new Event('online'));
    });

    // Should end up online
    expect(result.current.isOnline).toBe(true);
  });
});
