import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { PageHeader } from '@/components/PageHeader';
import {
  listCampaigns,
  createCampaign,
  updateCampaign,
  startCampaign,
  pauseCampaign,
  resumeCampaign,
  deleteCampaign,
  listAssistants,
  listPhoneNumbers,
} from '../lib/api';
import type {
  Campaign,
  CampaignStatus,
  CampaignContact,
  CampaignSchedule,
  Assistant,
  PhoneNumber,
  CreateCampaignRequest,
} from '../types';
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
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { AlertDialog } from '@/components/ui/alert-dialog';
import { Megaphone, Plus, Pencil, Trash2, Play, Pause, RotateCcw, X, Users, Clock, DollarSign } from 'lucide-react';
import { toast } from 'sonner';

const STATUS_COLORS: Record<CampaignStatus, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  DRAFT: 'outline',
  RUNNING: 'default',
  PAUSED: 'secondary',
  COMPLETED: 'secondary',
};

interface CampaignForm {
  name: string;
  assistantId: string;
  phoneNumberId: string;
  contacts: CampaignContact[];
  schedule: CampaignSchedule;
}

const emptyForm: CampaignForm = {
  name: '',
  assistantId: '',
  phoneNumberId: '',
  contacts: [{ name: '', number: '' }],
  schedule: { maxConcurrent: 1, timezone: 'UTC', delayBetweenCalls: 0, maxRetries: 0 },
};

function estimateDuration(
  contactCount: number,
  maxConcurrent: number,
  delayBetweenCalls: number,
  maxRetries: number,
): string {
  if (contactCount === 0) return '0m';
  const avgCallDuration = 60; // seconds
  const totalCalls = contactCount * (1 + maxRetries);
  const batches = Math.ceil(totalCalls / Math.max(maxConcurrent, 1));
  const totalSeconds = batches * (avgCallDuration + delayBetweenCalls);
  const minutes = Math.ceil(totalSeconds / 60);
  if (minutes < 60) return `~${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `~${hours}h ${remainingMinutes}m`;
}

function estimateCost(completedCalls: number): string {
  const avgCostPerCall = 0.12; // $0.12 per call
  const total = completedCalls * avgCostPerCall;
  return `$${total.toFixed(2)}`;
}

export function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [phoneNumbers, setPhoneNumbers] = useState<PhoneNumber[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<CampaignForm>(emptyForm);
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    try {
      const [campaignsRes, assistantsRes, phoneRes] = await Promise.all([
        listCampaigns(),
        listAssistants(1, 100),
        listPhoneNumbers(1, 100),
      ]);
      setCampaigns(campaignsRes.data);
      setAssistants(assistantsRes.data);
      setPhoneNumbers(phoneRes.data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Failed to load campaigns', { description: message });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  function openCreate() { setEditingId(null); setForm(emptyForm); setDialogOpen(true); }

  function openEdit(campaign: Campaign) {
    setEditingId(campaign.id);
    setForm({
      name: campaign.name,
      assistantId: campaign.assistantId,
      phoneNumberId: campaign.phoneNumberId,
      contacts: campaign.contacts.length > 0 ? campaign.contacts : [{ name: '', number: '' }],
      schedule: {
        maxConcurrent: campaign.schedule?.maxConcurrent ?? 1,
        timezone: campaign.schedule?.timezone ?? 'UTC',
        startTime: campaign.schedule?.startTime,
        endTime: campaign.schedule?.endTime,
        delayBetweenCalls: campaign.schedule?.delayBetweenCalls ?? 0,
        maxRetries: campaign.schedule?.maxRetries ?? 0,
      },
    });
    setDialogOpen(true);
  }

  function addContact() { setForm({ ...form, contacts: [...form.contacts, { name: '', number: '' }] }); }
  function removeContact(index: number) { const updated = form.contacts.filter((_, i) => i !== index); setForm({ ...form, contacts: updated.length > 0 ? updated : [{ name: '', number: '' }] }); }
  function updateContact(index: number, field: 'name' | 'number', value: string) { const updated = form.contacts.map((c, i) => (i === index ? { ...c, [field]: value } : c)); setForm({ ...form, contacts: updated }); }
  function updateSchedule(field: keyof CampaignSchedule, value: string | number) { setForm({ ...form, schedule: { ...form.schedule, [field]: value } }); }
  function getAssistantName(id: string): string { return assistants.find((a) => a.id === id)?.name ?? '—'; }
  function getPhoneNumberDisplay(id: string): string { return phoneNumbers.find((p) => p.id === id)?.number ?? '—'; }

  const validContacts = useMemo(
    () => form.contacts.filter((c) => c.name && c.number),
    [form.contacts],
  );

  const estDuration = useMemo(
    () => estimateDuration(
      validContacts.length,
      form.schedule.maxConcurrent ?? 1,
      form.schedule.delayBetweenCalls ?? 0,
      form.schedule.maxRetries ?? 0,
    ),
    [validContacts.length, form.schedule.maxConcurrent, form.schedule.delayBetweenCalls, form.schedule.maxRetries],
  );

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!form.assistantId || !form.phoneNumberId) { toast.error('Select an assistant and phone number'); return; }
    setSaving(true);
    try {
      const data: CreateCampaignRequest = { name: form.name, assistantId: form.assistantId, phoneNumberId: form.phoneNumberId, contacts: validContacts, schedule: form.schedule };
      if (editingId) { await updateCampaign(editingId, data); toast.success('Campaign updated'); }
      else { await createCampaign(data); toast.success('Campaign created'); }
      setDialogOpen(false); await load();
    } catch (err: unknown) { const message = err instanceof Error ? err.message : 'Unknown error'; toast.error(editingId ? 'Failed to update campaign' : 'Failed to create campaign', { description: message }); }
    finally { setSaving(false); }
  }

  async function handleAction(id: string, action: 'start' | 'pause' | 'resume') {
    try {
      if (action === 'start') await startCampaign(id);
      else if (action === 'pause') await pauseCampaign(id);
      else await resumeCampaign(id);
      toast.success(`Campaign ${action === 'start' ? 'started' : action === 'pause' ? 'paused' : 'resumed'}`);
      await load();
    } catch (err: unknown) { const message = err instanceof Error ? err.message : 'Unknown error'; toast.error(`Failed to ${action} campaign`, { description: message }); }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try { await deleteCampaign(deleteTarget.id); toast.success('Campaign deleted'); setDeleteTarget(null); await load(); }
    catch (err: unknown) { const message = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to delete campaign', { description: message }); }
    finally { setDeleting(false); }
  }

  return (
    <div className="animate-slide-up">
      <PageHeader title="Campaigns" subtitle="Manage bulk outbound calling campaigns">
        <Button onClick={openCreate} className="font-semibold"><Plus size={15} className="mr-2" />Create Campaign</Button>
      </PageHeader>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto scrollbar-thin">
          <DialogHeader>
            <DialogTitle className="font-display">{editingId ? 'Edit Campaign' : 'Create Campaign'}</DialogTitle>
            <DialogDescription>{editingId ? 'Update campaign configuration.' : 'Set up an outbound calling campaign.'}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs font-medium">Name</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required placeholder="e.g., Q1 Outreach" className="h-10" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="text-xs font-medium">Assistant</Label>
                <Select value={form.assistantId} onValueChange={(v) => setForm({ ...form, assistantId: v })}>
                  <SelectTrigger className="h-10"><SelectValue placeholder="Select assistant..." /></SelectTrigger>
                  <SelectContent>{assistants.map((a) => (<SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>))}</SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-medium">Phone Number</Label>
                <Select value={form.phoneNumberId} onValueChange={(v) => setForm({ ...form, phoneNumberId: v })}>
                  <SelectTrigger className="h-10"><SelectValue placeholder="Select number..." /></SelectTrigger>
                  <SelectContent>{phoneNumbers.map((p) => (<SelectItem key={p.id} value={p.id}>{p.number}{p.name ? ` (${p.name})` : ''}</SelectItem>))}</SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-xs font-medium">Contacts</Label>
              <div className="space-y-2">
                {form.contacts.map((contact, i) => (
                  <div key={i} className="flex gap-2 items-center">
                    <Input placeholder="Name" value={contact.name} onChange={(e) => updateContact(i, 'name', e.target.value)} className="flex-1 h-10" />
                    <Input placeholder="+1234567890" value={contact.number} onChange={(e) => updateContact(i, 'number', e.target.value)} className="flex-1 h-10" />
                    <Button type="button" variant="ghost" size="icon" onClick={() => removeContact(i)} className="shrink-0 h-8 w-8 text-muted-foreground hover:text-destructive"><X size={14} /></Button>
                  </div>
                ))}
              </div>
              <Button type="button" variant="outline" size="sm" onClick={addContact} className="text-xs h-8"><Plus size={13} className="mr-1" />Add Contact</Button>
            </div>

            <div className="space-y-2">
              <Label className="text-xs font-medium">Schedule</Label>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Max Concurrent</Label>
                  <Input type="number" min={1} max={100} value={form.schedule.maxConcurrent ?? 1} onChange={(e) => updateSchedule('maxConcurrent', parseInt(e.target.value) || 1)} className="h-10" />
                </div>
                <div className="space-y-1">
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Timezone</Label>
                  <Input value={form.schedule.timezone ?? 'UTC'} onChange={(e) => updateSchedule('timezone', e.target.value)} placeholder="UTC" className="h-10" />
                </div>
                <div className="space-y-1">
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Start Time</Label>
                  <Input type="time" value={form.schedule.startTime ?? ''} onChange={(e) => updateSchedule('startTime', e.target.value)} className="h-10" />
                </div>
                <div className="space-y-1">
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">End Time</Label>
                  <Input type="time" value={form.schedule.endTime ?? ''} onChange={(e) => updateSchedule('endTime', e.target.value)} className="h-10" />
                </div>
                <div className="space-y-1">
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Delay Between Calls (sec)</Label>
                  <Input type="number" min={0} max={300} value={form.schedule.delayBetweenCalls ?? 0} onChange={(e) => updateSchedule('delayBetweenCalls', parseInt(e.target.value) || 0)} className="h-10" />
                </div>
                <div className="space-y-1">
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Maximum Retries</Label>
                  <Input type="number" min={0} max={5} value={form.schedule.maxRetries ?? 0} onChange={(e) => updateSchedule('maxRetries', parseInt(e.target.value) || 0)} className="h-10" />
                </div>
              </div>
            </div>

            {/* Estimated Duration */}
            {validContacts.length > 0 && (
              <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-muted/50 border border-border">
                <Clock size={14} className="text-muted-foreground shrink-0" />
                <div className="flex-1">
                  <p className="text-xs font-medium">Estimated Duration</p>
                  <p className="text-[11px] text-muted-foreground">
                    {validContacts.length} contacts, {form.schedule.maxConcurrent ?? 1} concurrent, {form.schedule.delayBetweenCalls ?? 0}s delay, {form.schedule.maxRetries ?? 0} retries
                  </p>
                </div>
                <span className="text-sm font-semibold text-primary">{estDuration}</span>
              </div>
            )}

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={saving} className="font-semibold">{saving ? 'Saving...' : editingId ? 'Update' : 'Create'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteTarget !== null} onOpenChange={(open) => !open && setDeleteTarget(null)} title="Delete Campaign" description={`Are you sure you want to delete "${deleteTarget?.name ?? ''}"? This action cannot be undone.`} confirmLabel="Delete" variant="destructive" loading={deleting} onConfirm={handleDelete} />

      {loading ? (
        <Card><CardContent className="p-0"><div className="p-4 space-y-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}</div></CardContent></Card>
      ) : campaigns.length === 0 ? (
        <Card className="border-dashed"><CardContent className="py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4"><Megaphone size={24} className="text-muted-foreground/40" /></div>
          <h2 className="text-base font-display font-semibold mb-1">No campaigns yet</h2>
          <p className="text-sm text-muted-foreground mb-5">Create an outbound calling campaign to reach your contacts.</p>
          <Button onClick={openCreate} className="font-semibold">Create Campaign</Button>
        </CardContent></Card>
      ) : (
        <Card><CardContent className="p-0">
          <Table>
            <TableHeader><TableRow className="hover:bg-transparent">
              <TableHead className="text-xs">Name</TableHead>
              <TableHead className="text-xs">Status</TableHead>
              <TableHead className="text-xs">Assistant</TableHead>
              <TableHead className="text-xs">Phone</TableHead>
              <TableHead className="text-xs">Contacts</TableHead>
              <TableHead className="text-xs">Progress</TableHead>
              <TableHead className="text-xs">Est. Cost</TableHead>
              <TableHead className="w-[140px] text-xs">Actions</TableHead>
            </TableRow></TableHeader>
            <TableBody>
              {campaigns.map((c) => {
                const successRate = c.stats && c.stats.completed > 0
                  ? Math.round((c.stats.completed / (c.stats.completed + c.stats.failed)) * 100)
                  : 0;

                return (
                  <TableRow key={c.id} className="group">
                    <TableCell className="font-medium text-sm">{c.name}</TableCell>
                    <TableCell><Badge variant={STATUS_COLORS[c.status]} className="text-[10px]">{c.status}</Badge></TableCell>
                    <TableCell className="text-xs text-muted-foreground">{getAssistantName(c.assistantId)}</TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">{getPhoneNumberDisplay(c.phoneNumberId)}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Users size={11} />
                        {c.contacts.length}
                      </div>
                    </TableCell>
                    <TableCell>
                      {c.stats ? (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-1.5 bg-secondary rounded-full overflow-hidden max-w-[80px]">
                              <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${c.stats.total > 0 ? (c.stats.completed / c.stats.total) * 100 : 0}%` }} />
                            </div>
                            <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                              {c.stats.completed}/{c.stats.total}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-[10px]">
                            {successRate > 0 && (
                              <span className="text-green-500">{successRate}% success</span>
                            )}
                            {c.stats.failed > 0 && (
                              <span className="text-destructive">{c.stats.failed} failed</span>
                            )}
                            {c.stats.inProgress > 0 && (
                              <span className="text-primary">{c.stats.inProgress} active</span>
                            )}
                          </div>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {c.stats && c.stats.completed > 0 ? (
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <DollarSign size={11} />
                          <span>{estimateCost(c.stats.completed)}</span>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {c.status === 'DRAFT' && (
                          <Button variant="ghost" size="icon" onClick={() => handleAction(c.id, 'start')} className="h-8 w-8 text-primary" title="Start"><Play size={13} /></Button>
                        )}
                        {c.status === 'RUNNING' && (
                          <Button variant="ghost" size="icon" onClick={() => handleAction(c.id, 'pause')} className="h-8 w-8" title="Pause"><Pause size={13} /></Button>
                        )}
                        {c.status === 'PAUSED' && (
                          <Button variant="ghost" size="icon" onClick={() => handleAction(c.id, 'resume')} className="h-8 w-8 text-primary" title="Resume"><RotateCcw size={13} /></Button>
                        )}
                        {(c.status === 'DRAFT' || c.status === 'PAUSED') && (
                          <Button variant="ghost" size="icon" onClick={() => openEdit(c)} className="h-8 w-8"><Pencil size={13} /></Button>
                        )}
                        {(c.status === 'DRAFT' || c.status === 'COMPLETED') && (
                          <Button variant="ghost" size="icon" onClick={() => setDeleteTarget({ id: c.id, name: c.name })} className="h-8 w-8 text-muted-foreground hover:text-destructive"><Trash2 size={13} /></Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent></Card>
      )}
    </div>
  );
}
