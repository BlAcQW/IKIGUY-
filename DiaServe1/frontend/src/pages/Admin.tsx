/**
 * EstateFlow Admin Page
 *
 * Universal admin panel for managing organizations, users, and system settings.
 * Only accessible to admin@ailabsafrica.com or users with role=admin.
 */

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { inviteUser, listUsers, listPendingInvitations } from "@/lib/api/user-api";
import type { UserInvite, User, PendingInvitation } from "@/lib/api/user-api";
import { updateExchangeRate, getExchangeRates } from "@/lib/api/currency-api";
import { useExchangeRates, currencyKeys } from "@/hooks/use-currencies";
import { useQueryClient } from "@tanstack/react-query";
import {
  Users,
  Edit,
  Trash2,
  Mail,
  UserPlus,
  Shield,
  Settings,
  Eye,
  Loader2,
  Clock,
  RefreshCw,
  DollarSign,
  Save,
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

function ExchangeRateManager() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { data: exchangeRates, isLoading: isLoadingRates } = useExchangeRates();
  const [rateInput, setRateInput] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Sync input with current GHS rate when data loads
  useEffect(() => {
    if (exchangeRates?.rates?.GHS) {
      setRateInput(exchangeRates.rates.GHS.toString());
    }
  }, [exchangeRates?.rates?.GHS]);

  const isAdminRate = exchangeRates?.source === "admin-override";

  const handleSaveRate = async () => {
    const numRate = parseFloat(rateInput);
    if (isNaN(numRate) || numRate <= 0) {
      toast({
        title: "Invalid Rate",
        description: "Please enter a positive number",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSaving(true);
      await updateExchangeRate("GHS", numRate);
      await queryClient.invalidateQueries({ queryKey: currencyKeys.all });
      toast({
        title: "Rate Updated",
        description: `Exchange rate set to 1 USD = ${numRate} GHS`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update rate",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleRefreshFromApi = async () => {
    try {
      setIsRefreshing(true);
      await getExchangeRates(true);
      await queryClient.invalidateQueries({ queryKey: currencyKeys.all });
      toast({
        title: "Rates Refreshed",
        description: "Exchange rates fetched from external API",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to refresh rates",
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const lastUpdated = exchangeRates?.last_updated
    ? new Date(exchangeRates.last_updated).toLocaleString()
    : "N/A";

  const adminSetAt = exchangeRates?.admin_rate?.set_at
    ? new Date(exchangeRates.admin_rate.set_at).toLocaleString()
    : null;

  return (
    <Card variant="elevated">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5" />
              Exchange Rate Management
            </CardTitle>
            <CardDescription>
              Set the USD to GHS exchange rate used across the platform
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshFromApi}
            disabled={isRefreshing}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh from API
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Rate Display */}
        <div className="rounded-lg border p-4 bg-secondary/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Current Rate</p>
              {isLoadingRates ? (
                <Loader2 className="h-5 w-5 animate-spin mt-1" />
              ) : (
                <p className="text-2xl font-bold">
                  1 USD = {exchangeRates?.rates?.GHS?.toFixed(2) ?? "—"} GHS
                </p>
              )}
            </div>
            <Badge variant={isAdminRate ? "premium" : "soft"}>
              {isAdminRate ? "Admin Set" : "API Rate"}
            </Badge>
          </div>
          <div className="mt-2 text-xs text-muted-foreground space-y-0.5">
            <p>Last updated: {lastUpdated}</p>
            {isAdminRate && exchangeRates?.admin_rate?.set_by && (
              <p>
                Set by: {exchangeRates.admin_rate.set_by}
                {adminSetAt ? ` on ${adminSetAt}` : ""}
              </p>
            )}
          </div>
        </div>

        {/* Rate Input */}
        <div className="space-y-3">
          <Label htmlFor="ghs-rate">Set GHS Rate (1 USD = X GHS)</Label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">
                GH¢
              </span>
              <Input
                id="ghs-rate"
                type="number"
                step="0.01"
                min="0.01"
                value={rateInput}
                onChange={(e) => setRateInput(e.target.value)}
                className="pl-12"
                placeholder="15.50"
              />
            </div>
            <Button
              onClick={handleSaveRate}
              disabled={isSaving || !rateInput}
              className="gap-2"
            >
              {isSaving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Save Rate
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            This rate will override the external API rate for all users.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

export default function Admin() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Check if user is universal admin
  const isAdmin = user?.role === 'admin' || user?.email === 'admin@ailabsafrica.com' || user?.email === 'admin@estateflow.com';

  // Invitation form state
  const [inviteForm, setInviteForm] = useState({
    email: "",
    name: "",
    role: "user" as "admin" | "manager" | "agent" | "user",
    organization_id: "default", // Hardcoded for single-tenant
  });

  // Real user/invitation data
  const [teamMembers, setTeamMembers] = useState<User[]>([]);
  const [pendingInvitations, setPendingInvitations] = useState<PendingInvitation[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);

  const fetchUsersAndInvitations = useCallback(async () => {
    try {
      setIsLoadingUsers(true);
      const [usersRes, invitationsRes] = await Promise.all([
        listUsers(),
        listPendingInvitations(),
      ]);
      setTeamMembers(usersRes.users);
      setPendingInvitations(invitationsRes.invitations);
    } catch (error) {
      console.error("Failed to fetch users:", error);
    } finally {
      setIsLoadingUsers(false);
    }
  }, []);

  useEffect(() => {
    if (isAdmin) {
      fetchUsersAndInvitations();
    }
  }, [isAdmin, fetchUsersAndInvitations]);

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
      fetchUsersAndInvitations();
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
                {isLoadingUsers ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : teamMembers.length === 0 ? (
                  <EmptyState
                    icon={Users}
                    title="No Users Found"
                    description="Invite your first team member to get started"
                  />
                ) : (
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
                )}
              </CardContent>
            </Card>

            {/* Pending Invitations */}
            {pendingInvitations.length > 0 && (
              <Card variant="elevated">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Pending Invitations
                  </CardTitle>
                  <CardDescription>Invitations awaiting acceptance</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {pendingInvitations.map((invitation) => (
                      <div
                        key={invitation.token}
                        className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-secondary/50 transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-warning/20 text-warning font-semibold">
                            <Mail className="h-5 w-5" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-medium">{invitation.name || invitation.email}</p>
                              <Badge variant="soft">{invitation.role}</Badge>
                              <Badge variant="soft-warning">pending</Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {invitation.email} — Expires {new Date(invitation.expires_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* System Settings Tab */}
          <TabsContent value="system" className="space-y-6">
            <ExchangeRateManager />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
