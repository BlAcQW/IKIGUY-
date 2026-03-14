import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Cpu } from 'lucide-react';
import type { PipelineDefaults } from '@/types';

// ---------------------------------------------------------------------------
// Provider options for the select dropdowns
// ---------------------------------------------------------------------------

const STT_PROVIDERS = ['openai', 'deepgram'];
const TTS_PROVIDERS = ['openai', 'elevenlabs', 'deepgram', 'cartesia'];
const LLM_PROVIDERS = ['openai'];

interface Props {
  defaults: PipelineDefaults;
  onChange: (patch: Partial<PipelineDefaults>) => void;
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs">{label}</Label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt.charAt(0).toUpperCase() + opt.slice(1)}
          </option>
        ))}
      </select>
    </div>
  );
}

export function PipelineDefaultsCard({ defaults, onChange }: Props) {
  return (
    <Card className="mb-4">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <Cpu size={16} className="text-primary" />
          </div>
          <div>
            <CardTitle className="text-base font-display">Pipeline Defaults</CardTitle>
            <CardDescription className="text-xs">
              Default STT, LLM, and TTS configuration inherited by all assistants.
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* --- Timing sliders --- */}
        <div className="space-y-4">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Timing</h4>

          <Slider
            value={defaults.silenceTimeout}
            min={5}
            max={120}
            step={5}
            onChange={(v) => onChange({ silenceTimeout: v })}
            label="Silence Timeout"
            formatValue={(v) => `${v}s`}
          />
          <Slider
            value={defaults.responseDelay}
            min={0}
            max={2}
            step={0.1}
            onChange={(v) => onChange({ responseDelay: v })}
            label="Response Delay"
            formatValue={(v) => `${v.toFixed(1)}s`}
          />
          <Slider
            value={defaults.interruptionThreshold}
            min={0}
            max={1}
            step={0.05}
            onChange={(v) => onChange({ interruptionThreshold: v })}
            label="Interruption Threshold"
            formatValue={(v) => v.toFixed(2)}
          />
        </div>

        {/* --- Transcriber (STT) --- */}
        <div className="space-y-3">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Transcriber (STT)</h4>
          <div className="grid grid-cols-3 gap-3">
            <SelectField
              label="Provider"
              value={defaults.transcriber.provider}
              options={STT_PROVIDERS}
              onChange={(v) => onChange({ transcriber: { ...defaults.transcriber, provider: v } })}
            />
            <div className="space-y-1.5">
              <Label className="text-xs">Model</Label>
              <Input
                value={defaults.transcriber.model}
                onChange={(e) => onChange({ transcriber: { ...defaults.transcriber, model: e.target.value } })}
                className="text-xs"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Language</Label>
              <Input
                value={defaults.transcriber.language}
                onChange={(e) => onChange({ transcriber: { ...defaults.transcriber, language: e.target.value } })}
                className="text-xs"
              />
            </div>
          </div>
        </div>

        {/* --- Voice (TTS) --- */}
        <div className="space-y-3">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Voice (TTS)</h4>
          <div className="grid grid-cols-3 gap-3">
            <SelectField
              label="Provider"
              value={defaults.voice.provider}
              options={TTS_PROVIDERS}
              onChange={(v) => onChange({ voice: { ...defaults.voice, provider: v } })}
            />
            <div className="space-y-1.5">
              <Label className="text-xs">Voice ID</Label>
              <Input
                value={defaults.voice.voiceId}
                onChange={(e) => onChange({ voice: { ...defaults.voice, voiceId: e.target.value } })}
                className="text-xs"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Speed</Label>
              <Input
                type="number"
                min={0.5}
                max={2}
                step={0.1}
                value={defaults.voice.speed}
                onChange={(e) => onChange({ voice: { ...defaults.voice, speed: parseFloat(e.target.value) || 1 } })}
                className="text-xs"
              />
            </div>
          </div>
        </div>

        {/* --- LLM --- */}
        <div className="space-y-3">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">LLM</h4>
          <div className="grid grid-cols-2 gap-3">
            <SelectField
              label="Provider"
              value={defaults.llm.provider}
              options={LLM_PROVIDERS}
              onChange={(v) => onChange({ llm: { ...defaults.llm, provider: v } })}
            />
            <div className="space-y-1.5">
              <Label className="text-xs">Model</Label>
              <Input
                value={defaults.llm.model}
                onChange={(e) => onChange({ llm: { ...defaults.llm, model: e.target.value } })}
                className="text-xs"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Slider
              value={defaults.llm.temperature}
              min={0}
              max={2}
              step={0.1}
              onChange={(v) => onChange({ llm: { ...defaults.llm, temperature: v } })}
              label="Temperature"
              formatValue={(v) => v.toFixed(1)}
            />
            <div className="space-y-1.5">
              <Label className="text-xs">Max Tokens</Label>
              <Input
                type="number"
                min={1}
                max={128000}
                value={defaults.llm.maxTokens}
                onChange={(e) => onChange({ llm: { ...defaults.llm, maxTokens: parseInt(e.target.value) || 1000 } })}
                className="text-xs"
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
