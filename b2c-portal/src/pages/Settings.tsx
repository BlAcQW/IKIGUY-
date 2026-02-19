import React, { useState, useEffect } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import {
  User,
  Building,
  Bell,
  Shield,
  Trash2,
  Save,
  Key,
  Puzzle,
  Settings as SettingsIcon
} from 'lucide-react';
import { HelpIcon } from '@/components/ui/help-icon';
import { getHelpContent } from '@/lib/help-content';
import { IntegrationsManagement } from '@/components/integrations/IntegrationsManagement';
import AppSettings from '@/components/settings/AppSettings';

const Settings = () => {
  const [profile, setProfile] = useState({
    display_name: '',
    workspace_name: '',
    company_name: '',
    industry: '',
    phone: '',
    timezone: 'UTC'
  });
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const { toast } = useToast();

  // Help content
  const settingsHelp = getHelpContent('settings_overview');
  const brandingHelp = getHelpContent('branding_settings');
  const telephonyHelp = getHelpContent('telephony_settings');
  const paymentHelp = getHelpContent('payment_settings');

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      // Mock user and profile data - replace with Supabase when types are regenerated
      const mockUser = {
        id: '1',
        email: 'user@example.com'
      };
      
      const mockProfile = {
        display_name: 'John Doe',
        workspace_name: 'My Workspace',
        company_name: 'Acme Corp',
        industry: 'Technology',
        phone: '+1 (555) 123-4567',
        timezone: 'America/New_York'
      };
      
      setUser(mockUser);
      setProfile(mockProfile);
    } catch (error) {
      toast({
        title: "Error loading profile",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const saveProfile = async () => {
    if (!user) return;
    
    setSaving(true);
    try {
      // Mock save - replace with Supabase when types are regenerated
      toast({
        title: "Profile updated",
        description: "Your profile has been saved successfully."
      });
    } catch (error) {
      toast({
        title: "Error saving profile",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const industries = [
    'Insurance',
    'Banking & Finance',
    'Real Estate',
    'Healthcare',
    'Education',
    'Retail',
    'Technology',
    'Manufacturing',
    'Professional Services',
    'Government',
    'Non-profit',
    'Other'
  ];

  const timezones = [
    'UTC',
    'America/New_York',
    'America/Chicago',
    'America/Denver', 
    'America/Los_Angeles',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Africa/Lagos',
    'Africa/Cairo'
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="flex">
          <DashboardSidebar />
          <main className="flex-1 p-6">
            <div className="text-center py-12">
              <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600">Loading settings...</p>
            </div>
          </main>
        </div>
      </div>
    );
  }

  const settingsTabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'workspace', label: 'Workspace', icon: Building },
    { id: 'integrations', label: 'Integrations', icon: Puzzle },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'app-settings', label: 'App Settings', icon: SettingsIcon }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Personal Information
                </CardTitle>
                <CardDescription>
                  Update your personal details and contact information
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="display_name">Display Name</Label>
                    <Input
                      id="display_name"
                      value={profile.display_name}
                      onChange={(e) => setProfile({...profile, display_name: e.target.value})}
                      placeholder="Enter your display name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone Number</Label>
                    <Input
                      id="phone"
                      value={profile.phone}
                      onChange={(e) => setProfile({...profile, phone: e.target.value})}
                      placeholder="+1 (555) 123-4567"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select value={profile.timezone} onValueChange={(value) => setProfile({...profile, timezone: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select timezone" />
                    </SelectTrigger>
                    <SelectContent>
                      {timezones.map((tz) => (
                        <SelectItem key={tz} value={tz}>{tz}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </div>
        );
      case 'workspace':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building className="h-5 w-5" />
                  Workspace Information
                </CardTitle>
                <CardDescription>
                  Manage your workspace settings and company details
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="workspace_name">Workspace Name</Label>
                    <Input
                      id="workspace_name"
                      value={profile.workspace_name}
                      onChange={(e) => setProfile({...profile, workspace_name: e.target.value})}
                      placeholder="Enter workspace name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="company_name">Company Name</Label>
                    <Input
                      id="company_name"
                      value={profile.company_name}
                      onChange={(e) => setProfile({...profile, company_name: e.target.value})}
                      placeholder="Enter company name"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="industry">Industry</Label>
                  <Select value={profile.industry} onValueChange={(value) => setProfile({...profile, industry: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select industry" />
                    </SelectTrigger>
                    <SelectContent>
                      {industries.map((industry) => (
                        <SelectItem key={industry} value={industry}>{industry}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </div>
        );
      case 'integrations':
        return <IntegrationsManagement />;
      case 'app-settings':
        return <AppSettings />;
      case 'notifications':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5" />
                  Notification Preferences
                </CardTitle>
                <CardDescription>
                  Configure how you receive notifications
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Email Notifications</Label>
                    <p className="text-sm text-gray-600">
                      Receive notifications via email
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Push Notifications</Label>
                    <p className="text-sm text-gray-600">
                      Receive push notifications in browser
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Weekly Reports</Label>
                    <p className="text-sm text-gray-600">
                      Get weekly usage and performance reports
                    </p>
                  </div>
                  <Switch />
                </div>
              </CardContent>
            </Card>
          </div>
        );
      case 'security':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Security Settings
                </CardTitle>
                <CardDescription>
                  Manage your account security and privacy
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Two-Factor Authentication</Label>
                  <p className="text-sm text-gray-600">
                    Add an extra layer of security to your account
                  </p>
                  <Button variant="outline" className="mt-2">
                    Enable 2FA
                  </Button>
                </div>
                <Separator />
                <div className="space-y-2">
                  <Label>Session Management</Label>
                  <p className="text-sm text-gray-600">
                    View and manage your active sessions
                  </p>
                  <Button variant="outline" className="mt-2">
                    View Sessions
                  </Button>
                </div>
                <Separator />
                <div className="space-y-2">
                  <Label className="text-destructive">Danger Zone</Label>
                  <p className="text-sm text-gray-600">
                    Permanently delete your account and all data
                  </p>
                  <Button variant="destructive" className="mt-2">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Account
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        <DashboardSidebar />
        
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col lg:flex-row">
          {/* Left Panel - Settings Navigation */}
          <div className="w-full lg:w-80 bg-card border-r border-border p-4 lg:p-6 flex-shrink-0">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Settings</h2>
            </div>
            
            <div className="space-y-2">
              {settingsTabs.map((tab) => (
                <div 
                  key={tab.id} 
                  className={`p-3 rounded-md cursor-pointer transition-colors ${
                    activeTab === tab.id
                      ? 'bg-indigo-600 text-primary-foreground border-l-4 border-primary/60' 
                      : 'hover:bg-accent text-gray-600 hover:text-foreground'
                  }`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  <div className="flex items-center space-x-3">
                    <tab.icon className="w-4 h-4" />
                    <span className="font-medium">{tab.label}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Center Panel - Settings Content */}
          <div className="flex-1 bg-gray-900 p-4 lg:p-6 min-w-0">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-2">
                <div>
                  <h1 className="text-3xl text-heading text-white">
                    {settingsTabs.find(tab => tab.id === activeTab)?.label}
                  </h1>
                  <p className="text-gray-400 mt-1">
                    Manage your {activeTab} settings
                  </p>
                </div>
                {settingsHelp && (
                  <HelpIcon 
                    content={settingsHelp} 
                    size="sm" 
                    variant="tooltip" 
                    position="bottom"
                  />
                )}
              </div>
              <Button onClick={saveProfile} disabled={saving} className="gap-2">
                <Save className="h-4 w-4" />
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>

            {/* Tab Content */}
            <div className="space-y-6">
              {renderTabContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;