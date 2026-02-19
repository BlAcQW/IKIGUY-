import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import {
  ArrowLeft,
  Save,
  Play,
  Settings,
  MessageSquare,
  Mail,
  Phone,
  Calendar,
  Database,
  Globe,
  Key,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  ExternalLink,
  Plus,
  Loader2,
  Mic
} from 'lucide-react';
import {
  automationOrchestrationService,
  type AutomationTemplate
} from '@/services/AutomationOrchestrationService';
import VAPIAgentGenerator from '@/services/VAPIAgentGenerator';
import { vapiIntegrationService } from '@/services/vapiIntegrationService';
import UnifiedAutomationDashboard from '@/components/analytics/UnifiedAutomationDashboard';
// AutomationDeploymentService deprecated - using AutomationOrchestrationService

interface IntegrationStepConfig {
  categoryId: string;
  categoryName: string;
  description: string;
  icon: React.ReactNode;
  required: boolean;
  selectedProvider?: string;
  providerConfig?: Record<string, any>;
  isConfigured: boolean;
}

interface SavedIntegration {
  id: string;
  name: string;
  apiKey: string;
  isConfigured: boolean;
  category: string;
}

// Icon mapping for integration categories
const getCategoryIcon = (categoryId: string): React.ReactNode => {
  const icons = {
    messaging: <MessageSquare className="h-4 w-4" />,
    email: <Mail className="h-4 w-4" />,
    calendar: <Calendar className="h-4 w-4" />,
    crm: <Database className="h-4 w-4" />,
    payment: <Globe className="h-4 w-4" />,
    support: <Phone className="h-4 w-4" />,
    storage: <Database className="h-4 w-4" />,
    analytics: <Globe className="h-4 w-4" />,
    automation: <Zap className="h-4 w-4" />
  };
  return icons[categoryId as keyof typeof icons] || <Settings className="h-4 w-4" />;
};

const AutomationConfiguration: React.FC = () => {
  const { templateId } = useParams<{ templateId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [activeTab, setActiveTab] = useState('overview');
  const [integrationConfigs, setIntegrationConfigs] = useState<IntegrationStepConfig[]>([]);
  const [savedIntegrations, setSavedIntegrations] = useState<SavedIntegration[]>([]);
  const [automationName, setAutomationName] = useState('');
  const [automationDescription, setAutomationDescription] = useState('');
  const [autoStart, setAutoStart] = useState(true);
  const [notifications, setNotifications] = useState(true);

  // VAPI Agent Configuration
  const [enableVoiceAgent, setEnableVoiceAgent] = useState(false);
  const [voiceAgentConfig, setVoiceAgentConfig] = useState({
    companyName: '',
    supportEmail: '',
    supportPhone: '',
    customPrompt: ''
  });
  const [isDeploying, setIsDeploying] = useState(false);
  const [deploymentProgress, setDeploymentProgress] = useState({
    automation: false,
    voiceAgent: false,
    webhooks: false
  });

  // State for template data
  const [template, setTemplate] = useState<AutomationTemplate | null>(null);
  const [templateLoading, setTemplateLoading] = useState(true);
  const [templateError, setTemplateError] = useState<string | null>(null);

  // Load template from API
  useEffect(() => {
    const loadTemplate = async () => {
      if (!templateId) {
        setTemplateError('No template ID provided');
        setTemplateLoading(false);
        return;
      }

      try {
        setTemplateLoading(true);
        setTemplateError(null);

        const loadedTemplate = await automationOrchestrationService.getTemplate(templateId);
        setTemplate(loadedTemplate);
      } catch (error) {
        console.error('Error loading template:', error);
        setTemplateError('Template not found');
      } finally {
        setTemplateLoading(false);
      }
    };

    loadTemplate();
  }, [templateId]);

  useEffect(() => {
    if (template) {
      setAutomationName(template.name);
      setAutomationDescription(template.description);
      
      // Initialize integration configs based on template's integration categories
      const configs = template.integrationCategories.map(categoryId => {
        return {
          categoryId,
          categoryName: categoryId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          description: `Configure ${categoryId.replace(/_/g, ' ')} integration for this automation`,
          icon: getCategoryIcon(categoryId),
          required: template.workflow.some(step =>
            step.type === 'integration' ||
            (step as any).integrationCategory === categoryId
          ),
          selectedProvider: undefined,
          providerConfig: {},
          isConfigured: false
        };
      });
      setIntegrationConfigs(configs);
    }
  }, [template]);

  useEffect(() => {
    // Load saved integrations from localStorage
    const saved = localStorage.getItem('kasaai_integrations');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSavedIntegrations(parsed.filter((i: SavedIntegration) => i.isConfigured));
      } catch (error) {
        console.error('Error loading saved integrations:', error);
      }
    }
  }, []);

  const handleProviderSelect = (categoryId: string, providerId: string) => {
    setIntegrationConfigs(prev => prev.map(config => 
      config.categoryId === categoryId 
        ? { ...config, selectedProvider: providerId, isConfigured: true }
        : config
    ));
  };

  const handleSaveConfiguration = async () => {
    try {
      // Save automation configuration
      const automationConfig = {
        templateId,
        name: automationName,
        description: automationDescription,
        autoStart,
        notifications,
        integrationConfigs,
        createdAt: new Date().toISOString()
      };

      // Save to localStorage (in production, this would be an API call)
      const savedAutomations = localStorage.getItem('kasaai_automations');
      const automations = savedAutomations ? JSON.parse(savedAutomations) : [];
      
      const existingIndex = automations.findIndex((a: any) => a.templateId === templateId);
      if (existingIndex >= 0) {
        automations[existingIndex] = automationConfig;
      } else {
        automations.push(automationConfig);
      }
      
      localStorage.setItem('kasaai_automations', JSON.stringify(automations));
      
      toast({
        title: "Configuration saved",
        description: "Your automation configuration has been saved successfully.",
      });
    } catch (error) {
      toast({
        title: "Error saving configuration",
        description: "Failed to save the automation configuration.",
        variant: "destructive"
      });
    }
  };

  const handleDeployAutomation = async () => {
    if (!template) return;

    setIsDeploying(true);
    setDeploymentProgress({ automation: false, voiceAgent: false, webhooks: false });

    try {
      // Use the comprehensive deployment service
      const deploymentConfig = {
        templateId: template.id,
        automationName,
        companyName: voiceAgentConfig.companyName || 'Premier Health Insurance',
        supportEmail: voiceAgentConfig.supportEmail || 'support@premierhealthinsurance.com',
        supportPhone: voiceAgentConfig.supportPhone || '1-800-PREMIER',
        customInstructions: voiceAgentConfig.customPrompt,
        integrations: {
          freshdesk: {
            domain: 'premierhealthinsurance', // Default domain
            apiKey: 'your-freshdesk-api-key' // This would come from integration settings
          },
          twilio: {
            accountSid: process.env.VITE_TWILIO_ACCOUNT_SID || '',
            authToken: process.env.VITE_TWILIO_AUTH_TOKEN || '',
            phoneNumber: process.env.VITE_TWILIO_PHONE_NUMBER || '+1234567890'
          }
        }
      };

      setDeploymentProgress(prev => ({ ...prev, automation: true }));

      // Deploy complete automation with VAPI agent, N8N workflow, and Freshdesk integration
      const configData = { template_id: templateId, automation_name: deploymentConfig.automationName, config: deploymentConfig };
      const result = await automationOrchestrationService.createConfiguration(configData);

      if (!result.success) {
        throw new Error(result.errors?.join(', ') || 'Deployment failed');
      }

      setDeploymentProgress(prev => ({ ...prev, voiceAgent: true, webhooks: true }));

      // Success notification
      toast({
        title: "🎉 Complete automation deployed successfully!",
        description: `${automationName} with VAPI agent (${result.vapiAgentId}) and Freshdesk integration is now live.`,
      });

      // Navigate to success page with deployment details
      navigate('/automations/success', {
        state: {
          templateId: template.id,
          automationName,
          voiceAgentEnabled: true,
          vapiAgentId: result.vapiAgentId,
          n8nWorkflowId: result.n8nWorkflowId,
          webhookUrl: result.webhookUrl,
          automationId: result.automationId
        }
      });

    } catch (error) {
      console.error('Deployment failed:', error);
      toast({
        title: "Deployment failed",
        description: error instanceof Error ? error.message : "Failed to deploy the automation.",
        variant: "destructive"
      });
    } finally {
      setIsDeploying(false);
    }
  };

  const deployVAPIAgent = async (): Promise<string> => {
    if (!template || !template.vapiConfig?.voiceAgentEnabled) {
      throw new Error('Template does not support voice agent deployment');
    }

    // Use template-based agent creation endpoint with auto-configured webhooks
    const response = await fetch('/api/vapi/agents/from-template', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}` // TODO: Use proper auth
      },
      body: JSON.stringify({
        template_id: template.id,
        tenant_id: 'default', // TODO: Get actual tenant ID from auth context
        automation_id: `automation_${template.id}_${Date.now()}`, // TODO: Use actual automation ID once saved
        customization: {
          companyName: voiceAgentConfig.companyName || 'Your Company',
          supportEmail: voiceAgentConfig.supportEmail || 'support@yourcompany.com',
          supportPhone: voiceAgentConfig.supportPhone || '1-800-SUPPORT',
          customPrompt: voiceAgentConfig.customInstructions
        }
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`Failed to create VAPI agent: ${errorData.detail || errorData.message || response.statusText}`);
    }

    const result = await response.json();

    // Log validation warnings if any
    if (result.validation_warnings?.length > 0) {
      console.warn('VAPI agent created with warnings:', result.validation_warnings);
    }

    return result.agent.id;
  };

  const configureWebhooks = async (vapiAgentId: string | null): Promise<void> => {
    // TODO: Implement webhook configuration
    // This would set up the n8n workflow webhooks and link them to the VAPI agent
    console.log('Configuring webhooks for agent:', vapiAgentId);

    // Simulate webhook setup
    await new Promise(resolve => setTimeout(resolve, 1000));
  };

  const getConfigurationStatus = (config: IntegrationStepConfig) => {
    if (config.isConfigured) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
    if (config.required) {
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
    return <Clock className="h-4 w-4 text-gray-400" />;
  };

  const getAvailableProviders = (categoryId: string) => {
    return savedIntegrations.filter(integration => {
      // Map integration categories to provider types
      const categoryMap: Record<string, string[]> = {
        messaging: ['messaging', 'sms', 'whatsapp', 'telegram'],
        email: ['email'],
        payment: ['payment'],
        crm: ['crm'],
        support: ['support'],
        storage: ['storage'],
        analytics: ['analytics'],
        automation: ['automation']
      };
      
      return categoryMap[categoryId]?.includes(integration.category) || false;
    });
  };

  const allRequiredConfigured = integrationConfigs
    .filter(config => config.required)
    .every(config => config.isConfigured);

  if (templateLoading) {
    return (
      <div className="flex min-h-screen bg-background">
        <DashboardSidebar />
        <div className="flex-1 overflow-auto">
          <div className="container mx-auto p-6">
            <div className="flex items-center justify-center min-h-96">
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Loading template configuration...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (templateError || !template) {
    return (
      <div className="flex min-h-screen bg-background">
        <DashboardSidebar />

        <div className="flex-1 overflow-auto">
          <div className="container mx-auto p-6">
            <Card>
          <CardContent className="text-center py-12">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Template not found</h3>
            <p className="text-gray-600 mb-4">
              {templateError || "The automation template you're looking for doesn't exist."}
            </p>
            <Button onClick={() => navigate('/automations')}>
              Back to Automations
            </Button>
          </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />
      
      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Settings className="h-6 w-6 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Configure: {template.name}</h1>
            <p className="text-gray-600">
              Set up your integrations and customize the automation workflow
            </p>
          </div>
        </div>
      </div>

      {/* Configuration Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 lg:grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          {template?.vapiConfig?.voiceAgentEnabled && (
            <TabsTrigger value="voice-agent" className="flex items-center gap-2">
              <Phone className="h-4 w-4" />
              <span className="hidden sm:inline">Voice Agent</span>
            </TabsTrigger>
          )}
          {integrationConfigs.map((config) => (
            <TabsTrigger key={config.categoryId} value={config.categoryId} className="relative">
              <div className="flex items-center gap-2">
                {config.icon}
                <span className="hidden sm:inline">{config.categoryName}</span>
                <div className="absolute -top-1 -right-1">
                  {getConfigurationStatus(config)}
                </div>
              </div>
            </TabsTrigger>
          ))}
          <TabsTrigger value="monitoring" className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            <span className="hidden sm:inline">Monitoring</span>
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>Automation Overview</CardTitle>
                  <CardDescription>
                    Configure the basic settings for your automation
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="automation-name">Automation Name</Label>
                    <Input
                      id="automation-name"
                      placeholder="Enter a name for this automation"
                      value={automationName}
                      onChange={(e) => setAutomationName(e.target.value)}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      placeholder="Describe what this automation does"
                      rows={3}
                      value={automationDescription}
                      onChange={(e) => setAutomationDescription(e.target.value)}
                    />
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Switch 
                      id="auto-start" 
                      checked={autoStart}
                      onCheckedChange={setAutoStart}
                    />
                    <Label htmlFor="auto-start">Start automation immediately after setup</Label>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Switch 
                      id="notifications" 
                      checked={notifications}
                      onCheckedChange={setNotifications}
                    />
                    <Label htmlFor="notifications">Send me notifications about automation status</Label>
                  </div>
                </CardContent>
              </Card>

              <Card className="mt-4">
                <CardHeader>
                  <CardTitle>Template Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Industry:</span>
                      <p className="capitalize text-gray-600">{template.industry.replace('_', ' ')}</p>
                    </div>
                    <div>
                      <span className="font-medium">Category:</span>
                      <p className="text-gray-600">{template.category || 'general'}</p>
                    </div>
                    <div>
                      <span className="font-medium">Complexity:</span>
                      <Badge variant={template.complexity === 'Simple' ? 'secondary' : template.complexity === 'Medium' ? 'default' : 'destructive'}>
                        {template.complexity}
                      </Badge>
                    </div>
                    <div>
                      <span className="font-medium">Estimated Setup:</span>
                      <p className="text-gray-600">{template.estimatedTime}</p>
                    </div>
                  </div>
                  
                  <div>
                    <span className="font-medium text-sm">Features:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {template.features.map((feature) => (
                        <Badge key={feature} variant="outline" className="text-xs">
                          {feature}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
            
            <div>
              <Card>
                <CardHeader>
                  <CardTitle>Integration Status</CardTitle>
                  <CardDescription>
                    Configure required integrations to proceed
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {integrationConfigs.map((config) => (
                      <div key={config.categoryId} className="flex items-center justify-between p-2 rounded-lg border">
                        <div className="flex items-center gap-2">
                          {config.icon}
                          <span className="text-sm font-medium">{config.categoryName}</span>
                          {config.required && (
                            <Badge variant="secondary" className="text-xs">Required</Badge>
                          )}
                        </div>
                        {getConfigurationStatus(config)}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card className="mt-4">
                <CardHeader>
                  <CardTitle>Deployment</CardTitle>
                  <CardDescription>
                    Ready to activate your automation?
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button
                    onClick={handleSaveConfiguration}
                    variant="outline"
                    className="w-full"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    Save Configuration
                  </Button>

                  {/* Deployment Progress */}
                  {isDeploying && (
                    <div className="space-y-3 p-3 bg-muted/50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm font-medium">Deploying automation...</span>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          {deploymentProgress.automation ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                          )}
                          <span>Automation configuration</span>
                        </div>

                        {template?.vapiConfig?.voiceAgentEnabled && voiceAgentConfig.enabled && (
                          <div className="flex items-center gap-2 text-sm">
                            {deploymentProgress.voiceAgent ? (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            ) : deploymentProgress.automation ? (
                              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                            ) : (
                              <Clock className="h-4 w-4 text-gray-600" />
                            )}
                            <span>Voice agent setup</span>
                          </div>
                        )}

                        <div className="flex items-center gap-2 text-sm">
                          {deploymentProgress.webhooks ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (deploymentProgress.automation && (!template?.vapiConfig?.voiceAgentEnabled || !voiceAgentConfig.enabled || deploymentProgress.voiceAgent)) ? (
                            <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                          ) : (
                            <Clock className="h-4 w-4 text-gray-600" />
                          )}
                          <span>Webhook configuration</span>
                        </div>
                      </div>
                    </div>
                  )}

                  <Button
                    onClick={handleDeployAutomation}
                    className="w-full"
                    disabled={!allRequiredConfigured || isDeploying}
                  >
                    {isDeploying ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4 mr-2" />
                    )}
                    {isDeploying ? 'Deploying...' : 'Deploy Automation'}
                  </Button>

                  {!allRequiredConfigured && !isDeploying && (
                    <p className="text-xs text-gray-600">
                      Complete required integrations to deploy
                    </p>
                  )}

                  {template?.vapiConfig?.voiceAgentEnabled && voiceAgentConfig.enabled && !isDeploying && (
                    <div className="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Mic className="h-4 w-4 text-blue-600" />
                        <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                          Voice Agent Included
                        </span>
                      </div>
                      <p className="text-xs text-blue-700 dark:text-blue-300">
                        This deployment will create a voice agent with the personality "{voiceAgentConfig.agentName}"
                        and configure automatic webhook integration.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Voice Agent Configuration Tab */}
        {template?.vapiConfig?.voiceAgentEnabled && (
          <TabsContent value="voice-agent" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Phone className="h-5 w-5" />
                  Voice Agent Configuration
                </CardTitle>
                <CardDescription>
                  Configure your AI voice agent for {template.name}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Enable Voice Agent */}
                <div className="flex items-center space-x-2">
                  <Switch
                    id="enable-voice-agent"
                    checked={enableVoiceAgent}
                    onCheckedChange={setEnableVoiceAgent}
                  />
                  <Label htmlFor="enable-voice-agent">
                    Enable voice agent for this automation
                  </Label>
                </div>

                {enableVoiceAgent && (
                  <div className="space-y-4 border-t pt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="company-name">Company Name</Label>
                        <Input
                          id="company-name"
                          placeholder="Your Company Name"
                          value={voiceAgentConfig.companyName}
                          onChange={(e) => setVoiceAgentConfig(prev => ({
                            ...prev,
                            companyName: e.target.value
                          }))}
                        />
                      </div>

                      <div>
                        <Label htmlFor="support-email">Support Email</Label>
                        <Input
                          id="support-email"
                          type="email"
                          placeholder="support@yourcompany.com"
                          value={voiceAgentConfig.supportEmail}
                          onChange={(e) => setVoiceAgentConfig(prev => ({
                            ...prev,
                            supportEmail: e.target.value
                          }))}
                        />
                      </div>

                      <div>
                        <Label htmlFor="support-phone">Support Phone</Label>
                        <Input
                          id="support-phone"
                          placeholder="1-800-SUPPORT"
                          value={voiceAgentConfig.supportPhone}
                          onChange={(e) => setVoiceAgentConfig(prev => ({
                            ...prev,
                            supportPhone: e.target.value
                          }))}
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="custom-prompt">Additional Instructions (Optional)</Label>
                      <Textarea
                        id="custom-prompt"
                        placeholder="Add any specific instructions for your voice agent..."
                        rows={3}
                        value={voiceAgentConfig.customPrompt}
                        onChange={(e) => setVoiceAgentConfig(prev => ({
                          ...prev,
                          customPrompt: e.target.value
                        }))}
                      />
                    </div>

                    {/* Voice Agent Preview */}
                    <div className="bg-muted p-4 rounded-lg">
                      <h4 className="font-medium mb-2">Voice Agent Preview</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <strong>Agent Role:</strong> {template.vapiConfig.agentPersonality.role}
                        </div>
                        <div>
                          <strong>Tone:</strong> {template.vapiConfig.agentPersonality.tone}
                        </div>
                        <div>
                          <strong>Voice:</strong> {template.vapiConfig.voiceSettings.voiceId}
                        </div>
                        <div>
                          <strong>Functions:</strong> {template.vapiConfig.customFunctions?.length || 0} available
                        </div>
                      </div>
                    </div>

                    {/* Supported Scenarios */}
                    <div>
                      <h4 className="font-medium mb-2">Supported Call Scenarios</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {template.vapiConfig.callScenarios.scenarios.map((scenario, index) => (
                          <div key={index} className="flex items-center gap-2 text-sm">
                            <CheckCircle className="h-4 w-4 text-green-500" />
                            {scenario}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Integration Configuration Tabs */}
        {integrationConfigs.map((config) => (
          <TabsContent key={config.categoryId} value={config.categoryId} className="mt-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {config.icon}
                      {config.categoryName}
                      {config.required && (
                        <Badge variant="destructive" className="text-xs">Required</Badge>
                      )}
                    </CardTitle>
                    <CardDescription>{config.description}</CardDescription>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {config.isConfigured && (
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Configured
                      </Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <Label>Available Providers</Label>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate('/integrations')}
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      Add Integration
                    </Button>
                  </div>
                  
                  {getAvailableProviders(config.categoryId).length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {getAvailableProviders(config.categoryId).map((provider) => (
                        <Card 
                          key={provider.id} 
                          className={`cursor-pointer border-2 transition-colors ${
                            config.selectedProvider === provider.id 
                              ? 'border-primary bg-primary/5' 
                              : 'border-border hover:border-primary/50'
                          }`}
                          onClick={() => handleProviderSelect(config.categoryId, provider.id)}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                              <CheckCircle className={`h-4 w-4 ${
                                config.selectedProvider === provider.id 
                                  ? 'text-primary' 
                                  : 'text-gray-600'
                              }`} />
                              <div>
                                <div className="font-medium">{provider.name}</div>
                                <div className="text-sm text-gray-600 capitalize">
                                  {provider.category}
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <Card className="border-dashed border-2">
                      <CardContent className="text-center py-8">
                        <AlertCircle className="h-8 w-8 text-gray-600 mx-auto mb-3" />
                        <h3 className="font-medium mb-2">No {config.categoryName} integrations configured</h3>
                        <p className="text-sm text-gray-600 mb-4">
                          You need to configure at least one {config.categoryName.toLowerCase()} integration to use this automation.
                        </p>
                        <Button
                          variant="outline"
                          onClick={() => navigate('/integrations')}
                        >
                          <ExternalLink className="h-4 w-4 mr-2" />
                          Configure Integrations
                        </Button>
                      </CardContent>
                    </Card>
                  )}
                </div>
                
                <div className="flex gap-3 pt-4 border-t">
                  <Button 
                    onClick={handleSaveConfiguration}
                    disabled={!config.isConfigured}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    Save Settings
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        ))}

        {/* Monitoring Tab */}
        <TabsContent value="monitoring" className="mt-6">
          <UnifiedAutomationDashboard timeRange="7d" />
        </TabsContent>
      </Tabs>
        </div>
      </div>
    </div>
  );
};

export default AutomationConfiguration;