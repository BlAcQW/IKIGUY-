/**
 * VoiceAgent Hook for StudyFlow
 *
 * Provides real-time voice interaction for tutoring using:
 * - WebSocket connection for bidirectional communication
 * - PCM audio streaming with 16kHz resampling
 * - AudioQueue for smooth TTS playback
 * - Server-side VAD for hands-free operation
 * - Barge-in support for interrupting responses
 *
 * Author: AI Labs Africa
 * Created: November 30, 2025
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { getAuthToken } from '@/lib/auth-utils';
import { playAudioBase64, AudioQueue } from '@/lib/audio-utils';
import { getAudioProcessor } from '@/services/audio-processor';
import { STUDYFLOW_WS_URL } from '@/config/api-config';

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

interface UseVoiceAgentOptions {
  sessionId: string;  // Study session ID for tutoring context
  materialId?: string;  // Optional material ID for RAG context
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

export const useVoiceAgent = ({
  sessionId,
  materialId,
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
}: UseVoiceAgentOptions) => {
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

  // Store callbacks in refs to avoid recreating connect on every render
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

  // Update callback refs on each render
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

  // Track if we've initiated connection for current sessionId
  const connectionInitiatedRef = useRef<string | null>(null);

  // Wrapper to update both state and ref
  const updateIsRecording = useCallback((value: boolean) => {
    isRecordingRef.current = value;
    setIsRecording(value);
  }, []);

  const updateIsSpeaking = useCallback((value: boolean) => {
    isSpeakingRef.current = value;
    setIsSpeaking(value);
  }, []);

  // Initialize AudioQueue on first render
  if (!audioQueueRef.current) {
    audioQueueRef.current = new AudioQueue(updateIsSpeaking, onError);
    console.log('[VoiceAgent] AudioQueue initialized for streaming TTS');
  }

  // WebSocket URL with authentication (stable - no callback dependencies)
  const getWebSocketUrl = useCallback(async (sid: string, matId?: string) => {
    const baseUrl = STUDYFLOW_WS_URL;

    if (!sid || sid.trim() === '') {
      const errorMsg = `[VoiceAgent] CRITICAL ERROR: sessionId is empty! Value: "${sid}"`;
      console.error(errorMsg);
      callbacksRef.current.onError?.('Session ID is required but was not provided');
      throw new Error('Session ID is required for WebSocket connection');
    }

    try {
      console.log(`[VoiceAgent] Getting auth token for session ${sid}...`);
      const token = await getAuthToken();
      let url = `${baseUrl}/api/v1/voice-agent/ws/${sid}?token=${token}`;

      // Add material ID if provided
      if (matId) {
        url += `&material_id=${matId}`;
      }

      console.log(`[VoiceAgent] WebSocket URL: ${url.substring(0, 80)}...`);
      return url;
    } catch (error) {
      console.error('[VoiceAgent] Failed to get auth token:', error);
      // Fallback without token (will likely fail but provides clearer error)
      let url = `${baseUrl}/api/v1/voice-agent/ws/${sid}`;
      if (matId) {
        url += `?material_id=${matId}`;
      }
      return url;
    }
  }, []);

  // Handle incoming WebSocket messages (uses callback refs for stability)
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    console.log(`[VoiceAgent] Handling message type: ${message.type}`);
    const cbs = callbacksRef.current;

    switch (message.type) {
      case 'status':
        console.log('[VoiceAgent] Status update:', message.data);
        cbs.onStatusChange?.(message.data);
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

        console.log(`[VoiceAgent] Transcription: "${transcriptionText}" (final: ${isFinal})`);
        setTranscription(transcriptionText);
        cbs.onTranscription?.(transcriptionText, isFinal);
        break;

      case 'text_response':
        console.log('[VoiceAgent] Text response:', message.data?.substring(0, 100) + '...');
        setResponse(message.data);
        cbs.onTextResponse?.(message.data);
        break;

      case 'audio_chunk':
        const chunkSize = message.data?.length || 0;
        console.log(`[VoiceAgent] Audio chunk received (${chunkSize} bytes)`);
        cbs.onAudioChunk?.(message.data);
        // Use AudioQueue for smooth streaming playback
        audioQueueRef.current?.enqueue(message.data);
        break;

      case 'audio_complete':
        console.log('[VoiceAgent] Audio stream complete:', message.data);
        if (message.data?.chunks) {
          console.log(`[VoiceAgent] Streaming stats: ${message.data.chunks} chunks`);
        }
        cbs.onAudioComplete?.(message.data);
        break;

      case 'ready_to_listen':
        console.log('[VoiceAgent] Ready to listen');
        cbs.onStatusChange?.(message.data || 'Ready to listen');
        break;

      case 'start_recording':
        console.log('[VoiceAgent] Server requested start recording (hands-free mode)');
        if (!isRecordingRef.current) {
          const waitForAudioComplete = () => {
            if (isSpeakingRef.current || currentAudioRef.current) {
              console.log('[VoiceAgent] Waiting for audio to finish...');
              setTimeout(waitForAudioComplete, 200);
            } else {
              console.log('[VoiceAgent] Audio finished, auto-starting recording');
              startRecordingInternal();
            }
          };
          setTimeout(waitForAudioComplete, 100);
          cbs.onStatusChange?.('Listening...');
        }
        break;

      case 'stop_recording':
        console.log('[VoiceAgent] Server requested stop recording');
        stopRecordingInternal();
        cbs.onStatusChange?.(message.data || 'Processing...');
        break;

      // VoiceAgent-style messages
      case 'conversation_state':
        console.log('[VoiceAgent] Conversation state update:', message.data);
        setConversationState(message.data);
        cbs.onConversationStateChange?.(message.data);
        break;

      case 'vad_speech_start':
        console.log('[VoiceAgent] VAD: Speech detected');
        cbs.onVADEvent?.('speech_start', message.data);
        cbs.onStatusChange?.('Speech detected...');
        break;

      case 'vad_utterance_complete':
        console.log('[VoiceAgent] VAD: Utterance complete');
        cbs.onVADEvent?.('utterance_complete', message.data);
        stopRecordingInternal();
        cbs.onStatusChange?.(message.data || 'Processing...');
        break;

      case 'interrupted':
        console.log('[VoiceAgent] Interrupted:', message.data);
        cbs.onStatusChange?.('Interrupted');
        break;

      case 'barge_in_ack':
        console.log('[VoiceAgent] Barge-in acknowledged');
        cbs.onStatusChange?.('Stopped speaking');
        break;

      case 'pong':
        console.log('[VoiceAgent] Pong received');
        break;

      case 'error':
        console.error('[VoiceAgent] Server error:', message.data);
        cbs.onError?.(message.data);
        break;

      default:
        console.warn('[VoiceAgent] Unknown message type:', message.type);
    }
  }, []);

  // Connect to WebSocket (stable - uses refs for callbacks)
  const connectWithParams = useCallback(async (
    sid: string,
    matId: string | undefined,
    vSettings: VoiceSettings | undefined,
    aSettings: ASRSettings | undefined,
    lSettings: LLMSettings | undefined,
    hfMode: boolean
  ) => {
    console.log('[VoiceAgent] Initiating WebSocket connection...');

    // Prevent duplicate connections
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[VoiceAgent] Already connected');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      console.log('[VoiceAgent] Connection in progress, skipping...');
      return;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }

    try {
      const wsUrl = await getWebSocketUrl(sid, matId);
      console.log('[VoiceAgent] Creating WebSocket connection...');
      const ws = new WebSocket(wsUrl);

      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[VoiceAgent] WebSocket connected');
        setIsConnected(true);
        callbacksRef.current.onStatusChange?.('Connected');

        // Send initialization message with settings
        console.log('[VoiceAgent] Sending init message with hands_free:', hfMode);
        ws.send(JSON.stringify({
          type: 'init',
          data: {
            voice_settings: vSettings || {
              provider_id: 'kokoro',
              voice_id: 'am_adam',
              speed: 1.0,
              language: 'en'
            },
            asr_settings: aSettings || {
              provider: 'faster_whisper',
              model: 'medium',
              language: 'en'
            },
            llm_settings: lSettings || {
              model: 'gemini-2.5-flash',
              temperature: 0.7
            },
            hands_free: hfMode,  // Enable server-side hands-free mode
            material_id: matId  // Pass material ID for RAG context
          }
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (err) {
          console.error('[VoiceAgent] Error parsing message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[VoiceAgent] WebSocket error:', error);
        callbacksRef.current.onError?.('Connection error');
      };

      ws.onclose = (event) => {
        console.log('[VoiceAgent] WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;
        callbacksRef.current.onStatusChange?.('Disconnected');

        // Reconnect on abnormal closure (only if still same session)
        if (!event.wasClean && event.code !== 1000 && connectionInitiatedRef.current === sid) {
          console.log('[VoiceAgent] Abnormal closure, reconnecting in 3s...');
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWithParams(sid, matId, vSettings, aSettings, lSettings, hfMode);
          }, 3000);
        }
      };
    } catch (error) {
      console.error('[VoiceAgent] Failed to create WebSocket:', error);
      wsRef.current = null;
      callbacksRef.current.onError?.('Failed to connect');
    }
  }, [getWebSocketUrl, handleWebSocketMessage]);

  // Public connect function that uses current props
  const connect = useCallback(() => {
    connectWithParams(sessionId, materialId, voiceSettings, asrSettings, llmSettings, handsFree);
  }, [connectWithParams, sessionId, materialId, voiceSettings, asrSettings, llmSettings, handsFree]);

  // Send message through WebSocket (uses callback refs for stability)
  const sendMessage = useCallback((type: string, data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log(`[VoiceAgent] Sending: ${type}`);
      wsRef.current.send(JSON.stringify({ type, data }));
    } else {
      console.error('[VoiceAgent] Cannot send - not connected');
      callbacksRef.current.onError?.('Not connected');
    }
  }, []);

  // Send text message
  const sendTextMessage = useCallback((text: string) => {
    console.log(`[VoiceAgent] Sending text: "${text}"`);
    sendMessage('text', text);
  }, [sendMessage]);

  // Start recording with PCM streaming (uses callback refs for stability)
  const startRecordingInternal = useCallback(async () => {
    console.log('[VoiceAgent] Starting PCM streaming...');

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

            console.log(`[VoiceAgent] PCM chunk sent: ${pcmData.length} samples @ ${sampleRate}Hz`);
          }
        },
        500  // Chunk interval
      );

      stopStreamingRef.current = stopStreaming;
      updateIsRecording(true);
      callbacksRef.current.onStatusChange?.('Recording...');

      console.log('[VoiceAgent] PCM streaming started');
    } catch (error) {
      console.error('[VoiceAgent] Error starting PCM streaming:', error);
      callbacksRef.current.onError?.('Microphone access denied');
    }
  }, [updateIsRecording]);

  // Stop recording PCM streaming (uses callback refs for stability)
  const stopRecordingInternal = useCallback(() => {
    console.log('[VoiceAgent] Stopping PCM streaming...');

    if (stopStreamingRef.current) {
      stopStreamingRef.current();
      stopStreamingRef.current = null;

      // Notify server that recording stopped
      sendMessage('stop_recording', null);

      console.log('[VoiceAgent] PCM streaming stopped');
    }

    updateIsRecording(false);
    callbacksRef.current.onStatusChange?.('Processing...');
  }, [updateIsRecording, sendMessage]);

  // Public API - start recording
  const startRecording = useCallback(() => {
    console.log('[VoiceAgent] User started recording');
    startRecordingInternal();
  }, [startRecordingInternal]);

  // Public API - stop recording
  const stopRecording = useCallback(() => {
    console.log('[VoiceAgent] User stopped recording');
    stopRecordingInternal();
  }, [stopRecordingInternal]);

  // Public API - stop audio playback (barge-in)
  const stopAudio = useCallback(() => {
    console.log('[VoiceAgent] Barge-in requested');

    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }

    // Clear AudioQueue
    if (audioQueueRef.current) {
      audioQueueRef.current.clear();
      console.log('[VoiceAgent] AudioQueue cleared');
    }

    updateIsSpeaking(false);
    sendMessage('barge_in', 'User interrupted');
  }, [updateIsSpeaking, sendMessage]);

  // Connect when sessionId is available (only once per sessionId)
  useEffect(() => {
    if (!sessionId || sessionId.trim() === '') {
      console.log('[VoiceAgent] Waiting for valid session ID...');
      return;
    }

    // Only connect if we haven't connected for this sessionId yet
    if (connectionInitiatedRef.current === sessionId) {
      console.log('[VoiceAgent] Already initiated connection for this session, skipping...');
      return;
    }

    console.log('[VoiceAgent] Valid session ID, connecting...', sessionId);
    connectionInitiatedRef.current = sessionId;

    // Connect with current settings (captured at this moment)
    connectWithParams(sessionId, materialId, voiceSettings, asrSettings, llmSettings, handsFree);

    // Cleanup on unmount or sessionId change
    return () => {
      console.log('[VoiceAgent] Cleaning up...');

      // Clear connection tracking for this session
      if (connectionInitiatedRef.current === sessionId) {
        connectionInitiatedRef.current = null;
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = undefined;
      }

      if (stopStreamingRef.current) {
        stopStreamingRef.current();
        stopStreamingRef.current = null;
      }

      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }
    };
  }, [sessionId]);  // Only re-run when sessionId changes, not on every render

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
      console.log('[VoiceAgent] Manual disconnect');
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

export default useVoiceAgent;
