/**
 * EstateFlow Settings Page
 *
 * Organization and user settings management.
 */

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { getUserProfile, updateUserProfile, UserProfile, UserProfileUpdate } from "@/lib/api/user-api";
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
  User,
  Key,
  Bell,
  Users,
  Save,
  Eye,
  EyeOff,
} from "lucide-react";

export default function Settings() {
  const { user } = useAuth();
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

  // Organization Settings
  const [orgSettings, setOrgSettings] = useState({
    name: "My Real Estate Agency",
    email: "admin@agency.com",
    phone: "+233241234567",
    address: "123 Main Street, Accra, Ghana",
    description: "Premium real estate services",
    website: "https://agency.com",
  });

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
    setIsSaving(true);
    try {
      // TODO: Implement API call to save organization settings
      await new Promise((resolve) => setTimeout(resolve, 1000));
      console.log("Organization settings saved:", orgSettings);
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
              <User className="h-4 w-4" />
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
                <div className="text-center py-12">
                  <Users className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    Team management coming soon
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Invite team members and manage their roles and permissions
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
