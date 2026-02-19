/**
 * Audio Cache Service
 *
 * Progressive audio caching using IndexedDB for offline-capable
 * audiobook playback. Caches audio chunks as they're played.
 *
 * Features:
 * - IndexedDB storage for large audio files
 * - LRU cache eviction when storage quota exceeded
 * - Automatic cleanup of old entries
 * - Cache statistics and management
 */

const DB_NAME = 'inkwave_audio_cache';
const DB_VERSION = 1;
const STORE_NAME = 'audio_chunks';
const MAX_CACHE_SIZE = 500 * 1024 * 1024; // 500MB default
const MAX_AGE_DAYS = 7; // Cache entries expire after 7 days

interface CachedChunk {
  key: string; // bookId:chunkIndex:voiceId
  bookId: string;
  chunkIndex: number;
  voiceId: string;
  audioBlob: Blob;
  duration: number;
  size: number;
  cachedAt: number;
  lastAccessed: number;
}

interface CacheStats {
  totalSize: number;
  entryCount: number;
  oldestEntry: number | null;
  newestEntry: number | null;
}

class AudioCacheService {
  private db: IDBDatabase | null = null;
  private isInitialized = false;
  private initPromise: Promise<void> | null = null;

  /**
   * Initialize the IndexedDB database.
   */
  async init(): Promise<void> {
    if (this.isInitialized) return;

    if (this.initPromise) {
      return this.initPromise;
    }

    this.initPromise = new Promise((resolve, reject) => {
      if (!window.indexedDB) {
        console.warn('IndexedDB not supported, audio caching disabled');
        resolve();
        return;
      }

      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        console.error('Failed to open audio cache database');
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        this.isInitialized = true;
        console.log('Audio cache initialized');
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create object store if it doesn't exist
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'key' });
          store.createIndex('bookId', 'bookId', { unique: false });
          store.createIndex('cachedAt', 'cachedAt', { unique: false });
          store.createIndex('lastAccessed', 'lastAccessed', { unique: false });
        }
      };
    });

    return this.initPromise;
  }

  /**
   * Generate cache key for a chunk.
   */
  private getCacheKey(bookId: string, chunkIndex: number, voiceId: string): string {
    return `${bookId}:${chunkIndex}:${voiceId}`;
  }

  /**
   * Store audio chunk in cache.
   */
  async cacheChunk(
    bookId: string,
    chunkIndex: number,
    voiceId: string,
    audioBlob: Blob,
    duration: number
  ): Promise<void> {
    await this.init();
    if (!this.db) return;

    const key = this.getCacheKey(bookId, chunkIndex, voiceId);
    const now = Date.now();

    const entry: CachedChunk = {
      key,
      bookId,
      chunkIndex,
      voiceId,
      audioBlob,
      duration,
      size: audioBlob.size,
      cachedAt: now,
      lastAccessed: now,
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.put(entry);

      request.onsuccess = () => {
        // Check cache size and evict if necessary
        this.evictIfNeeded().then(resolve).catch(reject);
      };

      request.onerror = () => {
        console.error('Failed to cache audio chunk:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Retrieve audio chunk from cache.
   */
  async getChunk(
    bookId: string,
    chunkIndex: number,
    voiceId: string
  ): Promise<{ audioUrl: string; duration: number } | null> {
    await this.init();
    if (!this.db) return null;

    const key = this.getCacheKey(bookId, chunkIndex, voiceId);

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get(key);

      request.onsuccess = () => {
        const entry = request.result as CachedChunk | undefined;

        if (!entry) {
          resolve(null);
          return;
        }

        // Check if expired
        const age = Date.now() - entry.cachedAt;
        if (age > MAX_AGE_DAYS * 24 * 60 * 60 * 1000) {
          // Delete expired entry
          store.delete(key);
          resolve(null);
          return;
        }

        // Update last accessed time
        entry.lastAccessed = Date.now();
        store.put(entry);

        // Create blob URL
        const audioUrl = URL.createObjectURL(entry.audioBlob);
        resolve({ audioUrl, duration: entry.duration });
      };

      request.onerror = () => {
        console.error('Failed to retrieve cached chunk:', request.error);
        resolve(null);
      };
    });
  }

  /**
   * Check if a chunk is cached.
   */
  async hasChunk(
    bookId: string,
    chunkIndex: number,
    voiceId: string
  ): Promise<boolean> {
    await this.init();
    if (!this.db) return false;

    const key = this.getCacheKey(bookId, chunkIndex, voiceId);

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getKey(key);

      request.onsuccess = () => {
        resolve(request.result !== undefined);
      };

      request.onerror = () => {
        resolve(false);
      };
    });
  }

  /**
   * Get cache statistics.
   */
  async getStats(): Promise<CacheStats> {
    await this.init();
    if (!this.db) {
      return { totalSize: 0, entryCount: 0, oldestEntry: null, newestEntry: null };
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getAll();

      request.onsuccess = () => {
        const entries = request.result as CachedChunk[];
        const totalSize = entries.reduce((sum, e) => sum + e.size, 0);
        const timestamps = entries.map((e) => e.cachedAt);

        resolve({
          totalSize,
          entryCount: entries.length,
          oldestEntry: timestamps.length ? Math.min(...timestamps) : null,
          newestEntry: timestamps.length ? Math.max(...timestamps) : null,
        });
      };

      request.onerror = () => {
        resolve({ totalSize: 0, entryCount: 0, oldestEntry: null, newestEntry: null });
      };
    });
  }

  /**
   * Evict old entries if cache size exceeds limit.
   */
  private async evictIfNeeded(): Promise<void> {
    const stats = await this.getStats();

    if (stats.totalSize <= MAX_CACHE_SIZE) return;

    // Get all entries sorted by last accessed (LRU)
    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const index = store.index('lastAccessed');
      const request = index.openCursor();

      let freedSpace = 0;
      const targetFree = stats.totalSize - MAX_CACHE_SIZE * 0.8; // Free 20% of max

      request.onsuccess = () => {
        const cursor = request.result;
        if (!cursor || freedSpace >= targetFree) {
          resolve();
          return;
        }

        const entry = cursor.value as CachedChunk;
        freedSpace += entry.size;
        cursor.delete();
        cursor.continue();
      };

      request.onerror = () => {
        resolve();
      };
    });
  }

  /**
   * Clear all cached audio for a specific book.
   */
  async clearBook(bookId: string): Promise<void> {
    await this.init();
    if (!this.db) return;

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const index = store.index('bookId');
      const request = index.openCursor(IDBKeyRange.only(bookId));

      request.onsuccess = () => {
        const cursor = request.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        } else {
          resolve();
        }
      };

      request.onerror = () => {
        resolve();
      };
    });
  }

  /**
   * Clear all cached audio.
   */
  async clearAll(): Promise<void> {
    await this.init();
    if (!this.db) return;

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.clear();

      request.onsuccess = () => resolve();
      request.onerror = () => resolve();
    });
  }

  /**
   * Convert base64 data URL to Blob.
   */
  dataUrlToBlob(dataUrl: string): Blob {
    const parts = dataUrl.split(',');
    const mime = parts[0].match(/:(.*?);/)?.[1] || 'audio/mp3';
    const bstr = atob(parts[1]);
    const u8arr = new Uint8Array(bstr.length);

    for (let i = 0; i < bstr.length; i++) {
      u8arr[i] = bstr.charCodeAt(i);
    }

    return new Blob([u8arr], { type: mime });
  }
}

// Singleton instance
export const audioCache = new AudioCacheService();

// Format bytes for display
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
