/**
 * Shared WebRTC Voice Chat Hook
 *
 * Provides WebRTC-based voice conversation capabilities for any app.
 * Features:
 * - Low-latency voice streaming via RTCPeerConnection
 * - Data channel for control messages
 * - TTS audio playback queue
 * - Barge-in support
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { playAudioBase64 } from '../lib/audio-utils';

export interface UseVoiceWebRTCOptions {
  apiBaseUrl: string;
  assistantId: string;
  getAuthToken: () => Promise<string>;
  assistant?: {
    language?: string;
    llm_provider?: string;
    llm_model?: string;
    tts_provider?: string;
    stt_provider?: string;
  };
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

export const useVoiceWebRTC = ({
  apiBaseUrl,
  assistantId,
  getAuthToken,
  assistant,
  onTranscription,
  onTextResponse,
  onAudioChunk,
  onAudioComplete,
  onError,
  onStatusChange
}: UseVoiceWebRTCOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioQueueRef = useRef<AudioQueue | null>(null);
  const connectingRef = useRef(false);
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

  const handleDataChannelMessage = useCallback((event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'transcription':
          const { text, is_final } = message.data;
          onTranscription?.(text, is_final);
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

        case 'status':
          onStatusChange?.(message.data);
          break;

        case 'error':
          console.error('[RTC] Server error:', message.data);
          onError?.(message.data);
          break;

        default:
          console.warn('[RTC] Unknown message type:', message.type);
      }
    } catch (err) {
      console.error('[RTC] Error parsing data channel message:', err);
    }
  }, [onTranscription, onTextResponse, onAudioChunk, onAudioComplete, onStatusChange, onError]);

  const connect = useCallback(async () => {
    if (connectingRef.current || peerConnectionRef.current) {
      return;
    }

    if (!assistantId || assistantId.trim() === '') {
      onError?.('Assistant ID is required');
      return;
    }

    connectingRef.current = true;

    try {
      const pc = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' }
        ]
      });

      peerConnectionRef.current = pc;

      const dc = pc.createDataChannel('chat', { ordered: true });
      dataChannelRef.current = dc;

      dc.onopen = () => {
        console.log('[RTC] Data channel opened');
        setIsConnected(true);
        onStatusChange?.('Connected');
      };

      dc.onclose = () => {
        console.log('[RTC] Data channel closed');
        setIsConnected(false);
        onStatusChange?.('Disconnected');
      };

      dc.onmessage = handleDataChannelMessage;

      pc.ontrack = (event) => {
        console.log('[RTC] Received remote audio track');
        const remoteStream = event.streams[0];
        const audioElement = new Audio();
        audioElement.srcObject = remoteStream;
        audioElement.autoplay = true;
      };

      console.log('[RTC] Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });

      audioStreamRef.current = stream;

      stream.getTracks().forEach(track => {
        pc.addTrack(track, stream);
      });

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const token = await getAuthToken();
      const response = await fetch(`${apiBaseUrl}/voice/webrtc/offer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          sdp: offer.sdp,
          type: offer.type,
          assistant_id: assistantId,
          // Include provider overrides if available
          ...(assistant?.llm_provider && { llm_provider: assistant.llm_provider }),
          ...(assistant?.llm_model && { llm_model: assistant.llm_model }),
          ...(assistant?.tts_provider && { tts_provider: assistant.tts_provider }),
          ...(assistant?.stt_provider && { stt_provider: assistant.stt_provider }),
          ...(assistant?.language && { language: assistant.language })
        })
      });

      if (!response.ok) {
        throw new Error(`WebRTC offer failed: ${response.statusText}`);
      }

      const answer = await response.json();
      await pc.setRemoteDescription(new RTCSessionDescription(answer));
      console.log('[RTC] WebRTC connection established');

      connectingRef.current = false;

    } catch (error) {
      console.error('[RTC] Failed to establish connection:', error);
      onError?.(`Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsConnected(false);
      connectingRef.current = false;

      if (peerConnectionRef.current) {
        peerConnectionRef.current.close();
        peerConnectionRef.current = null;
      }
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
        audioStreamRef.current = null;
      }
    }
  }, [assistantId, apiBaseUrl, getAuthToken, onError, onStatusChange, handleDataChannelMessage]);

  const disconnect = useCallback(() => {
    if (dataChannelRef.current) {
      dataChannelRef.current.close();
      dataChannelRef.current = null;
    }

    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }

    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop());
      audioStreamRef.current = null;
    }

    audioQueueRef.current?.clear();
    setIsConnected(false);
    updateIsRecording(false);
    updateIsSpeaking(false);
    connectingRef.current = false;
    onStatusChange?.('Disconnected');
  }, [onStatusChange]);

  const sendMessage = useCallback((type: string, data: any) => {
    if (dataChannelRef.current?.readyState === 'open') {
      dataChannelRef.current.send(JSON.stringify({ type, data }));
    } else {
      onError?.('Not connected');
    }
  }, [onError]);

  const sendTextMessage = useCallback((text: string) => {
    sendMessage('text', text);
  }, [sendMessage]);

  const startRecording = useCallback(() => {
    if (!audioStreamRef.current) {
      onError?.('Microphone not initialized');
      return;
    }

    audioStreamRef.current.getAudioTracks().forEach(track => {
      track.enabled = true;
    });

    updateIsRecording(true);
    onStatusChange?.('Recording...');
    sendMessage('start_recording', null);
  }, [onError, onStatusChange, sendMessage]);

  const stopRecording = useCallback(() => {
    if (!audioStreamRef.current) return;

    audioStreamRef.current.getAudioTracks().forEach(track => {
      track.enabled = false;
    });

    updateIsRecording(false);
    onStatusChange?.('Processing...');
    sendMessage('stop_recording', null);
  }, [onStatusChange, sendMessage]);

  const stopSpeaking = useCallback(() => {
    audioQueueRef.current?.clear();
    updateIsSpeaking(false);
    sendMessage('barge_in', 'User interrupted');
  }, [sendMessage]);

  // Connect when assistant ID is available
  useEffect(() => {
    if (!assistantId || assistantId.trim() === '') {
      return;
    }

    connect();

    return () => {
      disconnect();
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
