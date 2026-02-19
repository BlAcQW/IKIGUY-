/**
 * useVoiceRecorder Hook
 *
 * Manages voice recording with Web Audio API for browser-based voice chat.
 * Provides audio level visualization and converts recordings to base64.
 */

import { useState, useRef, useCallback, useEffect } from 'react';

interface UseVoiceRecorderOptions {
  onRecordingComplete?: (audioBase64: string, blob: Blob) => void;
  onError?: (error: string) => void;
  maxDuration?: number; // in seconds
  autoStopOnSilence?: boolean;
  silenceThreshold?: number; // 0-1
  silenceTimeout?: number; // ms
}

interface UseVoiceRecorderResult {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  audioLevel: number;
  permissionGranted: boolean | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  pauseRecording: () => void;
  resumeRecording: () => void;
  cancelRecording: () => void;
  checkPermission: () => Promise<boolean>;
}

/**
 * Convert blob to base64 string
 */
async function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result as string;
      // Remove the data URL prefix (e.g., "data:audio/webm;base64,")
      const base64Data = base64.split(',')[1];
      resolve(base64Data);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

export function useVoiceRecorder({
  onRecordingComplete,
  onError,
  maxDuration = 60,
  autoStopOnSilence = false,
  silenceThreshold = 0.05,
  silenceTimeout = 2000,
}: UseVoiceRecorderOptions = {}): UseVoiceRecorderResult {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [duration, setDuration] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [permissionGranted, setPermissionGranted] = useState<boolean | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, []);

  const cleanup = useCallback(() => {
    // Stop all tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    // Clean up audio context
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Clear intervals and animation frames
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
      durationIntervalRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }

    setIsRecording(false);
    setIsPaused(false);
    setDuration(0);
    setAudioLevel(0);
  }, []);

  // Analyze audio level for visualization and silence detection
  const analyzeAudio = useCallback(() => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    // Calculate average volume
    const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
    const normalized = Math.min(average / 128, 1);

    setAudioLevel(normalized);

    // Auto-stop on silence detection
    if (autoStopOnSilence && normalized < silenceThreshold) {
      if (!silenceTimeoutRef.current) {
        silenceTimeoutRef.current = setTimeout(() => {
          if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            stopRecording();
          }
        }, silenceTimeout);
      }
    } else {
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
        silenceTimeoutRef.current = null;
      }
    }

    animationFrameRef.current = requestAnimationFrame(analyzeAudio);
  }, [autoStopOnSilence, silenceThreshold, silenceTimeout]);

  const checkPermission = useCallback(async (): Promise<boolean> => {
    try {
      // Check if permission API is available
      if (navigator.permissions) {
        const result = await navigator.permissions.query({ name: 'microphone' as PermissionName });
        if (result.state === 'granted') {
          setPermissionGranted(true);
          return true;
        } else if (result.state === 'denied') {
          setPermissionGranted(false);
          return false;
        }
      }

      // Try to get permission by requesting media
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      setPermissionGranted(true);
      return true;
    } catch {
      setPermissionGranted(false);
      return false;
    }
  }, []);

  const startRecording = useCallback(async () => {
    try {
      // Request microphone access with optimal settings
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000, // Optimal for speech recognition
        },
      });

      streamRef.current = stream;
      setPermissionGranted(true);

      // Set up audio analysis for visualization
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;
      const analyser = audioContext.createAnalyser();
      analyserRef.current = analyser;
      analyser.fftSize = 256;

      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);

      // Set up media recorder with webm/opus for best browser support
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });

        try {
          const audioBase64 = await blobToBase64(audioBlob);
          onRecordingComplete?.(audioBase64, audioBlob);
        } catch (err) {
          console.error('Error converting audio to base64:', err);
          onError?.('Failed to process recording');
        }

        cleanup();
      };

      // Start recording with timeslice for continuous data
      mediaRecorder.start(1000);
      setIsRecording(true);
      setDuration(0);

      // Start duration counter
      durationIntervalRef.current = setInterval(() => {
        setDuration((prev) => {
          const newDuration = prev + 1;
          if (newDuration >= maxDuration) {
            stopRecording();
          }
          return newDuration;
        });
      }, 1000);

      // Start audio analysis
      analyzeAudio();
    } catch (err) {
      console.error('Error starting recording:', err);
      setPermissionGranted(false);

      let errorMessage = 'Failed to access microphone';
      if (err instanceof DOMException) {
        if (err.name === 'NotAllowedError') {
          errorMessage = 'Microphone access denied. Please allow microphone access in your browser settings.';
        } else if (err.name === 'NotFoundError') {
          errorMessage = 'No microphone found. Please connect a microphone.';
        } else if (err.name === 'NotReadableError') {
          errorMessage = 'Microphone is in use by another application.';
        }
      }

      onError?.(errorMessage);
      cleanup();
    }
  }, [onRecordingComplete, onError, maxDuration, analyzeAudio, cleanup]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
    }
  }, []);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.pause();
      setIsPaused(true);

      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    }
  }, []);

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
      mediaRecorderRef.current.resume();
      setIsPaused(false);

      // Resume duration counter
      durationIntervalRef.current = setInterval(() => {
        setDuration((prev) => {
          const newDuration = prev + 1;
          if (newDuration >= maxDuration) {
            stopRecording();
          }
          return newDuration;
        });
      }, 1000);

      // Resume audio analysis
      analyzeAudio();
    }
  }, [maxDuration, stopRecording, analyzeAudio]);

  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current) {
      // Stop without triggering onRecordingComplete
      mediaRecorderRef.current.ondataavailable = null;
      mediaRecorderRef.current.onstop = null;
      if (mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
    }
    cleanup();
  }, [cleanup]);

  return {
    isRecording,
    isPaused,
    duration,
    audioLevel,
    permissionGranted,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    cancelRecording,
    checkPermission,
  };
}

export default useVoiceRecorder;
