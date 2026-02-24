import { Button } from '@/components/ui/button';
import { Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';
import type { AssistantForm } from '../hooks/useAssistantEditor';
import { buildPayload } from '../hooks/useAssistantEditor';

interface CodeTabProps {
  form: AssistantForm;
}

export function CodeTab({ form }: CodeTabProps) {
  const [copied, setCopied] = useState(false);
  const payload = buildPayload(form);
  const json = JSON.stringify(payload, null, 2);

  function handleCopy() {
    navigator.clipboard.writeText(json);
    setCopied(true);
    toast.success('JSON copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
          Assistant Configuration
        </h3>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 px-2.5 text-xs gap-1.5"
          onClick={handleCopy}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? 'Copied' : 'Copy JSON'}
        </Button>
      </div>
      <pre className="bg-muted/50 border border-border/50 rounded-lg p-4 text-xs font-mono leading-relaxed overflow-auto max-h-[600px] scrollbar-thin whitespace-pre-wrap break-all">
        {json}
      </pre>
    </div>
  );
}
