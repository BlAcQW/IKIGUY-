import { useEffect, useState, useRef, useCallback } from 'react';
import { listAssistants } from '../lib/api';
import { getToken } from '../lib/auth';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Mic, MicOff, PhoneOff, Loader2, Headphones, Bot, User } from 'lucide-react';
import { toast } from 'sonner';

interface Assistant {
  id: string;
  name: string;
  voice: { voiceId: string };
  firstMessage: string | null;
}

interface TranscriptEntry {
  role: 'user' | 'assistant';
  content: string;
}

type CallStatus = 'idle' | 'connecting' | 'active' | 'processing' | 'ended' | 'error';

function Waveform({ active, className }: { active: boolean; className?: string }) {
  const bars = 16;
  return (
    <div className={`flex items-center justify-center gap-[3px] h-16 ${className ?? ''}`}>
      {Array.from({ length: bars }).map((_, i) => (
        <div
          key={i}
          className={`w-[3px] rounded-full transition-all duration-300 ${
            active
              ? 'bg-primary waveform-bar'
              : 'bg-muted-foreground/15 h-2'
          }`}
          style={
            active
              ? {
                  height: '100%',
                  animationDelay: `${(i * 67) % 500}ms`,
                  animationDuration: `${600 + (i * 37) % 400}ms`,
                }
              : undefined
          }
        />
      ))}
    </div>
  );
}

function PulseRings({ active }: { active: boolean }) {
  if (!active) return null;
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div className="absolute w-32 h-32 rounded-full border border-primary/20 animate-pulse-ring" />
      <div className="absolute w-32 h-32 rounded-full border border-primary/10 animate-pulse-ring" style={{ animationDelay: '0.5s' }} />
      <div className="absolute w-32 h-32 rounded-full border border-primary/5 animate-pulse-ring" style={{ animationDelay: '1s' }} />
    </div>
  );
}

export function WebCallPage() {
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [selectedAssistantId, setSelectedAssistantId] = useState('');
  const [callStatus, setCallStatus] = useState<CallStatus>('idle');
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [callId, setCallId] = useState('');
  const [loadingAssistants, setLoadingAssistants] = useState(true);
  const [callDuration, setCallDuration] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const durationIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const result = await listAssistants();
        setAssistants(result.data);
        if (result.data.length > 0) {
          setSelectedAssistantId(result.data[0].id);
        }
      } catch {
        toast.error('Failed to load assistants');
      } finally {
        setLoadingAssistants(false);
      }
    }
    load();
  }, []);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  useEffect(() => {
    return () => {
      stopCall();
    };
  }, []);

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

  function startCall() {
    if (!selectedAssistantId) {
      setErrorMessage('Select an assistant first');
      return;
    }

    const token = getToken();
    if (!token) {
      setErrorMessage('Not authenticated');
      return;
    }

    setCallStatus('connecting');
    setTranscript([]);
    setErrorMessage('');
    setCallDuration(0);
    audioQueueRef.current = [];

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/calls/web?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    let receivingAudio = false;
    let audioChunks: ArrayBuffer[] = [];

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'start', assistantId: selectedAssistantId }));
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
            break;
          case 'call_started':
            setCallStatus('active');
            setCallId(msg.callId);
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
              setCallStatus('processing');
            } else {
              setCallStatus('active');
            }
            break;
          case 'call_ended':
          case 'call_ending':
            setCallStatus('ended');
            stopRecording();
            break;
          case 'error':
            setErrorMessage(msg.message);
            if (msg.code === 'UNAUTHORIZED') {
              setCallStatus('error');
            }
            break;
        }
      } catch {
        // Non-JSON message
      }
    };

    ws.onclose = () => {
      if (callStatus !== 'ended' && callStatus !== 'idle') {
        setCallStatus('ended');
      }
      stopRecording();
    };

    ws.onerror = () => {
      setErrorMessage('WebSocket connection failed');
      setCallStatus('error');
    };
  }

  async function startRecording() {
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
  }

  function stopRecording() {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
    mediaStreamRef.current = null;
    mediaRecorderRef.current = null;
    setIsRecording(false);
  }

  function sendEndTurn() {
    stopRecording();
    wsRef.current?.send(JSON.stringify({ type: 'end_turn' }));
  }

  function stopCall() {
    wsRef.current?.send(JSON.stringify({ type: 'stop' }));
    wsRef.current?.close();
    wsRef.current = null;
    stopRecording();
    audioQueueRef.current = [];
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setCallStatus('idle');
  }

  const isInCall = callStatus === 'active' || callStatus === 'processing' || callStatus === 'connecting';
  const selectedAssistant = assistants.find((a) => a.id === selectedAssistantId);

  function formatCallDuration(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  return (
    <div className="max-w-3xl mx-auto animate-slide-up">
      {/* Hero Header */}
      <div className="text-center mb-8">
        <h1 className="text-2xl font-display font-bold tracking-tight">Web Call</h1>
        <p className="text-sm text-muted-foreground mt-1.5">Test your assistant with a browser-based voice call</p>
      </div>

      {/* Idle State — Assistant Selection */}
      {callStatus === 'idle' && (
        <Card className="mb-6 overflow-hidden">
          <CardContent className="p-0">
            {/* Visual hero area */}
            <div className="relative py-12 px-6 flex flex-col items-center bg-gradient-to-b from-primary/[0.03] to-transparent">
              <div className="absolute inset-0 dot-grid opacity-20" />

              <div className="relative mb-6">
                <div className="w-20 h-20 rounded-3xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                  <Headphones size={32} className="text-primary" />
                </div>
                <div className="absolute -inset-4 rounded-[28px] border border-primary/5 animate-pulse" />
              </div>

              <h2 className="text-lg font-display font-semibold mb-1 relative">Ready to call</h2>
              <p className="text-sm text-muted-foreground relative">Select an assistant and start a voice conversation</p>
            </div>

            {/* Assistant selector */}
            <div className="p-6 pt-0 -mt-2">
              <label className="block text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider">Assistant</label>
              {loadingAssistants ? (
                <Skeleton className="h-11 w-full mb-4" />
              ) : (
                <Select value={selectedAssistantId} onValueChange={setSelectedAssistantId}>
                  <SelectTrigger className="mb-4 h-11 bg-background">
                    <SelectValue placeholder="Choose an assistant" />
                  </SelectTrigger>
                  <SelectContent>
                    {assistants.length === 0 ? (
                      <div className="px-2 py-4 text-sm text-muted-foreground text-center">No assistants available</div>
                    ) : (
                      assistants.map((a) => (
                        <SelectItem key={a.id} value={a.id}>
                          <div className="flex items-center gap-2">
                            <Bot size={14} className="text-muted-foreground" />
                            {a.name}
                          </div>
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              )}
              <Button
                onClick={startCall}
                disabled={!selectedAssistantId}
                className="w-full h-12 text-base font-semibold shadow-glow hover:shadow-glow-lg transition-shadow"
                size="lg"
              >
                <Headphones size={18} className="mr-2" />
                Start Call
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {errorMessage && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg mb-4 text-sm flex items-start gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-destructive mt-1.5 shrink-0" />
          {errorMessage}
        </div>
      )}

      {/* Active Call Interface */}
      {isInCall && (
        <Card className="mb-6 overflow-hidden">
          <CardContent className="p-0">
            {/* Call visualization area */}
            <div className="relative py-10 px-6 flex flex-col items-center bg-gradient-to-b from-primary/[0.04] to-transparent">
              <div className="absolute inset-0 dot-grid opacity-15" />

              {/* Pulse rings behind the orb */}
              <div className="relative mb-6">
                <PulseRings active={callStatus === 'active' && isRecording} />
                <div className={`relative z-10 w-20 h-20 rounded-3xl flex items-center justify-center transition-all duration-500 ${
                  isRecording
                    ? 'bg-primary/20 border-2 border-primary shadow-glow-lg'
                    : callStatus === 'processing'
                    ? 'bg-chart-3/10 border border-chart-3/30'
                    : 'bg-primary/10 border border-primary/20'
                }`}>
                  {callStatus === 'connecting' ? (
                    <Loader2 size={28} className="animate-spin text-primary" />
                  ) : callStatus === 'processing' ? (
                    <Loader2 size={28} className="animate-spin text-chart-3" />
                  ) : isRecording ? (
                    <Mic size={28} className="text-primary" />
                  ) : (
                    <Headphones size={28} className="text-primary" />
                  )}
                </div>
              </div>

              {/* Waveform */}
              <Waveform active={isRecording || callStatus === 'processing'} className="mb-4" />

              {/* Status */}
              <div className="flex items-center gap-3 mb-1 relative">
                <Badge variant={callStatus === 'active' ? 'default' : 'secondary'} className="text-xs px-2.5">
                  {callStatus === 'connecting' ? 'Connecting' : callStatus === 'active' ? 'Active' : 'Processing'}
                </Badge>
                <span className="text-sm font-mono text-muted-foreground">{formatCallDuration(callDuration)}</span>
              </div>
              {callId && (
                <span className="text-[11px] text-muted-foreground/60 font-mono relative">
                  {callId.slice(0, 8)}...
                </span>
              )}
              {selectedAssistant && (
                <span className="text-xs text-muted-foreground mt-1 relative">
                  Talking to {selectedAssistant.name}
                </span>
              )}
            </div>

            {/* Controls */}
            <div className="p-6 flex gap-3 justify-center border-t border-border/50">
              {!isRecording ? (
                <Button
                  onClick={startRecording}
                  disabled={callStatus !== 'active'}
                  size="lg"
                  className="rounded-2xl px-8 h-12 shadow-glow hover:shadow-glow-lg transition-shadow font-semibold"
                >
                  <Mic size={18} className="mr-2" />
                  Hold to Talk
                </Button>
              ) : (
                <Button
                  onClick={sendEndTurn}
                  variant="destructive"
                  size="lg"
                  className="rounded-2xl px-8 h-12 animate-pulse-glow font-semibold"
                >
                  <MicOff size={18} className="mr-2" />
                  Send
                </Button>
              )}
              <Button
                onClick={stopCall}
                variant="outline"
                size="lg"
                className="rounded-2xl px-8 h-12 hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30"
              >
                <PhoneOff size={18} className="mr-2" />
                End Call
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Call Ended */}
      {callStatus === 'ended' && (
        <Card className="mb-6">
          <CardContent className="p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4">
              <PhoneOff size={24} className="text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground mb-1">Call ended</p>
            <p className="text-xs text-muted-foreground/60 font-mono mb-5">{formatCallDuration(callDuration)}</p>
            <Button onClick={() => { setCallStatus('idle'); setTranscript([]); setErrorMessage(''); setCallDuration(0); }} className="font-semibold">
              New Call
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Transcript */}
      {transcript.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-5">Transcript</h2>
            <div className="space-y-4 max-h-[400px] overflow-y-auto scrollbar-thin pr-2">
              {transcript.map((entry, i) => (
                <div
                  key={i}
                  className={`flex gap-3 ${entry.role === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                    entry.role === 'user'
                      ? 'bg-primary/10 text-primary'
                      : 'bg-muted text-muted-foreground'
                  }`}>
                    {entry.role === 'user' ? <User size={13} /> : <Bot size={13} />}
                  </div>
                  <div
                    className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                      entry.role === 'user'
                        ? 'bg-primary text-primary-foreground rounded-br-lg'
                        : 'bg-muted text-foreground rounded-bl-lg'
                    }`}
                  >
                    {entry.content}
                  </div>
                </div>
              ))}
              <div ref={transcriptEndRef} />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
