import { useEffect, useState, useCallback } from 'react';
import { devotionalDB } from '@/lib/db';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

/**
 * useOfflineSync - Manages offline actions and synchronization
 * Queues actions when offline and syncs them when back online
 */
export function useOfflineSync() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingActions, setPendingActions] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const { toast } = useToast();

  /**
   * Update the count of pending sync actions
   */
  const updatePendingCount = useCallback(async () => {
    try {
      const queue = await devotionalDB.getSyncQueue();
      setPendingActions(queue.length);
    } catch (error) {
      console.error('Failed to update pending count:', error);
    }
  }, []);

  /**
   * Queue an action for offline sync
   */
  const queueAction = useCallback(async (action: {
    action: 'like' | 'unlike' | 'bookmark' | 'unbookmark' | 'comment' | 'reading_progress';
    target_id: string;
    payload?: any;
  }) => {
    try {
      await devotionalDB.addToSyncQueue(action);
      await updatePendingCount();

      // Try immediate sync if online
      if (navigator.onLine) {
        processQueue();
      } else {
        toast({
          title: 'Saved offline',
          description: 'Your action will sync when you\'re back online',
          duration: 2000
        });
      }
    } catch (error) {
      console.error('Failed to queue action:', error);
      toast({
        title: 'Error',
        description: 'Failed to save action',
        variant: 'destructive'
      });
    }
  }, [updatePendingCount, toast]);

  /**
   * Process the sync queue
   */
  const processQueue = useCallback(async () => {
    if (isSyncing || !navigator.onLine) return;

    setIsSyncing(true);
    const queue = await devotionalDB.getSyncQueue();

    if (queue.length === 0) {
      setIsSyncing(false);
      return;
    }

    let successCount = 0;
    let errorCount = 0;

    for (const item of queue) {
      try {
        // Process action based on type
        switch (item.action) {
          case 'like':
            await apiClient.likeDevotional(item.target_id);
            break;
          case 'unlike':
            await apiClient.likeDevotional(item.target_id); // Toggle
            break;
          case 'bookmark':
            await apiClient.bookmarkDevotional(item.target_id);
            break;
          case 'unbookmark':
            await apiClient.bookmarkDevotional(item.target_id); // Toggle
            break;
          case 'comment':
            if (item.payload?.devotional_id && item.payload?.text) {
              await apiClient.createComment(item.payload.devotional_id, {
                text: item.payload.text,
                parent_comment_id: item.payload.parent_comment_id
              });
            }
            break;
          case 'reading_progress':
            if (item.payload) {
              await apiClient.trackReading(item.target_id, item.payload);
            }
            break;
          default:
            console.warn('Unknown action type:', item.action);
        }

        // Success - remove from queue
        await devotionalDB.removeFromSyncQueue(item.id!);
        successCount++;
      } catch (error) {
        console.error('Sync failed for action:', item, error);
        errorCount++;

        // Increment retry count
        if (item.retry_count < 3) {
          await devotionalDB.incrementRetryCount(item.id!);
        } else {
          // Max retries reached - remove from queue
          await devotionalDB.removeFromSyncQueue(item.id!);
          console.warn('Max retries reached, removing action:', item);
        }
      }
    }

    await updatePendingCount();
    setIsSyncing(false);

    // Show toast if any actions were synced
    if (successCount > 0) {
      toast({
        title: 'Synced successfully',
        description: `${successCount} action(s) synced${errorCount > 0 ? `, ${errorCount} failed` : ''}`,
        duration: 3000
      });
    } else if (errorCount > 0) {
      toast({
        title: 'Sync failed',
        description: `Failed to sync ${errorCount} action(s). Will retry later.`,
        variant: 'destructive',
        duration: 3000
      });
    }
  }, [isSyncing, toast, updatePendingCount]);

  // Setup online/offline listeners
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      toast({
        title: 'Back online',
        description: 'Syncing your changes...',
        duration: 2000
      });
      // Wait a bit for connection to stabilize
      setTimeout(() => processQueue(), 1000);
    };

    const handleOffline = () => {
      setIsOnline(false);
      toast({
        title: 'You\'re offline',
        description: 'Your actions will be saved and synced later',
        duration: 3000
      });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initial count
    updatePendingCount();

    // Process queue on visibility change (when tab becomes active)
    const handleVisibilityChange = () => {
      if (!document.hidden && navigator.onLine) {
        processQueue();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [processQueue, updatePendingCount, toast]);

  return {
    isOnline,
    pendingActions,
    isSyncing,
    queueAction,
    processQueue
  };
}
