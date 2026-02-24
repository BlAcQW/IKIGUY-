import { useEffect, useState, useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { Wrench, Plus, Trash2, ChevronRight, Layers } from 'lucide-react';
import {
  getAssistantTools,
  attachToolToAssistant,
  detachToolFromAssistant,
  listTools,
  listToolTemplates,
  createToolFromTemplate,
} from '@/lib/api';
import type { Tool, ToolTemplate, ToolTemplateCategory, ToolTemplatesResponse } from '@/types';
import type { AssistantForm } from '../hooks/useAssistantEditor';
import { toast } from 'sonner';

interface FunctionsTabProps {
  form: AssistantForm;
  updateField: <K extends keyof AssistantForm>(key: K, value: AssistantForm[K]) => void;
  assistantId?: string;
}

type PickerView = 'choose' | 'existing' | 'templates';

export function FunctionsTab({ form, updateField, assistantId }: FunctionsTabProps) {
  const [attachedTools, setAttachedTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);

  const loadAttachedTools = useCallback(async () => {
    if (!assistantId) return;
    setLoading(true);
    try {
      const result = await getAssistantTools(assistantId);
      setAttachedTools(result.data);
    } catch {
      /* ignore load errors on tab mount */
    } finally {
      setLoading(false);
    }
  }, [assistantId]);

  useEffect(() => { loadAttachedTools(); }, [loadAttachedTools]);

  async function handleDetach(toolId: string) {
    if (!assistantId) return;
    try {
      await detachToolFromAssistant(assistantId, toolId);
      setAttachedTools((prev) => prev.filter((t) => t.id !== toolId));
      toast.success('Tool removed');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Failed to remove tool', { description: message });
    }
  }

  function handleToolAdded() {
    setPickerOpen(false);
    loadAttachedTools();
  }

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

      {/* Attached Tools */}
      <div className="editor-section">
        <div className="flex items-center justify-between mb-3">
          <h3 className="!mb-0">Tools</h3>
          {assistantId && (
            <Button variant="outline" size="sm" onClick={() => setPickerOpen(true)} className="h-7 text-xs">
              <Plus size={13} className="mr-1.5" />Add Tool
            </Button>
          )}
        </div>

        {!assistantId ? (
          <div className="rounded-lg border border-dashed border-panel-border p-8 text-center">
            <div className="w-10 h-10 rounded-xl bg-muted/50 flex items-center justify-center mx-auto mb-3">
              <Wrench size={18} className="text-muted-foreground/40" />
            </div>
            <p className="text-sm text-muted-foreground mb-1">Save assistant first</p>
            <p className="text-[11px] text-muted-foreground/60">
              Publish this assistant before attaching tools.
            </p>
          </div>
        ) : loading ? (
          <div className="space-y-2">
            {[1, 2].map((i) => <Skeleton key={i} className="h-16 w-full rounded-lg" />)}
          </div>
        ) : attachedTools.length === 0 ? (
          <div className="rounded-lg border border-dashed border-panel-border p-8 text-center">
            <div className="w-10 h-10 rounded-xl bg-muted/50 flex items-center justify-center mx-auto mb-3">
              <Wrench size={18} className="text-muted-foreground/40" />
            </div>
            <p className="text-sm text-muted-foreground mb-1">No tools attached</p>
            <p className="text-[11px] text-muted-foreground/60 mb-3">
              Add tools to give your assistant custom capabilities.
            </p>
            <Button variant="outline" size="sm" onClick={() => setPickerOpen(true)} className="text-xs">
              <Plus size={13} className="mr-1.5" />Add Tool
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            {attachedTools.map((tool) => (
              <div key={tool.id} className="flex items-start gap-3 p-3 rounded-lg border border-panel-border bg-background group">
                <div className="w-8 h-8 rounded-lg bg-muted/50 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Wrench size={14} className="text-muted-foreground" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate">{tool.name}</span>
                    <Badge variant="outline" className="text-[9px] flex-shrink-0">
                      {tool.type === 'FUNCTION' ? 'Function' : tool.type === 'TRANSFER_CALL' ? 'Transfer' : 'End Call'}
                    </Badge>
                  </div>
                  {tool.description && (
                    <p className="text-[11px] text-muted-foreground mt-0.5 truncate">{tool.description}</p>
                  )}
                  {tool.function && (
                    <code className="text-[10px] text-muted-foreground/60 font-mono">{tool.function.name}</code>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleDetach(tool.id)}
                  className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive flex-shrink-0"
                >
                  <Trash2 size={13} />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tool Picker Dialog */}
      {assistantId && (
        <ToolPickerDialog
          open={pickerOpen}
          onOpenChange={setPickerOpen}
          assistantId={assistantId}
          attachedToolIds={attachedTools.map((t) => t.id)}
          onToolAdded={handleToolAdded}
        />
      )}
    </div>
  );
}

// ─── Tool Picker Dialog ──────────────────────────────────────────────

interface ToolPickerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  assistantId: string;
  attachedToolIds: string[];
  onToolAdded: () => void;
}

function ToolPickerDialog({ open, onOpenChange, assistantId, attachedToolIds, onToolAdded }: ToolPickerDialogProps) {
  const [view, setView] = useState<PickerView>('choose');
  const [orgTools, setOrgTools] = useState<Tool[]>([]);
  const [templatesData, setTemplatesData] = useState<ToolTemplatesResponse | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<ToolTemplateCategory | ''>('');
  const [serverUrl, setServerUrl] = useState('');
  const [serverSecret, setServerSecret] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<ToolTemplate | null>(null);
  const [loadingTools, setLoadingTools] = useState(false);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!open) {
      setView('choose');
      setSelectedCategory('');
      setServerUrl('');
      setServerSecret('');
      setSelectedTemplate(null);
    }
  }, [open]);

  async function loadOrgTools() {
    setView('existing');
    setLoadingTools(true);
    try {
      const result = await listTools();
      setOrgTools(result.data.filter((t) => !attachedToolIds.includes(t.id)));
    } catch {
      toast.error('Failed to load tools');
    } finally {
      setLoadingTools(false);
    }
  }

  async function loadTemplates() {
    setView('templates');
    setLoadingTools(true);
    try {
      const result = await listToolTemplates();
      setTemplatesData(result.data);
    } catch {
      toast.error('Failed to load templates');
    } finally {
      setLoadingTools(false);
    }
  }

  async function handleAttachExisting(toolId: string) {
    try {
      await attachToolToAssistant(assistantId, toolId);
      toast.success('Tool attached');
      onToolAdded();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Failed to attach tool', { description: message });
    }
  }

  async function handleCreateFromTemplate() {
    if (!selectedTemplate || !serverUrl) return;
    setCreating(true);
    try {
      const result = await createToolFromTemplate({
        templateName: selectedTemplate.function.name,
        serverUrl,
        serverSecret: serverSecret || undefined,
      });
      await attachToolToAssistant(assistantId, result.data.id);
      toast.success(`Created and attached "${selectedTemplate.name}"`);
      onToolAdded();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Failed to create tool', { description: message });
    } finally {
      setCreating(false);
    }
  }

  const categoryTemplates = selectedCategory && templatesData
    ? templatesData.templates[selectedCategory] ?? []
    : [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="font-display">
            {view === 'choose' && 'Add Tool'}
            {view === 'existing' && 'Attach Existing Tool'}
            {view === 'templates' && !selectedTemplate && 'Create from Template'}
            {view === 'templates' && selectedTemplate && selectedTemplate.name}
          </DialogTitle>
          <DialogDescription>
            {view === 'choose' && 'Choose how to add a tool to this assistant.'}
            {view === 'existing' && 'Select a tool from your organization.'}
            {view === 'templates' && !selectedTemplate && 'Pick a pre-built tool template.'}
            {view === 'templates' && selectedTemplate && 'Configure the webhook URL for this tool.'}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto min-h-0">
          {/* Choose view */}
          {view === 'choose' && (
            <div className="space-y-2 py-2">
              <button
                onClick={loadOrgTools}
                className="w-full flex items-center gap-3 p-3 rounded-lg border border-panel-border hover:bg-muted/30 transition-colors text-left"
              >
                <div className="w-9 h-9 rounded-lg bg-muted/50 flex items-center justify-center flex-shrink-0">
                  <Wrench size={16} className="text-muted-foreground" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Existing Tool</p>
                  <p className="text-[11px] text-muted-foreground">Attach a tool already created in your organization</p>
                </div>
                <ChevronRight size={16} className="text-muted-foreground" />
              </button>
              <button
                onClick={loadTemplates}
                className="w-full flex items-center gap-3 p-3 rounded-lg border border-panel-border hover:bg-muted/30 transition-colors text-left"
              >
                <div className="w-9 h-9 rounded-lg bg-muted/50 flex items-center justify-center flex-shrink-0">
                  <Layers size={16} className="text-muted-foreground" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">From Template</p>
                  <p className="text-[11px] text-muted-foreground">Create a new tool from a pre-built template</p>
                </div>
                <ChevronRight size={16} className="text-muted-foreground" />
              </button>
            </div>
          )}

          {/* Existing tools list */}
          {view === 'existing' && (
            <div className="py-2">
              {loadingTools ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => <Skeleton key={i} className="h-14 w-full rounded-lg" />)}
                </div>
              ) : orgTools.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm text-muted-foreground">No available tools</p>
                  <p className="text-[11px] text-muted-foreground/60 mt-1">
                    All tools are already attached, or none have been created yet.
                  </p>
                </div>
              ) : (
                <div className="space-y-1.5">
                  {orgTools.map((tool) => (
                    <button
                      key={tool.id}
                      onClick={() => handleAttachExisting(tool.id)}
                      className="w-full flex items-center gap-3 p-3 rounded-lg border border-panel-border hover:bg-muted/30 transition-colors text-left"
                    >
                      <div className="w-8 h-8 rounded-lg bg-muted/50 flex items-center justify-center flex-shrink-0">
                        <Wrench size={14} className="text-muted-foreground" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium truncate">{tool.name}</span>
                          <Badge variant="outline" className="text-[9px]">{tool.type}</Badge>
                        </div>
                        {tool.description && (
                          <p className="text-[11px] text-muted-foreground truncate">{tool.description}</p>
                        )}
                      </div>
                      <Plus size={14} className="text-muted-foreground flex-shrink-0" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Templates view */}
          {view === 'templates' && !selectedTemplate && (
            <div className="py-2 space-y-3">
              <div className="space-y-2">
                <Label className="text-xs font-medium">Category</Label>
                <Select value={selectedCategory} onValueChange={(v) => setSelectedCategory(v as ToolTemplateCategory)}>
                  <SelectTrigger className="h-10">
                    <SelectValue placeholder="Select a category..." />
                  </SelectTrigger>
                  <SelectContent>
                    {templatesData && Object.entries(templatesData.categories).map(([key, label]) => (
                      <SelectItem key={key} value={key}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selectedCategory && (
                <div className="space-y-1.5">
                  {categoryTemplates.map((template) => (
                    <button
                      key={template.function.name}
                      onClick={() => setSelectedTemplate(template)}
                      className="w-full flex items-center gap-3 p-3 rounded-lg border border-panel-border hover:bg-muted/30 transition-colors text-left"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium">{template.name}</p>
                        <p className="text-[11px] text-muted-foreground truncate">{template.description}</p>
                        <code className="text-[10px] text-muted-foreground/60 font-mono">{template.function.name}</code>
                      </div>
                      <ChevronRight size={14} className="text-muted-foreground flex-shrink-0" />
                    </button>
                  ))}
                  {categoryTemplates.length === 0 && (
                    <p className="text-center text-sm text-muted-foreground py-4">No templates in this category</p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Template config form */}
          {view === 'templates' && selectedTemplate && (
            <div className="py-2 space-y-4">
              <div className="p-3 rounded-lg bg-muted/30 border border-panel-border">
                <p className="text-xs font-medium mb-1">{selectedTemplate.function.description}</p>
                <code className="text-[10px] text-muted-foreground font-mono">{selectedTemplate.function.name}</code>
                <div className="mt-2">
                  <p className="text-[10px] text-muted-foreground/60">
                    Parameters: {Object.keys((selectedTemplate.function.parameters as Record<string, unknown>).properties ?? {}).join(', ')}
                  </p>
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-medium">Webhook URL</Label>
                <Input
                  value={serverUrl}
                  onChange={(e) => setServerUrl(e.target.value)}
                  placeholder="https://your-server.com/webhook"
                  className="h-10"
                />
                <p className="text-[11px] text-muted-foreground">
                  The URL that will receive function call requests during voice calls.
                </p>
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-medium">Server Secret (Optional)</Label>
                <Input
                  value={serverSecret}
                  onChange={(e) => setServerSecret(e.target.value)}
                  type="password"
                  placeholder="HMAC secret for request signing"
                  className="h-10"
                />
                <p className="text-[11px] text-muted-foreground">
                  If set, requests will include an HMAC-SHA256 signature header.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <DialogFooter className="pt-2">
          {view !== 'choose' && !selectedTemplate && (
            <Button variant="ghost" size="sm" onClick={() => setView('choose')} className="mr-auto text-xs">
              Back
            </Button>
          )}
          {selectedTemplate && (
            <Button variant="ghost" size="sm" onClick={() => setSelectedTemplate(null)} className="mr-auto text-xs">
              Back
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>Cancel</Button>
          {selectedTemplate && (
            <Button
              size="sm"
              disabled={!serverUrl || creating}
              onClick={handleCreateFromTemplate}
              className="font-semibold"
            >
              {creating ? 'Creating...' : 'Create & Attach'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
