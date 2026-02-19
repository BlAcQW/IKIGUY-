import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useIsMobile } from '@/hooks/use-mobile';

describe('useIsMobile Hook', () => {
  const originalInnerWidth = window.innerWidth;
  const originalMatchMedia = window.matchMedia;

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset window.innerWidth
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
  });

  afterEach(() => {
    // Restore original matchMedia
    window.matchMedia = originalMatchMedia;
    vi.clearAllMocks();
  });

  it('should return false for desktop width', () => {
    // Set desktop width
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });

    // Mock matchMedia to return false for mobile
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(false);
    expect(mockMatchMedia).toHaveBeenCalledWith('(max-width: 767px)');
  });

  it('should return true for mobile width', () => {
    // Set mobile width
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    // Mock matchMedia to return true for mobile
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: true,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(true);
    expect(mockMatchMedia).toHaveBeenCalledWith('(max-width: 767px)');
  });

  it('should return true for tablet width (edge case)', () => {
    // Set tablet width (767px - edge case)
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 767,
    });

    // Mock matchMedia to return true for mobile
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: true,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(true);
  });

  it('should return false for desktop width (edge case)', () => {
    // Set desktop width (768px - edge case)
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    });

    // Mock matchMedia to return false for mobile
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(false);
  });

  it('should handle window resize events', () => {
    const mockAddEventListener = vi.fn();
    const mockRemoveEventListener = vi.fn();

    // Mock matchMedia
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: mockAddEventListener,
      removeEventListener: mockRemoveEventListener,
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    const { result, unmount } = renderHook(() => useIsMobile());

    // Check that event listener was added
    expect(mockAddEventListener).toHaveBeenCalledWith('change', expect.any(Function));

    // Simulate resize to mobile
    act(() => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      // Get the change handler and call it
      const changeHandler = mockAddEventListener.mock.calls[0][1];
      changeHandler();
    });

    expect(result.current).toBe(true);

    // Cleanup
    unmount();

    // Check that event listener was removed
    expect(mockRemoveEventListener).toHaveBeenCalledWith('change', expect.any(Function));
  });

  it('should handle multiple resize events', () => {
    const mockAddEventListener = vi.fn();
    const mockRemoveEventListener = vi.fn();

    // Mock matchMedia
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: mockAddEventListener,
      removeEventListener: mockRemoveEventListener,
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    const { result } = renderHook(() => useIsMobile());

    const changeHandler = mockAddEventListener.mock.calls[0][1];

    // Simulate multiple resize events
    act(() => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      changeHandler();
    });

    expect(result.current).toBe(true);

    act(() => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024,
      });
      changeHandler();
    });

    expect(result.current).toBe(false);

    act(() => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      changeHandler();
    });

    expect(result.current).toBe(true);
  });

  it('should handle very small mobile screens', () => {
    // Set very small mobile width
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 320,
    });

    // Mock matchMedia to return true for mobile
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: true,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(true);
  });

  it('should handle large desktop screens', () => {
    // Set large desktop width
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1920,
    });

    // Mock matchMedia to return false for mobile
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(false);
  });

  it('should handle zero width edge case', () => {
    // Set zero width
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 0,
    });

    // Mock matchMedia to return true for mobile
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: true,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(true);
  });

  it('should handle negative width edge case', () => {
    // Set negative width (edge case)
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: -100,
    });

    // Mock matchMedia to return true for mobile
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: true,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(true);
  });

  it('should handle undefined innerWidth', () => {
    // Set undefined innerWidth
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: undefined,
    });

    // Mock matchMedia to return false for mobile (since undefined width should default to desktop)
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    const { result } = renderHook(() => useIsMobile());

    // When innerWidth is undefined, the hook should still work and return the matchMedia result
    expect(result.current).toBe(false);
  });

  it('should use the correct breakpoint constant', () => {
    // The hook uses MOBILE_BREAKPOINT = 768
    // So it should check for max-width: 767px (768 - 1)
    
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    renderHook(() => useIsMobile());

    // Verify the correct breakpoint is used
    expect(mockMatchMedia).toHaveBeenCalledWith('(max-width: 767px)');
  });

  it('should handle cleanup on unmount', () => {
    const mockAddEventListener = vi.fn();
    const mockRemoveEventListener = vi.fn();

    // Mock matchMedia
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: mockAddEventListener,
      removeEventListener: mockRemoveEventListener,
      dispatchEvent: vi.fn(),
    }));

    window.matchMedia = mockMatchMedia;

    const { unmount } = renderHook(() => useIsMobile());

    // Verify event listener was added
    expect(mockAddEventListener).toHaveBeenCalledWith('change', expect.any(Function));

    // Unmount the hook
    unmount();

    // Verify event listener was removed
    expect(mockRemoveEventListener).toHaveBeenCalledWith('change', expect.any(Function));
  });
});
