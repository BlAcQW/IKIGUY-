import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Users, Loader2, Trash2 } from 'lucide-react';
import { listOrgMembers, removeOrgMember, type OrgMember } from '@/lib/api';

interface TeamCardProps {
  userRole: string;
  currentUserId: string;
}

const roleBadgeVariant = (role: string) => {
  switch (role) {
    case 'OWNER': return 'default' as const;
    case 'ADMIN': return 'secondary' as const;
    default: return 'outline' as const;
  }
};

export function TeamCard({ userRole, currentUserId }: TeamCardProps) {
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState<string | null>(null);

  const isOwner = userRole === 'OWNER';

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await listOrgMembers();
        if (!cancelled) setMembers(res.data);
      } catch {
        if (!cancelled) toast.error('Failed to load team members');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  async function handleRemove(userId: string) {
    if (!confirm('Remove this team member? This action cannot be undone.')) return;
    setRemovingId(userId);
    try {
      await removeOrgMember(userId);
      setMembers((prev) => prev.filter((m) => m.id !== userId));
      toast.success('Member removed');
    } catch (err) {
      toast.error('Failed to remove member', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <Card className="mb-4">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-green-500/10">
            <Users size={16} className="text-green-500" />
          </div>
          <div className="flex-1">
            <CardTitle className="text-base font-display">Team</CardTitle>
            <CardDescription className="text-xs">
              Manage organization members and roles
            </CardDescription>
          </div>
          {!loading && (
            <Badge variant="secondary" className="text-xs">
              {members.length} member{members.length !== 1 ? 's' : ''}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center gap-2 text-xs text-muted-foreground py-4">
            <Loader2 size={14} className="animate-spin" />
            Loading...
          </div>
        ) : members.length === 0 ? (
          <p className="text-xs text-muted-foreground">No team members found.</p>
        ) : (
          <div className="space-y-2">
            {members.map((member) => (
              <div
                key={member.id}
                className="flex items-center justify-between px-3 py-2.5 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium text-primary shrink-0">
                    {member.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium truncate">{member.name}</span>
                      {member.id === currentUserId && (
                        <span className="text-[10px] text-muted-foreground">(you)</span>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground truncate block">{member.email}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Badge variant={roleBadgeVariant(member.role)} className="text-[10px]">
                    {member.role}
                  </Badge>
                  {isOwner && member.id !== currentUserId && member.role !== 'OWNER' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
                      onClick={() => handleRemove(member.id)}
                      disabled={removingId === member.id}
                    >
                      {removingId === member.id ? (
                        <Loader2 size={12} className="animate-spin" />
                      ) : (
                        <Trash2 size={12} />
                      )}
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
