import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
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
  EyeOff,
  Building,
  DollarSign,
  BarChart3,
  FileText,
  Users,
  Webhook
} from 'lucide-react';

interface IntegrationConfig {
  // CRM Integrations
  crm?: {
    enabled: boolean;
    provider: 'pipedrive' | 'freshsales' | 'zoho' | 'hubspot' | 'salesforce' | 'custom';
    apiKey?: string;
    baseUrl?: string;
    customFields?: Record<string, string>;
  };
  
  // Communication Integrations
  email?: {
    enabled: boolean;
    provider: 'gmail' | 'outlook' | 'sendgrid' | 'custom';
    apiKey?: string;
    fromAddress?: string;
    templates?: {
      welcome?: string;
      followUp?: string;
      reminder?: string;
    };
  };
  
  sms?: {
    enabled: boolean;
    provider: 'twilio' | 'vonage' | 'custom';
    apiKey?: string;
    phoneNumber?: string;
  };
  
  whatsapp?: {
    enabled: boolean;
    provider: 'twilio' | 'whatsapp_business' | 'custom';
    apiKey?: string;
    phoneNumber?: string;
    webhookUrl?: string;
  };
  
  // Calendar & Scheduling
  calendar?: {
    enabled: boolean;
    provider: 'google_workspace' | 'microsoft_365' | 'calendly' | 'custom';
    apiKey?: string;
    calendarId?: string;
    timezone?: string;
  };
  
  // Data & Storage
  sheets?: {
    enabled: boolean;
    provider: 'google_drive' | 'microsoft_365' | 'notion' | 'custom';
    apiKey?: string;
    spreadsheetId?: string;
    sheetName?: string;
  };
  
  database?: {
    enabled: boolean;
    provider: 'mongodb' | 'mysql' | 'postgresql' | 'custom';
    connectionString?: string;
    tableName?: string;
  };
  
  // Payment Processing
  payments?: {
    enabled: boolean;
    provider: 'paystack' | 'flutterwave' | 'stripe' | 'custom';
    publicKey?: string;
    secretKey?: string;
    webhookSecret?: string;
  };
  
  // Analytics & Reporting
  analytics?: {
    enabled: boolean;
    provider: 'google_analytics' | 'mixpanel' | 'custom';
    trackingId?: string;
    apiKey?: string;
  };
  
  // Workflow Automation
  automation?: {
    enabled: boolean;
    provider: 'zapier' | 'n8n' | 'make' | 'custom';
    webhookUrl?: string;
    apiKey?: string;
  };
  
  // Support & Ticketing
  support?: {
    enabled: boolean;
    provider: 'freshdesk' | 'zendesk' | 'intercom' | 'custom';
    apiKey?: string;
    domain?: string;
  };
}

const INTEGRATION_CATEGORIES = [
  {
    id: 'crm',
    name: 'CRM & Sales',
    icon: Users,
    description: 'Connect to your CRM for lead management and sales tracking',
    integrations: [
      { id: 'pipedrive', name: 'Pipedrive', description: 'Sales pipeline management' },
      { id: 'freshsales', name: 'Freshsales', description: 'CRM and sales automation' },
      { id: 'zoho', name: 'Zoho CRM', description: 'Customer relationship management' },
      { id: 'hubspot', name: 'HubSpot', description: 'Inbound marketing and sales' },
      { id: 'salesforce', name: 'Salesforce', description: 'Enterprise CRM platform' }
    ]
  },
  {
    id: 'communication',
    name: 'Communication',
    icon: MessageSquare,
    description: 'Email, SMS, and messaging integrations',
    integrations: [
      { id: 'email', name: 'Email', description: 'Send automated emails' },
      { id: 'sms', name: 'SMS', description: 'Text message notifications' },
      { id: 'whatsapp', name: 'WhatsApp', description: 'WhatsApp Business messaging' },
      { id: 'telegram', name: 'Telegram', description: 'Telegram bot integration' }
    ]
  },
  {
    id: 'calendar',
    name: 'Calendar & Scheduling',
    icon: Calendar,
    description: 'Appointment booking and calendar management',
    integrations: [
      { id: 'google_workspace', name: 'Google Calendar', description: 'Google Workspace integration' },
      { id: 'microsoft_365', name: 'Outlook Calendar', description: 'Microsoft 365 integration' },
      { id: 'calendly', name: 'Calendly', description: 'Scheduling automation' }
    ]
  },
  {
    id: 'data',
    name: 'Data & Storage',
    icon: Database,
    description: 'Store and manage campaign data',
    integrations: [
      { id: 'sheets', name: 'Spreadsheets', description: 'Google Sheets, Excel integration' },
      { id: 'database', name: 'Databases', description: 'Direct database connections' },
      { id: 'notion', name: 'Notion', description: 'Workspace and documentation' }
    ]
  },
  {
    id: 'payments',
    name: 'Payments',
    icon: DollarSign,
    description: 'Payment processing and billing',
    integrations: [
      { id: 'paystack', name: 'Paystack', description: 'African payment processing' },
      { id: 'flutterwave', name: 'Flutterwave', description: 'Pan-African payments' },
      { id: 'stripe', name: 'Stripe', description: 'Global payment processing' }
    ]
  },
  {
    id: 'analytics',
    name: 'Analytics',
    icon: BarChart3,
    description: 'Track performance and generate insights',
    integrations: [
      { id: 'google_analytics', name: 'Google Analytics', description: 'Web analytics' },
      { id: 'mixpanel', name: 'Mixpanel', description: 'Product analytics' },
      { id: 'grafana', name: 'Grafana', description: 'Data visualization' }
    ]
  },
  {
    id: 'automation',
    name: 'Automation',
    icon: Zap,
    description: 'Workflow automation and webhooks',
    integrations: [
      { id: 'zapier', name: 'Zapier', description: 'App automation platform' },
      { id: 'n8n', name: 'n8n', description: 'Open-source automation' },
      { id: 'make', name: 'Make (Integromat)', description: 'Visual automation' }
    ]
  },
  {
    id: 'support',
    name: 'Support & Ticketing',
    icon: Shield,
    description: 'Customer support and help desk',
    integrations: [
      { id: 'freshdesk', name: 'Freshdesk', description: 'Help desk software' },
      { id: 'zendesk', name: 'Zendesk', description: 'Customer service platform' },
      { id: 'intercom', name: 'Intercom', description: 'Customer messaging' }
    ]
  }
];

interface CampaignIntegrationConfigProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (config: IntegrationConfig) => void;
  initialConfig?: IntegrationConfig;
  recommendedIntegrations?: string[];
}

const CampaignIntegrationConfig: React.FC<CampaignIntegrationConfigProps> = ({
  isOpen,
  onClose,
  onSave,
  initialConfig = {},
  recommendedIntegrations = []
}) => {
  const { toast } = useToast();
  const [config, setConfig] = useState<IntegrationConfig>(initialConfig);
  const [activeTab, setActiveTab] = useState('crm');
  const [testingIntegration, setTestingIntegration] = useState<string | null>(null);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setConfig(initialConfig);
  }, [initialConfig]);

  const updateConfig = (category: string, field: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [category]: {
        ...prev[category as keyof IntegrationConfig],
        [field]: value
      }
    }));
  };

  const toggleIntegration = (category: string, enabled: boolean) => {
    updateConfig(category, 'enabled', enabled);
  };

  const testIntegration = async (category: string) => {
    setTestingIntegration(category);
    
    try {
      // Mock API call to test integration
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast({
        title: "Integration Test Successful",
        description: `${category} integration is working correctly.`,
      });
    } catch (error) {
      toast({
        title: "Integration Test Failed",
        description: "Please check your configuration and try again.",
        variant: "destructive"
      });
    } finally {
      setTestingIntegration(null);
    }
  };

  const toggleSecretVisibility = (key: string) => {
    setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = () => {
    onSave(config);
    toast({
      title: "Integration Configuration Saved",
      description: "Your campaign integrations have been configured successfully.",
    });
    onClose();
  };

  const renderIntegrationForm = (category: any) => {
    const categoryConfig = config[category.id as keyof IntegrationConfig] as any;
    
    if (!categoryConfig?.enabled) {
      return (
        <div className="text-center py-8 text-gray-600">
          <div className="mb-4">
            <category.icon className="h-12 w-12 mx-auto opacity-50" />
          </div>
          <p>Enable {category.name} integration to configure settings</p>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* CRM Configuration */}
        {category.id === 'crm' && (
          <>
            <div className="space-y-2">
              <Label>CRM Provider</Label>
              <Select 
                value={categoryConfig.provider || ''} 
                onValueChange={(value) => updateConfig('crm', 'provider', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select CRM provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pipedrive">Pipedrive</SelectItem>
                  <SelectItem value="freshsales">Freshsales</SelectItem>
                  <SelectItem value="zoho">Zoho CRM</SelectItem>
                  <SelectItem value="hubspot">HubSpot</SelectItem>
                  <SelectItem value="salesforce">Salesforce</SelectItem>
                  <SelectItem value="custom">Custom API</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>API Key</Label>
              <div className="relative">
                <Input
                  type={showSecrets.crmApiKey ? 'text' : 'password'}
                  value={categoryConfig.apiKey || ''}
                  onChange={(e) => updateConfig('crm', 'apiKey', e.target.value)}
                  placeholder="Enter your CRM API key"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8"
                  onClick={() => toggleSecretVisibility('crmApiKey')}
                >
                  {showSecrets.crmApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            {categoryConfig.provider === 'custom' && (
              <div className="space-y-2">
                <Label>Base URL</Label>
                <Input
                  value={categoryConfig.baseUrl || ''}
                  onChange={(e) => updateConfig('crm', 'baseUrl', e.target.value)}
                  placeholder="https://api.your-crm.com"
                />
              </div>
            )}
          </>
        )}

        {/* Email Configuration */}
        {category.id === 'communication' && config.email?.enabled && (
          <>
            <div className="space-y-2">
              <Label>Email Provider</Label>
              <Select 
                value={config.email.provider || ''} 
                onValueChange={(value) => updateConfig('email', 'provider', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select email provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gmail">Gmail</SelectItem>
                  <SelectItem value="outlook">Outlook</SelectItem>
                  <SelectItem value="sendgrid">SendGrid</SelectItem>
                  <SelectItem value="custom">Custom SMTP</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>API Key</Label>
              <div className="relative">
                <Input
                  type={showSecrets.emailApiKey ? 'text' : 'password'}
                  value={config.email.apiKey || ''}
                  onChange={(e) => updateConfig('email', 'apiKey', e.target.value)}
                  placeholder="Enter your email API key"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8"
                  onClick={() => toggleSecretVisibility('emailApiKey')}
                >
                  {showSecrets.emailApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label>From Email Address</Label>
              <Input
                type="email"
                value={config.email.fromAddress || ''}
                onChange={(e) => updateConfig('email', 'fromAddress', e.target.value)}
                placeholder="campaigns@yourcompany.com"
              />
            </div>
          </>
        )}

        {/* Calendar Configuration */}
        {category.id === 'calendar' && config.calendar?.enabled && (
          <>
            <div className="space-y-2">
              <Label>Calendar Provider</Label>
              <Select 
                value={config.calendar.provider || ''} 
                onValueChange={(value) => updateConfig('calendar', 'provider', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select calendar provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="google_workspace">Google Calendar</SelectItem>
                  <SelectItem value="microsoft_365">Outlook Calendar</SelectItem>
                  <SelectItem value="calendly">Calendly</SelectItem>
                  <SelectItem value="custom">Custom Calendar</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Calendar ID</Label>
              <Input
                value={config.calendar.calendarId || ''}
                onChange={(e) => updateConfig('calendar', 'calendarId', e.target.value)}
                placeholder="primary"
              />
            </div>

            <div className="space-y-2">
              <Label>Timezone</Label>
              <Select 
                value={config.calendar.timezone || ''} 
                onValueChange={(value) => updateConfig('calendar', 'timezone', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select timezone" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Africa/Lagos">Africa/Lagos (WAT)</SelectItem>
                  <SelectItem value="Africa/Accra">Africa/Accra (GMT)</SelectItem>
                  <SelectItem value="Africa/Cairo">Africa/Cairo (EET)</SelectItem>
                  <SelectItem value="UTC">UTC</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </>
        )}

        {/* Add test integration button */}
        <div className="pt-4 border-t">
          <Button
            onClick={() => testIntegration(category.id)}
            disabled={testingIntegration === category.id}
            className="gap-2"
            variant="outline"
          >
            {testingIntegration === category.id ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <TestTube className="h-4 w-4" />
            )}
            Test Integration
          </Button>
        </div>
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Configure Campaign Integrations
          </DialogTitle>
          <DialogDescription>
            Connect your campaign to external services for automation and data management.
            {recommendedIntegrations.length > 0 && (
              <span className="block mt-2 text-indigo-600">
                Recommended: {recommendedIntegrations.join(', ')}
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-[calc(90vh-250px)]">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
            {/* Integration Categories */}
            <div className="space-y-2 border-r pr-4">
              <TabsList className="grid w-full grid-cols-1 h-auto bg-transparent p-0">
                {INTEGRATION_CATEGORIES.map((category) => {
                  const Icon = category.icon;
                  const isEnabled = config[category.id as keyof IntegrationConfig]?.enabled;
                  const isRecommended = recommendedIntegrations.includes(category.id);
                  
                  return (
                    <TabsTrigger
                      key={category.id}
                      value={category.id}
                      className="w-full justify-start p-3 data-[state=active]:bg-indigo-600 data-[state=active]:text-primary-foreground"
                    >
                      <div className="flex items-center gap-3 w-full">
                        <Icon className="h-4 w-4" />
                        <div className="flex-1 text-left">
                          <div className="flex items-center gap-2">
                            {category.name}
                            {isEnabled && <CheckCircle className="h-3 w-3 text-green-500" />}
                            {isRecommended && <Badge variant="secondary" className="text-xs">Recommended</Badge>}
                          </div>
                        </div>
                      </div>
                    </TabsTrigger>
                  );
                })}
              </TabsList>
            </div>

            {/* Integration Configuration */}
            <div className="lg:col-span-3 overflow-auto">
              {INTEGRATION_CATEGORIES.map((category) => (
                <TabsContent key={category.id} value={category.id} className="mt-0 h-full">
                  <div className="space-y-6">
                    {/* Category Header */}
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-lg font-semibold flex items-center gap-2">
                            <category.icon className="h-5 w-5" />
                            {category.name}
                          </h3>
                          <p className="text-sm text-gray-600">{category.description}</p>
                        </div>
                        <Switch
                          checked={config[category.id as keyof IntegrationConfig]?.enabled || false}
                          onCheckedChange={(enabled) => toggleIntegration(category.id, enabled)}
                        />
                      </div>
                    </div>

                    {/* Configuration Form */}
                    <Card>
                      <CardContent className="p-6">
                        {renderIntegrationForm(category)}
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>
              ))}
            </div>
          </div>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Configuration
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CampaignIntegrationConfig;