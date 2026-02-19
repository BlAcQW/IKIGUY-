/**
 * Real-time ASR Hook with Voice Activity Detection
 *
 * Provides hands-free transcription with automatic speech detection.
 * Uses browser-side VAD to detect speech start/end and sends audio
 * to the ASR backend for transcription.
 *
 * Shared hook for all apps (StudyFlow, InkWave, etc.)
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { VoiceActivityDetector, VADOptions } from '../utils/vad';

export interface RealtimeASROptions {
  apiBaseUrl: string;
  providerId?: string;
  language?: string;
  task?: 'transcribe' | 'translate';
  getAuthHeaders?: () => Promise<Record<string, string>>;
  onTranscription?: (text: string, isFinal: boolean) => void;
  onError?: (error: string) => void;
  onStatusChange?: (status: string) => void;
  onVolumeChange?: (volume: number) => void;
  // VAD options
  energyThreshold?: number;
  silenceTimeout?: number;
  speechTimeout?: number;
}

export interface RealtimeASRResult {
  isListening: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;
  volume: number;
  transcript: string;
  interimTranscript: string;
  error: string | null;
  startListening: () => Promise<void>;
  stopListening: () => void;
  clearTranscript: () => void;
}

export function useRealtimeASR(options: RealtimeASROptions): RealtimeASRResult {
  const {
    apiBaseUrl,
    providerId = 'faster_whisper_large',
    language = 'en',
    task = 'transcribe',
    getAuthHeaders,
    onTranscription,
    onError,
    onStatusChange,
    onVolumeChange,
    energyThreshold = 0.02,
    silenceTimeout = 1500,
    speechTimeout = 300
  } = options;

  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [volume, setVolume] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);

  const vadRef = useRef<VoiceActivityDetector | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Transcribe audio blob via API
   */
  const transcribeAudio = useCallback(async (audioBlob: Blob) => {
    setIsProcessing(true);
    setInterimTranscript('Transcribing...');
    onStatusChange?.('Transcribing...');

    try {
      // Create FormData with audio file and form fields
      const formData = new FormData();
      formData.append('file', audioBlob, 'speech.webm');
      formData.append('provider_id', providerId);
      formData.append('language', language);
      formData.append('task', task);

      // Get auth headers
      const headers: Record<string, string> = getAuthHeaders
        ? await getAuthHeaders()
        : {};

      // Create abort controller for this request
      abortControllerRef.current = new AbortController();

      // Make API request
      const response = await fetch(
        `${apiBaseUrl}/api/asr/transcribe/upload?skip_billing=true`,
        {
          method: 'POST',
          headers,
          body: formData,
          signal: abortControllerRef.current.signal
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      const text = result.text?.trim() || '';

      if (text) {
        setTranscript(prev => prev ? `${prev} ${text}` : text);
        setInterimTranscript('');
        onTranscription?.(text, true);
        onStatusChange?.('Listening...');
      } else {
        setInterimTranscript('');
        onStatusChange?.('No speech detected - Listening...');
      }

    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('[RealtimeASR] Request aborted');
      } else {
        const errorMsg = err.message || 'Transcription failed';
        console.error('[RealtimeASR] Error:', errorMsg);
        setError(errorMsg);
        onError?.(errorMsg);
        setInterimTranscript('');
        onStatusChange?.(`Error: ${errorMsg}`);
      }
    } finally {
      setIsProcessing(false);
      abortControllerRef.current = null;
    }
  }, [apiBaseUrl, providerId, language, task, getAuthHeaders, onTranscription, onError, onStatusChange]);

  /**
   * Start listening with VAD
   */
  const startListening = useCallback(async () => {
    if (vadRef.current) {
      console.warn('[RealtimeASR] Already listening');
      return;
    }

    setError(null);
    onStatusChange?.('Starting microphone...');

    try {
      // Create VAD instance
      vadRef.current = new VoiceActivityDetector({
        energyThreshold,
        silenceTimeout,
        speechTimeout,
        onSpeechStart: () => {
          console.log('[RealtimeASR] Speech started');
          setIsSpeaking(true);
          setInterimTranscript('Listening...');
          onStatusChange?.('Recording speech...');
        },
        onSpeechEnd: (audioBlob: Blob) => {
          console.log('[RealtimeASR] Speech ended, transcribing...');
          setIsSpeaking(false);
          transcribeAudio(audioBlob);
        },
        onVolumeChange: (vol: number) => {
          setVolume(vol);
          onVolumeChange?.(vol);
        },
        onError: (err: string) => {
          setError(err);
          onError?.(err);
        }
      });

      // Start VAD
      await vadRef.current.start();
      setIsListening(true);
      onStatusChange?.('Listening... (speak when ready)');

    } catch (err: any) {
      const errorMsg = err.message || 'Failed to start microphone';
      setError(errorMsg);
      onError?.(errorMsg);
      vadRef.current = null;
    }
  }, [energyThreshold, silenceTimeout, speechTimeout, transcribeAudio, onStatusChange, onVolumeChange, onError]);

  /**
   * Stop listening
   */
  const stopListening = useCallback(() => {
    // Cancel any pending transcription
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    // Stop VAD
    if (vadRef.current) {
      vadRef.current.stop();
      vadRef.current = null;
    }

    setIsListening(false);
    setIsProcessing(false);
    setIsSpeaking(false);
    setVolume(0);
    setInterimTranscript('');
    onStatusChange?.('Stopped');
  }, [onStatusChange]);

  /**
   * Clear transcript
   */
  const clearTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (vadRef.current) {
        vadRef.current.stop();
        vadRef.current = null;
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, []);

  return {
    isListening,
    isProcessing,
    isSpeaking,
    volume,
    transcript,
    interimTranscript,
    error,
    startListening,
    stopListening,
    clearTranscript
  };
}
