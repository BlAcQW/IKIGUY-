import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { AssistantForm } from '../hooks/useAssistantEditor';

interface TranscriberTabProps {
  form: AssistantForm;
  updateField: <K extends keyof AssistantForm>(key: K, value: AssistantForm[K]) => void;
}

const STT_MODELS: Record<string, { label: string; value: string }[]> = {
  openai: [{ label: 'Whisper-1', value: 'whisper-1' }],
  deepgram: [
    { label: 'Nova-2', value: 'nova-2' },
    { label: 'Nova-2 General', value: 'nova-2-general' },
    { label: 'Nova-2 Medical', value: 'nova-2-medical' },
    { label: 'Nova-2 Meeting', value: 'nova-2-meeting' },
    { label: 'Nova-2 Phonecall', value: 'nova-2-phonecall' },
    { label: 'Nova-2 Finance', value: 'nova-2-finance' },
    { label: 'Nova-2 Conversational AI', value: 'nova-2-conversationalai' },
    { label: 'Nova-2 Voicemail', value: 'nova-2-voicemail' },
    { label: 'Flux General English', value: 'flux-general-en' },
  ],
  assemblyai: [
    { label: 'Best', value: 'best' },
    { label: 'Nano', value: 'nano' },
  ],
  azure: [
    { label: 'Azure Speech Default', value: 'azure-speech-default' },
    { label: 'Azure Speech Custom', value: 'azure-speech-custom' },
  ],
  google: [
    { label: 'Latest Long', value: 'latest_long' },
    { label: 'Latest Short', value: 'latest_short' },
    { label: 'Chirp', value: 'chirp' },
    { label: 'Chirp 2', value: 'chirp_2' },
  ],
  gladia: [
    { label: 'Solaria', value: 'solaria' },
    { label: 'Solaria Enhanced', value: 'solaria-enhanced' },
  ],
  speechmatics: [
    { label: 'Enhanced', value: 'enhanced' },
    { label: 'Standard', value: 'standard' },
  ],
  parakeet: [
    { label: 'Parakeet TDT 1.1', value: 'parakeet-tdt-1.1' },
    { label: 'Parakeet CTC 1.0', value: 'parakeet-ctc-1.0' },
  ],
  custom: [
    { label: 'Custom Endpoint', value: 'custom' },
  ],
};

const LANGUAGES = [
  { label: 'English', value: 'en' },
  { label: 'Spanish', value: 'es' },
  { label: 'French', value: 'fr' },
  { label: 'German', value: 'de' },
  { label: 'Portuguese', value: 'pt' },
  { label: 'Japanese', value: 'ja' },
  { label: 'Chinese', value: 'zh' },
  { label: 'Arabic', value: 'ar' },
  { label: 'Hindi', value: 'hi' },
  { label: 'Korean', value: 'ko' },
  { label: 'Italian', value: 'it' },
  { label: 'Dutch', value: 'nl' },
  { label: 'Polish', value: 'pl' },
  { label: 'Russian', value: 'ru' },
  { label: 'Turkish', value: 'tr' },
  { label: 'Swedish', value: 'sv' },
  { label: 'Norwegian', value: 'no' },
  { label: 'Danish', value: 'da' },
  { label: 'Finnish', value: 'fi' },
  { label: 'Czech', value: 'cs' },
  { label: 'Romanian', value: 'ro' },
  { label: 'Hungarian', value: 'hu' },
  { label: 'Ukrainian', value: 'uk' },
  { label: 'Thai', value: 'th' },
  { label: 'Vietnamese', value: 'vi' },
  { label: 'Indonesian', value: 'id' },
  { label: 'Malay', value: 'ms' },
  { label: 'Greek', value: 'el' },
  { label: 'Hebrew', value: 'he' },
  { label: 'Bulgarian', value: 'bg' },
];

export function TranscriberTab({ form, updateField }: TranscriberTabProps) {
  const models = STT_MODELS[form.transcriberProvider] ?? STT_MODELS.openai;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="editor-section">
        <h3>Speech-to-Text</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label className="text-xs font-medium">Provider</Label>
            <Select
              value={form.transcriberProvider}
              onValueChange={(v) => {
                updateField('transcriberProvider', v);
                const firstModel = STT_MODELS[v]?.[0]?.value;
                if (firstModel) updateField('transcriberModel', firstModel);
              }}
            >
              <SelectTrigger className="h-10 bg-background">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="deepgram">Deepgram</SelectItem>
                <SelectItem value="assemblyai">AssemblyAI</SelectItem>
                <SelectItem value="azure">Azure Speech</SelectItem>
                <SelectItem value="google">Google Cloud</SelectItem>
                <SelectItem value="gladia">Gladia</SelectItem>
                <SelectItem value="speechmatics">Speechmatics</SelectItem>
                <SelectItem value="parakeet">Parakeet</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-medium">Model</Label>
            <Select
              value={form.transcriberModel}
              onValueChange={(v) => updateField('transcriberModel', v)}
            >
              <SelectTrigger className="h-10 bg-background">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {models.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Custom STT Endpoint */}
      {form.transcriberProvider === 'custom' && (
        <div className="editor-section">
          <h3>Custom Endpoint</h3>
          <div className="space-y-2">
            <Label className="text-xs font-medium">STT Endpoint URL</Label>
            <Input
              value={form.transcriberCustomUrl}
              onChange={(e) => updateField('transcriberCustomUrl', e.target.value)}
              placeholder="https://your-stt-server.com/v1/transcribe"
              className="h-10 bg-background font-mono text-xs"
            />
            <p className="text-[11px] text-muted-foreground">
              Your custom STT endpoint must accept audio and return transcription text.
            </p>
          </div>
        </div>
      )}

      <div className="editor-section">
        <h3>Language</h3>
        <div className="space-y-2">
          <Label className="text-xs font-medium">Transcription Language</Label>
          <Select
            value={form.transcriberLanguage}
            onValueChange={(v) => updateField('transcriberLanguage', v)}
          >
            <SelectTrigger className="h-10 bg-background max-w-[240px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LANGUAGES.map((l) => (
                <SelectItem key={l.value} value={l.value}>
                  {l.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-[11px] text-muted-foreground">
            The language your callers will speak. Auto-detection is used if not set.
          </p>
        </div>
      </div>

      <div className="editor-section">
        <h3>Keywords</h3>
        <div className="space-y-2">
          <Label className="text-xs font-medium">Keyword Boosting</Label>
          <textarea
            value={form.transcriberKeywords}
            onChange={(e) => updateField('transcriberKeywords', e.target.value)}
            placeholder="LOAD, Vapi, KasaAI, enterprise, webhook"
            rows={3}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
          />
          <p className="text-[11px] text-muted-foreground">
            Comma-separated keywords to boost transcription accuracy for domain-specific terms.
          </p>
        </div>
      </div>

      <div className="editor-section">
        <h3>Turn Detection</h3>
        <Slider
          value={form.endOfTurnConfidenceThreshold}
          min={0}
          max={1}
          step={0.05}
          onChange={(v) => updateField('endOfTurnConfidenceThreshold', v)}
          label="End of Turn Confidence Threshold"
          formatValue={(v) => v.toFixed(2)}
        />
        <p className="text-[11px] text-muted-foreground mt-2">
          Higher values require more confidence before detecting end of speech turn. 0 = disabled.
        </p>
      </div>
    </div>
  );
}
