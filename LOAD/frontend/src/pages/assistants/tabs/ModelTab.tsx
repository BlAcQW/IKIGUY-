import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Sparkles } from 'lucide-react';
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

const PROMPT_TEMPLATES: Record<string, string> = {
  sales: `You are a professional sales assistant. Your goal is to understand the customer's needs, present relevant solutions, handle objections gracefully, and guide the conversation toward a positive outcome. Be consultative, not pushy. Ask discovery questions and listen actively.`,
  support: `You are a friendly and efficient customer support agent. Help callers resolve their issues quickly and empathetically. Follow troubleshooting steps methodically, escalate when needed, and always confirm the issue is resolved before ending the call.`,
  scheduling: `You are a scheduling assistant. Help callers book, reschedule, or cancel appointments. Confirm availability, collect necessary details (name, date, time, purpose), and provide confirmation. Be efficient and polite.`,
  receptionist: `You are a professional receptionist. Greet callers warmly, determine the purpose of their call, and route them to the appropriate department or person. Take messages when needed and provide basic information about the organization.`,
};

export function ModelTab({ form, updateField }: ModelTabProps) {
  const models = MODEL_OPTIONS[form.modelProvider] ?? MODEL_OPTIONS.openai;
  const [showTemplates, setShowTemplates] = useState(false);

  function applyTemplate(category: string) {
    const template = PROMPT_TEMPLATES[category];
    if (template) {
      updateField('systemPrompt', template);
    }
    setShowTemplates(false);
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* First Message Mode */}
      <div className="editor-section">
        <h3>Greeting</h3>
        <div className="space-y-3">
          <div className="space-y-2">
            <Label className="text-xs font-medium">First Message Mode</Label>
            <Select
              value={form.firstMessageMode}
              onValueChange={(v) => updateField('firstMessageMode', v as AssistantForm['firstMessageMode'])}
            >
              <SelectTrigger className="h-10 bg-background">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="assistant-speaks-first">Assistant speaks first</SelectItem>
                <SelectItem value="wait-for-user">Wait for user</SelectItem>
                <SelectItem value="off">Off</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-[11px] text-muted-foreground">
              Controls whether the assistant initiates the conversation.
            </p>
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-medium">First Message</Label>
            <Input
              value={form.firstMessage}
              onChange={(e) => updateField('firstMessage', e.target.value)}
              placeholder="Hello! How can I help you today?"
              className="h-10 bg-background"
              disabled={form.firstMessageMode === 'off'}
            />
            <p className="text-[11px] text-muted-foreground">
              The message your assistant says when the call starts.
            </p>
          </div>
        </div>
      </div>

      {/* System Prompt */}
      <div className="editor-section">
        <div className="flex items-center justify-between mb-0">
          <h3>System Prompt</h3>
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2.5 text-xs gap-1.5 text-primary hover:text-primary"
              onClick={() => setShowTemplates(!showTemplates)}
            >
              <Sparkles size={12} />
              Generate
            </Button>
            {showTemplates && (
              <div className="absolute right-0 top-full mt-1 z-20 bg-popover border border-border rounded-lg shadow-lg py-1 w-44">
                {Object.keys(PROMPT_TEMPLATES).map((category) => (
                  <button
                    key={category}
                    className="w-full text-left px-3 py-2 text-xs hover:bg-muted transition-colors capitalize"
                    onClick={() => applyTemplate(category)}
                  >
                    {category}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
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
