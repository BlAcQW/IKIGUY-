import { useState } from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  PenLine,
  Calendar,
  BarChart3,
  Settings,
  FileText,
  User,
  Bell,
  Lock,
  Palette,
  Globe,
  Save,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { NavLink, useLocation } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";

const menuItems = [
  { title: "Overview", url: "/dashboard", icon: BarChart3 },
  { title: "Author Dashboard", url: "/dashboard/author", icon: BookOpen },
  { title: "Compose", url: "/dashboard/compose", icon: PenLine },
  { title: "Calendar", url: "/dashboard/calendar", icon: Calendar },
  { title: "Devotionals", url: "/dashboard/devotionals", icon: FileText },
  { title: "Settings", url: "/dashboard/settings", icon: Settings },
];

function DashboardSidebar() {
  const location = useLocation();

  return (
    <Sidebar className="border-r border-border bg-card">
      <div className="p-4 border-b border-border">
        <a href="/" className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-secondary flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-secondary-foreground" />
          </div>
          <div>
            <h2 className="font-serif font-bold text-lg text-foreground">FreshManna</h2>
            <p className="text-xs text-muted-foreground">Author Portal</p>
          </div>
        </a>
      </div>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Menu</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={location.pathname === item.url}>
                    <NavLink to={item.url}>
                      <item.icon className="w-4 h-4" />
                      <span>{item.title}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}

export default function AuthorSettings() {
  const { toast } = useToast();
  const [saving, setSaving] = useState(false);

  // Profile settings
  const [displayName, setDisplayName] = useState("Pastor Michael Chen");
  const [bio, setBio] = useState("Sharing God's word with passion and purpose");
  const [ministryName, setMinistryName] = useState("Grace Community Church");
  const [website, setWebsite] = useState("https://gracechurch.com");

  // Notification settings
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [commentNotifications, setCommentNotifications] = useState(true);
  const [likeNotifications, setLikeNotifications] = useState(false);
  const [weeklyReport, setWeeklyReport] = useState(true);

  // Writing preferences
  const [autoSave, setAutoSave] = useState(true);
  const [defaultCategory, setDefaultCategory] = useState("Faith");
  const [aiSuggestions, setAiSuggestions] = useState(true);

  const handleSaveProfile = async () => {
    setSaving(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaving(false);
    toast({
      title: "Profile updated",
      description: "Your profile settings have been saved successfully.",
    });
  };

  const handleSaveNotifications = async () => {
    setSaving(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaving(false);
    toast({
      title: "Notifications updated",
      description: "Your notification preferences have been saved.",
    });
  };

  const handleSavePreferences = async () => {
    setSaving(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaving(false);
    toast({
      title: "Preferences updated",
      description: "Your writing preferences have been saved.",
    });
  };

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-background">
        <DashboardSidebar />

        <main className="flex-1 overflow-auto">
          {/* Header */}
          <header className="sticky top-0 z-10 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
            <div className="flex h-16 items-center gap-4 px-6">
              <SidebarTrigger className="md:hidden" />
              <div className="flex-1">
                <h1 className="text-xl font-serif font-bold text-foreground">Settings</h1>
                <p className="text-sm text-muted-foreground">Manage your account and preferences</p>
              </div>
            </div>
          </header>

          {/* Content */}
          <div className="p-6 max-w-4xl mx-auto">
            <Tabs defaultValue="profile" className="space-y-6">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="profile">
                  <User className="w-4 h-4 mr-2" />
                  Profile
                </TabsTrigger>
                <TabsTrigger value="notifications">
                  <Bell className="w-4 h-4 mr-2" />
                  Notifications
                </TabsTrigger>
                <TabsTrigger value="writing">
                  <PenLine className="w-4 h-4 mr-2" />
                  Writing
                </TabsTrigger>
                <TabsTrigger value="security">
                  <Lock className="w-4 h-4 mr-2" />
                  Security
                </TabsTrigger>
              </TabsList>

              {/* Profile Tab */}
              <TabsContent value="profile" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Profile Information</CardTitle>
                    <CardDescription>
                      Update your profile details and ministry information
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="displayName">Display Name</Label>
                      <Input
                        id="displayName"
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        placeholder="Your name"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="bio">Bio</Label>
                      <Textarea
                        id="bio"
                        value={bio}
                        onChange={(e) => setBio(e.target.value)}
                        placeholder="Tell readers about yourself"
                        rows={3}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="ministry">Ministry Name</Label>
                      <Input
                        id="ministry"
                        value={ministryName}
                        onChange={(e) => setMinistryName(e.target.value)}
                        placeholder="Your church or ministry"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="website">Website</Label>
                      <Input
                        id="website"
                        value={website}
                        onChange={(e) => setWebsite(e.target.value)}
                        placeholder="https://example.com"
                        type="url"
                      />
                    </div>

                    <div className="flex gap-2 pt-4">
                      <Button onClick={handleSaveProfile} disabled={saving}>
                        <Save className="w-4 h-4 mr-2" />
                        {saving ? "Saving..." : "Save Changes"}
                      </Button>
                      <Button variant="outline">
                        <X className="w-4 h-4 mr-2" />
                        Cancel
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Notifications Tab */}
              <TabsContent value="notifications" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Notification Preferences</CardTitle>
                    <CardDescription>
                      Choose how you want to receive updates about your devotionals
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Email Notifications</Label>
                        <p className="text-sm text-muted-foreground">
                          Receive email updates about activity
                        </p>
                      </div>
                      <Switch
                        checked={emailNotifications}
                        onCheckedChange={setEmailNotifications}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>New Comments</Label>
                        <p className="text-sm text-muted-foreground">
                          Get notified when someone comments on your devotionals
                        </p>
                      </div>
                      <Switch
                        checked={commentNotifications}
                        onCheckedChange={setCommentNotifications}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Likes & Reactions</Label>
                        <p className="text-sm text-muted-foreground">
                          Get notified when readers like your content
                        </p>
                      </div>
                      <Switch
                        checked={likeNotifications}
                        onCheckedChange={setLikeNotifications}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Weekly Performance Report</Label>
                        <p className="text-sm text-muted-foreground">
                          Receive a weekly summary of your devotional performance
                        </p>
                      </div>
                      <Switch
                        checked={weeklyReport}
                        onCheckedChange={setWeeklyReport}
                      />
                    </div>

                    <div className="flex gap-2 pt-4">
                      <Button onClick={handleSaveNotifications} disabled={saving}>
                        <Save className="w-4 h-4 mr-2" />
                        {saving ? "Saving..." : "Save Preferences"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Writing Preferences Tab */}
              <TabsContent value="writing" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Writing Preferences</CardTitle>
                    <CardDescription>
                      Customize your devotional writing experience
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Auto-save Drafts</Label>
                        <p className="text-sm text-muted-foreground">
                          Automatically save your work every 30 seconds
                        </p>
                      </div>
                      <Switch checked={autoSave} onCheckedChange={setAutoSave} />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="defaultCategory">Default Category</Label>
                      <Input
                        id="defaultCategory"
                        value={defaultCategory}
                        onChange={(e) => setDefaultCategory(e.target.value)}
                        placeholder="e.g., Faith, Prayer, Hope"
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>AI Writing Suggestions</Label>
                        <p className="text-sm text-muted-foreground">
                          Get AI-powered suggestions while writing
                        </p>
                      </div>
                      <Switch
                        checked={aiSuggestions}
                        onCheckedChange={setAiSuggestions}
                      />
                    </div>

                    <div className="flex gap-2 pt-4">
                      <Button onClick={handleSavePreferences} disabled={saving}>
                        <Save className="w-4 h-4 mr-2" />
                        {saving ? "Saving..." : "Save Preferences"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Security Tab */}
              <TabsContent value="security" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Password & Security</CardTitle>
                    <CardDescription>
                      Manage your account security settings
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="currentPassword">Current Password</Label>
                      <Input id="currentPassword" type="password" />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="newPassword">New Password</Label>
                      <Input id="newPassword" type="password" />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="confirmPassword">Confirm New Password</Label>
                      <Input id="confirmPassword" type="password" />
                    </div>

                    <div className="flex gap-2 pt-4">
                      <Button>
                        <Lock className="w-4 h-4 mr-2" />
                        Update Password
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-destructive">
                  <CardHeader>
                    <CardTitle className="text-destructive">Danger Zone</CardTitle>
                    <CardDescription>
                      Irreversible actions for your account
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button variant="destructive">Delete Account</Button>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}
