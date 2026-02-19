/**
 * Shared Audio Utilities
 *
 * Provides cross-app utilities for audio processing, conversion, and playback.
 * Used by voice testing components in StudyFlow, InkWave, and other apps.
 */

/**
 * Convert Blob to base64 string
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
 */
export function base64ToBlob(base64: string, mimeType: string = 'audio/wav'): Blob {
  const base64Data = base64.includes(',') ? base64.split(',')[1] : base64;
  const binaryString = window.atob(base64Data);
  const bytes = new Uint8Array(binaryString.length);

  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }

  return new Blob([bytes], { type: mimeType });
}

/**
 * Download audio blob as file
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
 */
export function downloadAudioBase64(
  base64Audio: string,
  filename: string = `audio_${Date.now()}.wav`,
  mimeType: string = 'audio/wav'
): void {
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
 */
export function createAudioPlayer(
  base64Audio: string,
  mimeType: string = 'audio/wav'
): HTMLAudioElement {
  const dataUri = base64Audio.startsWith('data:')
    ? base64Audio
    : `data:${mimeType};base64,${base64Audio}`;

  return new Audio(dataUri);
}

/**
 * Play base64 audio with Promise support
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

    if (options.volume !== undefined) {
      audio.volume = Math.max(0, Math.min(1, options.volume));
    }
    if (options.playbackRate !== undefined) {
      audio.playbackRate = Math.max(0.5, Math.min(4, options.playbackRate));
    }

    if (options.onProgress) {
      audio.ontimeupdate = () => {
        options.onProgress!(audio.currentTime, audio.duration);
      };
    }

    audio.onended = () => resolve();
    audio.onerror = () => reject(new Error('Audio playback failed'));
    audio.play().catch(reject);
  });
}

/**
 * Get audio duration from base64 audio
 */
export async function getAudioDuration(base64Audio: string): Promise<number> {
  return new Promise<number>((resolve, reject) => {
    const audio = createAudioPlayer(base64Audio);
    audio.onloadedmetadata = () => resolve(audio.duration);
    audio.onerror = () => reject(new Error('Failed to load audio metadata'));
  });
}

/**
 * Format duration in seconds to human-readable string
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
 */
export function canPlayAudio(): boolean {
  return typeof Audio !== 'undefined';
}
