import { useState, useEffect, useRef, useCallback } from 'react';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Play,
  Square,
  Upload,
  Mic,
  Trash2,
  Plus,
  X,
  Loader2,
} from 'lucide-react';
import { listVoices, cloneVoice, deleteVoice, previewVoice } from '@/lib/api';
import { toast } from 'sonner';

interface VoiceCard {
  voiceId: string;
  name: string;
  provider: string;
  category: string;
  labels: Record<string, string>;
  previewUrl?: string;
}

// Built-in voices for providers that don't have a list API
const BUILTIN_VOICES: VoiceCard[] = [
  { voiceId: 'alloy', name: 'Alloy', provider: 'openai', category: 'premade', labels: { gender: 'Neutral', accent: 'American', style: 'Balanced' } },
  { voiceId: 'echo', name: 'Echo', provider: 'openai', category: 'premade', labels: { gender: 'Male', accent: 'American', style: 'Warm' } },
  { voiceId: 'fable', name: 'Fable', provider: 'openai', category: 'premade', labels: { gender: 'Male', accent: 'British', style: 'Expressive' } },
  { voiceId: 'nova', name: 'Nova', provider: 'openai', category: 'premade', labels: { gender: 'Female', accent: 'American', style: 'Friendly' } },
  { voiceId: 'onyx', name: 'Onyx', provider: 'openai', category: 'premade', labels: { gender: 'Male', accent: 'American', style: 'Deep' } },
  { voiceId: 'shimmer', name: 'Shimmer', provider: 'openai', category: 'premade', labels: { gender: 'Female', accent: 'American', style: 'Clear' } },
  { voiceId: 'aura-asteria-en', name: 'Asteria', provider: 'deepgram', category: 'premade', labels: { gender: 'Female', accent: 'American', style: 'Professional' } },
  { voiceId: 'aura-luna-en', name: 'Luna', provider: 'deepgram', category: 'premade', labels: { gender: 'Female', accent: 'American', style: 'Warm' } },
  { voiceId: 'aura-orion-en', name: 'Orion', provider: 'deepgram', category: 'premade', labels: { gender: 'Male', accent: 'American', style: 'Authoritative' } },
  { voiceId: 'aura-arcas-en', name: 'Arcas', provider: 'deepgram', category: 'premade', labels: { gender: 'Male', accent: 'American', style: 'Confident' } },
  { voiceId: 'a0e99841-438c-4a64-b679-ae501e7d6091', name: 'Barbershop Man', provider: 'cartesia', category: 'premade', labels: { gender: 'Male', accent: 'American', style: 'Warm' } },
  { voiceId: '79a125e8-cd45-4c13-8a67-188112f4dd22', name: 'British Lady', provider: 'cartesia', category: 'premade', labels: { gender: 'Female', accent: 'British', style: 'Elegant' } },
  { voiceId: 'b7d50908-b17c-442d-ad8d-7c56e5dd3b37', name: 'California Girl', provider: 'cartesia', category: 'premade', labels: { gender: 'Female', accent: 'American', style: 'Casual' } },
  { voiceId: 'c45bc5ec-dc68-4feb-8829-6e6b2f236b73', name: 'Movieman', provider: 'cartesia', category: 'premade', labels: { gender: 'Male', accent: 'American', style: 'Dramatic' } },
];

const providerColors: Record<string, string> = {
  openai: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
  elevenlabs: 'bg-violet-500/10 text-violet-500 border-violet-500/20',
  deepgram: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  cartesia: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
};

const providerLabels: Record<string, string> = {
  openai: 'OpenAI',
  elevenlabs: 'ElevenLabs',
  deepgram: 'Deepgram',
  cartesia: 'Cartesia',
};

export function VoiceLibraryPage() {
  const [elevenLabsVoices, setElevenLabsVoices] = useState<VoiceCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [showCloneDialog, setShowCloneDialog] = useState(false);
  const [cloneName, setCloneName] = useState('');
  const [cloneFile, setCloneFile] = useState<File | null>(null);
  const [cloning, setCloning] = useState(false);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const loadVoices = useCallback(async () => {
    try {
      const result = await listVoices();
      setElevenLabsVoices(result.data);
    } catch {
      // ElevenLabs voices will just not show
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadVoices();
  }, [loadVoices]);

  const allVoices = [...elevenLabsVoices, ...BUILTIN_VOICES];
  const filteredVoices = filter === 'all'
    ? allVoices
    : filter === 'cloned'
      ? allVoices.filter((v) => v.category === 'cloned')
      : allVoices.filter((v) => v.provider === filter);

  const clonedVoices = allVoices.filter((v) => v.category === 'cloned');

  async function handleClone() {
    if (!cloneName || !cloneFile) return;
    setCloning(true);
    try {
      await cloneVoice(cloneName, '', cloneFile);
      toast.success(`Voice "${cloneName}" cloned successfully!`);
      setShowCloneDialog(false);
      setCloneName('');
      setCloneFile(null);
      loadVoices();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Cloning failed');
    } finally {
      setCloning(false);
    }
  }

  async function handleDelete(voiceId: string, name: string) {
    if (!confirm(`Delete cloned voice "${name}"?`)) return;
    try {
      await deleteVoice(voiceId);
      toast.success(`Voice "${name}" deleted`);
      loadVoices();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Delete failed');
    }
  }

  async function handlePreview(voice: VoiceCard) {
    // If already playing this voice, stop
    if (playingId === voice.voiceId) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      setPlayingId(null);
      return;
    }

    // Stop any current playback
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    setPreviewLoading(voice.voiceId);

    try {
      // Use ElevenLabs preview URL if available
      if (voice.previewUrl) {
        const audio = new Audio(voice.previewUrl);
        audioRef.current = audio;
        audio.onended = () => { setPlayingId(null); audioRef.current = null; };
        audio.onerror = () => { setPlayingId(null); audioRef.current = null; };
        setPlayingId(voice.voiceId);
        setPreviewLoading(null);
        await audio.play();
        return;
      }

      // Use our preview API
      const blob = await previewVoice(voice.provider, voice.voiceId);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        setPlayingId(null);
        audioRef.current = null;
        URL.revokeObjectURL(url);
      };
      audio.onerror = () => {
        setPlayingId(null);
        audioRef.current = null;
        URL.revokeObjectURL(url);
      };
      setPlayingId(voice.voiceId);
      setPreviewLoading(null);
      await audio.play();
    } catch {
      toast.error('Preview not available');
      setPreviewLoading(null);
      setPlayingId(null);
    }
  }

  return (
    <div className="animate-slide-up">
      <PageHeader
        title="Voice Library"
        subtitle="Browse voices, preview them, and clone your own"
      >
        <Button onClick={() => setShowCloneDialog(true)} size="sm">
          <Plus size={14} className="mr-1.5" />
          Clone My Voice
        </Button>
      </PageHeader>

      {/* Clone Dialog */}
      {showCloneDialog && (
        <div className="bg-card border border-border rounded-lg p-5 mb-6 animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Mic size={16} className="text-primary" />
              <h3 className="text-sm font-semibold">Clone Your Voice</h3>
            </div>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setShowCloneDialog(false)}>
              <X size={14} />
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mb-4">
            Upload a clear audio recording of your voice (30 seconds minimum, 1-2 minutes ideal).
            MP3, WAV, or M4A format. Your voice will be available as a custom voice in the assistant editor.
          </p>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="space-y-2">
              <Label className="text-xs">Voice Name</Label>
              <Input
                placeholder="e.g., My Voice"
                value={cloneName}
                onChange={(e) => setCloneName(e.target.value)}
                className="h-9"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs">Audio File</Label>
              <div className="relative">
                <Input
                  type="file"
                  accept="audio/*"
                  onChange={(e) => setCloneFile(e.target.files?.[0] ?? null)}
                  className="h-9 text-xs"
                />
              </div>
            </div>
          </div>
          {cloneFile && (
            <p className="text-xs text-muted-foreground mb-3">
              Selected: {cloneFile.name} ({(cloneFile.size / 1024 / 1024).toFixed(1)} MB)
            </p>
          )}
          <div className="flex gap-2">
            <Button
              onClick={handleClone}
              disabled={!cloneName || !cloneFile || cloning}
              size="sm"
            >
              {cloning ? (
                <>
                  <Loader2 size={14} className="mr-1.5 animate-spin" />
                  Cloning...
                </>
              ) : (
                <>
                  <Upload size={14} className="mr-1.5" />
                  Clone Voice
                </>
              )}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setShowCloneDialog(false)}>
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Cloned voices section */}
      {clonedVoices.length > 0 && (
        <div className="mb-8">
          <h2 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Mic size={14} className="text-primary" />
            Your Cloned Voices
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {clonedVoices.map((voice) => (
              <Card key={voice.voiceId} className="group border-primary/20 bg-primary/[0.02]">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-sm font-semibold">{voice.name}</h3>
                      <Badge variant="outline" className="text-[10px] mt-1 bg-primary/10 text-primary border-primary/20">
                        Cloned
                      </Badge>
                    </div>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => handlePreview(voice)}
                        disabled={previewLoading === voice.voiceId}
                      >
                        {previewLoading === voice.voiceId ? (
                          <Loader2 size={13} className="animate-spin" />
                        ) : playingId === voice.voiceId ? (
                          <Square size={13} />
                        ) : (
                          <Play size={13} />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 hover:text-destructive"
                        onClick={() => handleDelete(voice.voiceId, voice.name)}
                      >
                        <Trash2 size={13} />
                      </Button>
                    </div>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    Voice ID: <code className="text-[10px]">{voice.voiceId.substring(0, 16)}...</code>
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {['all', 'openai', 'elevenlabs', 'deepgram', 'cartesia'].map((f) => (
          <Button
            key={f}
            variant={filter === f ? 'default' : 'outline'}
            size="sm"
            className="h-7 text-xs"
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? 'All Voices' : providerLabels[f] ?? f}
          </Button>
        ))}
      </div>

      {/* Voice grid */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={20} className="animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredVoices
            .filter((v) => v.category !== 'cloned')
            .map((voice) => (
              <Card key={`${voice.provider}-${voice.voiceId}`} className="group hover:border-primary/20 transition-colors">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-sm font-semibold">{voice.name}</h3>
                      <Badge
                        variant="outline"
                        className={`text-[10px] mt-1 ${providerColors[voice.provider] ?? ''}`}
                      >
                        {providerLabels[voice.provider] ?? voice.provider}
                      </Badge>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => handlePreview(voice)}
                      disabled={previewLoading === voice.voiceId}
                    >
                      {previewLoading === voice.voiceId ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : playingId === voice.voiceId ? (
                        <Square size={14} />
                      ) : (
                        <Play size={14} />
                      )}
                    </Button>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                    {voice.labels.gender && <span>{voice.labels.gender}</span>}
                    {voice.labels.accent && (
                      <>
                        <span className="w-0.5 h-0.5 rounded-full bg-muted-foreground/40" />
                        <span>{voice.labels.accent}</span>
                      </>
                    )}
                    {voice.labels.style && (
                      <>
                        <span className="w-0.5 h-0.5 rounded-full bg-muted-foreground/40" />
                        <span>{voice.labels.style}</span>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
        </div>
      )}
    </div>
  );
}
