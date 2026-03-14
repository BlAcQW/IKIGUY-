import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Phone } from 'lucide-react';
import type { CallBehavior } from '@/types';

// ---------------------------------------------------------------------------
// Toggle switch — same pattern used in the assistant AdvancedTab
// ---------------------------------------------------------------------------

function ToggleSwitch({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
        checked ? 'bg-primary' : 'bg-muted'
      }`}
    >
      <span
        className={`pointer-events-none block h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${
          checked ? 'translate-x-4' : 'translate-x-0'
        }`}
      />
    </button>
  );
}

interface Props {
  behavior: CallBehavior;
  onChange: (patch: Partial<CallBehavior>) => void;
}

export function CallBehaviorCard({ behavior, onChange }: Props) {
  return (
    <Card className="mb-4">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <Phone size={16} className="text-primary" />
          </div>
          <div>
            <CardTitle className="text-base font-display">Call Behavior</CardTitle>
            <CardDescription className="text-xs">
              Defaults for call duration, recording, HIPAA compliance, and retry logic.
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* --- Duration & Timeout --- */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Max Call Duration (seconds)</Label>
            <Input
              type="number"
              min={60}
              max={14400}
              value={behavior.maxCallDuration}
              onChange={(e) => onChange({ maxCallDuration: parseInt(e.target.value) || 3600 })}
              className="text-xs"
            />
            <p className="text-[10px] text-muted-foreground/70">60s – 14 400s (4 hours)</p>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Session Idle Timeout (seconds)</Label>
            <Input
              type="number"
              min={30}
              max={600}
              value={behavior.sessionIdleTimeout}
              onChange={(e) => onChange({ sessionIdleTimeout: parseInt(e.target.value) || 120 })}
              className="text-xs"
            />
            <p className="text-[10px] text-muted-foreground/70">30s – 600s (10 min)</p>
          </div>
        </div>

        {/* --- Toggles --- */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-xs">Recording Enabled</Label>
              <p className="text-[10px] text-muted-foreground/70">Record all calls for this organization</p>
            </div>
            <ToggleSwitch
              checked={behavior.recordingEnabled}
              onChange={(v) => onChange({ recordingEnabled: v })}
            />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-xs">HIPAA Compliant</Label>
              <p className="text-[10px] text-muted-foreground/70">Disable logging of PHI in transcripts</p>
            </div>
            <ToggleSwitch
              checked={behavior.hipaaCompliant}
              onChange={(v) => onChange({ hipaaCompliant: v })}
            />
          </div>
        </div>

        {/* --- Retry Settings --- */}
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Retry Settings</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label className="text-xs">Max Retries</Label>
              <Input
                type="number"
                min={0}
                max={10}
                value={behavior.retrySettings.maxRetries}
                onChange={(e) =>
                  onChange({
                    retrySettings: {
                      ...behavior.retrySettings,
                      maxRetries: parseInt(e.target.value) || 0,
                    },
                  })
                }
                className="text-xs"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Retry Delay (seconds)</Label>
              <Input
                type="number"
                min={1}
                max={300}
                value={behavior.retrySettings.retryDelay}
                onChange={(e) =>
                  onChange({
                    retrySettings: {
                      ...behavior.retrySettings,
                      retryDelay: parseInt(e.target.value) || 30,
                    },
                  })
                }
                className="text-xs"
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
