/**
 * useChunkPlayer Hook
 * Manages chunk-based audiobook playback with seamless transitions
 *
 * Features:
 * - Chunk-based playback (auto-advance between chunks)
 * - Prefetching next chunks for seamless playback
 * - Cross-chunk seeking
 * - Session progress tracking
 * - Voice/quality settings support
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { api } from '../lib/api';
import { ErrorTracker, EventTracker, PlaybackMetricsTracker } from '../lib/tracking';

/**
 * Convert a data URL to a blob URL for reliable audio playback.
 * Keep a reference to the blob to prevent garbage collection.
 *
 * H02 FIX: Added LRU eviction to prevent unbounded memory growth.
 * At 100K users with 2+ hour sessions, each chunk ~50KB, this prevents
 * memory from growing beyond ~2.5MB (50 entries * 50KB).
 */
const MAX_BLOB_CACHE_SIZE = 50; // Max entries before eviction
const blobCache = new Map<string, { blob: Blob; url: string; lastAccess: number }>();
const blobCacheOrder: string[] = []; // Track insertion order for LRU

/**
 * Evict oldest entries from blob cache to stay under size limit
 */
function evictOldestBlobCacheEntries(): void {
  while (blobCache.size >= MAX_BLOB_CACHE_SIZE && blobCacheOrder.length > 0) {
    const oldestKey = blobCacheOrder.shift();
    if (oldestKey && blobCache.has(oldestKey)) {
      const entry = blobCache.get(oldestKey)!;
      try {
        URL.revokeObjectURL(entry.url);
        console.log(`[BlobCache] Evicted oldest entry, cache size: ${blobCache.size - 1}`);
      } catch (e) {
        // Ignore revoke errors
      }
      blobCache.delete(oldestKey);
    }
  }
}

function dataUrlToBlobUrl(dataUrl: string): string {
  // Check if we already have this data URL cached
  if (blobCache.has(dataUrl)) {
    const cached = blobCache.get(dataUrl)!;
    // Update last access time for LRU tracking
    cached.lastAccess = Date.now();
    console.log(`Using cached blob URL: ${cached.url}`);
    return cached.url;
  }

  try {
    // Extract base64 data and mime type from data URL
    const matches = dataUrl.match(/^data:([^;]+);base64,(.+)$/);
    if (!matches) {
      console.error('Invalid data URL format, returning original');
      return dataUrl; // Return original as fallback
    }

    const mimeType = matches[1];
    const base64Data = matches[2];

    // Decode base64 to binary
    const binaryString = atob(base64Data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    // H02 FIX: Evict old entries before adding new one
    evictOldestBlobCacheEntries();

    // Create blob and URL - keep reference to prevent GC
    const blob = new Blob([bytes], { type: mimeType });
    const blobUrl = URL.createObjectURL(blob);

    // Cache both blob and URL to prevent garbage collection
    blobCache.set(dataUrl, { blob, url: blobUrl, lastAccess: Date.now() });
    blobCacheOrder.push(dataUrl);

    console.log(`Converted data URL (${dataUrl.length} chars) to blob URL: ${blobUrl}, cache size: ${blobCache.size}`);
    return blobUrl;
  } catch (err) {
    console.error('Failed to convert data URL to blob URL:', err);
    return dataUrl; // Return original as fallback
  }
}

/**
 * Clear cached blobs and revoke their URLs
 */
function clearBlobCache(): void {
  blobCache.forEach(({ url }) => {
    try {
      URL.revokeObjectURL(url);
    } catch (e) {
      // Ignore errors
    }
  });
  blobCache.clear();
  // H02 FIX: Also clear the order tracking array
  blobCacheOrder.length = 0;
}

export interface VoiceSettings {
  provider_id?: string;
  voice_id?: string;
  speed?: number;
  language?: string;
}

export interface ChapterBoundary {
  chunk_index: number;
  chapter_title: string;
}

interface ChunkInfo {
  total_chunks: number;
  chunk_durations: number[];
  total_duration: number;
  generated_count: number;
  all_generated: boolean;
  chapter_boundaries: ChapterBoundary[];
  skip_chunks?: number[];  // Chunk indices to skip (TOC, etc.)
  playable_chunks?: number;
  playable_duration?: number;
}

interface UseChunkPlayerProps {
  bookId: string;
  sessionId?: string;
  initialChunkIndex?: number;
  initialPositionSeconds?: number;
  initialTotalTimeMinutes?: number;
  voiceSettings?: VoiceSettings;
  onChunkChange?: (chunkIndex: number) => void;
  onProgressUpdate?: (chunkIndex: number, positionSeconds: number, totalTimeMinutes?: number) => void;
  /** If true, skip loading initial chunk audio until voice settings are explicitly set */
  waitForVoiceSettings?: boolean;
}

interface ChunkPlayerState {
  // Playback state
  isPlaying: boolean;
  isLoading: boolean;
  isBuffering: boolean;  // C04 FIX: Detect buffer underruns (stalled/waiting events)
  error: string | null;

  // Position tracking
  currentChunkIndex: number;
  currentTime: number;  // Position within current chunk
  globalPosition: number;  // Total position across all chunks

  // Book info
  totalChunks: number;
  chunkDurations: number[];
  totalDuration: number;
  chapterBoundaries: ChapterBoundary[];
  skipChunks: number[];  // Chunk indices to skip (TOC, etc.)

  // Audio state
  playbackRate: number;
  volume: number;
}

/**
 * Calculate the chunk index and position within chunk from a global position
 */
function seekAcrossChunks(
  globalPosition: number,
  chunkDurations: number[]
): { chunkIndex: number; positionInChunk: number } {
  let accumulated = 0;

  for (let i = 0; i < chunkDurations.length; i++) {
    const chunkDuration = chunkDurations[i] || 30; // Default 30s if unknown
    if (accumulated + chunkDuration > globalPosition) {
      return {
        chunkIndex: i,
        positionInChunk: globalPosition - accumulated,
      };
    }
    accumulated += chunkDuration;
  }

  // Beyond end - return last chunk
  return {
    chunkIndex: chunkDurations.length - 1,
    positionInChunk: 0,
  };
}

/**
 * Calculate the starting position of a chunk in the global timeline
 */
function getChunkStartPosition(chunkIndex: number, chunkDurations: number[]): number {
  return chunkDurations.slice(0, chunkIndex).reduce((sum, d) => sum + (d || 30), 0);
}

/**
 * Find the next playable chunk (skipping TOC and other skip chunks)
 */
function findNextPlayableChunk(
  currentIndex: number,
  totalChunks: number,
  skipChunks: number[]
): number | null {
  for (let i = currentIndex + 1; i < totalChunks; i++) {
    if (!skipChunks.includes(i)) {
      return i;
    }
  }
  return null; // No more playable chunks
}

/**
 * Find the previous playable chunk (not in skip list)
 */
function findPreviousPlayableChunk(
  currentIndex: number,
  skipChunks: number[]
): number | null {
  for (let i = currentIndex - 1; i >= 0; i--) {
    if (!skipChunks.includes(i)) {
      return i;
    }
  }
  return null; // No previous playable chunks
}

/**
 * Find the nearest playable chunk to a target index
 * Prefers backward if seeking backward, forward if seeking forward
 */
function findNearestPlayableChunk(
  targetIndex: number,
  currentIndex: number,
  totalChunks: number,
  skipChunks: number[]
): number {
  // If target is playable, use it
  if (!skipChunks.includes(targetIndex)) {
    return targetIndex;
  }

  // Determine direction preference based on seek direction
  const seekingBackward = targetIndex < currentIndex;

  if (seekingBackward) {
    // Try to find previous playable chunk first
    const prev = findPreviousPlayableChunk(targetIndex, skipChunks);
    if (prev !== null) return prev;
    // Fall back to next playable
    const next = findNextPlayableChunk(targetIndex, totalChunks, skipChunks);
    if (next !== null) return next;
  } else {
    // Try to find next playable chunk first
    const next = findNextPlayableChunk(targetIndex, totalChunks, skipChunks);
    if (next !== null) return next;
    // Fall back to previous playable
    const prev = findPreviousPlayableChunk(targetIndex, skipChunks);
    if (prev !== null) return prev;
  }

  // Default to current if nothing found
  return currentIndex;
}

export const useChunkPlayer = ({
  bookId,
  sessionId,
  initialChunkIndex = 0,
  initialPositionSeconds = 0,
  initialTotalTimeMinutes = 0,
  voiceSettings: initialVoiceSettings,
  onChunkChange,
  onProgressUpdate,
  waitForVoiceSettings = false,
}: UseChunkPlayerProps) => {
  // Audio element ref
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const shouldAutoPlay = useRef(false);
  const progressUpdateTimer = useRef<NodeJS.Timeout | null>(null);

  // Prefetch cache: chunk index -> blob URL
  const chunkCache = useRef<Map<number, string>>(new Map());
  const loadingChunks = useRef<Set<number>>(new Set());
  const prefetchChunkRef = useRef<((chunkIndex: number) => Promise<void>) | null>(null);
  const nextChunkPreparedRef = useRef<number | null>(null); // Track which chunk is pre-loaded in audio element

  // Refs for callbacks to avoid recreating audio element on callback changes
  const onChunkChangeRef = useRef(onChunkChange);
  const onProgressUpdateRef = useRef(onProgressUpdate);

  // Ref for skip chunks to use in handleEnded closure
  const skipChunksRef = useRef<number[]>([]);

  // Refs for current state values used in interval callbacks
  const currentChunkIndexRef = useRef<number>(0);
  const currentTimeRef = useRef<number>(0);
  const totalListeningMinutesRef = useRef<number>(initialTotalTimeMinutes);

  // State
  const [state, setState] = useState<ChunkPlayerState>({
    isPlaying: false,
    isLoading: true,
    isBuffering: false,  // C04 FIX: Initialize buffering state
    error: null,
    currentChunkIndex: initialChunkIndex,
    currentTime: initialPositionSeconds,
    globalPosition: 0,
    totalChunks: 0,
    chunkDurations: [],
    totalDuration: 0,
    chapterBoundaries: [],
    skipChunks: [],
    playbackRate: 1,
    volume: 1,
  });

  const [voiceSettings, setVoiceSettingsState] = useState<VoiceSettings>(
    initialVoiceSettings || { provider_id: 'kokoro', speed: 1 }
  );

  // Track if voice settings have been explicitly set (for waitForVoiceSettings mode)
  const voiceSettingsReady = useRef(!waitForVoiceSettings);

  // Time tracking state (for analytics)
  // Initialize with session's existing time to send cumulative total
  const [totalListeningMinutes, setTotalListeningMinutes] = useState(initialTotalTimeMinutes);
  const lastPlayTimeRef = useRef<number>(Date.now());
  const accumulatedSecondsRef = useRef<number>(0);

  // Update total listening minutes when initialTotalTimeMinutes changes (session loaded)
  // Use a ref to track if we've already initialized from session
  const initializedFromSession = useRef(false);
  useEffect(() => {
    if (initialTotalTimeMinutes > 0 && !initializedFromSession.current) {
      setTotalListeningMinutes(initialTotalTimeMinutes);
      initializedFromSession.current = true;
    }
  }, [initialTotalTimeMinutes]);

  // Playback metrics tracker for buffer/stall tracking
  const metricsTrackerRef = useRef<PlaybackMetricsTracker | null>(null);

  // Keep callback refs updated
  useEffect(() => {
    onChunkChangeRef.current = onChunkChange;
  }, [onChunkChange]);

  useEffect(() => {
    onProgressUpdateRef.current = onProgressUpdate;
  }, [onProgressUpdate]);

  // Keep skipChunksRef updated
  useEffect(() => {
    skipChunksRef.current = state.skipChunks;
  }, [state.skipChunks]);

  // Keep state refs updated for interval callbacks
  useEffect(() => {
    currentChunkIndexRef.current = state.currentChunkIndex;
    currentTimeRef.current = state.currentTime;
  }, [state.currentChunkIndex, state.currentTime]);

  useEffect(() => {
    totalListeningMinutesRef.current = totalListeningMinutes;
  }, [totalListeningMinutes]);

  // Track listening time during playback
  useEffect(() => {
    if (state.isPlaying) {
      lastPlayTimeRef.current = Date.now();

      const interval = setInterval(() => {
        const now = Date.now();
        const elapsedSeconds = (now - lastPlayTimeRef.current) / 1000;
        lastPlayTimeRef.current = now;

        // Accumulate seconds
        accumulatedSecondsRef.current += elapsedSeconds;

        // Convert to minutes when we reach 60 seconds
        if (accumulatedSecondsRef.current >= 60) {
          const minutesToAdd = Math.floor(accumulatedSecondsRef.current / 60);
          accumulatedSecondsRef.current = accumulatedSecondsRef.current % 60;
          setTotalListeningMinutes(prev => prev + minutesToAdd);
        }
      }, 1000); // Update every second

      return () => clearInterval(interval);
    }
  }, [state.isPlaying]);

  // Initialize audio element
  useEffect(() => {
    const audio = new Audio();
    audioRef.current = audio;

    // Start with preload 'none' - we'll set to 'auto' when we have a valid source
    audio.preload = 'none';
    // Explicitly set src to empty string to avoid CSP violations with 'about:blank'
    audio.src = '';
    // Ensure audio doesn't try to load anything until we set a valid source

    /**
     * Check if audio element has a valid source
     */
    const hasValidSource = (): boolean => {
      const src = audio.src;
      return src !== '' &&
             src !== 'about:blank' &&
             src !== window.location.href &&
             (src.startsWith('data:audio/') || src.startsWith('blob:'));
    };

    const handleCanPlay = () => {
      console.log('Audio canplay event. shouldAutoPlay:', shouldAutoPlay.current, 'hasValidSource:', hasValidSource());
      setState((prev) => ({ ...prev, isLoading: false }));

      // End buffer tracking
      if (metricsTrackerRef.current) {
        metricsTrackerRef.current.bufferEnd();
      }

      if (shouldAutoPlay.current) {
        shouldAutoPlay.current = false;
        // Only auto-play if we have a valid source
        if (hasValidSource()) {
          console.log('Attempting auto-play from canplay...');
          audio.play().then(() => {
            console.log('Auto-play successful');
            setState((prev) => ({ ...prev, isPlaying: true }));
          }).catch((err) => {
            // Don't set error for common auto-play restrictions
            if (err.name !== 'NotAllowedError' && err.name !== 'AbortError') {
              console.error('Auto-play failed:', err);
              setState((prev) => ({ ...prev, error: 'Failed to play audio' }));
            } else {
              console.log('Auto-play blocked by browser policy:', err.name);
              // Track autoplay blocking
              ErrorTracker.autoplayBlocked(bookId, state.currentChunkIndex);
            }
          });
        }
      }
    };

    // loadeddata is often more reliable than canplay for blob URLs
    const handleLoadedData = () => {
      console.log('Audio loadeddata event. shouldAutoPlay:', shouldAutoPlay.current, 'hasValidSource:', hasValidSource());
      setState((prev) => ({ ...prev, isLoading: false }));

      // End buffer tracking (if not already ended)
      if (metricsTrackerRef.current) {
        metricsTrackerRef.current.bufferEnd();
      }

      // If canplay hasn't fired but loadeddata has, we can try to play
      if (shouldAutoPlay.current && hasValidSource()) {
        shouldAutoPlay.current = false;
        console.log('Attempting play from loadeddata...');
        audio.play().then(() => {
          console.log('Play from loadeddata successful');
          setState((prev) => ({ ...prev, isPlaying: true }));
        }).catch((err) => {
          if (err.name !== 'NotAllowedError' && err.name !== 'AbortError') {
            console.error('Play from loadeddata failed:', err);
          } else {
            console.log('Play blocked by browser policy:', err.name);
            // Track autoplay blocking
            ErrorTracker.autoplayBlocked(bookId, state.currentChunkIndex);
          }
        });
      }
    };

    const handleTimeUpdate = () => {
      const time = audio.currentTime;
      setState((prev) => {
        const globalPos = getChunkStartPosition(prev.currentChunkIndex, prev.chunkDurations) + time;
        const currentChunkDuration = prev.chunkDurations[prev.currentChunkIndex] || 30;
        const progressPercent = (time / currentChunkDuration) * 100;
        
        // Find next playable chunk
        const nextIndex = findNextPlayableChunk(
          prev.currentChunkIndex,
          prev.totalChunks,
          skipChunksRef.current
        );
        
        // When 50% through current chunk, prefetch next chunk if not already cached
        if (progressPercent >= 50 && nextIndex !== null && !chunkCache.current.has(nextIndex) && !loadingChunks.current.has(nextIndex)) {
          // Prefetch next chunk in background using ref
          if (prefetchChunkRef.current) {
            prefetchChunkRef.current(nextIndex);
          }
        }
        
        // When 90% through current chunk, PRE-LOAD next chunk into audio element for seamless transition
        if (progressPercent >= 90 && nextIndex !== null && nextIndex !== nextChunkPreparedRef.current) {
          const nextChunkUrl = chunkCache.current.get(nextIndex);
          if (nextChunkUrl && audioRef.current) {
            console.log(`[ChunkPlayer] Pre-loading next chunk ${nextIndex} at 90% progress for seamless transition`);
            // Pre-load the next chunk's source (but don't play it yet)
            // This prepares the browser's audio decoder
            audioRef.current.preload = 'auto';
            // Store a temporary source that we'll switch to when current chunk ends
            nextChunkPreparedRef.current = nextIndex;
            // Note: We don't set src yet - we'll do that in handleEnded for seamless transition
          }
        }
        
        return { ...prev, currentTime: time, globalPosition: globalPos };
      });
    };

    const handleEnded = () => {
      // Auto-advance to next playable chunk (skip TOC and other skip chunks)
      // Get current state values we need
      setState((prev) => {
        // Find next playable chunk using the ref
        const nextIndex = findNextPlayableChunk(
          prev.currentChunkIndex,
          prev.totalChunks,
          skipChunksRef.current
        );

        console.log(`[ChunkPlayer] handleEnded: current=${prev.currentChunkIndex}, next=${nextIndex}, totalChunks=${prev.totalChunks}, skipChunks=${skipChunksRef.current}`);

        if (nextIndex !== null) {
          // Check if next chunk is already cached
          const nextChunkUrl = chunkCache.current.get(nextIndex);
          const isCached = !!nextChunkUrl;
          
          if (isCached && audioRef.current) {
            // Chunk is cached - switch immediately for seamless playback
            console.log(`[ChunkPlayer] Switching to cached chunk ${nextIndex} immediately`);
            
            // Check if source is already set to this chunk (avoid unnecessary load)
            const isSameSource = audioRef.current.src === nextChunkUrl;
            
            if (!isSameSource) {
              // Set autoPlay flag BEFORE changing source
              shouldAutoPlay.current = true;
              
              // Switch to next chunk's source
              audioRef.current.preload = 'auto';
              audioRef.current.src = nextChunkUrl;
              audioRef.current.currentTime = 0; // Reset position
              // Only call load() if source changed - this minimizes pause
              audioRef.current.load();
            } else {
              // Same source - just reset position and continue playing
              console.log(`[ChunkPlayer] Same source, just resetting position`);
              audioRef.current.currentTime = 0;
              shouldAutoPlay.current = true;
            }
            
            // Try to play (will use canplay event if not ready yet)
            // Don't call play() immediately - let canplay event handle it for smoother transition
            if (audioRef.current.readyState >= 3) { // HAVE_FUTURE_DATA or HAVE_ENOUGH_DATA
              // Audio is ready, play immediately
              audioRef.current.play().catch((err) => {
                console.log('Auto-play after chunk transition blocked:', err.name);
                shouldAutoPlay.current = false;
              });
            }
            // If not ready, canplay event will handle playback
            
            nextChunkPreparedRef.current = null; // Reset prepared chunk
            onChunkChangeRef.current?.(nextIndex);
            
            return { ...prev, currentChunkIndex: nextIndex, currentTime: 0, isLoading: !isSameSource, isPlaying: true };
          } else {
            // Chunk not cached - load it (will show loading state briefly)
            console.log(`[ChunkPlayer] Next chunk ${nextIndex} not cached, loading now...`);
            // Use requestAnimationFrame for immediate execution (faster than setTimeout)
            requestAnimationFrame(() => {
              loadChunkAudio(nextIndex, true);
              onChunkChangeRef.current?.(nextIndex);
            });
            
            return { ...prev, currentChunkIndex: nextIndex, currentTime: 0, isLoading: true };
          }
        }
        // No more playable chunks - end of book
        console.log('[ChunkPlayer] End of book reached');
        return { ...prev, isPlaying: false };
      });
    };

    const handleError = (e: Event) => {
      const target = e.target as HTMLAudioElement;

      // Only set error if we actually have a valid source (avoid errors for empty/uninitialized audio)
      if (hasValidSource()) {
        const errorCode = target.error?.code;
        const errorMsg = target.error?.message || 'Unknown audio error';
        console.error('Audio playback error:', errorCode, errorMsg);

        // Track audio playback error
        ErrorTracker.audioPlaybackFailed(
          bookId,
          state.currentChunkIndex,
          new Error(`Audio error ${errorCode}: ${errorMsg}`)
        );

        setState((prev) => ({ ...prev, isLoading: false, error: 'Failed to load audio chunk' }));
      } else {
        // Silently ignore errors for empty sources - this is expected during initialization
        // Also ignore CSP violations for 'about:blank' and window.location.href - we'll set a proper source soon
        if (target.src && target.src !== 'about:blank' && target.src !== window.location.href) {
          console.warn('Audio error with invalid source:', target.src);
        }
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    };

    // C04 FIX: Buffer underrun detection via stalled/waiting events
    const handleStalled = () => {
      console.log('[ChunkPlayer] Audio stalled - buffer underrun detected');
      setState((prev) => ({ ...prev, isBuffering: true }));
      // Track buffer underrun for analytics
      if (metricsTrackerRef.current) {
        metricsTrackerRef.current.bufferStart();
      }
    };

    const handleWaiting = () => {
      console.log('[ChunkPlayer] Audio waiting - buffering required');
      setState((prev) => ({ ...prev, isBuffering: true }));
    };

    const handlePlayingResume = () => {
      // Clear buffering state when playback resumes
      setState((prev) => ({ ...prev, isBuffering: false, isPlaying: true }));
      if (metricsTrackerRef.current) {
        metricsTrackerRef.current.bufferEnd();
      }
    };

    audio.addEventListener('canplay', handleCanPlay);
    audio.addEventListener('loadeddata', handleLoadedData);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);
    // C04 FIX: Listen for buffer underrun events
    audio.addEventListener('stalled', handleStalled);
    audio.addEventListener('waiting', handleWaiting);
    audio.addEventListener('playing', handlePlayingResume);

    return () => {
      audio.removeEventListener('canplay', handleCanPlay);
      audio.removeEventListener('loadeddata', handleLoadedData);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
      // C04 FIX: Remove buffer underrun listeners
      audio.removeEventListener('stalled', handleStalled);
      audio.removeEventListener('waiting', handleWaiting);
      audio.removeEventListener('playing', handlePlayingResume);
      audio.pause();
      audio.src = '';

      // Clean up blob URLs from chunk cache
      chunkCache.current.forEach((url) => {
        try {
          URL.revokeObjectURL(url);
        } catch (e) {
          // Ignore errors
        }
      });
      chunkCache.current.clear();

      // Clear global blob cache
      clearBlobCache();

      // Clear progress timer
      if (progressUpdateTimer.current) {
        clearInterval(progressUpdateTimer.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty array - audio element should only be created once

  // Load chunk info on mount
  useEffect(() => {
    const loadChunkInfo = async () => {
      try {
        setState((prev) => ({ ...prev, isLoading: true, error: null }));
        const response = await api.books.getChunksInfo(bookId);
        const info: ChunkInfo = response.data;

        // Get skip chunks list (TOC, etc.)
        const skipChunks = info.skip_chunks || [];

        // Find the first playable chunk (not in skip list)
        let startChunk = initialChunkIndex;
        if (skipChunks.includes(startChunk)) {
          // Find first non-skipped chunk
          for (let i = 0; i < info.total_chunks; i++) {
            if (!skipChunks.includes(i)) {
              startChunk = i;
              break;
            }
          }
          console.log(`[ChunkPlayer] Initial chunk ${initialChunkIndex} is in skip list, starting at ${startChunk}`);
        }

        const initialGlobalPos =
          getChunkStartPosition(startChunk, info.chunk_durations) + initialPositionSeconds;

        setState((prev) => ({
          ...prev,
          totalChunks: info.total_chunks,
          chunkDurations: info.chunk_durations,
          totalDuration: info.total_duration,
          chapterBoundaries: info.chapter_boundaries,
          skipChunks: skipChunks,
          currentChunkIndex: startChunk,
          globalPosition: initialGlobalPos,
          // Keep isLoading true until audio is loaded
        }));

        // Only load initial chunk audio if voice settings are ready
        // (skip if waitForVoiceSettings is true and settings haven't been set yet)
        if (voiceSettingsReady.current) {
          console.log('[ChunkPlayer] Voice settings ready, loading initial chunk audio');
          // Load initial chunk (use startChunk which accounts for skip list)
          await loadChunkAudio(startChunk, false);

          // Prefetch next playable chunk
          const nextPlayable = findNextPlayableChunk(startChunk, info.total_chunks, skipChunks);
          if (nextPlayable !== null) {
            prefetchChunk(nextPlayable);
          }
        } else {
          console.log('[ChunkPlayer] Waiting for voice settings before loading audio');
        }
      } catch (err: any) {
        console.error('Failed to load chunk info:', err);
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: err.response?.data?.detail || 'Failed to load book audio info',
        }));
      }
    };

    if (bookId) {
      loadChunkInfo();
    }
  }, [bookId, initialChunkIndex, initialPositionSeconds]);

  // Progress update timer (debounced)
  useEffect(() => {
    if (sessionId && state.isPlaying) {
      progressUpdateTimer.current = setInterval(() => {
        // Use refs to get current values without causing effect re-runs
        onProgressUpdateRef.current?.(
          currentChunkIndexRef.current,
          currentTimeRef.current,
          totalListeningMinutesRef.current
        );
      }, 60000); // Update every 60 seconds (1 minute) - server batches every 5 minutes

      return () => {
        if (progressUpdateTimer.current) {
          clearInterval(progressUpdateTimer.current);
        }
      };
    }
  }, [sessionId, state.isPlaying]); // Only depend on sessionId and isPlaying to prevent timer reset

  // Track previous voice settings to detect changes (ref defined here, effect defined after functions)
  const prevVoiceSettingsRef = useRef<VoiceSettings | null>(null);

  /**
   * Load audio for a specific chunk
   */
  const loadChunkAudio = useCallback(
    async (chunkIndex: number, autoPlay: boolean = false, overrideSettings?: VoiceSettings) => {
      console.log(`[ChunkPlayer] loadChunkAudio called: chunk=${chunkIndex}, autoPlay=${autoPlay}`);

      if (loadingChunks.current.has(chunkIndex)) {
        console.log(`[ChunkPlayer] Chunk ${chunkIndex} already loading, will retry after delay`);
        // If autoPlay is requested but chunk is loading, wait and retry
        if (autoPlay) {
          setTimeout(() => {
            console.log(`[ChunkPlayer] Retrying chunk ${chunkIndex} after prefetch delay`);
            loadChunkAudio(chunkIndex, autoPlay, overrideSettings);
          }, 500);
        }
        return; // Already loading
      }

      // Use override settings if provided, otherwise use state
      const settingsToUse = overrideSettings || voiceSettings;

      // Check cache first - if cached, use it immediately (no API call = no regeneration)
      const cached = chunkCache.current.get(chunkIndex);
      if (cached && audioRef.current) {
        console.log(`[ChunkPlayer] Using cached audio for chunk ${chunkIndex} (no regeneration), autoPlay=${autoPlay}`);
        
        // If source is already set to this chunk, don't reload (avoids pause)
        const isAlreadyLoaded = audioRef.current.src === cached && audioRef.current.readyState >= 2; // HAVE_CURRENT_DATA
        
        if (!isAlreadyLoaded) {
          // Set autoPlay BEFORE setting source to avoid race condition
          if (autoPlay) {
            shouldAutoPlay.current = true;
          }
          audioRef.current.preload = 'auto';
          audioRef.current.src = cached;
          audioRef.current.currentTime = 0; // Reset position
          // Only call load() if source actually changed - this avoids unnecessary pause
          audioRef.current.load();
        } else {
          // Source is already loaded - just reset position and play if needed
          console.log(`[ChunkPlayer] Chunk ${chunkIndex} already loaded, just resetting position`);
          audioRef.current.currentTime = 0;
          if (autoPlay && audioRef.current.paused) {
            shouldAutoPlay.current = true;
            audioRef.current.play().catch((err) => {
              console.log('Auto-play from already-loaded chunk blocked:', err.name);
              shouldAutoPlay.current = false;
            });
          }
        }
        
        nextChunkPreparedRef.current = null; // Reset prepared chunk
        setState((prev) => ({ ...prev, currentChunkIndex: chunkIndex, currentTime: 0, isLoading: false, isPlaying: autoPlay && !audioRef.current?.paused }));
        return;
      }

      loadingChunks.current.add(chunkIndex);
      setState((prev) => ({ ...prev, isLoading: true }));

      // Start tracking buffer time
      if (sessionId) {
        metricsTrackerRef.current = new PlaybackMetricsTracker(sessionId, bookId, chunkIndex);
        metricsTrackerRef.current.bufferStart();
      }

      try {
        const response = await api.audiobook.getChunkAudio(bookId, chunkIndex, {
          provider_id: settingsToUse.provider_id,
          voice_id: settingsToUse.voice_id,
          speed: settingsToUse.speed,
          language: settingsToUse.language,
        });

        const data = response.data;
        console.log('[ChunkPlayer] loadChunkAudio response:', {
          chunk_id: data.chunk_id,
          audio_url_length: data.audio_url?.length,
          duration: data.duration
        });

        // Validate audio_url before using it
        if (!data.audio_url || typeof data.audio_url !== 'string' || data.audio_url.trim().length === 0) {
          throw new Error(`Invalid audio_url received for chunk ${chunkIndex}`);
        }

        // Validate it's a proper data URL
        if (!data.audio_url.startsWith('data:audio/')) {
          console.error(`Invalid audio_url format for chunk ${chunkIndex}:`, data.audio_url.substring(0, 50));
          throw new Error(`Invalid audio_url format for chunk ${chunkIndex}`);
        }

        // Validate base64 portion (after the comma)
        const base64Part = data.audio_url.split(',')[1];
        if (!base64Part || base64Part.length < 100) {
          console.error(`Invalid base64 data for chunk ${chunkIndex}: base64 length = ${base64Part?.length || 0}`);
          throw new Error(`Invalid base64 audio data for chunk ${chunkIndex}`);
        }

        // Check for invalid base64 characters (basic validation)
        const base64Regex = /^[A-Za-z0-9+/=]+$/;
        if (!base64Regex.test(base64Part)) {
          console.error(`Invalid base64 characters in chunk ${chunkIndex}`);
          throw new Error(`Invalid base64 encoding for chunk ${chunkIndex}`);
        }

        // The response contains audio_url as a data URL (base64)
        // Convert to blob URL for reliable browser playback
        if (data.audio_url && audioRef.current) {
          // Convert data URL to blob URL for better browser compatibility
          const blobUrl = dataUrlToBlobUrl(data.audio_url);

          // Cache the blob URL (not the data URL)
          chunkCache.current.set(chunkIndex, blobUrl);

          // Update chunk duration if we got it
          if (data.duration) {
            setState((prev) => {
              const newDurations = [...prev.chunkDurations];
              newDurations[chunkIndex] = data.duration;
              const newTotal = newDurations.reduce((sum, d) => sum + (d || 30), 0);
              return { ...prev, chunkDurations: newDurations, totalDuration: newTotal };
            });
          }

          console.log(`Setting audio src for chunk ${chunkIndex}, blob URL length: ${blobUrl.length}`);

          // Stop current playback before switching source
          if (audioRef.current.src) {
            audioRef.current.pause();
          }

          // IMPORTANT: Set autoPlay flag BEFORE setting source to avoid race condition
          // The canplay/loadeddata event may fire immediately after load() if blob is ready
          if (autoPlay) {
            shouldAutoPlay.current = true;
          }

          // Set new audio source with blob URL
          try {
            // Set preload to 'auto' to ensure browser loads enough data
            audioRef.current.preload = 'auto';
            audioRef.current.src = blobUrl;
            audioRef.current.load();
            console.log(`Audio src set successfully for chunk ${chunkIndex}`);
          } catch (err) {
            console.error(`Failed to set audio src for chunk ${chunkIndex}:`, err);
            shouldAutoPlay.current = false; // Reset on error
            throw err;
          }

          setState((prev) => ({ ...prev, currentChunkIndex: chunkIndex, currentTime: 0, isLoading: false }));

          // Prefetch next 2-3 chunks ahead for seamless playback
          if (chunkIndex < state.totalChunks - 1) {
            // Prefetch next chunk immediately
            prefetchChunk(chunkIndex + 1);
            
            // Prefetch 2-3 chunks ahead if available
            const chunksToPrefetch = Math.min(3, state.totalChunks - chunkIndex - 1);
            for (let i = 2; i <= chunksToPrefetch; i++) {
              const nextChunkIndex = chunkIndex + i;
              // Prefetch with a small delay to avoid overwhelming the server
              setTimeout(() => {
                prefetchChunk(nextChunkIndex);
              }, i * 200);
            }
          }
        }
      } catch (err: any) {
        console.error(`Failed to load chunk ${chunkIndex}:`, err);

        // Track audio load failure
        ErrorTracker.audioLoadFailed(
          bookId,
          chunkIndex,
          err instanceof Error ? err : new Error(err.response?.data?.detail || `Failed to generate audio for chunk ${chunkIndex}`)
        );

        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: err.response?.data?.detail || `Failed to generate audio for chunk ${chunkIndex}`,
        }));
      } finally {
        loadingChunks.current.delete(chunkIndex);
      }
    },
    [bookId, voiceSettings, state.totalChunks]
  );

  /**
   * Prefetch a chunk without playing
   */
  const prefetchChunk = useCallback(
    async (chunkIndex: number) => {
      // Skip if chunk is in skip list (non-narratable content)
      if (state.skipChunks.includes(chunkIndex)) {
        console.log(`[ChunkPlayer] Skipping prefetch of non-narratable chunk ${chunkIndex}`);
        return;
      }

      if (chunkCache.current.has(chunkIndex) || loadingChunks.current.has(chunkIndex)) {
        return; // Already cached or loading
      }

      loadingChunks.current.add(chunkIndex);

      try {
        const response = await api.audiobook.getChunkAudio(bookId, chunkIndex, {
          provider_id: voiceSettings.provider_id,
          voice_id: voiceSettings.voice_id,
          speed: voiceSettings.speed,
          language: voiceSettings.language,
        });

        const data = response.data;

        // Handle skipped chunks (non-narratable content)
        if (data.skipped || data.provider_used === 'skipped') {
          console.log(`[ChunkPlayer] Chunk ${chunkIndex} is non-narratable, skipping`);
          return;
        }

        if (data.audio_url) {
          // Convert to blob URL for better browser compatibility
          const blobUrl = dataUrlToBlobUrl(data.audio_url);
          chunkCache.current.set(chunkIndex, blobUrl);

          // Update duration
          if (data.duration) {
            setState((prev) => {
              const newDurations = [...prev.chunkDurations];
              newDurations[chunkIndex] = data.duration;
              return { ...prev, chunkDurations: newDurations };
            });
          }
        }
      } catch (err) {
        console.error(`Failed to prefetch chunk ${chunkIndex}:`, err);
      } finally {
        loadingChunks.current.delete(chunkIndex);
      }
    },
    [bookId, voiceSettings, state.skipChunks]
  );

  // Store prefetch function in ref so it's accessible in event handlers
  useEffect(() => {
    prefetchChunkRef.current = prefetchChunk;
  }, [prefetchChunk]);

  // Effect to load initial chunk when voice settings become ready
  // NOTE: This effect MUST be defined after loadChunkAudio and prefetchChunk
  useEffect(() => {
    // Only act when:
    // 1. We have chunks available
    // 2. Voice settings are now ready
    // 3. Voice settings have actually changed (not just re-render)
    const settingsChanged =
      prevVoiceSettingsRef.current === null ||
      prevVoiceSettingsRef.current.provider_id !== voiceSettings.provider_id ||
      prevVoiceSettingsRef.current.voice_id !== voiceSettings.voice_id;

    if (state.totalChunks > 0 && voiceSettingsReady.current && settingsChanged) {
      console.log('[ChunkPlayer] Voice settings effect triggered, loading chunk with:', voiceSettings);
      // Clear any existing cache for clean reload
      chunkCache.current.clear();
      clearBlobCache();
      // Load initial chunk with new settings
      loadChunkAudio(state.currentChunkIndex, false);
      // Prefetch next chunk
      if (state.currentChunkIndex < state.totalChunks - 1) {
        prefetchChunk(state.currentChunkIndex + 1);
      }
    }
    prevVoiceSettingsRef.current = voiceSettings;
  }, [voiceSettings, state.totalChunks, state.currentChunkIndex, loadChunkAudio, prefetchChunk]);

  /**
   * Check if audio element has a valid playable source
   */
  const hasPlayableSource = useCallback((): boolean => {
    if (!audioRef.current) return false;
    const src = audioRef.current.src;
    return src !== '' &&
           src !== 'about:blank' &&
           src !== window.location.href &&
           (src.startsWith('data:audio/') || src.startsWith('blob:'));
  }, []);

  // Controls
  const play = useCallback(async () => {
    if (!audioRef.current) {
      return;
    }

    // If no audio source is loaded, load the current chunk first
    if (!hasPlayableSource()) {
      const currentChunk = state.currentChunkIndex;
      if (currentChunk >= 0 && currentChunk < state.totalChunks) {
        console.log('Loading chunk before play:', currentChunk);
        await loadChunkAudio(currentChunk, true); // Load with auto-play
        return;
      } else {
        // No chunks available, don't attempt to play
        console.log('No audio source available and no chunks to load');
        return;
      }
    }

    try {
      await audioRef.current.play();
      setState((prev) => ({ ...prev, isPlaying: true, error: null }));

      // Track play event
      EventTracker.playClicked(bookId, sessionId, state.currentChunkIndex);
    } catch (err: any) {
      // Ignore AbortError and NotSupportedError for empty sources
      if (err.name === 'AbortError') {
        return; // Normal when play is interrupted
      }
      if (err.name === 'NotSupportedError' && !hasPlayableSource()) {
        console.log('Ignoring NotSupportedError for empty source');
        return;
      }
      console.error('Play failed:', err.name, err.message);
      setState((prev) => ({ ...prev, error: 'Failed to play audio' }));
    }
  }, [state.currentChunkIndex, state.totalChunks, loadChunkAudio, hasPlayableSource]);

  const pause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setState((prev) => ({ ...prev, isPlaying: false }));

      // Track pause event
      EventTracker.pauseClicked(bookId, sessionId, state.currentChunkIndex);

      // Save progress immediately on pause - use refs for current values
      onProgressUpdateRef.current?.(
        currentChunkIndexRef.current,
        currentTimeRef.current,
        totalListeningMinutesRef.current
      );
    }
  }, [bookId, sessionId]); // Only depend on bookId and sessionId

  const togglePlay = useCallback(() => {
    if (state.isPlaying) {
      pause();
    } else {
      play();
    }
  }, [state.isPlaying, play, pause]);

  /**
   * Seek to a global position (across all chunks)
   * Handles non-narratable chunks by finding the nearest playable chunk
   */
  const seekToGlobalPosition = useCallback(
    async (globalSeconds: number) => {
      const { chunkIndex: targetChunk, positionInChunk } = seekAcrossChunks(globalSeconds, state.chunkDurations);

      // Check if target chunk is in skip list (non-narratable)
      // If so, find the nearest playable chunk
      const chunkIndex = state.skipChunks.includes(targetChunk)
        ? findNearestPlayableChunk(targetChunk, state.currentChunkIndex, state.totalChunks, state.skipChunks)
        : targetChunk;

      console.log(`[ChunkPlayer] seekToGlobalPosition: target=${targetChunk}, playable=${chunkIndex}, skip=${state.skipChunks.includes(targetChunk)}`);

      if (chunkIndex !== state.currentChunkIndex) {
        // Need to load a different chunk
        const wasPlaying = state.isPlaying;
        if (wasPlaying) pause();

        await loadChunkAudio(chunkIndex, wasPlaying);
        onChunkChangeRef.current?.(chunkIndex);

        // Seek within the new chunk after it loads
        // Only seek if we're on the original target chunk (not a fallback)
        if (chunkIndex === targetChunk) {
          setTimeout(() => {
            if (audioRef.current) {
              audioRef.current.currentTime = positionInChunk;
            }
          }, 100);
        }
      } else {
        // Same chunk, just seek within it
        if (audioRef.current) {
          audioRef.current.currentTime = positionInChunk;
        }
      }

      // Update state with actual chunk we're playing
      const actualGlobalPos = getChunkStartPosition(chunkIndex, state.chunkDurations) +
        (chunkIndex === targetChunk ? positionInChunk : 0);

      setState((prev) => ({
        ...prev,
        currentChunkIndex: chunkIndex,
        currentTime: chunkIndex === targetChunk ? positionInChunk : 0,
        globalPosition: actualGlobalPos,
      }));
    },
    [state.chunkDurations, state.currentChunkIndex, state.isPlaying, state.skipChunks, state.totalChunks, loadChunkAudio, pause]
  );

  /**
   * Seek within current chunk only
   */
  const seekWithinChunk = useCallback((seconds: number) => {
    if (audioRef.current && isFinite(seconds) && seconds >= 0) {
      audioRef.current.currentTime = seconds;
      setState((prev) => ({ ...prev, currentTime: seconds }));
    }
  }, []);

  const skipForward = useCallback(
    (seconds: number = 15) => {
      const newGlobalPos = Math.min(state.globalPosition + seconds, state.totalDuration);
      seekToGlobalPosition(newGlobalPos);

      // Track skip forward event
      EventTracker.skipForward(bookId, sessionId, seconds);
    },
    [bookId, sessionId, state.globalPosition, state.totalDuration, seekToGlobalPosition]
  );

  const skipBackward = useCallback(
    (seconds: number = 15) => {
      const newGlobalPos = Math.max(state.globalPosition - seconds, 0);
      seekToGlobalPosition(newGlobalPos);

      // Track skip backward event
      EventTracker.skipBackward(bookId, sessionId, seconds);
    },
    [bookId, sessionId, state.globalPosition, seekToGlobalPosition]
  );

  /**
   * Jump to a specific chunk
   * Handles non-narratable chunks by finding the nearest playable chunk
   */
  const goToChunk = useCallback(
    async (chunkIndex: number) => {
      if (chunkIndex >= 0 && chunkIndex < state.totalChunks) {
        // Check if target chunk is in skip list (non-narratable)
        // If so, find the nearest playable chunk
        const targetChunk = state.skipChunks.includes(chunkIndex)
          ? findNearestPlayableChunk(chunkIndex, state.currentChunkIndex, state.totalChunks, state.skipChunks)
          : chunkIndex;

        console.log(`[ChunkPlayer] goToChunk: requested=${chunkIndex}, playable=${targetChunk}, skipped=${state.skipChunks.includes(chunkIndex)}`);

        const wasPlaying = state.isPlaying;
        if (wasPlaying) pause();
        await loadChunkAudio(targetChunk, wasPlaying);
        onChunkChangeRef.current?.(targetChunk);

        // Track chunk change event
        EventTracker.chunkChanged(bookId, sessionId, targetChunk);
      }
    },
    [bookId, sessionId, state.totalChunks, state.currentChunkIndex, state.skipChunks, state.isPlaying, loadChunkAudio, pause]
  );

  /**
   * Jump to a chapter by name or index
   */
  const goToChapter = useCallback(
    (chapterIndex: number) => {
      if (chapterIndex >= 0 && chapterIndex < state.chapterBoundaries.length) {
        const boundary = state.chapterBoundaries[chapterIndex];
        goToChunk(boundary.chunk_index);
      }
    },
    [state.chapterBoundaries, goToChunk]
  );

  const changePlaybackRate = useCallback((rate: number) => {
    if (audioRef.current) {
      audioRef.current.playbackRate = rate;
      setState((prev) => ({ ...prev, playbackRate: rate }));

      // Track speed change event
      EventTracker.speedChanged(bookId, sessionId, rate);
    }
  }, [bookId, sessionId]);

  const changeVolume = useCallback((vol: number) => {
    if (audioRef.current) {
      audioRef.current.volume = vol;
      setState((prev) => ({ ...prev, volume: vol }));

      // Track volume change event
      EventTracker.volumeChanged(bookId, sessionId, vol);
    }
  }, [bookId, sessionId]);

  /**
   * Update voice settings and clear cache (audio will regenerate)
   */
  const setVoiceSettings = useCallback((settings: VoiceSettings) => {
    console.log('[ChunkPlayer] setVoiceSettings called:', settings);
    setVoiceSettingsState(settings);

    // Mark voice settings as ready
    const wasWaiting = !voiceSettingsReady.current;
    voiceSettingsReady.current = true;

    // Clear caches since settings changed
    chunkCache.current.forEach((url) => {
      try {
        URL.revokeObjectURL(url);
      } catch (e) {
        // Ignore errors
      }
    });
    chunkCache.current.clear();
    clearBlobCache();

    // If we were waiting for settings and now have them, load the initial chunk
    // Otherwise, reload current chunk with new settings
    if (wasWaiting && state.totalChunks > 0) {
      console.log('[ChunkPlayer] Voice settings now ready, loading initial chunk with settings:', settings);
      // Load initial chunk immediately with new settings
      // Use initialChunkIndex from props, or currentChunkIndex if available
      const chunkToLoad = state.currentChunkIndex >= 0 ? state.currentChunkIndex : initialChunkIndex;
      // Pass settings directly to ensure we use the new settings immediately
      loadChunkAudio(chunkToLoad, false, settings);
      // Prefetch next chunk if available
      if (chunkToLoad < state.totalChunks - 1) {
        prefetchChunk(chunkToLoad + 1);
      }
    } else if (state.totalChunks > 0) {
      // Settings changed mid-playback, reload current chunk
      loadChunkAudio(state.currentChunkIndex, state.isPlaying);
    }
  }, [state.currentChunkIndex, state.isPlaying, state.totalChunks, loadChunkAudio, prefetchChunk, initialChunkIndex]);

  /**
   * Get current chapter info
   */
  const getCurrentChapter = useCallback(() => {
    const boundaries = state.chapterBoundaries;
    for (let i = boundaries.length - 1; i >= 0; i--) {
      if (boundaries[i].chunk_index <= state.currentChunkIndex) {
        return {
          index: i,
          title: boundaries[i].chapter_title,
          chunkIndex: boundaries[i].chunk_index,
        };
      }
    }
    return null;
  }, [state.chapterBoundaries, state.currentChunkIndex]);

  return {
    // State
    ...state,
    voiceSettings,

    // Computed
    currentChapter: getCurrentChapter(),
    progress: state.totalDuration > 0 ? (state.globalPosition / state.totalDuration) * 100 : 0,

    // Controls
    play,
    pause,
    togglePlay,
    seekToGlobalPosition,
    seekWithinChunk,
    skipForward,
    skipBackward,
    goToChunk,
    goToChapter,
    changePlaybackRate,
    changeVolume,
    setVoiceSettings,

    // Utilities
    loadChunkAudio,
    prefetchChunk,
  };
};

export default useChunkPlayer;
