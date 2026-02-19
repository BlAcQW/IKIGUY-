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
import { useOrganization } from "@/contexts/OrganizationContext";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { createOrganization, updateOrganization, deleteOrganization } from "@/lib/api/organization-api";
import type { OrganizationCreate, OrganizationUpdate } from "@/lib/api/organization-api";
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

interface Organization {
  id: string;
  name: string;
  description?: string;
  email?: string;
  phone?: string;
  created_at?: string;
}

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
  const { organizations, refreshOrganizations } = useOrganization();
  const { toast } = useToast();
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [orgDialogOpen, setOrgDialogOpen] = useState(false);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Check if user is universal admin
  const isAdmin = user?.user_metadata?.role === 'admin' || user?.email === 'admin@ailabsafrica.com';

  // Organization form state
  const [orgForm, setOrgForm] = useState<Partial<Organization>>({
    name: "",
    description: "",
    email: "",
    phone: "",
  });

  // Invitation form state
  const [inviteForm, setInviteForm] = useState({
    email: "",
    name: "",
    role: "user" as "admin" | "manager" | "agent" | "user",
    organization_id: "",
  });

  // Mock team members (replace with real API)
  const [teamMembers] = useState<TeamMember[]>([
    {
      id: "1",
      email: "admin@ailabsafrica.com",
      name: "System Admin",
      role: "admin",
      organization_id: "all",
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

  const handleCreateOrganization = async () => {
    if (!orgForm.name) {
      toast({
        title: "Validation Error",
        description: "Organization name is required",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsLoading(true);
      const orgData: OrganizationCreate = {
        name: orgForm.name,
        description: orgForm.description,
        email: orgForm.email,
        phone: orgForm.phone,
      };

      const newOrg = await createOrganization(orgData);

      toast({
        title: "Organization Created",
        description: `${newOrg.name} has been created successfully`,
      });

      setOrgDialogOpen(false);
      setOrgForm({ name: "", description: "", email: "", phone: "" });
      await refreshOrganizations();
    } catch (error) {
      console.error("Failed to create organization:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create organization",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateOrganization = async () => {
    if (!selectedOrg?.id) {
      toast({
        title: "Error",
        description: "No organization selected",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsLoading(true);
      const updateData: OrganizationUpdate = {};

      // Only include changed fields
      if (orgForm.name && orgForm.name !== selectedOrg.name) {
        updateData.name = orgForm.name;
      }
      if (orgForm.description !== selectedOrg.description) {
        updateData.description = orgForm.description;
      }
      if (orgForm.email !== selectedOrg.email) {
        updateData.email = orgForm.email;
      }
      if (orgForm.phone !== selectedOrg.phone) {
        updateData.phone = orgForm.phone;
      }

      const updatedOrg = await updateOrganization(selectedOrg.id, updateData);

      toast({
        title: "Organization Updated",
        description: `${updatedOrg.name} has been updated successfully`,
      });

      setOrgDialogOpen(false);
      setSelectedOrg(null);
      setOrgForm({ name: "", description: "", email: "", phone: "" });
      await refreshOrganizations();
    } catch (error) {
      console.error("Failed to update organization:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update organization",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteOrganization = async (orgId: string) => {
    const org = organizations.find(o => o.id === orgId);
    if (!org) return;

    if (!confirm(`Are you sure you want to delete "${org.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setIsLoading(true);
      await deleteOrganization(orgId);

      toast({
        title: "Organization Deleted",
        description: `${org.name} has been deleted successfully`,
      });

      await refreshOrganizations();
    } catch (error) {
      console.error("Failed to delete organization:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to delete organization",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

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
      setInviteForm({ email: "", name: "", role: "user", organization_id: "" });
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

  const openEditDialog = (org: Organization) => {
    setSelectedOrg(org);
    setOrgForm({
      name: org.name,
      description: org.description,
      email: org.email,
      phone: org.phone,
    });
    setOrgDialogOpen(true);
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
        <Tabs defaultValue="organizations" className="space-y-6">
          <TabsList>
            <TabsTrigger value="organizations" className="gap-2">
              <Building2 className="h-4 w-4" />
              Organizations
            </TabsTrigger>
            <TabsTrigger value="users" className="gap-2">
              <Users className="h-4 w-4" />
              Users & Invitations
            </TabsTrigger>
            <TabsTrigger value="system" className="gap-2">
              <Settings className="h-4 w-4" />
              System Settings
            </TabsTrigger>
          </TabsList>

          {/* Organizations Tab */}
          <TabsContent value="organizations" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold">Organizations</h2>
                <p className="text-muted-foreground">Manage all organizations in the system</p>
              </div>
              <Dialog open={orgDialogOpen} onOpenChange={setOrgDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="gradient" className="gap-2" onClick={() => {
                    setSelectedOrg(null);
                    setOrgForm({ name: "", description: "", email: "", phone: "" });
                  }}>
                    <Plus className="h-4 w-4" />
                    Create Organization
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>
                      {selectedOrg ? "Edit Organization" : "Create New Organization"}
                    </DialogTitle>
                    <DialogDescription>
                      {selectedOrg
                        ? "Update organization details and settings"
                        : "Add a new organization to the system"}
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div>
                      <Label htmlFor="org-name">Organization Name *</Label>
                      <Input
                        id="org-name"
                        value={orgForm.name}
                        onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })}
                        placeholder="Acme Real Estate Ltd"
                      />
                    </div>
                    <div>
                      <Label htmlFor="org-email">Email</Label>
                      <Input
                        id="org-email"
                        type="email"
                        value={orgForm.email}
                        onChange={(e) => setOrgForm({ ...orgForm, email: e.target.value })}
                        placeholder="contact@acmerealestate.com"
                      />
                    </div>
                    <div>
                      <Label htmlFor="org-phone">Phone</Label>
                      <Input
                        id="org-phone"
                        value={orgForm.phone}
                        onChange={(e) => setOrgForm({ ...orgForm, phone: e.target.value })}
                        placeholder="+233 24 123 4567"
                      />
                    </div>
                    <div>
                      <Label htmlFor="org-description">Description</Label>
                      <Textarea
                        id="org-description"
                        rows={4}
                        value={orgForm.description}
                        onChange={(e) => setOrgForm({ ...orgForm, description: e.target.value })}
                        placeholder="Brief description of the organization..."
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      onClick={() => setOrgDialogOpen(false)}
                      disabled={isLoading}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="gradient"
                      onClick={selectedOrg ? handleUpdateOrganization : handleCreateOrganization}
                      disabled={!orgForm.name || isLoading}
                    >
                      {isLoading ? "Saving..." : selectedOrg ? "Update Organization" : "Create Organization"}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {organizations.map((org, index) => (
                <Card
                  key={org.id}
                  variant="elevated"
                  className="animate-scale-in"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-primary/20 to-secondary/20">
                          <Building2 className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <CardTitle className="text-lg">{org.name}</CardTitle>
                          <CardDescription className="text-xs">ID: {org.id.slice(0, 8)}...</CardDescription>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {org.email && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Mail className="h-4 w-4" />
                        {org.email}
                      </div>
                    )}
                    {org.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">{org.description}</p>
                    )}
                    <div className="flex gap-2 pt-2">
                      <Button
                        variant="soft"
                        size="sm"
                        className="flex-1"
                        onClick={() => openEditDialog(org)}
                        disabled={isLoading}
                      >
                        <Edit className="h-3 w-3 mr-1" />
                        Edit
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleDeleteOrganization(org.id)}
                        disabled={isLoading}
                      >
                        <Trash2 className="h-3 w-3 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

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
                      Send an invitation email to add a new user to an organization
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
                      <Label htmlFor="invite-org">Organization *</Label>
                      <Select
                        value={inviteForm.organization_id}
                        onValueChange={(value) => setInviteForm({ ...inviteForm, organization_id: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select organization..." />
                        </SelectTrigger>
                        <SelectContent>
                          {organizations.map((org) => (
                            <SelectItem key={org.id} value={org.id}>
                              {org.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
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
                          <SelectItem value="admin">Admin (Organization Admin)</SelectItem>
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
                      disabled={!inviteForm.email || !inviteForm.organization_id || isLoading}
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
                <CardDescription>Manage users across all organizations</CardDescription>
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
