import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Bot,
  Trash2,
  Pencil,
  Brain,
  Mic,
  Volume2,
  Wrench,
  Settings2,
  Code2,
  BarChart3,
  ShieldCheck,
  Play,
  Copy,
  Check,
} from 'lucide-react';
import { toast } from 'sonner';
import type { AssistantForm } from './hooks/useAssistantEditor';
import { ModelTab } from './tabs/ModelTab';
import { TranscriberTab } from './tabs/TranscriberTab';
import { VoiceTab } from './tabs/VoiceTab';
import { FunctionsTab } from './tabs/FunctionsTab';
import { AdvancedTab } from './tabs/AdvancedTab';
import { AnalysisTab } from './tabs/AnalysisTab';
import { ComplianceTab } from './tabs/ComplianceTab';
import { CodeTab } from './tabs/CodeTab';
import { TestTab } from './tabs/TestTab';
import { MetricBar } from './components/MetricBar';

interface AssistantEditorPanelProps {
  form: AssistantForm;
  updateField: <K extends keyof AssistantForm>(key: K, value: AssistantForm[K]) => void;
  loading: boolean;
  saving: boolean;
  dirty: boolean;
  onPublish: () => void;
  onDelete: () => void;
  hasAssistant: boolean;
  assistantId?: string;
}

function ToggleSwitch({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
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

export function AssistantEditorPanel({
  form,
  updateField,
  loading,
  saving,
  dirty,
  onPublish,
  onDelete,
  hasAssistant,
  assistantId,
}: AssistantEditorPanelProps) {
  const [editingName, setEditingName] = useState(false);
  const [copiedId, setCopiedId] = useState(false);
  const [published, setPublished] = useState(true);
  const nameInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingName && nameInputRef.current) {
      nameInputRef.current.focus();
      nameInputRef.current.select();
    }
  }, [editingName]);

  function handleCopyId() {
    if (assistantId) {
      navigator.clipboard.writeText(assistantId);
      setCopiedId(true);
      toast.success('ID copied');
      setTimeout(() => setCopiedId(false), 2000);
    }
  }

  function handlePublishToggle(checked: boolean) {
    setPublished(checked);
    if (dirty) {
      onPublish();
    }
  }

  // Empty state
  if (!hasAssistant && !loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-editor">
        <div className="text-center">
          <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4">
            <Bot size={24} className="text-muted-foreground/30" />
          </div>
          <h3 className="text-base font-display font-semibold text-foreground mb-1">
            Select an assistant
          </h3>
          <p className="text-sm text-muted-foreground max-w-[260px]">
            Choose an assistant from the list or create a new one to start editing.
          </p>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex-1 bg-editor p-6">
        <div className="flex items-center justify-between mb-6">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-9 w-24" />
        </div>
        <Skeleton className="h-9 w-full mb-4" />
        <div className="space-y-4">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-editor flex flex-col h-full overflow-hidden">
      {/* Header Row 1: Name + Actions */}
      <div className="px-6 py-3 border-b border-panel-border shrink-0">
        <div className="flex items-center justify-between gap-4">
          {/* Left: Name + ID */}
          <div className="flex items-center gap-3 min-w-0 flex-1">
            {editingName ? (
              <input
                ref={nameInputRef}
                type="text"
                value={form.name}
                onChange={(e) => updateField('name', e.target.value)}
                onBlur={() => setEditingName(false)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') setEditingName(false);
                  if (e.key === 'Escape') setEditingName(false);
                }}
                className="text-xl font-display font-bold bg-transparent border-b-2 border-primary outline-none px-0 py-0.5 min-w-[200px]"
              />
            ) : (
              <button
                onClick={() => setEditingName(true)}
                className="flex items-center gap-2 group min-w-0"
              >
                <h2 className="text-xl font-display font-bold text-foreground truncate">
                  {form.name || 'Untitled Assistant'}
                </h2>
                <Pencil
                  size={14}
                  className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                />
              </button>
            )}
            {assistantId && (
              <button
                onClick={handleCopyId}
                className="flex items-center gap-1 text-[10px] font-mono text-muted-foreground/60 hover:text-muted-foreground transition-colors shrink-0"
              >
                {assistantId.slice(0, 8)}...
                {copiedId ? <Check size={10} /> : <Copy size={10} />}
              </button>
            )}
            {dirty && (
              <Badge
                variant="outline"
                className="text-[10px] border-yellow-500/30 text-yellow-500 bg-yellow-500/10 shrink-0"
              >
                Unsaved
              </Badge>
            )}
          </div>

          {/* Right: Action buttons */}
          <div className="flex items-center gap-2 shrink-0">
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-muted-foreground">Published</span>
              <ToggleSwitch
                checked={published}
                onChange={handlePublishToggle}
                label="Published toggle"
              />
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={onDelete}
              className="h-8 w-8 text-muted-foreground hover:text-destructive"
            >
              <Trash2 size={15} />
            </Button>

            <Button
              onClick={onPublish}
              disabled={saving || !dirty}
              size="sm"
              className="h-8 px-4 text-xs font-semibold"
            >
              {saving ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>

        {/* Header Row 2: Metrics */}
        <div className="flex items-center gap-6 mt-2.5 pb-0.5">
          <MetricBar label="Cost" value="~$0.12/min" percent={35} color="green" />
          <MetricBar label="Latency" value="~800ms" percent={40} color="blue" />
          <MetricBar label="Quality" value="High" percent={85} color="green" />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <Tabs defaultValue="model" className="flex flex-col h-full">
          <div className="px-6 pt-3 shrink-0">
            <TabsList className="w-full h-10 bg-muted/50">
              <TabsTrigger value="model" className="flex-1 text-xs gap-1.5">
                <Brain size={13} />
                Model
              </TabsTrigger>
              <TabsTrigger value="transcriber" className="flex-1 text-xs gap-1.5">
                <Mic size={13} />
                Transcriber
              </TabsTrigger>
              <TabsTrigger value="voice" className="flex-1 text-xs gap-1.5">
                <Volume2 size={13} />
                Voice
              </TabsTrigger>
              <TabsTrigger value="functions" className="flex-1 text-xs gap-1.5">
                <Wrench size={13} />
                Functions
              </TabsTrigger>
              <TabsTrigger value="advanced" className="flex-1 text-xs gap-1.5">
                <Settings2 size={13} />
                Advanced
              </TabsTrigger>
              <TabsTrigger value="analysis" className="flex-1 text-xs gap-1.5">
                <BarChart3 size={13} />
                Analysis
              </TabsTrigger>
              <TabsTrigger value="compliance" className="flex-1 text-xs gap-1.5">
                <ShieldCheck size={13} />
                Compliance
              </TabsTrigger>
              <TabsTrigger value="code" className="flex-1 text-xs gap-1.5">
                <Code2 size={13} />
                Code
              </TabsTrigger>
              <TabsTrigger value="test" className="flex-1 text-xs gap-1.5">
                <Play size={13} />
                Test
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 overflow-y-auto scrollbar-thin px-6 py-4">
            <TabsContent value="model" className="mt-0">
              <ModelTab form={form} updateField={updateField} />
            </TabsContent>
            <TabsContent value="transcriber" className="mt-0">
              <TranscriberTab form={form} updateField={updateField} />
            </TabsContent>
            <TabsContent value="voice" className="mt-0">
              <VoiceTab form={form} updateField={updateField} />
            </TabsContent>
            <TabsContent value="functions" className="mt-0">
              <FunctionsTab form={form} updateField={updateField} assistantId={assistantId} />
            </TabsContent>
            <TabsContent value="advanced" className="mt-0">
              <AdvancedTab form={form} updateField={updateField} />
            </TabsContent>
            <TabsContent value="analysis" className="mt-0">
              <AnalysisTab form={form} updateField={updateField} />
            </TabsContent>
            <TabsContent value="compliance" className="mt-0">
              <ComplianceTab form={form} updateField={updateField} />
            </TabsContent>
            <TabsContent value="code" className="mt-0">
              <CodeTab form={form} />
            </TabsContent>
            <TabsContent value="test" className="mt-0">
              <TestTab form={form} assistantId={assistantId} />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}
