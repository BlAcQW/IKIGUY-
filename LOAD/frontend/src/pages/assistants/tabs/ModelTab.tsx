import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { AssistantForm } from '../hooks/useAssistantEditor';

interface ModelTabProps {
  form: AssistantForm;
  updateField: <K extends keyof AssistantForm>(key: K, value: AssistantForm[K]) => void;
}

const MODEL_OPTIONS: Record<string, { label: string; value: string }[]> = {
  openai: [
    { label: 'GPT-4o', value: 'gpt-4o' },
    { label: 'GPT-4o Mini', value: 'gpt-4o-mini' },
    { label: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
    { label: 'GPT-4', value: 'gpt-4' },
    { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' },
  ],
  anthropic: [
    { label: 'Claude 4 Sonnet', value: 'claude-sonnet-4-20250514' },
    { label: 'Claude 3.5 Haiku', value: 'claude-3-5-haiku-20241022' },
  ],
  google: [
    { label: 'Gemini 2.0 Flash', value: 'gemini-2.0-flash' },
    { label: 'Gemini 1.5 Pro', value: 'gemini-1.5-pro' },
  ],
};

export function ModelTab({ form, updateField }: ModelTabProps) {
  const models = MODEL_OPTIONS[form.modelProvider] ?? MODEL_OPTIONS.openai;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* First Message */}
      <div className="editor-section">
        <h3>Greeting</h3>
        <div className="space-y-2">
          <Label className="text-xs font-medium">First Message</Label>
          <Input
            value={form.firstMessage}
            onChange={(e) => updateField('firstMessage', e.target.value)}
            placeholder="Hello! How can I help you today?"
            className="h-10 bg-background"
          />
          <p className="text-[11px] text-muted-foreground">
            The message your assistant says when the call starts.
          </p>
        </div>
      </div>

      {/* System Prompt */}
      <div className="editor-section">
        <h3>System Prompt</h3>
        <Textarea
          value={form.systemPrompt}
          onChange={(e) => updateField('systemPrompt', e.target.value)}
          rows={8}
          placeholder="You are a helpful assistant that..."
          className="resize-none text-sm bg-background font-mono"
        />
        <p className="text-[11px] text-muted-foreground mt-1">
          Instructions that define your assistant's behavior and personality.
        </p>
      </div>

      {/* Provider & Model */}
      <div className="editor-section">
        <h3>Model</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label className="text-xs font-medium">Provider</Label>
            <Select
              value={form.modelProvider}
              onValueChange={(v) => {
                updateField('modelProvider', v);
                const firstModel = MODEL_OPTIONS[v]?.[0]?.value;
                if (firstModel) updateField('model', firstModel);
              }}
            >
              <SelectTrigger className="h-10 bg-background">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="anthropic">Anthropic</SelectItem>
                <SelectItem value="google">Google</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-medium">Model</Label>
            <Select value={form.model} onValueChange={(v) => updateField('model', v)}>
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

      {/* Temperature & Max Tokens */}
      <div className="editor-section">
        <h3>Parameters</h3>
        <Slider
          value={form.temperature}
          min={0}
          max={2}
          step={0.1}
          onChange={(v) => updateField('temperature', v)}
          label="Temperature"
          formatValue={(v) => v.toFixed(1)}
        />
        <div className="space-y-2 mt-4">
          <Label className="text-xs font-medium">Max Tokens</Label>
          <Input
            type="number"
            min={1}
            max={16000}
            value={form.maxTokens}
            onChange={(e) => updateField('maxTokens', parseInt(e.target.value) || 1000)}
            className="h-10 bg-background"
          />
          <p className="text-[11px] text-muted-foreground">
            Maximum response length (1 - 16,000). Default: 1,000.
          </p>
        </div>
      </div>
    </div>
  );
}
