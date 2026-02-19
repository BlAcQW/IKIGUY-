/**
 * Audio Utilities for StudyFlow Voice Chat
 *
 * Shared utilities for audio processing, conversion, and playback
 * across voice chat features.
 *
 * Functions:
 * - blobToBase64: Convert audio Blob to base64 string
 * - base64ToBlob: Convert base64 string to Blob
 * - downloadAudioBlob: Download audio blob as file
 * - downloadAudioBase64: Download base64 audio as file
 * - createAudioPlayer: Create HTMLAudioElement from base64
 * - playAudioBase64: Play base64 audio with Promise support
 *
 * Author: AI Labs Africa
 * Created: November 30, 2025
 */

/**
 * Convert Blob to base64 string
 *
 * @param blob - Audio blob to convert
 * @returns Promise resolving to base64 string (without data URI prefix)
 *
 * @example
 * const base64 = await blobToBase64(audioBlob);
 * // Returns: "UklGRiQAAABXQVZFZm10IBAAAAABAAEA..."
 */
export async function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result?.toString();
      if (!result) {
        reject(new Error('Failed to convert audio to base64'));
        return;
      }
      // Extract base64 data (remove data:audio/...;base64, prefix)
      const base64 = result.split(',')[1];
      if (!base64) {
        reject(new Error('Invalid base64 data'));
        return;
      }
      resolve(base64);
    };
    reader.onerror = () => reject(new Error('FileReader error'));
    reader.readAsDataURL(blob);
  });
}

/**
 * Convert base64 string to Blob
 *
 * @param base64 - Base64 encoded audio data
 * @param mimeType - MIME type (default: 'audio/wav')
 * @returns Blob containing audio data
 *
 * @example
 * const blob = base64ToBlob(base64Audio, 'audio/wav');
 */
export function base64ToBlob(base64: string, mimeType: string = 'audio/wav'): Blob {
  // Remove data URI prefix if present
  const base64Data = base64.includes(',') ? base64.split(',')[1] : base64;

  // Decode base64
  const binaryString = window.atob(base64Data);
  const bytes = new Uint8Array(binaryString.length);

  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }

  return new Blob([bytes], { type: mimeType });
}

/**
 * Download audio blob as file
 *
 * @param blob - Audio blob to download
 * @param filename - Filename for download (default: generates timestamp-based name)
 *
 * @example
 * downloadAudioBlob(audioBlob, 'recording.wav');
 */
export function downloadAudioBlob(blob: Blob, filename?: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || `audio_${Date.now()}.wav`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Download base64 audio as file
 *
 * @param base64Audio - Base64 encoded audio (with or without data URI prefix)
 * @param filename - Filename for download
 * @param mimeType - MIME type (default: 'audio/wav')
 *
 * @example
 * downloadAudioBase64(base64Audio, 'speech.wav');
 */
export function downloadAudioBase64(
  base64Audio: string,
  filename: string = `audio_${Date.now()}.wav`,
  mimeType: string = 'audio/wav'
): void {
  // Ensure data URI prefix
  const dataUri = base64Audio.startsWith('data:')
    ? base64Audio
    : `data:${mimeType};base64,${base64Audio}`;

  const a = document.createElement('a');
  a.href = dataUri;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

/**
 * Create HTMLAudioElement from base64 audio
 *
 * @param base64Audio - Base64 encoded audio (with or without data URI prefix)
 * @param mimeType - MIME type (default: 'audio/wav')
 * @returns HTMLAudioElement ready to play
 *
 * @example
 * const audio = createAudioPlayer(base64Audio);
 * audio.play();
 * audio.onended = () => console.log('Playback finished');
 */
export function createAudioPlayer(
  base64Audio: string,
  mimeType: string = 'audio/wav'
): HTMLAudioElement {
  // Ensure data URI prefix
  const dataUri = base64Audio.startsWith('data:')
    ? base64Audio
    : `data:${mimeType};base64,${base64Audio}`;

  const audio = new Audio(dataUri);
  return audio;
}

/**
 * Play base64 audio with Promise support
 *
 * @param base64Audio - Base64 encoded audio (with or without data URI prefix)
 * @param options - Playback options
 * @returns Promise that resolves when audio finishes playing or rejects on error
 *
 * @example
 * try {
 *   await playAudioBase64(base64Audio);
 *   console.log('Playback complete');
 * } catch (error) {
 *   console.error('Playback failed:', error);
 * }
 */
export async function playAudioBase64(
  base64Audio: string,
  options: {
    volume?: number;
    playbackRate?: number;
    onProgress?: (currentTime: number, duration: number) => void;
  } = {}
): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    if (!base64Audio) {
      reject(new Error('No audio data provided'));
      return;
    }

    const audio = createAudioPlayer(base64Audio);

    // Apply options
    if (options.volume !== undefined) {
      audio.volume = Math.max(0, Math.min(1, options.volume));
    }
    if (options.playbackRate !== undefined) {
      audio.playbackRate = Math.max(0.5, Math.min(4, options.playbackRate));
    }

    // Progress tracking
    if (options.onProgress) {
      audio.ontimeupdate = () => {
        options.onProgress!(audio.currentTime, audio.duration);
      };
    }

    // Event handlers
    audio.onended = () => resolve();
    audio.onerror = () => reject(new Error('Audio playback failed'));

    // Start playback
    audio.play().catch(reject);
  });
}

/**
 * Get audio duration from base64 audio
 *
 * @param base64Audio - Base64 encoded audio
 * @returns Promise resolving to duration in seconds
 *
 * @example
 * const duration = await getAudioDuration(base64Audio);
 * console.log(`Audio is ${duration} seconds long`);
 */
export async function getAudioDuration(base64Audio: string): Promise<number> {
  return new Promise<number>((resolve, reject) => {
    const audio = createAudioPlayer(base64Audio);

    audio.onloadedmetadata = () => {
      resolve(audio.duration);
    };

    audio.onerror = () => {
      reject(new Error('Failed to load audio metadata'));
    };
  });
}

/**
 * Format duration in seconds to human-readable string
 *
 * @param seconds - Duration in seconds
 * @returns Formatted string (e.g., "1:23", "12:34")
 *
 * @example
 * formatDuration(83.5); // Returns "1:24"
 */
export function formatDuration(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) {
    return '0:00';
  }

  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Check if browser supports audio recording
 *
 * @returns True if getUserMedia and MediaRecorder are available
 *
 * @example
 * if (canRecordAudio()) {
 *   // Enable recording UI
 * }
 */
export function canRecordAudio(): boolean {
  return !!(
    navigator.mediaDevices &&
    navigator.mediaDevices.getUserMedia &&
    window.MediaRecorder
  );
}

/**
 * Check if browser supports audio playback
 *
 * @returns True if Audio API is available
 *
 * @example
 * if (canPlayAudio()) {
 *   // Enable playback UI
 * }
 */
export function canPlayAudio(): boolean {
  return typeof Audio !== 'undefined';
}

/**
 * AudioQueue - Manages sequential playback of streaming audio chunks.
 * Ensures smooth continuous playback without overlaps or gaps.
 */
export class AudioQueue {
  private queue: string[] = [];
  private isPlaying: boolean = false;
  private updateIsSpeaking: (value: boolean) => void;
  private onError?: (error: string) => void;

  constructor(updateIsSpeaking: (value: boolean) => void, onError?: (error: string) => void) {
    this.updateIsSpeaking = updateIsSpeaking;
    this.onError = onError;
  }

  /**
   * Enqueue an audio chunk for playback.
   * If not currently playing, starts playback immediately.
   */
  async enqueue(base64Audio: string): Promise<void> {
    // Skip empty audio chunks
    if (!base64Audio) {
      console.log('[AudioQueue] Skipping empty chunk');
      return;
    }

    this.queue.push(base64Audio);
    console.log(`[AudioQueue] Enqueued chunk (queue size: ${this.queue.length})`);

    // Start playback if not already playing
    if (!this.isPlaying) {
      await this.playNext();
    }
  }

  /**
   * Play the next chunk in the queue.
   * Recursively calls itself until queue is empty.
   */
  private async playNext(): Promise<void> {
    // Queue is empty - stop playback
    if (this.queue.length === 0) {
      console.log('[AudioQueue] Queue empty, playback complete');
      this.isPlaying = false;
      this.updateIsSpeaking(false);
      return;
    }

    // Mark as playing and update speaking state
    this.isPlaying = true;
    this.updateIsSpeaking(true);

    // Get next chunk
    const chunk = this.queue.shift()!;
    console.log(`[AudioQueue] Playing chunk (${this.queue.length} remaining in queue)`);

    try {
      // Play the chunk
      await playAudioBase64(chunk);
      console.log('[AudioQueue] Chunk played successfully');

      // Play next chunk
      await this.playNext();
    } catch (error) {
      console.error('[AudioQueue] Error playing chunk:', error);
      this.onError?.('Audio playback failed');

      // Continue with next chunk despite error
      await this.playNext();
    }
  }

  /**
   * Clear the queue and stop playback.
   * Used for barge-in/interruption.
   */
  clear(): void {
    console.log(`[AudioQueue] Clearing queue (${this.queue.length} chunks discarded)`);
    this.queue = [];
    this.isPlaying = false;
    this.updateIsSpeaking(false);
  }

  /**
   * Get current queue size.
   */
  size(): number {
    return this.queue.length;
  }

  /**
   * Check if currently playing.
   */
  playing(): boolean {
    return this.isPlaying;
  }
}
