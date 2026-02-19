/**
 * WebSocket Voice Chat Hook for InkWave
 *
 * Provides real-time voice interaction with books using:
 * - WebSocket connection for bidirectional communication
 * - PCM audio streaming with 16kHz resampling
 * - AudioQueue for smooth TTS playback
 * - Barge-in support for interrupting responses
 *
 * Author: AI Labs Africa
 * Created: November 30, 2025
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { getAuthToken } from '@/lib/auth-utils';
import { playAudioBase64, AudioQueue } from '@/lib/audio-utils';
import { getAudioProcessor } from '@/services/audio-processor';
import { INKWAVE_WS_URL } from '@/config/api-config';

interface WebSocketMessage {
  type: string;
  data: any;
}

interface VoiceSettings {
  provider_id?: string;
  voice_id?: string;
  speed?: number;
  language?: string;
}

interface ASRSettings {
  provider?: string;
  model?: string;
  language?: string;
}

interface LLMSettings {
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

interface ConversationStateInfo {
  conversation_state: string;
  vad_state: string;
  hands_free_mode: boolean;
  can_record: boolean;
  time_in_current_state?: number;
  old_state?: string;
  new_state?: string;
}

interface UseWebSocketVoiceChatOptions {
  bookId: string;
  voiceSettings?: VoiceSettings;
  asrSettings?: ASRSettings;
  llmSettings?: LLMSettings;
  handsFree?: boolean;  // Enable hands-free mode (auto-resume listening)
  onTranscription?: (text: string, isFinal: boolean) => void;
  onTextResponse?: (text: string) => void;
  onAudioChunk?: (audioData: string) => void;
  onAudioComplete?: (metadata: any) => void;
  onError?: (error: string) => void;
  onStatusChange?: (status: string) => void;
  onConversationStateChange?: (state: ConversationStateInfo) => void;
  onVADEvent?: (event: 'speech_start' | 'utterance_complete', data?: any) => void;
}

export const useWebSocketVoiceChat = ({
  bookId,
  voiceSettings,
  asrSettings,
  llmSettings,
  handsFree = true,  // Default to hands-free mode
  onTranscription,
  onTextResponse,
  onAudioChunk,
  onAudioComplete,
  onError,
  onStatusChange,
  onConversationStateChange,
  onVADEvent
}: UseWebSocketVoiceChatOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [response, setResponse] = useState('');
  const [conversationState, setConversationState] = useState<ConversationStateInfo | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  // PCM streaming refs
  const stopStreamingRef = useRef<(() => void) | null>(null);

  // Audio queue for streaming TTS chunks
  const audioQueueRef = useRef<AudioQueue | null>(null);

  // Use refs to track latest state for use in callbacks (avoid stale closures)
  const isRecordingRef = useRef(false);
  const isSpeakingRef = useRef(false);

  // Store callbacks in refs to avoid dependency changes triggering reconnects
  const callbacksRef = useRef({
    onTranscription,
    onTextResponse,
    onAudioChunk,
    onAudioComplete,
    onError,
    onStatusChange,
    onConversationStateChange,
    onVADEvent
  });

  // Update callback refs when props change
  useEffect(() => {
    callbacksRef.current = {
      onTranscription,
      onTextResponse,
      onAudioChunk,
      onAudioComplete,
      onError,
      onStatusChange,
      onConversationStateChange,
      onVADEvent
    };
  }, [onTranscription, onTextResponse, onAudioChunk, onAudioComplete, onError, onStatusChange, onConversationStateChange, onVADEvent]);

  // Store settings in refs to avoid dependency changes
  const settingsRef = useRef({
    voiceSettings,
    asrSettings,
    llmSettings,
    handsFree
  });

  // Update settings refs when props change
  useEffect(() => {
    settingsRef.current = {
      voiceSettings,
      asrSettings,
      llmSettings,
      handsFree
    };
  }, [voiceSettings, asrSettings, llmSettings, handsFree]);

  // Wrapper to update both state and ref
  const updateIsRecording = useCallback((value: boolean) => {
    isRecordingRef.current = value;
    setIsRecording(value);
  }, []);

  const updateIsSpeaking = useCallback((value: boolean) => {
    isSpeakingRef.current = value;
    setIsSpeaking(value);
  }, []);

  // Microphone mute/unmute callbacks for echo prevention
  // These are called by AudioQueue when TTS starts/stops
  const handleTTSPlaybackStart = useCallback(() => {
    console.log('[WS-Voice] TTS playback starting - muting microphone to prevent echo');
    const audioProcessor = getAudioProcessor();
    audioProcessor.muteMicrophone();
  }, []);

  const handleTTSPlaybackEnd = useCallback(() => {
    console.log('[WS-Voice] TTS playback ended - unmuting microphone');
    const audioProcessor = getAudioProcessor();
    audioProcessor.unmuteMicrophone();
  }, []);

  // Initialize AudioQueue with mic mute callbacks on first render
  if (!audioQueueRef.current) {
    audioQueueRef.current = new AudioQueue(
      updateIsSpeaking,
      onError,
      handleTTSPlaybackStart,  // Called when TTS starts - mutes mic
      handleTTSPlaybackEnd     // Called when TTS ends - unmutes mic
    );
    console.log('[WS-Voice] AudioQueue initialized with mic muting for echo prevention');
  } else {
    // Update callbacks if they change (shouldn't happen, but be safe)
    audioQueueRef.current.setCallbacks(handleTTSPlaybackStart, handleTTSPlaybackEnd);
  }

  // WebSocket URL with authentication
  const getWebSocketUrl = useCallback(async () => {
    const baseUrl = INKWAVE_WS_URL;

    if (!bookId || bookId.trim() === '') {
      const errorMsg = `[WS-Voice] CRITICAL ERROR: bookId is empty! Value: "${bookId}"`;
      console.error(errorMsg);
      callbacksRef.current.onError?.('Book ID is required but was not provided');
      throw new Error('Book ID is required for WebSocket connection');
    }

    try {
      console.log(`[WS-Voice] Getting auth token for book ${bookId}...`);
      const token = await getAuthToken();
      const url = `${baseUrl}/ws/voice-chat/${bookId}?token=${token.substring(0, 20)}...`;
      console.log(`[WS-Voice] WebSocket URL: ${url}`);
      return `${baseUrl}/ws/voice-chat/${bookId}?token=${token}`;
    } catch (error) {
      console.error('[WS-Voice] Failed to get auth token:', error);
      // Fallback without token (will likely fail but provides clearer error)
      return `${baseUrl}/ws/voice-chat/${bookId}`;
    }
  }, [bookId]);  // Only depends on bookId - uses ref for callbacks

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    console.log(`[WS-Voice] Handling message type: ${message.type}`);
    const callbacks = callbacksRef.current;

    switch (message.type) {
      case 'status':
        console.log('[WS-Voice] Status update:', message.data);
        callbacks.onStatusChange?.(message.data);
        break;

      case 'transcription':
        let transcriptionText = '';
        let isFinal = false;

        if (typeof message.data === 'string') {
          transcriptionText = message.data;
          isFinal = true;
        } else if (message.data && typeof message.data === 'object') {
          transcriptionText = message.data.text || '';
          isFinal = message.data.is_final ?? false;
        }

        console.log(`[WS-Voice] Transcription: "${transcriptionText}" (final: ${isFinal})`);
        setTranscription(transcriptionText);
        callbacks.onTranscription?.(transcriptionText, isFinal);
        break;

      case 'text_response':
        console.log('[WS-Voice] Text response:', message.data?.substring(0, 100) + '...');
        setResponse(message.data);
        callbacks.onTextResponse?.(message.data);
        break;

      case 'audio_chunk':
        const chunkSize = message.data?.length || 0;
        console.log(`[WS-Voice] Audio chunk received (${chunkSize} bytes)`);
        callbacks.onAudioChunk?.(message.data);
        // Use AudioQueue for smooth streaming playback
        audioQueueRef.current?.enqueue(message.data);
        break;

      case 'audio_complete':
        console.log('[WS-Voice] Audio stream complete:', message.data);
        if (message.data?.chunks) {
          console.log(`[WS-Voice] Streaming stats: ${message.data.chunks} chunks`);
        }
        callbacks.onAudioComplete?.(message.data);
        break;

      case 'ready_to_listen':
        console.log('[WS-Voice] Ready to listen');
        callbacks.onStatusChange?.(message.data || 'Ready to listen');
        break;

      case 'start_recording':
        console.log('[WS-Voice] Server requested start recording (hands-free mode)');
        if (!isRecordingRef.current) {
          const waitForAudioComplete = () => {
            if (isSpeakingRef.current || currentAudioRef.current) {
              console.log('[WS-Voice] Waiting for audio to finish...');
              setTimeout(waitForAudioComplete, 200);
            } else {
              console.log('[WS-Voice] Audio finished, auto-starting recording');
              startRecordingInternal();
            }
          };
          setTimeout(waitForAudioComplete, 100);
          callbacks.onStatusChange?.('Listening...');
        }
        break;

      case 'stop_recording':
        console.log('[WS-Voice] Server requested stop recording');
        stopRecordingInternal();
        callbacks.onStatusChange?.(message.data || 'Processing...');
        break;

      // VoiceAgent-style messages
      case 'conversation_state':
        console.log('[WS-Voice] Conversation state update:', message.data);
        setConversationState(message.data);
        callbacks.onConversationStateChange?.(message.data);
        break;

      case 'vad_speech_start':
        console.log('[WS-Voice] VAD: Speech detected');
        callbacks.onVADEvent?.('speech_start', message.data);
        callbacks.onStatusChange?.('Speech detected...');
        break;

      case 'vad_utterance_complete':
        console.log('[WS-Voice] VAD: Utterance complete');
        callbacks.onVADEvent?.('utterance_complete', message.data);
        stopRecordingInternal();
        callbacks.onStatusChange?.(message.data || 'Processing...');
        break;

      case 'interrupted':
        console.log('[WS-Voice] Interrupted:', message.data);
        callbacks.onStatusChange?.('Interrupted');
        break;

      case 'barge_in_ack':
        console.log('[WS-Voice] Barge-in acknowledged');
        callbacks.onStatusChange?.('Stopped speaking');
        break;

      case 'stop_audio':
        // Backend requests immediate audio stop (e.g., barge-in detected)
        console.log('[WS-Voice] Server requested stop_audio - clearing audio queue');
        if (audioQueueRef.current) {
          audioQueueRef.current.clear();
        }
        if (currentAudioRef.current) {
          currentAudioRef.current.pause();
          currentAudioRef.current = null;
        }
        updateIsSpeaking(false);
        callbacks.onStatusChange?.('Listening...');
        break;

      case 'pong':
        console.log('[WS-Voice] Pong received');
        break;

      case 'error':
        console.error('[WS-Voice] Server error:', message.data);
        callbacks.onError?.(message.data);
        break;

      default:
        console.warn('[WS-Voice] Unknown message type:', message.type);
    }
  }, []);  // No dependencies - uses refs

  // Connect to WebSocket
  const connect = useCallback(async () => {
    console.log('[WS-Voice] Initiating WebSocket connection...');

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WS-Voice] Already connected');
      return;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }

    try {
      const wsUrl = await getWebSocketUrl();
      console.log('[WS-Voice] Creating WebSocket connection...');
      const ws = new WebSocket(wsUrl);

      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS-Voice] WebSocket connected');
        setIsConnected(true);
        callbacksRef.current.onStatusChange?.('Connected');

        // Get current settings from ref
        const settings = settingsRef.current;

        // Send initialization message with settings
        console.log('[WS-Voice] Sending init message with hands_free:', settings.handsFree);
        ws.send(JSON.stringify({
          type: 'init',
          data: {
            voice_settings: settings.voiceSettings || {
              provider_id: 'kokoro',
              voice_id: 'am_adam',
              speed: 1.0,
              language: 'en'
            },
            asr_settings: settings.asrSettings || {
              provider: 'faster_whisper',
              model: 'medium',
              language: 'en'
            },
            llm_settings: settings.llmSettings || {
              model: 'gemini-2.5-flash',
              temperature: 0.7
            },
            hands_free: settings.handsFree  // Enable server-side hands-free mode
          }
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (err) {
          console.error('[WS-Voice] Error parsing message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS-Voice] WebSocket error:', error);
        callbacksRef.current.onError?.('Connection error');
      };

      ws.onclose = (event) => {
        console.log('[WS-Voice] WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;
        callbacksRef.current.onStatusChange?.('Disconnected');

        // Reconnect on abnormal closure (but NOT immediately - use exponential backoff)
        if (!event.wasClean && event.code !== 1000) {
          console.log('[WS-Voice] Abnormal closure, reconnecting in 3s...');
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        }
      };
    } catch (error) {
      console.error('[WS-Voice] Failed to create WebSocket:', error);
      wsRef.current = null;
      callbacksRef.current.onError?.('Failed to connect');
    }
  }, [getWebSocketUrl, handleWebSocketMessage]);  // Minimal dependencies - uses refs for settings/callbacks

  // Send message through WebSocket
  const sendMessage = useCallback((type: string, data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log(`[WS-Voice] Sending: ${type}`);
      wsRef.current.send(JSON.stringify({ type, data }));
    } else {
      console.error('[WS-Voice] Cannot send - not connected');
      onError?.('Not connected');
    }
  }, [onError]);

  // Send text message
  const sendTextMessage = useCallback((text: string) => {
    console.log(`[WS-Voice] Sending text: "${text}"`);
    sendMessage('text', text);
  }, [sendMessage]);

  // Start recording with PCM streaming
  const startRecordingInternal = useCallback(async () => {
    console.log('[WS-Voice] Starting PCM streaming...');

    try {
      const audioProcessor = getAudioProcessor();

      const stopStreaming = await audioProcessor.startPCMStreaming(
        (pcmData: Float32Array, sampleRate: number) => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            // Convert Float32Array to base64
            const buffer = pcmData.buffer;
            const base64 = btoa(
              String.fromCharCode(...new Uint8Array(buffer))
            );

            wsRef.current.send(JSON.stringify({
              type: 'pcm_chunk',
              data: base64,
              sample_rate: sampleRate
            }));

            console.log(`[WS-Voice] PCM chunk sent: ${pcmData.length} samples @ ${sampleRate}Hz`);
          }
        },
        500  // Chunk interval
      );

      stopStreamingRef.current = stopStreaming;
      updateIsRecording(true);
      onStatusChange?.('Recording...');

      console.log('[WS-Voice] PCM streaming started');
    } catch (error) {
      console.error('[WS-Voice] Error starting PCM streaming:', error);
      onError?.('Microphone access denied');
    }
  }, [updateIsRecording, onStatusChange, onError]);

  // Stop recording PCM streaming
  const stopRecordingInternal = useCallback(() => {
    console.log('[WS-Voice] Stopping PCM streaming...');

    if (stopStreamingRef.current) {
      stopStreamingRef.current();
      stopStreamingRef.current = null;

      // Notify server that recording stopped
      sendMessage('stop_recording', null);

      console.log('[WS-Voice] PCM streaming stopped');
    }

    updateIsRecording(false);
    onStatusChange?.('Processing...');
  }, [updateIsRecording, sendMessage, onStatusChange]);

  // Public API - start recording
  const startRecording = useCallback(() => {
    console.log('[WS-Voice] User started recording');
    startRecordingInternal();
  }, [startRecordingInternal]);

  // Public API - stop recording
  const stopRecording = useCallback(() => {
    console.log('[WS-Voice] User stopped recording');
    stopRecordingInternal();
  }, [stopRecordingInternal]);

  // Public API - stop audio playback (barge-in)
  const stopAudio = useCallback(() => {
    console.log('[WS-Voice] Barge-in requested');

    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }

    // Clear AudioQueue
    if (audioQueueRef.current) {
      audioQueueRef.current.clear();
      console.log('[WS-Voice] AudioQueue cleared');
    }

    updateIsSpeaking(false);
    sendMessage('barge_in', 'User interrupted');
  }, [updateIsSpeaking, sendMessage]);

  // Cleanup on unmount only
  useEffect(() => {
    // Don't auto-connect - let component call connect() explicitly
    // This prevents reconnect loops from dependency changes

    return () => {
      console.log('[WS-Voice] Cleaning up on unmount...');

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      if (stopStreamingRef.current) {
        stopStreamingRef.current();
      }

      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }
    };
  }, []);  // Only run once on mount/unmount

  return {
    // State
    isConnected,
    isRecording,
    isSpeaking,
    transcription,
    response,
    conversationState,  // VoiceAgent conversation state

    // Actions
    startRecording,
    stopRecording,
    stopAudio,
    stopSpeaking: stopAudio,  // Alias
    sendTextMessage,
    connect,
    disconnect: () => {
      console.log('[WS-Voice] Manual disconnect');
      if (wsRef.current) {
        wsRef.current.close(1000, 'User disconnected');
        wsRef.current = null;
      }
      setIsConnected(false);
    },

    // Clear state
    clearTranscription: () => setTranscription(''),
    clearResponse: () => setResponse('')
  };
};
