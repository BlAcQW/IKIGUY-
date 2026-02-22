import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { AssistantForm } from '../hooks/useAssistantEditor';

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
  ],
  elevenlabs: [
    { label: 'Rachel', value: 'rachel' },
    { label: 'Drew', value: 'drew' },
    { label: 'Clyde', value: 'clyde' },
    { label: 'Paul', value: 'paul' },
    { label: 'Domi', value: 'domi' },
    { label: 'Dave', value: 'dave' },
  ],
  deepgram: [
    { label: 'Asteria', value: 'aura-asteria-en' },
    { label: 'Luna', value: 'aura-luna-en' },
    { label: 'Stella', value: 'aura-stella-en' },
    { label: 'Athena', value: 'aura-athena-en' },
    { label: 'Hera', value: 'aura-hera-en' },
    { label: 'Orion', value: 'aura-orion-en' },
  ],
};

export function VoiceTab({ form, updateField }: VoiceTabProps) {
  const voices = VOICE_OPTIONS[form.voiceProvider] ?? VOICE_OPTIONS.openai;

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
    </div>
  );
}
