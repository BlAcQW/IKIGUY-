import { useState, useRef, useCallback, useEffect } from 'react';
import { getAuthToken } from '@/lib/auth-utils';
import { blobToBase64, playAudioBase64 } from '@/lib/audio-utils';
import { getAudioProcessor } from '@/services/audio-processor';
import { WS_BASE_URL } from '@/config/api-config';

interface WebSocketMessage {
  type: string;
  data: any;
}

interface UseWebSocketChatOptions {
  assistantId: string;
  onTranscription?: (text: string, isFinal: boolean) => void;
  onTextResponse?: (text: string) => void;
  onAudioChunk?: (audioData: string) => void;
  onAudioComplete?: (metadata: any) => void;
  onError?: (error: string) => void;
  onStatusChange?: (status: string) => void;
}

export const useWebSocketChat = ({
  assistantId,
  onTranscription,
  onTextResponse,
  onAudioChunk,
  onAudioComplete,
  onError,
  onStatusChange
}: UseWebSocketChatOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  // Use refs to track latest state for use in callbacks (avoid stale closures)
  const isRecordingRef = useRef(false);
  const isSpeakingRef = useRef(false);

  // VAD refs - persist across recordings
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaStreamSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const vadMonitoringRef = useRef<boolean>(false);

  // Wrapper to update both state and ref
  const updateIsRecording = (value: boolean) => {
    isRecordingRef.current = value;
    setIsRecording(value);
  };

  const updateIsSpeaking = (value: boolean) => {
    isSpeakingRef.current = value;
    setIsSpeaking(value);
  };

  // WebSocket URL with authentication
  const getWebSocketUrl = async () => {
    const baseUrl = WS_BASE_URL;
    try {
      console.log(`[WS] 🔑 Getting auth token for assistant ${assistantId}...`);
      const token = await getAuthToken();
      const url = `${baseUrl}/voice/ws/voice-chat/${assistantId}?token=${token.substring(0, 20)}...`;
      console.log(`[WS] ✅ Auth token obtained. URL: ${url}`);
      return `${baseUrl}/voice/ws/voice-chat/${assistantId}?token=${token}`;
    } catch (error) {
      console.error('[WS] ❌ Failed to get auth token for WebSocket:', error);
      // Fallback without token (will likely fail but provides clearer error)
      return `${baseUrl}/voice/ws/voice-chat/${assistantId}`;
    }
  };

  // Handle incoming WebSocket messages (defined before connect so it can be used)
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    console.log(`[WS] 🎯 Handling message type: ${message.type}`);

    switch (message.type) {
      case 'status':
        console.log('[WS] 📊 Status update:', message.data);
        onStatusChange?.(message.data);
        break;

      case 'transcription':
        const { text, is_final } = message.data;
        console.log(`[WS] 🎤 Transcription: "${text}" (final: ${is_final})`);
        onTranscription?.(text, is_final);
        break;

      case 'text_response':
        console.log('[WS] 💬 Text response:', message.data.substring(0, 100) + (message.data.length > 100 ? '...' : ''));
        onTextResponse?.(message.data);
        break;

      case 'audio_chunk':
        const chunkSize = message.data?.length || 0;
        console.log(`[WS] 🔊 Audio chunk received (${chunkSize} bytes)`);
        onAudioChunk?.(message.data);
        break;

      case 'audio_complete':
        console.log('[WS] ✅ Audio complete:', message.data);
        onAudioComplete?.(message.data);
        break;

      case 'stop_recording':
        console.log('[WS] 🛑 Server requested stop recording:', message.data);
        // Auto-stop recording when server detects silence
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          console.log('[WS] 🔴 Auto-stopping recording due to silence detection');
          mediaRecorderRef.current.stop();
          updateIsRecording(false);
          onStatusChange?.(message.data || 'Processing...');
        }
        break;

      case 'ready_to_listen':
        console.log('[WS] 👂 Assistant ready to listen:', message.data);
        // Signal user that it's their turn
        onStatusChange?.('Your turn - speak now');
        break;

      case 'start_recording':
        console.log('[WS] 🎤 Server requested start recording (hands-free):', message.data);
        // Hands-free mode: Auto-start recording
        // CRITICAL: Wait for audio to ACTUALLY finish playing before starting
        if (!isRecordingRef.current) {
          const waitForAudioComplete = () => {
            if (isSpeakingRef.current || currentAudioRef.current) {
              console.log('[WS] ⏳ Waiting for audio to finish before starting recording...');
              setTimeout(waitForAudioComplete, 200);
            } else {
              console.log('[WS] ✅ Audio finished, auto-starting recording in hands-free mode');
              startRecordingInternal();
            }
          };

          // Start checking after small delay
          setTimeout(waitForAudioComplete, 100);
          onStatusChange?.('Listening...');
        } else {
          console.log('[WS] ⏭️  Skipping auto-start - already recording');
        }
        break;

      case 'conversation_state':
        console.log('[WS] 🔄 Conversation state changed:', message.data);
        // Update UI based on conversation state
        const canRecord = message.data.can_record;
        if (!canRecord && isRecordingRef.current) {
          console.log('[WS] ⛔ Cannot record in current state, stopping');
          stopRecordingInternal();
        }
        break;

      case 'interrupted':
        console.log('[WS] ⚡ User interrupted assistant');
        // Clear audio queue
        audioQueueRef.current = [];
        isPlayingRef.current = false;
        updateIsSpeaking(false);
        onStatusChange?.('Interrupted');
        break;

      case 'barge_in':
        console.log('[WS] 🎤 Server acknowledged barge-in');
        // Barge-in acknowledged by server
        break;

      case 'barge_in_ack':
        console.log('[WS] ✅ Barge-in acknowledged by server');
        onStatusChange?.('Ready to listen');
        break;

      case 'assistant_speaking_start':
        console.log('[WS] 🔊 Assistant started speaking');
        updateIsSpeaking(true);
        onStatusChange?.('Assistant speaking...');
        break;

      case 'assistant_speaking_end':
        console.log('[WS] ✅ Assistant finished speaking');
        updateIsSpeaking(false);
        onStatusChange?.('Ready');
        break;

      case 'error':
        console.error('[WS] ❌ Server error:', message.data);
        onError?.(message.data);
        break;

      default:
        console.warn('[WS] ⚠️  Unknown message type:', message.type, message);
    }
  }, [onStatusChange, onTranscription, onTextResponse, onAudioChunk, onAudioComplete, onError]);

  // Connect to WebSocket
  const connect = useCallback(async () => {
    // Validate assistantId before connecting
    if (!assistantId || assistantId.trim() === '') {
      const errorMsg = 'Cannot connect: Assistant ID is required';
      console.error('[WS] ❌', errorMsg);
      onError?.(errorMsg);
      onStatusChange?.('Error: No assistant selected');
      return;
    }

    // Close existing connection if any
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
        console.log('[WS] ⏭️  Connection already exists (state:', wsRef.current.readyState, '), closing first...');
        wsRef.current.close();
      }
      wsRef.current = null;
    }

    const wsUrl = await getWebSocketUrl();
    console.log('[WS] 🔌 Connecting to WebSocket...');
    console.log('[WS] 📍 Assistant ID:', assistantId);
    console.log('[WS] 🔗 URL (masked):', wsUrl.substring(0, 80) + '...');

    try {
      const ws = new WebSocket(wsUrl);

      // Set ref IMMEDIATELY after creation to prevent race conditions
      wsRef.current = ws;
      console.log('[WS] 🚀 WebSocket instance created (ReadyState:', ws.readyState, ') - waiting for open event...');

      ws.onopen = () => {
        console.log('[WS] ✅ WebSocket connected successfully!');
        console.log('[WS] 📊 ReadyState:', ws.readyState, '(1 = OPEN)');
        setIsConnected(true);
        onStatusChange?.('Connected');

        // Clear reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          console.log('[WS] 🔄 Cleared reconnect timeout');
        }
      };

      ws.onmessage = (event) => {
        console.log('[WS] 📨 Message received:', event.data.substring(0, 100) + (event.data.length > 100 ? '...' : ''));
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log(`[WS] 📦 Parsed message type: ${message.type}`);
          handleWebSocketMessage(message);
        } catch (err) {
          console.error('[WS] ❌ Error parsing WebSocket message:', err);
          console.error('[WS] 📄 Raw message:', event.data);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] ❌ WebSocket error event:', error);
        console.error('[WS] 📊 ReadyState:', ws.readyState, '(0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED)');
        console.error('[WS] 🔗 URL (masked):', wsUrl.substring(0, 80) + '...');
        onError?.('Connection error');
      };

      ws.onclose = (event) => {
        console.log('[WS] 🔌 WebSocket closed');
        console.log('[WS] 📊 Close code:', event.code);
        console.log('[WS] 📝 Close reason:', event.reason || '(no reason provided)');
        console.log('[WS] 🧹 Was clean:', event.wasClean);
        setIsConnected(false);
        wsRef.current = null;
        onStatusChange?.('Disconnected');

        // Only attempt to reconnect for abnormal closures
        if (!event.wasClean && event.code !== 1000) {
          console.log('[WS] 🔄 Abnormal closure detected, will attempt reconnect in 3 seconds...');
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('[WS] 🔄 Attempting to reconnect...');
            connect();
          }, 3000);
        }
      };
    } catch (error) {
      console.error('[WS] ❌ Failed to create WebSocket:', error);
      wsRef.current = null;
      onError?.('Failed to connect');
    }
  }, [assistantId, onStatusChange, onError, handleWebSocketMessage]);

  // Send message through WebSocket
  const sendMessage = (type: string, data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const dataPreview = typeof data === 'string'
        ? data.substring(0, 100) + (data.length > 100 ? '...' : '')
        : JSON.stringify(data).substring(0, 100);
      console.log(`[WS] 📤 Sending message type: ${type}, data: ${dataPreview}`);
      wsRef.current.send(JSON.stringify({ type, data }));
    } else {
      console.error('[WS] ❌ Cannot send message - WebSocket not connected. ReadyState:', wsRef.current?.readyState);
      onError?.('Not connected');
    }
  };

  // Send text message
  const sendTextMessage = (text: string) => {
    console.log(`[WS] 💬 Sending text message: "${text}"`);
    sendMessage('text', text);
  };

  // Start recording audio (internal function) - using original MediaRecorder approach
  const startRecordingInternal = async () => {
    console.log('[WS] 🎤 Starting audio recording...');

    try {
      console.log('[WS] 🔒 Requesting microphone access...');

      // CRITICAL FIX: Request a FRESH microphone stream for each recording
      // to ensure MediaRecorder starts with EBML header, not just clusters
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1
        }
      });

      console.log('[WS] ✅ Microphone access granted');
      console.log('[WS] 🎚️  Audio tracks:', stream.getAudioTracks().length);

      // Use WebM with Opus for browser compatibility
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/wav';

      console.log('[WS] 🎵 Recording format:', mimeType);

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      let chunkCount = 0;

      // Send audio chunks in real-time for streaming transcription
      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          chunkCount++;
          console.log(`[WS] 🎤 Audio chunk #${chunkCount} received (${event.data.size} bytes, type: ${event.data.type})`);

          // DEBUG: Check magic bytes
          const arrayBuffer = await event.data.arrayBuffer();
          const bytes = new Uint8Array(arrayBuffer);
          const magicBytes = Array.from(bytes.slice(0, 4)).map(b => '0x' + b.toString(16).padStart(2, '0')).join(' ');
          console.log(`[WS] 🔍 Magic bytes of chunk #${chunkCount}: ${magicBytes}`);

          // Convert back to Blob for storage
          const blob = new Blob([arrayBuffer], { type: event.data.type });
          audioChunksRef.current.push(blob);

          // Convert chunk to base64 and send immediately for streaming
          try {
            const chunkBase64 = await blobToBase64(blob);
            console.log(`[WS] 📤 Sending audio chunk #${chunkCount} for streaming`);
            sendMessage('audio', chunkBase64);
          } catch (error) {
            console.error('[WS] ❌ Failed to send audio chunk:', error);
          }
        }
      };

      mediaRecorder.onstop = async () => {
        console.log('[WS] ⏹️  Recording stopped after', chunkCount, 'chunks');

        // Send end of audio signal to finalize any pending transcriptions
        console.log('[WS] 📤 Sending end_audio signal');
        sendMessage('end_audio', null);

        // Clear chunks buffer
        audioChunksRef.current = [];

        // Stop all tracks from THIS recording's stream
        console.log('[WS] 🛑 Stopping all audio tracks');
        stream.getTracks().forEach(track => {
          console.log('[WS] 🔌 Stopping track:', track.kind, track.label);
          track.stop();
        });

        // Clear MediaRecorder ref to ensure fresh instance next time
        mediaRecorderRef.current = null;
      };

      // Set up frontend VAD (Voice Activity Detection) for auto-stop
      // Reuse AudioContext if available, create new if not
      if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
        console.log('[WS] 🎧 Creating new AudioContext for VAD');
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }

      const audioContext = audioContextRef.current;

      // FIXED: Disconnect old source first to prevent interference
      if (mediaStreamSourceRef.current) {
        console.log('[WS] 🔌 Disconnecting old MediaStreamSource');
        try {
          mediaStreamSourceRef.current.disconnect();
        } catch (e) {
          console.warn('[WS] ⚠️  Failed to disconnect old source:', e);
        }
      }

      // Create new MediaStreamSource and analyser for EACH recording
      // because we get a new stream each time
      console.log('[WS] 🎧 Creating new MediaStreamSource and analyser for this recording');
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);

      // Store refs for cleanup
      mediaStreamSourceRef.current = source;
      analyserRef.current = analyser;

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      let silenceStart: number | null = null;
      const SILENCE_THRESHOLD = 5; // Lower threshold for sensitive detection (0-100 RMS scale)
      const SILENCE_DURATION = 1500; // 1.5 seconds of silence triggers auto-stop

      // Monitor audio levels for VAD
      const checkAudioLevel = () => {
        if (!mediaRecorderRef.current || mediaRecorderRef.current.state !== 'recording') {
          console.log('[WS] 🛑 VAD monitoring stopped - recording ended');
          vadMonitoringRef.current = false; // Reset flag so next recording can start VAD
          return; // Stop monitoring if recording stopped
        }

        analyser.getByteTimeDomainData(dataArray);

        // Calculate RMS energy
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          const normalized = (dataArray[i] - 128) / 128;
          sum += normalized * normalized;
        }
        const rms = Math.sqrt(sum / bufferLength) * 100;

        console.log(`[WS] 📊 Audio level: ${rms.toFixed(1)}`);

        if (rms < SILENCE_THRESHOLD) {
          // Silence detected
          if (silenceStart === null) {
            silenceStart = Date.now();
            console.log('[WS] 🔇 Silence detected, starting timer...');
          } else {
            const silenceDuration = Date.now() - silenceStart;
            if (silenceDuration >= SILENCE_DURATION) {
              console.log(`[WS] ⏱️  ${silenceDuration}ms of silence detected, auto-stopping...`);
              stopRecordingInternal();
              return; // Stop checking
            }
          }
        } else {
          // Speech detected
          if (silenceStart !== null) {
            console.log('[WS] 🗣️  Speech resumed, resetting silence timer');
          }
          silenceStart = null;
        }

        // Check again in 500ms
        setTimeout(checkAudioLevel, 500);
      };

      // Start monitoring after 1 second (ignore initial noise)
      // Only start if not already monitoring
      if (!vadMonitoringRef.current) {
        vadMonitoringRef.current = true;
        setTimeout(() => {
          console.log('[WS] 🎧 Starting VAD monitoring...');
          checkAudioLevel();
        }, 1000);
      } else {
        console.log('[WS] ⏭️  VAD already monitoring, not starting new loop');
      }

      // Start recording with 1000ms chunks for better audio quality and processing
      console.log('[WS] ▶️  Starting MediaRecorder with 1000ms chunks');
      mediaRecorder.start(1000);
      updateIsRecording(true);
      onStatusChange?.('Recording...');
      console.log('[WS] ✅ Recording started successfully with frontend VAD');

    } catch (error) {
      console.error('[WS] ❌ Error starting recording:', error);
      if (error instanceof DOMException) {
        console.error('[WS] 📝 Error name:', error.name);
        console.error('[WS] 📝 Error message:', error.message);
      }
      onError?.('Microphone access denied');
    }
  };

  // Stop recording (internal function)
  const stopRecordingInternal = () => {
    console.log('[WS] 🛑 Stopping recording...');
    console.log('[WS] 📊 MediaRecorder state:', mediaRecorderRef.current?.state);
    console.log('[WS] 📊 isRecording state:', isRecordingRef.current);

    if (mediaRecorderRef.current) {
      // Force stop regardless of state
      if (mediaRecorderRef.current.state === 'recording') {
        console.log('[WS] 🔴 Stopping MediaRecorder...');
        mediaRecorderRef.current.stop();
      } else {
        console.warn('[WS] ⚠️  MediaRecorder not in recording state:', mediaRecorderRef.current.state);
      }
      updateIsRecording(false);
      onStatusChange?.('Processing...');
      console.log('[WS] ✅ Recording stop requested');
    } else {
      console.error('[WS] ❌ No MediaRecorder reference found!');
    }
  };

  // Play audio from base64 using voice-api service
  const playAudio = async (base64Audio: string) => {
    try {
      // Skip empty audio chunks
      if (!base64Audio) {
        console.log('[WS] ⏭️  Skipping empty audio chunk');
        return;
      }

      console.log(`[WS] 🔊 Playing audio (${base64Audio.length} base64 chars)...`);
      updateIsSpeaking(true);

      // Convert base64 to blob
      const byteCharacters = atob(base64Audio);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);

      // Detect audio format from file signature
      let mimeType = 'audio/wav';
      if (byteArray[0] === 0x4f && byteArray[1] === 0x67 && byteArray[2] === 0x67 && byteArray[3] === 0x53) {
        mimeType = 'audio/ogg; codecs=opus';
      }

      const blob = new Blob([byteArray], { type: mimeType });
      const url = URL.createObjectURL(blob);

      // Create audio element
      const audio = new Audio(url);
      currentAudioRef.current = audio;

      // Set up event listeners
      return new Promise<void>((resolve, reject) => {
        audio.onended = () => {
          console.log('[WS] ✅ Audio playback completed');
          URL.revokeObjectURL(url);
          currentAudioRef.current = null;
          updateIsSpeaking(false);
          resolve();
        };

        audio.onerror = (error) => {
          console.error('[WS] ❌ Audio playback error:', error);
          URL.revokeObjectURL(url);
          currentAudioRef.current = null;
          updateIsSpeaking(false);
          onError?.('Failed to play audio');
          reject(error);
        };

        audio.play().catch((playError) => {
          console.error('[WS] ❌ Play() failed:', playError);
          URL.revokeObjectURL(url);
          currentAudioRef.current = null;
          updateIsSpeaking(false);
          reject(playError);
        });
      });
    } catch (error) {
      console.error('[WS] ❌ Error in playAudio:', error);
      updateIsSpeaking(false);
      onError?.('Failed to play audio');
      throw error;
    }
  };

  // Stop speaking (barge-in)
  const stopSpeaking = () => {
    console.log('[WS] 🛑 Stopping audio playback (barge-in)');
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
    }
    updateIsSpeaking(false);
    // Send barge-in signal to backend
    sendMessage('barge_in', null);
  };

  // Public API wrappers
  const startRecording = () => {
    return startRecordingInternal();
  };

  const stopRecording = () => {
    return stopRecordingInternal();
  };

  // Update configuration
  const updateConfig = (config: any) => {
    sendMessage('config', config);
  };

  // Disconnect WebSocket
  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  };

  // Connect on mount
  useEffect(() => {
    // Only connect if assistantId is provided
    if (!assistantId) {
      console.log('[WS] ⏸️  No assistantId provided, skipping connection');
      return;
    }

    // Auto-connect on mount
    console.log('[WS] 🔄 Hook initialized with assistantId:', assistantId, '- auto-connecting...');
    connect();

    // Cleanup on unmount
    return () => {
      console.log('[WS] 🧹 Hook unmounting, disconnecting...');
      disconnect();
    };
    // Only reconnect if assistantId changes, not when connect function changes
  }, [assistantId]);

  return {
    isConnected,
    isRecording,
    isSpeaking,
    connect,
    disconnect,
    sendTextMessage,
    startRecording,
    stopRecording,
    stopSpeaking,
    playAudio,
    updateConfig
  };
};