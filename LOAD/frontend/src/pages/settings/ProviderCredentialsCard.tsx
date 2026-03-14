import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { KeyRound, Eye, EyeOff } from 'lucide-react';
import type { ProviderCredentials } from '@/types';

// ---------------------------------------------------------------------------
// Provider credential fields — each maps to a key in ProviderCredentials
// ---------------------------------------------------------------------------

const CREDENTIAL_FIELDS: Array<{
  key: keyof ProviderCredentials;
  label: string;
  placeholder: string;
}> = [
  { key: 'openaiApiKey', label: 'OpenAI API Key', placeholder: 'sk-...' },
  { key: 'googleAiApiKey', label: 'Google AI API Key', placeholder: 'AIza...' },
  { key: 'anthropicApiKey', label: 'Anthropic API Key', placeholder: 'sk-ant-...' },
  { key: 'deepgramApiKey', label: 'Deepgram API Key', placeholder: 'dg_...' },
  { key: 'elevenLabsApiKey', label: 'ElevenLabs API Key', placeholder: 'xi_...' },
  { key: 'cartesiaApiKey', label: 'Cartesia API Key', placeholder: 'sk_car_...' },
  { key: 'twilioAccountSid', label: 'Twilio Account SID', placeholder: 'AC...' },
  { key: 'twilioAuthToken', label: 'Twilio Auth Token', placeholder: 'Auth token...' },
];

interface Props {
  credentials: ProviderCredentials;
  /** Only fields the user actually typed in — avoids writing back masked values */
  editedFields: Set<keyof ProviderCredentials>;
  onChange: (key: keyof ProviderCredentials, value: string) => void;
}

export function ProviderCredentialsCard({ credentials, editedFields, onChange }: Props) {
  // Track which fields have their value visible (toggled per-field)
  const [visible, setVisible] = useState<Set<string>>(new Set());

  function toggleVisible(key: string) {
    setVisible((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  return (
    <Card className="mb-4">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <KeyRound size={16} className="text-primary" />
          </div>
          <div>
            <CardTitle className="text-base font-display">Provider Credentials</CardTitle>
            <CardDescription className="text-xs">
              API keys for STT, LLM, TTS, and telephony providers. These override server environment variables.
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {CREDENTIAL_FIELDS.map(({ key, label, placeholder }) => {
          const rawValue = credentials[key] ?? '';
          const isEdited = editedFields.has(key);
          const showPassword = visible.has(key);

          return (
            <div key={key} className="space-y-1.5">
              <Label className="text-xs">{label}</Label>
              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder={placeholder}
                  value={rawValue}
                  onChange={(e) => onChange(key, e.target.value)}
                  className="pr-9 font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={() => toggleVisible(key)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
              {/* Hint when showing a masked value from the server */}
              {rawValue && !isEdited && (
                <p className="text-[10px] text-muted-foreground/70">
                  Showing masked value from server. Type a new value to replace it.
                </p>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
