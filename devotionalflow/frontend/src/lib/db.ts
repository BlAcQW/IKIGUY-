import { openDB, DBSchema, IDBPDatabase } from 'idb';

/**
 * IndexedDB schema for FreshManna offline storage
 */
interface FreshMannaDB extends DBSchema {
  devotionals: {
    key: string;
    value: {
      id: string;
      title: string;
      content: any[];
      excerpt: string;
      author_id: string;
      author_name: string;
      cover_image_url?: string;
      audio_url?: string;
      reading_time_minutes: number;
      published_at: string;
      cached_at: string;
      categories: string[];
      likes_count: number;
      comments_count: number;
      full_content_cached: boolean;
    };
    indexes: { 'by_cached_at': string; 'by_published_at': string };
  };
  bookmarks: {
    key: string;
    value: {
      id: string;
      devotional_id: string;
      devotional_title: string;
      devotional_excerpt: string;
      created_at: string;
      synced: boolean;
    };
    indexes: { 'by_created_at': string };
  };
  reading_history: {
    key: string;
    value: {
      devotional_id: string;
      reading_progress: number;
      listening_progress: number;
      last_read_at: string;
      time_spent_seconds: number;
      synced: boolean;
    };
    indexes: { 'by_last_read_at': string };
  };
  sync_queue: {
    key: number;
    value: {
      id?: number;
      action: 'like' | 'unlike' | 'bookmark' | 'unbookmark' | 'comment' | 'reading_progress';
      target_id: string;
      payload: any;
      created_at: string;
      retry_count: number;
    };
    indexes: { 'by_created_at': string };
  };
}

/**
 * DevotionalDB - IndexedDB wrapper for offline data storage
 * Manages devotionals, bookmarks, reading history, and sync queue
 */
class DevotionalDB {
  private db: IDBPDatabase<FreshMannaDB> | null = null;
  private readonly DB_NAME = 'devotionalflow-db';
  private readonly DB_VERSION = 1;

  /**
   * Initialize database connection and create object stores
   */
  async init(): Promise<void> {
    if (this.db) return;

    this.db = await openDB<FreshMannaDB>(this.DB_NAME, this.DB_VERSION, {
      upgrade(db) {
        // Devotionals store
        if (!db.objectStoreNames.contains('devotionals')) {
          const devotionalStore = db.createObjectStore('devotionals', { keyPath: 'id' });
          devotionalStore.createIndex('by_cached_at', 'cached_at');
          devotionalStore.createIndex('by_published_at', 'published_at');
        }

        // Bookmarks store
        if (!db.objectStoreNames.contains('bookmarks')) {
          const bookmarkStore = db.createObjectStore('bookmarks', { keyPath: 'id' });
          bookmarkStore.createIndex('by_created_at', 'created_at');
        }

        // Reading history store
        if (!db.objectStoreNames.contains('reading_history')) {
          const historyStore = db.createObjectStore('reading_history', { keyPath: 'devotional_id' });
          historyStore.createIndex('by_last_read_at', 'last_read_at');
        }

        // Sync queue store
        if (!db.objectStoreNames.contains('sync_queue')) {
          const queueStore = db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true });
          queueStore.createIndex('by_created_at', 'created_at');
        }
      }
    });
  }

  // ============ Devotionals ============

  /**
   * Cache a devotional for offline access
   */
  async cacheDevotional(devotional: any): Promise<void> {
    await this.init();
    await this.db!.put('devotionals', {
      ...devotional,
      cached_at: new Date().toISOString(),
      full_content_cached: true
    });
  }

  /**
   * Get a cached devotional by ID
   */
  async getCachedDevotional(id: string): Promise<any | null> {
    await this.init();
    return await this.db!.get('devotionals', id) || null;
  }

  /**
   * Get all cached devotionals sorted by cache time
   */
  async getCachedDevotionals(): Promise<any[]> {
    await this.init();
    return await this.db!.getAllFromIndex('devotionals', 'by_cached_at');
  }

  /**
   * Clear old devotionals keeping only the most recent ones
   */
  async clearOldDevotionals(keepCount: number = 100): Promise<void> {
    await this.init();
    const all = await this.getCachedDevotionals();
    if (all.length > keepCount) {
      const toDelete = all.slice(0, all.length - keepCount);
      for (const item of toDelete) {
        await this.db!.delete('devotionals', item.id);
      }
    }
  }

  // ============ Bookmarks ============

  /**
   * Add a bookmark to offline storage
   */
  async addBookmark(bookmark: any): Promise<void> {
    await this.init();
    await this.db!.put('bookmarks', {
      ...bookmark,
      synced: false
    });
  }

  /**
   * Remove a bookmark from offline storage
   */
  async removeBookmark(id: string): Promise<void> {
    await this.init();
    await this.db!.delete('bookmarks', id);
  }

  /**
   * Get all bookmarks
   */
  async getBookmarks(): Promise<any[]> {
    await this.init();
    return await this.db!.getAllFromIndex('bookmarks', 'by_created_at');
  }

  // ============ Reading History ============

  /**
   * Update reading progress for a devotional
   */
  async updateReadingProgress(devotional_id: string, progress: number, timeSpent: number = 0): Promise<void> {
    await this.init();
    const existing = await this.db!.get('reading_history', devotional_id);
    await this.db!.put('reading_history', {
      devotional_id,
      reading_progress: progress,
      listening_progress: existing?.listening_progress || 0,
      last_read_at: new Date().toISOString(),
      time_spent_seconds: (existing?.time_spent_seconds || 0) + timeSpent,
      synced: false
    });
  }

  /**
   * Update listening progress for a devotional audio
   */
  async updateListeningProgress(devotional_id: string, progress: number): Promise<void> {
    await this.init();
    const existing = await this.db!.get('reading_history', devotional_id);
    await this.db!.put('reading_history', {
      devotional_id,
      reading_progress: existing?.reading_progress || 0,
      listening_progress: progress,
      last_read_at: new Date().toISOString(),
      time_spent_seconds: existing?.time_spent_seconds || 0,
      synced: false
    });
  }

  /**
   * Get reading history for all devotionals
   */
  async getReadingHistory(): Promise<any[]> {
    await this.init();
    return await this.db!.getAllFromIndex('reading_history', 'by_last_read_at');
  }

  /**
   * Get reading progress for a specific devotional
   */
  async getReadingProgress(devotional_id: string): Promise<any | null> {
    await this.init();
    return await this.db!.get('reading_history', devotional_id) || null;
  }

  // ============ Sync Queue ============

  /**
   * Add an action to the sync queue for offline operations
   */
  async addToSyncQueue(action: {
    action: 'like' | 'unlike' | 'bookmark' | 'unbookmark' | 'comment' | 'reading_progress';
    target_id: string;
    payload?: any;
  }): Promise<void> {
    await this.init();
    await this.db!.add('sync_queue', {
      ...action,
      created_at: new Date().toISOString(),
      retry_count: 0
    });
  }

  /**
   * Get all pending sync actions
   */
  async getSyncQueue(): Promise<any[]> {
    await this.init();
    return await this.db!.getAllFromIndex('sync_queue', 'by_created_at');
  }

  /**
   * Remove a completed sync action from queue
   */
  async removeFromSyncQueue(id: number): Promise<void> {
    await this.init();
    await this.db!.delete('sync_queue', id);
  }

  /**
   * Clear all sync queue items
   */
  async clearSyncQueue(): Promise<void> {
    await this.init();
    await this.db!.clear('sync_queue');
  }

  /**
   * Increment retry count for a failed sync action
   */
  async incrementRetryCount(id: number): Promise<void> {
    await this.init();
    const item = await this.db!.get('sync_queue', id);
    if (item) {
      await this.db!.put('sync_queue', {
        ...item,
        retry_count: item.retry_count + 1
      });
    }
  }

  // ============ Utility Methods ============

  /**
   * Get storage usage statistics
   */
  async getStorageStats(): Promise<{
    devotionals: number;
    bookmarks: number;
    history: number;
    syncQueue: number;
  }> {
    await this.init();
    return {
      devotionals: await this.db!.count('devotionals'),
      bookmarks: await this.db!.count('bookmarks'),
      history: await this.db!.count('reading_history'),
      syncQueue: await this.db!.count('sync_queue')
    };
  }

  /**
   * Clear all data from the database
   */
  async clearAll(): Promise<void> {
    await this.init();
    await this.db!.clear('devotionals');
    await this.db!.clear('bookmarks');
    await this.db!.clear('reading_history');
    await this.db!.clear('sync_queue');
  }
}

// Export singleton instance
export const devotionalDB = new DevotionalDB();
