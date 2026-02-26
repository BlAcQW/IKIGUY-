import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { AssistantForm, FallbackVoice } from '../hooks/useAssistantEditor';
import { Plus, X } from 'lucide-react';

interface VoiceTabProps {
  form: AssistantForm;
  updateField: <K extends keyof AssistantForm>(key: K, value: AssistantForm[K]) => void;
}

const VOICE_OPTIONS: Record<string, { label: string; value: string }[]> = {
  openai: [
    { label: 'Alloy', value: 'alloy' },
    { label: 'Echo', value: 'echo' },
    { label: 'Fable', value: 'fable' },
    { label: 'Onyx', value: 'onyx' },
    { label: 'Nova', value: 'nova' },
    { label: 'Shimmer', value: 'shimmer' },
    { label: 'Ash', value: 'ash' },
    { label: 'Ballad', value: 'ballad' },
    { label: 'Coral', value: 'coral' },
    { label: 'Sage', value: 'sage' },
    { label: 'Verse', value: 'verse' },
  ],
  elevenlabs: [
    { label: 'Rachel', value: '21m00Tcm4TlvDq8ikWAM' },
    { label: 'Adam', value: 'pNInz6obpgDQGcFmaJgB' },
    { label: 'Bella', value: 'EXAVITQu4vr4xnSDxMaL' },
    { label: 'Antoni', value: 'ErXwobaYiN019PkySvjV' },
    { label: 'Domi', value: 'AZnzlk1XvdvUeBnXmlld' },
    { label: 'Elli', value: 'MF3mGyEYCl7XYWbV9V6O' },
  ],
  deepgram: [
    { label: 'Asteria', value: 'aura-asteria-en' },
    { label: 'Luna', value: 'aura-luna-en' },
    { label: 'Stella', value: 'aura-stella-en' },
    { label: 'Athena', value: 'aura-athena-en' },
    { label: 'Hera', value: 'aura-hera-en' },
    { label: 'Orion', value: 'aura-orion-en' },
    { label: 'Arcas', value: 'aura-arcas-en' },
    { label: 'Perseus', value: 'aura-perseus-en' },
    { label: 'Angus', value: 'aura-angus-en' },
    { label: 'Orpheus', value: 'aura-orpheus-en' },
    { label: 'Helios', value: 'aura-helios-en' },
    { label: 'Zeus', value: 'aura-zeus-en' },
  ],
  cartesia: [
    { label: 'Barbershop Man', value: 'a0e99841-438c-4a64-b679-ae501e7d6091' },
    { label: 'British Lady', value: '79a125e8-cd45-4c13-8a67-188112f4dd22' },
    { label: 'California Girl', value: 'b7d50908-b17c-442d-ad8d-7c56e5dd3b37' },
    { label: 'Doctor Mischief', value: 'fb26447f-308b-471e-8b00-8e9f04284eb5' },
    { label: 'Friendly Reading Man', value: '69267136-1bdc-412f-ad78-0caad210fb40' },
    { label: 'Indian Lady', value: '384b625b-da5a-4b3a-a2e7-5a63d4992b3f' },
    { label: 'Midwestern Woman', value: '11af83e2-23eb-452f-956e-7fee218ccb5c' },
    { label: 'Movieman', value: 'c45bc5ec-dc68-4feb-8829-6e6b2f236b73' },
    { label: 'Newsman', value: 'd46abd1d-2571-4540-b559-a4f18285ceb3' },
    { label: 'Pilot Over Intercom', value: 'f9836c6e-a0bd-460e-9d3c-f7299fa60f94' },
    { label: 'Southern Woman', value: 'f786b574-daa5-4673-aa0c-cbe3e6d6e9cd' },
    { label: 'Wise Man', value: '3b554273-4299-48b9-9aaf-eefd438e3941' },
  ],
};

const PROVIDER_LABELS: Record<string, string> = {
  openai: 'OpenAI',
  elevenlabs: 'ElevenLabs',
  deepgram: 'Deepgram',
  cartesia: 'Cartesia',
};

export function VoiceTab({ form, updateField }: VoiceTabProps) {
  const voices = VOICE_OPTIONS[form.voiceProvider] ?? VOICE_OPTIONS.openai;

  function addFallbackVoice() {
    if (form.fallbackVoices.length >= 3) return;
    const newVoice: FallbackVoice = { provider: 'openai', voiceId: 'alloy' };
    updateField('fallbackVoices', [...form.fallbackVoices, newVoice]);
  }

  function removeFallbackVoice(index: number) {
    updateField('fallbackVoices', form.fallbackVoices.filter((_, i) => i !== index));
  }

  function updateFallbackVoice(index: number, field: keyof FallbackVoice, value: string) {
    const updated = form.fallbackVoices.map((v, i) => {
      if (i !== index) return v;
      if (field === 'provider') {
        const firstVoice = VOICE_OPTIONS[value]?.[0]?.value ?? 'alloy';
        return { ...v, provider: value, voiceId: firstVoice };
      }
      return { ...v, [field]: value };
    });
    updateField('fallbackVoices', updated);
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="editor-section">
        <h3>Text-to-Speech</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label className="text-xs font-medium">Provider</Label>
            <Select
              value={form.voiceProvider}
              onValueChange={(v) => {
                updateField('voiceProvider', v);
                const firstVoice = VOICE_OPTIONS[v]?.[0]?.value;
                if (firstVoice) updateField('voiceId', firstVoice);
              }}
            >
              <SelectTrigger className="h-10 bg-background">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="elevenlabs">ElevenLabs</SelectItem>
                <SelectItem value="deepgram">Deepgram</SelectItem>
                <SelectItem value="cartesia">Cartesia</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-medium">Voice</Label>
            <Select value={form.voiceId} onValueChange={(v) => updateField('voiceId', v)}>
              <SelectTrigger className="h-10 bg-background">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {voices.map((v) => (
                  <SelectItem key={v.value} value={v.value}>
                    {v.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div className="editor-section">
        <h3>Speech Settings</h3>
        <Slider
          value={form.speed}
          min={0.25}
          max={4}
          step={0.25}
          onChange={(v) => updateField('speed', v)}
          label="Speech Speed"
          formatValue={(v) => `${v.toFixed(2)}x`}
        />
      </div>

      {/* Fallback Voices */}
      <div className="editor-section">
        <div className="flex items-center justify-between mb-1">
          <h3 className="!mb-0">Fallback Voices</h3>
          {form.fallbackVoices.length < 3 && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addFallbackVoice}
              className="text-xs h-7"
            >
              <Plus size={13} className="mr-1" />
              Add Fallback
            </Button>
          )}
        </div>
        <p className="text-[11px] text-muted-foreground mb-3">
          If the primary voice provider fails, these voices will be tried in order.
        </p>
        {form.fallbackVoices.length === 0 ? (
          <p className="text-xs text-muted-foreground/60 italic">No fallback voices configured.</p>
        ) : (
          <div className="space-y-2">
            {form.fallbackVoices.map((fb, i) => {
              const fbVoices = VOICE_OPTIONS[fb.provider] ?? VOICE_OPTIONS.openai;
              return (
                <div key={i} className="flex gap-2 items-center">
                  <Select
                    value={fb.provider}
                    onValueChange={(v) => updateFallbackVoice(i, 'provider', v)}
                  >
                    <SelectTrigger className="h-9 bg-background flex-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(PROVIDER_LABELS).map(([val, label]) => (
                        <SelectItem key={val} value={val}>{label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select
                    value={fb.voiceId}
                    onValueChange={(v) => updateFallbackVoice(i, 'voiceId', v)}
                  >
                    <SelectTrigger className="h-9 bg-background flex-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {fbVoices.map((v) => (
                        <SelectItem key={v.value} value={v.value}>{v.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeFallbackVoice(i)}
                    className="shrink-0 h-8 w-8 text-muted-foreground hover:text-destructive"
                  >
                    <X size={14} />
                  </Button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
