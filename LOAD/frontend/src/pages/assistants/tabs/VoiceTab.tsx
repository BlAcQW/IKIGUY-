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
    </div>
  );
}
