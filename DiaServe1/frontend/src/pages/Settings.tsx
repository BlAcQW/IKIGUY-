/**
 * EstateFlow Settings Page
 *
 * Organization and user settings management.
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useOrganization } from "@/contexts/OrganizationContext";
import { getUserProfile, updateUserProfile, listUsers, UserProfile, UserProfileUpdate, User } from "@/lib/api/user-api";
import { updateOrganization } from "@/lib/api/organization-api";
import { toast } from "sonner";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Building,
  User as UserIcon,
  Key,
  Bell,
  Users,
  Save,
  Eye,
  EyeOff,
  Loader2,
  Plug,
  CheckCircle,
  XCircle,
  DollarSign,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  useQBOStatus,
  useQBODisconnect,
  getQBOAuthUrl,
} from "@/lib/api/quickbooks-api";
import { useSearchParams } from "react-router-dom";

export default function Settings() {
  const { user } = useAuth();
  const { currentOrganization } = useOrganization();
  const [showApiKeys, setShowApiKeys] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);

  // User Profile State
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [profileForm, setProfileForm] = useState({
    first_name: "",
    last_name: "",
    phone: "",
  });

  // Organization Settings - loaded from context
  const [orgSettings, setOrgSettings] = useState({
    name: "",
    email: "",
    phone: "",
    address: "",
    description: "",
    website: "",
  });

  // Team members state
  const [teamMembers, setTeamMembers] = useState<User[]>([]);
  const [isLoadingTeam, setIsLoadingTeam] = useState(false);

  // Load org settings from context
  useEffect(() => {
    if (currentOrganization) {
      setOrgSettings({
        name: currentOrganization.name || "",
        email: currentOrganization.email || "",
        phone: currentOrganization.phone || "",
        address: "",
        description: currentOrganization.description || "",
        website: "",
      });
    }
  }, [currentOrganization]);

  // Fetch team members
  const fetchTeamMembers = useCallback(async () => {
    try {
      setIsLoadingTeam(true);
      const res = await listUsers();
      setTeamMembers(res.users);
    } catch (error) {
      console.error("Failed to fetch team members:", error);
    } finally {
      setIsLoadingTeam(false);
    }
  }, []);

  // API Keys
  const [apiKeys, setApiKeys] = useState({
    arkesel_api_key: "",
    arkesel_sender_id: "",
    vapi_api_key: "",
    vapi_assistant_id: "",
    iredmail_smtp_host: "mail.ailabsafrica.com",
    iredmail_smtp_port: "587",
    iredmail_username: "",
    iredmail_password: "",
    whatsapp_business_token: "",
  });

  // QuickBooks integration
  const { data: qboStatus, isLoading: loadingQBO } = useQBOStatus();
  const qboDisconnect = useQBODisconnect();
  const [searchParams, setSearchParams] = useSearchParams();

  // Handle QBO OAuth redirect query params
  useEffect(() => {
    const qboParam = searchParams.get("qbo");
    if (qboParam === "connected") {
      toast.success("QuickBooks connected successfully!");
      searchParams.delete("qbo");
      setSearchParams(searchParams, { replace: true });
    } else if (qboParam === "error") {
      toast.error("Failed to connect QuickBooks. Please try again.");
      searchParams.delete("qbo");
      setSearchParams(searchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  // Notification Settings
  const [notifications, setNotifications] = useState({
    email_new_booking: true,
    email_new_inquiry: true,
    email_campaign_complete: true,
    sms_new_booking: false,
    sms_campaign_complete: false,
  });

  // Load user profile on mount
  useEffect(() => {
    const loadProfile = async () => {
      if (!user) {
        setIsLoadingProfile(false);
        return;
      }

      try {
        const data = await getUserProfile();
        setProfile(data);
        setProfileForm({
          first_name: data.first_name || "",
          last_name: data.last_name || "",
          phone: data.phone || "",
        });
      } catch (error) {
        console.error("Failed to load profile:", error);
        toast.error("Failed to load profile");
      } finally {
        setIsLoadingProfile(false);
      }
    };

    loadProfile();
  }, [user]);

  // Load team members on mount
  useEffect(() => {
    fetchTeamMembers();
  }, [fetchTeamMembers]);

  const handleSaveProfile = async () => {
    setIsSaving(true);
    try {
      const updateData: UserProfileUpdate = {
        first_name: profileForm.first_name || null,
        last_name: profileForm.last_name || null,
        phone: profileForm.phone || null,
      };

      const updatedProfile = await updateUserProfile(updateData);
      setProfile(updatedProfile);
      toast.success("Profile updated successfully");
    } catch (error) {
      console.error("Failed to update profile:", error);
      toast.error("Failed to update profile");
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveOrganization = async () => {
    if (!currentOrganization?.id) {
      toast.error("No organization selected");
      return;
    }
    setIsSaving(true);
    try {
      await updateOrganization(currentOrganization.id, {
        name: orgSettings.name || undefined,
        description: orgSettings.description || undefined,
        email: orgSettings.email || undefined,
        phone: orgSettings.phone || undefined,
      });
      toast.success("Organization settings saved");
    } catch (error) {
      console.error("Failed to save organization:", error);
      toast.error("Failed to save organization settings");
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveApiKeys = async () => {
    setIsSaving(true);
    try {
      // TODO: Implement API call to save API keys
      await new Promise((resolve) => setTimeout(resolve, 1000));
      console.log("API keys saved");
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveNotifications = async () => {
    setIsSaving(true);
    try {
      // TODO: Implement API call to save notification settings
      await new Promise((resolve) => setTimeout(resolve, 1000));
      console.log("Notification settings saved:", notifications);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Header
        title="Settings"
        subtitle="Manage your organization and user settings"
      />

      <div className="p-6">
        <Tabs defaultValue="organization" className="space-y-6">
          <TabsList>
            <TabsTrigger value="organization" className="gap-2">
              <Building className="h-4 w-4" />
              Organization
            </TabsTrigger>
            <TabsTrigger value="profile" className="gap-2">
              <UserIcon className="h-4 w-4" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="api-keys" className="gap-2">
              <Key className="h-4 w-4" />
              API Keys
            </TabsTrigger>
            <TabsTrigger value="notifications" className="gap-2">
              <Bell className="h-4 w-4" />
              Notifications
            </TabsTrigger>
            <TabsTrigger value="team" className="gap-2">
              <Users className="h-4 w-4" />
              Team
            </TabsTrigger>
            <TabsTrigger value="integrations" className="gap-2">
              <Plug className="h-4 w-4" />
              Integrations
            </TabsTrigger>
          </TabsList>

          {/* Organization Settings */}
          <TabsContent value="organization">
            <Card>
              <CardHeader>
                <CardTitle>Organization Information</CardTitle>
                <CardDescription>
                  Update your organization's profile and contact information
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="org-name">Organization Name</Label>
                    <Input
                      id="org-name"
                      value={orgSettings.name}
                      onChange={(e) =>
                        setOrgSettings({ ...orgSettings, name: e.target.value })
                      }
                    />
                  </div>

                  <div>
                    <Label htmlFor="org-email">Email</Label>
                    <Input
                      id="org-email"
                      type="email"
                      value={orgSettings.email}
                      onChange={(e) =>
                        setOrgSettings({ ...orgSettings, email: e.target.value })
                      }
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="org-phone">Phone</Label>
                    <Input
                      id="org-phone"
                      type="tel"
                      value={orgSettings.phone}
                      onChange={(e) =>
                        setOrgSettings({ ...orgSettings, phone: e.target.value })
                      }
                    />
                  </div>

                  <div>
                    <Label htmlFor="org-website">Website</Label>
                    <Input
                      id="org-website"
                      type="url"
                      value={orgSettings.website}
                      onChange={(e) =>
                        setOrgSettings({ ...orgSettings, website: e.target.value })
                      }
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="org-address">Address</Label>
                  <Input
                    id="org-address"
                    value={orgSettings.address}
                    onChange={(e) =>
                      setOrgSettings({ ...orgSettings, address: e.target.value })
                    }
                  />
                </div>

                <div>
                  <Label htmlFor="org-description">Description</Label>
                  <Textarea
                    id="org-description"
                    rows={4}
                    value={orgSettings.description}
                    onChange={(e) =>
                      setOrgSettings({
                        ...orgSettings,
                        description: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="flex justify-end pt-4">
                  <Button onClick={handleSaveOrganization} disabled={isSaving}>
                    <Save className="mr-2 h-4 w-4" />
                    Save Changes
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Profile Settings */}
          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Personal Information</CardTitle>
                <CardDescription>
                  Update your personal profile and preferences
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {isLoadingProfile ? (
                  <div className="text-center py-8 text-muted-foreground">
                    Loading profile...
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="first-name">First Name</Label>
                        <Input
                          id="first-name"
                          placeholder="John"
                          value={profileForm.first_name}
                          onChange={(e) =>
                            setProfileForm({ ...profileForm, first_name: e.target.value })
                          }
                        />
                      </div>

                      <div>
                        <Label htmlFor="last-name">Last Name</Label>
                        <Input
                          id="last-name"
                          placeholder="Doe"
                          value={profileForm.last_name}
                          onChange={(e) =>
                            setProfileForm({ ...profileForm, last_name: e.target.value })
                          }
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="user-email">Email</Label>
                      <Input
                        id="user-email"
                        type="email"
                        value={profile?.email || user?.email || ""}
                        disabled
                        className="bg-muted"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        Email cannot be changed. Managed by your account.
                      </p>
                    </div>

                    <div>
                      <Label htmlFor="user-phone">Phone</Label>
                      <Input
                        id="user-phone"
                        type="tel"
                        placeholder="+233241234567"
                        value={profileForm.phone}
                        onChange={(e) =>
                          setProfileForm({ ...profileForm, phone: e.target.value })
                        }
                      />
                    </div>

                    <div className="flex justify-end pt-4">
                      <Button onClick={handleSaveProfile} disabled={isSaving}>
                        <Save className="mr-2 h-4 w-4" />
                        {isSaving ? "Saving..." : "Save Changes"}
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* API Keys */}
          <TabsContent value="api-keys">
            <Card>
              <CardHeader>
                <CardTitle>API Keys & Integrations</CardTitle>
                <CardDescription>
                  Configure API keys for campaign delivery services
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Arkesel SMS */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold">Arkesel (SMS)</h3>
                  <div className="space-y-3">
                    <div>
                      <Label htmlFor="arkesel-key">API Key</Label>
                      <div className="relative">
                        <Input
                          id="arkesel-key"
                          type={showApiKeys ? "text" : "password"}
                          value={apiKeys.arkesel_api_key}
                          onChange={(e) =>
                            setApiKeys({
                              ...apiKeys,
                              arkesel_api_key: e.target.value,
                            })
                          }
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          className="absolute right-2 top-1/2 -translate-y-1/2"
                          onClick={() => setShowApiKeys(!showApiKeys)}
                        >
                          {showApiKeys ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="arkesel-sender">Sender ID</Label>
                      <Input
                        id="arkesel-sender"
                        value={apiKeys.arkesel_sender_id}
                        onChange={(e) =>
                          setApiKeys({
                            ...apiKeys,
                            arkesel_sender_id: e.target.value,
                          })
                        }
                        placeholder="Your Brand"
                      />
                    </div>
                  </div>
                </div>

                {/* Vapi Voice */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold">Vapi (Voice Calls)</h3>
                  <div className="space-y-3">
                    <div>
                      <Label htmlFor="vapi-key">API Key</Label>
                      <Input
                        id="vapi-key"
                        type={showApiKeys ? "text" : "password"}
                        value={apiKeys.vapi_api_key}
                        onChange={(e) =>
                          setApiKeys({ ...apiKeys, vapi_api_key: e.target.value })
                        }
                      />
                    </div>

                    <div>
                      <Label htmlFor="vapi-assistant">Assistant ID</Label>
                      <Input
                        id="vapi-assistant"
                        value={apiKeys.vapi_assistant_id}
                        onChange={(e) =>
                          setApiKeys({
                            ...apiKeys,
                            vapi_assistant_id: e.target.value,
                          })
                        }
                      />
                    </div>
                  </div>
                </div>

                {/* iRedMail SMTP */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold">iRedMail (Email Server)</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label htmlFor="smtp-host">SMTP Host</Label>
                      <Input
                        id="smtp-host"
                        value={apiKeys.iredmail_smtp_host}
                        onChange={(e) =>
                          setApiKeys({
                            ...apiKeys,
                            iredmail_smtp_host: e.target.value,
                          })
                        }
                        placeholder="mail.ailabsafrica.com"
                      />
                    </div>

                    <div>
                      <Label htmlFor="smtp-port">SMTP Port</Label>
                      <Input
                        id="smtp-port"
                        value={apiKeys.iredmail_smtp_port}
                        onChange={(e) =>
                          setApiKeys({
                            ...apiKeys,
                            iredmail_smtp_port: e.target.value,
                          })
                        }
                        placeholder="587"
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="smtp-username">Email Username</Label>
                    <Input
                      id="smtp-username"
                      value={apiKeys.iredmail_username}
                      onChange={(e) =>
                        setApiKeys({
                          ...apiKeys,
                          iredmail_username: e.target.value,
                        })
                      }
                      placeholder="noreply@agency.com"
                    />
                  </div>

                  <div>
                    <Label htmlFor="smtp-password">Email Password</Label>
                    <Input
                      id="smtp-password"
                      type={showApiKeys ? "text" : "password"}
                      value={apiKeys.iredmail_password}
                      onChange={(e) =>
                        setApiKeys({
                          ...apiKeys,
                          iredmail_password: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>

                {/* WhatsApp */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold">WhatsApp Business</h3>
                  <div>
                    <Label htmlFor="whatsapp-token">Access Token</Label>
                    <Input
                      id="whatsapp-token"
                      type={showApiKeys ? "text" : "password"}
                      value={apiKeys.whatsapp_business_token}
                      onChange={(e) =>
                        setApiKeys({
                          ...apiKeys,
                          whatsapp_business_token: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <Button onClick={handleSaveApiKeys} disabled={isSaving}>
                    <Save className="mr-2 h-4 w-4" />
                    Save API Keys
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Notifications */}
          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>
                  Choose how you want to be notified about important events
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Email - New Booking</Label>
                    <p className="text-sm text-muted-foreground">
                      Get notified when a new property booking is made
                    </p>
                  </div>
                  <Switch
                    checked={notifications.email_new_booking}
                    onCheckedChange={(checked) =>
                      setNotifications({
                        ...notifications,
                        email_new_booking: checked,
                      })
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Email - New Inquiry</Label>
                    <p className="text-sm text-muted-foreground">
                      Get notified when someone inquires about a property
                    </p>
                  </div>
                  <Switch
                    checked={notifications.email_new_inquiry}
                    onCheckedChange={(checked) =>
                      setNotifications({
                        ...notifications,
                        email_new_inquiry: checked,
                      })
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Email - Campaign Complete</Label>
                    <p className="text-sm text-muted-foreground">
                      Get notified when a marketing campaign completes
                    </p>
                  </div>
                  <Switch
                    checked={notifications.email_campaign_complete}
                    onCheckedChange={(checked) =>
                      setNotifications({
                        ...notifications,
                        email_campaign_complete: checked,
                      })
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>SMS - New Booking</Label>
                    <p className="text-sm text-muted-foreground">
                      Receive SMS alerts for new bookings
                    </p>
                  </div>
                  <Switch
                    checked={notifications.sms_new_booking}
                    onCheckedChange={(checked) =>
                      setNotifications({
                        ...notifications,
                        sms_new_booking: checked,
                      })
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>SMS - Campaign Complete</Label>
                    <p className="text-sm text-muted-foreground">
                      Receive SMS alerts when campaigns complete
                    </p>
                  </div>
                  <Switch
                    checked={notifications.sms_campaign_complete}
                    onCheckedChange={(checked) =>
                      setNotifications({
                        ...notifications,
                        sms_campaign_complete: checked,
                      })
                    }
                  />
                </div>

                <div className="flex justify-end pt-4">
                  <Button onClick={handleSaveNotifications} disabled={isSaving}>
                    <Save className="mr-2 h-4 w-4" />
                    Save Preferences
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Integrations */}
          <TabsContent value="integrations">
            <Card>
              <CardHeader>
                <CardTitle>Integrations</CardTitle>
                <CardDescription>
                  Connect third-party services to sync your data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* QuickBooks Online */}
                <div className="flex items-start justify-between p-4 rounded-lg border border-border">
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
                      <DollarSign className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">QuickBooks Online</h3>
                        {loadingQBO ? (
                          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                        ) : qboStatus?.is_connected ? (
                          <Badge variant="success" className="gap-1">
                            <CheckCircle className="h-3 w-3" />
                            Connected
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="gap-1 text-muted-foreground">
                            <XCircle className="h-3 w-3" />
                            Disconnected
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        Sync invoices to QuickBooks Online for accounting
                      </p>
                      {qboStatus?.is_connected && qboStatus.company_name && (
                        <p className="text-sm text-foreground mt-1">
                          Connected to: <span className="font-medium">{qboStatus.company_name}</span>
                        </p>
                      )}
                    </div>
                  </div>
                  <div>
                    {qboStatus?.is_connected ? (
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-destructive border-destructive hover:bg-destructive/10"
                        disabled={qboDisconnect.isPending}
                        onClick={() => {
                          if (!window.confirm("Disconnect QuickBooks? You can reconnect later.")) {
                            return;
                          }
                          qboDisconnect.mutate(undefined, {
                            onSuccess: () => {
                              toast.success("QuickBooks disconnected");
                            },
                            onError: (error) => {
                              toast.error(`Failed to disconnect: ${error.message}`);
                            },
                          });
                        }}
                      >
                        {qboDisconnect.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        ) : null}
                        Disconnect
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        className="border-emerald-600 text-emerald-600 hover:bg-emerald-50"
                        onClick={async () => {
                          try {
                            const { auth_url } = await getQBOAuthUrl();
                            window.location.href = auth_url;
                          } catch (error: any) {
                            toast.error(error.message || "Failed to connect QuickBooks");
                          }
                        }}
                      >
                        Connect QuickBooks
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Team Management */}
          <TabsContent value="team">
            <Card>
              <CardHeader>
                <CardTitle>Team Members</CardTitle>
                <CardDescription>
                  Manage team members and their permissions
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoadingTeam ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : teamMembers.length === 0 ? (
                  <div className="text-center py-12">
                    <Users className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">
                      No team members found
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Invite team members from the Admin panel
                    </p>
                  </div>
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
                            </div>
                            <p className="text-sm text-muted-foreground">{member.email}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
