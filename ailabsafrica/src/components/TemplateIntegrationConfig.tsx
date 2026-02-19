import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { 
  Calendar,
  Mail,
  MessageSquare,
  Database,
  Sheet,
  Settings,
  TestTube,
  CheckCircle,
  AlertCircle,
  Loader2,
  ExternalLink,
  Key,
  Globe,
  Phone,
  Zap,
  Shield,
  RefreshCw,
  Copy,
  Eye,
  EyeOff
} from 'lucide-react';

interface IntegrationConfig {
  calendar?: {
    enabled: boolean;
    type: 'google' | 'outlook' | 'calendly' | 'custom';
    calendarId?: string;
    apiKey?: string;
    webhookUrl?: string;
    timezone?: string;
  };
  email?: {
    enabled: boolean;
    provider: 'gmail' | 'outlook' | 'sendgrid' | 'mailgun' | 'custom';
    emailAddress?: string;
    apiKey?: string;
    templates?: {
      confirmation?: string;
      reminder?: string;
      cancellation?: string;
      followUp?: string;
    };
  };
  whatsapp?: {
    enabled: boolean;
    phoneNumber?: string;
    apiKey?: string;
    provider?: 'twilio' | 'whatsapp-business' | 'custom';
    webhookUrl?: string;
  };
  sms?: {
    enabled: boolean;
    phoneNumber?: string;
    apiKey?: string;
    provider?: 'twilio' | 'vonage' | 'custom';
  };
  telegram?: {
    enabled: boolean;
    botToken?: string;
    chatId?: string;
    webhookUrl?: string;
  };
  slack?: {
    enabled: boolean;
    webhookUrl?: string;
    channel?: string;
    botToken?: string;
  };
  sheets?: {
    enabled: boolean;
    spreadsheetId?: string;
    apiKey?: string;
    sheets?: {
      appointments?: string;
      contacts?: string;
      analytics?: string;
      interactions?: string;
    };
  };
  crm?: {
    enabled: boolean;
    provider: 'salesforce' | 'hubspot' | 'pipedrive' | 'zoho' | 'custom';
    apiKey?: string;
    baseUrl?: string;
    customFields?: Record<string, string>;
  };
  database?: {
    enabled: boolean;
    type: 'supabase' | 'firebase' | 'mongodb' | 'postgresql' | 'mysql' | 'custom';
    connectionString?: string;
    tables?: {
      appointments?: string;
      contacts?: string;
      interactions?: string;
      analytics?: string;
    };
  };
  helpdesk?: {
    enabled: boolean;
    provider: 'freshdesk' | 'intercom' | 'zendesk' | 'custom';
    apiKey?: string;
    baseUrl?: string;
    ticketFields?: Record<string, string>;
  };
}

interface TemplateIntegrationConfigProps {
  templateId: string;
  initialConfig?: IntegrationConfig;
  onSave: (config: IntegrationConfig) => void;
  onClose: () => void;
}

const TemplateIntegrationConfig: React.FC<TemplateIntegrationConfigProps> = ({
  templateId,
  initialConfig = {},
  onSave,
  onClose
}) => {
  const [config, setConfig] = useState<IntegrationConfig>(initialConfig);
  const [isOpen, setIsOpen] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const { toast } = useToast();

  const updateConfig = (path: string, value: any) => {
    setConfig(prev => {
      const newConfig = { ...prev };
      const keys = path.split('.');
      let current: any = newConfig;
      
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) current[keys[i]] = {};
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;
      return newConfig;
    });
  };

  const toggleSecret = (path: string) => {
    setShowSecrets(prev => ({
      ...prev,
      [path]: !prev[path]
    }));
  };

  const testIntegration = async (integrationType: string) => {
    setTesting(integrationType);
    try {
      // Simulate API test
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock test result
      const success = Math.random() > 0.3; // 70% success rate
      
      toast({
        title: success ? "Test Successful" : "Test Failed",
        description: success 
          ? `${integrationType} integration is working correctly`
          : `Failed to connect to ${integrationType}. Please check your configuration.`,
        variant: success ? "default" : "destructive"
      });
    } catch (error) {
      toast({
        title: "Test Failed",
        description: `Error testing ${integrationType} integration`,
        variant: "destructive"
      });
    } finally {
      setTesting(null);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Validate required fields
      const errors: string[] = [];
      
      Object.entries(config).forEach(([integration, settings]) => {
        if (settings?.enabled) {
          // Add validation logic for each integration type
          if (integration === 'calendar' && !settings.calendarId) {
            errors.push('Calendar ID is required for calendar integration');
          }
          if (integration === 'email' && !settings.emailAddress) {
            errors.push('Email address is required for email integration');
          }
          // Add more validation as needed
        }
      });

      if (errors.length > 0) {
        toast({
          title: "Validation Error",
          description: errors.join(', '),
          variant: "destructive"
        });
        return;
      }

      onSave(config);
      toast({
        title: "Success",
        description: "Integration configuration saved successfully"
      });
      setIsOpen(false);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save integration configuration",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const renderCalendarConfig = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Calendar Integration
        </CardTitle>
        <CardDescription>
          Connect to Google Calendar, Outlook, or Calendly for appointment scheduling
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <Label htmlFor="calendar-enabled">Enable Calendar Integration</Label>
          <Switch
            id="calendar-enabled"
            checked={config.calendar?.enabled || false}
            onCheckedChange={(checked) => updateConfig('calendar.enabled', checked)}
          />
        </div>

        {config.calendar?.enabled && (
          <div className="space-y-4">
            <div>
              <Label htmlFor="calendar-type">Calendar Provider</Label>
              <Select
                value={config.calendar?.type || 'google'}
                onValueChange={(value) => updateConfig('calendar.type', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="google">Google Calendar</SelectItem>
                  <SelectItem value="outlook">Outlook Calendar</SelectItem>
                  <SelectItem value="calendly">Calendly</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="calendar-id">Calendar ID</Label>
              <Input
                id="calendar-id"
                placeholder="Enter calendar ID or URL"
                value={config.calendar?.calendarId || ''}
                onChange={(e) => updateConfig('calendar.calendarId', e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="calendar-api-key">API Key</Label>
              <div className="relative">
                <Input
                  id="calendar-api-key"
                  type={showSecrets['calendar.apiKey'] ? 'text' : 'password'}
                  placeholder="Enter API key"
                  value={config.calendar?.apiKey || ''}
                  onChange={(e) => updateConfig('calendar.apiKey', e.target.value)}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => toggleSecret('calendar.apiKey')}
                >
                  {showSecrets['calendar.apiKey'] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => testIntegration('Calendar')}
                disabled={testing === 'Calendar'}
              >
                {testing === 'Calendar' ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Testing...
                  </>
                ) : (
                  <>
                    <TestTube className="h-4 w-4 mr-2" />
                    Test Connection
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderEmailConfig = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Mail className="h-5 w-5" />
          Email Integration
        </CardTitle>
        <CardDescription>
          Configure email notifications and templates
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <Label htmlFor="email-enabled">Enable Email Integration</Label>
          <Switch
            id="email-enabled"
            checked={config.email?.enabled || false}
            onCheckedChange={(checked) => updateConfig('email.enabled', checked)}
          />
        </div>

        {config.email?.enabled && (
          <div className="space-y-4">
            <div>
              <Label htmlFor="email-provider">Email Provider</Label>
              <Select
                value={config.email?.provider || 'gmail'}
                onValueChange={(value) => updateConfig('email.provider', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gmail">Gmail</SelectItem>
                  <SelectItem value="outlook">Outlook</SelectItem>
                  <SelectItem value="sendgrid">SendGrid</SelectItem>
                  <SelectItem value="mailgun">Mailgun</SelectItem>
                  <SelectItem value="custom">Custom SMTP</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="email-address">Email Address</Label>
              <Input
                id="email-address"
                type="email"
                placeholder="Enter email address"
                value={config.email?.emailAddress || ''}
                onChange={(e) => updateConfig('email.emailAddress', e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="email-api-key">API Key</Label>
              <div className="relative">
                <Input
                  id="email-api-key"
                  type={showSecrets['email.apiKey'] ? 'text' : 'password'}
                  placeholder="Enter API key"
                  value={config.email?.apiKey || ''}
                  onChange={(e) => updateConfig('email.apiKey', e.target.value)}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => toggleSecret('email.apiKey')}
                >
                  {showSecrets['email.apiKey'] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Email Templates</Label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="confirmation-template">Confirmation Template</Label>
                  <Textarea
                    id="confirmation-template"
                    placeholder="Enter confirmation email template"
                    value={config.email?.templates?.confirmation || ''}
                    onChange={(e) => updateConfig('email.templates.confirmation', e.target.value)}
                    rows={3}
                  />
                </div>
                <div>
                  <Label htmlFor="reminder-template">Reminder Template</Label>
                  <Textarea
                    id="reminder-template"
                    placeholder="Enter reminder email template"
                    value={config.email?.templates?.reminder || ''}
                    onChange={(e) => updateConfig('email.templates.reminder', e.target.value)}
                    rows={3}
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => testIntegration('Email')}
                disabled={testing === 'Email'}
              >
                {testing === 'Email' ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Testing...
                  </>
                ) : (
                  <>
                    <TestTube className="h-4 w-4 mr-2" />
                    Test Connection
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderChatConfig = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Chat Integrations
        </CardTitle>
        <CardDescription>
          Configure WhatsApp, SMS, Telegram, and Slack integrations
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* WhatsApp */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="whatsapp-enabled">Enable WhatsApp</Label>
            <Switch
              id="whatsapp-enabled"
              checked={config.whatsapp?.enabled || false}
              onCheckedChange={(checked) => updateConfig('whatsapp.enabled', checked)}
            />
          </div>

          {config.whatsapp?.enabled && (
            <div className="space-y-4 pl-4 border-l-2 border-muted">
              <div>
                <Label htmlFor="whatsapp-phone">Phone Number</Label>
                <Input
                  id="whatsapp-phone"
                  placeholder="+1234567890"
                  value={config.whatsapp?.phoneNumber || ''}
                  onChange={(e) => updateConfig('whatsapp.phoneNumber', e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="whatsapp-provider">Provider</Label>
                <Select
                  value={config.whatsapp?.provider || 'twilio'}
                  onValueChange={(value) => updateConfig('whatsapp.provider', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="twilio">Twilio</SelectItem>
                    <SelectItem value="whatsapp-business">WhatsApp Business API</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="whatsapp-api-key">API Key</Label>
                <div className="relative">
                  <Input
                    id="whatsapp-api-key"
                    type={showSecrets['whatsapp.apiKey'] ? 'text' : 'password'}
                    placeholder="Enter API key"
                    value={config.whatsapp?.apiKey || ''}
                    onChange={(e) => updateConfig('whatsapp.apiKey', e.target.value)}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => toggleSecret('whatsapp.apiKey')}
                  >
                    {showSecrets['whatsapp.apiKey'] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* SMS */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="sms-enabled">Enable SMS</Label>
            <Switch
              id="sms-enabled"
              checked={config.sms?.enabled || false}
              onCheckedChange={(checked) => updateConfig('sms.enabled', checked)}
            />
          </div>

          {config.sms?.enabled && (
            <div className="space-y-4 pl-4 border-l-2 border-muted">
              <div>
                <Label htmlFor="sms-phone">Phone Number</Label>
                <Input
                  id="sms-phone"
                  placeholder="+1234567890"
                  value={config.sms?.phoneNumber || ''}
                  onChange={(e) => updateConfig('sms.phoneNumber', e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="sms-provider">Provider</Label>
                <Select
                  value={config.sms?.provider || 'twilio'}
                  onValueChange={(value) => updateConfig('sms.provider', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="twilio">Twilio</SelectItem>
                    <SelectItem value="vonage">Vonage</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="sms-api-key">API Key</Label>
                <div className="relative">
                  <Input
                    id="sms-api-key"
                    type={showSecrets['sms.apiKey'] ? 'text' : 'password'}
                    placeholder="Enter API key"
                    value={config.sms?.apiKey || ''}
                    onChange={(e) => updateConfig('sms.apiKey', e.target.value)}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => toggleSecret('sms.apiKey')}
                  >
                    {showSecrets['sms.apiKey'] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => testIntegration('Chat')}
            disabled={testing === 'Chat'}
          >
            {testing === 'Chat' ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Testing...
              </>
            ) : (
              <>
                <TestTube className="h-4 w-4 mr-2" />
                Test Chat Integrations
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const renderDataConfig = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5" />
          Data Integrations
        </CardTitle>
        <CardDescription>
          Configure Google Sheets, CRM, and database connections
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Google Sheets */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="sheets-enabled">Enable Google Sheets</Label>
            <Switch
              id="sheets-enabled"
              checked={config.sheets?.enabled || false}
              onCheckedChange={(checked) => updateConfig('sheets.enabled', checked)}
            />
          </div>

          {config.sheets?.enabled && (
            <div className="space-y-4 pl-4 border-l-2 border-muted">
              <div>
                <Label htmlFor="sheets-id">Spreadsheet ID</Label>
                <Input
                  id="sheets-id"
                  placeholder="Enter Google Sheets ID"
                  value={config.sheets?.spreadsheetId || ''}
                  onChange={(e) => updateConfig('sheets.spreadsheetId', e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="sheets-api-key">API Key</Label>
                <div className="relative">
                  <Input
                    id="sheets-api-key"
                    type={showSecrets['sheets.apiKey'] ? 'text' : 'password'}
                    placeholder="Enter API key"
                    value={config.sheets?.apiKey || ''}
                    onChange={(e) => updateConfig('sheets.apiKey', e.target.value)}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => toggleSecret('sheets.apiKey')}
                  >
                    {showSecrets['sheets.apiKey'] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* CRM */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="crm-enabled">Enable CRM</Label>
            <Switch
              id="crm-enabled"
              checked={config.crm?.enabled || false}
              onCheckedChange={(checked) => updateConfig('crm.enabled', checked)}
            />
          </div>

          {config.crm?.enabled && (
            <div className="space-y-4 pl-4 border-l-2 border-muted">
              <div>
                <Label htmlFor="crm-provider">CRM Provider</Label>
                <Select
                  value={config.crm?.provider || 'salesforce'}
                  onValueChange={(value) => updateConfig('crm.provider', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="salesforce">Salesforce</SelectItem>
                    <SelectItem value="hubspot">HubSpot</SelectItem>
                    <SelectItem value="pipedrive">Pipedrive</SelectItem>
                    <SelectItem value="zoho">Zoho CRM</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="crm-api-key">API Key</Label>
                <div className="relative">
                  <Input
                    id="crm-api-key"
                    type={showSecrets['crm.apiKey'] ? 'text' : 'password'}
                    placeholder="Enter API key"
                    value={config.crm?.apiKey || ''}
                    onChange={(e) => updateConfig('crm.apiKey', e.target.value)}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => toggleSecret('crm.apiKey')}
                  >
                    {showSecrets['crm.apiKey'] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>

              <div>
                <Label htmlFor="crm-base-url">Base URL</Label>
                <Input
                  id="crm-base-url"
                  placeholder="https://api.example.com"
                  value={config.crm?.baseUrl || ''}
                  onChange={(e) => updateConfig('crm.baseUrl', e.target.value)}
                />
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => testIntegration('Data')}
            disabled={testing === 'Data'}
          >
            {testing === 'Data' ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Testing...
              </>
            ) : (
              <>
                <TestTube className="h-4 w-4 mr-2" />
                Test Data Integrations
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configure Template Integrations</DialogTitle>
          <DialogDescription>
            Set up integrations for calendar, email, chat, and data services
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="calendar" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="calendar">Calendar</TabsTrigger>
            <TabsTrigger value="email">Email</TabsTrigger>
            <TabsTrigger value="chat">Chat</TabsTrigger>
            <TabsTrigger value="data">Data</TabsTrigger>
          </TabsList>

          <TabsContent value="calendar" className="space-y-4">
            {renderCalendarConfig()}
          </TabsContent>

          <TabsContent value="email" className="space-y-4">
            {renderEmailConfig()}
          </TabsContent>

          <TabsContent value="chat" className="space-y-4">
            {renderChatConfig()}
          </TabsContent>

          <TabsContent value="data" className="space-y-4">
            {renderDataConfig()}
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Saving...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4 mr-2" />
                Save Configuration
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TemplateIntegrationConfig;
