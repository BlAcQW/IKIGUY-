import { Input } from '@/components/ui/input';
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

interface AdvancedTabProps {
  form: AssistantForm;
  updateField: <K extends keyof AssistantForm>(key: K, value: AssistantForm[K]) => void;
}

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

export function AdvancedTab({ form, updateField }: AdvancedTabProps) {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Pipeline Settings */}
      <div className="editor-section">
        <h3>Pipeline</h3>
        <div className="space-y-4">
          <Slider
            value={form.silenceTimeout}
            min={5}
            max={120}
            step={5}
            onChange={(v) => updateField('silenceTimeout', v)}
            label="Silence Timeout"
            formatValue={(v) => `${v}s`}
          />
          <Slider
            value={form.responseDelay}
            min={0}
            max={2}
            step={0.1}
            onChange={(v) => updateField('responseDelay', v)}
            label="Response Delay"
            formatValue={(v) => `${v.toFixed(1)}s`}
          />
          <Slider
            value={form.interruptionThreshold}
            min={0}
            max={1}
            step={0.05}
            onChange={(v) => updateField('interruptionThreshold', v)}
            label="Interruption Threshold"
            formatValue={(v) => v.toFixed(2)}
          />
          <p className="text-[11px] text-muted-foreground">
            Lower values make the assistant easier to interrupt. 0 = instant interruption.
          </p>
        </div>
      </div>

      {/* Start Speaking Plan */}
      <div className="editor-section">
        <h3>Start Speaking Plan</h3>
        <div className="space-y-4">
          <Slider
            value={form.startSpeakingWaitTime}
            min={0}
            max={5}
            step={0.1}
            onChange={(v) => updateField('startSpeakingWaitTime', v)}
            label="Wait Time"
            formatValue={(v) => `${v.toFixed(1)}s`}
          />
          <p className="text-[11px] text-muted-foreground">
            How long to wait after detecting end of speech before the assistant starts speaking.
          </p>
          <div className="flex items-center justify-between py-2">
            <div>
              <Label className="text-sm">Smart Endpointing</Label>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Use ML-based detection to determine when the user has finished speaking.
              </p>
            </div>
            <ToggleSwitch
              checked={form.smartEndpointing}
              onChange={(v) => updateField('smartEndpointing', v)}
            />
          </div>
        </div>
      </div>

      {/* Stop Speaking Plan */}
      <div className="editor-section">
        <h3>Stop Speaking Plan</h3>
        <div className="space-y-4">
          <Slider
            value={form.stopSpeakingNumWords}
            min={0}
            max={10}
            step={1}
            onChange={(v) => updateField('stopSpeakingNumWords', v)}
            label="Num Words to Trigger Stop"
            formatValue={(v) => `${v} word${v !== 1 ? 's' : ''}`}
          />
          <p className="text-[11px] text-muted-foreground">
            Number of words the user must speak to trigger the assistant to stop. 0 = disabled.
          </p>
          <Slider
            value={form.backoffTime}
            min={0}
            max={5}
            step={0.1}
            onChange={(v) => updateField('backoffTime', v)}
            label="Backoff Time"
            formatValue={(v) => `${v.toFixed(1)}s`}
          />
          <p className="text-[11px] text-muted-foreground">
            How long the assistant waits before resuming after being interrupted.
          </p>
        </div>
      </div>

      {/* Voicemail Detection */}
      <div className="editor-section">
        <h3>Voicemail Detection</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-2">
            <div>
              <Label className="text-sm">Enable Voicemail Detection</Label>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Detect when the call reaches voicemail and optionally leave a message.
              </p>
            </div>
            <ToggleSwitch
              checked={form.voicemailDetectionEnabled}
              onChange={(v) => updateField('voicemailDetectionEnabled', v)}
            />
          </div>
          {form.voicemailDetectionEnabled && (
            <>
              <div className="space-y-2">
                <Label className="text-xs font-medium">Voicemail Message</Label>
                <textarea
                  value={form.voicemailMessage}
                  onChange={(e) => updateField('voicemailMessage', e.target.value)}
                  placeholder="Hi, this is your AI assistant calling about..."
                  rows={3}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
                />
              </div>
              <Slider
                value={form.voicemailTimeout}
                min={5}
                max={60}
                step={5}
                onChange={(v) => updateField('voicemailTimeout', v)}
                label="Detection Timeout"
                formatValue={(v) => `${v}s`}
              />
              <p className="text-[11px] text-muted-foreground">
                Time to wait before concluding the call has reached voicemail.
              </p>
            </>
          )}
        </div>
      </div>

      {/* Recording Settings */}
      <div className="editor-section">
        <h3>Recording</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2">
            <div>
              <Label className="text-sm">Call Recording</Label>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Record all calls for quality and training purposes.
              </p>
            </div>
            <ToggleSwitch
              checked={form.recordingEnabled}
              onChange={(v) => updateField('recordingEnabled', v)}
            />
          </div>
          {form.recordingEnabled && (
            <div className="space-y-2">
              <Label className="text-xs font-medium">Audio Format</Label>
              <Select
                value={form.audioRecordingFormat}
                onValueChange={(v) => updateField('audioRecordingFormat', v as 'wav' | 'mp3')}
              >
                <SelectTrigger className="h-10 bg-background max-w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="wav">WAV (Lossless)</SelectItem>
                  <SelectItem value="mp3">MP3 (Compressed)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
          <div className="flex items-center justify-between py-2">
            <div>
              <Label className="text-sm">Video Recording</Label>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Enable video recording for web calls (if supported).
              </p>
            </div>
            <ToggleSwitch
              checked={form.videoRecordingEnabled}
              onChange={(v) => updateField('videoRecordingEnabled', v)}
            />
          </div>
        </div>
      </div>

      {/* Privacy Settings */}
      <div className="editor-section">
        <h3>Privacy</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2">
            <div>
              <Label className="text-sm">HIPAA Compliant</Label>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Enable HIPAA-compliant data handling for healthcare use cases.
              </p>
            </div>
            <ToggleSwitch
              checked={form.hipaaCompliant}
              onChange={(v) => updateField('hipaaCompliant', v)}
            />
          </div>
        </div>
      </div>

      {/* Messaging Settings */}
      <div className="editor-section">
        <h3>Messaging</h3>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label className="text-xs font-medium">Server URL</Label>
            <Input
              value={form.serverUrl}
              onChange={(e) => updateField('serverUrl', e.target.value)}
              placeholder="https://your-server.com/webhook"
              className="h-10 bg-background font-mono text-xs"
            />
            <p className="text-[11px] text-muted-foreground">
              Webhook URL for real-time event forwarding during calls.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label className="text-xs font-medium">Idle Timeout (seconds)</Label>
              <Input
                type="number"
                min={10}
                max={600}
                value={form.idleTimeout}
                onChange={(e) => updateField('idleTimeout', parseInt(e.target.value) || 120)}
                className="h-10 bg-background"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-medium">Idle Message</Label>
              <Input
                value={form.idleMessage}
                onChange={(e) => updateField('idleMessage', e.target.value)}
                placeholder="Are you still there?"
                className="h-10 bg-background"
              />
            </div>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Message sent when no activity is detected for the idle timeout duration.
          </p>
        </div>
      </div>
    </div>
  );
}
