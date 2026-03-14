import { useState, useRef, useCallback, useEffect } from 'react';
import { getToken } from '../lib/auth';

interface TranscriptEntry {
  role: 'user' | 'assistant';
  content: string;
}

type TestStatus = 'idle' | 'connecting' | 'active' | 'processing' | 'ended' | 'error';

interface UseVoiceTestReturn {
  status: TestStatus;
  transcript: TranscriptEntry[];
  callDuration: number;
  errorMessage: string;
  isRecording: boolean;
  startTest: (config: object) => void;
  endTest: () => void;
  startRecording: () => Promise<void>;
  sendEndTurn: () => void;
  reset: () => void;
}

export function useVoiceTest(): UseVoiceTestReturn {
  const [status, setStatus] = useState<TestStatus>('idle');
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [callDuration, setCallDuration] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const durationIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const configRef = useRef<object | null>(null);

  // Duration timer
  useEffect(() => {
    if (status === 'active' || status === 'processing') {
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
  }, [status]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopTestInternal();
    };
  }, []);

  const playAudioQueue = useCallback(async () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) return;
    isPlayingRef.current = true;

    while (audioQueueRef.current.length > 0) {
      const data = audioQueueRef.current.shift();
      if (!data) break;

      try {
        if (!audioContextRef.current) {
          audioContextRef.current = new AudioContext({ sampleRate: 24000 });
        }
        const ctx = audioContextRef.current;

        const int16 = new Int16Array(data);
        const float32 = new Float32Array(int16.length);
        for (let i = 0; i < int16.length; i++) {
          float32[i] = int16[i] / 32768;
        }

        const audioBuffer = ctx.createBuffer(1, float32.length, 24000);
        audioBuffer.getChannelData(0).set(float32);

        const source = ctx.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(ctx.destination);

        await new Promise<void>((resolve) => {
          source.onended = () => resolve();
          source.start();
        });
      } catch {
        // Skip corrupted audio chunks
      }
    }

    isPlayingRef.current = false;
  }, []);

  function stopRecordingInternal() {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
    mediaStreamRef.current = null;
    mediaRecorderRef.current = null;
    setIsRecording(false);
  }

  function stopTestInternal() {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'stop' }));
    }
    wsRef.current?.close();
    wsRef.current = null;
    stopRecordingInternal();
    audioQueueRef.current = [];
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
  }

  const startTest = useCallback((config: object) => {
    const token = getToken();
    if (!token) {
      setErrorMessage('Not authenticated');
      setStatus('error');
      return;
    }

    configRef.current = config;
    setStatus('connecting');
    setTranscript([]);
    setErrorMessage('');
    setCallDuration(0);
    audioQueueRef.current = [];

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/calls/web`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    let receivingAudio = false;
    let audioChunks: ArrayBuffer[] = [];

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'auth', token }));
    };

    ws.onmessage = (event) => {
      if (event.data instanceof Blob) {
        event.data.arrayBuffer().then((buf) => {
          if (receivingAudio) {
            audioChunks.push(buf);
          }
        });
        return;
      }

      try {
        const msg = JSON.parse(event.data);

        switch (msg.type) {
          case 'status':
            if (msg.status === 'ready') {
              // Send inline assistantConfig instead of assistantId
              ws.send(JSON.stringify({ type: 'start', assistantConfig: configRef.current }));
            }
            break;
          case 'call_started':
            setStatus('active');
            break;
          case 'user_transcript':
            setTranscript((prev) => [...prev, { role: 'user', content: msg.text }]);
            break;
          case 'assistant_message':
            setTranscript((prev) => [...prev, { role: 'assistant', content: msg.text }]);
            if (msg.hasAudio) {
              receivingAudio = true;
              audioChunks = [];
            }
            break;
          case 'audio_end':
            receivingAudio = false;
            for (const chunk of audioChunks) {
              audioQueueRef.current.push(chunk);
            }
            audioChunks = [];
            playAudioQueue();
            break;
          case 'processing':
            if (msg.status === 'started') {
              setStatus('processing');
            } else {
              setStatus('active');
            }
            break;
          case 'call_ended':
          case 'call_ending':
            setStatus('ended');
            stopRecordingInternal();
            break;
          case 'error':
            setErrorMessage(msg.message);
            if (msg.code === 'UNAUTHORIZED') {
              setStatus('error');
            }
            break;
        }
      } catch {
        // Non-JSON message
      }
    };

    ws.onclose = () => {
      setStatus((prev) => {
        if (prev !== 'ended' && prev !== 'idle') return 'ended';
        return prev;
      });
      stopRecordingInternal();
    };

    ws.onerror = () => {
      setErrorMessage('WebSocket connection failed');
      setStatus('error');
    };
  }, [playAudioQueue]);

  const endTest = useCallback(() => {
    stopTestInternal();
    setStatus('ended');
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true },
      });
      mediaStreamRef.current = stream;

      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          e.data.arrayBuffer().then((buf) => {
            wsRef.current?.send(buf);
          });
        }
      };

      recorder.start(250);
      setIsRecording(true);
    } catch {
      setErrorMessage('Microphone access denied');
    }
  }, []);

  const sendEndTurn = useCallback(() => {
    stopRecordingInternal();
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'end_turn' }));
    }
  }, []);

  const reset = useCallback(() => {
    setStatus('idle');
    setTranscript([]);
    setErrorMessage('');
    setCallDuration(0);
  }, []);

  return {
    status,
    transcript,
    callDuration,
    errorMessage,
    isRecording,
    startTest,
    endTest,
    startRecording,
    sendEndTurn,
    reset,
  };
}
