/**
 * useASRStreaming Hook
 *
 * React hook for ASR (Speech Recognition) functionality with multiple modes:
 * - Real-time WebSocket streaming (interim + final results)
 * - File-based transcription (record then transcribe)
 * - VAD (Voice Activity Detection) - hands-free auto-transcription
 *
 * Features:
 * - Real-time WebSocket streaming (interim + final results)
 * - File-based transcription (record then transcribe)
 * - VAD mode with automatic speech detection
 * - Audio recording with MediaRecorder
 * - Language selection
 * - Error handling
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { VoiceActivityDetector } from '../utils/vad';

export type ASRMode = 'realtime' | 'file' | 'vad';

export interface TranscriptSegment {
  id: number;
  text: string;
  start?: number;
  end?: number;
  isFinal: boolean;
}

export interface UseASRStreamingOptions {
  apiBaseUrl: string;
  wsBaseUrl: string;
  getAuthToken: () => Promise<string>;
  providerId?: string;
  language?: string;
  mode?: ASRMode;
  onTranscript?: (text: string, isFinal: boolean) => void;
  onError?: (error: Error) => void;
  onVolumeChange?: (volume: number) => void;
  onStatusChange?: (status: string) => void;
  // VAD options
  vadEnergyThreshold?: number;
  vadSilenceTimeout?: number;
  vadSpeechTimeout?: number;
}

export interface UseASRStreamingResult {
  isRecording: boolean;
  isConnected: boolean;
  isProcessing: boolean;
  isListening: boolean;  // VAD mode: listening for speech
  isSpeaking: boolean;   // VAD mode: speech detected
  volume: number;        // VAD mode: current audio level 0-100
  transcript: string;
  interimTranscript: string;
  segments: TranscriptSegment[];
  error: string | null;
  status: string;
  mode: ASRMode;
  recordingTime: number;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  clearTranscript: () => void;
  setMode: (mode: ASRMode) => void;
  setLanguage: (language: string) => void;
  setProviderId: (providerId: string) => void;
}

export function useASRStreaming({
  apiBaseUrl,
  wsBaseUrl,
  getAuthToken,
  providerId: initialProviderId = 'faster_whisper_large',
  language: initialLanguage = 'en',
  mode: initialMode = 'realtime', // Default to 'realtime' mode for streaming
  onTranscript,
  onError,
  onVolumeChange,
  onStatusChange,
  vadEnergyThreshold = 0.02,
  vadSilenceTimeout = 1500,
  vadSpeechTimeout = 300,
}: UseASRStreamingOptions): UseASRStreamingResult {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [volume, setVolume] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState('');
  const [mode, setMode] = useState<ASRMode>(initialMode || 'realtime');
  const [language, setLanguage] = useState(initialLanguage);
  const [providerId, setProviderId] = useState(initialProviderId);
  const [recordingTime, setRecordingTime] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const websocketRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const vadRef = useRef<VoiceActivityDetector | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const recordingStartTimeRef = useRef<number>(0);
  const recordingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Sync mode when initialMode prop changes
  useEffect(() => {
    if (initialMode && mode !== initialMode) {
      console.log('[useASRStreaming] Syncing mode from', mode, 'to', initialMode);
      setMode(initialMode);
    }
  }, [initialMode]); // eslint-disable-line react-hooks/exhaustive-deps

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  // Recording timer
  useEffect(() => {
    if (isRecording) {
      recordingStartTimeRef.current = Date.now();
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(Math.floor((Date.now() - recordingStartTimeRef.current) / 1000));
      }, 100);
    } else {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
      setRecordingTime(0);
    }

    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, [isRecording]);

  const startRealtimeRecording = useCallback(async () => {
    try {
      const token = await getAuthToken();

      // Connect WebSocket for real-time streaming
      // Note: Backend WebSocket is at /api/asr/ws/transcribe/stream/{provider_id}
      // and expects JSON messages with base64 audio data
      const wsUrl = `${wsBaseUrl}/api/asr/ws/transcribe/stream/${providerId}?token=${token}&language=${language}`;

      websocketRef.current = new WebSocket(wsUrl);

      websocketRef.current.onopen = () => {
        setIsConnected(true);
        setError(null);
      };

      websocketRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.error) {
            setError(data.error);
            onError?.(new Error(data.error));
            return;
          }

          if (data.type === 'interim') {
            setInterimTranscript(data.text || '');
            onTranscript?.(data.text || '', false);
          } else if (data.type === 'final') {
            const finalText = data.text || '';
            setTranscript(prev => prev + (prev ? ' ' : '') + finalText);
            setInterimTranscript('');
            setSegments(prev => [...prev, {
              id: prev.length,
              text: finalText,
              start: data.start,
              end: data.end,
              isFinal: true,
            }]);
            onTranscript?.(finalText, true);
          }
        } catch (err) {
          console.warn('Failed to parse WebSocket message:', event.data);
        }
      };

      websocketRef.current.onerror = (event) => {
        const errorMsg = 'Real-time ASR not available. Switching to file-based mode.';
        console.warn('WebSocket ASR error - endpoint may not exist:', wsUrl);
        setError(errorMsg);
        setIsConnected(false);
        // Auto-fallback to file mode
        setMode('file');
        // Close any existing stream before starting file recording
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
        startFileRecording();
      };

      websocketRef.current.onclose = () => {
        setIsConnected(false);
      };

      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        }
      });

      streamRef.current = stream;

      // Set up audio processing for WebSocket streaming
      audioContextRef.current = new AudioContext({ sampleRate: 16000 });
      const source = audioContextRef.current.createMediaStreamSource(stream);

      // Use ScriptProcessorNode for raw audio access (deprecated but widely supported)
      processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);

      processorRef.current.onaudioprocess = (event) => {
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
          const inputData = event.inputBuffer.getChannelData(0);
          // Convert Float32Array to Int16Array for transmission
          const int16Data = new Int16Array(inputData.length);
          for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]));
            int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
          }
          // Send as JSON with base64-encoded audio data (backend expects this format)
          const uint8Array = new Uint8Array(int16Data.buffer);
          const base64Audio = btoa(String.fromCharCode(...uint8Array));
          websocketRef.current.send(JSON.stringify({
            type: 'audio',
            data: base64Audio
          }));
        }
      };

      source.connect(processorRef.current);
      processorRef.current.connect(audioContextRef.current.destination);

      setIsRecording(true);

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to start recording';
      setError(errorMsg);
      onError?.(err instanceof Error ? err : new Error(errorMsg));
      // Fallback to file mode
      setMode('file');
      await startFileRecording();
    }
  }, [wsBaseUrl, getAuthToken, providerId, language, onTranscript, onError]);

  const startFileRecording = useCallback(async () => {
    try {
      setError(null);
      audioChunksRef.current = [];

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        }
      });

      streamRef.current = stream;

      // Use MediaRecorder for file-based recording
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000,
      });

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        await processRecordedAudio();
      };

      mediaRecorderRef.current.start(1000); // Collect data every second
      setIsRecording(true);

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to start recording';
      setError(errorMsg);
      onError?.(err instanceof Error ? err : new Error(errorMsg));
    }
  }, [onError]);

  const processRecordedAudio = useCallback(async () => {
    if (audioChunksRef.current.length === 0) return;

    setIsProcessing(true);

    try {
      const token = await getAuthToken();

      // Create audio blob
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

      // Create FormData with audio file and form fields
      // Note: backend expects 'audio_file' field name, not 'file'
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');
      formData.append('provider_id', providerId);
      formData.append('language', language || '');
      formData.append('task', 'transcribe');

      // Send to file upload API endpoint
      const response = await fetch(`${apiBaseUrl}/api/asr/transcribe/upload?skip_billing=true`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Transcription failed: ${response.status}`);
      }

      const result = await response.json();

      // Update transcript
      const text = result.text?.trim() || '';
      if (text) {
        setTranscript(prev => prev + (prev ? ' ' : '') + text);

        // Add segment
        setSegments(prev => [...prev, {
          id: prev.length,
          text: text,
          isFinal: true,
        }]);

        onTranscript?.(text, true);
      }

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Transcription failed';
      setError(errorMsg);
      onError?.(err instanceof Error ? err : new Error(errorMsg));
    } finally {
      setIsProcessing(false);
      audioChunksRef.current = [];
    }
  }, [apiBaseUrl, getAuthToken, providerId, language, onTranscript, onError]);

  // VAD-based transcription using file upload endpoint
  const transcribeAudioBlob = useCallback(async (audioBlob: Blob) => {
    setIsProcessing(true);
    setInterimTranscript('Transcribing...');
    setStatus('Transcribing...');
    onStatusChange?.('Transcribing...');

    try {
      const token = await getAuthToken();

      // Create FormData with audio file and form fields
      // Note: backend expects 'audio_file' field name, not 'file'
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'speech.webm');
      formData.append('provider_id', providerId);
      formData.append('language', language || '');
      formData.append('task', 'transcribe');

      // Create abort controller for this request
      abortControllerRef.current = new AbortController();

      // Make API request - using file upload endpoint
      const response = await fetch(
        `${apiBaseUrl}/api/asr/transcribe/upload?skip_billing=true`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
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
        setSegments(prev => [...prev, {
          id: prev.length,
          text: text,
          isFinal: true,
        }]);
        setInterimTranscript('');
        onTranscript?.(text, true);
        setStatus('Listening...');
        onStatusChange?.('Listening...');
      } else {
        setInterimTranscript('');
        setStatus('No speech detected - Listening...');
        onStatusChange?.('No speech detected - Listening...');
      }

    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('[ASR] Request aborted');
      } else {
        const errorMsg = err.message || 'Transcription failed';
        console.error('[ASR] Error:', errorMsg);
        setError(errorMsg);
        onError?.(err instanceof Error ? err : new Error(errorMsg));
        setInterimTranscript('');
        setStatus(`Error: ${errorMsg}`);
        onStatusChange?.(`Error: ${errorMsg}`);
      }
    } finally {
      setIsProcessing(false);
      abortControllerRef.current = null;
    }
  }, [apiBaseUrl, getAuthToken, providerId, language, onTranscript, onError, onStatusChange]);

  // Start VAD-based listening
  const startVADListening = useCallback(async () => {
    try {
      setError(null);
      setStatus('Starting microphone...');
      onStatusChange?.('Starting microphone...');

      // Create VAD instance
      vadRef.current = new VoiceActivityDetector({
        energyThreshold: vadEnergyThreshold,
        silenceTimeout: vadSilenceTimeout,
        speechTimeout: vadSpeechTimeout,
        onSpeechStart: () => {
          console.log('[ASR VAD] Speech started');
          setIsSpeaking(true);
          setInterimTranscript('Listening...');
          setStatus('Recording speech...');
          onStatusChange?.('Recording speech...');
        },
        onSpeechEnd: (audioBlob: Blob) => {
          console.log('[ASR VAD] Speech ended, transcribing...');
          setIsSpeaking(false);
          transcribeAudioBlob(audioBlob);
        },
        onVolumeChange: (vol: number) => {
          setVolume(vol);
          onVolumeChange?.(vol);
        },
        onError: (err: string) => {
          setError(err);
          onError?.(new Error(err));
        }
      });

      // Start VAD
      await vadRef.current.start();
      setIsListening(true);
      setIsRecording(true);
      setStatus('Listening... (speak when ready)');
      onStatusChange?.('Listening... (speak when ready)');

    } catch (err: any) {
      const errorMsg = err.message || 'Failed to start microphone';
      setError(errorMsg);
      onError?.(err instanceof Error ? err : new Error(errorMsg));
      vadRef.current = null;
    }
  }, [vadEnergyThreshold, vadSilenceTimeout, vadSpeechTimeout, transcribeAudioBlob, onVolumeChange, onError, onStatusChange]);

  // Stop VAD listening
  const stopVADListening = useCallback(() => {
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
    setIsRecording(false);
    setIsSpeaking(false);
    setVolume(0);
    setInterimTranscript('');
    setStatus('Stopped');
    onStatusChange?.('Stopped');
  }, [onStatusChange]);

  const startRecording = useCallback(async () => {
    if (mode === 'realtime') {
      await startRealtimeRecording();
    } else if (mode === 'vad') {
      await startVADListening();
    } else {
      await startFileRecording();
    }
  }, [mode, startRealtimeRecording, startVADListening, startFileRecording]);

  const stopRecording = useCallback(() => {
    // Stop VAD if active
    if (vadRef.current) {
      stopVADListening();
      return;
    }

    // Send end message to trigger transcription before closing WebSocket
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({ type: 'end' }));
    }

    // Stop WebSocket after a short delay to allow end message to be sent
    setTimeout(() => {
      if (websocketRef.current) {
        websocketRef.current.close();
        websocketRef.current = null;
      }
    }, 500);

    // Stop audio processing
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Stop MediaRecorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }

    // Stop media stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    setIsRecording(false);
    setIsConnected(false);
    setIsListening(false);
    setIsSpeaking(false);
    setVolume(0);
    setInterimTranscript('');
    setStatus('');
  }, [stopVADListening]);

  const clearTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    setSegments([]);
    setError(null);
  }, []);

  return {
    isRecording,
    isConnected,
    isProcessing,
    isListening,
    isSpeaking,
    volume,
    transcript,
    interimTranscript,
    segments,
    error,
    status,
    mode,
    recordingTime,
    startRecording,
    stopRecording,
    clearTranscript,
    setMode,
    setLanguage,
    setProviderId,
  };
}

export default useASRStreaming;
