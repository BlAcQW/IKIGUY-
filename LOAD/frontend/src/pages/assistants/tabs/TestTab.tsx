import { useState, useRef, useCallback, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
  Volume2, Mic, MicOff, Play, Square, Loader2, AudioLines, RefreshCw,
  Phone, Bot, User, AlertCircle, RotateCcw,
} from 'lucide-react';
import { synthesizeTts, transcribeStt, chatWithAssistant } from '@/lib/api';
import { useVoiceTest } from '@/hooks/useVoiceTest';
import { toast } from 'sonner';
import type { AssistantForm } from '../hooks/useAssistantEditor';
import { buildPayload } from '../hooks/useAssistantEditor';

interface TestTabProps {
  form: AssistantForm;
  assistantId?: string;
}

// ---------------------------------------------------------------------------
// TTS Panel
// ---------------------------------------------------------------------------

function TtsPanel({ form }: { form: AssistantForm }) {
  const [text, setText] = useState('Hello! This is a test of the text to speech system.');
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  async function handleSpeak() {
    if (!text.trim()) return;
    setLoading(true);
    setAudioUrl(null);
    setDurationMs(null);

    const start = performance.now();
    try {
      const blob = await synthesizeTts({
        text: text.trim(),
        provider: form.voiceProvider,
        voiceId: form.voiceId || undefined,
        speed: form.speed,
      });

      setDurationMs(Math.round(performance.now() - start));
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);

      // Auto-play
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        audioRef.current = null;
      };
      await audio.play();
    } catch (err) {
      toast.error('TTS failed', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  }

  function handleStop() {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-foreground">
        <Volume2 size={15} className="text-primary" />
        Text-to-Speech
      </div>
      <p className="text-xs text-muted-foreground">
        Using <span className="font-mono text-foreground/80">{form.voiceProvider}</span> / <span className="font-mono text-foreground/80">{form.voiceId || 'default'}</span> at {form.speed}x speed
      </p>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={3}
        className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
        placeholder="Enter text to synthesize..."
      />
      <div className="flex items-center gap-2">
        <Button
          onClick={handleSpeak}
          disabled={loading || !text.trim()}
          size="sm"
          className="gap-1.5"
        >
          {loading ? <Loader2 size={13} className="animate-spin" /> : <Play size={13} />}
          {loading ? 'Synthesizing...' : 'Speak'}
        </Button>
        <Button
          onClick={handleStop}
          variant="ghost"
          size="sm"
          className="gap-1.5"
          disabled={!audioRef.current}
        >
          <Square size={13} />
          Stop
        </Button>
        {durationMs !== null && (
          <span className="text-xs text-muted-foreground ml-auto">
            {durationMs}ms latency
          </span>
        )}
      </div>
      {audioUrl && (
        <audio controls src={audioUrl} className="w-full h-8 mt-1" />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// STT Panel
// ---------------------------------------------------------------------------

function SttPanel({ form }: { form: AssistantForm }) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [loading, setLoading] = useState(false);
  const [durationMs, setDurationMs] = useState<number | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  async function startRecording() {
    setTranscript('');
    setDurationMs(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];

      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setLoading(true);

        const start = performance.now();
        try {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
          const text = await transcribeStt(
            blob,
            'audio.webm',
            form.transcriberProvider,
          );
          setDurationMs(Math.round(performance.now() - start));
          setTranscript(text || '(no speech detected)');
        } catch (err) {
          toast.error('STT failed', {
            description: err instanceof Error ? err.message : 'Unknown error',
          });
        } finally {
          setLoading(false);
        }
      };

      mediaRecorderRef.current = mr;
      mr.start();
      setIsRecording(true);
    } catch (err) {
      toast.error('Microphone access denied', {
        description: 'Allow microphone access in your browser settings.',
      });
    }
  }

  function stopRecording() {
    const mr = mediaRecorderRef.current;
    if (mr && mr.state !== 'inactive') {
      mr.stop();
    }
    setIsRecording(false);
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-foreground">
        <Mic size={15} className="text-primary" />
        Speech-to-Text
      </div>
      <p className="text-xs text-muted-foreground">
        Using <span className="font-mono text-foreground/80">{form.transcriberProvider}</span> / <span className="font-mono text-foreground/80">{form.transcriberModel}</span>
      </p>
      <div className="flex items-center gap-2">
        <Button
          onClick={isRecording ? stopRecording : startRecording}
          variant={isRecording ? 'destructive' : 'default'}
          size="sm"
          className="gap-1.5"
          disabled={loading}
        >
          {loading ? (
            <Loader2 size={13} className="animate-spin" />
          ) : isRecording ? (
            <MicOff size={13} />
          ) : (
            <Mic size={13} />
          )}
          {loading ? 'Transcribing...' : isRecording ? 'Stop Recording' : 'Record'}
        </Button>
        {isRecording && (
          <span className="flex items-center gap-1.5 text-xs text-destructive animate-pulse">
            <span className="w-2 h-2 rounded-full bg-destructive" />
            Recording...
          </span>
        )}
        {durationMs !== null && !isRecording && (
          <span className="text-xs text-muted-foreground ml-auto">
            {durationMs}ms latency
          </span>
        )}
      </div>
      {transcript && (
        <div className="rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm">
          {transcript}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Voice Loop Panel
// ---------------------------------------------------------------------------

function VoiceLoopPanel({ form, assistantId }: { form: AssistantForm; assistantId?: string }) {
  const [phase, setPhase] = useState<'idle' | 'recording' | 'transcribing' | 'thinking' | 'speaking'>('idle');
  const [transcript, setTranscript] = useState('');
  const [reply, setReply] = useState('');
  const [history, setHistory] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
  }, []);

  async function startLoop() {
    if (!assistantId) {
      toast.error('Save the assistant first to use voice loop.');
      return;
    }

    stopAudio();
    setTranscript('');
    setReply('');
    setPhase('recording');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];

      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        processRecording();
      };

      mediaRecorderRef.current = mr;
      mr.start();
    } catch {
      toast.error('Microphone access denied');
      setPhase('idle');
    }
  }

  function stopRecording() {
    const mr = mediaRecorderRef.current;
    if (mr && mr.state !== 'inactive') {
      mr.stop();
    }
  }

  async function processRecording() {
    // 1. STT
    setPhase('transcribing');
    let userText: string;
    try {
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
      userText = await transcribeStt(blob, 'audio.webm', form.transcriberProvider);
      if (!userText.trim()) {
        toast.info('No speech detected. Try again.');
        setPhase('idle');
        return;
      }
      setTranscript(userText);
    } catch (err) {
      toast.error('STT failed', { description: err instanceof Error ? err.message : 'Unknown error' });
      setPhase('idle');
      return;
    }

    // 2. LLM (agent chat)
    setPhase('thinking');
    const updatedHistory = [...history, { role: 'user' as const, content: userText }];
    let assistantText: string;
    try {
      const result = await chatWithAssistant(assistantId!, updatedHistory);
      assistantText = result.data.message;
      setReply(assistantText);
      setHistory([...updatedHistory, { role: 'assistant', content: assistantText }]);
    } catch (err) {
      toast.error('Agent chat failed', { description: err instanceof Error ? err.message : 'Unknown error' });
      setPhase('idle');
      return;
    }

    // 3. TTS
    setPhase('speaking');
    try {
      const blob = await synthesizeTts({
        text: assistantText,
        provider: form.voiceProvider,
        voiceId: form.voiceId || undefined,
        speed: form.speed,
      });

      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        URL.revokeObjectURL(url);
        audioRef.current = null;
        setPhase('idle');
      };
      await audio.play();
    } catch (err) {
      toast.error('TTS failed', { description: err instanceof Error ? err.message : 'Unknown error' });
      setPhase('idle');
    }
  }

  function handleReset() {
    stopAudio();
    setHistory([]);
    setTranscript('');
    setReply('');
    setPhase('idle');
  }

  const phaseLabels: Record<string, string> = {
    idle: 'Ready',
    recording: 'Listening...',
    transcribing: 'Transcribing...',
    thinking: 'Agent thinking...',
    speaking: 'Speaking...',
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-foreground">
        <AudioLines size={15} className="text-primary" />
        Voice Loop
        <span className="text-xs font-normal text-muted-foreground ml-1">
          Mic → STT → Agent → TTS → Speaker
        </span>
      </div>
      {!assistantId && (
        <p className="text-xs text-muted-foreground">
          Save the assistant first to use voice loop.
        </p>
      )}
      <div className="flex items-center gap-2">
        {phase === 'idle' ? (
          <Button
            onClick={startLoop}
            disabled={!assistantId}
            size="sm"
            className="gap-1.5"
          >
            <Mic size={13} />
            Start Voice Loop
          </Button>
        ) : phase === 'recording' ? (
          <Button
            onClick={stopRecording}
            variant="destructive"
            size="sm"
            className="gap-1.5"
          >
            <Square size={13} />
            Stop & Send
          </Button>
        ) : (
          <Button disabled size="sm" className="gap-1.5">
            <Loader2 size={13} className="animate-spin" />
            {phaseLabels[phase]}
          </Button>
        )}

        {history.length > 0 && (
          <Button
            onClick={handleReset}
            variant="ghost"
            size="sm"
            className="gap-1.5"
          >
            <RefreshCw size={13} />
            Reset
          </Button>
        )}

        {phase === 'recording' && (
          <span className="flex items-center gap-1.5 text-xs text-destructive animate-pulse">
            <span className="w-2 h-2 rounded-full bg-destructive" />
            Recording...
          </span>
        )}
      </div>

      {/* Status / Results */}
      {(transcript || reply) && (
        <div className="space-y-2 pt-1">
          {transcript && (
            <div className="rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm">
              <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">You said</span>
              <p className="mt-0.5">{transcript}</p>
            </div>
          )}
          {reply && (
            <div className="rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-sm">
              <span className="text-[10px] font-medium text-primary/60 uppercase tracking-wider">Agent replied</span>
              <p className="mt-0.5">{reply}</p>
            </div>
          )}
        </div>
      )}

      {/* Conversation History */}
      {history.length > 2 && (
        <details className="text-xs text-muted-foreground">
          <summary className="cursor-pointer hover:text-foreground">
            Conversation history ({history.length} messages)
          </summary>
          <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
            {history.map((msg, i) => (
              <div key={i} className="flex gap-2">
                <span className={`font-medium shrink-0 ${msg.role === 'user' ? 'text-blue-400' : 'text-green-400'}`}>
                  {msg.role === 'user' ? 'You:' : 'Agent:'}
                </span>
                <span className="text-foreground/80 truncate">{msg.content}</span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// WebSocket Voice Call Panel (uses inline config — no save required)
// ---------------------------------------------------------------------------

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function WebSocketCallPanel({ form }: { form: AssistantForm }) {
  const {
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
  } = useVoiceTest();

  const bottomRef = useRef<HTMLDivElement>(null);
  const [holdingMic, setHoldingMic] = useState(false);

  // Auto-scroll transcript
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  // Spacebar push-to-talk
  useEffect(() => {
    if (status !== 'active' && status !== 'processing') return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.code === 'Space' && !e.repeat && !holdingMic && status === 'active') {
        // Don't capture space when typing in an input
        const tag = (e.target as HTMLElement)?.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA') return;
        e.preventDefault();
        setHoldingMic(true);
        startRecording();
      }
    }

    function handleKeyUp(e: KeyboardEvent) {
      if (e.code === 'Space' && holdingMic) {
        e.preventDefault();
        setHoldingMic(false);
        sendEndTurn();
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [status, holdingMic, startRecording, sendEndTurn]);

  const handleStartTest = useCallback(() => {
    const payload = buildPayload(form);
    const assistantConfig = {
      name: payload.name,
      model: {
        provider: payload.model.provider,
        model: payload.model.model,
        temperature: payload.model.temperature,
        maxTokens: payload.model.maxTokens,
        systemPrompt: payload.model.systemPrompt,
      },
      voice: {
        provider: payload.voice.provider,
        voiceId: payload.voice.voiceId,
        speed: payload.voice.speed,
      },
      transcriber: {
        provider: payload.transcriber.provider,
        model: payload.transcriber.model,
        language: payload.transcriber.language,
      },
      firstMessage: payload.firstMessage,
      endCallPhrases: payload.endCallPhrases,
    };
    startTest(assistantConfig);
  }, [form, startTest]);

  const handleMicDown = useCallback(() => {
    if (status !== 'active') return;
    setHoldingMic(true);
    startRecording();
  }, [status, startRecording]);

  const handleMicUp = useCallback(() => {
    if (!holdingMic) return;
    setHoldingMic(false);
    sendEndTurn();
  }, [holdingMic, sendEndTurn]);

  const isIdle = status === 'idle' || status === 'ended' || status === 'error';

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
          <Phone size={15} className="text-primary" />
          Voice Call Test
          <span className="text-xs font-normal text-muted-foreground ml-1">
            No save required
          </span>
        </div>
        {(status === 'active' || status === 'processing') && (
          <span className="text-xs font-mono text-muted-foreground">
            {formatDuration(callDuration)}
          </span>
        )}
      </div>

      {/* Transcript area */}
      <div className="h-[220px] bg-background rounded-lg border border-border overflow-y-auto scrollbar-thin p-3 space-y-2">
        {transcript.length === 0 && isIdle && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-9 h-9 rounded-full bg-muted/50 flex items-center justify-center mb-2">
              <Mic size={16} className="text-muted-foreground/40" />
            </div>
            <p className="text-xs text-muted-foreground">
              Start a voice test using current unsaved settings
            </p>
          </div>
        )}

        {transcript.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`w-5 h-5 rounded-md flex items-center justify-center shrink-0 mt-0.5 ${
                msg.role === 'user'
                  ? 'bg-primary/10 text-primary'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {msg.role === 'user' ? <User size={10} /> : <Bot size={10} />}
            </div>
            <div
              className={`max-w-[80%] px-2.5 py-1.5 rounded-lg text-xs leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground rounded-br-sm'
                  : 'bg-muted text-foreground rounded-bl-sm'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {status === 'processing' && (
          <div className="flex gap-2">
            <div className="w-5 h-5 rounded-md flex items-center justify-center shrink-0 bg-muted text-muted-foreground">
              <Bot size={10} />
            </div>
            <div className="bg-muted rounded-lg rounded-bl-sm px-2.5 py-1.5">
              <Loader2 size={12} className="animate-spin text-muted-foreground" />
            </div>
          </div>
        )}

        {status === 'connecting' && (
          <div className="flex items-center justify-center h-full gap-2 text-xs text-muted-foreground">
            <Loader2 size={14} className="animate-spin" />
            Connecting...
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Error display */}
      {errorMessage && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-destructive/10 border border-destructive/20">
          <AlertCircle size={12} className="text-destructive shrink-0" />
          <p className="text-xs text-destructive">{errorMessage}</p>
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center justify-center gap-3">
        {isIdle ? (
          <>
            <Button
              onClick={handleStartTest}
              size="sm"
              className="gap-1.5"
            >
              <Play size={13} />
              Start Test Call
            </Button>
            {status === 'ended' && (
              <Button onClick={reset} variant="ghost" size="sm" className="gap-1.5">
                <RotateCcw size={13} />
                Reset
              </Button>
            )}
          </>
        ) : (
          <>
            <Button
              variant={isRecording ? 'destructive' : 'secondary'}
              size="icon"
              className="h-11 w-11 rounded-full"
              onMouseDown={handleMicDown}
              onMouseUp={handleMicUp}
              onMouseLeave={() => {
                if (holdingMic) {
                  setHoldingMic(false);
                  sendEndTurn();
                }
              }}
              disabled={status !== 'active'}
            >
              {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
            </Button>

            <Button
              onClick={endTest}
              variant="destructive"
              size="sm"
              className="gap-1.5"
            >
              <Square size={12} />
              End Test
            </Button>
          </>
        )}
      </div>

      {/* Push-to-talk hint */}
      {(status === 'active' || status === 'processing') && (
        <p className="text-center text-[10px] text-muted-foreground/60">
          Hold mic button or spacebar to talk, release to send
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Test Tab
// ---------------------------------------------------------------------------

export function TestTab({ form, assistantId }: TestTabProps) {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-1">Pipeline Testing</h3>
        <p className="text-xs text-muted-foreground">
          Test individual pipeline stages or run a full voice call without leaving the editor.
        </p>
      </div>

      {/* WebSocket Voice Call (uses current unsaved settings) */}
      <div className="rounded-xl border border-primary/20 bg-card p-4">
        <WebSocketCallPanel form={form} />
      </div>

      {/* TTS Panel */}
      <div className="rounded-xl border border-border bg-card p-4">
        <TtsPanel form={form} />
      </div>

      {/* STT Panel */}
      <div className="rounded-xl border border-border bg-card p-4">
        <SttPanel form={form} />
      </div>

      {/* Voice Loop Panel */}
      <div className="rounded-xl border border-border bg-card p-4">
        <VoiceLoopPanel form={form} assistantId={assistantId} />
      </div>
    </div>
  );
}
