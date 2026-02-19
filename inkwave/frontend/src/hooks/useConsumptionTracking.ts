/**
 * useConsumptionTracking Hook
 *
 * React hook for integrating consumption tracking with audio players.
 * Works with both legacy audio player and chunk-based player.
 *
 * NON-NEGOTIABLE requirements:
 * - Tracking starts when audio actually plays (not on click)
 * - Progress updates on a timer (every 30 seconds)
 * - Completion is deterministic (when last chunk ends)
 * - AI narration counts as listening time
 * - Survives page refreshes
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import {
  consumptionTracker,
  ConsumptionMode,
  BillingInfo,
} from '../lib/consumption-tracker';

interface UseConsumptionTrackingProps {
  sessionId: string | null;
  bookId: string;
  bookTitle?: string;
  bookAuthor?: string;
  totalChunks: number;
  isPlaying: boolean;
  currentChunkIndex: number;
  currentPosition: number;
  consumptionMode?: ConsumptionMode;
  enabled?: boolean;
}

interface UseConsumptionTrackingReturn {
  /** Mark that the book has been completed */
  markCompleted: () => Promise<void>;
  /** Clean up tracking (call on unmount) */
  cleanup: () => Promise<void>;
  /** Total credits charged this session (real-time) */
  sessionCostCredits: number;
  /** Whether last billing was successful */
  lastBillingSuccess: boolean;
  /** Last billing info from backend */
  lastBillingInfo: BillingInfo | null;
}

/**
 * Hook for tracking book consumption.
 *
 * Automatically tracks:
 * - Session initialization when entering player
 * - Playback start/pause events
 * - Chunk changes
 * - Position updates (for internal state)
 *
 * Must manually call:
 * - markCompleted() when book ends
 * - cleanup() on unmount
 */
export function useConsumptionTracking({
  sessionId,
  bookId,
  bookTitle,
  bookAuthor,
  totalChunks,
  isPlaying,
  currentChunkIndex,
  currentPosition,
  consumptionMode = 'audio_playback',
  enabled = true,
}: UseConsumptionTrackingProps): UseConsumptionTrackingReturn {
  const isInitialized = useRef(false);
  const wasPlaying = useRef(false);
  const lastChunkIndex = useRef(currentChunkIndex);
  const lastMode = useRef(consumptionMode);

  // Billing state - real-time tracking of session costs
  const [sessionCostCredits, setSessionCostCredits] = useState(0);
  const [lastBillingSuccess, setLastBillingSuccess] = useState(true);
  const [lastBillingInfo, setLastBillingInfo] = useState<BillingInfo | null>(null);

  // Subscribe to billing updates
  useEffect(() => {
    if (!enabled) return;

    const unsubscribe = consumptionTracker.onBillingUpdate(
      (billingInfo: BillingInfo, totalSessionCost: number) => {
        setLastBillingInfo(billingInfo);
        setSessionCostCredits(totalSessionCost);
        setLastBillingSuccess(billingInfo.billing_success);
        console.log('[useConsumptionTracking] Billing update:', {
          charged: billingInfo.credits_charged,
          totalSessionCost,
          success: billingInfo.billing_success,
        });
      }
    );

    return () => {
      unsubscribe();
    };
  }, [enabled]);

  // Initialize session when sessionId becomes available
  useEffect(() => {
    if (!enabled || !sessionId || !bookId || isInitialized.current) {
      return;
    }

    const initSession = async () => {
      try {
        await consumptionTracker.initSession(
          sessionId,
          bookId,
          totalChunks,
          bookTitle,
          bookAuthor
        );
        isInitialized.current = true;
        console.log('[useConsumptionTracking] Session initialized');
      } catch (error) {
        console.error('[useConsumptionTracking] Failed to initialize:', error);
      }
    };

    initSession();
  }, [enabled, sessionId, bookId, totalChunks, bookTitle, bookAuthor]);

  // Track play/pause state changes
  // NON-NEGOTIABLE: This fires when audio actually starts playing
  useEffect(() => {
    if (!enabled || !isInitialized.current) return;

    const handlePlayStateChange = async () => {
      if (isPlaying && !wasPlaying.current) {
        // Started playing
        await consumptionTracker.onPlaybackStarted(
          consumptionMode,
          currentChunkIndex,
          currentPosition
        );
      } else if (!isPlaying && wasPlaying.current) {
        // Paused
        await consumptionTracker.onPaused();
      }
      wasPlaying.current = isPlaying;
    };

    handlePlayStateChange();
  }, [enabled, isPlaying, consumptionMode, currentChunkIndex, currentPosition]);

  // Track chunk changes
  useEffect(() => {
    if (!enabled || !isInitialized.current) return;
    if (lastChunkIndex.current === currentChunkIndex) return;

    const handleChunkChange = async () => {
      await consumptionTracker.onChunkChanged(currentChunkIndex, currentPosition);
      lastChunkIndex.current = currentChunkIndex;
    };

    handleChunkChange();
  }, [enabled, currentChunkIndex, currentPosition]);

  // Track consumption mode changes (e.g., switching to AI voice)
  useEffect(() => {
    if (!enabled || !isInitialized.current) return;
    if (lastMode.current === consumptionMode) return;

    // If playing and mode changes, record as new listening session
    if (isPlaying) {
      const handleModeChange = async () => {
        // Pause current, start new with new mode
        await consumptionTracker.onPaused();
        await consumptionTracker.onPlaybackStarted(
          consumptionMode,
          currentChunkIndex,
          currentPosition
        );
        lastMode.current = consumptionMode;
      };
      handleModeChange();
    } else {
      lastMode.current = consumptionMode;
    }
  }, [enabled, consumptionMode, isPlaying, currentChunkIndex, currentPosition]);

  // Track position updates (for internal state)
  useEffect(() => {
    if (!enabled || !isInitialized.current) return;
    consumptionTracker.onPositionUpdate(currentPosition);
  }, [enabled, currentPosition]);

  // Mark book as completed
  const markCompleted = useCallback(async () => {
    if (!enabled) return;
    await consumptionTracker.onBookCompleted();
  }, [enabled]);

  // Cleanup on unmount
  const cleanup = useCallback(async () => {
    if (!enabled) return;
    await consumptionTracker.cleanup();
    isInitialized.current = false;
  }, [enabled]);

  // Auto-cleanup on unmount
  useEffect(() => {
    return () => {
      if (isInitialized.current) {
        consumptionTracker.cleanup();
      }
    };
  }, []);

  return {
    markCompleted,
    cleanup,
    sessionCostCredits,
    lastBillingSuccess,
    lastBillingInfo,
  };
}

export default useConsumptionTracking;
