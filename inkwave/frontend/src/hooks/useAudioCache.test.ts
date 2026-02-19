/**
 * useAudioCache Hook Tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAudioCache } from './useAudioCache';

// Mock the Cache API
const mockCache = {
  put: vi.fn().mockResolvedValue(undefined),
  match: vi.fn().mockResolvedValue(null),
  delete: vi.fn().mockResolvedValue(true),
  keys: vi.fn().mockResolvedValue([]),
};

const mockCaches = {
  open: vi.fn().mockResolvedValue(mockCache),
  delete: vi.fn().mockResolvedValue(true),
  keys: vi.fn().mockResolvedValue(['inkwave-audio-v1']),
  match: vi.fn().mockResolvedValue(null),
};

// Store original values
const originalCaches = global.caches;
const originalNavigator = global.navigator;

describe('useAudioCache', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    // Mock caches API
    Object.defineProperty(global, 'caches', {
      value: mockCaches,
      writable: true,
    });

    // Mock navigator.serviceWorker
    Object.defineProperty(global, 'navigator', {
      value: {
        ...originalNavigator,
        serviceWorker: {
          register: vi.fn(),
          ready: Promise.resolve({}),
        },
      },
      writable: true,
    });
  });

  afterEach(() => {
    // Restore originals
    Object.defineProperty(global, 'caches', {
      value: originalCaches,
      writable: true,
    });
  });

  it('should initialize with correct default state', async () => {
    const { result } = renderHook(() => useAudioCache());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isSupported).toBe(true);
    expect(result.current.cachedBooks).toEqual([]);
    expect(result.current.totalCacheSize).toBe(0);
  });

  it('should report isSupported based on caches availability', async () => {
    // With caches available (from setup), should be supported
    const { result } = renderHook(() => useAudioCache());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Since caches is mocked in setup, it should be supported
    expect(result.current.isSupported).toBe(true);
  });

  it('should provide formatSize utility', async () => {
    const { result } = renderHook(() => useAudioCache());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.formatSize(500)).toBe('500 B');
    expect(result.current.formatSize(1024)).toBe('1.0 KB');
    expect(result.current.formatSize(1024 * 1024)).toBe('1.0 MB');
    expect(result.current.formatSize(1024 * 1024 * 1024)).toBe('1.0 GB');
  });

  it('should check if book is cached', async () => {
    // Set up metadata in localStorage
    const metadata = [
      { bookId: 'book-123', title: 'Test Book', cachedAt: new Date().toISOString(), size: 1000, chunkCount: 5 },
    ];
    localStorage.setItem('inkwave-audio-cache-metadata', JSON.stringify(metadata));

    const { result } = renderHook(() => useAudioCache());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isBookCached('book-123')).toBe(true);
    expect(result.current.isBookCached('book-456')).toBe(false);
  });

  it('should load cached books from localStorage', async () => {
    const metadata = [
      { bookId: 'book-1', title: 'Book 1', cachedAt: '2024-01-01', size: 1000, chunkCount: 2 },
      { bookId: 'book-2', title: 'Book 2', cachedAt: '2024-01-02', size: 2000, chunkCount: 3 },
    ];
    localStorage.setItem('inkwave-audio-cache-metadata', JSON.stringify(metadata));

    const { result } = renderHook(() => useAudioCache());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.cachedBooks).toHaveLength(2);
    expect(result.current.totalCacheSize).toBe(3000);
  });

  it('should handle corrupted localStorage gracefully', async () => {
    localStorage.setItem('inkwave-audio-cache-metadata', 'invalid-json');

    const { result } = renderHook(() => useAudioCache());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should not crash, just return empty
    expect(result.current.cachedBooks).toEqual([]);
  });

  it('should provide download progress state', async () => {
    const { result } = renderHook(() => useAudioCache());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.downloadProgress).toBeNull();
  });

  it('should clear all cache when requested', async () => {
    const metadata = [
      { bookId: 'book-1', title: 'Book 1', cachedAt: '2024-01-01', size: 1000, chunkCount: 2 },
    ];
    localStorage.setItem('inkwave-audio-cache-metadata', JSON.stringify(metadata));

    const { result } = renderHook(() => useAudioCache());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.clearAllCache();
    });

    expect(mockCaches.delete).toHaveBeenCalledWith('inkwave-audio-v1');
    expect(localStorage.getItem('inkwave-audio-cache-metadata')).toBeNull();
  });
});

describe('useAudioCache edge cases', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    Object.defineProperty(global, 'caches', {
      value: mockCaches,
      writable: true,
    });
  });

  it('should handle empty audio URLs array', async () => {
    const { result } = renderHook(() => useAudioCache());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Caching with empty array should complete immediately
    await act(async () => {
      await result.current.cacheBook('book-123', 'Test Book', []);
    });

    expect(result.current.downloadProgress?.status).toBe('completed');
  });

  it('should not cache when not supported', async () => {
    Object.defineProperty(global, 'caches', {
      value: undefined,
      writable: true,
    });

    const { result } = renderHook(() => useAudioCache());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // When caches is undefined, cacheBook should throw
    await expect(
      result.current.cacheBook('book-123', 'Test', ['http://example.com/audio.mp3'])
    ).rejects.toThrow();
  });
});
