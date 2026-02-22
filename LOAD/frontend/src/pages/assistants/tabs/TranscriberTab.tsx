import { Label } from '@/components/ui/label';
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
    </div>
  );
}
