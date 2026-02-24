import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import type { AssistantForm } from '../hooks/useAssistantEditor';

interface AnalysisTabProps {
  form: AssistantForm;
  updateField: <K extends keyof AssistantForm>(key: K, value: AssistantForm[K]) => void;
}

export function AnalysisTab({ form, updateField }: AnalysisTabProps) {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Success Evaluation */}
      <div className="editor-section">
        <h3>Success Evaluation</h3>
        <div className="space-y-2">
          <Label className="text-xs font-medium">Evaluation Prompt</Label>
          <Textarea
            value={form.successEvaluationPrompt}
            onChange={(e) => updateField('successEvaluationPrompt', e.target.value)}
            rows={5}
            placeholder="Evaluate whether the call achieved its objective. Consider: Did the assistant successfully address the caller's needs? Was the outcome positive?"
            className="resize-none text-sm bg-background font-mono"
          />
          <p className="text-[11px] text-muted-foreground">
            Prompt used to evaluate whether a call was successful. Runs after each call ends.
          </p>
        </div>
      </div>

      {/* Summary Prompt */}
      <div className="editor-section">
        <h3>Call Summary</h3>
        <div className="space-y-2">
          <Label className="text-xs font-medium">Summary Prompt</Label>
          <Textarea
            value={form.summaryPrompt}
            onChange={(e) => updateField('summaryPrompt', e.target.value)}
            rows={5}
            placeholder="Summarize this call in 2-3 sentences. Include: the caller's intent, key topics discussed, and the outcome."
            className="resize-none text-sm bg-background font-mono"
          />
          <p className="text-[11px] text-muted-foreground">
            Prompt used to generate a summary after each call.
          </p>
        </div>
      </div>

      {/* Structured Data Extraction */}
      <div className="editor-section">
        <h3>Structured Data Extraction</h3>
        <div className="space-y-2">
          <Label className="text-xs font-medium">JSON Schema</Label>
          <Textarea
            value={form.structuredDataSchema}
            onChange={(e) => updateField('structuredDataSchema', e.target.value)}
            rows={8}
            placeholder={`{
  "type": "object",
  "properties": {
    "customerName": { "type": "string" },
    "issue": { "type": "string" },
    "resolved": { "type": "boolean" }
  }
}`}
            className="resize-none text-sm bg-background font-mono"
          />
          <p className="text-[11px] text-muted-foreground">
            JSON schema defining structured data to extract from each call transcript.
          </p>
        </div>
      </div>
    </div>
  );
}
