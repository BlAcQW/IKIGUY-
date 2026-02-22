import React, { useEffect, useState, useCallback } from 'react';
import { listTools, createTool, updateTool, deleteTool } from '../lib/api';
import type { Tool, ToolType, CreateToolRequest, UpdateToolRequest } from '../types';
import { PageHeader } from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { AlertDialog } from '@/components/ui/alert-dialog';
import { Wrench, Plus, Pencil, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

const TOOL_TYPE_LABELS: Record<ToolType, string> = { FUNCTION: 'Function', TRANSFER_CALL: 'Transfer Call', END_CALL: 'End Call' };
const TOOL_TYPE_COLORS: Record<ToolType, 'default' | 'secondary' | 'outline'> = { FUNCTION: 'default', TRANSFER_CALL: 'secondary', END_CALL: 'outline' };

interface ToolForm {
  name: string; type: ToolType; description: string; functionName: string;
  functionParameters: string; serverUrl: string; serverSecret: string;
}

const emptyForm: ToolForm = { name: '', type: 'FUNCTION', description: '', functionName: '', functionParameters: '{}', serverUrl: '', serverSecret: '' };

function formToRequest(form: ToolForm): CreateToolRequest | UpdateToolRequest {
  const req: CreateToolRequest = { name: form.name, type: form.type, description: form.description || undefined, serverUrl: form.serverUrl || undefined, serverSecret: form.serverSecret || undefined };
  if (form.type === 'FUNCTION' && form.functionName) {
    let params: Record<string, unknown> = {};
    try { params = JSON.parse(form.functionParameters); } catch { /* keep empty */ }
    req.function = { name: form.functionName, parameters: params };
  }
  return req;
}

function toolToForm(tool: Tool): ToolForm {
  return { name: tool.name, type: tool.type, description: tool.description ?? '', functionName: tool.function?.name ?? '', functionParameters: tool.function?.parameters ? JSON.stringify(tool.function.parameters, null, 2) : '{}', serverUrl: tool.serverUrl ?? '', serverSecret: tool.serverSecret ?? '' };
}

export function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<ToolForm>(emptyForm);
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadTools = useCallback(async () => {
    try { const result = await listTools(); setTools(result.data); }
    catch (err: unknown) { const message = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to load tools', { description: message }); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadTools(); }, [loadTools]);

  function openCreate() { setEditingId(null); setForm(emptyForm); setDialogOpen(true); }
  function openEdit(tool: Tool) { setEditingId(tool.id); setForm(toolToForm(tool)); setDialogOpen(true); }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault(); setSaving(true);
    try {
      const data = formToRequest(form);
      if (editingId) { await updateTool(editingId, data); toast.success('Tool updated'); }
      else { await createTool(data as CreateToolRequest); toast.success('Tool created'); }
      setDialogOpen(false); await loadTools();
    } catch (err: unknown) { const message = err instanceof Error ? err.message : 'Unknown error'; toast.error(editingId ? 'Failed to update tool' : 'Failed to create tool', { description: message }); }
    finally { setSaving(false); }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try { await deleteTool(deleteTarget.id); toast.success('Tool deleted'); setDeleteTarget(null); await loadTools(); }
    catch (err: unknown) { const message = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to delete tool', { description: message }); }
    finally { setDeleting(false); }
  }

  return (
    <div className="animate-slide-up">
      <PageHeader title="Tools" subtitle="Define custom functions and actions for your assistants">
        <Button onClick={openCreate} className="font-semibold"><Plus size={15} className="mr-2" />Create Tool</Button>
      </PageHeader>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-display">{editingId ? 'Edit Tool' : 'Create Tool'}</DialogTitle>
            <DialogDescription>{editingId ? 'Update tool configuration.' : 'Add a new tool for your assistants.'}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label className="text-xs font-medium">Name</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required placeholder="e.g., check_availability" className="h-10" /></div>
              <div className="space-y-2"><Label className="text-xs font-medium">Type</Label>
                <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v as ToolType })}><SelectTrigger className="h-10"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="FUNCTION">Function</SelectItem><SelectItem value="TRANSFER_CALL">Transfer Call</SelectItem><SelectItem value="END_CALL">End Call</SelectItem></SelectContent></Select>
              </div>
            </div>
            <div className="space-y-2"><Label className="text-xs font-medium">Description</Label><Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} placeholder="What does this tool do?" className="resize-none" /></div>
            {form.type === 'FUNCTION' && (
              <>
                <div className="space-y-2"><Label className="text-xs font-medium">Function Name</Label><Input value={form.functionName} onChange={(e) => setForm({ ...form, functionName: e.target.value })} placeholder="e.g., checkAvailability" className="h-10" /></div>
                <div className="space-y-2"><Label className="text-xs font-medium">Parameters (JSON)</Label><Textarea value={form.functionParameters} onChange={(e) => setForm({ ...form, functionParameters: e.target.value })} rows={4} className="font-mono text-xs resize-none" placeholder='{"type": "object", "properties": {}}' /></div>
              </>
            )}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label className="text-xs font-medium">Server URL</Label><Input value={form.serverUrl} onChange={(e) => setForm({ ...form, serverUrl: e.target.value })} placeholder="https://..." className="h-10" /></div>
              <div className="space-y-2"><Label className="text-xs font-medium">Server Secret</Label><Input value={form.serverSecret} onChange={(e) => setForm({ ...form, serverSecret: e.target.value })} type="password" placeholder="Optional" className="h-10" /></div>
            </div>
            <DialogFooter className="pt-2"><Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button><Button type="submit" disabled={saving} className="font-semibold">{saving ? 'Saving...' : editingId ? 'Update' : 'Create'}</Button></DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteTarget !== null} onOpenChange={(open) => !open && setDeleteTarget(null)} title="Delete Tool" description={`Are you sure you want to delete "${deleteTarget?.name ?? ''}"? This action cannot be undone.`} confirmLabel="Delete" variant="destructive" loading={deleting} onConfirm={handleDelete} />

      {loading ? (
        <Card><CardContent className="p-0"><div className="p-4 space-y-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}</div></CardContent></Card>
      ) : tools.length === 0 ? (
        <Card className="border-dashed"><CardContent className="py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4"><Wrench size={24} className="text-muted-foreground/40" /></div>
          <h2 className="text-base font-display font-semibold mb-1">No tools yet</h2>
          <p className="text-sm text-muted-foreground mb-5">Create tools to extend your assistant's capabilities.</p>
          <Button onClick={openCreate} className="font-semibold">Create Tool</Button>
        </CardContent></Card>
      ) : (
        <Card><CardContent className="p-0">
          <Table>
            <TableHeader><TableRow className="hover:bg-transparent"><TableHead className="text-xs">Name</TableHead><TableHead className="text-xs">Type</TableHead><TableHead className="text-xs">Description</TableHead><TableHead className="text-xs">Server URL</TableHead><TableHead className="w-[100px] text-xs">Actions</TableHead></TableRow></TableHeader>
            <TableBody>
              {tools.map((tool) => (
                <TableRow key={tool.id} className="group">
                  <TableCell className="font-medium text-sm">{tool.name}</TableCell>
                  <TableCell><Badge variant={TOOL_TYPE_COLORS[tool.type]} className="text-[10px]">{TOOL_TYPE_LABELS[tool.type]}</Badge></TableCell>
                  <TableCell className="text-muted-foreground text-xs truncate max-w-[200px]">{tool.description ?? '--'}</TableCell>
                  <TableCell className="text-muted-foreground text-xs truncate max-w-[200px] font-mono">{tool.serverUrl ?? '--'}</TableCell>
                  <TableCell>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button variant="ghost" size="icon" onClick={() => openEdit(tool)} className="h-8 w-8"><Pencil size={13} /></Button>
                      <Button variant="ghost" size="icon" onClick={() => setDeleteTarget({ id: tool.id, name: tool.name })} className="h-8 w-8 text-muted-foreground hover:text-destructive"><Trash2 size={13} /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent></Card>
      )}
    </div>
  );
}
