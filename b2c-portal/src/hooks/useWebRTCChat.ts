import { useState, useRef, useCallback, useEffect } from 'react';
import { getAuthToken } from '@/lib/auth-utils';
import { playAudioBase64 } from '@/lib/audio-utils';
import { API_BASE_URL } from '@/config/api-config';

interface UseWebRTCChatOptions {
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
    if (!base64Audio) {
      console.log('[AudioQueue] ⏭️  Skipping empty chunk');
      return;
    }

    this.queue.push(base64Audio);
    console.log(`[AudioQueue] 📥 Enqueued chunk (queue size: ${this.queue.length})`);

    if (!this.isPlaying) {
      await this.playNext();
    }
  }

  /**
   * Play the next chunk in the queue
   * Recursively calls itself until queue is empty
   */
  private async playNext(): Promise<void> {
    if (this.queue.length === 0) {
      console.log('[AudioQueue] ✅ Queue empty, playback complete');
      this.isPlaying = false;
      this.updateIsSpeaking(false);
      return;
    }

    this.isPlaying = true;
    this.updateIsSpeaking(true);

    const chunk = this.queue.shift()!;
    console.log(`[AudioQueue] 🔊 Playing chunk (${this.queue.length} remaining in queue)`);

    try {
      await playAudioBase64(chunk);
      console.log('[AudioQueue] ✅ Chunk played successfully');
      await this.playNext();
    } catch (error) {
      console.error('[AudioQueue] ❌ Error playing chunk:', error);
      this.onError?.('Audio playback failed');
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

/**
 * useWebRTCChat - React hook for WebRTC voice conversations
 *
 * Uses the FastRTC backend at /voice/webrtc for low-latency voice chat.
 * Provides similar interface to useWebSocketChat for easy migration.
 */
export const useWebRTCChat = ({
  assistantId,
  onTranscription,
  onTextResponse,
  onAudioChunk,
  onAudioComplete,
  onError,
  onStatusChange
}: UseWebRTCChatOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioQueueRef = useRef<AudioQueue | null>(null);
  const connectingRef = useRef(false);

  // Track state in refs to avoid stale closures
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
    console.log('[RTC] 🎵 AudioQueue initialized for streaming TTS');
  }

  /**
   * Handle incoming data channel messages from WebRTC
   */
  const handleDataChannelMessage = useCallback((event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data);
      console.log(`[RTC] 🎯 Received message type: ${message.type}`);

      switch (message.type) {
        case 'transcription':
          const { text, is_final } = message.data;
          console.log(`[RTC] 🎤 Transcription: "${text}" (final: ${is_final})`);
          onTranscription?.(text, is_final);
          break;

        case 'text_response':
          console.log('[RTC] 💬 Text response:', message.data.substring(0, 100));
          onTextResponse?.(message.data);
          break;

        case 'audio_chunk':
          const chunkSize = message.data?.length || 0;
          console.log(`[RTC] 🔊 Audio chunk received (${chunkSize} bytes)`);
          onAudioChunk?.(message.data);
          audioQueueRef.current?.enqueue(message.data);
          break;

        case 'audio_complete':
          console.log('[RTC] ✅ Audio stream complete:', message.data);
          onAudioComplete?.(message.data);
          break;

        case 'status':
          console.log('[RTC] 📊 Status update:', message.data);
          onStatusChange?.(message.data);
          break;

        case 'error':
          console.error('[RTC] ❌ Server error:', message.data);
          onError?.(message.data);
          break;

        default:
          console.warn('[RTC] ⚠️  Unknown message type:', message.type);
      }
    } catch (err) {
      console.error('[RTC] ❌ Error parsing data channel message:', err);
    }
  }, [onTranscription, onTextResponse, onAudioChunk, onAudioComplete, onStatusChange, onError]);

  /**
   * Connect to WebRTC endpoint
   */
  const connect = useCallback(async () => {
    console.log('[RTC] 🔗 Initiating WebRTC connection...');

    // Guard: Prevent duplicate connection attempts
    if (connectingRef.current) {
      console.log('[RTC] ⚠️ Already connecting - ignoring duplicate request');
      return;
    }

    if (peerConnectionRef.current) {
      console.log('[RTC] ✅ Already have peer connection');
      return;
    }

    connectingRef.current = true;

    try {
      // Create RTCPeerConnection
      const pc = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' }
        ]
      });

      peerConnectionRef.current = pc;

      // Set up data channel for control messages
      const dc = pc.createDataChannel('chat', { ordered: true });
      dataChannelRef.current = dc;

      dc.onopen = () => {
        console.log('[RTC] 📡 Data channel opened');
        setIsConnected(true);
        onStatusChange?.('Connected');
      };

      dc.onclose = () => {
        console.log('[RTC] 📡 Data channel closed');
        setIsConnected(false);
        onStatusChange?.('Disconnected');
      };

      dc.onmessage = handleDataChannelMessage;

      // Handle incoming audio tracks
      pc.ontrack = (event) => {
        console.log('[RTC] 🎵 Received remote audio track');
        const remoteStream = event.streams[0];

        // Play remote audio (assistant response)
        const audioElement = new Audio();
        audioElement.srcObject = remoteStream;
        audioElement.autoplay = true;

        console.log('[RTC] 🔊 Playing remote audio stream');
      };

      // Get user's microphone
      console.log('[RTC] 🎤 Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });

      audioStreamRef.current = stream;
      console.log('[RTC] ✅ Microphone access granted');

      // Add audio track to peer connection
      stream.getTracks().forEach(track => {
        pc.addTrack(track, stream);
        console.log('[RTC] 📤 Added audio track to peer connection');
      });

      // Create offer
      console.log('[RTC] 📝 Creating WebRTC offer...');
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // Send offer to server
      const token = await getAuthToken();
      const response = await fetch(`${API_BASE_URL}/voice/webrtc/offer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          sdp: offer.sdp,
          type: offer.type,
          assistant_id: assistantId
        })
      });

      if (!response.ok) {
        throw new Error(`WebRTC offer failed: ${response.statusText}`);
      }

      const answer = await response.json();
      console.log('[RTC] 📥 Received answer from server');

      // Set remote description
      await pc.setRemoteDescription(new RTCSessionDescription(answer));
      console.log('[RTC] ✅ WebRTC connection established');

      // Connection successful - reset connecting flag
      connectingRef.current = false;

      // First message is now handled by backend startup_fn via data channel
      // NO HTTP calls - everything streams in real-time via data channel
      // The data channel onmessage handler will receive first message chunks automatically

    } catch (error) {
      console.error('[RTC] ❌ Failed to establish WebRTC connection:', error);
      onError?.(`Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsConnected(false);

      // Reset connecting flag on error
      connectingRef.current = false;

      // Cleanup on error
      if (peerConnectionRef.current) {
        peerConnectionRef.current.close();
        peerConnectionRef.current = null;
      }
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
        audioStreamRef.current = null;
      }
    }
  }, [assistantId, onError, onStatusChange, handleDataChannelMessage]);

  /**
   * Disconnect WebRTC connection
   */
  const disconnect = useCallback(() => {
    console.log('[RTC] 🔌 Disconnecting WebRTC...');

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

  /**
   * Send message through data channel
   */
  const sendMessage = useCallback((type: string, data: any) => {
    if (dataChannelRef.current?.readyState === 'open') {
      const message = JSON.stringify({ type, data });
      dataChannelRef.current.send(message);
      console.log(`[RTC] 📤 Sent message: ${type}`);
    } else {
      console.error('[RTC] ❌ Cannot send message - data channel not open');
      onError?.('Not connected');
    }
  }, [onError]);

  /**
   * Send text message
   */
  const sendTextMessage = useCallback((text: string) => {
    console.log(`[RTC] 💬 Sending text message: "${text}"`);
    sendMessage('text', text);
  }, [sendMessage]);

  /**
   * Start recording (enable microphone track)
   */
  const startRecording = useCallback(() => {
    console.log('[RTC] 🎤 Starting recording...');

    if (!audioStreamRef.current) {
      console.error('[RTC] ❌ No audio stream available');
      onError?.('Microphone not initialized');
      return;
    }

    // Enable audio tracks
    audioStreamRef.current.getAudioTracks().forEach(track => {
      track.enabled = true;
    });

    updateIsRecording(true);
    onStatusChange?.('Recording...');
    sendMessage('start_recording', null);
  }, [onError, onStatusChange, sendMessage]);

  /**
   * Stop recording (mute microphone track)
   */
  const stopRecording = useCallback(() => {
    console.log('[RTC] 🛑 Stopping recording...');

    if (!audioStreamRef.current) {
      return;
    }

    // Disable audio tracks
    audioStreamRef.current.getAudioTracks().forEach(track => {
      track.enabled = false;
    });

    updateIsRecording(false);
    onStatusChange?.('Processing...');
    sendMessage('stop_recording', null);
  }, [onStatusChange, sendMessage]);

  /**
   * Stop audio playback (barge-in)
   */
  const stopAudio = useCallback(() => {
    console.log('[RTC] 🚫 User requested barge-in (stop audio)');
    audioQueueRef.current?.clear();
    updateIsSpeaking(false);
    sendMessage('barge_in', 'User interrupted');
  }, [sendMessage]);

  // Auto-connect on mount
  useEffect(() => {
    console.log('[RTC] 🚀 Component mounted, connecting...');
    connect();

    // Cleanup on unmount
    return () => {
      console.log('[RTC] 🧹 Component unmounting, cleaning up...');
      disconnect();
    };
  }, []); // Empty deps - only run on mount/unmount (connect/disconnect are stable via useCallback)

  return {
    isConnected,
    isRecording,
    isSpeaking,
    startRecording,
    stopRecording,
    stopAudio,
    sendTextMessage,
    connect,
    disconnect
  };
};
