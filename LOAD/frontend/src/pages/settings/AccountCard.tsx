import { useState } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { User, Loader2 } from 'lucide-react';
import { updateProfile } from '@/lib/api';

interface AccountCardProps {
  userName: string;
  userEmail: string;
  onProfileUpdated: () => void;
}

export function AccountCard({ userName, userEmail, onProfileUpdated }: AccountCardProps) {
  const [name, setName] = useState(userName);
  const [email, setEmail] = useState(userEmail);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [saving, setSaving] = useState(false);

  const profileDirty = name !== userName || email !== userEmail;
  const passwordReady = currentPassword.length > 0 && newPassword.length >= 8;

  async function handleSaveProfile() {
    setSaving(true);
    try {
      const updates: Record<string, string> = {};
      if (name !== userName) updates.name = name;
      if (email !== userEmail) updates.email = email;
      await updateProfile(updates);
      toast.success('Profile updated');
      onProfileUpdated();
    } catch (err) {
      toast.error('Failed to update profile', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleChangePassword() {
    setSaving(true);
    try {
      await updateProfile({ currentPassword, newPassword });
      toast.success('Password changed');
      setCurrentPassword('');
      setNewPassword('');
    } catch (err) {
      toast.error('Failed to change password', {
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
          <div className="p-2 rounded-lg bg-blue-500/10">
            <User size={16} className="text-blue-500" />
          </div>
          <div>
            <CardTitle className="text-base font-display">Account</CardTitle>
            <CardDescription className="text-xs">
              Your personal profile and password
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label className="text-xs">Name</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="h-8 text-sm"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Email</Label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-8 text-sm"
            />
          </div>
        </div>
        {profileDirty && (
          <Button size="sm" onClick={handleSaveProfile} disabled={saving} className="text-xs gap-1.5">
            {saving && <Loader2 size={12} className="animate-spin" />}
            Save Profile
          </Button>
        )}

        <Separator />

        <div className="space-y-3">
          <p className="text-xs font-medium text-muted-foreground">Change Password</p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label className="text-xs">Current Password</Label>
              <Input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="h-8 text-sm"
                placeholder="Enter current password"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">New Password</Label>
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="h-8 text-sm"
                placeholder="Min 8 characters"
              />
            </div>
          </div>
          {passwordReady && (
            <Button size="sm" variant="outline" onClick={handleChangePassword} disabled={saving} className="text-xs gap-1.5">
              {saving && <Loader2 size={12} className="animate-spin" />}
              Change Password
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
