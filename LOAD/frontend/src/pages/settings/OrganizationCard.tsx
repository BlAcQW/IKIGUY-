import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Building2, Loader2 } from 'lucide-react';
import { getOrganization, updateOrganization } from '@/lib/api';
import type { Organization } from '@/types';

interface OrganizationCardProps {
  userRole: string;
}

export function OrganizationCard({ userRole }: OrganizationCardProps) {
  const [org, setOrg] = useState<Organization | null>(null);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const canEdit = userRole === 'OWNER' || userRole === 'ADMIN';
  const isDirty = org !== null && name !== org.name;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await getOrganization();
        if (cancelled) return;
        setOrg(res.data);
        setName(res.data.name);
      } catch {
        if (!cancelled) toast.error('Failed to load organization');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  async function handleSave() {
    if (!isDirty || !canEdit) return;
    setSaving(true);
    try {
      const res = await updateOrganization({ name: name.trim() });
      setOrg(res.data);
      setName(res.data.name);
      toast.success('Organization updated');
    } catch (err) {
      toast.error('Failed to update organization', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className="mb-4">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-500/10">
            <Building2 size={16} className="text-purple-500" />
          </div>
          <div>
            <CardTitle className="text-base font-display">Organization</CardTitle>
            <CardDescription className="text-xs">
              Workspace details and billing plan
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? (
          <div className="flex items-center gap-2 text-xs text-muted-foreground py-4">
            <Loader2 size={14} className="animate-spin" />
            Loading...
          </div>
        ) : org ? (
          <>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label className="text-xs">Organization Name</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="h-8 text-sm"
                  disabled={!canEdit}
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Slug</Label>
                <Input
                  value={org.slug}
                  className="h-8 text-sm bg-muted/50"
                  disabled
                />
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Plan</Label>
                <div>
                  <Badge variant={org.plan === 'FREE' ? 'secondary' : 'default'} className="text-xs">
                    {org.plan}
                  </Badge>
                </div>
              </div>
            </div>
            {isDirty && canEdit && (
              <Button size="sm" onClick={handleSave} disabled={saving} className="text-xs gap-1.5">
                {saving && <Loader2 size={12} className="animate-spin" />}
                Save Organization
              </Button>
            )}
            {!canEdit && (
              <p className="text-xs text-muted-foreground">Only owners and admins can edit organization settings.</p>
            )}
          </>
        ) : (
          <p className="text-xs text-muted-foreground">Failed to load organization details.</p>
        )}
      </CardContent>
    </Card>
  );
}
