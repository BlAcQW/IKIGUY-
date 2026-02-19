/**
 * Audio Worker Hook
 *
 * Uses Web Worker to decode base64 audio off the main thread.
 * Prevents UI freezing during large audio file processing.
 *
 * Created: 2025-10-27
 * Sprint 3: Performance Optimization (Phase 8)
 */

import { useRef, useEffect } from 'react';

interface AudioWorkerMessage {
  id: string;
  audioBase64: string;
}

interface AudioWorkerResponse {
  id: string;
  success: boolean;
  audioBuffer?: ArrayBuffer;
  error?: string;
}

type DecodeCallback = (audioBlob: Blob | null, error?: string) => void;

export const useAudioWorker = () => {
  const workerRef = useRef<Worker | null>(null);
  const callbacksRef = useRef<Map<string, DecodeCallback>>(new Map());

  // Initialize worker
  useEffect(() => {
    // Create worker instance
    workerRef.current = new Worker('/audioDecoder.worker.js');

    // Handle messages from worker
    workerRef.current.onmessage = (e: MessageEvent<AudioWorkerResponse>) => {
      const { id, success, audioBuffer, error } = e.data;

      // Get callback for this request
      const callback = callbacksRef.current.get(id);
      if (!callback) return;

      // Remove callback from map
      callbacksRef.current.delete(id);

      if (success && audioBuffer) {
        // Convert ArrayBuffer to Blob
        const blob = new Blob([audioBuffer], { type: 'audio/wav' });
        callback(blob);
      } else {
        callback(null, error || 'Failed to decode audio');
      }
    };

    // Handle worker errors
    workerRef.current.onerror = (error) => {
      console.error('Audio worker error:', error);

      // Call all pending callbacks with error
      callbacksRef.current.forEach((callback) => {
        callback(null, 'Worker error: ' + error.message);
      });
      callbacksRef.current.clear();
    };

    // Cleanup on unmount
    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
        workerRef.current = null;
      }
      callbacksRef.current.clear();
    };
  }, []);

  /**
   * Decode base64 audio using Web Worker
   */
  const decodeAudio = (audioBase64: string, callback: DecodeCallback) => {
    if (!workerRef.current) {
      callback(null, 'Worker not initialized');
      return;
    }

    // Generate unique ID for this request
    const id = Math.random().toString(36).substring(7);

    // Store callback
    callbacksRef.current.set(id, callback);

    // Send message to worker
    const message: AudioWorkerMessage = {
      id,
      audioBase64,
    };

    workerRef.current.postMessage(message);
  };

  return { decodeAudio };
};
