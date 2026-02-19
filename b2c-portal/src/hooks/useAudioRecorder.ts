import { useState, useRef, useCallback } from 'react';

interface UseAudioRecorderOptions {
  onRecordingComplete?: (audioBlob: Blob) => void;
  onError?: (error: Error) => void;
  mimeType?: string;
}

interface UseAudioRecorderReturn {
  isRecording: boolean;
  audioBlob: Blob | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  clearRecording: () => void;
  error: Error | null;
}

/**
 * Reusable hook for audio recording using MediaRecorder API
 *
 * @example
 * const { isRecording, audioBlob, startRecording, stopRecording } = useAudioRecorder({
 *   onRecordingComplete: (blob) => console.log('Recording complete:', blob),
 *   onError: (err) => console.error('Recording error:', err)
 * });
 */
export const useAudioRecorder = (
  options: UseAudioRecorderOptions = {}
): UseAudioRecorderReturn => {
  const {
    onRecordingComplete,
    onError,
    mimeType = 'audio/webm',
  } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  /**
   * Start recording audio from user's microphone
   */
  const startRecording = useCallback(async () => {
    try {
      console.log('[AudioRecorder] 🎤 Requesting microphone access...');

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });

      streamRef.current = stream;
      console.log('[AudioRecorder] ✅ Microphone access granted');

      // Determine best supported mime type
      let selectedMimeType = mimeType;
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        console.warn(`[AudioRecorder] ⚠️  ${mimeType} not supported, trying alternatives...`);

        const alternatives = [
          'audio/webm;codecs=opus',
          'audio/webm',
          'audio/ogg;codecs=opus',
          'audio/mp4',
          'audio/wav'
        ];

        for (const altType of alternatives) {
          if (MediaRecorder.isTypeSupported(altType)) {
            selectedMimeType = altType;
            console.log(`[AudioRecorder] ✅ Using ${altType}`);
            break;
          }
        }
      }

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: selectedMimeType
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Handle data available event
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          console.log(`[AudioRecorder] 📦 Audio chunk received: ${event.data.size} bytes`);
          audioChunksRef.current.push(event.data);
        }
      };

      // Handle stop event
      mediaRecorder.onstop = () => {
        console.log(`[AudioRecorder] ⏹️  Recording stopped, total chunks: ${audioChunksRef.current.length}`);

        // Create final blob
        const blob = new Blob(audioChunksRef.current, { type: selectedMimeType });
        setAudioBlob(blob);

        // Cleanup
        stream.getTracks().forEach(track => {
          track.stop();
          console.log('[AudioRecorder] 🛑 Audio track stopped');
        });
        streamRef.current = null;

        // Call callback
        onRecordingComplete?.(blob);
      };

      // Handle errors
      mediaRecorder.onerror = (event: Event) => {
        const error = new Error(`MediaRecorder error: ${(event as any).error?.message || 'Unknown error'}`);
        console.error('[AudioRecorder] ❌ Recording error:', error);
        setError(error);
        onError?.(error);
      };

      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
      setError(null);
      console.log('[AudioRecorder] ▶️  Recording started');

    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      console.error('[AudioRecorder] ❌ Failed to start recording:', error);

      setError(error);
      setIsRecording(false);
      onError?.(error);

      // Cleanup on error
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    }
  }, [mimeType, onRecordingComplete, onError]);

  /**
   * Stop recording audio
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      console.log('[AudioRecorder] 🛑 Stopping recording...');
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    } else {
      console.warn('[AudioRecorder] ⚠️  Cannot stop - not currently recording');
    }
  }, [isRecording]);

  /**
   * Clear the current recording
   */
  const clearRecording = useCallback(() => {
    console.log('[AudioRecorder] 🗑️  Clearing recording');
    setAudioBlob(null);
    setError(null);
    audioChunksRef.current = [];
  }, []);

  return {
    isRecording,
    audioBlob,
    startRecording,
    stopRecording,
    clearRecording,
    error,
  };
};