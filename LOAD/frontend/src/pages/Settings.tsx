import React, { useEffect, useState } from 'react';
import { listApiKeys, createApiKey, revokeApiKey } from '../lib/api';
import { PageHeader } from '@/components/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertDialog } from '@/components/ui/alert-dialog';
import { Key, Plus, Trash2, Copy, Shield, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

interface ApiKeyItem {
  id: string;
  prefix: string;
  name: string;
  lastUsedAt: string | null;
  createdAt: string;
}

export function SettingsPage() {
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState<{ id: string; name: string } | null>(null);
  const [revoking, setRevoking] = useState(false);

  async function loadKeys() {
    try {
      const result = await listApiKeys();
      setKeys(result.data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Failed to load API keys', { description: message });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadKeys();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    setCreating(true);
    try {
      const result = await createApiKey({ name: newKeyName });
      setCreatedKey(result.data.key);
      setNewKeyName('');
      setShowKey(true);
      toast.success('API key created');
      await loadKeys();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Failed to create API key', { description: message });
    } finally {
      setCreating(false);
    }
  }

  async function handleRevoke() {
    if (!revokeTarget) return;
    setRevoking(true);
    try {
      await revokeApiKey(revokeTarget.id);
      toast.success('API key revoked');
      setRevokeTarget(null);
      await loadKeys();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Failed to revoke API key', { description: message });
    } finally {
      setRevoking(false);
    }
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  }

  return (
    <div className="animate-slide-up max-w-3xl">
      <PageHeader title="Settings" subtitle="API keys, account settings, and configuration" />

      <AlertDialog open={revokeTarget !== null} onOpenChange={(open) => !open && setRevokeTarget(null)} title="Revoke API Key" description={`Are you sure you want to revoke "${revokeTarget?.name ?? ''}"? This cannot be undone. Any integrations using this key will stop working.`} confirmLabel="Revoke" variant="destructive" loading={revoking} onConfirm={handleRevoke} />

      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Key size={16} className="text-primary" />
            </div>
            <div>
              <CardTitle className="text-base font-display">API Keys</CardTitle>
              <CardDescription className="text-xs">API keys are used for programmatic access. Keep them secret.</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="flex gap-3 mb-6">
            <Input
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="Key name (e.g., Production)"
              className="flex-1 h-10"
            />
            <Button type="submit" disabled={creating || !newKeyName.trim()} className="font-semibold h-10">
              <Plus size={15} className="mr-1.5" />
              Create Key
            </Button>
          </form>

          {createdKey && (
            <div className="bg-primary/5 border border-primary/15 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-2 mb-2.5">
                <Shield size={14} className="text-primary" />
                <p className="text-xs font-semibold text-primary">
                  API key created. Copy it now — you won't see it again.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-background px-3 py-2.5 rounded-lg text-xs font-mono border overflow-x-auto scrollbar-thin">
                  {showKey ? createdKey : createdKey.slice(0, 16) + '...' + createdKey.slice(-8)}
                </code>
                <Button variant="ghost" size="icon" className="h-9 w-9 shrink-0" onClick={() => setShowKey(!showKey)}>
                  {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
                </Button>
                <Button variant="ghost" size="icon" className="h-9 w-9 shrink-0" onClick={() => copyToClipboard(createdKey)}>
                  <Copy size={14} />
                </Button>
              </div>
            </div>
          )}

          {loading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : keys.length === 0 ? (
            <div className="text-center py-10">
              <div className="w-12 h-12 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-3">
                <Key size={20} className="text-muted-foreground/40" />
              </div>
              <p className="text-sm text-muted-foreground">No API keys yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {keys.map((key) => (
                <div key={key.id} className="flex items-center justify-between p-3.5 bg-muted/30 rounded-lg border border-border/50 group hover:border-border transition-colors">
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center shrink-0">
                      <Key size={13} className="text-muted-foreground" />
                    </div>
                    <div className="min-w-0">
                      <span className="text-sm font-medium block">{key.name}</span>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[11px] text-muted-foreground font-mono">{key.prefix}...</span>
                        <span className="text-[11px] text-muted-foreground">
                          Created {new Date(key.createdAt).toLocaleDateString()}
                        </span>
                        {key.lastUsedAt && (
                          <span className="text-[11px] text-muted-foreground hidden sm:inline">
                            Last used {new Date(key.lastUsedAt).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setRevokeTarget({ id: key.id, name: key.name })}
                    className="text-muted-foreground hover:text-destructive shrink-0 h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 size={14} />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
