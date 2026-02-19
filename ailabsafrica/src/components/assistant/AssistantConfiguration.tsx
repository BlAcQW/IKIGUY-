import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { 
  Calendar,
  Mail,
  MessageSquare,
  FileSpreadsheet,
  Database,
  Users,
  Settings,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Copy,
  Eye,
  EyeOff,
  Phone,
  MessageCircle,
  HeadphonesIcon,
  Zap
} from 'lucide-react';

interface Assistant {
  id: string;
  assistant_name: string;
  assistant_type: string;
  assistant_id: string;
  demo_url: string;
  created_at: string;
  status: string;
  voice_id?: string;
}

interface AssistantConfigurationProps {
  assistant: Assistant;
  onConfigurationComplete: (assistantId: string, config: any) => void;
  onClose: () => void;
}

const AssistantConfiguration: React.FC<AssistantConfigurationProps> = ({
  assistant,
  onConfigurationComplete,
  onClose
}) => {
  const { toast } = useToast();
  const { user } = useAuth();
  const [config, setConfig] = useState({
    calendar: {
      enabled: false,
      type: 'google' as const,
      calendarId: '',
      apiKey: ''
    },
    email: {
      enabled: false,
      provider: 'gmail' as const,
      emailAddress: '',
      apiKey: '',
      templates: {
        confirmation: '',
        reminder: '',
        cancellation: ''
      }
    },
    chats: {
      enabled: false,
      whatsapp: {
        enabled: false,
        phoneNumber: '',
        apiKey: '',
        provider: 'twilio' as const
      },
      sms: {
        enabled: false,
        phoneNumber: '',
        apiKey: '',
        provider: 'twilio' as const
      },
      telegram: {
        enabled: false,
        botToken: '',
        chatId: ''
      },
      slack: {
        enabled: false,
        webhookUrl: '',
        channel: ''
      }
    },
    helpdesk: {
      enabled: false,
      provider: 'freshdesk' as const,
      apiKey: '',
      baseUrl: '',
      domain: ''
    },
    sheets: {
      enabled: false,
      spreadsheetId: '',
      apiKey: '',
      sheets: {
        appointments: 'Appointments',
        contacts: 'Contacts',
        analytics: 'Analytics'
      }
    },
    crm: {
      enabled: false,
      provider: 'salesforce' as const,
      apiKey: '',
      baseUrl: ''
    },
    database: {
      enabled: false,
      type: 'supabase' as const,
      connectionString: '',
      tables: {
        appointments: 'appointments',
        contacts: 'contacts',
        interactions: 'interactions'
      }
    }
  });

  const [showApiKeys, setShowApiKeys] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateConfig = (section: string, field: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section as keyof typeof prev],
        [field]: value
      }
    }));
  };

  const updateNestedConfig = (section: string, subsection: string, field: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section as keyof typeof prev],
        [subsection]: {
          ...prev[section as keyof typeof prev][subsection as keyof any],
          [field]: value
        }
      }
    }));
  };

  const handleSave = async () => {
    setIsSubmitting(true);
    try {
      // Save configuration to database
      const { error } = await supabase.functions.invoke('manage-assistant-config', {
        body: {
          action: 'save',
          assistant_id: assistant.id,
          user_id: user.id,
          configuration: config
        }
      });

      if (error) throw error;

      onConfigurationComplete(assistant.id, config);
      
      toast({
        title: 'Configuration Saved',
        description: 'Assistant integrations have been configured successfully.',
      });
      
      onClose();
    } catch (error: any) {
      console.error('Error saving configuration:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to save configuration. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied',
      description: 'API key copied to clipboard',
    });
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Configure {assistant.assistant_name}
          </DialogTitle>
          <DialogDescription>
            Set up integrations and webhooks for your assistant. These will be used to perform actions based on Vapi webhook events.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="calendar" className="w-full">
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="calendar" className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              <span className="hidden sm:inline">Calendar</span>
            </TabsTrigger>
            <TabsTrigger value="email" className="flex items-center gap-2">
              <Mail className="h-4 w-4" />
              <span className="hidden sm:inline">Email</span>
            </TabsTrigger>
            <TabsTrigger value="chats" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              <span className="hidden sm:inline">Chats</span>
            </TabsTrigger>
            <TabsTrigger value="helpdesk" className="flex items-center gap-2">
              <HeadphonesIcon className="h-4 w-4" />
              <span className="hidden sm:inline">Helpdesk</span>
            </TabsTrigger>
            <TabsTrigger value="sheets" className="flex items-center gap-2">
              <FileSpreadsheet className="h-4 w-4" />
              <span className="hidden sm:inline">Sheets</span>
            </TabsTrigger>
            <TabsTrigger value="crm" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              <span className="hidden sm:inline">CRM</span>
            </TabsTrigger>
            <TabsTrigger value="database" className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              <span className="hidden sm:inline">Database</span>
            </TabsTrigger>
          </TabsList>

          {/* Calendar Configuration */}
          <TabsContent value="calendar" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Calendar Integration
                </CardTitle>
                <CardDescription>
                  Connect your calendar to automatically schedule appointments and send reminders.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="calendar-enabled">Enable Calendar Integration</Label>
                  <Switch
                    id="calendar-enabled"
                    checked={config.calendar.enabled}
                    onCheckedChange={(checked) => updateConfig('calendar', 'enabled', checked)}
                  />
                </div>

                {config.calendar.enabled && (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="calendar-type">Calendar Provider</Label>
                      <Select
                        value={config.calendar.type}
                        onValueChange={(value) => updateConfig('calendar', 'type', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="google">Google Calendar</SelectItem>
                          <SelectItem value="outlook">Outlook Calendar</SelectItem>
                          <SelectItem value="calendly">Calendly</SelectItem>
                          <SelectItem value="custom">Custom Calendar</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="calendar-id">Calendar ID</Label>
                      <Input
                        id="calendar-id"
                        placeholder="Enter calendar ID"
                        value={config.calendar.calendarId}
                        onChange={(e) => updateConfig('calendar', 'calendarId', e.target.value)}
                      />
                    </div>

                    <div>
                      <Label htmlFor="calendar-api-key">API Key</Label>
                      <div className="relative">
                        <Input
                          id="calendar-api-key"
                          type={showApiKeys ? 'text' : 'password'}
                          placeholder="Enter API key"
                          value={config.calendar.apiKey}
                          onChange={(e) => updateConfig('calendar', 'apiKey', e.target.value)}
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3"
                          onClick={() => setShowApiKeys(!showApiKeys)}
                        >
                          {showApiKeys ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Email Configuration */}
          <TabsContent value="email" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  Email Integration
                </CardTitle>
                <CardDescription>
                  Configure email notifications and automated responses.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="email-enabled">Enable Email Integration</Label>
                  <Switch
                    id="email-enabled"
                    checked={config.email.enabled}
                    onCheckedChange={(checked) => updateConfig('email', 'enabled', checked)}
                  />
                </div>

                {config.email.enabled && (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="email-provider">Email Provider</Label>
                      <Select
                        value={config.email.provider}
                        onValueChange={(value) => updateConfig('email', 'provider', value)}
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
                        value={config.email.emailAddress}
                        onChange={(e) => updateConfig('email', 'emailAddress', e.target.value)}
                      />
                    </div>

                    <div>
                      <Label htmlFor="email-api-key">API Key</Label>
                      <div className="relative">
                        <Input
                          id="email-api-key"
                          type={showApiKeys ? 'text' : 'password'}
                          placeholder="Enter API key"
                          value={config.email.apiKey}
                          onChange={(e) => updateConfig('email', 'apiKey', e.target.value)}
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3"
                          onClick={() => setShowApiKeys(!showApiKeys)}
                        >
                          {showApiKeys ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Email Templates</Label>
                      <div className="space-y-2">
                        <div>
                          <Label htmlFor="confirmation-template">Confirmation Template</Label>
                          <Textarea
                            id="confirmation-template"
                            placeholder="Enter confirmation email template"
                            value={config.email.templates.confirmation}
                            onChange={(e) => updateNestedConfig('email', 'templates', 'confirmation', e.target.value)}
                          />
                        </div>
                        <div>
                          <Label htmlFor="reminder-template">Reminder Template</Label>
                          <Textarea
                            id="reminder-template"
                            placeholder="Enter reminder email template"
                            value={config.email.templates.reminder}
                            onChange={(e) => updateNestedConfig('email', 'templates', 'reminder', e.target.value)}
                          />
                        </div>
                        <div>
                          <Label htmlFor="cancellation-template">Cancellation Template</Label>
                          <Textarea
                            id="cancellation-template"
                            placeholder="Enter cancellation email template"
                            value={config.email.templates.cancellation}
                            onChange={(e) => updateNestedConfig('email', 'templates', 'cancellation', e.target.value)}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Chats Configuration */}
          <TabsContent value="chats" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Chat Integrations
                </CardTitle>
                <CardDescription>
                  Configure messaging platforms for notifications and automated responses.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <Label htmlFor="chats-enabled">Enable Chat Integrations</Label>
                  <Switch
                    id="chats-enabled"
                    checked={config.chats.enabled}
                    onCheckedChange={(checked) => updateConfig('chats', 'enabled', checked)}
                  />
                </div>

                {config.chats.enabled && (
                  <div className="space-y-6">
                    {/* WhatsApp */}
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                          <MessageSquare className="h-5 w-5 text-green-600" />
                          <Label className="text-lg font-semibold">WhatsApp</Label>
                        </div>
                        <Switch
                          checked={config.chats.whatsapp.enabled}
                          onCheckedChange={(checked) => updateNestedConfig('chats', 'whatsapp', 'enabled', checked)}
                        />
                      </div>
                      
                      {config.chats.whatsapp.enabled && (
                        <div className="space-y-4">
                          <div>
                            <Label htmlFor="whatsapp-provider">Provider</Label>
                            <Select
                              value={config.chats.whatsapp.provider}
                              onValueChange={(value) => updateNestedConfig('chats', 'whatsapp', 'provider', value)}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="twilio">Twilio</SelectItem>
                                <SelectItem value="whatsapp-business">WhatsApp Business API</SelectItem>
                                <SelectItem value="custom">Custom Provider</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label htmlFor="whatsapp-phone">Phone Number</Label>
                            <Input
                              id="whatsapp-phone"
                              placeholder="+1234567890"
                              value={config.chats.whatsapp.phoneNumber}
                              onChange={(e) => updateNestedConfig('chats', 'whatsapp', 'phoneNumber', e.target.value)}
                            />
                          </div>
                          <div>
                            <Label htmlFor="whatsapp-api-key">API Key</Label>
                            <Input
                              id="whatsapp-api-key"
                              type="password"
                              placeholder="Enter API key"
                              value={config.chats.whatsapp.apiKey}
                              onChange={(e) => updateNestedConfig('chats', 'whatsapp', 'apiKey', e.target.value)}
                            />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* SMS */}
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                          <Phone className="h-5 w-5 text-blue-600" />
                          <Label className="text-lg font-semibold">SMS</Label>
                        </div>
                        <Switch
                          checked={config.chats.sms.enabled}
                          onCheckedChange={(checked) => updateNestedConfig('chats', 'sms', 'enabled', checked)}
                        />
                      </div>
                      
                      {config.chats.sms.enabled && (
                        <div className="space-y-4">
                          <div>
                            <Label htmlFor="sms-provider">Provider</Label>
                            <Select
                              value={config.chats.sms.provider}
                              onValueChange={(value) => updateNestedConfig('chats', 'sms', 'provider', value)}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="twilio">Twilio</SelectItem>
                                <SelectItem value="aws-sns">AWS SNS</SelectItem>
                                <SelectItem value="custom">Custom Provider</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label htmlFor="sms-phone">Phone Number</Label>
                            <Input
                              id="sms-phone"
                              placeholder="+1234567890"
                              value={config.chats.sms.phoneNumber}
                              onChange={(e) => updateNestedConfig('chats', 'sms', 'phoneNumber', e.target.value)}
                            />
                          </div>
                          <div>
                            <Label htmlFor="sms-api-key">API Key</Label>
                            <Input
                              id="sms-api-key"
                              type="password"
                              placeholder="Enter API key"
                              value={config.chats.sms.apiKey}
                              onChange={(e) => updateNestedConfig('chats', 'sms', 'apiKey', e.target.value)}
                            />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Telegram */}
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                          <MessageCircle className="h-5 w-5 text-blue-500" />
                          <Label className="text-lg font-semibold">Telegram</Label>
                        </div>
                        <Switch
                          checked={config.chats.telegram.enabled}
                          onCheckedChange={(checked) => updateNestedConfig('chats', 'telegram', 'enabled', checked)}
                        />
                      </div>
                      
                      {config.chats.telegram.enabled && (
                        <div className="space-y-4">
                          <div>
                            <Label htmlFor="telegram-bot-token">Bot Token</Label>
                            <Input
                              id="telegram-bot-token"
                              type="password"
                              placeholder="Enter bot token"
                              value={config.chats.telegram.botToken}
                              onChange={(e) => updateNestedConfig('chats', 'telegram', 'botToken', e.target.value)}
                            />
                          </div>
                          <div>
                            <Label htmlFor="telegram-chat-id">Chat ID</Label>
                            <Input
                              id="telegram-chat-id"
                              placeholder="Enter chat ID"
                              value={config.chats.telegram.chatId}
                              onChange={(e) => updateNestedConfig('chats', 'telegram', 'chatId', e.target.value)}
                            />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Slack */}
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                          <Zap className="h-5 w-5 text-purple-600" />
                          <Label className="text-lg font-semibold">Slack</Label>
                        </div>
                        <Switch
                          checked={config.chats.slack.enabled}
                          onCheckedChange={(checked) => updateNestedConfig('chats', 'slack', 'enabled', checked)}
                        />
                      </div>
                      
                      {config.chats.slack.enabled && (
                        <div className="space-y-4">
                          <div>
                            <Label htmlFor="slack-webhook">Webhook URL</Label>
                            <Input
                              id="slack-webhook"
                              type="password"
                              placeholder="Enter webhook URL"
                              value={config.chats.slack.webhookUrl}
                              onChange={(e) => updateNestedConfig('chats', 'slack', 'webhookUrl', e.target.value)}
                            />
                          </div>
                          <div>
                            <Label htmlFor="slack-channel">Channel</Label>
                            <Input
                              id="slack-channel"
                              placeholder="#general"
                              value={config.chats.slack.channel}
                              onChange={(e) => updateNestedConfig('chats', 'slack', 'channel', e.target.value)}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Helpdesk Configuration */}
          <TabsContent value="helpdesk" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <HeadphonesIcon className="h-5 w-5" />
                  Helpdesk Integration
                </CardTitle>
                <CardDescription>
                  Connect your helpdesk system to automatically create and update tickets.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="helpdesk-enabled">Enable Helpdesk Integration</Label>
                  <Switch
                    id="helpdesk-enabled"
                    checked={config.helpdesk.enabled}
                    onCheckedChange={(checked) => updateConfig('helpdesk', 'enabled', checked)}
                  />
                </div>

                {config.helpdesk.enabled && (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="helpdesk-provider">Helpdesk Provider</Label>
                      <Select
                        value={config.helpdesk.provider}
                        onValueChange={(value) => updateConfig('helpdesk', 'provider', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="freshdesk">Freshdesk</SelectItem>
                          <SelectItem value="intercom">Intercom</SelectItem>
                          <SelectItem value="zendesk">Zendesk</SelectItem>
                          <SelectItem value="custom">Custom Helpdesk</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="helpdesk-domain">Domain</Label>
                      <Input
                        id="helpdesk-domain"
                        placeholder="yourcompany.freshdesk.com"
                        value={config.helpdesk.domain}
                        onChange={(e) => updateConfig('helpdesk', 'domain', e.target.value)}
                      />
                    </div>

                    <div>
                      <Label htmlFor="helpdesk-api-key">API Key</Label>
                      <div className="relative">
                        <Input
                          id="helpdesk-api-key"
                          type={showApiKeys ? 'text' : 'password'}
                          placeholder="Enter API key"
                          value={config.helpdesk.apiKey}
                          onChange={(e) => updateConfig('helpdesk', 'apiKey', e.target.value)}
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3"
                          onClick={() => setShowApiKeys(!showApiKeys)}
                        >
                          {showApiKeys ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="helpdesk-base-url">Base URL (Optional)</Label>
                      <Input
                        id="helpdesk-base-url"
                        placeholder="https://api.freshdesk.com/v2"
                        value={config.helpdesk.baseUrl}
                        onChange={(e) => updateConfig('helpdesk', 'baseUrl', e.target.value)}
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Sheets Configuration */}
          <TabsContent value="sheets" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5" />
                  Google Sheets Integration
                </CardTitle>
                <CardDescription>
                  Connect Google Sheets to log interactions and store data.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="sheets-enabled">Enable Sheets Integration</Label>
                  <Switch
                    id="sheets-enabled"
                    checked={config.sheets.enabled}
                    onCheckedChange={(checked) => updateConfig('sheets', 'enabled', checked)}
                  />
                </div>

                {config.sheets.enabled && (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="sheets-id">Spreadsheet ID</Label>
                      <Input
                        id="sheets-id"
                        placeholder="Enter Google Sheets ID"
                        value={config.sheets.spreadsheetId}
                        onChange={(e) => updateConfig('sheets', 'spreadsheetId', e.target.value)}
                      />
                    </div>

                    <div>
                      <Label htmlFor="sheets-api-key">API Key</Label>
                      <div className="relative">
                        <Input
                          id="sheets-api-key"
                          type={showApiKeys ? 'text' : 'password'}
                          placeholder="Enter API key"
                          value={config.sheets.apiKey}
                          onChange={(e) => updateConfig('sheets', 'apiKey', e.target.value)}
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3"
                          onClick={() => setShowApiKeys(!showApiKeys)}
                        >
                          {showApiKeys ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Sheet Names</Label>
                      <div className="space-y-2">
                        <div>
                          <Label htmlFor="appointments-sheet">Appointments Sheet</Label>
                          <Input
                            id="appointments-sheet"
                            placeholder="Appointments"
                            value={config.sheets.sheets.appointments}
                            onChange={(e) => updateNestedConfig('sheets', 'sheets', 'appointments', e.target.value)}
                          />
                        </div>
                        <div>
                          <Label htmlFor="contacts-sheet">Contacts Sheet</Label>
                          <Input
                            id="contacts-sheet"
                            placeholder="Contacts"
                            value={config.sheets.sheets.contacts}
                            onChange={(e) => updateNestedConfig('sheets', 'sheets', 'contacts', e.target.value)}
                          />
                        </div>
                        <div>
                          <Label htmlFor="analytics-sheet">Analytics Sheet</Label>
                          <Input
                            id="analytics-sheet"
                            placeholder="Analytics"
                            value={config.sheets.sheets.analytics}
                            onChange={(e) => updateNestedConfig('sheets', 'sheets', 'analytics', e.target.value)}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* CRM Configuration */}
          <TabsContent value="crm" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  CRM Integration
                </CardTitle>
                <CardDescription>
                  Connect your CRM system to manage leads and customer data.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="crm-enabled">Enable CRM Integration</Label>
                  <Switch
                    id="crm-enabled"
                    checked={config.crm.enabled}
                    onCheckedChange={(checked) => updateConfig('crm', 'enabled', checked)}
                  />
                </div>

                {config.crm.enabled && (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="crm-provider">CRM Provider</Label>
                      <Select
                        value={config.crm.provider}
                        onValueChange={(value) => updateConfig('crm', 'provider', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="salesforce">Salesforce</SelectItem>
                          <SelectItem value="hubspot">HubSpot</SelectItem>
                          <SelectItem value="pipedrive">Pipedrive</SelectItem>
                          <SelectItem value="custom">Custom CRM</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="crm-api-key">API Key</Label>
                      <div className="relative">
                        <Input
                          id="crm-api-key"
                          type={showApiKeys ? 'text' : 'password'}
                          placeholder="Enter API key"
                          value={config.crm.apiKey}
                          onChange={(e) => updateConfig('crm', 'apiKey', e.target.value)}
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3"
                          onClick={() => setShowApiKeys(!showApiKeys)}
                        >
                          {showApiKeys ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="crm-base-url">Base URL</Label>
                      <Input
                        id="crm-base-url"
                        placeholder="https://api.salesforce.com"
                        value={config.crm.baseUrl}
                        onChange={(e) => updateConfig('crm', 'baseUrl', e.target.value)}
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Database Configuration */}
          <TabsContent value="database" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Database Integration
                </CardTitle>
                <CardDescription>
                  Connect your database to store and retrieve data from conversations.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="database-enabled">Enable Database Integration</Label>
                  <Switch
                    id="database-enabled"
                    checked={config.database.enabled}
                    onCheckedChange={(checked) => updateConfig('database', 'enabled', checked)}
                  />
                </div>

                {config.database.enabled && (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="database-type">Database Type</Label>
                      <Select
                        value={config.database.type}
                        onValueChange={(value) => updateConfig('database', 'type', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="supabase">Supabase</SelectItem>
                          <SelectItem value="firebase">Firebase</SelectItem>
                          <SelectItem value="mongodb">MongoDB</SelectItem>
                          <SelectItem value="postgresql">PostgreSQL</SelectItem>
                          <SelectItem value="custom">Custom Database</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="database-connection">Connection String</Label>
                      <div className="relative">
                        <Input
                          id="database-connection"
                          type={showApiKeys ? 'text' : 'password'}
                          placeholder="Enter connection string"
                          value={config.database.connectionString}
                          onChange={(e) => updateConfig('database', 'connectionString', e.target.value)}
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3"
                          onClick={() => setShowApiKeys(!showApiKeys)}
                        >
                          {showApiKeys ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Table Names</Label>
                      <div className="space-y-2">
                        <div>
                          <Label htmlFor="appointments-table">Appointments Table</Label>
                          <Input
                            id="appointments-table"
                            placeholder="appointments"
                            value={config.database.tables.appointments}
                            onChange={(e) => updateNestedConfig('database', 'tables', 'appointments', e.target.value)}
                          />
                        </div>
                        <div>
                          <Label htmlFor="contacts-table">Contacts Table</Label>
                          <Input
                            id="contacts-table"
                            placeholder="contacts"
                            value={config.database.tables.contacts}
                            onChange={(e) => updateNestedConfig('database', 'tables', 'contacts', e.target.value)}
                          />
                        </div>
                        <div>
                          <Label htmlFor="interactions-table">Interactions Table</Label>
                          <Input
                            id="interactions-table"
                            placeholder="interactions"
                            value={config.database.tables.interactions}
                            onChange={(e) => updateNestedConfig('database', 'tables', 'interactions', e.target.value)}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
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

export default AssistantConfiguration;
