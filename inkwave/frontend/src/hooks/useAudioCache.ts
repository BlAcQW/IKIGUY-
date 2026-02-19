/**
 * useAudioCache Hook
 * Manages offline caching of audiobook audio files
 */

import { useState, useCallback, useEffect } from 'react';

const AUDIO_CACHE_NAME = 'inkwave-audio-v1';

interface CachedBook {
  bookId: string;
  title: string;
  cachedAt: string;
  size: number;
  chunkCount: number;
}

interface CacheState {
  isSupported: boolean;
  cachedBooks: CachedBook[];
  totalCacheSize: number;
  isLoading: boolean;
}

interface CacheProgress {
  bookId: string;
  current: number;
  total: number;
  status: 'downloading' | 'completed' | 'error';
}

export function useAudioCache() {
  const [state, setState] = useState<CacheState>({
    isSupported: false,
    cachedBooks: [],
    totalCacheSize: 0,
    isLoading: true,
  });

  const [downloadProgress, setDownloadProgress] = useState<CacheProgress | null>(null);

  // Check if caching is supported
  useEffect(() => {
    const checkSupport = async () => {
      const supported = 'caches' in window && 'serviceWorker' in navigator;
      setState((prev) => ({ ...prev, isSupported: supported }));

      if (supported) {
        await refreshCachedBooks();
      }

      setState((prev) => ({ ...prev, isLoading: false }));
    };

    checkSupport();
  }, []);

  // Get list of cached books from localStorage metadata
  const refreshCachedBooks = useCallback(async () => {
    try {
      const metadataStr = localStorage.getItem('inkwave-audio-cache-metadata');
      const metadata: CachedBook[] = metadataStr ? JSON.parse(metadataStr) : [];

      // Calculate total size
      const totalSize = metadata.reduce((sum, book) => sum + book.size, 0);

      setState((prev) => ({
        ...prev,
        cachedBooks: metadata,
        totalCacheSize: totalSize,
      }));
    } catch (error) {
      console.error('Failed to refresh cached books:', error);
    }
  }, []);

  // Cache audio chunks for a book
  const cacheBook = useCallback(
    async (bookId: string, title: string, audioUrls: string[]) => {
      if (!state.isSupported) {
        throw new Error('Caching not supported');
      }

      setDownloadProgress({
        bookId,
        current: 0,
        total: audioUrls.length,
        status: 'downloading',
      });

      try {
        const cache = await caches.open(AUDIO_CACHE_NAME);
        let cachedSize = 0;

        for (let i = 0; i < audioUrls.length; i++) {
          const url = audioUrls[i];

          try {
            const response = await fetch(url);
            if (!response.ok) {
              throw new Error(`Failed to fetch ${url}`);
            }

            const blob = await response.blob();
            cachedSize += blob.size;

            // Store in cache
            await cache.put(url, new Response(blob, {
              headers: {
                'Content-Type': response.headers.get('Content-Type') || 'audio/mpeg',
                'Content-Length': String(blob.size),
              },
            }));

            setDownloadProgress({
              bookId,
              current: i + 1,
              total: audioUrls.length,
              status: 'downloading',
            });
          } catch (err) {
            console.error(`Failed to cache chunk ${i}:`, err);
            throw err;
          }
        }

        // Update metadata
        const newCachedBook: CachedBook = {
          bookId,
          title,
          cachedAt: new Date().toISOString(),
          size: cachedSize,
          chunkCount: audioUrls.length,
        };

        const metadataStr = localStorage.getItem('inkwave-audio-cache-metadata');
        const metadata: CachedBook[] = metadataStr ? JSON.parse(metadataStr) : [];

        // Remove existing entry for this book if exists
        const filtered = metadata.filter((b) => b.bookId !== bookId);
        filtered.push(newCachedBook);

        localStorage.setItem('inkwave-audio-cache-metadata', JSON.stringify(filtered));

        setDownloadProgress({
          bookId,
          current: audioUrls.length,
          total: audioUrls.length,
          status: 'completed',
        });

        await refreshCachedBooks();

        return true;
      } catch (error) {
        setDownloadProgress({
          bookId,
          current: 0,
          total: audioUrls.length,
          status: 'error',
        });
        throw error;
      }
    },
    [state.isSupported, refreshCachedBooks]
  );

  // Remove cached audio for a book
  const removeBook = useCallback(
    async (bookId: string) => {
      if (!state.isSupported) return;

      try {
        const cache = await caches.open(AUDIO_CACHE_NAME);
        const keys = await cache.keys();

        // Remove all entries for this book
        for (const request of keys) {
          if (request.url.includes(bookId)) {
            await cache.delete(request);
          }
        }

        // Update metadata
        const metadataStr = localStorage.getItem('inkwave-audio-cache-metadata');
        const metadata: CachedBook[] = metadataStr ? JSON.parse(metadataStr) : [];
        const filtered = metadata.filter((b) => b.bookId !== bookId);
        localStorage.setItem('inkwave-audio-cache-metadata', JSON.stringify(filtered));

        await refreshCachedBooks();
      } catch (error) {
        console.error('Failed to remove cached book:', error);
        throw error;
      }
    },
    [state.isSupported, refreshCachedBooks]
  );

  // Check if a book is cached
  const isBookCached = useCallback(
    (bookId: string) => {
      return state.cachedBooks.some((b) => b.bookId === bookId);
    },
    [state.cachedBooks]
  );

  // Clear all cached audio
  const clearAllCache = useCallback(async () => {
    if (!state.isSupported) return;

    try {
      await caches.delete(AUDIO_CACHE_NAME);
      localStorage.removeItem('inkwave-audio-cache-metadata');
      await refreshCachedBooks();
    } catch (error) {
      console.error('Failed to clear cache:', error);
      throw error;
    }
  }, [state.isSupported, refreshCachedBooks]);

  // Format cache size for display
  const formatSize = useCallback((bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  }, []);

  return {
    ...state,
    downloadProgress,
    cacheBook,
    removeBook,
    isBookCached,
    clearAllCache,
    formatSize,
    refreshCachedBooks,
  };
}
