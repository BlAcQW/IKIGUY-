import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import {
  Settings,
  Palette,
  Save,
  Loader2,
  CheckCircle,
  AlertCircle,
  Wrench,
  Shield,
  Building2
} from 'lucide-react';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


interface AutomationTemplate {
  id: string;
  template_name: string;
  industry: string;
  category: string;
  description: string;
  version: string;
  created_at: string;
  updated_at: string;
}

interface AutomationSettings {
  enabled_industries: string[];
  enabled_templates: string[];
  custom_automations_enabled: boolean;
  max_automations_per_org: number;
  automation_approval_required: boolean;
  default_automation_language: string;
  automation_templates_enabled: boolean;
}

interface BrandingSettings {
  app_name: string;
  app_logo_url: string;
  app_favicon_url: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  show_powered_by: boolean;
  custom_footer_text: string;
  support_email: string;
  support_url: string;
  login_background_url: string;
  login_logo_url: string;
  welcome_message: string;
}

interface AppSettingsData {
  id: string;
  deployment_name: string;
  deployment_description: string;
  version: string;
  environment: string;
  multi_tenant_enabled: boolean;
  user_registration_enabled: boolean;
  organization_creation_enabled: boolean;
  api_access_enabled: boolean;
  automation_settings: AutomationSettings;
  branding_settings: BrandingSettings;
  max_organizations: number;
  max_users_per_org: number;
  data_retention_days: number;
  created_at: string;
  updated_at: string;
}


const AppSettings = () => {
  const [settings, setSettings] = useState<AppSettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeSection, setActiveSection] = useState<'automation' | 'branding'>('automation');
  const [isUniversalAdmin, setIsUniversalAdmin] = useState(false);
  const [availableIndustries, setAvailableIndustries] = useState<string[]>([]);
  const [templatesByIndustry, setTemplatesByIndustry] = useState<Record<string, AutomationTemplate[]>>({});
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const { toast } = useToast();
  const { user, getAccessToken } = useMongoAuth();

  useEffect(() => {
    loadAppSettings();
    checkUniversalAdminStatus();
    loadAutomationTemplates();
  }, []);

  const checkUniversalAdminStatus = async () => {
    try {
      if (!user) return;

      const accessToken = getAccessToken();
      if (!accessToken) return;

      const response = await fetch(`${API_BASE_URL}/api/admin/users/${user.id}/universal-admin-status`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setIsUniversalAdmin(data.is_universal_admin);
      }
    } catch (error) {
      console.error('Error checking universal admin status:', error);
    }
  };

  const loadAutomationTemplates = async () => {
    try {
      setLoadingTemplates(true);

      // Load available industries
      const industriesResponse = await fetch(buildApiUrl('/api/app-settings/industries/available'));
      if (industriesResponse.ok) {
        const industries = await industriesResponse.json();
        setAvailableIndustries(industries);
      }

      // Load templates by industry
      const templatesResponse = await fetch(buildApiUrl('/api/app-settings/templates/by-industry'));
      if (templatesResponse.ok) {
        const templatesByIndustry = await templatesResponse.json();
        setTemplatesByIndustry(templatesByIndustry);
      }
    } catch (error) {
      console.error('Error loading automation templates:', error);
      toast({
        title: "Error loading templates",
        description: "Failed to load automation templates from database.",
        variant: "destructive"
      });
    } finally {
      setLoadingTemplates(false);
    }
  };

  const loadAppSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch(buildApiUrl('/api/app-settings/'), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      } else {
        throw new Error('Failed to load app settings');
      }
    } catch (error) {
      console.error('Error loading app settings:', error);
      toast({
        title: "Error loading settings",
        description: "Failed to load app settings. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    if (!settings || !isUniversalAdmin) return;

    try {
      setSaving(true);
      if (!user) throw new Error('Not authenticated');

      const accessToken = getAccessToken();
      if (!accessToken) throw new Error('No access token available');

      const response = await fetch(buildApiUrl('/api/app-settings/'), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          deployment_name: settings.deployment_name,
          deployment_description: settings.deployment_description,
          environment: settings.environment,
          multi_tenant_enabled: settings.multi_tenant_enabled,
          user_registration_enabled: settings.user_registration_enabled,
          organization_creation_enabled: settings.organization_creation_enabled,
          api_access_enabled: settings.api_access_enabled,
          automation_settings: settings.automation_settings,
          branding_settings: settings.branding_settings,
          max_organizations: settings.max_organizations,
          max_users_per_org: settings.max_users_per_org,
          data_retention_days: settings.data_retention_days
        })
      });

      if (response.ok) {
        const updatedSettings = await response.json();
        setSettings(updatedSettings);
        toast({
          title: "Settings saved",
          description: "App settings have been updated successfully."
        });
      } else {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      toast({
        title: "Error saving settings",
        description: "Failed to save app settings. Please try again.",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const toggleIndustry = (industryValue: string) => {
    if (!settings) return;

    const enabled = settings.automation_settings.enabled_industries;
    const updated = enabled.includes(industryValue)
      ? enabled.filter(i => i !== industryValue)
      : [...enabled, industryValue];

    // When disabling an industry, also disable all its templates
    let updatedTemplates = settings.automation_settings.enabled_templates;
    if (enabled.includes(industryValue) && !updated.includes(industryValue)) {
      const industryTemplates = templatesByIndustry[industryValue] || [];
      const industryTemplateIds = industryTemplates.map(t => t.id);
      updatedTemplates = updatedTemplates.filter(id => !industryTemplateIds.includes(id));
    }

    setSettings({
      ...settings,
      automation_settings: {
        ...settings.automation_settings,
        enabled_industries: updated,
        enabled_templates: updatedTemplates
      }
    });
  };

  const toggleTemplate = (templateId: string) => {
    if (!settings) return;

    const enabled = settings.automation_settings.enabled_templates;
    const updated = enabled.includes(templateId)
      ? enabled.filter(id => id !== templateId)
      : [...enabled, templateId];

    setSettings({
      ...settings,
      automation_settings: {
        ...settings.automation_settings,
        enabled_templates: updated
      }
    });
  };

  const toggleAllTemplatesInIndustry = (industry: string, enable: boolean) => {
    if (!settings) return;

    const industryTemplates = templatesByIndustry[industry] || [];
    const industryTemplateIds = industryTemplates.map(t => t.id);

    let updatedTemplates = settings.automation_settings.enabled_templates;

    if (enable) {
      // Add all templates from this industry
      updatedTemplates = [...new Set([...updatedTemplates, ...industryTemplateIds])];
    } else {
      // Remove all templates from this industry
      updatedTemplates = updatedTemplates.filter(id => !industryTemplateIds.includes(id));
    }

    setSettings({
      ...settings,
      automation_settings: {
        ...settings.automation_settings,
        enabled_templates: updatedTemplates
      }
    });
  };

  const updateAutomationSetting = (field: keyof AutomationSettings, value: any) => {
    if (!settings) return;

    setSettings({
      ...settings,
      automation_settings: {
        ...settings.automation_settings,
        [field]: value
      }
    });
  };

  const updateBrandingSetting = (field: keyof BrandingSettings, value: any) => {
    if (!settings) return;

    setSettings({
      ...settings,
      branding_settings: {
        ...settings.branding_settings,
        [field]: value
      }
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading app settings...</span>
        </div>
      </div>
    );
  }

  if (!isUniversalAdmin) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <Shield className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Access Restricted</h3>
            <p className="text-gray-600">
              Universal admin privileges are required to access app settings.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!settings) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Settings Not Found</h3>
            <p className="text-gray-600 mb-4">
              Unable to load app settings. Please try refreshing the page.
            </p>
            <Button onClick={loadAppSettings} variant="outline">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">App Settings</h2>
          <p className="text-gray-600">
            Configure global application settings for on-premises deployments
          </p>
        </div>
        <Button onClick={saveSettings} disabled={saving}>
          {saving ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Save className="h-4 w-4 mr-2" />
          )}
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>

      {/* Section Navigation */}
      <Card>
        <CardContent className="p-4">
          <div className="flex space-x-4">
            <Button
              variant={activeSection === 'automation' ? 'default' : 'outline'}
              onClick={() => setActiveSection('automation')}
              className="flex items-center gap-2"
            >
              <Wrench className="h-4 w-4" />
              Automation Settings
            </Button>
            <Button
              variant={activeSection === 'branding' ? 'default' : 'outline'}
              onClick={() => setActiveSection('branding')}
              className="flex items-center gap-2"
            >
              <Palette className="h-4 w-4" />
              Branding Settings
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Automation Settings */}
      {activeSection === 'automation' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wrench className="h-5 w-5" />
                Industry Automations
              </CardTitle>
              <CardDescription>
                Configure which industry-specific automations are available for clients
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {loadingTemplates ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" />
                  <span>Loading templates...</span>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Industry Overview */}
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {availableIndustries.map((industry) => {
                      const industryTemplates = templatesByIndustry[industry] || [];
                      const enabledTemplatesInIndustry = industryTemplates.filter(t =>
                        settings.automation_settings.enabled_templates.includes(t.id)
                      ).length;
                      const isIndustryEnabled = settings.automation_settings.enabled_industries.includes(industry);

                      return (
                        <div
                          key={industry}
                          className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                            isIndustryEnabled
                              ? 'border-primary bg-primary/5'
                              : 'border-border hover:border-primary/50'
                          }`}
                          onClick={() => toggleIndustry(industry)}
                        >
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium">{industry}</span>
                              {isIndustryEnabled && (
                                <CheckCircle className="h-4 w-4 text-indigo-600" />
                              )}
                            </div>
                            <div className="text-xs text-gray-600">
                              {enabledTemplatesInIndustry}/{industryTemplates.length} templates
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Summary */}
                  <div className="flex items-center gap-4">
                    <Badge variant="secondary">
                      {settings.automation_settings.enabled_industries.length} industries enabled
                    </Badge>
                    <Badge variant="outline">
                      {settings.automation_settings.enabled_templates.length} templates enabled
                    </Badge>
                  </div>

                  <Separator />

                  {/* Templates by Industry */}
                  <div className="space-y-4">
                    <h4 className="text-sm font-medium text-gray-600">Templates by Industry</h4>
                    {Object.entries(templatesByIndustry).map(([industry, templates]) => {
                      const isIndustryEnabled = settings.automation_settings.enabled_industries.includes(industry);
                      const enabledTemplatesInIndustry = templates.filter(t =>
                        settings.automation_settings.enabled_templates.includes(t.id)
                      );
                      const allTemplatesEnabled = templates.length > 0 && enabledTemplatesInIndustry.length === templates.length;

                      if (!isIndustryEnabled) return null;

                      return (
                        <div key={industry} className="border rounded-lg p-4 space-y-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <h5 className="font-medium">{industry}</h5>
                              <Badge variant="outline" className="text-xs">
                                {enabledTemplatesInIndustry.length}/{templates.length}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => toggleAllTemplatesInIndustry(industry, !allTemplatesEnabled)}
                              >
                                {allTemplatesEnabled ? 'Disable All' : 'Enable All'}
                              </Button>
                            </div>
                          </div>

                          <div className="grid gap-2">
                            {templates.map((template) => {
                              const isEnabled = settings.automation_settings.enabled_templates.includes(template.id);

                              return (
                                <div
                                  key={template.id}
                                  className={`p-3 border rounded cursor-pointer transition-colors ${
                                    isEnabled
                                      ? 'border-green-500 bg-green-50 dark:bg-green-950/20'
                                      : 'border-border hover:border-primary/50'
                                  }`}
                                  onClick={() => toggleTemplate(template.id)}
                                >
                                  <div className="flex items-start justify-between">
                                    <div className="space-y-1 flex-1">
                                      <div className="flex items-center gap-2">
                                        <span className="font-medium text-sm">{template.template_name}</span>
                                        {isEnabled && <CheckCircle className="h-4 w-4 text-green-600" />}
                                        <Badge variant="secondary" className="text-xs">
                                          {template.category}
                                        </Badge>
                                      </div>
                                      {template.description && (
                                        <p className="text-xs text-gray-600 line-clamp-2">
                                          {template.description}
                                        </p>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Automation Limits & Permissions</CardTitle>
              <CardDescription>
                Configure automation limits and approval requirements
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="max_automations">Max Automations per Organization</Label>
                  <Input
                    id="max_automations"
                    type="number"
                    value={settings.automation_settings.max_automations_per_org}
                    onChange={(e) => updateAutomationSetting('max_automations_per_org', parseInt(e.target.value) || 0)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="default_language">Default Language</Label>
                  <Select
                    value={settings.automation_settings.default_automation_language}
                    onValueChange={(value) => updateAutomationSetting('default_automation_language', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                      <SelectItem value="it">Italian</SelectItem>
                      <SelectItem value="pt">Portuguese</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Custom Automations</Label>
                    <p className="text-sm text-gray-600">
                      Allow users to create custom automations
                    </p>
                  </div>
                  <Switch
                    checked={settings.automation_settings.custom_automations_enabled}
                    onCheckedChange={(checked) => updateAutomationSetting('custom_automations_enabled', checked)}
                  />
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Automation Templates</Label>
                    <p className="text-sm text-gray-600">
                      Enable pre-built automation templates
                    </p>
                  </div>
                  <Switch
                    checked={settings.automation_settings.automation_templates_enabled}
                    onCheckedChange={(checked) => updateAutomationSetting('automation_templates_enabled', checked)}
                  />
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Approval Required</Label>
                    <p className="text-sm text-gray-600">
                      Require approval for new automations
                    </p>
                  </div>
                  <Switch
                    checked={settings.automation_settings.automation_approval_required}
                    onCheckedChange={(checked) => updateAutomationSetting('automation_approval_required', checked)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Branding Settings */}
      {activeSection === 'branding' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                Application Branding
              </CardTitle>
              <CardDescription>
                Customize the application branding for client deployments
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="app_name">Application Name</Label>
                  <Input
                    id="app_name"
                    value={settings.branding_settings.app_name}
                    onChange={(e) => updateBrandingSetting('app_name', e.target.value)}
                    placeholder="KasaAI"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="support_email">Support Email</Label>
                  <Input
                    id="support_email"
                    type="email"
                    value={settings.branding_settings.support_email}
                    onChange={(e) => updateBrandingSetting('support_email', e.target.value)}
                    placeholder="support@example.com"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="support_url">Support URL</Label>
                <Input
                  id="support_url"
                  type="url"
                  value={settings.branding_settings.support_url}
                  onChange={(e) => updateBrandingSetting('support_url', e.target.value)}
                  placeholder="https://support.example.com"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="welcome_message">Welcome Message</Label>
                <Textarea
                  id="welcome_message"
                  value={settings.branding_settings.welcome_message}
                  onChange={(e) => updateBrandingSetting('welcome_message', e.target.value)}
                  placeholder="Welcome to our AI platform..."
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="custom_footer">Custom Footer Text</Label>
                <Input
                  id="custom_footer"
                  value={settings.branding_settings.custom_footer_text}
                  onChange={(e) => updateBrandingSetting('custom_footer_text', e.target.value)}
                  placeholder="© 2024 Your Company. All rights reserved."
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Brand Colors & Assets
              </CardTitle>
              <CardDescription>
                Configure brand colors and upload logos
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="primary_color">Primary Color</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="primary_color"
                      type="color"
                      value={settings.branding_settings.primary_color}
                      onChange={(e) => updateBrandingSetting('primary_color', e.target.value)}
                      className="w-16 h-10 p-1"
                    />
                    <Input
                      value={settings.branding_settings.primary_color}
                      onChange={(e) => updateBrandingSetting('primary_color', e.target.value)}
                      placeholder="#6366f1"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="secondary_color">Secondary Color</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="secondary_color"
                      type="color"
                      value={settings.branding_settings.secondary_color}
                      onChange={(e) => updateBrandingSetting('secondary_color', e.target.value)}
                      className="w-16 h-10 p-1"
                    />
                    <Input
                      value={settings.branding_settings.secondary_color}
                      onChange={(e) => updateBrandingSetting('secondary_color', e.target.value)}
                      placeholder="#8b5cf6"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="accent_color">Accent Color</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="accent_color"
                      type="color"
                      value={settings.branding_settings.accent_color}
                      onChange={(e) => updateBrandingSetting('accent_color', e.target.value)}
                      className="w-16 h-10 p-1"
                    />
                    <Input
                      value={settings.branding_settings.accent_color}
                      onChange={(e) => updateBrandingSetting('accent_color', e.target.value)}
                      placeholder="#06b6d4"
                    />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="app_logo">Application Logo URL</Label>
                  <Input
                    id="app_logo"
                    type="url"
                    value={settings.branding_settings.app_logo_url}
                    onChange={(e) => updateBrandingSetting('app_logo_url', e.target.value)}
                    placeholder="https://example.com/logo.png"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="favicon">Favicon URL</Label>
                  <Input
                    id="favicon"
                    type="url"
                    value={settings.branding_settings.app_favicon_url}
                    onChange={(e) => updateBrandingSetting('app_favicon_url', e.target.value)}
                    placeholder="https://example.com/favicon.ico"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="login_logo">Login Page Logo URL</Label>
                  <Input
                    id="login_logo"
                    type="url"
                    value={settings.branding_settings.login_logo_url}
                    onChange={(e) => updateBrandingSetting('login_logo_url', e.target.value)}
                    placeholder="https://example.com/login-logo.png"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="login_background">Login Background URL</Label>
                  <Input
                    id="login_background"
                    type="url"
                    value={settings.branding_settings.login_background_url}
                    onChange={(e) => updateBrandingSetting('login_background_url', e.target.value)}
                    placeholder="https://example.com/background.jpg"
                  />
                </div>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label>Show "Powered by KasaAI"</Label>
                  <p className="text-sm text-gray-600">
                    Display KasaAI branding in the footer
                  </p>
                </div>
                <Switch
                  checked={settings.branding_settings.show_powered_by}
                  onCheckedChange={(checked) => updateBrandingSetting('show_powered_by', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default AppSettings;