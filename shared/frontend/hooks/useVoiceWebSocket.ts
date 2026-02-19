/**
 * Shared WebSocket Voice Chat Hook
 *
 * Provides WebSocket-based voice conversation capabilities for any app.
 * Features:
 * - PCM audio streaming
 * - Transcription handling
 * - TTS audio playback queue
 * - Barge-in support
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { playAudioBase64 } from '../lib/audio-utils';
import { getAudioProcessor } from '../services/audio-processor';

interface WebSocketMessage {
  type: string;
  data: any;
}

export interface UseVoiceWebSocketOptions {
  wsBaseUrl: string;
  assistantId: string;
  getAuthToken: () => Promise<string>;
  onTranscription?: (text: string, isFinal: boolean) => void;
  onTextResponse?: (text: string) => void;
  onAudioChunk?: (audioData: string) => void;
  onAudioComplete?: (metadata: any) => void;
  onError?: (error: string) => void;
  onStatusChange?: (status: string) => void;
}

/**
 * AudioQueue - Manages sequential playback of streaming audio chunks
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

  async enqueue(base64Audio: string): Promise<void> {
    if (!base64Audio) return;

    this.queue.push(base64Audio);
    console.log(`[AudioQueue] 📥 Enqueued chunk (queue size: ${this.queue.length})`);

    if (!this.isPlaying) {
      await this.playNext();
    }
  }

  private async playNext(): Promise<void> {
    if (this.queue.length === 0) {
      this.isPlaying = false;
      this.updateIsSpeaking(false);
      return;
    }

    this.isPlaying = true;
    this.updateIsSpeaking(true);

    const chunk = this.queue.shift()!;

    try {
      await playAudioBase64(chunk);
      await this.playNext();
    } catch (error) {
      console.error('[AudioQueue] ❌ Error playing chunk:', error);
      this.onError?.('Audio playback failed');
      await this.playNext();
    }
  }

  clear(): void {
    console.log(`[AudioQueue] 🗑️ Clearing queue (${this.queue.length} chunks)`);
    this.queue = [];
    this.isPlaying = false;
    this.updateIsSpeaking(false);
  }

  size(): number {
    return this.queue.length;
  }
}

export const useVoiceWebSocket = ({
  wsBaseUrl,
  assistantId,
  getAuthToken,
  onTranscription,
  onTextResponse,
  onAudioChunk,
  onAudioComplete,
  onError,
  onStatusChange
}: UseVoiceWebSocketOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const stopStreamingRef = useRef<(() => void) | null>(null);
  const audioQueueRef = useRef<AudioQueue | null>(null);
  const isRecordingRef = useRef(false);
  const isSpeakingRef = useRef(false);

  const updateIsRecording = (value: boolean) => {
    isRecordingRef.current = value;
    setIsRecording(value);
  };

  const updateIsSpeaking = (value: boolean) => {
    isSpeakingRef.current = value;
    setIsSpeaking(value);
  };

  // Initialize AudioQueue
  if (!audioQueueRef.current) {
    audioQueueRef.current = new AudioQueue(updateIsSpeaking, onError);
  }

  const getWebSocketUrl = async () => {
    if (!assistantId || assistantId.trim() === '') {
      throw new Error('Assistant ID is required');
    }

    try {
      const token = await getAuthToken();
      return `${wsBaseUrl}/voice/ws/voice-chat/${assistantId}?token=${token}`;
    } catch (error) {
      console.error('[WS] Failed to get auth token:', error);
      return `${wsBaseUrl}/voice/ws/voice-chat/${assistantId}`;
    }
  };

  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'status':
        onStatusChange?.(message.data);
        break;

      case 'transcription':
        let text = '';
        let isFinal = false;

        if (typeof message.data === 'string') {
          text = message.data;
          isFinal = true;
        } else if (message.data && typeof message.data === 'object') {
          text = message.data.text || '';
          isFinal = message.data.is_final ?? false;
        }
        onTranscription?.(text, isFinal);
        break;

      case 'text_response':
        onTextResponse?.(message.data);
        break;

      case 'audio_chunk':
        onAudioChunk?.(message.data);
        audioQueueRef.current?.enqueue(message.data);
        break;

      case 'audio_complete':
        onAudioComplete?.(message.data);
        break;

      case 'error':
        console.error('[WS] Server error:', message.data);
        onError?.(message.data);
        break;

      default:
        console.warn('[WS] Unknown message type:', message.type);
    }
  }, [onTranscription, onTextResponse, onAudioChunk, onAudioComplete, onStatusChange, onError]);

  const connect = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    try {
      const wsUrl = await getWebSocketUrl();
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected');
        setIsConnected(true);
        onStatusChange?.('Connected');

        ws.send(JSON.stringify({
          type: 'init',
          data: { session_id: Date.now().toString() }
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (err) {
          console.error('[WS] Error parsing message:', err);
        }
      };

      ws.onerror = () => {
        onError?.('Connection error');
      };

      ws.onclose = (event) => {
        console.log('[WS] Disconnected');
        setIsConnected(false);
        wsRef.current = null;
        onStatusChange?.('Disconnected');

        if (!event.wasClean && event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => connect(), 3000);
        }
      };
    } catch (error) {
      console.error('[WS] Failed to connect:', error);
      onError?.('Failed to connect');
    }
  }, [assistantId, onStatusChange, onError, handleWebSocketMessage]);

  const sendMessage = (type: string, data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, data }));
    } else {
      onError?.('Not connected');
    }
  };

  const sendTextMessage = (text: string) => {
    sendMessage('text', text);
  };

  const startRecording = async () => {
    try {
      const audioProcessor = getAudioProcessor();

      const stopStreaming = await audioProcessor.startPCMStreaming(
        (pcmData: Float32Array, sampleRate: number) => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            const buffer = pcmData.buffer;
            const base64 = btoa(String.fromCharCode(...new Uint8Array(buffer)));

            wsRef.current.send(JSON.stringify({
              type: 'pcm_chunk',
              data: base64,
              sample_rate: sampleRate
            }));
          }
        },
        500
      );

      stopStreamingRef.current = stopStreaming;
      updateIsRecording(true);
      onStatusChange?.('Recording...');
    } catch (error) {
      console.error('[WS] Error starting recording:', error);
      onError?.('Microphone access denied');
    }
  };

  const stopRecording = () => {
    if (stopStreamingRef.current) {
      stopStreamingRef.current();
      stopStreamingRef.current = null;
    }
    updateIsRecording(false);
    onStatusChange?.('Processing...');
  };

  const stopSpeaking = () => {
    audioQueueRef.current?.clear();
    updateIsSpeaking(false);
    sendMessage('barge_in', 'User interrupted');
  };

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    setIsConnected(false);
  };

  // Connect when assistant ID is available
  useEffect(() => {
    if (!assistantId || assistantId.trim() === '') {
      return;
    }

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (stopStreamingRef.current) {
        stopStreamingRef.current();
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
      }
    };
  }, [assistantId]);

  return {
    isConnected,
    isRecording,
    isSpeaking,
    startRecording,
    stopRecording,
    stopSpeaking,
    sendTextMessage,
    connect,
    disconnect
  };
};
