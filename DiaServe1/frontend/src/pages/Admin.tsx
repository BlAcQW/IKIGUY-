/**
 * EstateFlow Admin Page
 *
 * Universal admin panel for managing organizations, users, and system settings.
 * Only accessible to admin@ailabsafrica.com or users with role=admin.
 */

import { useState } from "react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { inviteUser, listUsers, listPendingInvitations } from "@/lib/api/user-api";
import type { UserInvite, User, PendingInvitation } from "@/lib/api/user-api";
import {
  Building2,
  Users,
  Plus,
  Edit,
  Trash2,
  Mail,
  UserPlus,
  Shield,
  Settings,
  Eye,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EmptyState } from "@/components/ui/empty-state";

interface TeamMember {
  id: string;
  email: string;
  name?: string;
  role: "admin" | "manager" | "agent" | "user";
  organization_id: string;
  status: "active" | "invited" | "suspended";
  created_at?: string;
}

export default function Admin() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Check if user is universal admin
  const isAdmin = user?.role === 'admin' || user?.email === 'admin@ailabsafrica.com' || user?.email === 'admin@estateflow.local';

  // Invitation form state
  const [inviteForm, setInviteForm] = useState({
    email: "",
    name: "",
    role: "user" as "admin" | "manager" | "agent" | "user",
    organization_id: "default", // Hardcoded for single-tenant
  });

  // Mock team members (replace with real API)
  const [teamMembers] = useState<TeamMember[]>([
    {
      id: "1",
      email: "admin@ailabsafrica.com",
      name: "System Admin",
      role: "admin",
      organization_id: "default",
      status: "active",
      created_at: "2025-01-01",
    },
  ]);

  if (!isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <EmptyState
          icon={Shield}
          title="Access Denied"
          description="You don't have permission to access the admin panel. Please contact your administrator."
        />
      </div>
    );
  }

  const handleInviteUser = async () => {
    if (!inviteForm.email || !inviteForm.organization_id) {
      toast({
        title: "Validation Error",
        description: "Email and organization are required",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsLoading(true);
      const inviteData: UserInvite = {
        email: inviteForm.email,
        name: inviteForm.name || undefined,
        role: inviteForm.role as any,
        organization_id: inviteForm.organization_id,
      };

      const result = await inviteUser(inviteData);

      toast({
        title: "Invitation Sent",
        description: `Invitation sent to ${result.email}. They have 7 days to accept.`,
      });

      setInviteDialogOpen(false);
      setInviteForm({ email: "", name: "", role: "user", organization_id: "default" });
    } catch (error) {
      console.error("Failed to invite user:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to invite user",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Header
        title="Admin Panel"
        subtitle="Manage organizations, users, and system settings"
        actions={
          <Badge variant="premium" className="gap-1">
            <Shield className="h-3 w-3" />
            Universal Admin
          </Badge>
        }
      />

      <div className="p-6">
        <Tabs defaultValue="users" className="space-y-6">
          <TabsList>
            <TabsTrigger value="users" className="gap-2">
              <Users className="h-4 w-4" />
              Users & Invitations
            </TabsTrigger>
            <TabsTrigger value="system" className="gap-2">
              <Settings className="h-4 w-4" />
              System Settings
            </TabsTrigger>
          </TabsList>

          {/* Users & Invitations Tab */}
          <TabsContent value="users" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold">Users & Invitations</h2>
                <p className="text-muted-foreground">Invite users and manage team members</p>
              </div>
              <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="gradient" className="gap-2">
                    <UserPlus className="h-4 w-4" />
                    Invite User
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-lg">
                  <DialogHeader>
                    <DialogTitle>Invite User via Email</DialogTitle>
                    <DialogDescription>
                      Send an invitation email to add a new user to the system
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div>
                      <Label htmlFor="invite-email">Email Address *</Label>
                      <Input
                        id="invite-email"
                        type="email"
                        value={inviteForm.email}
                        onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                        placeholder="user@example.com"
                      />
                    </div>
                    <div>
                      <Label htmlFor="invite-name">Full Name</Label>
                      <Input
                        id="invite-name"
                        value={inviteForm.name}
                        onChange={(e) => setInviteForm({ ...inviteForm, name: e.target.value })}
                        placeholder="John Doe"
                      />
                    </div>
                    <div>
                      <Label htmlFor="invite-role">Role *</Label>
                      <Select
                        value={inviteForm.role}
                        onValueChange={(value: any) => setInviteForm({ ...inviteForm, role: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="user">User (View Only)</SelectItem>
                          <SelectItem value="agent">Agent (Manage Properties)</SelectItem>
                          <SelectItem value="manager">Manager (Full Access)</SelectItem>
                          <SelectItem value="admin">Admin (System Admin)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      onClick={() => setInviteDialogOpen(false)}
                      disabled={isLoading}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="gradient"
                      onClick={handleInviteUser}
                      disabled={!inviteForm.email || isLoading}
                    >
                      <Mail className="h-4 w-4 mr-2" />
                      {isLoading ? "Sending..." : "Send Invitation"}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>

            <Card variant="elevated">
              <CardHeader>
                <CardTitle>All Users</CardTitle>
                <CardDescription>Manage team members and their access levels</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {teamMembers.map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-secondary/50 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-primary to-secondary text-white font-semibold">
                          {member.name?.[0] || member.email[0].toUpperCase()}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{member.name || member.email}</p>
                            <Badge variant={member.role === "admin" ? "premium" : "soft"}>
                              {member.role}
                            </Badge>
                            <Badge
                              variant={
                                member.status === "active" ? "soft-success" :
                                  member.status === "invited" ? "soft-warning" : "soft"
                              }
                            >
                              {member.status}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">{member.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Edit className="h-4 w-4" />
                        </Button>
                        {member.role !== 'admin' && (
                          <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive hover:bg-destructive/10">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* System Settings Tab */}
          <TabsContent value="system">
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>System Settings</CardTitle>
                <CardDescription>Configure global system settings</CardDescription>
              </CardHeader>
              <CardContent>
                <EmptyState
                  icon={Settings}
                  title="System Settings"
                  description="Global system configuration options will appear here"
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
