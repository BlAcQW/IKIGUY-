import React, { useEffect, useState, useCallback } from 'react';
import { PageHeader } from '@/components/PageHeader';
import {
  listWebhooks,
  createWebhook,
  updateWebhook,
  deleteWebhook,
  getWebhookDeliveries,
} from '../lib/api';
import type { Webhook, WebhookDelivery, CreateWebhookRequest } from '../types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { AlertDialog } from '@/components/ui/alert-dialog';
import { Bell, Plus, Pencil, Trash2, ChevronDown, ChevronRight, Copy, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

const WEBHOOK_EVENTS = [
  'call.started',
  'call.ended',
  'call.failed',
  'transcript.update',
  'campaign.progress',
  'campaign.completed',
];

interface WebhookForm {
  url: string;
  events: string[];
  active: boolean;
}

const emptyForm: WebhookForm = { url: '', events: [], active: true };

function webhookToForm(webhook: Webhook): WebhookForm {
  return { url: webhook.url, events: webhook.events, active: webhook.active };
}

export function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<WebhookForm>(emptyForm);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [deliveriesLoading, setDeliveriesLoading] = useState(false);
  const [visibleSecrets, setVisibleSecrets] = useState<Set<string>>(new Set());
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; url: string } | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadWebhooks = useCallback(async () => {
    try { const result = await listWebhooks(); setWebhooks(result.data); }
    catch (err: unknown) { const message = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to load webhooks', { description: message }); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadWebhooks(); }, [loadWebhooks]);

  async function loadDeliveries(webhookId: string) {
    setDeliveriesLoading(true);
    try { const result = await getWebhookDeliveries(webhookId); setDeliveries(result.data); }
    catch { setDeliveries([]); }
    finally { setDeliveriesLoading(false); }
  }

  function toggleExpand(webhookId: string) {
    if (expandedId === webhookId) { setExpandedId(null); }
    else { setExpandedId(webhookId); loadDeliveries(webhookId); }
  }

  function openCreate() { setEditingId(null); setForm(emptyForm); setDialogOpen(true); }
  function openEdit(webhook: Webhook) { setEditingId(webhook.id); setForm(webhookToForm(webhook)); setDialogOpen(true); }

  function toggleEvent(event: string) {
    setForm((prev) => ({
      ...prev,
      events: prev.events.includes(event) ? prev.events.filter((e) => e !== event) : [...prev.events, event],
    }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (form.events.length === 0) { toast.error('Select at least one event'); return; }
    setSaving(true);
    try {
      const data: CreateWebhookRequest = { url: form.url, events: form.events, active: form.active };
      if (editingId) { await updateWebhook(editingId, data); toast.success('Webhook updated'); }
      else { await createWebhook(data); toast.success('Webhook created'); }
      setDialogOpen(false); await loadWebhooks();
    } catch (err: unknown) { const message = err instanceof Error ? err.message : 'Unknown error'; toast.error(editingId ? 'Failed to update webhook' : 'Failed to create webhook', { description: message }); }
    finally { setSaving(false); }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try { await deleteWebhook(deleteTarget.id); toast.success('Webhook deleted'); if (expandedId === deleteTarget.id) setExpandedId(null); setDeleteTarget(null); await loadWebhooks(); }
    catch (err: unknown) { const message = err instanceof Error ? err.message : 'Unknown error'; toast.error('Failed to delete webhook', { description: message }); }
    finally { setDeleting(false); }
  }

  function toggleSecretVisibility(id: string) {
    setVisibleSecrets((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  function copySecret(secret: string) {
    navigator.clipboard.writeText(secret).then(
      () => toast.success('Secret copied to clipboard'),
      () => toast.error('Failed to copy secret'),
    );
  }

  function formatDate(iso: string) { return new Date(iso).toLocaleString(); }

  return (
    <div className="animate-slide-up">
      <PageHeader title="Webhooks" subtitle="Receive real-time event notifications via HTTP">
        <Button onClick={openCreate} className="font-semibold"><Plus size={15} className="mr-2" />Create Webhook</Button>
      </PageHeader>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-display">{editingId ? 'Edit Webhook' : 'Create Webhook'}</DialogTitle>
            <DialogDescription>{editingId ? 'Update webhook configuration.' : 'Add a new webhook endpoint.'}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs font-medium">URL</Label>
              <Input value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} required type="url" placeholder="https://your-server.com/webhook" className="h-10 font-mono text-sm" />
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-medium">Events</Label>
              <div className="flex flex-wrap gap-1.5">
                {WEBHOOK_EVENTS.map((event) => (
                  <Badge
                    key={event}
                    variant={form.events.includes(event) ? 'default' : 'outline'}
                    className="cursor-pointer text-[10px] transition-colors hover:border-primary/50"
                    onClick={() => toggleEvent(event)}
                  >
                    {event}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={form.active} onCheckedChange={(checked) => setForm({ ...form, active: checked })} />
              <Label className="text-xs font-medium">Active</Label>
            </div>
            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={saving} className="font-semibold">{saving ? 'Saving...' : editingId ? 'Update' : 'Create'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteTarget !== null} onOpenChange={(open) => !open && setDeleteTarget(null)} title="Delete Webhook" description={`Are you sure you want to delete the webhook for "${deleteTarget?.url ?? ''}"? This action cannot be undone.`} confirmLabel="Delete" variant="destructive" loading={deleting} onConfirm={handleDelete} />

      {loading ? (
        <Card><CardContent className="p-0"><div className="p-4 space-y-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-16 w-full" />)}</div></CardContent></Card>
      ) : webhooks.length === 0 ? (
        <Card className="border-dashed"><CardContent className="py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4"><Bell size={24} className="text-muted-foreground/40" /></div>
          <h2 className="text-base font-display font-semibold mb-1">No webhooks yet</h2>
          <p className="text-sm text-muted-foreground mb-5">Create webhooks to receive real-time event notifications.</p>
          <Button onClick={openCreate} className="font-semibold">Create Webhook</Button>
        </CardContent></Card>
      ) : (
        <div className="space-y-3 stagger-children">
          {webhooks.map((webhook) => (
            <Card key={webhook.id} className="group transition-all duration-200 hover:border-border/80">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Button variant="ghost" size="icon" className="shrink-0 h-8 w-8" onClick={() => toggleExpand(webhook.id)}>
                    {expandedId === webhook.id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </Button>

                  <div className="w-9 h-9 rounded-xl bg-chart-3/10 flex items-center justify-center shrink-0">
                    <Bell size={15} className="text-chart-3" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-sm truncate">{webhook.url}</span>
                      <Badge variant={webhook.active ? 'default' : 'secondary'} className="text-[10px]">
                        {webhook.active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {webhook.events.map((event) => (
                        <Badge key={event} variant="outline" className="text-[10px]">{event}</Badge>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-1">
                    <div className="flex items-center gap-1 mr-2">
                      <code className="text-[10px] text-muted-foreground bg-muted px-2 py-1 rounded font-mono max-w-[100px] truncate">
                        {visibleSecrets.has(webhook.id) ? webhook.secret : `${webhook.secret.slice(0, 8)}...`}
                      </code>
                      <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => toggleSecretVisibility(webhook.id)}>
                        {visibleSecrets.has(webhook.id) ? <EyeOff size={11} /> : <Eye size={11} />}
                      </Button>
                      <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => copySecret(webhook.secret)}>
                        <Copy size={11} />
                      </Button>
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button variant="ghost" size="icon" onClick={() => openEdit(webhook)} className="h-8 w-8"><Pencil size={12} /></Button>
                      <Button variant="ghost" size="icon" onClick={() => setDeleteTarget({ id: webhook.id, url: webhook.url })} className="h-8 w-8 text-muted-foreground hover:text-destructive"><Trash2 size={12} /></Button>
                    </div>
                  </div>
                </div>

                {expandedId === webhook.id && (
                  <div className="mt-4 border-t border-border/50 pt-4">
                    <h3 className="text-xs font-display font-semibold mb-3 text-muted-foreground uppercase tracking-wider">Delivery History</h3>
                    {deliveriesLoading ? (
                      <div className="space-y-2">{[1, 2].map((i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
                    ) : deliveries.length === 0 ? (
                      <p className="text-xs text-muted-foreground py-4 text-center">No deliveries yet.</p>
                    ) : (
                      <Table>
                        <TableHeader><TableRow className="hover:bg-transparent">
                          <TableHead className="text-[10px]">Event</TableHead>
                          <TableHead className="text-[10px]">Status</TableHead>
                          <TableHead className="text-[10px]">Code</TableHead>
                          <TableHead className="text-[10px]">Time</TableHead>
                          <TableHead className="text-[10px]">Attempt</TableHead>
                          <TableHead className="text-[10px]">Date</TableHead>
                        </TableRow></TableHeader>
                        <TableBody>
                          {deliveries.map((d) => (
                            <TableRow key={d.id}>
                              <TableCell className="text-[10px] font-mono">{d.event}</TableCell>
                              <TableCell>
                                <Badge variant={d.status === 'success' ? 'default' : d.status === 'failed' ? 'destructive' : 'secondary'} className="text-[10px]">{d.status}</Badge>
                              </TableCell>
                              <TableCell className="text-[10px] text-muted-foreground font-mono">{d.responseCode ?? '—'}</TableCell>
                              <TableCell className="text-[10px] text-muted-foreground">{d.responseTime != null ? `${d.responseTime}ms` : '—'}</TableCell>
                              <TableCell className="text-[10px] text-muted-foreground">#{d.attemptNumber}</TableCell>
                              <TableCell className="text-[10px] text-muted-foreground">{formatDate(d.createdAt)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
