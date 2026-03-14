import { useEffect, useState, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { listAssistants } from '../lib/api';
import { useWebRTC } from '../hooks/useWebRTC';
import { useWebSocketCall } from '../hooks/useWebSocketCall';
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
import { Mic, MicOff, PhoneOff, Loader2, Headphones, Bot, User, Radio, Wifi, AlertTriangle, Settings } from 'lucide-react';
import { toast } from 'sonner';

interface Assistant {
  id: string;
  name: string;
  voice: { voiceId: string };
  firstMessage: string | null;
}

type CallMode = 'webrtc' | 'classic';

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
  const [searchParams] = useSearchParams();
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [selectedAssistantId, setSelectedAssistantId] = useState('');
  const [loadingAssistants, setLoadingAssistants] = useState(true);
  const [callMode, setCallMode] = useState<CallMode>('webrtc');

  const transcriptEndRef = useRef<HTMLDivElement>(null);

  // ── Hooks for each mode ──
  const webrtc = useWebRTC();
  const wsCall = useWebSocketCall();

  // Determine which state to use based on mode
  const isWebRTC = callMode === 'webrtc';
  const callStatus = isWebRTC ? webrtc.callStatus : wsCall.callStatus;
  const transcript = isWebRTC ? webrtc.transcript : wsCall.transcript;
  const callId = isWebRTC ? webrtc.callId : wsCall.callId;
  const callDuration = isWebRTC ? webrtc.callDuration : wsCall.callDuration;

  useEffect(() => {
    async function load() {
      try {
        const result = await listAssistants();
        setAssistants(result.data);
        const assistantParam = searchParams.get('assistant');
        if (assistantParam && result.data.some((a: Assistant) => a.id === assistantParam)) {
          setSelectedAssistantId(assistantParam);
        } else if (result.data.length > 0) {
          setSelectedAssistantId(result.data[0].id);
        }
      } catch {
        toast.error('Failed to load assistants');
      } finally {
        setLoadingAssistants(false);
      }
    }
    load();
  }, [searchParams]);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  // ── Unified call actions ──

  function handleStartCall() {
    if (!selectedAssistantId) return;

    if (isWebRTC) {
      webrtc.startCall(selectedAssistantId);
    } else {
      wsCall.startCall(selectedAssistantId);
    }
  }

  function handleEndCall() {
    if (isWebRTC) {
      webrtc.endCall();
    } else {
      wsCall.endCall();
    }
  }

  function handleNewCall() {
    if (isWebRTC) {
      webrtc.reset();
    } else {
      wsCall.reset();
    }
  }

  // Derive the displayed error
  const displayedError = isWebRTC ? webrtc.errorMessage : wsCall.errorMessage;
  const isProviderError = isWebRTC && webrtc.errorCode === 'PROVIDER_NOT_CONFIGURED';
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

            {/* Assistant selector + mode toggle */}
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

              {/* Mode toggle */}
              <div className="flex items-center gap-2 mb-4">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Mode</label>
                <div className="flex bg-muted rounded-lg p-0.5 ml-auto">
                  <button
                    onClick={() => setCallMode('webrtc')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      callMode === 'webrtc'
                        ? 'bg-background text-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    <Radio size={12} />
                    WebRTC
                  </button>
                  <button
                    onClick={() => setCallMode('classic')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      callMode === 'classic'
                        ? 'bg-background text-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    <Wifi size={12} />
                    Classic
                  </button>
                </div>
              </div>

              <Button
                onClick={handleStartCall}
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

      {/* Error banner */}
      {displayedError && callStatus !== 'error' && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg mb-4 text-sm flex items-start gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-destructive mt-1.5 shrink-0" />
          {displayedError}
        </div>
      )}

      {/* Error State Card */}
      {callStatus === 'error' && (
        <Card className="mb-6 overflow-hidden border-destructive/20">
          <CardContent className="p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-destructive/10 flex items-center justify-center mx-auto mb-4">
              <AlertTriangle size={24} className="text-destructive" />
            </div>
            <h3 className="text-base font-display font-semibold mb-1.5">Call Failed</h3>
            <p className="text-sm text-muted-foreground mb-4 max-w-md mx-auto">
              {displayedError || 'An unexpected error occurred while starting the call.'}
            </p>
            {isProviderError && (
              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg px-4 py-3 mb-4 text-left max-w-md mx-auto">
                <div className="flex items-center gap-2 mb-1">
                  <Settings size={14} className="text-yellow-500" />
                  <span className="text-xs font-semibold text-yellow-500">Provider Not Configured</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  The voice provider API key is missing. Add it in your environment configuration and restart the server.
                </p>
              </div>
            )}
            <Button onClick={handleNewCall} className="font-semibold">
              Try Again
            </Button>
          </CardContent>
        </Card>
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
                <PulseRings active={callStatus === 'active' && (isWebRTC ? !webrtc.isMuted : wsCall.isRecording)} />
                <div className={`relative z-10 w-20 h-20 rounded-3xl flex items-center justify-center transition-all duration-500 ${
                  (isWebRTC ? !webrtc.isMuted : wsCall.isRecording) && callStatus === 'active'
                    ? 'bg-primary/20 border-2 border-primary shadow-glow-lg'
                    : callStatus === 'processing'
                    ? 'bg-chart-3/10 border border-chart-3/30'
                    : 'bg-primary/10 border border-primary/20'
                }`}>
                  {callStatus === 'connecting' ? (
                    <Loader2 size={28} className="animate-spin text-primary" />
                  ) : callStatus === 'processing' ? (
                    <Loader2 size={28} className="animate-spin text-chart-3" />
                  ) : (isWebRTC ? !webrtc.isMuted : wsCall.isRecording) ? (
                    <Mic size={28} className="text-primary" />
                  ) : (
                    <Headphones size={28} className="text-primary" />
                  )}
                </div>
              </div>

              {/* Waveform */}
              <Waveform active={(isWebRTC ? !webrtc.isMuted && callStatus === 'active' : wsCall.isRecording) || callStatus === 'processing'} className="mb-4" />

              {/* Status */}
              <div className="flex items-center gap-3 mb-1 relative">
                <Badge variant={callStatus === 'active' ? 'default' : 'secondary'} className="text-xs px-2.5">
                  {callStatus === 'connecting' ? 'Connecting' : callStatus === 'active' ? 'Active' : 'Processing'}
                </Badge>
                <Badge variant="outline" className="text-[10px] px-2 gap-1">
                  {isWebRTC ? <Radio size={10} /> : <Wifi size={10} />}
                  {isWebRTC ? 'WebRTC' : 'Classic'}
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
              {isWebRTC ? (
                /* WebRTC mode: Mute toggle instead of record buttons */
                <Button
                  onClick={webrtc.toggleMute}
                  disabled={callStatus !== 'active'}
                  variant={webrtc.isMuted ? 'destructive' : 'default'}
                  size="lg"
                  className={`rounded-2xl px-8 h-12 font-semibold ${
                    !webrtc.isMuted ? 'shadow-glow hover:shadow-glow-lg transition-shadow' : ''
                  }`}
                >
                  {webrtc.isMuted ? (
                    <>
                      <MicOff size={18} className="mr-2" />
                      Unmute
                    </>
                  ) : (
                    <>
                      <Mic size={18} className="mr-2" />
                      Mute
                    </>
                  )}
                </Button>
              ) : (
                /* Classic mode: Hold to Talk / Send buttons */
                !wsCall.isRecording ? (
                  <Button
                    onClick={wsCall.startRecording}
                    disabled={callStatus !== 'active'}
                    size="lg"
                    className="rounded-2xl px-8 h-12 shadow-glow hover:shadow-glow-lg transition-shadow font-semibold"
                  >
                    <Mic size={18} className="mr-2" />
                    Hold to Talk
                  </Button>
                ) : (
                  <Button
                    onClick={wsCall.sendEndTurn}
                    variant="destructive"
                    size="lg"
                    className="rounded-2xl px-8 h-12 animate-pulse-glow font-semibold"
                  >
                    <MicOff size={18} className="mr-2" />
                    Send
                  </Button>
                )
              )}
              <Button
                onClick={handleEndCall}
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
            <Button onClick={handleNewCall} className="font-semibold">
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
