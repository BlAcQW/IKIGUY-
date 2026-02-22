import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Wrench } from 'lucide-react';
import type { AssistantForm } from '../hooks/useAssistantEditor';

interface FunctionsTabProps {
  form: AssistantForm;
  updateField: <K extends keyof AssistantForm>(key: K, value: AssistantForm[K]) => void;
}

export function FunctionsTab({ form, updateField }: FunctionsTabProps) {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* End Call Config */}
      <div className="editor-section">
        <h3>End Call</h3>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label className="text-xs font-medium">End Call Message</Label>
            <Input
              value={form.endCallMessage}
              onChange={(e) => updateField('endCallMessage', e.target.value)}
              placeholder="Thank you for calling. Goodbye!"
              className="h-10 bg-background"
            />
            <p className="text-[11px] text-muted-foreground">
              Message spoken before the assistant ends the call.
            </p>
          </div>

          <div className="space-y-2">
            <Label className="text-xs font-medium">End Call Phrases</Label>
            <Input
              value={form.endCallPhrases}
              onChange={(e) => updateField('endCallPhrases', e.target.value)}
              placeholder="goodbye, bye, end call, hang up"
              className="h-10 bg-background"
            />
            <p className="text-[11px] text-muted-foreground">
              Comma-separated phrases that trigger the assistant to end the call.
            </p>
          </div>
        </div>
      </div>

      {/* Tools placeholder */}
      <div className="editor-section">
        <h3>Tools</h3>
        <div className="rounded-lg border border-dashed border-panel-border p-8 text-center">
          <div className="w-10 h-10 rounded-xl bg-muted/50 flex items-center justify-center mx-auto mb-3">
            <Wrench size={18} className="text-muted-foreground/40" />
          </div>
          <p className="text-sm text-muted-foreground mb-1">No tools attached</p>
          <p className="text-[11px] text-muted-foreground/60">
            Tool integration coming soon. Create tools in the Tools page and attach them here.
          </p>
        </div>
      </div>
    </div>
  );
}
