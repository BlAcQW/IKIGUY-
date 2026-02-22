import React, { useEffect, useState, useCallback } from 'react';
import { listSquads, createSquad, updateSquad, deleteSquad, listAssistants } from '../lib/api';
import type { Squad, Assistant, SquadMember, CreateSquadRequest } from '../types';
import { PageHeader } from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { AlertDialog } from '@/components/ui/alert-dialog';
import { Users, Plus, Pencil, Trash2, X, Bot } from 'lucide-react';
import { toast } from 'sonner';

interface SquadForm { name: string; members: SquadMember[]; }
const emptyForm: SquadForm = { name: '', members: [{ assistantId: '' }] };

export function SquadsPage() {
  const [squads, setSquads] = useState<Squad[]>([]);
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<SquadForm>(emptyForm);
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    try {
      const [squadsRes, assistantsRes] = await Promise.all([listSquads(), listAssistants(1, 100)]);
      setSquads(squadsRes.data); setAssistants(assistantsRes.data);
    } catch (err: unknown) { const msg = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to load squads', { description: msg }); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  function openCreate() { setEditingId(null); setForm(emptyForm); setDialogOpen(true); }
  function openEdit(squad: Squad) { setEditingId(squad.id); setForm({ name: squad.name, members: squad.members.length > 0 ? squad.members : [{ assistantId: '' }] }); setDialogOpen(true); }
  function addMember() { setForm({ ...form, members: [...form.members, { assistantId: '' }] }); }
  function removeMember(index: number) { const updated = form.members.filter((_, i) => i !== index); setForm({ ...form, members: updated.length > 0 ? updated : [{ assistantId: '' }] }); }
  function updateMember(index: number, assistantId: string) { const updated = form.members.map((m, i) => (i === index ? { ...m, assistantId } : m)); setForm({ ...form, members: updated }); }
  function getAssistantName(id: string): string { return assistants.find((a) => a.id === id)?.name ?? id.slice(0, 8); }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    const validMembers = form.members.filter((m) => m.assistantId);
    if (validMembers.length === 0) { toast.error('Add at least one member'); return; }
    setSaving(true);
    try {
      const data: CreateSquadRequest = { name: form.name, members: validMembers };
      if (editingId) { await updateSquad(editingId, data); toast.success('Squad updated'); }
      else { await createSquad(data); toast.success('Squad created'); }
      setDialogOpen(false); await load();
    } catch (err: unknown) { const msg = err instanceof Error ? err.message : 'Unknown error'; toast.error(editingId ? 'Failed to update squad' : 'Failed to create squad', { description: msg }); }
    finally { setSaving(false); }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try { await deleteSquad(deleteTarget.id); toast.success('Squad deleted'); setDeleteTarget(null); await load(); }
    catch (err: unknown) { const msg = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to delete squad', { description: msg }); }
    finally { setDeleting(false); }
  }

  return (
    <div className="animate-slide-up">
      <PageHeader title="Squads" subtitle="Group assistants for multi-agent call routing">
        <Button onClick={openCreate} className="font-semibold"><Plus size={15} className="mr-2" />Create Squad</Button>
      </PageHeader>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-display">{editingId ? 'Edit Squad' : 'Create Squad'}</DialogTitle>
            <DialogDescription>{editingId ? 'Update squad configuration.' : 'Group assistants together to collaborate on calls.'}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="space-y-2"><Label className="text-xs font-medium">Name</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required placeholder="e.g., Sales Team" className="h-10" /></div>
            <div className="space-y-2">
              <Label className="text-xs font-medium">Members</Label>
              <div className="space-y-2">
                {form.members.map((member, i) => (
                  <div key={i} className="flex gap-2 items-center">
                    <Select value={member.assistantId} onValueChange={(v) => updateMember(i, v)}>
                      <SelectTrigger className="flex-1 h-10"><SelectValue placeholder="Select assistant..." /></SelectTrigger>
                      <SelectContent>{assistants.map((a) => (<SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>))}</SelectContent>
                    </Select>
                    <Button type="button" variant="ghost" size="icon" onClick={() => removeMember(i)} className="shrink-0 h-8 w-8 text-muted-foreground hover:text-destructive"><X size={14} /></Button>
                  </div>
                ))}
              </div>
              <Button type="button" variant="outline" size="sm" onClick={addMember} className="text-xs h-8"><Plus size={13} className="mr-1" />Add Member</Button>
            </div>
            <DialogFooter className="pt-2"><Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button><Button type="submit" disabled={saving} className="font-semibold">{saving ? 'Saving...' : editingId ? 'Update' : 'Create'}</Button></DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteTarget !== null} onOpenChange={(open) => !open && setDeleteTarget(null)} title="Delete Squad" description={`Are you sure you want to delete "${deleteTarget?.name ?? ''}"? This action cannot be undone.`} confirmLabel="Delete" variant="destructive" loading={deleting} onConfirm={handleDelete} />

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-children">{[1, 2, 3].map((i) => (<Card key={i}><CardContent className="p-5"><Skeleton className="h-5 w-40 mb-3" /><Skeleton className="h-4 w-24" /></CardContent></Card>))}</div>
      ) : squads.length === 0 ? (
        <Card className="border-dashed"><CardContent className="py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4"><Users size={24} className="text-muted-foreground/40" /></div>
          <h2 className="text-base font-display font-semibold mb-1">No squads yet</h2>
          <p className="text-sm text-muted-foreground mb-5">Create squads to group assistants for multi-agent calls.</p>
          <Button onClick={openCreate} className="font-semibold">Create Squad</Button>
        </CardContent></Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-children">
          {squads.map((squad) => (
            <Card key={squad.id} className="group transition-all duration-200 hover:border-border/80">
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-chart-4/10 flex items-center justify-center shrink-0">
                      <Users size={16} className="text-chart-4" />
                    </div>
                    <h3 className="font-display font-semibold text-sm">{squad.name}</h3>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(squad)}><Pencil size={12} /></Button>
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive" onClick={() => setDeleteTarget({ id: squad.id, name: squad.name })}><Trash2 size={12} /></Button>
                  </div>
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <Badge variant="secondary" className="text-[10px]">{squad.members.length} member{squad.members.length !== 1 ? 's' : ''}</Badge>
                  <span className="text-[10px] text-muted-foreground">{new Date(squad.createdAt).toLocaleDateString()}</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {squad.members.map((m, i) => (
                    <Badge key={i} variant="outline" className="text-[10px] gap-1"><Bot size={9} />{getAssistantName(m.assistantId)}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
