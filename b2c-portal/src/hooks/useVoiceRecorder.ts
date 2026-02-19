import { useState, useRef, useCallback } from 'react';

/**
 * Reusable hook for voice recording and playback
 * Based on the working implementation from VoiceCreationWizard
 *
 * @example
 * const {
 *   isRecording,
 *   isPlaying,
 *   audioUrl,
 *   audioBlob,
 *   startRecording,
 *   stopRecording,
 *   playAudio,
 *   stopPlayback
 * } = useVoiceRecorder();
 */
export interface UseVoiceRecorderReturn {
  isRecording: boolean;
  isPlaying: boolean;
  audioUrl: string | null;
  audioBlob: Blob | null;
  duration: number;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  playAudio: () => void;
  stopPlayback: () => void;
  clearRecording: () => void;
}

export const useVoiceRecorder = (): UseVoiceRecorderReturn => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [duration, setDuration] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const startTimeRef = useRef<number>(0);

  /**
   * Start recording audio from microphone
   */
  const startRecording = useCallback(async () => {
    console.log('[VoiceRecorder] 🎙️ Starting audio recording...');

    try {
      console.log('[VoiceRecorder] 🔍 Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });
      console.log('[VoiceRecorder] ✅ Microphone access granted');

      // Try to use audio/webm if supported, otherwise fallback
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/wav';

      console.log('[VoiceRecorder] 🎵 Using audio format:', mimeType);

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      startTimeRef.current = Date.now();
      console.log('[VoiceRecorder] 📱 MediaRecorder initialized');

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          console.log(`[VoiceRecorder] 📊 Audio chunk received (${event.data.size} bytes)`);
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const recordingDuration = (Date.now() - startTimeRef.current) / 1000;
        const blob = new Blob(chunksRef.current, { type: mimeType });
        console.log('[VoiceRecorder] 🎵 Recording completed:', {
          size: `${(blob.size / 1024).toFixed(2)} KB`,
          type: blob.type,
          chunks: chunksRef.current.length,
          duration: `${recordingDuration.toFixed(2)}s`
        });

        // Create audio URL for playback
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        setAudioBlob(blob);
        setDuration(recordingDuration);
        console.log('[VoiceRecorder] 🎧 Audio URL created for playback');

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        console.log('[VoiceRecorder] 🔇 Microphone stream stopped');
      };

      mediaRecorder.start();
      setIsRecording(true);
      console.log('[VoiceRecorder] ▶️ Recording started successfully');
    } catch (error) {
      console.error('[VoiceRecorder] ❌ Error starting recording:', error);
      if (error instanceof DOMException) {
        console.error('[VoiceRecorder] 📝 Error name:', error.name);
        console.error('[VoiceRecorder] 📝 Error message:', error.message);

        // Provide helpful error messages
        if (error.name === 'NotAllowedError') {
          throw new Error('Microphone access denied. Please grant microphone permissions and try again.');
        } else if (error.name === 'NotFoundError') {
          throw new Error('No microphone found. Please connect a microphone and try again.');
        }
      }
      throw error;
    }
  }, []);

  /**
   * Stop recording
   */
  const stopRecording = useCallback(() => {
    console.log('[VoiceRecorder] ⏹️ Stopping audio recording...');
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      console.log('[VoiceRecorder] ✅ Recording stopped successfully');
    } else {
      console.log('[VoiceRecorder] ⚠️ No active recording to stop');
    }
  }, []);

  /**
   * Play recorded audio
   */
  const playAudio = useCallback(() => {
    if (audioUrl && !isPlaying) {
      console.log('[VoiceRecorder] ▶️ Playing recorded audio...');

      // Stop previous audio if any
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlaying(false);
        console.log('[VoiceRecorder] ⏹️ Audio playback ended');
      };

      audio.onerror = (error) => {
        setIsPlaying(false);
        console.error('[VoiceRecorder] ❌ Audio playback error:', error);
      };

      audio.play()
        .then(() => {
          setIsPlaying(true);
          console.log('[VoiceRecorder] ✅ Audio playback started');
        })
        .catch(error => {
          setIsPlaying(false);
          console.error('[VoiceRecorder] ❌ Failed to play audio:', error);
        });
    } else if (isPlaying) {
      console.log('[VoiceRecorder] ⚠️ Audio is already playing');
    } else {
      console.log('[VoiceRecorder] ⚠️ No audio to play');
    }
  }, [audioUrl, isPlaying]);

  /**
   * Stop audio playback
   */
  const stopPlayback = useCallback(() => {
    if (audioRef.current && isPlaying) {
      console.log('[VoiceRecorder] ⏸️ Stopping audio playback...');
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      console.log('[VoiceRecorder] ✅ Audio playback stopped');
    }
  }, [isPlaying]);

  /**
   * Clear recorded audio
   */
  const clearRecording = useCallback(() => {
    console.log('[VoiceRecorder] 🗑️ Clearing recording...');

    // Stop playback if active
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    // Revoke object URL to free memory
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }

    setAudioUrl(null);
    setAudioBlob(null);
    setIsPlaying(false);
    setDuration(0);
    chunksRef.current = [];
    console.log('[VoiceRecorder] ✅ Recording cleared');
  }, [audioUrl]);

  return {
    isRecording,
    isPlaying,
    audioUrl,
    audioBlob,
    duration,
    startRecording,
    stopRecording,
    playAudio,
    stopPlayback,
    clearRecording
  };
};