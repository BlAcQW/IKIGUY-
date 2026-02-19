/**
 * Tracking utility for analytics, errors, and events.
 *
 * Provides easy-to-use functions for logging errors, tracking events,
 * and recording user behavior throughout the application.
 */

import { api } from './api';

// Offline queue for errors and events
interface QueuedError {
  type: string;
  error: Error | string;
  context: Record<string, any>;
  timestamp: string;
}

interface QueuedEvent {
  type: string;
  name: string;
  properties: Record<string, any>;
  timestamp: string;
}

const errorQueue: QueuedError[] = [];
const eventQueue: QueuedEvent[] = [];
const MAX_QUEUE_SIZE = 100;

// Process queued items when coming back online
if (typeof window !== 'undefined') {
  window.addEventListener('online', async () => {
    console.log('[Tracking] Back online, processing queued items...');

    // Process queued errors
    while (errorQueue.length > 0) {
      const queuedError = errorQueue.shift();
      if (queuedError) {
        try {
          await ErrorTracker.logError(
            queuedError.type,
            queuedError.error,
            { ...queuedError.context, queued_at: queuedError.timestamp }
          );
        } catch (e) {
          // If still fails, put it back
          errorQueue.unshift(queuedError);
          break;
        }
      }
    }

    // Process queued events
    while (eventQueue.length > 0) {
      const queuedEvent = eventQueue.shift();
      if (queuedEvent) {
        try {
          await EventTracker.trackEvent(
            queuedEvent.type,
            queuedEvent.name,
            { ...queuedEvent.properties, queued_at: queuedEvent.timestamp }
          );
        } catch (e) {
          // If still fails, put it back
          eventQueue.unshift(queuedEvent);
          break;
        }
      }
    }
  });
}

/**
 * Detect browser information from user agent.
 */
function detectBrowser(): { browser: string; device_type: string } {
  const ua = navigator.userAgent;
  let browser = 'unknown';
  let device_type = 'desktop';

  // Detect browser
  if (ua.includes('Firefox')) browser = 'firefox';
  else if (ua.includes('Chrome') && !ua.includes('Edg')) browser = 'chrome';
  else if (ua.includes('Safari') && !ua.includes('Chrome')) browser = 'safari';
  else if (ua.includes('Edg')) browser = 'edge';
  else if (ua.includes('MSIE') || ua.includes('Trident')) browser = 'ie';

  // Detect device type
  if (/Mobile|Android|iPhone|iPad|iPod/.test(ua)) {
    device_type = 'mobile';
  } else if (/Tablet|iPad/.test(ua)) {
    device_type = 'tablet';
  }

  return { browser, device_type };
}

/**
 * Error tracking service.
 */
export const ErrorTracker = {
  /**
   * Log an error.
   *
   * @param type - Error type (e.g., "audio_load_failed", "tts_timeout")
   * @param error - Error object or message
   * @param context - Additional context (book_id, chunk_index, etc.)
   */
  async logError(
    type: string,
    error: Error | string,
    context: Record<string, any> = {}
  ): Promise<void> {
    // If offline, queue the error for later
    if (!navigator.onLine) {
      if (errorQueue.length < MAX_QUEUE_SIZE) {
        errorQueue.push({
          type,
          error,
          context,
          timestamp: new Date().toISOString(),
        });
        console.log(`[ErrorTracker] Queued error (offline): ${type} (${errorQueue.length} in queue)`);
      }
      return;
    }

    try {
      const { browser, device_type } = detectBrowser();
      const errorMessage = typeof error === 'string' ? error : error.message;
      const stackTrace = typeof error === 'object' && error.stack ? error.stack : undefined;

      await api.tracking.logError({
        error_type: type,
        error_message: errorMessage,
        stack_trace: stackTrace,
        context: {
          ...context,
          url: window.location.href,
          timestamp: new Date().toISOString(),
        },
        user_agent: navigator.userAgent,
        browser,
        device_type,
      });

      // Also log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.error(`[ErrorTracker] ${type}:`, errorMessage, context);
      }
    } catch (e) {
      // Queue for retry if it's a network error
      const isNetworkError = e instanceof Error &&
        (e.message?.includes('fetch') || e.message?.includes('Network'));

      if (isNetworkError && errorQueue.length < MAX_QUEUE_SIZE) {
        errorQueue.push({
          type,
          error,
          context,
          timestamp: new Date().toISOString(),
        });
        console.log(`[ErrorTracker] Queued error (network failure): ${type}`);
      } else {
        // Silently fail - don't let error tracking break the app
        console.warn('[ErrorTracker] Failed to log error:', e);
      }
    }
  },

  /**
   * Log an audio loading failure.
   */
  async audioLoadFailed(bookId: string, chunkIndex: number, error: Error): Promise<void> {
    return this.logError('audio_load_failed', error, {
      book_id: bookId,
      chunk_index: chunkIndex,
    });
  },

  /**
   * Log an audio playback failure.
   */
  async audioPlaybackFailed(bookId: string, chunkIndex: number, error: Error): Promise<void> {
    return this.logError('audio_playback_failed', error, {
      book_id: bookId,
      chunk_index: chunkIndex,
    });
  },

  /**
   * Log a TTS generation failure.
   */
  async ttsGenerationFailed(bookId: string, chunkIndex: number, error: Error): Promise<void> {
    return this.logError('tts_generation_failed', error, {
      book_id: bookId,
      chunk_index: chunkIndex,
    });
  },

  /**
   * Log an autoplay blocked event.
   */
  async autoplayBlocked(bookId: string, chunkIndex: number): Promise<void> {
    return this.logError('autoplay_blocked', 'Browser blocked autoplay', {
      book_id: bookId,
      chunk_index: chunkIndex,
    });
  },

  /**
   * Log a network error.
   */
  async networkError(url: string, error: Error): Promise<void> {
    return this.logError('network_error', error, {
      url,
    });
  },
};

/**
 * Event tracking service.
 */
export const EventTracker = {
  /**
   * Track an event.
   *
   * @param type - Event type (e.g., "play_clicked", "bookmark_created")
   * @param name - Human-readable event name
   * @param properties - Event properties (book_id, session_id, etc.)
   */
  async trackEvent(
    type: string,
    name: string,
    properties: Record<string, any> = {}
  ): Promise<void> {
    // If offline, queue the event for later
    if (!navigator.onLine) {
      if (eventQueue.length < MAX_QUEUE_SIZE) {
        eventQueue.push({
          type,
          name,
          properties,
          timestamp: new Date().toISOString(),
        });
        console.log(`[EventTracker] Queued event (offline): ${type} (${eventQueue.length} in queue)`);
      }
      return;
    }

    try {
      await api.tracking.trackEvent({
        event_type: type,
        event_name: name,
        properties,
        page_url: window.location.href,
        referrer: document.referrer || undefined,
      });

      // Also log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`[EventTracker] ${type}:`, name, properties);
      }
    } catch (e) {
      // Queue for retry if it's a network error
      const isNetworkError = e instanceof Error &&
        (e.message?.includes('fetch') || e.message?.includes('Network'));

      if (isNetworkError && eventQueue.length < MAX_QUEUE_SIZE) {
        eventQueue.push({
          type,
          name,
          properties,
          timestamp: new Date().toISOString(),
        });
        console.log(`[EventTracker] Queued event (network failure): ${type}`);
      } else {
        // Silently fail
        console.warn('[EventTracker] Failed to track event:', e);
      }
    }
  },

  // Playback events
  playClicked(bookId: string, sessionId?: string, chunkIndex?: number): Promise<void> {
    return this.trackEvent('play_clicked', 'User clicked play button', {
      book_id: bookId,
      session_id: sessionId,
      chunk_index: chunkIndex,
    });
  },

  pauseClicked(bookId: string, sessionId?: string, chunkIndex?: number): Promise<void> {
    return this.trackEvent('pause_clicked', 'User clicked pause button', {
      book_id: bookId,
      session_id: sessionId,
      chunk_index: chunkIndex,
    });
  },

  skipForward(bookId: string, sessionId?: string, seconds?: number): Promise<void> {
    return this.trackEvent('skip_forward', 'User skipped forward', {
      book_id: bookId,
      session_id: sessionId,
      seconds,
    });
  },

  skipBackward(bookId: string, sessionId?: string, seconds?: number): Promise<void> {
    return this.trackEvent('skip_backward', 'User skipped backward', {
      book_id: bookId,
      session_id: sessionId,
      seconds,
    });
  },

  speedChanged(bookId: string, sessionId?: string, speed?: number): Promise<void> {
    return this.trackEvent('speed_changed', 'User changed playback speed', {
      book_id: bookId,
      session_id: sessionId,
      speed,
    });
  },

  volumeChanged(bookId: string, sessionId?: string, volume?: number): Promise<void> {
    return this.trackEvent('volume_changed', 'User changed volume', {
      book_id: bookId,
      session_id: sessionId,
      volume,
    });
  },

  chunkChanged(bookId: string, sessionId?: string, chunkIndex?: number): Promise<void> {
    return this.trackEvent('chunk_changed', 'User navigated to different chunk', {
      book_id: bookId,
      session_id: sessionId,
      chunk_index: chunkIndex,
    });
  },

  // Navigation events
  bookViewed(bookId: string): Promise<void> {
    return this.trackEvent('book_viewed', 'User viewed book detail page', {
      book_id: bookId,
    });
  },

  bookOpened(bookId: string, sessionId?: string): Promise<void> {
    return this.trackEvent('book_opened', 'User opened book player', {
      book_id: bookId,
      session_id: sessionId,
    });
  },

  chapterSelected(bookId: string, chapterIndex: number): Promise<void> {
    return this.trackEvent('chapter_selected', 'User selected a chapter', {
      book_id: bookId,
      chapter_index: chapterIndex,
    });
  },

  // Feature usage
  bookmarkCreated(bookId: string, sessionId?: string, chunkIndex?: number): Promise<void> {
    return this.trackEvent('bookmark_created', 'User created a bookmark', {
      book_id: bookId,
      session_id: sessionId,
      chunk_index: chunkIndex,
    });
  },

  bookmarkUsed(bookId: string, sessionId?: string, bookmarkId?: string): Promise<void> {
    return this.trackEvent('bookmark_used', 'User jumped to bookmark', {
      book_id: bookId,
      session_id: sessionId,
      bookmark_id: bookmarkId,
    });
  },

  qaOpened(bookId: string, sessionId?: string): Promise<void> {
    return this.trackEvent('qa_opened', 'User opened Q&A panel', {
      book_id: bookId,
      session_id: sessionId,
    });
  },

  questionTyped(bookId: string, sessionId?: string, questionLength?: number): Promise<void> {
    return this.trackEvent('question_typed', 'User typed a question', {
      book_id: bookId,
      session_id: sessionId,
      question_length: questionLength,
    });
  },

  questionSent(bookId: string, sessionId?: string, question?: string): Promise<void> {
    return this.trackEvent('question_sent', 'User sent a question', {
      book_id: bookId,
      session_id: sessionId,
      question_preview: question ? question.substring(0, 100) : undefined,
    });
  },

  responseReceived(bookId: string, sessionId?: string, responseTime?: number): Promise<void> {
    return this.trackEvent('response_received', 'AI response received', {
      book_id: bookId,
      session_id: sessionId,
      response_time_ms: responseTime,
    });
  },

  // Session events
  sessionStarted(bookId: string, sessionId: string): Promise<void> {
    return this.trackEvent('session_started', 'Reading session started', {
      book_id: bookId,
      session_id: sessionId,
    });
  },

  sessionEnded(bookId: string, sessionId: string, duration?: number): Promise<void> {
    return this.trackEvent('session_ended', 'Reading session ended', {
      book_id: bookId,
      session_id: sessionId,
      duration_minutes: duration,
    });
  },

  sessionCompleted(bookId: string, sessionId: string): Promise<void> {
    return this.trackEvent('session_completed', 'User completed book', {
      book_id: bookId,
      session_id: sessionId,
    });
  },

  // Search and discovery
  searchPerformed(query: string, resultsCount?: number): Promise<void> {
    return this.trackEvent('search_performed', 'User performed search', {
      query,
      results_count: resultsCount,
    });
  },

  libraryOpened(): Promise<void> {
    return this.trackEvent('library_opened', 'User opened library', {});
  },
};

/**
 * Playback metrics tracker.
 */
export class PlaybackMetricsTracker {
  private sessionId: string;
  private bookId: string;
  private chunkIndex: number;
  private bufferStartMs: number = 0;
  private stallCount: number = 0;
  private stallStartMs: number = 0;
  private totalStallDuration: number = 0;

  constructor(sessionId: string, bookId: string, chunkIndex: number) {
    this.sessionId = sessionId;
    this.bookId = bookId;
    this.chunkIndex = chunkIndex;
  }

  /**
   * Mark start of buffering.
   */
  bufferStart(): void {
    this.bufferStartMs = Date.now();
  }

  /**
   * Mark end of buffering and send metrics.
   */
  async bufferEnd(): Promise<void> {
    if (this.bufferStartMs === 0) return;

    const bufferEndMs = Date.now();
    const bufferDuration = bufferEndMs - this.bufferStartMs;

    try {
      await api.tracking.logPlaybackMetrics({
        session_id: this.sessionId,
        book_id: this.bookId,
        chunk_index: this.chunkIndex,
        buffer_start_ms: this.bufferStartMs,
        buffer_end_ms: bufferEndMs,
        buffer_duration_ms: bufferDuration,
        stall_count: this.stallCount,
        total_stall_duration_ms: this.totalStallDuration,
      });
    } catch (e) {
      console.error('Failed to log playback metrics:', e);
    }
  }

  /**
   * Mark start of playback stall.
   */
  stallStart(): void {
    this.stallCount++;
    this.stallStartMs = Date.now();
  }

  /**
   * Mark end of playback stall.
   */
  stallEnd(): void {
    if (this.stallStartMs === 0) return;

    const stallDuration = Date.now() - this.stallStartMs;
    this.totalStallDuration += stallDuration;
    this.stallStartMs = 0;
  }
}

/**
 * Global error handler to catch unhandled errors.
 */
export function initializeGlobalErrorTracking(): void {
  // Catch unhandled errors
  window.addEventListener('error', (event) => {
    ErrorTracker.logError(
      'unknown',
      event.error || event.message,
      {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      }
    );
  });

  // Catch unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    ErrorTracker.logError(
      'unknown',
      event.reason instanceof Error ? event.reason : String(event.reason),
      {
        promise_rejection: true,
      }
    );
  });
}
