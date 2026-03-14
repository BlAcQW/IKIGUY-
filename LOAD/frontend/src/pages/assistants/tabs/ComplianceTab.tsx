import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { AssistantForm } from '../hooks/useAssistantEditor';

interface ComplianceTabProps {
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

export function ComplianceTab({ form, updateField }: ComplianceTabProps) {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* HIPAA */}
      <div className="editor-section">
        <h3>Healthcare (HIPAA)</h3>
        <div className="flex items-center justify-between py-2">
          <div>
            <Label className="text-sm">HIPAA Compliant</Label>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Enable HIPAA-compliant data handling for healthcare use cases. Restricts data storage and processing.
            </p>
          </div>
          <ToggleSwitch
            checked={form.hipaaCompliant}
            onChange={(v) => updateField('hipaaCompliant', v)}
          />
        </div>
      </div>

      {/* PCI DSS */}
      <div className="editor-section">
        <h3>Payment Card Industry (PCI DSS)</h3>
        <div className="flex items-center justify-between py-2">
          <div>
            <Label className="text-sm">PCI DSS Compliant</Label>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Enable PCI DSS compliance for handling payment card data. Prevents recording during payment collection.
            </p>
          </div>
          <ToggleSwitch
            checked={form.pciDssCompliant}
            onChange={(v) => updateField('pciDssCompliant', v)}
          />
        </div>
      </div>

      {/* Recording Consent */}
      <div className="editor-section">
        <h3>Recording Consent</h3>
        <div className="space-y-2">
          <Label className="text-xs font-medium">Consent Mode</Label>
          <Select
            value={form.recordingConsent}
            onValueChange={(v) => updateField('recordingConsent', v as AssistantForm['recordingConsent'])}
          >
            <SelectTrigger className="h-10 bg-background">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None (no consent announcement)</SelectItem>
              <SelectItem value="single-party">Single-party consent</SelectItem>
              <SelectItem value="all-party">All-party consent</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-[11px] text-muted-foreground">
            Determines whether and how recording consent is obtained. Check local laws for requirements.
          </p>
        </div>
      </div>

      {/* Data Retention */}
      <div className="editor-section">
        <h3>Data Retention</h3>
        <div className="space-y-2">
          <Label className="text-xs font-medium">Retention Period (days)</Label>
          <Input
            type="number"
            min={1}
            max={365}
            value={form.dataRetentionDays}
            onChange={(e) => updateField('dataRetentionDays', parseInt(e.target.value) || 90)}
            className="h-10 bg-background"
          />
          <p className="text-[11px] text-muted-foreground">
            Number of days to retain call recordings and transcripts. Default: 90 days.
          </p>
        </div>
      </div>
    </div>
  );
}
