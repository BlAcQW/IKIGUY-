/**
 * Voice Settings Admin Page
 *
 * Admin interface for configuring default voice settings and preferences.
 * Allows administrators to:
 * - Set default voices for different use cases
 * - Configure voice fallback preferences
 * - Manage organization-wide voice settings
 * - Set voice usage policies
 */

import React, { useState, useEffect } from 'react';
import { VoicePicker } from '@/components/voice-library';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Settings,
  Save,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Info,
  Volume2,
  Mic,
  MessageSquare,
} from 'lucide-react';
import { toast } from 'sonner';

interface VoiceSettings {
  // Default voices for different use cases
  defaultVoices: {
    narration?: string;
    conversation?: string;
    professional?: string;
    casual?: string;
    education?: string;
    customerService?: string;
  };

  // Voice preferences
  preferences: {
    preferFeatured: boolean;
    preferVerified: boolean;
    allowPrivateVoices: boolean;
    enableVoiceRatings: boolean;
    enableVoiceFavorites: boolean;
  };

  // Usage policies
  policies: {
    maxVoicesPerUser?: number;
    allowVoiceCloning: boolean;
    requireVerificationForPublic: boolean;
    autoDeleteUnusedVoices: boolean;
    unusedVoiceDays?: number;
  };

  // Fallback configuration
  fallback: {
    enabled: boolean;
    fallbackVoiceId?: string;
    fallbackLanguage?: string;
  };
}

export default function VoiceSettingsAdmin() {
  const [settings, setSettings] = useState<VoiceSettings>({
    defaultVoices: {},
    preferences: {
      preferFeatured: true,
      preferVerified: true,
      allowPrivateVoices: true,
      enableVoiceRatings: true,
      enableVoiceFavorites: true,
    },
    policies: {
      maxVoicesPerUser: 10,
      allowVoiceCloning: true,
      requireVerificationForPublic: true,
      autoDeleteUnusedVoices: false,
      unusedVoiceDays: 90,
    },
    fallback: {
      enabled: true,
      fallbackLanguage: 'en',
    },
  });

  const [loading, setLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      // TODO: Load settings from API
      // const response = await fetch('/api/admin/voice-settings');
      // const data = await response.json();
      // setSettings(data);

      toast.success('Settings loaded');
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setLoading(true);
      // TODO: Save settings to API
      // await fetch('/api/admin/voice-settings', {
      //   method: 'PUT',
      //   body: JSON.stringify(settings),
      // });

      toast.success('Settings saved successfully');
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = (path: string[], value: any) => {
    setSettings(prev => {
      const newSettings = { ...prev };
      let current: any = newSettings;

      for (let i = 0; i < path.length - 1; i++) {
        current[path[i]] = { ...current[path[i]] };
        current = current[path[i]];
      }

      current[path[path.length - 1]] = value;
      return newSettings;
    });
    setHasChanges(true);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Settings className="h-8 w-8" />
            Voice Settings Administration
          </h1>
          <p className="text-muted-foreground mt-1">
            Configure default voice settings and preferences
          </p>
        </div>

        <div className="flex items-center gap-2">
          {hasChanges && (
            <Badge variant="secondary">
              <AlertCircle className="h-3 w-3 mr-1" />
              Unsaved Changes
            </Badge>
          )}

          <Button variant="outline" onClick={loadSettings} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Reload
          </Button>

          <Button onClick={handleSaveSettings} disabled={loading || !hasChanges}>
            <Save className="h-4 w-4 mr-2" />
            Save Settings
          </Button>
        </div>
      </div>

      <Tabs defaultValue="defaults" className="space-y-4">
        <TabsList>
          <TabsTrigger value="defaults">Default Voices</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
          <TabsTrigger value="policies">Policies</TabsTrigger>
          <TabsTrigger value="fallback">Fallback</TabsTrigger>
        </TabsList>

        {/* Default Voices Tab */}
        <TabsContent value="defaults" className="space-y-4">
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Set default voices for different use cases. These will be recommended to users when selecting voices.
            </AlertDescription>
          </Alert>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Narration Voice */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Narration Voice</CardTitle>
                <CardDescription>
                  Default voice for audiobooks, storytelling, and long-form content
                </CardDescription>
              </CardHeader>
              <CardContent>
                <VoicePicker
                  value={settings.defaultVoices.narration}
                  onChange={(voiceId) => updateSetting(['defaultVoices', 'narration'], voiceId)}
                  filters={{ categories: ['Narration', 'Audiobook'] }}
                  showPreview={true}
                />
              </CardContent>
            </Card>

            {/* Conversation Voice */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Conversation Voice</CardTitle>
                <CardDescription>
                  Default voice for conversational AI, chatbots, and interactive content
                </CardDescription>
              </CardHeader>
              <CardContent>
                <VoicePicker
                  value={settings.defaultVoices.conversation}
                  onChange={(voiceId) => updateSetting(['defaultVoices', 'conversation'], voiceId)}
                  filters={{ categories: ['Conversational'] }}
                  showPreview={true}
                />
              </CardContent>
            </Card>

            {/* Professional Voice */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Professional Voice</CardTitle>
                <CardDescription>
                  Default voice for business, announcements, and formal content
                </CardDescription>
              </CardHeader>
              <CardContent>
                <VoicePicker
                  value={settings.defaultVoices.professional}
                  onChange={(voiceId) => updateSetting(['defaultVoices', 'professional'], voiceId)}
                  filters={{ categories: ['Professional'] }}
                  showPreview={true}
                />
              </CardContent>
            </Card>

            {/* Casual Voice */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Casual Voice</CardTitle>
                <CardDescription>
                  Default voice for informal, friendly content
                </CardDescription>
              </CardHeader>
              <CardContent>
                <VoicePicker
                  value={settings.defaultVoices.casual}
                  onChange={(voiceId) => updateSetting(['defaultVoices', 'casual'], voiceId)}
                  filters={{ categories: ['Casual'] }}
                  showPreview={true}
                />
              </CardContent>
            </Card>

            {/* Education Voice */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Education Voice</CardTitle>
                <CardDescription>
                  Default voice for educational content, tutorials, and lessons
                </CardDescription>
              </CardHeader>
              <CardContent>
                <VoicePicker
                  value={settings.defaultVoices.education}
                  onChange={(voiceId) => updateSetting(['defaultVoices', 'education'], voiceId)}
                  filters={{ categories: ['Education'] }}
                  showPreview={true}
                />
              </CardContent>
            </Card>

            {/* Customer Service Voice */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Customer Service Voice</CardTitle>
                <CardDescription>
                  Default voice for customer support, IVR, and help systems
                </CardDescription>
              </CardHeader>
              <CardContent>
                <VoicePicker
                  value={settings.defaultVoices.customerService}
                  onChange={(voiceId) => updateSetting(['defaultVoices', 'customerService'], voiceId)}
                  filters={{ categories: ['Customer Service', 'IVR'] }}
                  showPreview={true}
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences" className="space-y-4">
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Configure how voices are displayed and recommended to users.
            </AlertDescription>
          </Alert>

          <Card>
            <CardHeader>
              <CardTitle>Voice Display Preferences</CardTitle>
              <CardDescription>
                Control which voices are prioritized in search and selection
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between border-b pb-4">
                <div className="space-y-0.5">
                  <Label>Prefer Featured Voices</Label>
                  <p className="text-sm text-muted-foreground">
                    Show featured voices at the top of search results
                  </p>
                </div>
                <Switch
                  checked={settings.preferences.preferFeatured}
                  onCheckedChange={(checked) =>
                    updateSetting(['preferences', 'preferFeatured'], checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between border-b pb-4">
                <div className="space-y-0.5">
                  <Label>Prefer Verified Voices</Label>
                  <p className="text-sm text-muted-foreground">
                    Prioritize admin-verified voices in recommendations
                  </p>
                </div>
                <Switch
                  checked={settings.preferences.preferVerified}
                  onCheckedChange={(checked) =>
                    updateSetting(['preferences', 'preferVerified'], checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between border-b pb-4">
                <div className="space-y-0.5">
                  <Label>Allow Private Voices</Label>
                  <p className="text-sm text-muted-foreground">
                    Allow users to create private voices for personal use
                  </p>
                </div>
                <Switch
                  checked={settings.preferences.allowPrivateVoices}
                  onCheckedChange={(checked) =>
                    updateSetting(['preferences', 'allowPrivateVoices'], checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between border-b pb-4">
                <div className="space-y-0.5">
                  <Label>Enable Voice Ratings</Label>
                  <p className="text-sm text-muted-foreground">
                    Allow users to rate and review voices
                  </p>
                </div>
                <Switch
                  checked={settings.preferences.enableVoiceRatings}
                  onCheckedChange={(checked) =>
                    updateSetting(['preferences', 'enableVoiceRatings'], checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Voice Favorites</Label>
                  <p className="text-sm text-muted-foreground">
                    Allow users to save favorite voices for quick access
                  </p>
                </div>
                <Switch
                  checked={settings.preferences.enableVoiceFavorites}
                  onCheckedChange={(checked) =>
                    updateSetting(['preferences', 'enableVoiceFavorites'], checked)
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Policies Tab */}
        <TabsContent value="policies" className="space-y-4">
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Set usage policies and limits for voice management.
            </AlertDescription>
          </Alert>

          <Card>
            <CardHeader>
              <CardTitle>Voice Usage Policies</CardTitle>
              <CardDescription>
                Configure limits and rules for voice creation and usage
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="maxVoices">Maximum Voices Per User</Label>
                <Input
                  id="maxVoices"
                  type="number"
                  min="1"
                  max="100"
                  value={settings.policies.maxVoicesPerUser || ''}
                  onChange={(e) =>
                    updateSetting(
                      ['policies', 'maxVoicesPerUser'],
                      parseInt(e.target.value) || undefined
                    )
                  }
                />
                <p className="text-sm text-muted-foreground">
                  Set to 0 for unlimited voices
                </p>
              </div>

              <div className="flex items-center justify-between border-b pb-4">
                <div className="space-y-0.5">
                  <Label>Allow Voice Cloning</Label>
                  <p className="text-sm text-muted-foreground">
                    Permit users to create cloned voices from audio samples
                  </p>
                </div>
                <Switch
                  checked={settings.policies.allowVoiceCloning}
                  onCheckedChange={(checked) =>
                    updateSetting(['policies', 'allowVoiceCloning'], checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between border-b pb-4">
                <div className="space-y-0.5">
                  <Label>Require Verification for Public Voices</Label>
                  <p className="text-sm text-muted-foreground">
                    Public voices must be verified by admin before becoming visible
                  </p>
                </div>
                <Switch
                  checked={settings.policies.requireVerificationForPublic}
                  onCheckedChange={(checked) =>
                    updateSetting(['policies', 'requireVerificationForPublic'], checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between border-b pb-4">
                <div className="space-y-0.5">
                  <Label>Auto-Delete Unused Voices</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically delete voices that haven't been used in specified days
                  </p>
                </div>
                <Switch
                  checked={settings.policies.autoDeleteUnusedVoices}
                  onCheckedChange={(checked) =>
                    updateSetting(['policies', 'autoDeleteUnusedVoices'], checked)
                  }
                />
              </div>

              {settings.policies.autoDeleteUnusedVoices && (
                <div className="space-y-2">
                  <Label htmlFor="unusedDays">Unused Voice Retention (Days)</Label>
                  <Input
                    id="unusedDays"
                    type="number"
                    min="7"
                    max="365"
                    value={settings.policies.unusedVoiceDays || ''}
                    onChange={(e) =>
                      updateSetting(
                        ['policies', 'unusedVoiceDays'],
                        parseInt(e.target.value) || undefined
                      )
                    }
                  />
                  <p className="text-sm text-muted-foreground">
                    Voices unused for this many days will be automatically deleted
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Fallback Tab */}
        <TabsContent value="fallback" className="space-y-4">
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Configure fallback voices when the selected voice is unavailable.
            </AlertDescription>
          </Alert>

          <Card>
            <CardHeader>
              <CardTitle>Fallback Configuration</CardTitle>
              <CardDescription>
                Set fallback options when voices are not available
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between border-b pb-4">
                <div className="space-y-0.5">
                  <Label>Enable Fallback</Label>
                  <p className="text-sm text-muted-foreground">
                    Use fallback voice when selected voice is unavailable
                  </p>
                </div>
                <Switch
                  checked={settings.fallback.enabled}
                  onCheckedChange={(checked) => updateSetting(['fallback', 'enabled'], checked)}
                />
              </div>

              {settings.fallback.enabled && (
                <>
                  <div className="space-y-2">
                    <Label>Fallback Voice</Label>
                    <VoicePicker
                      value={settings.fallback.fallbackVoiceId}
                      onChange={(voiceId) => updateSetting(['fallback', 'fallbackVoiceId'], voiceId)}
                      filters={{ featured: true, verified: true }}
                      showPreview={true}
                    />
                    <p className="text-sm text-muted-foreground">
                      This voice will be used when the selected voice is unavailable
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="fallbackLang">Fallback Language</Label>
                    <Select
                      value={settings.fallback.fallbackLanguage}
                      onValueChange={(value) =>
                        updateSetting(['fallback', 'fallbackLanguage'], value)
                      }
                    >
                      <SelectTrigger id="fallbackLang">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="tw">Twi</SelectItem>
                        <SelectItem value="ak">Akan</SelectItem>
                        <SelectItem value="es">Spanish</SelectItem>
                        <SelectItem value="fr">French</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-sm text-muted-foreground">
                      Default language for fallback voices
                    </p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Success Message */}
      {!loading && !hasChanges && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>All settings are saved and up to date.</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
