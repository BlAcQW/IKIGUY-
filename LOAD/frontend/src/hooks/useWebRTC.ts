import { useState, useRef, useCallback, useEffect } from 'react';
import { getToken } from '../lib/auth';

const API_BASE = '/api';

interface TranscriptEntry {
  role: 'user' | 'assistant';
  content: string;
}

type CallStatus = 'idle' | 'connecting' | 'active' | 'processing' | 'ended' | 'error';

interface UseWebRTCReturn {
  callStatus: CallStatus;
  transcript: TranscriptEntry[];
  callId: string;
  callDuration: number;
  isMuted: boolean;
  errorMessage: string;
  errorCode: string;
  startCall: (assistantId: string) => Promise<void>;
  endCall: () => void;
  toggleMute: () => void;
  reset: () => void;
}

function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
}

export function useWebRTC(): UseWebRTCReturn {
  const [callStatus, setCallStatus] = useState<CallStatus>('idle');
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [callId, setCallId] = useState('');
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [errorCode, setErrorCode] = useState('');

  const pcRef = useRef<RTCPeerConnection | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const durationIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const callIdRef = useRef('');

  // Duration timer
  useEffect(() => {
    if (callStatus === 'active' || callStatus === 'processing') {
      if (!durationIntervalRef.current) {
        durationIntervalRef.current = setInterval(() => {
          setCallDuration((d) => d + 1);
        }, 1000);
      }
    } else {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }
    }
    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, [callStatus]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, []);

  const cleanup = useCallback(() => {
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
      durationIntervalRef.current = null;
    }

    localStreamRef.current?.getTracks().forEach((t) => t.stop());
    localStreamRef.current = null;

    try {
      pcRef.current?.close();
    } catch {
      // Already closed
    }
    pcRef.current = null;

    dataChannelRef.current = null;

    if (remoteAudioRef.current) {
      remoteAudioRef.current.srcObject = null;
      remoteAudioRef.current = null;
    }
  }, []);

  const handleDataChannelMessage = useCallback((event: MessageEvent) => {
    try {
      const msg = JSON.parse(event.data);

      switch (msg.type) {
        case 'call_started':
          setCallStatus('active');
          setCallId(msg.callId ?? '');
          callIdRef.current = msg.callId ?? '';
          break;
        case 'user_transcript':
          setTranscript((prev) => [...prev, { role: 'user', content: msg.text }]);
          break;
        case 'assistant_message':
          setTranscript((prev) => [...prev, { role: 'assistant', content: msg.text }]);
          break;
        case 'processing':
          if (msg.status === 'started') {
            setCallStatus('processing');
          } else {
            setCallStatus('active');
          }
          break;
        case 'call_ended':
        case 'call_ending':
          setCallStatus('ended');
          break;
        case 'transfer':
          // Transfer handled, transcript continues
          break;
        case 'error':
          console.error('[WebRTC] Server error:', msg.message);
          break;
      }
    } catch {
      // Non-JSON message
    }
  }, []);

  const startCall = useCallback(async (assistantId: string) => {
    const token = getToken();
    if (!token) {
      setCallStatus('error');
      return;
    }

    setCallStatus('connecting');
    setTranscript([]);
    setCallDuration(0);
    setIsMuted(false);
    setErrorMessage('');
    setErrorCode('');

    try {
      // Get user's microphone
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      localStreamRef.current = stream;

      // Create peer connection with STUN
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
      });
      pcRef.current = pc;

      // Add local audio track
      stream.getTracks().forEach((track) => {
        pc.addTrack(track, stream);
      });

      // Handle remote audio
      pc.ontrack = (event) => {
        const audio = new Audio();
        audio.srcObject = event.streams[0];
        audio.autoplay = true;
        remoteAudioRef.current = audio;
      };

      // Listen for DataChannel created by server
      pc.ondatachannel = (event) => {
        const dc = event.channel;
        dataChannelRef.current = dc;
        dc.onmessage = handleDataChannelMessage;
      };

      // Handle connection state changes
      pc.onconnectionstatechange = () => {
        if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
          setCallStatus('ended');
          cleanup();
        }
      };

      // Create offer
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // Wait for ICE gathering to complete (gather all candidates upfront)
      await waitForIceGathering(pc);

      // Send offer to server
      const response = await fetch(`${API_BASE}/calls/webrtc/offer`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          assistantId,
          sdpOffer: pc.localDescription?.sdp,
        }),
      });

      const json = await response.json();
      if (!json.success) {
        const errMsg = json.error?.message ?? 'Failed to start WebRTC call';
        const errCode = json.error?.code ?? '';
        setErrorMessage(errMsg);
        setErrorCode(errCode);
        throw new Error(errMsg);
      }

      callIdRef.current = json.data.callId;
      setCallId(json.data.callId);

      // Set remote description (server's answer)
      await pc.setRemoteDescription(
        new RTCSessionDescription({
          type: 'answer',
          sdp: json.data.sdpAnswer,
        })
      );
    } catch (err) {
      console.error('[WebRTC] Failed to start call:', err);
      if (!errorMessage) {
        setErrorMessage(err instanceof Error ? err.message : 'Failed to start call');
      }
      setCallStatus('error');
      cleanup();
    }
  }, [handleDataChannelMessage, cleanup]);

  const endCall = useCallback(() => {
    const currentCallId = callIdRef.current;
    if (currentCallId) {
      fetch(`${API_BASE}/calls/webrtc/${currentCallId}/end`, {
        method: 'POST',
        headers: getAuthHeaders(),
      }).catch(() => {});
    }

    setCallStatus('ended');
    cleanup();
  }, [cleanup]);

  const toggleMute = useCallback(() => {
    const stream = localStreamRef.current;
    if (!stream) return;

    const audioTrack = stream.getAudioTracks()[0];
    if (audioTrack) {
      audioTrack.enabled = !audioTrack.enabled;
      setIsMuted(!audioTrack.enabled);
    }
  }, []);

  const reset = useCallback(() => {
    setCallStatus('idle');
    setTranscript([]);
    setCallDuration(0);
    setCallId('');
    setErrorMessage('');
    setErrorCode('');
  }, []);

  return {
    callStatus,
    transcript,
    callId,
    callDuration,
    isMuted,
    errorMessage,
    errorCode,
    startCall,
    endCall,
    toggleMute,
    reset,
  };
}

/**
 * Wait for ICE gathering to complete (all candidates collected).
 * Times out after 3 seconds to avoid hanging on restrictive networks.
 */
function waitForIceGathering(pc: RTCPeerConnection): Promise<void> {
  return new Promise((resolve) => {
    if (pc.iceGatheringState === 'complete') {
      resolve();
      return;
    }

    const timeout = setTimeout(resolve, 3000);

    pc.onicegatheringstatechange = () => {
      if (pc.iceGatheringState === 'complete') {
        clearTimeout(timeout);
        resolve();
      }
    };
  });
}
