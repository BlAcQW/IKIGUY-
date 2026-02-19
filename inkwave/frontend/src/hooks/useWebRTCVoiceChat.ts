/**
 * WebRTC Voice Chat Hook for InkWave
 *
 * Provides low-latency voice interaction using WebRTC:
 * - Direct audio streaming via media tracks
 * - Data channel for control messages
 * - STUN server configuration for NAT traversal
 *
 * Author: AI Labs Africa
 * Created: November 30, 2025
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { getAuthToken } from '@/lib/auth-utils';
import { INKWAVE_WS_URL } from '@/config/api-config';

interface VoiceSettings {
  provider_id?: string;
  voice_id?: string;
  speed?: number;
  language?: string;
}

interface UseWebRTCVoiceChatOptions {
  bookId: string;
  voiceSettings?: VoiceSettings;
  onTranscription?: (text: string, isFinal: boolean) => void;
  onTextResponse?: (text: string) => void;
  onError?: (error: string) => void;
  onStatusChange?: (status: string) => void;
}

// STUN servers for NAT traversal
const ICE_SERVERS = [
  { urls: 'stun:stun.l.google.com:19302' },
  { urls: 'stun:stun1.l.google.com:19302' },
  { urls: 'stun:stun2.l.google.com:19302' }
];

export const useWebRTCVoiceChat = ({
  bookId,
  voiceSettings,
  onTranscription,
  onTextResponse,
  onError,
  onStatusChange
}: UseWebRTCVoiceChatOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [response, setResponse] = useState('');

  // WebSocket for signaling
  const wsRef = useRef<WebSocket | null>(null);

  // WebRTC connection
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);

  // Media streams
  const localStreamRef = useRef<MediaStream | null>(null);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);

  // State refs for callbacks
  const isRecordingRef = useRef(false);

  const updateIsRecording = useCallback((value: boolean) => {
    isRecordingRef.current = value;
    setIsRecording(value);
  }, []);

  // Get signaling WebSocket URL
  const getSignalingUrl = useCallback(async () => {
    const baseUrl = INKWAVE_WS_URL;

    if (!bookId) {
      throw new Error('Book ID is required');
    }

    try {
      const token = await getAuthToken();
      return `${baseUrl}/ws/webrtc-signaling/${bookId}?token=${token}`;
    } catch (error) {
      console.error('[WebRTC] Failed to get auth token:', error);
      return `${baseUrl}/ws/webrtc-signaling/${bookId}`;
    }
  }, [bookId]);

  // Initialize WebRTC peer connection
  const initializePeerConnection = useCallback(() => {
    console.log('[WebRTC] Initializing peer connection...');

    const pc = new RTCPeerConnection({
      iceServers: ICE_SERVERS
    });

    // Handle ICE candidates
    pc.onicecandidate = (event) => {
      if (event.candidate && wsRef.current?.readyState === WebSocket.OPEN) {
        console.log('[WebRTC] Sending ICE candidate');
        wsRef.current.send(JSON.stringify({
          type: 'ice_candidate',
          data: event.candidate
        }));
      }
    };

    // Handle connection state changes
    pc.onconnectionstatechange = () => {
      console.log('[WebRTC] Connection state:', pc.connectionState);
      if (pc.connectionState === 'connected') {
        setIsConnected(true);
        onStatusChange?.('Connected');
      } else if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
        setIsConnected(false);
        onStatusChange?.('Disconnected');
      }
    };

    // Handle incoming audio track
    pc.ontrack = (event) => {
      console.log('[WebRTC] Received remote track:', event.track.kind);
      if (event.track.kind === 'audio') {
        if (!remoteAudioRef.current) {
          remoteAudioRef.current = new Audio();
          remoteAudioRef.current.autoplay = true;
        }
        remoteAudioRef.current.srcObject = event.streams[0];
        setIsSpeaking(true);
      }
    };

    // Create data channel for control messages
    const dataChannel = pc.createDataChannel('control');
    dataChannel.onopen = () => {
      console.log('[WebRTC] Data channel open');
      // Send initialization
      dataChannel.send(JSON.stringify({
        type: 'init',
        voice_settings: voiceSettings
      }));
    };

    dataChannel.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleDataChannelMessage(message);
      } catch (error) {
        console.error('[WebRTC] Error parsing data channel message:', error);
      }
    };

    dataChannel.onclose = () => {
      console.log('[WebRTC] Data channel closed');
    };

    dataChannelRef.current = dataChannel;
    peerConnectionRef.current = pc;

    return pc;
  }, [voiceSettings, onStatusChange]);

  // Handle data channel messages
  const handleDataChannelMessage = useCallback((message: any) => {
    console.log('[WebRTC] Data channel message:', message.type);

    switch (message.type) {
      case 'transcription':
        const text = message.text || message.data?.text || '';
        const isFinal = message.is_final ?? message.data?.is_final ?? true;
        setTranscription(text);
        onTranscription?.(text, isFinal);
        break;

      case 'text_response':
        const responseText = message.text || message.data || '';
        setResponse(responseText);
        onTextResponse?.(responseText);
        break;

      case 'speaking_start':
        setIsSpeaking(true);
        break;

      case 'speaking_end':
        setIsSpeaking(false);
        break;

      case 'error':
        onError?.(message.data || message.error || 'Unknown error');
        break;

      case 'status':
        onStatusChange?.(message.data || message.status);
        break;
    }
  }, [onTranscription, onTextResponse, onError, onStatusChange]);

  // Handle signaling messages
  const handleSignalingMessage = useCallback(async (message: any) => {
    console.log('[WebRTC] Signaling message:', message.type);

    const pc = peerConnectionRef.current;
    if (!pc) return;

    switch (message.type) {
      case 'config':
        // Server config received
        console.log('[WebRTC] Server config:', message.data);
        break;

      case 'offer':
        // Received offer from server/peer
        console.log('[WebRTC] Received SDP offer');
        await pc.setRemoteDescription(new RTCSessionDescription(message.data.sdp));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);

        wsRef.current?.send(JSON.stringify({
          type: 'answer',
          data: answer,
          target: message.data.from
        }));
        break;

      case 'answer':
        // Received answer from server/peer
        console.log('[WebRTC] Received SDP answer');
        await pc.setRemoteDescription(new RTCSessionDescription(message.data.sdp));
        break;

      case 'ice_candidate':
        // Received ICE candidate
        console.log('[WebRTC] Received ICE candidate');
        if (message.data.candidate) {
          await pc.addIceCandidate(new RTCIceCandidate(message.data.candidate));
        }
        break;

      case 'peer_joined':
        console.log('[WebRTC] Peer joined:', message.data.peer_id);
        break;

      case 'peer_left':
        console.log('[WebRTC] Peer left:', message.data.peer_id);
        break;
    }
  }, []);

  // Connect to signaling server
  const connect = useCallback(async () => {
    console.log('[WebRTC] Connecting...');

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WebRTC] Already connected');
      return;
    }

    try {
      const wsUrl = await getSignalingUrl();
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = async () => {
        console.log('[WebRTC] Signaling connected');

        // Initialize peer connection
        const pc = initializePeerConnection();

        // Get local audio stream
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true
            }
          });

          localStreamRef.current = stream;

          // Add audio track to peer connection
          stream.getAudioTracks().forEach(track => {
            pc.addTrack(track, stream);
          });

          console.log('[WebRTC] Local audio track added');

          // Create and send offer
          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);

          ws.send(JSON.stringify({
            type: 'offer',
            data: offer
          }));

          console.log('[WebRTC] SDP offer sent');
          onStatusChange?.('Connecting...');

        } catch (mediaError) {
          console.error('[WebRTC] Media access error:', mediaError);
          onError?.('Microphone access denied');
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleSignalingMessage(message);
        } catch (error) {
          console.error('[WebRTC] Error parsing signaling message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebRTC] Signaling error:', error);
        onError?.('Connection error');
      };

      ws.onclose = () => {
        console.log('[WebRTC] Signaling disconnected');
        setIsConnected(false);
        onStatusChange?.('Disconnected');
      };

    } catch (error) {
      console.error('[WebRTC] Failed to connect:', error);
      onError?.('Failed to connect');
    }
  }, [bookId, getSignalingUrl, initializePeerConnection, handleSignalingMessage, onStatusChange, onError]);

  // Start/stop recording (mute/unmute local audio)
  const startRecording = useCallback(() => {
    console.log('[WebRTC] Start recording');

    if (localStreamRef.current) {
      localStreamRef.current.getAudioTracks().forEach(track => {
        track.enabled = true;
      });
    }

    updateIsRecording(true);

    // Notify via data channel
    if (dataChannelRef.current?.readyState === 'open') {
      dataChannelRef.current.send(JSON.stringify({
        type: 'start_recording'
      }));
    }

    onStatusChange?.('Recording...');
  }, [updateIsRecording, onStatusChange]);

  const stopRecording = useCallback(() => {
    console.log('[WebRTC] Stop recording');

    if (localStreamRef.current) {
      localStreamRef.current.getAudioTracks().forEach(track => {
        track.enabled = false;
      });
    }

    updateIsRecording(false);

    // Notify via data channel
    if (dataChannelRef.current?.readyState === 'open') {
      dataChannelRef.current.send(JSON.stringify({
        type: 'stop_recording'
      }));
    }

    onStatusChange?.('Processing...');
  }, [updateIsRecording, onStatusChange]);

  // Stop audio playback (barge-in)
  const stopAudio = useCallback(() => {
    console.log('[WebRTC] Barge-in');

    if (remoteAudioRef.current) {
      remoteAudioRef.current.pause();
      remoteAudioRef.current.currentTime = 0;
    }

    setIsSpeaking(false);

    // Notify via data channel
    if (dataChannelRef.current?.readyState === 'open') {
      dataChannelRef.current.send(JSON.stringify({
        type: 'barge_in'
      }));
    }
  }, []);

  // Send text message via data channel
  const sendTextMessage = useCallback((text: string) => {
    console.log('[WebRTC] Sending text:', text);

    if (dataChannelRef.current?.readyState === 'open') {
      dataChannelRef.current.send(JSON.stringify({
        type: 'text',
        text
      }));
    } else {
      onError?.('Not connected');
    }
  }, [onError]);

  // Disconnect
  const disconnect = useCallback(() => {
    console.log('[WebRTC] Disconnecting...');

    // Close data channel
    if (dataChannelRef.current) {
      dataChannelRef.current.close();
      dataChannelRef.current = null;
    }

    // Close peer connection
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }

    // Stop local stream
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
      localStreamRef.current = null;
    }

    // Close signaling WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  // Connect when bookId is available
  useEffect(() => {
    if (!bookId) {
      console.log('[WebRTC] Waiting for book ID...');
      return;
    }

    // Don't auto-connect - let component call connect()
    console.log('[WebRTC] Ready to connect for book:', bookId);

    return () => {
      disconnect();
    };
  }, [bookId, disconnect]);

  return {
    // State
    isConnected,
    isRecording,
    isSpeaking,
    transcription,
    response,

    // Actions
    connect,
    disconnect,
    startRecording,
    stopRecording,
    stopAudio,
    stopSpeaking: stopAudio,
    sendTextMessage,

    // Clear state
    clearTranscription: () => setTranscription(''),
    clearResponse: () => setResponse('')
  };
};
