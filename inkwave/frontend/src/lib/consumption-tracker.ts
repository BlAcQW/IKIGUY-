/**
 * Consumption Tracker
 *
 * Unified tracking for all book consumption activity.
 * Single source of truth for both user and admin dashboards.
 *
 * NON-NEGOTIABLE requirements:
 * - Tracking starts when audio actually plays, not on click
 * - Progress updates on a timer (every 30 seconds)
 * - Completion is deterministic (when last chunk ends)
 * - AI narration counts as listening time
 * - Survives page refreshes via session recovery
 */

import { api } from './api';

export type ConsumptionMode = 'manual_reading' | 'audio_playback' | 'ai_voice_narration';
export type ConsumptionEventType =
  | 'book_opened'
  | 'reading_started'
  | 'listening_started'
  | 'progress_update'
  | 'paused'
  | 'resumed'
  | 'completed';

interface ConsumptionState {
  sessionId: string;
  bookId: string;
  bookTitle?: string;
  bookAuthor?: string;
  mode: ConsumptionMode;
  isActive: boolean;
  startedAt: number;
  lastUpdateAt: number;
  cumulativeTimeSeconds: number;
  chunkIndex: number;
  positionSeconds: number;
  totalChunks: number;
  chunksConsumed: Set<number>;
  // Billing tracking - real-time credits charged this session
  sessionCostCredits: number;
  lastBillingSuccess: boolean;
}

// Billing response from backend
export interface BillingInfo {
  duration_seconds: number;
  duration_minutes: number;
  credits_charged: number;
  billing_success: boolean;
}

// Callback for billing updates - UI can subscribe to this
export type BillingCallback = (info: BillingInfo, totalSessionCost: number) => void;

// Browser/device detection
function detectDevice(): { deviceType: string; browser: string } {
  const ua = navigator.userAgent;
  let browser = 'unknown';
  let deviceType = 'desktop';

  // Detect browser
  if (ua.includes('Firefox')) browser = 'firefox';
  else if (ua.includes('Chrome') && !ua.includes('Edg')) browser = 'chrome';
  else if (ua.includes('Safari') && !ua.includes('Chrome')) browser = 'safari';
  else if (ua.includes('Edg')) browser = 'edge';
  else if (ua.includes('MSIE') || ua.includes('Trident')) browser = 'ie';

  // Detect device type
  if (/Mobile|Android|iPhone|iPod/.test(ua)) {
    deviceType = 'mobile';
  } else if (/Tablet|iPad/.test(ua)) {
    deviceType = 'tablet';
  }

  return { browser, deviceType };
}

/**
 * Consumption Tracker Class
 *
 * Manages tracking for a single consumption session.
 */
export class ConsumptionTracker {
  private state: ConsumptionState | null = null;
  private progressTimer: ReturnType<typeof setInterval> | null = null;
  private readonly PROGRESS_INTERVAL_MS = 30000; // 30 seconds
  private billingCallbacks: Set<BillingCallback> = new Set();

  /**
   * Subscribe to billing updates for UI display.
   * Returns unsubscribe function.
   */
  onBillingUpdate(callback: BillingCallback): () => void {
    this.billingCallbacks.add(callback);
    return () => this.billingCallbacks.delete(callback);
  }

  /**
   * Get current session cost in credits.
   */
  getSessionCost(): number {
    return this.state?.sessionCostCredits ?? 0;
  }

  /**
   * Initialize tracking for a book.
   * Call this when entering the player page.
   */
  async initSession(
    sessionId: string,
    bookId: string,
    totalChunks: number,
    bookTitle?: string,
    bookAuthor?: string
  ): Promise<void> {
    // Try to recover previous session state
    try {
      const response = await api.consumption.getSessionProgress(sessionId);
      const data = response.data;

      if (data.found) {
        // Recover from previous state
        this.state = {
          sessionId,
          bookId,
          bookTitle,
          bookAuthor,
          mode: data.consumption_mode || 'audio_playback',
          isActive: false, // Will be activated on actual playback
          startedAt: 0,
          lastUpdateAt: Date.now(),
          cumulativeTimeSeconds: data.cumulative_time_seconds || 0,
          chunkIndex: data.chunk_index || 0,
          positionSeconds: data.position_seconds || 0,
          totalChunks,
          chunksConsumed: new Set(),
          sessionCostCredits: 0, // Fresh billing for this session
          lastBillingSuccess: true,
        };
        console.log('[ConsumptionTracker] Recovered session state:', {
          cumulativeTime: this.state.cumulativeTimeSeconds,
          chunkIndex: this.state.chunkIndex,
        });
      } else {
        // Fresh session
        this.state = {
          sessionId,
          bookId,
          bookTitle,
          bookAuthor,
          mode: 'audio_playback',
          isActive: false,
          startedAt: 0,
          lastUpdateAt: Date.now(),
          cumulativeTimeSeconds: 0,
          chunkIndex: 0,
          positionSeconds: 0,
          totalChunks,
          chunksConsumed: new Set(),
          sessionCostCredits: 0,
          lastBillingSuccess: true,
        };
      }
    } catch (error) {
      // Fresh session on error
      console.warn('[ConsumptionTracker] Failed to recover session, starting fresh:', error);
      this.state = {
        sessionId,
        bookId,
        bookTitle,
        bookAuthor,
        mode: 'audio_playback',
        isActive: false,
        startedAt: 0,
        lastUpdateAt: Date.now(),
        cumulativeTimeSeconds: 0,
        chunkIndex: 0,
        positionSeconds: 0,
        totalChunks,
        chunksConsumed: new Set(),
        sessionCostCredits: 0,
        lastBillingSuccess: true,
      };
    }

    // Record book opened event
    await this.recordEvent('book_opened');
  }

  /**
   * Called when audio actually starts playing.
   * NON-NEGOTIABLE: Tracking starts here, not on click.
   */
  async onPlaybackStarted(
    mode: ConsumptionMode,
    chunkIndex: number,
    positionSeconds: number = 0
  ): Promise<void> {
    if (!this.state) {
      console.warn('[ConsumptionTracker] Cannot start playback without session');
      return;
    }

    this.state.mode = mode;
    this.state.chunkIndex = chunkIndex;
    this.state.positionSeconds = positionSeconds;
    this.state.isActive = true;
    this.state.startedAt = Date.now();
    this.state.lastUpdateAt = Date.now();

    // Record listening/reading started
    const eventType: ConsumptionEventType =
      mode === 'manual_reading' ? 'reading_started' : 'listening_started';
    await this.recordEvent(eventType);

    // Start progress timer
    this.startProgressTimer();

    console.log('[ConsumptionTracker] Playback started:', {
      mode,
      chunkIndex,
      positionSeconds,
    });
  }

  /**
   * Called when playback is paused.
   */
  async onPaused(): Promise<void> {
    if (!this.state || !this.state.isActive) return;

    // Update cumulative time
    const elapsed = (Date.now() - this.state.lastUpdateAt) / 1000;
    this.state.cumulativeTimeSeconds += elapsed;
    this.state.isActive = false;

    // Stop timer
    this.stopProgressTimer();

    // Record pause event with current progress
    await this.recordEvent('paused');
    await this.sendProgressUpdate();

    console.log('[ConsumptionTracker] Paused:', {
      cumulativeTime: this.state.cumulativeTimeSeconds,
    });
  }

  /**
   * Called when playback is resumed.
   */
  async onResumed(): Promise<void> {
    if (!this.state) return;

    this.state.isActive = true;
    this.state.lastUpdateAt = Date.now();

    await this.recordEvent('resumed');
    this.startProgressTimer();

    console.log('[ConsumptionTracker] Resumed');
  }

  /**
   * Called when chunk changes.
   */
  async onChunkChanged(
    chunkIndex: number,
    positionSeconds: number = 0
  ): Promise<void> {
    if (!this.state) return;

    // Mark previous chunk as consumed
    if (this.state.chunkIndex !== chunkIndex) {
      this.state.chunksConsumed.add(this.state.chunkIndex);
    }

    this.state.chunkIndex = chunkIndex;
    this.state.positionSeconds = positionSeconds;

    // Send progress update
    if (this.state.isActive) {
      const elapsed = (Date.now() - this.state.lastUpdateAt) / 1000;
      this.state.cumulativeTimeSeconds += elapsed;
      this.state.lastUpdateAt = Date.now();
      await this.sendProgressUpdate();
    }

    console.log('[ConsumptionTracker] Chunk changed:', { chunkIndex });
  }

  /**
   * Called when position within chunk updates.
   * This is for internal state tracking, not for sending updates.
   */
  onPositionUpdate(positionSeconds: number): void {
    if (!this.state) return;
    this.state.positionSeconds = positionSeconds;
  }

  /**
   * Called when the last chunk ends.
   * NON-NEGOTIABLE: This is the deterministic completion event.
   */
  async onBookCompleted(): Promise<void> {
    if (!this.state) return;

    // Final time update
    if (this.state.isActive) {
      const elapsed = (Date.now() - this.state.lastUpdateAt) / 1000;
      this.state.cumulativeTimeSeconds += elapsed;
    }

    // Mark final chunk as consumed
    this.state.chunksConsumed.add(this.state.chunkIndex);

    // Stop timer
    this.stopProgressTimer();
    this.state.isActive = false;

    // Send completion
    try {
      await api.consumption.recordCompletion({
        session_id: this.state.sessionId,
        book_id: this.state.bookId,
        consumption_mode: this.state.mode,
        total_chunks: this.state.totalChunks,
        final_chunk_index: this.state.chunkIndex,
        total_time_seconds: this.state.cumulativeTimeSeconds,
        all_chunks_consumed: this.state.chunksConsumed.size === this.state.totalChunks,
        chunk_indices_consumed: Array.from(this.state.chunksConsumed),
      });

      console.log('[ConsumptionTracker] Book completed:', {
        totalTime: this.state.cumulativeTimeSeconds,
        chunksConsumed: this.state.chunksConsumed.size,
      });
    } catch (error) {
      console.error('[ConsumptionTracker] Failed to record completion:', error);
    }
  }

  /**
   * Clean up when leaving the player.
   */
  async cleanup(): Promise<void> {
    // Send final progress update if active
    if (this.state?.isActive) {
      const elapsed = (Date.now() - this.state.lastUpdateAt) / 1000;
      this.state.cumulativeTimeSeconds += elapsed;
      await this.sendProgressUpdate();
    }

    this.stopProgressTimer();
    this.state = null;
    console.log('[ConsumptionTracker] Cleaned up');
  }

  /**
   * Get current state for UI display.
   */
  getState(): Readonly<ConsumptionState> | null {
    return this.state;
  }

  // Private methods

  private startProgressTimer(): void {
    if (this.progressTimer) return;

    this.progressTimer = setInterval(async () => {
      if (this.state?.isActive) {
        const elapsed = (Date.now() - this.state.lastUpdateAt) / 1000;
        this.state.cumulativeTimeSeconds += elapsed;
        this.state.lastUpdateAt = Date.now();
        await this.sendProgressUpdate();
      }
    }, this.PROGRESS_INTERVAL_MS);

    console.log('[ConsumptionTracker] Progress timer started');
  }

  private stopProgressTimer(): void {
    if (this.progressTimer) {
      clearInterval(this.progressTimer);
      this.progressTimer = null;
      console.log('[ConsumptionTracker] Progress timer stopped');
    }
  }

  private async sendProgressUpdate(): Promise<void> {
    if (!this.state) return;

    try {
      const isFinalChunk = this.state.chunkIndex === this.state.totalChunks - 1;
      const elapsed = this.state.isActive
        ? (Date.now() - this.state.lastUpdateAt) / 1000
        : 0;

      const response = await api.consumption.updateProgress({
        session_id: this.state.sessionId,
        book_id: this.state.bookId,
        consumption_mode: this.state.mode,
        chunk_index: this.state.chunkIndex,
        position_seconds: this.state.positionSeconds,
        duration_since_last_update: elapsed,
        cumulative_time_seconds: this.state.cumulativeTimeSeconds,
        total_chunks: this.state.totalChunks,
        is_final_chunk: isFinalChunk,
      });

      // Handle billing response
      const billing = response.data?.billing as BillingInfo | undefined;
      if (billing) {
        // Update session cost
        if (billing.billing_success && billing.credits_charged > 0) {
          this.state.sessionCostCredits += billing.credits_charged;
          this.state.lastBillingSuccess = true;
          console.log('[ConsumptionTracker] Billing charged:', {
            charged: billing.credits_charged,
            totalSessionCost: this.state.sessionCostCredits,
          });
        } else {
          this.state.lastBillingSuccess = billing.billing_success;
          if (!billing.billing_success) {
            console.warn('[ConsumptionTracker] Billing failed - insufficient balance?');
          }
        }

        // Notify all subscribers
        for (const callback of this.billingCallbacks) {
          try {
            callback(billing, this.state.sessionCostCredits);
          } catch (cbError) {
            console.error('[ConsumptionTracker] Billing callback error:', cbError);
          }
        }
      }
    } catch (error) {
      console.error('[ConsumptionTracker] Failed to send progress update:', error);
    }
  }

  private async recordEvent(eventType: ConsumptionEventType): Promise<void> {
    if (!this.state) return;

    const { deviceType, browser } = detectDevice();
    const progress =
      this.state.totalChunks > 0
        ? ((this.state.chunkIndex + 1) / this.state.totalChunks) * 100
        : 0;

    try {
      await api.consumption.recordEvent({
        book_id: this.state.bookId,
        session_id: this.state.sessionId,
        event_type: eventType,
        consumption_mode: this.state.mode,
        chunk_index: this.state.chunkIndex,
        total_chunks: this.state.totalChunks,
        progress_percentage: Math.min(progress, 100),
        position_seconds: this.state.positionSeconds,
        cumulative_time_seconds: this.state.cumulativeTimeSeconds,
        book_title: this.state.bookTitle,
        book_author: this.state.bookAuthor,
        device_type: deviceType,
        browser,
        user_agent: navigator.userAgent,
      });
    } catch (error) {
      console.error('[ConsumptionTracker] Failed to record event:', eventType, error);
    }
  }
}

// Singleton instance for global access
export const consumptionTracker = new ConsumptionTracker();
