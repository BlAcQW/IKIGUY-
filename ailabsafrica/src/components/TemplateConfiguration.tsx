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
  EyeOff
} from 'lucide-react';
import { VoiceTemplate } from './VoiceAgentTemplates';

interface TemplateConfigurationProps {
  template: VoiceTemplate;
  onConfigurationComplete: (configuredTemplate: VoiceTemplate) => void;
  onClose: () => void;
}

const TemplateConfiguration: React.FC<TemplateConfigurationProps> = ({
  template,
  onConfigurationComplete,
  onClose
}) => {
  const { toast } = useToast();
  const [config, setConfig] = useState({
    calendar: {
      type: 'google' as const,
      calendarId: '',
      apiKey: ''
    },
    email: {
      provider: 'gmail' as const,
      emailAddress: '',
      apiKey: '',
      templates: {
        confirmation: '',
        reminder: '',
        cancellation: ''
      }
    },
    whatsapp: {
      enabled: false,
      phoneNumber: '',
      apiKey: '',
      provider: 'twilio' as const
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
          ...(prev[section as keyof typeof prev] as any)[subsection],
          [field]: value
        }
      }
    }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      // Validate required fields based on enabled integrations
      const errors: string[] = [];

      if (config.calendar.type && !config.calendar.calendarId) {
        errors.push('Calendar ID is required for calendar integration');
      }

      if (config.email.provider && !config.email.emailAddress) {
        errors.push('Email address is required for email integration');
      }

      if (config.whatsapp.enabled && !config.whatsapp.phoneNumber) {
        errors.push('WhatsApp phone number is required');
      }

      if (config.sheets.enabled && !config.sheets.spreadsheetId) {
        errors.push('Google Sheets ID is required');
      }

      if (config.crm.enabled && !config.crm.apiKey) {
        errors.push('CRM API key is required');
      }

      if (config.database.enabled && !config.database.connectionString) {
        errors.push('Database connection string is required');
      }

      if (errors.length > 0) {
        toast({
          title: "Configuration Errors",
          description: errors.join(', '),
          variant: "destructive"
        });
        return;
      }

      // Create the configured template
      const configuredTemplate: VoiceTemplate = {
        ...template,
        integrations: config
      };

      // Here you would typically save the configuration to your backend
      // For now, we'll just pass it back to the parent component
      onConfigurationComplete(configuredTemplate);

      toast({
        title: "Configuration Complete",
        description: `${template.name} has been configured with your integration settings.`,
      });

    } catch (error) {
      console.error('Configuration error:', error);
      toast({
        title: "Configuration Error",
        description: "Failed to save configuration. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getIntegrationStatus = () => {
    const enabled = [];
    if (config.calendar.type) enabled.push('Calendar');
    if (config.email.provider) enabled.push('Email');
    if (config.whatsapp.enabled) enabled.push('WhatsApp');
    if (config.sheets.enabled) enabled.push('Google Sheets');
    if (config.crm.enabled) enabled.push('CRM');
    if (config.database.enabled) enabled.push('Database');
    return enabled;
  };

  const enabledIntegrations = getIntegrationStatus();

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Configure {template.name}
          </DialogTitle>
          <DialogDescription>
            Set up integrations and automation settings for your {template.name.toLowerCase()}.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Integration Status */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Integration Status</CardTitle>
              <CardDescription>
                Configure the integrations you want to enable for this assistant
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {enabledIntegrations.length > 0 ? (
                  enabledIntegrations.map((integration) => (
                    <Badge key={integration} variant="default" className="flex items-center gap-1">
                      <CheckCircle className="h-3 w-3" />
                      {integration}
                    </Badge>
                  ))
                ) : (
                  <p className="text-muted-foreground">No integrations configured yet</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Configuration Tabs */}
          <Tabs defaultValue="calendar" className="w-full">
            <TabsList className="grid w-full grid-cols-6">
              <TabsTrigger value="calendar" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Calendar
              </TabsTrigger>
              <TabsTrigger value="email" className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                Email
              </TabsTrigger>
              <TabsTrigger value="whatsapp" className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                WhatsApp
              </TabsTrigger>
              <TabsTrigger value="sheets" className="flex items-center gap-2">
                <FileSpreadsheet className="h-4 w-4" />
                Sheets
              </TabsTrigger>
              <TabsTrigger value="crm" className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                CRM
              </TabsTrigger>
              <TabsTrigger value="database" className="flex items-center gap-2">
                <Database className="h-4 w-4" />
                Database
              </TabsTrigger>
            </TabsList>

            {/* Calendar Configuration */}
            <TabsContent value="calendar" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Calendar Integration</CardTitle>
                  <CardDescription>
                    Connect your calendar to automatically schedule and manage appointments
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
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

                  <div className="space-y-2">
                    <Label htmlFor="calendar-id">Calendar ID</Label>
                    <Input
                      id="calendar-id"
                      placeholder="Enter your calendar ID"
                      value={config.calendar.calendarId}
                      onChange={(e) => updateConfig('calendar', 'calendarId', e.target.value)}
                    />
                    <p className="text-sm text-muted-foreground">
                      For Google Calendar: your-calendar-id@group.calendar.google.com
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="calendar-api-key">API Key (Optional)</Label>
                    <div className="relative">
                      <Input
                        id="calendar-api-key"
                        type={showApiKeys ? "text" : "password"}
                        placeholder="Enter API key if required"
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
                </CardContent>
              </Card>
            </TabsContent>

            {/* Email Configuration */}
            <TabsContent value="email" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Email Integration</CardTitle>
                  <CardDescription>
                    Set up email notifications and confirmations
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
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

                  <div className="space-y-2">
                    <Label htmlFor="email-address">Email Address</Label>
                    <Input
                      id="email-address"
                      type="email"
                      placeholder="your-email@example.com"
                      value={config.email.emailAddress}
                      onChange={(e) => updateConfig('email', 'emailAddress', e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email-api-key">API Key</Label>
                    <div className="relative">
                      <Input
                        id="email-api-key"
                        type={showApiKeys ? "text" : "password"}
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

                  {/* Email Templates */}
                  <div className="space-y-4">
                    <h4 className="font-semibold">Email Templates</h4>
                    
                    <div className="space-y-2">
                      <Label htmlFor="confirmation-template">Confirmation Email Template</Label>
                      <Textarea
                        id="confirmation-template"
                        placeholder="Hi {name}, your appointment on {date} at {time} has been confirmed..."
                        value={config.email.templates.confirmation}
                        onChange={(e) => updateNestedConfig('email', 'templates', 'confirmation', e.target.value)}
                        rows={3}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="reminder-template">Reminder Email Template</Label>
                      <Textarea
                        id="reminder-template"
                        placeholder="Hi {name}, this is a reminder for your appointment tomorrow..."
                        value={config.email.templates.reminder}
                        onChange={(e) => updateNestedConfig('email', 'templates', 'reminder', e.target.value)}
                        rows={3}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* WhatsApp Configuration */}
            <TabsContent value="whatsapp" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>WhatsApp Integration</CardTitle>
                  <CardDescription>
                    Enable WhatsApp messaging for notifications and chat support
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="whatsapp-enabled"
                      checked={config.whatsapp.enabled}
                      onCheckedChange={(checked) => updateConfig('whatsapp', 'enabled', checked)}
                    />
                    <Label htmlFor="whatsapp-enabled">Enable WhatsApp Integration</Label>
                  </div>

                  {config.whatsapp.enabled && (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="whatsapp-provider">WhatsApp Provider</Label>
                        <Select 
                          value={config.whatsapp.provider} 
                          onValueChange={(value) => updateConfig('whatsapp', 'provider', value)}
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

                      <div className="space-y-2">
                        <Label htmlFor="whatsapp-number">WhatsApp Phone Number</Label>
                        <Input
                          id="whatsapp-number"
                          placeholder="+1234567890"
                          value={config.whatsapp.phoneNumber}
                          onChange={(e) => updateConfig('whatsapp', 'phoneNumber', e.target.value)}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="whatsapp-api-key">API Key</Label>
                        <div className="relative">
                          <Input
                            id="whatsapp-api-key"
                            type={showApiKeys ? "text" : "password"}
                            placeholder="Enter API key"
                            value={config.whatsapp.apiKey}
                            onChange={(e) => updateConfig('whatsapp', 'apiKey', e.target.value)}
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
                    </>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Google Sheets Configuration */}
            <TabsContent value="sheets" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Google Sheets Integration</CardTitle>
                  <CardDescription>
                    Automatically save data to Google Sheets for tracking and analytics
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="sheets-enabled"
                      checked={config.sheets.enabled}
                      onCheckedChange={(checked) => updateConfig('sheets', 'enabled', checked)}
                    />
                    <Label htmlFor="sheets-enabled">Enable Google Sheets Integration</Label>
                  </div>

                  {config.sheets.enabled && (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="spreadsheet-id">Spreadsheet ID</Label>
                        <Input
                          id="spreadsheet-id"
                          placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                          value={config.sheets.spreadsheetId}
                          onChange={(e) => updateConfig('sheets', 'spreadsheetId', e.target.value)}
                        />
                        <p className="text-sm text-muted-foreground">
                          Found in the URL: https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="sheets-api-key">Google API Key</Label>
                        <div className="relative">
                          <Input
                            id="sheets-api-key"
                            type={showApiKeys ? "text" : "password"}
                            placeholder="Enter Google API key"
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

                      <div className="space-y-4">
                        <h4 className="font-semibold">Sheet Names</h4>
                        
                        <div className="space-y-2">
                          <Label htmlFor="appointments-sheet">Appointments Sheet</Label>
                          <Input
                            id="appointments-sheet"
                            placeholder="Appointments"
                            value={config.sheets.sheets.appointments}
                            onChange={(e) => updateNestedConfig('sheets', 'sheets', 'appointments', e.target.value)}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="contacts-sheet">Contacts Sheet</Label>
                          <Input
                            id="contacts-sheet"
                            placeholder="Contacts"
                            value={config.sheets.sheets.contacts}
                            onChange={(e) => updateNestedConfig('sheets', 'sheets', 'contacts', e.target.value)}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="analytics-sheet">Analytics Sheet</Label>
                          <Input
                            id="analytics-sheet"
                            placeholder="Analytics"
                            value={config.sheets.sheets.analytics}
                            onChange={(e) => updateNestedConfig('sheets', 'sheets', 'analytics', e.target.value)}
                          />
                        </div>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* CRM Configuration */}
            <TabsContent value="crm" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>CRM Integration</CardTitle>
                  <CardDescription>
                    Connect with your CRM system to manage leads and customer data
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="crm-enabled"
                      checked={config.crm.enabled}
                      onCheckedChange={(checked) => updateConfig('crm', 'enabled', checked)}
                    />
                    <Label htmlFor="crm-enabled">Enable CRM Integration</Label>
                  </div>

                  {config.crm.enabled && (
                    <>
                      <div className="space-y-2">
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

                      <div className="space-y-2">
                        <Label htmlFor="crm-api-key">API Key</Label>
                        <div className="relative">
                          <Input
                            id="crm-api-key"
                            type={showApiKeys ? "text" : "password"}
                            placeholder="Enter CRM API key"
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

                      <div className="space-y-2">
                        <Label htmlFor="crm-base-url">Base URL (Optional)</Label>
                        <Input
                          id="crm-base-url"
                          placeholder="https://your-instance.salesforce.com"
                          value={config.crm.baseUrl}
                          onChange={(e) => updateConfig('crm', 'baseUrl', e.target.value)}
                        />
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Database Configuration */}
            <TabsContent value="database" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Database Integration</CardTitle>
                  <CardDescription>
                    Store data in your own database for complete control
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="database-enabled"
                      checked={config.database.enabled}
                      onCheckedChange={(checked) => updateConfig('database', 'enabled', checked)}
                    />
                    <Label htmlFor="database-enabled">Enable Database Integration</Label>
                  </div>

                  {config.database.enabled && (
                    <>
                      <div className="space-y-2">
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

                      <div className="space-y-2">
                        <Label htmlFor="database-connection">Connection String</Label>
                        <div className="relative">
                          <Input
                            id="database-connection"
                            type={showApiKeys ? "text" : "password"}
                            placeholder="postgresql://user:password@host:port/database"
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

                      <div className="space-y-4">
                        <h4 className="font-semibold">Table Names</h4>
                        
                        <div className="space-y-2">
                          <Label htmlFor="appointments-table">Appointments Table</Label>
                          <Input
                            id="appointments-table"
                            placeholder="appointments"
                            value={config.database.tables.appointments}
                            onChange={(e) => updateNestedConfig('database', 'tables', 'appointments', e.target.value)}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="contacts-table">Contacts Table</Label>
                          <Input
                            id="contacts-table"
                            placeholder="contacts"
                            value={config.database.tables.contacts}
                            onChange={(e) => updateNestedConfig('database', 'tables', 'contacts', e.target.value)}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="interactions-table">Interactions Table</Label>
                          <Input
                            id="interactions-table"
                            placeholder="interactions"
                            value={config.database.tables.interactions}
                            onChange={(e) => updateNestedConfig('database', 'tables', 'interactions', e.target.value)}
                          />
                        </div>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit} 
              disabled={isSubmitting}
              className="flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                  Configuring...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4" />
                  Complete Configuration
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TemplateConfiguration;







