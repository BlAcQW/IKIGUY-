import { useState, useRef, useCallback, useEffect } from 'react';
import { getAuthToken } from '@/lib/auth-utils';
import { playAudioBase64 } from '@/lib/audio-utils';
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

/**
 * AudioQueue - Manages sequential playback of streaming audio chunks
 * Ensures smooth continuous playback without overlaps or gaps
 */
class AudioQueue {
  private queue: string[] = [];
  private isPlaying: boolean = false;
  private updateIsSpeaking: (value: boolean) => void;
  private onError?: (error: string) => void;

  constructor(updateIsSpeaking: (value: boolean) => void, onError?: (error: string) => void) {
    this.updateIsSpeaking = updateIsSpeaking;
    this.onError = onError;
  }

  /**
   * Enqueue an audio chunk for playback
   * If not currently playing, starts playback immediately
   */
  async enqueue(base64Audio: string): Promise<void> {
    // Skip empty audio chunks
    if (!base64Audio) {
      console.log('[AudioQueue] ⏭️  Skipping empty chunk');
      return;
    }

    this.queue.push(base64Audio);
    console.log(`[AudioQueue] 📥 Enqueued chunk (queue size: ${this.queue.length})`);

    // Start playback if not already playing
    if (!this.isPlaying) {
      await this.playNext();
    }
  }

  /**
   * Play the next chunk in the queue
   * Recursively calls itself until queue is empty
   */
  private async playNext(): Promise<void> {
    // Queue is empty - stop playback
    if (this.queue.length === 0) {
      console.log('[AudioQueue] ✅ Queue empty, playback complete');
      this.isPlaying = false;
      this.updateIsSpeaking(false);
      return;
    }

    // Mark as playing and update speaking state
    this.isPlaying = true;
    this.updateIsSpeaking(true);

    // Get next chunk
    const chunk = this.queue.shift()!;
    console.log(`[AudioQueue] 🔊 Playing chunk (${this.queue.length} remaining in queue)`);

    try {
      // Play the chunk
      await playAudioBase64(chunk);
      console.log('[AudioQueue] ✅ Chunk played successfully');

      // Play next chunk
      await this.playNext();
    } catch (error) {
      console.error('[AudioQueue] ❌ Error playing chunk:', error);
      this.onError?.('Audio playback failed');

      // Continue with next chunk despite error
      await this.playNext();
    }
  }

  /**
   * Clear the queue and stop playback
   * Used for barge-in/interruption
   */
  clear(): void {
    console.log(`[AudioQueue] 🗑️  Clearing queue (${this.queue.length} chunks discarded)`);
    this.queue = [];
    this.isPlaying = false;
    this.updateIsSpeaking(false);
  }

  /**
   * Get current queue size
   */
  size(): number {
    return this.queue.length;
  }
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
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  // PCM streaming refs
  const stopStreamingRef = useRef<(() => void) | null>(null);

  // Audio queue for streaming TTS chunks
  const audioQueueRef = useRef<AudioQueue | null>(null);

  // Use refs to track latest state for use in callbacks (avoid stale closures)
  const isRecordingRef = useRef(false);
  const isSpeakingRef = useRef(false);

  // Wrapper to update both state and ref
  const updateIsRecording = (value: boolean) => {
    isRecordingRef.current = value;
    setIsRecording(value);
  };

  const updateIsSpeaking = (value: boolean) => {
    isSpeakingRef.current = value;
    setIsSpeaking(value);
  };

  // Initialize AudioQueue on first render
  if (!audioQueueRef.current) {
    audioQueueRef.current = new AudioQueue(updateIsSpeaking, onError);
    console.log('[WS] 🎵 AudioQueue initialized for streaming TTS');
  }

  // WebSocket URL with authentication
  const getWebSocketUrl = async () => {
    const baseUrl = WS_BASE_URL;

    // ❌ CRITICAL VALIDATION: Ensure assistant ID is not empty
    if (!assistantId || assistantId.trim() === '') {
      const errorMsg = `[WS] ❌ CRITICAL ERROR: assistantId is empty! Value: "${assistantId}"`;
      console.error(errorMsg);
      console.trace('Stack trace for empty assistantId:');
      onError?.('Assistant ID is required but was not provided');
      throw new Error('Assistant ID is required for WebSocket connection');
    }

    try {
      console.log(`[WS] 🔑 Getting auth token for assistant ${assistantId}...`);
      const token = await getAuthToken();
      const url = `${baseUrl}/voice/ws/voice-chat/${assistantId}?token=${token.substring(0, 20)}...`;
      console.log(`[WS] ✅ Auth token obtained. Full WebSocket URL: ${url}`);
      return `${baseUrl}/voice/ws/voice-chat/${assistantId}?token=${token}`;
    } catch (error) {
      console.error('[WS] ❌ Failed to get auth token for WebSocket:', error);
      // Fallback without token (will likely fail but provides clearer error)
      return `${baseUrl}/voice/ws/voice-chat/${assistantId}`;
    }
  };

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    console.log(`[WS] 🎯 Handling message type: ${message.type}`);

    switch (message.type) {
      case 'status':
        console.log('[WS] 📊 Status update:', message.data);
        onStatusChange?.(message.data);
        break;

      case 'transcription':
        // Handle both string and object formats
        let transcriptionText = '';
        let isFinal = false;

        if (typeof message.data === 'string') {
          transcriptionText = message.data;
          isFinal = true;
        } else if (message.data && typeof message.data === 'object') {
          // Handle object format: {text, confidence, language, is_final}
          transcriptionText = message.data.text || '';
          isFinal = message.data.is_final ?? false;
        }

        console.log(`[WS] 🎤 Transcription: "${transcriptionText}" (final: ${isFinal})`);
        onTranscription?.(transcriptionText, isFinal);
        break;

      case 'text_response':
        console.log('[WS] 💬 Text response:', message.data.substring(0, 100) + (message.data.length > 100 ? '...' : ''));
        onTextResponse?.(message.data);
        break;

      case 'audio_chunk':
        const chunkSize = message.data?.length || 0;
        console.log(`[WS] 🔊 Audio chunk received (${chunkSize} bytes) - enqueueing for streaming playback`);
        onAudioChunk?.(message.data);
        // 🚀 NEW: Use AudioQueue for smooth streaming playback
        audioQueueRef.current?.enqueue(message.data);
        break;

      case 'audio_complete':
        console.log('[WS] ✅ Audio stream complete, metadata:', message.data);
        // Log streaming metrics if available
        if (message.data?.chunks) {
          console.log(`[WS] 📊 Streaming stats: ${message.data.chunks} chunks, first chunk: ${message.data.first_chunk_latency?.toFixed(3)}s`);
        }
        onAudioComplete?.(message.data);
        // Note: isSpeaking will be updated by AudioQueue when playback finishes
        break;

      // NEW: Server-side VAD events
      case 'vad_speech_start':
        console.log('[WS] 🗣️  Server VAD: Speech started');
        onStatusChange?.('Listening (speech detected)...');
        break;

      case 'vad_utterance_complete':
        console.log('[WS] ✅ Server VAD: Utterance complete, processing...');
        onStatusChange?.('Processing...');
        break;

      case 'vad_silence':
        console.log('[WS] 🔇 Server VAD: Silence detected');
        break;

      case 'ready_to_listen':
        console.log('[WS] 👂 Server: Ready to listen (hands-free)');
        onStatusChange?.(message.data || 'Listening...');
        break;

      case 'start_recording':
        console.log('[WS] 🎤 Server requested start recording (hands-free):', message.data);
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
        }
        break;

      case 'stop_recording':
        console.log('[WS] 🛑 Server requested stop recording:', message.data);
        stopRecordingInternal();
        onStatusChange?.(message.data || 'Processing...');
        break;

      case 'conversation_state':
        console.log('[WS] 📝 Conversation state update:', message.data);
        // Update status based on conversation state
        if (message.data?.state) {
          onStatusChange?.(message.data.state);
        }
        break;

      case 'error':
        console.error('[WS] ❌ Server error:', message.data);
        onError?.(message.data);
        break;

      default:
        console.warn('[WS] ⚠️  Unknown message type:', message.type);
    }
  }, [onTranscription, onTextResponse, onAudioChunk, onAudioComplete, onStatusChange, onError]);

  // Connect to WebSocket
  const connect = useCallback(async () => {
    console.log('[WS] 🔗 Initiating WebSocket connection...');

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WS] ✅ Already connected');
      return;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }

    try {
      const wsUrl = await getWebSocketUrl();
      console.log('[WS] 🌐 Creating WebSocket connection...');
      const ws = new WebSocket(wsUrl);

      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] ✅ WebSocket connected successfully');
        console.log('[WS] 📊 ReadyState:', ws.readyState, '(1=OPEN)');
        setIsConnected(true);
        onStatusChange?.('Connected');

        // Send initialization message
        console.log('[WS] 📤 Sending init message');
        ws.send(JSON.stringify({
          type: 'init',
          data: {
            user_id: 'user-123', // TODO: Get from auth
            session_id: Date.now().toString()
          }
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
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

  // Start recording with PCM streaming (NEW IMPLEMENTATION)
  const startRecordingInternal = async () => {
    console.log('[WS] 🎤 Starting PCM streaming for hands-free conversation...');

    try {
      // Get audio processor
      const audioProcessor = getAudioProcessor();

      // Start streaming raw PCM chunks
      const stopStreaming = await audioProcessor.startPCMStreaming(
        (pcmData: Float32Array, sampleRate: number) => {
          // Send PCM chunk to server
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            // Convert Float32Array to base64 for WebSocket transport
            const buffer = pcmData.buffer;
            const base64 = btoa(
              String.fromCharCode(...new Uint8Array(buffer))
            );

            // Send as pcm_chunk message type
            wsRef.current.send(JSON.stringify({
              type: 'pcm_chunk',
              data: base64,
              sample_rate: sampleRate
            }));

            console.log(`[WS] 📤 PCM chunk sent: ${pcmData.length} samples @ ${sampleRate}Hz`);
          }
        },
        500  // Send chunks every 500ms
      );

      // Store stop function for cleanup
      stopStreamingRef.current = stopStreaming;
      updateIsRecording(true);
      onStatusChange?.('Recording (PCM streaming)...');

      console.log('[WS] ✅ PCM streaming started successfully');

    } catch (error) {
      console.error('[WS] ❌ Error starting PCM streaming:', error);
      if (error instanceof DOMException) {
        console.error('[WS] 📝 Error name:', error.name);
        console.error('[WS] 📝 Error message:', error.message);
      }
      onError?.('Microphone access denied');
    }
  };

  // Stop recording PCM streaming
  const stopRecordingInternal = () => {
    console.log('[WS] 🛑 Stopping PCM streaming...');

    if (stopStreamingRef.current) {
      stopStreamingRef.current();
      stopStreamingRef.current = null;
      console.log('[WS] ✅ PCM streaming stopped');
    }

    updateIsRecording(false);
    onStatusChange?.('Processing...');
  };

  // Play audio from base64
  const playAudio = async (base64Audio: string) => {
    try {
      // Skip empty audio chunks
      if (!base64Audio) {
        console.log('[WS] ⏭️  Skipping empty audio chunk');
        return;
      }

      console.log(`[WS] 🔊 Playing audio (${base64Audio.length} base64 chars)...`);
      updateIsSpeaking(true);

      // Use playAudioBase64 utility
      await playAudioBase64(base64Audio);

      console.log('[WS] ✅ Audio playback completed');
      updateIsSpeaking(false);
      currentAudioRef.current = null;

    } catch (error) {
      console.error('[WS] ❌ Error playing audio:', error);
      updateIsSpeaking(false);
      currentAudioRef.current = null;
      onError?.('Audio playback failed');
    }
  };

  // Public API - start recording
  const startRecording = () => {
    console.log('[WS] 👆 User clicked start recording');
    startRecordingInternal();
  };

  // Public API - stop recording
  const stopRecording = () => {
    console.log('[WS] 👆 User clicked stop recording');
    stopRecordingInternal();
  };

  // Public API - stop audio playback (barge-in)
  const stopAudio = () => {
    console.log('[WS] 🚫 User requested barge-in (stop audio)');

    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }

    // 🚀 NEW: Clear AudioQueue for streaming TTS
    if (audioQueueRef.current) {
      audioQueueRef.current.clear();
      console.log('[WS] 🗑️  AudioQueue cleared for barge-in');
    }

    updateIsSpeaking(false);
    sendMessage('barge_in', 'User interrupted');
  };

  // Connect only when we have a valid assistant ID
  useEffect(() => {
    // Don't connect if assistant ID is empty/invalid
    if (!assistantId || assistantId.trim() === '') {
      console.log('[WS] ⏸️ Waiting for valid assistant ID before connecting...');
      return;
    }

    console.log('[WS] 🚀 Valid assistant ID detected, connecting...', assistantId);
    connect();

    // Cleanup on unmount
    return () => {
      console.log('[WS] 🧹 Component unmounting, cleaning up...');

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assistantId]); // Re-connect when assistant ID changes

  return {
    isConnected,
    isRecording,
    isSpeaking,
    startRecording,
    stopRecording,
    stopAudio,
    stopSpeaking: stopAudio, // Alias for component compatibility
    sendTextMessage,
    connect,
    disconnect: () => {
      console.log('[WS] 🔌 Manual disconnect requested');
      if (wsRef.current) {
        wsRef.current.close(1000, 'User disconnected');
        wsRef.current = null;
      }
      setIsConnected(false);
    },
    playAudio // Return playAudio function
  };
};
