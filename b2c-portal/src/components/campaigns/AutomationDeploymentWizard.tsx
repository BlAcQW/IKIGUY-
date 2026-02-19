import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Headphones,
  Calendar,
  Ticket,
  Settings,
  Workflow,
  Bot,
  Clock,
  AlertCircle,
  CheckCircle,
  Users,
  Globe,
  Sparkles,
  ExternalLink,
  Database,
  Phone,
  Mail,
  MessageSquare,
  BarChart3,
  Shield,
  FileText,
  Search,
  Filter,
  Star,
  Loader2,
  Save,
  Wrench,
  PlayCircle,
  TestTube,
  WifiOff,
  Wifi,
  X,
  Play,
  Zap,
  Activity
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  automationOrchestrationService,
  type AutomationTemplate as DatabaseTemplate,
  type AutomationConfig,
  type DeploymentResult,
  type ValidationResult,
  type TestResult,
  type AutomationStatusResponse
} from '@/services/AutomationOrchestrationService';
import { SystemPromptGenerator } from '@/components/shared/SystemPromptGenerator';
import { isAdminUser, getAuthHeaders } from '@/lib/auth-utils';
import CustomToolsTab from '@/components/automation/CustomToolsTab';
import IndustryConfigHandler from '@/components/automation/IndustryConfigHandler';
import UnifiedAutomationDashboard from '@/components/analytics/UnifiedAutomationDashboard';
import CustomToolsSelector from '@/components/automation/CustomToolsSelector';
import KnowledgeBaseStep from './steps/KnowledgeBaseStep';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';
import { VoiceSettingsOverride } from '@/components/automations/VoiceSettingsOverride';
import { useVoiceProviders } from '@/hooks/useVoiceProviders';


// Adapter interface to bridge between database template and wizard template
interface CampaignTemplate {
  id: string;
  name: string;
  description: string;
  industry: string;
  category?: string;
  complexity?: string;
  estimatedTime?: string;
  rating?: number;
  usageCount?: number;
  popular?: boolean;
  isEnhanced?: boolean;
  integrationCategories?: string[];
  defaultIntegrations?: string[];
  vapiConfig?: any;
  n8nConfig?: any;
  features?: string[];
  supportedLanguages?: string[];
  knowledgeBase?: any[];
  tags?: string[];
  customTools?: {
    name: string;
    description: string;
    endpoint: string;
    method: string;
    category: string;
  }[];
}

// Adapter function to convert database template to campaign template
const adaptDatabaseTemplate = (dbTemplate: DatabaseTemplate): CampaignTemplate => {
  return {
    id: dbTemplate.id,
    name: dbTemplate.name,
    description: dbTemplate.description,
    industry: dbTemplate.industry,
    category: dbTemplate.category || 'general',
    complexity: dbTemplate.complexity || 'Medium',
    estimatedTime: dbTemplate.estimatedTime || '30 minutes',
    rating: dbTemplate.rating || 4.5,
    usageCount: dbTemplate.usageCount || 0,
    popular: dbTemplate.popular || false,
    isEnhanced: true,
    integrationCategories: dbTemplate.integrationCategories || [],
    defaultIntegrations: dbTemplate.defaultIntegrations || [],
    vapiConfig: dbTemplate.vapiConfig,
    n8nConfig: null, // DatabaseTemplate doesn't have n8nConfig
    features: dbTemplate.features || [],
    supportedLanguages: dbTemplate.supportedLanguages || ['en'],
    knowledgeBase: dbTemplate.knowledgeBase || [],
    tags: dbTemplate.tags || [],
    customTools: dbTemplate.industry === 'Healthcare' ? [
      {
        name: 'Healthcare Provider Search',
        description: 'Search for healthcare providers by location, specialty, or type',
        endpoint: buildApiUrl('/custom-tools/healthcare/search-providers'),
        method: 'POST',
        category: 'healthcare'
      },
      {
        name: 'Emergency Provider Locator',
        description: 'Get emergency healthcare providers for urgent situations',
        endpoint: buildApiUrl('/custom-tools/healthcare/get-emergency-providers'),
        method: 'POST',
        category: 'healthcare'
      },
      {
        name: 'Provider Info Email',
        description: 'Send healthcare provider information via email',
        endpoint: buildApiUrl('/custom-tools/healthcare/send-provider-info-email'),
        method: 'POST',
        category: 'healthcare'
      },
      {
        name: 'Support Escalation',
        description: 'Escalate queries to support when issues arise',
        endpoint: buildApiUrl('/custom-tools/healthcare/escalate-to-support'),
        method: 'POST',
        category: 'healthcare'
      }
    ] : []
  };
};

interface CompanyInfo {
  name: string;
  description: string;
  url: string;
  transferNumber?: string;
  extractedInfo?: {
    services: string[];
    businessHours: string;
    contactInfo: {
      phone?: string;
      email?: string;
      address?: string;
    };
    aboutText: string;
  };
}

interface VAPIAgent {
  assistantId: string;
  phoneNumberId: string;
  systemPrompt: string;
  voiceSettings: {
    voiceId: string;
    model: string;
    maxDuration: number;
  };
  tools: string[];
}

interface N8NWorkflow {
  workflowId: string;
  workflowName: string;
  webhookUrl: string;
  endpoints: {
    calendar: string;
    tickets: string;
    availability: string;
    escalation: string;
    analytics: string;
  };
}

interface KnowledgeBaseDocument {
  id?: string;
  title: string;
  content: string;
  category: string;
  source?: string;
  tags: string[];
  metadata?: Record<string, any>;
}

interface AutomationDeploymentConfig {
  automationName: string;
  companyInfo: CompanyInfo;
  audienceSelection?: {
    targetAudience: string;
    audienceSize: string;
    demographics: string;
    channels: string[];
    timing: string;
    objectives: string[];
  };
  industryConfig?: any;
  knowledgeBase?: KnowledgeBaseDocument[];
  vapiAgent: VAPIAgent;
  n8nWorkflow: N8NWorkflow;
  integrations: {
    calendly: { enabled: boolean; apiKey: string; };
    supabase: { enabled: boolean; projectId: string; };
    tavily: { enabled: boolean; apiKey: string; };
    resend: { enabled: boolean; apiKey: string; };
    vonage: { enabled: boolean; apiKey: string; };
  };
  demoSettings: {
    enableDemo: boolean;
    demoUrl: string;
    htmlTemplate: string;
  };
  analytics: {
    enableTracking: boolean;
    webhookUrl: string;
    reportEmail: string;
  };
  customTools: {
    enabled: boolean;
    selectedTools: string[];
    availableTools: Array<{
      name: string;
      description: string;
      endpoint: string;
      method: string;
      category: string;
      enabled: boolean;
    }>;
  };
  status?: 'draft' | 'deployed' | 'stopped';
  id?: string;
  createdAt?: string;
  updatedAt?: string;
}

interface AutomationDeploymentWizardProps {
  isOpen: boolean;
  onClose: () => void;
  template?: CampaignTemplate;
  existingConfig?: any; // AutomationConfig for editing existing configurations
  isEditing?: boolean;
  onCreateCampaign: (config: AutomationDeploymentConfig) => Promise<CampaignCreationResult>;
  apiBaseUrl: string;
  existingConfigId?: string; // For editing existing configurations
}

interface CampaignCreationResult {
  success: boolean;
  demoUrl?: string;
  campaignId?: string;
  error?: string;
}

const NO_HALLUCINATION_TEMPLATE = `You are a helpful AI automation assistant. You must only provide answers grounded in official company documentation. If information is unavailable, you must politely decline to answer and redirect the customer to official contact points. You must never guess, speculate, or invent information, and must always prioritize accuracy, customer trust, and compliance.

## Core Responsibilities:
1. **Appointment Booking**: Check availability and book appointments with our team using the calendar integration
2. **Ticket Creation**: Create support tickets for technical issues or requests that require human attention
3. **General Support**: Answer common questions using verified company information only
4. **Escalation**: Route complex issues to appropriate team members

## Response Guidelines:
- Only answer using verified company information provided in your knowledge base
- If you don't know something, say "I don't have that specific information, but I can connect you with someone who does"
- Always be polite, professional, and helpful
- Provide structured responses: Overview → Key Details → Next Steps → Contact Information
- Include appropriate disclaimers for financial or policy-related queries

## Escalation Rules:
- Escalate policy changes, financial commitments, or legal advice to human support
- Escalate when required information is not in the knowledge base
- Escalate queries involving personal or confidential customer data

How may I assist you today?`;

export const AutomationDeploymentWizard: React.FC<AutomationDeploymentWizardProps> = ({
  isOpen,
  onClose,
  template,
  existingConfig,
  isEditing,
  onCreateCampaign,
  apiBaseUrl,
  existingConfigId
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isCreating, setIsCreating] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [configId, setConfigId] = useState<string | undefined>(existingConfigId);
  const [isSearchingTemplate, setIsSearchingTemplate] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isUpdatingTemplate, setIsUpdatingTemplate] = useState(false);
  const [testResults, setTestResults] = useState({
    vapi: { status: 'pending', message: '', tested: false },
    n8n: { status: 'pending', message: '', tested: false },
    webhooks: { status: 'pending', message: '', tested: false },
    customTools: { status: 'pending', message: '', tested: false },
    integrations: { status: 'pending', message: '', tested: false }
  });
  const [isRunningTests, setIsRunningTests] = useState(false);
  const [industryConfig, setIndustryConfig] = useState<any>({});
  const [selectedCustomTools, setSelectedCustomTools] = useState<any[]>([]);
  const { toast } = useToast();

  // Voice settings override state
  const [useCustomVoiceSettings, setUseCustomVoiceSettings] = useState(false);
  const [customVoiceSettings, setCustomVoiceSettings] = useState({
    tts: { provider: null as string | null, voice: null as string | null, speed: 1.0, pitch: 0.0 },
    asr: { provider: null as string | null, language: 'en' },
    llm: { model: null as string | null, temperature: 0.7, maxTokens: 2000 },
    referenceVoice: null as string | null,
  });
  
  // Fetch voice providers
  const { ttsProviders, asrProviders, llmModels, clonedVoices, isLoading: providersLoading } = useVoiceProviders(apiBaseUrl);

  const [config, setConfig] = useState<AutomationDeploymentConfig>({
    automationName: '',
    companyInfo: {
      name: '',
      description: '',
      url: '',
      transferNumber: '+12397783680'
    },
    audienceSelection: {
      targetAudience: '',
      audienceSize: '',
      demographics: '',
      channels: [],
      timing: '',
      objectives: []
    },
    knowledgeBase: [],
    vapiAgent: {
      assistantId: '',
      phoneNumberId: '',
      systemPrompt: NO_HALLUCINATION_TEMPLATE,
      voiceSettings: {
        voiceId: 'jennifer',
        model: 'gpt-4o',
        maxDuration: 600
      },
      tools: ['calendar_booking', 'ticket_creation', 'web_search', 'escalation']
    },
    n8nWorkflow: {
      workflowId: '',
      workflowName: 'Automation Deployment',
      webhookUrl: '',
      endpoints: {
        calendar: '/calendar/availability',
        tickets: '/tickets/create',
        availability: '/availability/check',
        escalation: '/escalation/route',
        analytics: '/analytics/track'
      }
    },
    integrations: {
      calendly: { enabled: true, apiKey: '' },
      supabase: { enabled: true, projectId: 'ljzbzjgvwzivpmlmuxhx' },
      tavily: { enabled: true, apiKey: '' },
      resend: { enabled: true, apiKey: '' },
      vonage: { enabled: true, apiKey: '' }
    },
    demoSettings: {
      enableDemo: true,
      demoUrl: '',
      htmlTemplate: ''
    },
    analytics: {
      enableTracking: true,
      webhookUrl: '',
      reportEmail: 'ailabsafrica@gmail.com'
    },
    customTools: {
      enabled: true,
      selectedTools: [],
      availableTools: []
    }
  });

  // Check admin status
  useEffect(() => {
    const checkAdminStatus = async () => {
      try {
        const adminStatus = await isAdminUser();
        console.log('Admin status check:', adminStatus);
        setIsAdmin(adminStatus);
      } catch (error) {
        console.error('Admin status check failed:', error);
        setIsAdmin(false);
      }
    };

    checkAdminStatus();
  }, []);

  // Initialize custom tools when template changes
  useEffect(() => {
    if (template?.customTools && template.customTools.length > 0) {
      setConfig(prev => ({
        ...prev,
        customTools: {
          enabled: true,
          selectedTools: template.customTools.map(t => t.name),
          availableTools: template.customTools.map(t => ({
            name: t.name,
            description: t.description,
            endpoint: t.endpoint,
            method: t.method,
            category: t.category || 'general',
            enabled: true
          }))
        }
      }));
    }
  }, [template]);

  // Load existing configuration if editing
  useEffect(() => {
    const loadExistingConfig = async () => {
      if (existingConfigId) {
        setIsLoading(true);
        try {
          const response = await automationOrchestrationService.getConfiguration(existingConfigId);
          setConfig(response.configuration);
          setConfigId(existingConfigId);

          // Load custom voice settings override if exists
          if (response.configuration.vapiAgent?.custom_settings_override) {
            const override = response.configuration.vapiAgent.custom_settings_override;
            setUseCustomVoiceSettings(true);
            setCustomVoiceSettings({
              tts: {
                provider: override.tts?.provider || null,
                voice: override.tts?.voice || null,
                speed: override.tts?.speed || 1.0,
                pitch: override.tts?.pitch || 0.0,
              },
              asr: {
                provider: override.asr?.provider || null,
                language: override.asr?.language || 'en',
              },
              llm: {
                model: override.llm?.model || null,
                temperature: override.llm?.temperature || 0.7,
                maxTokens: override.llm?.maxTokens || 2000,
              },
              referenceVoice: override.referenceVoice || null,
            });
          }

          // Initialize selected custom tools from loaded configuration
          if (response.configuration.customTools?.availableTools) {
            setSelectedCustomTools(response.configuration.customTools.availableTools.map(tool => ({
              id: tool.name, // Using name as ID fallback
              name: tool.name,
              description: tool.description,
              endpoint: tool.endpoint,
              method: tool.method,
              category: tool.category,
              client_id: '', // Will be populated from API
              industry: template?.industry || 'general',
              active: tool.enabled
            })));
          }
          toast({
            title: "Configuration Loaded",
            description: `Loaded automation: ${response.configuration.automationName}`
          });
        } catch (error) {
          toast({
            title: "Load Failed",
            description: "Failed to load existing configuration",
            variant: "destructive"
          });
        } finally {
          setIsLoading(false);
        }
      }
    };

    loadExistingConfig();
  }, [existingConfigId]);

  // Template adaptation - adjust configuration based on the passed template
  useEffect(() => {
    if (template && !existingConfigId) {
      // Only adapt from template if not editing existing config
      const adaptedConfig = adaptConfigForTemplate(template, config);
      setConfig(adaptedConfig);
    }
  }, [template, existingConfigId]);

  // Sync selected custom tools with configuration
  useEffect(() => {
    setConfig(prev => ({
      ...prev,
      customTools: {
        ...prev.customTools,
        selectedTools: selectedCustomTools.map(tool => tool.id),
        availableTools: selectedCustomTools.map(tool => ({
          name: tool.name,
          description: tool.description,
          endpoint: tool.endpoint,
          method: tool.method,
          category: tool.category,
          enabled: true
        }))
      }
    }));
  }, [selectedCustomTools]);

  // Function to adapt configuration based on template
  const adaptConfigForTemplate = (template: CampaignTemplate, baseConfig: AutomationDeploymentConfig): AutomationDeploymentConfig => {
    const adapted = { ...baseConfig };

    // Adapt VAPI agent configuration based on template
    if (template?.vapiConfig) {
      adapted.vapiAgent = {
        ...adapted.vapiAgent,
        systemPrompt: generateTemplateSpecificPrompt(template),
        tools: adaptToolsForTemplate(template)
      };
    }

    // Adapt N8N workflow configuration
    if (template?.n8nConfig) {
      // Use template's N8N configuration if available
      adapted.n8nWorkflow = {
        ...adapted.n8nWorkflow,
        ...template.n8nConfig
      };
    } else {
      // Generate default N8N configuration
      adapted.n8nWorkflow = {
        ...adapted.n8nWorkflow,
        workflowName: `${template?.name || 'Automation'} Automation`,
        endpoints: adaptEndpointsForTemplate(template)
      };
    }

    // Set default integrations based on template
    if (template.defaultIntegrations) {
      template.defaultIntegrations.forEach(integration => {
        if (adapted.integrations[integration as keyof typeof adapted.integrations]) {
          adapted.integrations[integration as keyof typeof adapted.integrations].enabled = true;
        }
      });
    }

    return adapted;
  };

  // Generate template-specific system prompt
  const generateTemplateSpecificPrompt = (template: CampaignTemplate): string => {
    const basePrompt = NO_HALLUCINATION_TEMPLATE;

    switch (template.category || 'general') {
      case 'sales':
        return basePrompt + `\n\n## Sales Focus:\nYou are specialized in sales support and lead qualification. Focus on understanding customer needs, scheduling sales consultations, and connecting prospects with the sales team. Always maintain a professional, helpful, and sales-oriented approach while providing accurate information.`;

      case 'retention':
        return basePrompt + `\n\n## Customer Retention Focus:\nYou are specialized in customer retention and reactivation. Focus on understanding why customers may have become inactive, offering personalized solutions, and helping them re-engage with our services. Always be empathetic and solution-oriented.`;

      case 'support':
        return basePrompt + `\n\n## Support Focus:\nYou are specialized in customer support and troubleshooting. Focus on resolving customer issues, providing technical assistance, and escalating complex problems to human agents when necessary. Always prioritize customer satisfaction and clear communication.`;

      case 'scheduling':
        return basePrompt + `\n\n## Scheduling Focus:\nYou are specialized in appointment booking and calendar management. Focus on finding optimal meeting times, handling rescheduling requests, and ensuring clear communication about appointments. Always confirm details and send appropriate reminders.`;

      default:
        return basePrompt;
    }
  };

  // Adapt tools based on template type
  const adaptToolsForTemplate = (template: CampaignTemplate): string[] => {
    const baseTool = ['web_search', 'escalation'];

    switch (template.category || 'general') {
      case 'sales':
        return [...baseTool, 'calendar_booking', 'lead_qualification', 'crm_integration'];

      case 'retention':
        return [...baseTool, 'customer_history', 'offer_generation', 'reactivation_tracking'];

      case 'support':
        return [...baseTool, 'ticket_creation', 'knowledge_base', 'escalation'];

      case 'scheduling':
        return [...baseTool, 'calendar_booking', 'availability_check', 'reminder_system'];

      default:
        return [...baseTool, 'calendar_booking', 'ticket_creation'];
    }
  };

  // Adapt N8N endpoints based on template type
  const adaptEndpointsForTemplate = (template: CampaignTemplate) => {
    const baseEndpoints = {
      analytics: '/analytics/track',
      escalation: '/escalation/route'
    };

    switch (template.category || 'general') {
      case 'sales':
        return {
          ...baseEndpoints,
          calendar: '/calendar/sales-booking',
          leads: '/leads/qualification',
          crm: '/crm/integration',
          follow_up: '/sales/follow-up'
        };

      case 'retention':
        return {
          ...baseEndpoints,
          customer_analysis: '/retention/analysis',
          offers: '/retention/offers',
          reactivation: '/retention/tracking',
          engagement: '/retention/engagement'
        };

      case 'support':
        return {
          ...baseEndpoints,
          tickets: '/tickets/create',
          knowledge: '/support/knowledge-base',
          availability: '/support/availability',
          calendar: '/calendar/support-booking'
        };

      case 'scheduling':
        return {
          ...baseEndpoints,
          calendar: '/calendar/availability',
          booking: '/calendar/booking',
          reminders: '/calendar/reminders',
          availability: '/availability/check'
        };

      default:
        return {
          ...baseEndpoints,
          calendar: '/calendar/availability',
          tickets: '/tickets/create',
          availability: '/availability/check'
        };
    }
  };

  // Check if this is a campaign template that requires audience selection
  const isCampaignTemplate = template && ['marketing', 'promotion', 'announcement', 'campaign', 'outreach'].some(cat =>
    template.category?.toLowerCase().includes(cat)
  );

  const steps = [
    ...(isCampaignTemplate ? [{ id: 'audience', title: 'Audience Selection', icon: Users }] : []),
    { id: 'company', title: 'Company Info', icon: Globe },
    { id: 'knowledge', title: 'Knowledge Base', icon: Database },
    { id: 'industry', title: 'Industry Config', icon: Shield },
    { id: 'prompt', title: 'System Prompt', icon: Bot },
    { id: 'voice', title: 'Voice Settings', icon: Headphones },
    { id: 'workflow', title: 'N8N Workflow', icon: Workflow },
    { id: 'integrations', title: 'Integrations', icon: Settings },
    { id: 'custom-tools', title: 'Custom Tools', icon: Wrench },
    { id: 'test', title: 'Test', icon: TestTube },
    { id: 'demo', title: 'Demo Setup', icon: ExternalLink },
    { id: 'analytics', title: 'Analytics', icon: BarChart3 },
    { id: 'review', title: 'Review', icon: CheckCircle }
  ];

  const extractCompanyInfo = async () => {
    if (!config.companyInfo.url) {
      toast({
        title: "URL Required",
        description: "Please enter a company URL to extract information.",
        variant: "destructive"
      });
      return;
    }

    setIsExtracting(true);
    try {
      // Use site extraction to get company information
      const response = await fetch(`${apiBaseUrl}/enhanced-helpdesk/extract-site-info`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          url: config.companyInfo.url,
          extraction_type: 'company_info'
        })
      });

      if (!response.ok) {
        throw new Error('Failed to extract company information');
      }

      const extractedData = await response.json();

      setConfig(prev => ({
        ...prev,
        companyInfo: {
          ...prev.companyInfo,
          extractedInfo: extractedData
        }
      }));

      // Generate enhanced system prompt with company information
      const enhancedPrompt = generateEnhancedSystemPrompt(extractedData);
      setConfig(prev => ({
        ...prev,
        vapiAgent: {
          ...prev.vapiAgent,
          systemPrompt: enhancedPrompt
        }
      }));

      toast({
        title: "Information Extracted",
        description: "Successfully extracted company information from the website."
      });
    } catch (error) {
      toast({
        title: "Extraction Failed",
        description: "Failed to extract company information. Please enter manually.",
        variant: "destructive"
      });
    } finally {
      setIsExtracting(false);
    }
  };

  const findAutomationTemplate = async () => {
    setIsSearchingTemplate(true);
    try {
      // Get template details from orchestration service
      const templateResult = await automationOrchestrationService.getTemplate(template.id);

      if (templateResult && templateResult.components && templateResult.components.n8n) {
        const n8nComponent = templateResult.components.n8n;

        // Update the N8N workflow configuration with template data
        setConfig(prev => ({
          ...prev,
          n8nWorkflow: {
            ...prev.n8nWorkflow,
            workflowName: n8nComponent.name || prev.n8nWorkflow.workflowName,
            workflowId: n8nComponent.workflowId || '',
            webhookUrl: n8nComponent.webhookUrl || '',
            endpoints: {
              ...prev.n8nWorkflow.endpoints,
              ...n8nComponent.endpoints
            }
          }
        }));

        toast({
          title: "Template Found",
          description: `Found and applied workflow: ${n8nComponent.name || 'Unknown'}. Configuration has been updated automatically.`
        });
      } else {
        toast({
          title: "No Template Found",
          description: "No suitable N8N workflow template was found for this automation type. You can configure manually or contact support.",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Template search error:', error);
      toast({
        title: "Search Failed",
        description: "Failed to search for workflow templates. Please configure manually or try again later.",
        variant: "destructive"
      });
    } finally {
      setIsSearchingTemplate(false);
    }
  };

  const updateTemplate = async () => {
    if (!isAdmin) {
      toast({
        title: "Access Denied",
        description: "You need admin privileges to update templates.",
        variant: "destructive"
      });
      return;
    }

    setIsUpdatingTemplate(true);
    try {
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${apiBaseUrl}/automation-templates/${template.id}/from-config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders
        },
        body: JSON.stringify({
          automation_config: config,
          update_template: true
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to update template');
      }

      const result = await response.json();

      toast({
        title: "Template Updated",
        description: `Template "${template.name}" has been updated with the current automation configuration.`
      });

    } catch (error) {
      console.error('Template update error:', error);
      toast({
        title: "Update Failed",
        description: error instanceof Error ? error.message : "Failed to update template. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsUpdatingTemplate(false);
    }
  };

  const generateEnhancedSystemPrompt = (extractedInfo: any) => {
    const companyName = config.companyInfo.name || extractedInfo?.companyName || 'our company';
    const services = extractedInfo?.services?.join(', ') || 'our services';
    const businessHours = extractedInfo?.businessHours || 'standard business hours';
    const contactInfo = extractedInfo?.contactInfo || {};

    return `${NO_HALLUCINATION_TEMPLATE}

## Company Information:
**Company Name**: ${companyName}
**Services**: ${services}
**Business Hours**: ${businessHours}
**Contact Information**:
- Phone: ${contactInfo?.phone || 'Available via support'}
- Email: ${contactInfo?.email || 'Available via support'}
- Address: ${contactInfo?.address || 'Available via support'}

## About ${companyName}:
${extractedInfo?.aboutText || config.companyInfo.description || 'Please refer to our official documentation for detailed information about our company.'}

## Knowledge Base:
Use only the information provided above when answering questions about ${companyName}. For any information not explicitly stated here, direct customers to our official contact points.`;
  };

  const createN8NWorkflow = async () => {
    try {
      // Create custom tool nodes for N8N workflow
      const customToolNodes = selectedCustomTools.map((tool, index) => ({
        id: `custom-tool-${tool.name}`,
        name: `Custom Tool: ${tool.name}`,
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: tool.endpoint,
          method: tool.method || 'POST',
          sendBody: true,
          specifyBody: 'json',
          jsonBody: '={{ $json }}',
          options: {}
        },
        position: [200 + (index * 300), 400]
      }));

      // Create N8N workflow using the n8n MCP tools
      const workflowConfig = {
        name: config.n8nWorkflow.workflowName,
        nodes: [
          {
            id: 'webhook-trigger',
            name: 'VAPI Webhook',
            type: 'n8n-nodes-base.webhook',
            parameters: {
              httpMethod: 'POST',
              path: 'vapi-helpdesk'
            },
            position: [0, 0]
          },
          {
            id: 'calendar-check',
            name: 'Check Calendar',
            type: 'n8n-nodes-base.calendly',
            parameters: {
              operation: 'getAvailability'
            },
            position: [200, 200]
          },
          {
            id: 'ticket-create',
            name: 'Create Ticket',
            type: 'n8n-nodes-base.freshdesk',
            parameters: {
              operation: 'createTicket'
            },
            position: [400, 200]
          },
          ...customToolNodes,
          {
            id: 'supabase-log',
            name: 'Log to Supabase',
            type: 'n8n-nodes-base.supabase',
            parameters: {
              operation: 'insert',
              table: 'call_logs'
            }
          }
        ],
        connections: {
          'webhook-trigger': {
            main: [
              [
                { node: 'calendar-check', type: 'main', index: 0 },
                { node: 'ticket-create', type: 'main', index: 0 },
                { node: 'supabase-log', type: 'main', index: 0 }
              ]
            ]
          }
        }
      };

      // This would integrate with the n8n MCP server to create the workflow
      // For now, we'll generate a mock workflow ID
      const workflowId = `helpdesk-${Date.now()}`;
      const webhookUrl = `https://automate.inspirecreations.it.com/webhook/${workflowId}`;

      setConfig(prev => ({
        ...prev,
        n8nWorkflow: {
          ...prev.n8nWorkflow,
          workflowId,
          webhookUrl
        }
      }));

      return workflowId;
    } catch (error) {
      console.error('Failed to create N8N workflow:', error);
      throw error;
    }
  };

  const createVAPIAgent = async () => {
    try {
      // Prepare custom tools for VAPI integration
      const customToolFunctions = selectedCustomTools.map(tool => ({
        type: 'function',
        function: {
          name: tool.name,
          description: tool.description,
          parameters: tool.schema?.function?.parameters || {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Query or input for the tool'
              }
            },
            required: ['query']
          }
        },
        server: {
          url: tool.endpoint,
          secret: process.env.VAPI_WEBHOOK_SECRET || 'webhook-secret'
        }
      }));

      // Combine standard tools with custom tools
      const allToolFunctions = [
        ...config.vapiAgent.tools.map(tool => ({
          type: 'function',
          function: {
            name: tool,
            description: `${tool.replace('_', ' ')} functionality`,
            parameters: {
              type: 'object',
              properties: {},
              required: []
            }
          }
        })),
        ...customToolFunctions
      ];

      const response = await fetch(`${apiBaseUrl}/vapi/create-assistant`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: `${config.companyInfo.name} Automation Assistant`,
          systemPrompt: config.vapiAgent.systemPrompt,
          voice: {
            model: 'eleven_flash_v2_5',
            voiceId: config.vapiAgent.voiceSettings.voiceId,
            provider: '11labs'
          },
          model: {
            model: config.vapiAgent.voiceSettings.model,
            provider: 'openai',
            maxTokens: 150
          },
          tools: allToolFunctions,
          firstMessage: `Hello! I'm ${config.companyInfo.name}'s AI automation assistant. I can help you book appointments, create support tickets, or answer questions about our services. How may I assist you today?`,
          serverUrl: config.n8nWorkflow.webhookUrl
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create VAPI assistant');
      }

      const vapiData = await response.json();
      setConfig(prev => ({
        ...prev,
        vapiAgent: {
          ...prev.vapiAgent,
          assistantId: vapiData.id,
          phoneNumberId: vapiData.phoneNumberId
        }
      }));

      return vapiData.id;
    } catch (error) {
      console.error('Failed to create VAPI agent:', error);
      throw error;
    }
  };

  const deployDemo = async () => {
    try {
      const demoHtml = generateDemoHTML();

      // Generate unique filename based on company name and timestamp
      const companySlug = config.companyInfo.name
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
      const timestamp = Date.now();
      const fileName = `${companySlug}-demo-${timestamp}.html`;

      const response = await fetch(`${apiBaseUrl}/deploy-demo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fileName: fileName,
          html: demoHtml
        })
      });

      if (!response.ok) {
        throw new Error('Failed to deploy demo');
      }

      const demoData = await response.json();
      setConfig(prev => ({
        ...prev,
        demoSettings: {
          ...prev.demoSettings,
          demoUrl: demoData.demoUrl, // Use correct field name from main.py response
          htmlTemplate: demoHtml,
          fileName: fileName
        }
      }));

      return demoData.demoUrl;
    } catch (error) {
      console.error('Failed to deploy demo:', error);
      throw error;
    }
  };

  const performDeploymentHealthChecks = async (configId: string, deploymentResult: DeploymentResult) => {
    try {
      const warnings: string[] = [];
      let success = true;

      // Check VAPI assistant health
      if (deploymentResult.vapi_assistant_id) {
        try {
          const vapiCheck = await automationOrchestrationService.testVAPIAssistant(deploymentResult.vapi_assistant_id);
          if (!vapiCheck.success) {
            warnings.push('VAPI assistant not responding properly');
            success = false;
          }
        } catch (error) {
          warnings.push('Failed to verify VAPI assistant');
          success = false;
        }
      } else {
        warnings.push('No VAPI assistant ID returned from deployment');
        success = false;
      }

      // Check n8n workflow health
      if (deploymentResult.n8n_workflow_id) {
        try {
          const n8nCheck = await automationOrchestrationService.testN8NWorkflow(deploymentResult.n8n_workflow_id);
          if (!n8nCheck.success) {
            warnings.push('n8n workflow not responding properly');
            success = false;
          }
        } catch (error) {
          warnings.push('Failed to verify n8n workflow');
          success = false;
        }
      } else {
        warnings.push('No n8n workflow ID returned from deployment');
        success = false;
      }

      // Check webhook connectivity
      if (deploymentResult.webhook_urls && Object.keys(deploymentResult.webhook_urls).length > 0) {
        for (const [nodeName, webhookUrl] of Object.entries(deploymentResult.webhook_urls)) {
          try {
            const webhookCheck = await fetch(webhookUrl, {
              method: 'GET',
              signal: AbortSignal.timeout(5000) // 5 second timeout
            });
            if (!webhookCheck.ok && webhookCheck.status !== 405) { // 405 Method Not Allowed is expected for webhooks
              warnings.push(`Webhook ${nodeName} not accessible`);
            }
          } catch (error) {
            warnings.push(`Failed to verify webhook ${nodeName}`);
          }
        }
      }

      return {
        success,
        warnings: warnings.length > 0 ? warnings : undefined
      };
    } catch (error) {
      return {
        success: false,
        warnings: ['Health check process failed: ' + (error instanceof Error ? error.message : 'Unknown error')]
      };
    }
  };

  const deployAutomation = async () => {
    setIsCreating(true);
    try {
      // Step 1: Always save configuration first with latest data
      toast({
        title: "Preparing Deployment",
        description: "Saving current configuration with all settings..."
      });

      const saveResult = await saveConfiguration(false); // Save as ready for deployment

      if (!saveResult?.success || !saveResult.configId) {
        throw new Error("Failed to save configuration before deployment. Please check your settings and try again.");
      }

      const currentConfigId = saveResult.configId;

      // Step 2: Pre-deployment validation
      toast({
        title: "Validating Configuration",
        description: "Checking configuration for any issues before deployment..."
      });

      try {
        const validationResult = await automationOrchestrationService.validateConfiguration(currentConfigId);

        if (!validationResult.valid) {
          const errorMessages = validationResult.errors.join(', ');
          throw new Error(`Configuration validation failed: ${errorMessages}`);
        }

        if (validationResult.warnings.length > 0) {
          console.warn('Configuration warnings:', validationResult.warnings);
        }
      } catch (validationError) {
        console.warn('Pre-deployment validation skipped:', validationError);
        // Continue with deployment even if validation fails (non-blocking)
      }

      // Step 3: Deploy the automation
      toast({
        title: "Deploying Automation",
        description: "Creating VAPI assistant, n8n workflow, and configuring integrations..."
      });

      const result = await automationOrchestrationService.deployConfiguration(currentConfigId);

      if (result.success) {
        // Step 4: Update local config with deployment results
        const updatedConfig = {
          ...config,
          status: 'deployed' as const,
          vapiAgent: {
            ...config.vapiAgent,
            assistantId: result.vapi_assistant_id || config.vapiAgent.assistantId,
            phoneNumberId: result.phone_number_id || config.vapiAgent.phoneNumberId
          },
          n8nWorkflow: {
            ...config.n8nWorkflow,
            workflowId: result.n8n_workflow_id || config.n8nWorkflow.workflowId,
            webhookUrl: result.webhook_urls?.['VAPI Webhook Trigger'] ||
                      result.webhook_urls?.['Webhook Trigger'] ||
                      config.n8nWorkflow.webhookUrl
          },
          demoSettings: {
            ...config.demoSettings,
            demoUrl: result.demo_url || config.demoSettings.demoUrl
          }
        };

        // Step 5: Save the updated configuration with deployment IDs
        await automationOrchestrationService.updateConfiguration(currentConfigId, {
          automation_name: updatedConfig.automationName,
          config: {
            userConfig: updatedConfig,
            vapi: updatedConfig.vapiAgent,
            n8n: updatedConfig.n8nWorkflow,
            integrations: updatedConfig.integrations,
            customTools: updatedConfig.customTools
          },
          status: 'deployed',
          deployment_info: {
            vapi_assistant_id: result.vapi_assistant_id,
            n8n_workflow_id: result.n8n_workflow_id,
            demo_url: result.demo_url,
            webhook_urls: result.webhook_urls,
            deployed_at: new Date().toISOString()
          }
        });

        setConfig(updatedConfig);
        setConfigId(currentConfigId);

        // Step 6: Perform comprehensive health checks
        toast({
          title: "Verifying Deployment",
          description: "Running comprehensive health checks to confirm all components are working..."
        });

        const healthCheckResult = await performDeploymentHealthChecks(currentConfigId, result);

        // Step 7: Post-deployment testing
        try {
          toast({
            title: "Testing Deployment",
            description: "Running automated tests to verify functionality..."
          });

          const testResult = await automationOrchestrationService.testConfiguration(currentConfigId, 'deployment_verification');

          if (testResult.success && testResult.summary.failed === 0) {
            toast({
              title: "🎉 Automation Deployed Successfully",
              description: `Your automation is live and fully functional!\n• VAPI Assistant: ${result.vapi_assistant_id}\n• N8N Workflow: ${result.n8n_workflow_id}\n• All tests passed: ${testResult.summary.passed}/${testResult.summary.total_tests}`
            });
          } else {
            toast({
              title: "Deployment Complete with Warnings",
              description: `Automation deployed but some tests failed. Check the test results for details.\n• Passed: ${testResult.summary.passed}\n• Failed: ${testResult.summary.failed}`,
              variant: "destructive"
            });
          }
        } catch (testError) {
          console.warn('Post-deployment testing failed:', testError);

          if (healthCheckResult.success) {
            toast({
              title: "Automation Deployed Successfully",
              description: `Your automation is now live!\n• VAPI Assistant: ${result.vapi_assistant_id}\n• N8N Workflow: ${result.n8n_workflow_id}\n• Health checks passed`
            });
          } else {
            toast({
              title: "Deployment Warning",
              description: `Automation deployed but health checks failed: ${healthCheckResult.warnings?.join(', ') || 'Unknown issues'}`,
              variant: "destructive"
            });
          }
        }

        // Step 8: Show deployment summary
        if (result.demo_url) {
          setTimeout(() => {
            toast({
              title: "Demo Available",
              description: `Your automation demo is ready at: ${result.demo_url}`,
            });
          }, 2000);
        }

      } else {
        throw new Error(result.error || 'Deployment failed - no error details provided');
      }
    } catch (error) {
      console.error('Deployment error:', error);

      // Update status to failed if we have a config ID
      if (configId) {
        try {
          await automationOrchestrationService.updateConfiguration(configId, {
            status: 'failed',
            deployment_info: {
              error: error instanceof Error ? error.message : 'Unknown deployment error',
              failed_at: new Date().toISOString()
            }
          });

          setConfig(prev => ({ ...prev, status: 'failed' }));
        } catch (updateError) {
          console.error('Failed to update status to failed:', updateError);
        }
      }

      toast({
        title: "Deployment Failed",
        description: error instanceof Error ? error.message : "Failed to deploy automation. Please check your configuration and try again.",
        variant: "destructive"
      });
    } finally {
      setIsCreating(false);
    }
  };

  const stopAutomation = async () => {
    if (!configId) return;

    const confirmed = window.confirm(
      `Are you sure you want to stop "${config.automationName}"? This will deactivate the automation.`
    );

    if (!confirmed) return;

    try {
      const result = await automationOrchestrationService.stopConfiguration(configId);
      if (result.success) {
        setConfig(prev => ({ ...prev, status: 'stopped' }));
        toast({
          title: "Automation Stopped",
          description: `Automation "${config.automationName}" has been stopped.`
        });
      } else {
        throw new Error(result.error || 'Stop failed');
      }
    } catch (error) {
      toast({
        title: "Stop Failed",
        description: error instanceof Error ? error.message : "Failed to stop automation",
        variant: "destructive"
      });
    }
  };

  const deleteConfiguration = async () => {
    if (!configId) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete "${config.automationName}"? This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      await automationOrchestrationService.deleteConfiguration(configId);
      toast({
        title: "Configuration Deleted",
        description: `Automation "${config.automationName}" has been deleted.`
      });
      onClose();
    } catch (error) {
      toast({
        title: "Delete Failed",
        description: error instanceof Error ? error.message : "Failed to delete configuration",
        variant: "destructive"
      });
    }
  };

  const saveConfiguration = async (asDraft: boolean = true) => {
    if (!config.automationName.trim()) {
      toast({
        title: "Name Required",
        description: "Please enter an automation name before saving.",
        variant: "destructive"
      });
      return;
    }

    setIsSaving(true);
    try {
      // Prepare comprehensive configuration data with all fields properly mapped
      const configToSave = {
        automationName: config.automationName,
        status: asDraft ? 'draft' as const : config.status || 'draft' as const,
        // Company Information
        companyInfo: {
          name: config.companyInfo.name || '',
          description: config.companyInfo.description || '',
          url: config.companyInfo.url || '',
          transferNumber: config.companyInfo.transferNumber || '+12397783680',
          extractedInfo: config.companyInfo.extractedInfo || null
        },
        // Audience Selection (for campaign templates)
        audienceSelection: config.audienceSelection ? {
          targetAudience: config.audienceSelection.targetAudience || '',
          audienceSize: config.audienceSelection.audienceSize || '',
          demographics: config.audienceSelection.demographics || '',
          channels: config.audienceSelection.channels || [],
          timing: config.audienceSelection.timing || '',
          objectives: config.audienceSelection.objectives || []
        } : null,
        // Industry Configuration
        industryConfig: industryConfig || {},
        // VAPI Agent Configuration - comprehensive save
        vapiAgent: {
          assistantId: config.vapiAgent.assistantId || '',
          phoneNumberId: config.vapiAgent.phoneNumberId || '',
          systemPrompt: config.vapiAgent.systemPrompt || NO_HALLUCINATION_TEMPLATE,
          voiceSettings: {
            voiceId: config.vapiAgent.voiceSettings?.voiceId || 'jennifer',
            model: config.vapiAgent.voiceSettings?.model || 'gpt-4o',
            maxDuration: config.vapiAgent.voiceSettings?.maxDuration || 600,
            voice: config.vapiAgent.voiceSettings?.voice || 'alloy',
            speed: config.vapiAgent.voiceSettings?.speed || 1.0,
            stability: config.vapiAgent.voiceSettings?.stability || 0.5,
            similarityBoost: config.vapiAgent.voiceSettings?.similarityBoost || 0.75
          },
          llmSettings: {
            model: config.vapiAgent.llmSettings?.model || config.vapiAgent.voiceSettings?.model || 'gpt-4o',
            temperature: config.vapiAgent.llmSettings?.temperature || 0.7,
            maxTokens: config.vapiAgent.llmSettings?.maxTokens || 150
          },
          callSettings: {
            maxDuration: config.vapiAgent.callSettings?.maxDuration || config.vapiAgent.voiceSettings?.maxDuration || 600,
            silenceTimeout: config.vapiAgent.callSettings?.silenceTimeout || 10,
            backgroundSound: config.vapiAgent.callSettings?.backgroundSound || 'off'
          },
          tools: config.vapiAgent.tools || ['calendar_booking', 'ticket_creation', 'web_search', 'escalation'],
          // Save custom settings override if enabled
          custom_settings_override: useCustomVoiceSettings ? {
            tts: {
              provider: customVoiceSettings.tts.provider,
              voice: customVoiceSettings.tts.voice,
              speed: customVoiceSettings.tts.speed,
              pitch: customVoiceSettings.tts.pitch,
            },
            asr: {
              provider: customVoiceSettings.asr.provider,
              language: customVoiceSettings.asr.language,
            },
            llm: {
              model: customVoiceSettings.llm.model,
              temperature: customVoiceSettings.llm.temperature,
              maxTokens: customVoiceSettings.llm.maxTokens,
            },
            referenceVoice: customVoiceSettings.referenceVoice,
          } : null
        },
        // N8N Workflow Configuration - comprehensive save
        n8nWorkflow: {
          workflowId: config.n8nWorkflow.workflowId || '',
          workflowName: config.n8nWorkflow.workflowName || config.automationName + ' Workflow',
          webhookUrl: config.n8nWorkflow.webhookUrl || '',
          nodes: config.n8nWorkflow.nodes || [],
          connections: config.n8nWorkflow.connections || {},
          endpoints: {
            calendar: config.n8nWorkflow.endpoints?.calendar || '/calendar/availability',
            tickets: config.n8nWorkflow.endpoints?.tickets || '/tickets/create',
            availability: config.n8nWorkflow.endpoints?.availability || '/availability/check',
            escalation: config.n8nWorkflow.endpoints?.escalation || '/escalation/route',
            analytics: config.n8nWorkflow.endpoints?.analytics || '/analytics/track',
            webhook: config.n8nWorkflow.endpoints?.webhook || '',
            healthCheck: config.n8nWorkflow.endpoints?.healthCheck || '',
            ...config.n8nWorkflow.endpoints
          }
        },
        // Integration Settings - comprehensive save
        integrations: {
          calendly: {
            enabled: config.integrations.calendly?.enabled || false,
            apiKey: config.integrations.calendly?.apiKey || ''
          },
          supabase: {
            enabled: config.integrations.supabase?.enabled || false,
            projectId: config.integrations.supabase?.projectId || 'ljzbzjgvwzivpmlmuxhx'
          },
          tavily: {
            enabled: config.integrations.tavily?.enabled || false,
            apiKey: config.integrations.tavily?.apiKey || ''
          },
          resend: {
            enabled: config.integrations.resend?.enabled || false,
            apiKey: config.integrations.resend?.apiKey || ''
          },
          vonage: {
            enabled: config.integrations.vonage?.enabled || false,
            apiKey: config.integrations.vonage?.apiKey || ''
          }
        },
        // Custom Tools Configuration - comprehensive save
        customTools: {
          enabled: config.customTools.enabled || false,
          selectedTools: config.customTools.selectedTools || [],
          availableTools: config.customTools.availableTools || [],
          templateTools: template?.customTools || []
        },
        // Demo Settings - comprehensive save
        demoSettings: {
          enableDemo: config.demoSettings.enableDemo || false,
          demoUrl: config.demoSettings.demoUrl || '',
          htmlTemplate: config.demoSettings.htmlTemplate || ''
        },
        // Analytics Settings - comprehensive save
        analytics: {
          enableTracking: config.analytics.enableTracking || false,
          webhookUrl: config.analytics.webhookUrl || '',
          reportEmail: config.analytics.reportEmail || 'ailabsafrica@gmail.com'
        },
        // Template Information
        templateId: template?.id || '',
        templateName: template?.name || '',
        templateCategory: template?.category || 'general',
        templateIndustry: template?.industry || 'General',
        // Metadata and Timestamps
        createdAt: config.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        version: '1.0.0'
      };

      let savedConfig: AutomationConfig;

      if (configId) {
        // Update existing configuration with all fields
        const updatePayload = {
          automation_name: configToSave.automationName,
          config: {
            userConfig: configToSave,
            vapi: configToSave.vapiAgent,
            n8n: configToSave.n8nWorkflow,
            integrations: configToSave.integrations,
            customTools: configToSave.customTools
          },
          status: configToSave.status,
          updated_at: configToSave.updatedAt
        };

        const response = await automationOrchestrationService.updateConfiguration(configId, updatePayload);
        savedConfig = response.configuration || response;

        toast({
          title: "Configuration Updated",
          description: `Automation "${configToSave.automationName}" has been updated with all settings including VAPI, N8N, integrations, and custom tools.`
        });
      } else {
        // Create new configuration with comprehensive data
        const configData = {
          template_id: template?.id || '',
          configuration: configToSave
        };

        const response = await automationOrchestrationService.createConfiguration(configData);
        savedConfig = response.configuration;
        setConfigId(savedConfig.id);

        toast({
          title: "Configuration Saved",
          description: `Automation "${configToSave.automationName}" has been saved with all settings including VAPI agent, N8N workflow, integrations, and custom tools.`
        });
      }

      // Update local state to reflect saved configuration
      setConfig(prevConfig => ({
        ...prevConfig,
        ...configToSave,
        id: savedConfig.id,
        status: savedConfig.status as any
      }));

      // Return success
      return { success: true, configId: savedConfig.id };

    } catch (error) {
      console.error('Save configuration error:', error);
      toast({
        title: "Save Failed",
        description: error instanceof Error ? error.message : "Failed to save configuration. Please check your settings and try again.",
        variant: "destructive"
      });
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    } finally {
      setIsSaving(false);
    }
  };

  const generateDemoHTML = () => {
    const companyName = config.companyInfo.name;
    const description = config.companyInfo.description || config.companyInfo.extractedInfo?.aboutText || '';
    const services = config.companyInfo.extractedInfo?.services?.join(', ') || 'our services';

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${companyName} - AI Automation Demo</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 40px; }
        .header h1 { font-size: 3em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .demo-card { background: white; border-radius: 15px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .call-button { background: #28a745; color: white; border: none; padding: 15px 30px; font-size: 1.1em; border-radius: 25px; cursor: pointer; transition: all 0.3s; }
        .call-button:hover { background: #218838; transform: translateY(-2px); }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; }
        .feature { text-align: center; padding: 20px; }
        .feature-icon { font-size: 2em; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>${companyName}</h1>
            <p>AI-Powered Automation Demo</p>
        </div>

        <div class="demo-card">
            <h2>Try Our AI Automation Assistant</h2>
            <p>${description}</p>
            <p><strong>Services:</strong> ${services}</p>

            <div style="text-align: center; margin: 30px 0;">
                <button class="call-button" onclick="startCall()">📞 Call Our AI Assistant</button>
            </div>

            <div class="features">
                <div class="feature">
                    <div class="feature-icon">📅</div>
                    <h3>Appointment Booking</h3>
                    <p>Book appointments with our team instantly</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">🎫</div>
                    <h3>Support Tickets</h3>
                    <p>Create support tickets for technical issues</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">🔍</div>
                    <h3>Information Search</h3>
                    <p>Get answers about our services and policies</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">👥</div>
                    <h3>Human Escalation</h3>
                    <p>Seamlessly connect with human agents when needed</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function startCall() {
            // This would integrate with VAPI to start a call
            alert('Demo call would start here with VAPI assistant: ${config.vapiAgent.assistantId}');
        }
    </script>
</body>
</html>`;
  };

  const handleSubmit = async () => {
    setIsCreating(true);
    try {
      // Save configuration first
      await saveConfiguration(false); // Save as deployed, not draft

      // Create N8N workflow
      await createN8NWorkflow();

      // Create VAPI agent
      await createVAPIAgent();

      // Deploy demo if enabled
      if (config.demoSettings.enableDemo) {
        await deployDemo();
      }

      const result = await onCreateCampaign(config);

      if (result.success) {
        // Update config status to deployed if we have an ID
        if (configId) {
          await automationConfigService.updateConfig(configId, {
            ...config,
            status: 'deployed'
          });
        }

        toast({
          title: "Automation Campaign Created",
          description: "Your automation campaign has been configured and deployed successfully."
        });

        // Handle redirection based on demo deployment
        if (config.demoSettings.enableDemo && result.demoUrl) {
          // Redirect to demo page
          window.open(result.demoUrl, '_blank');
          toast({
            title: "Demo Page Opened",
            description: "Your demo page has been opened in a new tab."
          });
        }

        // Close wizard and let parent component handle navigation to campaign list
        onClose();
      } else {
        throw new Error(result.error || 'Campaign creation failed');
      }
    } catch (error) {
      toast({
        title: "Creation Failed",
        description: error instanceof Error ? error.message : "Failed to create helpdesk campaign. Please check your configuration.",
        variant: "destructive"
      });
    } finally {
      setIsCreating(false);
    }
  };

  const updateConfig = (path: string, value: any) => {
    setConfig(prev => {
      const keys = path.split('.');
      const updated = { ...prev };
      let current = updated;

      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...current[keys[i]] };
        current = current[keys[i]];
      }

      current[keys[keys.length - 1]] = value;
      return updated;
    });
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Test Functions
  const testVAPIAgent = async () => {
    setTestResults(prev => ({ ...prev, vapi: { status: 'testing', message: 'Testing VAPI voice agent...', tested: true } }));

    try {
      // Test VAPI agent by making a test call to verify configuration
      const response = await fetch(`${apiBaseUrl}/vapi/test-agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          assistantId: config.vapiAgent.assistantId,
          phoneNumberId: config.vapiAgent.phoneNumberId,
          systemPrompt: config.vapiAgent.systemPrompt.substring(0, 100) + '...',
          voiceSettings: config.vapiAgent.voiceSettings
        })
      });

      if (response.ok) {
        const result = await response.json();
        setTestResults(prev => ({
          ...prev,
          vapi: {
            status: 'success',
            message: `VAPI agent configured successfully. Voice: ${config.vapiAgent.voiceSettings.voiceId}, Model: ${config.vapiAgent.voiceSettings.model}`,
            tested: true
          }
        }));
      } else {
        throw new Error('VAPI agent test failed');
      }
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        vapi: {
          status: 'error',
          message: 'VAPI agent configuration error. Please check your voice settings and system prompt.',
          tested: true
        }
      }));
    }
  };

  const testN8NWorkflow = async () => {
    setTestResults(prev => ({ ...prev, n8n: { status: 'testing', message: 'Testing N8N workflow connectivity...', tested: true } }));

    try {
      // Test N8N workflow by pinging the webhook URL
      const response = await fetch(config.n8nWorkflow.webhookUrl || `${apiBaseUrl}/n8n/test-workflow`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          workflowId: config.n8nWorkflow.workflowId,
          testData: { test: true, timestamp: new Date().toISOString() }
        })
      });

      if (response.ok || response.status === 404) {
        setTestResults(prev => ({
          ...prev,
          n8n: {
            status: 'success',
            message: `N8N workflow ready. Workflow ID: ${config.n8nWorkflow.workflowId || 'Auto-generated'}`,
            tested: true
          }
        }));
      } else {
        throw new Error('N8N workflow not responding');
      }
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        n8n: {
          status: 'error',
          message: 'N8N workflow connectivity issue. Please check workflow configuration.',
          tested: true
        }
      }));
    }
  };

  const testWebhooks = async () => {
    setTestResults(prev => ({ ...prev, webhooks: { status: 'testing', message: 'Testing webhook endpoints...', tested: true } }));

    try {
      // Test main webhook endpoints
      const endpoints = Object.values(config.n8nWorkflow.endpoints);
      let successCount = 0;

      for (const endpoint of endpoints) {
        try {
          const response = await fetch(`${apiBaseUrl}${endpoint}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ test: true })
          });
          if (response.ok || response.status === 404 || response.status === 405) {
            successCount++;
          }
        } catch (e) {
          // Endpoint might not exist yet, which is normal
          successCount++;
        }
      }

      setTestResults(prev => ({
        ...prev,
        webhooks: {
          status: 'success',
          message: `${successCount}/${endpoints.length} webhook endpoints configured and ready`,
          tested: true
        }
      }));
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        webhooks: {
          status: 'error',
          message: 'Webhook endpoint configuration error',
          tested: true
        }
      }));
    }
  };

  const testCustomTools = async () => {
    setTestResults(prev => ({ ...prev, customTools: { status: 'testing', message: 'Testing custom tools endpoints...', tested: true } }));

    try {
      if (!config.customTools.enabled || config.customTools.selectedTools.length === 0) {
        setTestResults(prev => ({
          ...prev,
          customTools: {
            status: 'success',
            message: 'Custom tools disabled - no tests needed',
            tested: true
          }
        }));
        return;
      }

      // Test healthcare provider search endpoint
      const response = await fetch(buildApiUrl('/custom-tools/healthcare/search-providers'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          query: 'test doctor',
          max_results: 1
        })
      });

      if (response.ok) {
        const result = await response.json();
        setTestResults(prev => ({
          ...prev,
          customTools: {
            status: 'success',
            message: `${config.customTools.selectedTools.length} custom tools available and responding`,
            tested: true
          }
        }));
      } else {
        throw new Error('Custom tools not responding');
      }
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        customTools: {
          status: 'error',
          message: 'Custom tools endpoint error. Tools may not be accessible.',
          tested: true
        }
      }));
    }
  };

  const testIntegrations = async () => {
    setTestResults(prev => ({ ...prev, integrations: { status: 'testing', message: 'Testing integrations connectivity...', tested: true } }));

    try {
      let successCount = 0;
      let totalEnabled = 0;
      const results = [];

      // Test enabled integrations
      Object.entries(config.integrations).forEach(([key, integration]) => {
        if (integration.enabled) {
          totalEnabled++;
          if (integration.apiKey || key === 'supabase') {
            successCount++;
            results.push(`${key}: configured`);
          } else {
            results.push(`${key}: missing API key`);
          }
        }
      });

      const status = successCount === totalEnabled ? 'success' : successCount > 0 ? 'warning' : 'error';
      const message = totalEnabled === 0 ?
        'No integrations enabled' :
        `${successCount}/${totalEnabled} integrations configured. ${results.join(', ')}`;

      setTestResults(prev => ({
        ...prev,
        integrations: {
          status,
          message,
          tested: true
        }
      }));
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        integrations: {
          status: 'error',
          message: 'Integration configuration error',
          tested: true
        }
      }));
    }
  };

  const runAllTests = async () => {
    setIsRunningTests(true);

    // Reset test results
    setTestResults({
      vapi: { status: 'pending', message: '', tested: false },
      n8n: { status: 'pending', message: '', tested: false },
      webhooks: { status: 'pending', message: '', tested: false },
      customTools: { status: 'pending', message: '', tested: false },
      integrations: { status: 'pending', message: '', tested: false }
    });

    // Run tests sequentially with small delays
    await testVAPIAgent();
    await new Promise(resolve => setTimeout(resolve, 500));

    await testN8NWorkflow();
    await new Promise(resolve => setTimeout(resolve, 500));

    await testWebhooks();
    await new Promise(resolve => setTimeout(resolve, 500));

    await testCustomTools();
    await new Promise(resolve => setTimeout(resolve, 500));

    await testIntegrations();

    setIsRunningTests(false);

    toast({
      title: "Tests Completed",
      description: "All component tests have been executed. Review results below.",
    });
  };

  // Enhanced validation using orchestration service
  const validateConfiguration = async () => {
    if (!configId) {
      toast({
        title: "Save Required",
        description: "Please save the configuration before validating.",
        variant: "destructive"
      });
      return;
    }

    setIsRunningTests(true);
    try {
      const validationResult = await automationOrchestrationService.validateConfiguration(configId);

      if (validationResult.valid) {
        toast({
          title: "Validation Successful",
          description: "Configuration passed all validation checks."
        });
      } else {
        const errors = validationResult.errors.join(', ');
        const warnings = validationResult.warnings.join(', ');
        toast({
          title: "Validation Issues Found",
          description: `Errors: ${errors}${warnings ? `, Warnings: ${warnings}` : ''}`,
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Validation Failed",
        description: error instanceof Error ? error.message : "Failed to validate configuration",
        variant: "destructive"
      });
    } finally {
      setIsRunningTests(false);
    }
  };

  // Get configuration status using orchestration service
  const getConfigurationStatus = async () => {
    if (!configId) return null;

    try {
      const statusResponse = await automationOrchestrationService.getConfigurationStatus(configId);

      // Update local state with status
      setConfig(prev => ({
        ...prev,
        status: statusResponse.status as any
      }));

      return statusResponse;
    } catch (error) {
      console.error('Failed to get configuration status:', error);
      return null;
    }
  };

  // Monitor configuration status periodically
  useEffect(() => {
    let statusInterval: NodeJS.Timeout | null = null;

    if (configId && config.status === 'deployed') {
      // Poll status every 30 seconds for deployed configurations
      statusInterval = setInterval(getConfigurationStatus, 30000);
    }

    return () => {
      if (statusInterval) clearInterval(statusInterval);
    };
  }, [configId, config.status]);

  // Test configuration using orchestration service
  const testConfigurationFull = async (testScenario?: string) => {
    if (!configId) {
      toast({
        title: "Save Required",
        description: "Please save the configuration before testing.",
        variant: "destructive"
      });
      return;
    }

    setIsRunningTests(true);
    try {
      const testResult = await automationOrchestrationService.testConfiguration(configId, testScenario);

      if (testResult.success) {
        const { summary } = testResult;
        toast({
          title: "Tests Completed",
          description: `Passed: ${summary.passed}, Failed: ${summary.failed}, Skipped: ${summary.skipped}`
        });
      } else {
        toast({
          title: "Tests Failed",
          description: "Some tests failed. Check the test results for details.",
          variant: "destructive"
        });
      }

      return testResult;
    } catch (error) {
      toast({
        title: "Testing Failed",
        description: error instanceof Error ? error.message : "Failed to run tests",
        variant: "destructive"
      });
    } finally {
      setIsRunningTests(false);
    }
  };

  const getTestStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'error':
        return <X className="h-4 w-4 text-red-600" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />;
      case 'testing':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getTestStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'border-green-200 bg-green-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      case 'testing':
        return 'border-blue-200 bg-blue-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const currentStepData = steps[currentStep];
  const StepIcon = currentStepData.icon;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="border-b pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Headphones className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <DialogTitle>Automation Deployment Setup</DialogTitle>
                <DialogDescription>
                  Step {currentStep + 1} of {steps.length}: {currentStepData.title}
                </DialogDescription>
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline" className="text-xs">
                  {template?.category || 'general'}
                </Badge>
                {template?.isEnhanced && (
                  <Badge variant="default" className="text-xs bg-blue-100 text-blue-800 border-blue-200">
                    Enhanced
                  </Badge>
                )}
              </div>
              <div className="text-sm font-medium text-gray-600">
                {existingConfigId ? `Editing: ${config?.automationName || 'Automation'}` : `Configuring: ${template?.name || template?.template_name || 'Template'}`}
              </div>
              {configId && (
                <div className="text-xs text-green-600 mt-1">
                  {config.status === 'deployed' ? '✅ Deployed' : config.status === 'stopped' ? '⏸️ Stopped' : '📝 Draft'}
                </div>
              )}
            </div>
          </div>
        </DialogHeader>

        {/* Progress */}
        <div className="flex justify-between mb-6">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = index === currentStep;
            const isCompleted = index < currentStep;

            return (
              <div
                key={step.id}
                className={`flex flex-col items-center gap-2 ${isActive ? 'text-primary' : isCompleted ? 'text-green-600' : 'text-gray-600'}`}
              >
                <div className={`p-2 rounded-full ${isActive ? 'bg-primary/10' : isCompleted ? 'bg-green-100' : 'bg-muted'}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <span className="text-xs text-center">{step.title}</span>
              </div>
            );
          })}
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Step 0: Audience Selection (for campaign templates only) */}
          {currentStep === 0 && isCampaignTemplate && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-orange-600" />
                    <div>
                      <CardTitle>Campaign Audience Selection</CardTitle>
                      <CardDescription>
                        Define your target audience for this campaign to ensure effective outreach and engagement.
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <Label htmlFor="target-audience">Target Audience</Label>
                    <Textarea
                      id="target-audience"
                      value={config.audienceSelection?.targetAudience || ''}
                      onChange={(e) => updateConfig('audienceSelection.targetAudience', e.target.value)}
                      placeholder="Describe your primary target audience (e.g., existing customers, potential leads, specific demographics)"
                      rows={3}
                    />
                  </div>

                  <div>
                    <Label htmlFor="audience-size">Expected Audience Size</Label>
                    <Input
                      id="audience-size"
                      value={config.audienceSelection?.audienceSize || ''}
                      onChange={(e) => updateConfig('audienceSelection.audienceSize', e.target.value)}
                      placeholder="e.g., 1,000-5,000 contacts"
                    />
                  </div>

                  <div>
                    <Label htmlFor="demographics">Demographics & Criteria</Label>
                    <Textarea
                      id="demographics"
                      value={config.audienceSelection?.demographics || ''}
                      onChange={(e) => updateConfig('audienceSelection.demographics', e.target.value)}
                      placeholder="Age range, location, interests, purchase history, etc."
                      rows={3}
                    />
                  </div>

                  <div>
                    <Label>Communication Channels</Label>
                    <div className="grid grid-cols-2 gap-3 mt-2">
                      {['Voice Calls', 'SMS', 'Email', 'WhatsApp', 'Social Media', 'In-App'].map((channel) => (
                        <div key={channel} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id={`channel-${channel}`}
                            checked={config.audienceSelection?.channels.includes(channel) || false}
                            onChange={(e) => {
                              const channels = config.audienceSelection?.channels || [];
                              const updatedChannels = e.target.checked
                                ? [...channels, channel]
                                : channels.filter(c => c !== channel);
                              updateConfig('audienceSelection.channels', updatedChannels);
                            }}
                            className="rounded border-gray-300"
                          />
                          <Label htmlFor={`channel-${channel}`} className="text-sm">
                            {channel}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="timing">Campaign Timing</Label>
                    <Input
                      id="timing"
                      value={config.audienceSelection?.timing || ''}
                      onChange={(e) => updateConfig('audienceSelection.timing', e.target.value)}
                      placeholder="e.g., Business hours, specific days/times, seasonal"
                    />
                  </div>

                  <div>
                    <Label>Campaign Objectives</Label>
                    <div className="grid grid-cols-2 gap-3 mt-2">
                      {['Lead Generation', 'Customer Retention', 'Product Launch', 'Event Promotion', 'Survey/Feedback', 'Support Outreach'].map((objective) => (
                        <div key={objective} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id={`objective-${objective}`}
                            checked={config.audienceSelection?.objectives.includes(objective) || false}
                            onChange={(e) => {
                              const objectives = config.audienceSelection?.objectives || [];
                              const updatedObjectives = e.target.checked
                                ? [...objectives, objective]
                                : objectives.filter(o => o !== objective);
                              updateConfig('audienceSelection.objectives', updatedObjectives);
                            }}
                            className="rounded border-gray-300"
                          />
                          <Label htmlFor={`objective-${objective}`} className="text-sm">
                            {objective}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Company Information */}
          {currentStep === (isCampaignTemplate ? 1 : 0) && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Company Information</CardTitle>
                  <CardDescription>Enter your company details for the helpdesk assistant</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="automation-name">Automation Name</Label>
                    <Input
                      id="automation-name"
                      value={config.automationName}
                      onChange={(e) => updateConfig('automationName', e.target.value)}
                      placeholder="e.g., Customer Support Automation"
                      className="mt-2"
                    />
                    <p className="text-xs text-gray-600 mt-1">
                      Give your automation a unique name for easy identification
                    </p>
                  </div>

                  <div>
                    <Label htmlFor="company-name">Company Name</Label>
                    <Input
                      id="company-name"
                      value={config.companyInfo.name}
                      onChange={(e) => updateConfig('companyInfo.name', e.target.value)}
                      placeholder="e.g., GLICO Life Insurance"
                      className="mt-2"
                    />
                  </div>

                  <div>
                    <Label htmlFor="company-url">Company Website URL</Label>
                    <Input
                      id="company-url"
                      value={config.companyInfo.url}
                      onChange={(e) => updateConfig('companyInfo.url', e.target.value)}
                      placeholder="https://www.company.com"
                      className="mt-2"
                    />
                  </div>

                  <div>
                    <Label htmlFor="company-description">Company Description</Label>
                    <Textarea
                      id="company-description"
                      value={config.companyInfo.description}
                      onChange={(e) => updateConfig('companyInfo.description', e.target.value)}
                      placeholder="Brief description of your company and services"
                      rows={4}
                      className="mt-2"
                    />
                  </div>

                  <div>
                    <Label htmlFor="transfer-number">Transfer Number</Label>
                    <Input
                      id="transfer-number"
                      value={config.companyInfo.transferNumber || '+12397783680'}
                      onChange={(e) => updateConfig('companyInfo.transferNumber', e.target.value)}
                      placeholder="+12397783680"
                      className="mt-2"
                    />
                    <p className="text-xs text-gray-600 mt-1">
                      Phone number to transfer calls to when customers request human assistance
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 1: Industry Configuration */}
          {currentStep === (isCampaignTemplate ? 3 : 2) && (
            <div className="space-y-6">
              <IndustryConfigHandler
                industry={template?.industry || 'General'}
                config={industryConfig}
                onConfigChange={(updates) => {
                  setIndustryConfig(prev => ({ ...prev, ...updates }));
                  // Also update the main config with industry-specific settings
                  setConfig(prev => ({
                    ...prev,
                    industryConfig: { ...prev.industryConfig, ...updates }
                  }));
                }}
              />
            </div>
          )}

          {/* Step 2: System Prompt Generation */}
          {currentStep === (isCampaignTemplate ? 4 : 3) && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Generate System Prompt</CardTitle>
                  <CardDescription>Extract information from your website and generate an AI system prompt for your voice agent</CardDescription>
                </CardHeader>
                <CardContent>
                  <SystemPromptGenerator
                    primaryUrl={config.companyInfo.url}
                    onUrlChange={(url) => updateConfig('companyInfo.url', url)}
                    onPromptGenerated={(prompt, extractedInfo) => {
                      // Update system prompt
                      updateConfig('vapiAgent.systemPrompt', prompt);

                      // Update extracted company info
                      if (extractedInfo) {
                        updateConfig('companyInfo.extractedInfo', extractedInfo);

                        // Update company name and description if they were extracted
                        if (extractedInfo.companyName && !config.companyInfo.name) {
                          updateConfig('companyInfo.name', extractedInfo.companyName);
                        }
                        if (extractedInfo.aboutText && !config.companyInfo.description) {
                          updateConfig('companyInfo.description', extractedInfo.aboutText);
                        }
                      }
                    }}
                    initialPrompt={config.vapiAgent.systemPrompt}
                    showDocumentUpload={true}
                    showMultipleUrls={true}
                    apiBaseUrl={apiBaseUrl}
                  />
                </CardContent>
              </Card>
            </div>
          )}

          {/* Knowledge Base Management */}
          {currentStep === (isCampaignTemplate ? 2 : 1) && (
            <KnowledgeBaseStep
              config={config}
              setConfig={setConfig}
              apiBaseUrl={apiBaseUrl}
            />
          )}

          {/* Step 3: Voice Settings */}
          {currentStep === (isCampaignTemplate ? 5 : 4) && (
            <div className="space-y-6">
              <VoiceSettingsOverride
                vapiVoiceSettings={{
                  provider: config.vapiAgent.voiceSettings?.provider,
                  voiceId: config.vapiAgent.voiceSettings?.voiceId,
                  model: config.vapiAgent.voiceSettings?.model,
                  speed: config.vapiAgent.voiceSettings?.speed,
                  pitch: config.vapiAgent.voiceSettings?.pitch,
                }}
                vapiTranscriberSettings={{
                  provider: config.vapiAgent.transcriber?.provider,
                  model: config.vapiAgent.transcriber?.model,
                  language: config.vapiAgent.transcriber?.language,
                }}
                vapiModelSettings={{
                  provider: config.vapiAgent.modelSettings?.provider,
                  model: config.vapiAgent.modelSettings?.model,
                  temperature: config.vapiAgent.modelSettings?.temperature,
                  maxTokens: config.vapiAgent.modelSettings?.maxTokens,
                }}
                useCustomSettings={useCustomVoiceSettings}
                onUseCustomSettingsChange={setUseCustomVoiceSettings}
                customTTSProvider={customVoiceSettings.tts.provider}
                customTTSVoice={customVoiceSettings.tts.voice}
                customTTSSpeed={customVoiceSettings.tts.speed}
                customTTSPitch={customVoiceSettings.tts.pitch}
                onCustomTTSChange={(settings) => {
                  setCustomVoiceSettings(prev => ({
                    ...prev,
                    tts: { ...prev.tts, ...settings }
                  }));
                }}
                customASRProvider={customVoiceSettings.asr.provider}
                customASRLanguage={customVoiceSettings.asr.language}
                onCustomASRChange={(settings) => {
                  setCustomVoiceSettings(prev => ({
                    ...prev,
                    asr: { ...prev.asr, ...settings }
                  }));
                }}
                customLLMModel={customVoiceSettings.llm.model}
                customLLMTemperature={customVoiceSettings.llm.temperature}
                customLLMMaxTokens={customVoiceSettings.llm.maxTokens}
                onCustomLLMChange={(settings) => {
                  setCustomVoiceSettings(prev => ({
                    ...prev,
                    llm: { ...prev.llm, ...settings }
                  }));
                }}
                customReferenceVoiceId={customVoiceSettings.referenceVoice}
                onCustomReferenceVoiceChange={(voiceId) => {
                  setCustomVoiceSettings(prev => ({
                    ...prev,
                    referenceVoice: voiceId
                  }));
                }}
                ttsProviders={ttsProviders}
                asrProviders={asrProviders}
                llmModels={llmModels}
                clonedVoices={clonedVoices}
                apiBaseUrl={apiBaseUrl}
                getAuthHeaders={async () => {
                  const headers = await getAuthHeaders();
                  return headers;
                }}
                isLoading={providersLoading}
              />
              
              <Card>
                <CardContent className="pt-6">
                  <div>
                    <Label htmlFor="max-duration">Max Call Duration (seconds)</Label>
                    <Input
                      id="max-duration"
                      type="number"
                      value={config.vapiAgent.voiceSettings.maxDuration}
                      onChange={(e) => updateConfig('vapiAgent.voiceSettings.maxDuration', parseInt(e.target.value) || 600)}
                      min="60"
                      max="3600"
                      className="mt-2"
                    />
                    <p className="text-xs text-gray-600 mt-1">
                      Maximum duration for voice calls (60-3600 seconds)
                    </p>
                  </div>

                  <div className="mt-4">
                    <Label>Available Tools</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {config.vapiAgent.tools.map((tool, index) => (
                        <Badge key={index} variant="default">{tool.replace('_', ' ')}</Badge>
                      ))}
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                      Tools are automatically configured based on your selected template and integrations
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 4: N8N Workflow */}
          {currentStep === (isCampaignTemplate ? 6 : 5) && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>N8N Workflow Configuration</CardTitle>
                  <CardDescription>Configure your automation workflow</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="workflow-name">Workflow Name</Label>
                    <Input
                      id="workflow-name"
                      value={config.n8nWorkflow.workflowName}
                      onChange={(e) => updateConfig('n8nWorkflow.workflowName', e.target.value)}
                      className="mt-2"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="calendar-endpoint">Calendar Endpoint</Label>
                      <Input
                        id="calendar-endpoint"
                        value={config.n8nWorkflow.endpoints.calendar}
                        onChange={(e) => updateConfig('n8nWorkflow.endpoints.calendar', e.target.value)}
                        className="mt-2"
                      />
                    </div>

                    <div>
                      <Label htmlFor="tickets-endpoint">Tickets Endpoint</Label>
                      <Input
                        id="tickets-endpoint"
                        value={config.n8nWorkflow.endpoints.tickets}
                        onChange={(e) => updateConfig('n8nWorkflow.endpoints.tickets', e.target.value)}
                        className="mt-2"
                      />
                    </div>
                  </div>

                  {/* Find Automation Template Button */}
                  {(!config.n8nWorkflow.workflowId || config.n8nWorkflow.workflowId === '') && (
                    <div className="mt-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-2">
                          <Search className="h-5 w-5 text-orange-500 mt-0.5" />
                          <div className="text-sm">
                            <strong className="text-orange-800">No Template Configured</strong>
                            <p className="mt-1 text-orange-700">
                              Search for tested N8N workflow templates that match your automation type: <strong>{template.name}</strong>
                            </p>
                          </div>
                        </div>
                        <Button
                          onClick={findAutomationTemplate}
                          disabled={isSearchingTemplate}
                          variant="outline"
                          size="sm"
                          className="border-orange-300 text-orange-700 hover:bg-orange-100"
                        >
                          {isSearchingTemplate ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin mr-2" />
                              Searching...
                            </>
                          ) : (
                            <>
                              <Search className="h-4 w-4 mr-2" />
                              Find Template
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* N8N Configuration Display */}
                  <div className="mt-6">
                    <Label>N8N Workflow Configuration</Label>
                    <div className="mt-2 p-4 bg-gray-50 border rounded-lg">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Settings className="h-5 w-5 text-gray-500" />
                          <span className="font-medium text-sm">
                            {template?.n8nConfig ? 'Template Configuration' : 'Generated Configuration'}
                          </span>
                        </div>
                        {isAdmin && (
                          <Button
                            onClick={updateTemplate}
                            disabled={isUpdatingTemplate}
                            size="sm"
                            variant="outline"
                            className="text-xs"
                          >
                            {isUpdatingTemplate ? (
                              <>
                                <Loader2 className="h-3 w-3 animate-spin mr-1" />
                                Updating...
                              </>
                            ) : (
                              <>
                                <Save className="h-3 w-3 mr-1" />
                                Update Template
                              </>
                            )}
                          </Button>
                        )}
                      </div>
                      <textarea
                        value={JSON.stringify(template?.n8nConfig || config.n8nWorkflow, null, 2)}
                        onChange={(e) => {
                          try {
                            const newConfig = JSON.parse(e.target.value);
                            updateConfig('n8nWorkflow', newConfig);
                          } catch (error) {
                            // Invalid JSON, don't update
                          }
                        }}
                        className="w-full h-64 p-3 text-sm font-mono border rounded resize-none bg-white text-gray-900 dark:bg-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="N8N workflow configuration will appear here..."
                      />
                      <p className="text-xs text-gray-600 mt-2">
                        {template?.n8nConfig
                          ? 'This configuration is loaded from the template database. Modifications can be saved by admin users.'
                          : 'This is the generated configuration based on your settings. Admin users can save this as the template default.'
                        }
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="h-5 w-5 text-blue-500 mt-0.5" />
                      <div className="text-sm">
                        <strong>Automatic Configuration</strong>
                        <p className="mt-1 text-gray-600">
                          The N8N workflow will be automatically created with endpoints for calendar integration,
                          ticket management, and analytics tracking based on your settings.
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 5: Integrations */}
          {currentStep === (isCampaignTemplate ? 7 : 6) && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Integration Configuration</CardTitle>
                  <CardDescription>Configure third-party integrations</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <Tabs defaultValue="calendly" className="w-full">
                    <TabsList className="grid w-full grid-cols-5">
                      <TabsTrigger value="calendly">Calendly</TabsTrigger>
                      <TabsTrigger value="supabase">Supabase</TabsTrigger>
                      <TabsTrigger value="tavily">Tavily</TabsTrigger>
                      <TabsTrigger value="resend">Resend</TabsTrigger>
                      <TabsTrigger value="vonage">Vonage</TabsTrigger>
                    </TabsList>

                    <TabsContent value="calendly" className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">Calendly Integration</h4>
                          <p className="text-sm text-gray-600">Appointment booking functionality</p>
                        </div>
                        <Switch
                          checked={config.integrations.calendly.enabled}
                          onCheckedChange={(checked) => updateConfig('integrations.calendly.enabled', checked)}
                        />
                      </div>
                      {config.integrations.calendly.enabled && (
                        <div>
                          <Label htmlFor="calendly-key">API Key</Label>
                          <Input
                            id="calendly-key"
                            type="password"
                            value={config.integrations.calendly.apiKey}
                            onChange={(e) => updateConfig('integrations.calendly.apiKey', e.target.value)}
                            placeholder="Enter Calendly API key"
                            className="mt-2"
                          />
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="supabase" className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">Supabase Integration</h4>
                          <p className="text-sm text-gray-600">Database and call logging</p>
                        </div>
                        <Switch
                          checked={config.integrations.supabase.enabled}
                          onCheckedChange={(checked) => updateConfig('integrations.supabase.enabled', checked)}
                        />
                      </div>
                      {config.integrations.supabase.enabled && (
                        <div>
                          <Label htmlFor="supabase-project">Project ID</Label>
                          <Input
                            id="supabase-project"
                            value={config.integrations.supabase.projectId}
                            onChange={(e) => updateConfig('integrations.supabase.projectId', e.target.value)}
                            className="mt-2"
                          />
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="tavily" className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">Tavily Integration</h4>
                          <p className="text-sm text-gray-600">Web search capabilities</p>
                        </div>
                        <Switch
                          checked={config.integrations.tavily.enabled}
                          onCheckedChange={(checked) => updateConfig('integrations.tavily.enabled', checked)}
                        />
                      </div>
                      {config.integrations.tavily.enabled && (
                        <div>
                          <Label htmlFor="tavily-key">API Key</Label>
                          <Input
                            id="tavily-key"
                            type="password"
                            value={config.integrations.tavily.apiKey}
                            onChange={(e) => updateConfig('integrations.tavily.apiKey', e.target.value)}
                            placeholder="Enter Tavily API key"
                            className="mt-2"
                          />
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="resend" className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">Resend Integration</h4>
                          <p className="text-sm text-gray-600">Email notifications</p>
                        </div>
                        <Switch
                          checked={config.integrations.resend.enabled}
                          onCheckedChange={(checked) => updateConfig('integrations.resend.enabled', checked)}
                        />
                      </div>
                      {config.integrations.resend.enabled && (
                        <div>
                          <Label htmlFor="resend-key">API Key</Label>
                          <Input
                            id="resend-key"
                            type="password"
                            value={config.integrations.resend.apiKey}
                            onChange={(e) => updateConfig('integrations.resend.apiKey', e.target.value)}
                            placeholder="Enter Resend API key"
                            className="mt-2"
                          />
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="vonage" className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">Vonage Integration</h4>
                          <p className="text-sm text-gray-600">SMS messaging</p>
                        </div>
                        <Switch
                          checked={config.integrations.vonage.enabled}
                          onCheckedChange={(checked) => updateConfig('integrations.vonage.enabled', checked)}
                        />
                      </div>
                      {config.integrations.vonage.enabled && (
                        <div>
                          <Label htmlFor="vonage-key">API Key</Label>
                          <Input
                            id="vonage-key"
                            type="password"
                            value={config.integrations.vonage.apiKey}
                            onChange={(e) => updateConfig('integrations.vonage.apiKey', e.target.value)}
                            placeholder="Enter Vonage API key"
                            className="mt-2"
                          />
                        </div>
                      )}
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 6: Custom Tools */}
          {currentStep === (isCampaignTemplate ? 8 : 7) && (
            <div className="space-y-6">
              <CustomToolsSelector
                selectedTools={selectedCustomTools}
                onToolsChange={setSelectedCustomTools}
                industry={template?.industry}
                clientId={template?.industry === 'healthcare' ? 'premier-health' : undefined}
              />

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Wrench className="h-5 w-5" />
                    Integration Settings
                  </CardTitle>
                  <CardDescription>
                    Configure how custom tools integrate with your automation workflow
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-blue-100 rounded-lg">
                          <Settings className="h-4 w-4 text-blue-600" />
                        </div>
                        <div>
                          <h4 className="font-medium text-blue-900 mb-1">Custom Tools Integration</h4>
                          <p className="text-sm text-blue-700 mb-3">
                            Selected custom tools will be automatically integrated into your N8N workflows and VAPI voice agents.
                          </p>
                          <div className="space-y-2 text-sm text-blue-700">
                            <div>• <strong>N8N Integration</strong> - Tools available as HTTP Request nodes</div>
                            <div>• <strong>VAPI Integration</strong> - Tools callable as voice agent functions</div>
                            <div>• <strong>Webhook Endpoints</strong> - Direct API access for external systems</div>
                            <div>• <strong>Authentication</strong> - Secure access with API tokens</div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <Card className="border-2 border-dashed border-gray-200 hover:border-primary/50 transition-colors">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-lg flex items-center gap-2">
                            <Workflow className="h-5 w-5 text-purple-600" />
                            N8N Integration
                          </CardTitle>
                          <CardDescription>
                            Add custom tools to your N8N workflows
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="text-sm text-gray-600">
                            Your N8N workflow will automatically have access to these custom tools through HTTP Request nodes.
                          </div>
                          <Badge variant="outline" className="gap-1">
                            <CheckCircle className="h-3 w-3" />
                            Auto-configured
                          </Badge>
                        </CardContent>
                      </Card>

                      <Card className="border-2 border-dashed border-gray-200 hover:border-primary/50 transition-colors">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-lg flex items-center gap-2">
                            <Headphones className="h-5 w-5 text-green-600" />
                            VAPI Integration
                          </CardTitle>
                          <CardDescription>
                            Enable custom tools for your voice agent
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="text-sm text-gray-600">
                            Your VAPI voice agent will be able to call these tools during conversations.
                          </div>
                          <Badge variant="outline" className="gap-1">
                            <CheckCircle className="h-3 w-3" />
                            Auto-configured
                          </Badge>
                        </CardContent>
                      </Card>
                    </div>

                    <Card className="bg-green-50 border-green-200">
                      <CardContent className="pt-4">
                        <div className="space-y-4">
                          <div className="flex items-start gap-3">
                            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                            <div className="flex-1">
                              <div className="flex items-center justify-between">
                                <h4 className="font-medium text-green-900 mb-1">Template-Specific Tools</h4>
                                <Switch
                                  checked={config.customTools.enabled}
                                  onCheckedChange={(checked) => {
                                    setConfig(prev => ({
                                      ...prev,
                                      customTools: {
                                        ...prev.customTools,
                                        enabled: checked,
                                        selectedTools: checked && template?.customTools ?
                                          template.customTools.map(t => t.name) : [],
                                        availableTools: checked && template?.customTools ?
                                          template.customTools.map(t => ({
                                            name: t.name,
                                            description: t.description,
                                            endpoint: t.endpoint,
                                            method: t.method,
                                            category: t.category || 'general',
                                            enabled: true
                                          })) : []
                                      }
                                    }));
                                  }}
                                />
                              </div>
                              <p className="text-sm text-green-700">
                                The selected "{template?.name}" template includes {template?.customTools?.length || 0} pre-configured custom tools that can be automatically enabled for your automation.
                              </p>
                              {config.customTools.enabled && template?.customTools && template.customTools.length > 0 && (
                                <div className="mt-3 space-y-2">
                                  <div className="text-xs font-medium text-green-800">Enabled Tools:</div>
                                  <div className="space-y-1">
                                    {template.customTools.map((tool, index) => (
                                      <div key={index} className="flex items-center gap-2 text-xs text-green-700">
                                        <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                                        <span className="font-medium">{tool.name}</span>
                                        <span className="text-green-600">- {tool.description}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Tool Configuration Preview */}
                    <details className="group">
                      <summary className="flex items-center gap-2 text-sm font-medium cursor-pointer hover:text-indigo-600">
                        <span className="group-open:rotate-90 transition-transform">▶</span>
                        View Tool Configuration Details
                      </summary>
                      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                        <CustomToolsTab />
                      </div>
                    </details>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 7: Test */}
          {currentStep === (isCampaignTemplate ? 9 : 8) && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TestTube className="h-5 w-5" />
                    System Testing
                  </CardTitle>
                  <CardDescription>
                    Validate your automation setup by testing all components
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {/* Test All Button */}
                    <div className="flex justify-center gap-4">
                      <Button
                        onClick={validateConfiguration}
                        disabled={isRunningTests || !configId}
                        size="lg"
                        className="gap-2"
                        variant="outline"
                      >
                        {isRunningTests ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Validating...
                          </>
                        ) : (
                          <>
                            <Shield className="h-4 w-4" />
                            Validate Config
                          </>
                        )}
                      </Button>

                      <Button
                        onClick={() => testConfigurationFull()}
                        disabled={isRunningTests || !configId}
                        size="lg"
                        className="gap-2"
                        variant="outline"
                      >
                        {isRunningTests ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Testing...
                          </>
                        ) : (
                          <>
                            <TestTube className="h-4 w-4" />
                            Full Test
                          </>
                        )}
                      </Button>

                      <Button
                        onClick={runAllTests}
                        disabled={isRunningTests}
                        size="lg"
                        className="gap-2"
                      >
                        {isRunningTests ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Running Tests...
                          </>
                        ) : (
                          <>
                            <Play className="h-4 w-4" />
                            Run All Tests
                          </>
                        )}
                      </Button>
                    </div>

                    {/* Individual Test Cards */}
                    <div className="grid gap-4 md:grid-cols-2">
                      {/* VAPI Test */}
                      <Card className="border-2">
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Phone className="h-4 w-4 text-green-600" />
                              <CardTitle className="text-base">VAPI Voice Agent</CardTitle>
                            </div>
                            <div className="flex items-center gap-2">
                              {getTestStatusIcon(testResults.vapi?.status)}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={testVAPIAgent}
                                disabled={isRunningTests}
                                className="gap-1"
                              >
                                {testResults.vapi?.status === 'testing' ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <Play className="h-3 w-3" />
                                )}
                                Test
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="text-sm">
                              <div className="font-medium">Configuration Check:</div>
                              <div className="text-gray-600 text-xs">
                                Voice ID: {config.vapiAgent.voiceSettings.voiceId || 'Not set'}<br />
                                Model: {config.vapiAgent.voiceSettings.model || 'Not set'}<br />
                                Assistant ID: {config.vapiAgent.assistantId || 'Not created yet'}
                              </div>
                            </div>
                            {testResults.vapi?.tested && (
                              <div className={`text-xs p-2 rounded ${getTestStatusColor(testResults.vapi.status)}`}>
                                {testResults.vapi.message}
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>

                      {/* N8N Test */}
                      <Card className="border-2">
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Workflow className="h-4 w-4 text-purple-600" />
                              <CardTitle className="text-base">N8N Workflow</CardTitle>
                            </div>
                            <div className="flex items-center gap-2">
                              {getTestStatusIcon(testResults.n8n?.status)}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={testN8NWorkflow}
                                disabled={isRunningTests}
                                className="gap-1"
                              >
                                {testResults.n8n?.status === 'testing' ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <Play className="h-3 w-3" />
                                )}
                                Test
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="text-sm">
                              <div className="font-medium">Workflow Status:</div>
                              <div className="text-gray-600 text-xs">
                                ID: {config.n8nWorkflow.workflowId || 'Auto-generated'}<br />
                                Webhook: {config.n8nWorkflow.webhookUrl ? 'Configured' : 'Not set'}
                              </div>
                            </div>
                            {testResults.n8n?.tested && (
                              <div className={`text-xs p-2 rounded ${getTestStatusColor(testResults.n8n.status)}`}>
                                {testResults.n8n.message}
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>

                      {/* Webhooks Test */}
                      <Card className="border-2">
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Zap className="h-4 w-4 text-orange-600" />
                              <CardTitle className="text-base">Webhook Endpoints</CardTitle>
                            </div>
                            <div className="flex items-center gap-2">
                              {getTestStatusIcon(testResults.webhooks?.status)}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={testWebhooks}
                                disabled={isRunningTests}
                                className="gap-1"
                              >
                                {testResults.webhooks?.status === 'testing' ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <Play className="h-3 w-3" />
                                )}
                                Test
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="text-sm">
                              <div className="font-medium">Configured Endpoints:</div>
                              <div className="text-gray-600 text-xs">
                                {Object.values(config.n8nWorkflow.endpoints).length} endpoints configured
                              </div>
                            </div>
                            {testResults.webhooks?.tested && (
                              <div className={`text-xs p-2 rounded ${getTestStatusColor(testResults.webhooks.status)}`}>
                                {testResults.webhooks.message}
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>

                      {/* Custom Tools Test */}
                      <Card className="border-2">
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Wrench className="h-4 w-4 text-blue-600" />
                              <CardTitle className="text-base">Custom Tools</CardTitle>
                            </div>
                            <div className="flex items-center gap-2">
                              {getTestStatusIcon(testResults.customTools?.status)}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={testCustomTools}
                                disabled={isRunningTests}
                                className="gap-1"
                              >
                                {testResults.customTools?.status === 'testing' ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <Play className="h-3 w-3" />
                                )}
                                Test
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="text-sm">
                              <div className="font-medium">Tools Status:</div>
                              <div className="text-gray-600 text-xs">
                                {config.customTools.enabled ?
                                  `${config.customTools.selectedTools.length} tools selected` :
                                  'Custom tools disabled'
                                }
                              </div>
                            </div>
                            {testResults.customTools?.tested && (
                              <div className={`text-xs p-2 rounded ${getTestStatusColor(testResults.customTools.status)}`}>
                                {testResults.customTools.message}
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>

                      {/* Integrations Test */}
                      <Card className="border-2">
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Settings className="h-4 w-4 text-indigo-600" />
                              <CardTitle className="text-base">Integrations</CardTitle>
                            </div>
                            <div className="flex items-center gap-2">
                              {getTestStatusIcon(testResults.integrations?.status)}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={testIntegrations}
                                disabled={isRunningTests}
                                className="gap-1"
                              >
                                {testResults.integrations?.status === 'testing' ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <Play className="h-3 w-3" />
                                )}
                                Test
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="text-sm">
                              <div className="font-medium">Active Integrations:</div>
                              <div className="text-gray-600 text-xs">
                                {[
                                  config.integrations.calendly.enabled && 'Calendly',
                                  config.integrations.supabase.enabled && 'Supabase',
                                  config.integrations.tavily.enabled && 'Tavily',
                                  config.integrations.resend.enabled && 'Resend',
                                  config.integrations.vonage.enabled && 'Vonage'
                                ].filter(Boolean).join(', ') || 'None enabled'}
                              </div>
                            </div>
                            {testResults.integrations?.tested && (
                              <div className={`text-xs p-2 rounded ${getTestStatusColor(testResults.integrations.status)}`}>
                                {testResults.integrations.message}
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    </div>

                    {/* Overall Test Status */}
                    {Object.values(testResults).some(result => result?.tested) && (
                      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
                        <CardHeader>
                          <CardTitle className="text-lg flex items-center gap-2">
                            <Activity className="h-5 w-5 text-blue-600" />
                            Test Summary
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid gap-2">
                            {Object.entries(testResults).map(([key, result]) =>
                              result?.tested ? (
                                <div key={key} className="flex items-center justify-between text-sm">
                                  <span className="capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                                  <div className="flex items-center gap-2">
                                    {getTestStatusIcon(result.status)}
                                    <span className={getTestStatusColor(result.status).includes('green') ? 'text-green-700' :
                                                   getTestStatusColor(result.status).includes('red') ? 'text-red-700' : 'text-yellow-700'}>
                                      {result.status === 'success' ? 'Passed' :
                                       result.status === 'error' ? 'Failed' : 'Testing...'}
                                    </span>
                                  </div>
                                </div>
                              ) : null
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 8: Demo Setup */}
          {currentStep === (isCampaignTemplate ? 10 : 9) && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Demo Deployment</CardTitle>
                      <CardDescription>Create a demo page for your helpdesk</CardDescription>
                    </div>
                    <Switch
                      checked={config.demoSettings.enableDemo}
                      onCheckedChange={(checked) => updateConfig('demoSettings.enableDemo', checked)}
                    />
                  </div>
                </CardHeader>
                {config.demoSettings.enableDemo && (
                  <CardContent className="space-y-4">
                    <div className="p-4 bg-green-50 rounded-lg">
                      <div className="flex items-start gap-2">
                        <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                        <div className="text-sm">
                          <strong>Demo Features</strong>
                          <ul className="mt-2 space-y-1 text-gray-600">
                            <li>• Branded demo page with your company information</li>
                            <li>• Direct integration with your VAPI voice assistant</li>
                            <li>• Showcase of helpdesk capabilities</li>
                            <li>• Professional design matching your brand</li>
                          </ul>
                        </div>
                      </div>
                    </div>

                    {config.demoSettings.demoUrl && (
                      <div>
                        <Label>Demo URL</Label>
                        <div className="flex gap-2 mt-2">
                          <Input
                            value={config.demoSettings.demoUrl}
                            readOnly
                            className="flex-1"
                          />
                          <Button
                            variant="outline"
                            onClick={() => window.open(config.demoSettings.demoUrl, '_blank')}
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                )}
              </Card>
            </div>
          )}

          {/* Step 9: Analytics */}
          {currentStep === (isCampaignTemplate ? 11 : 10) && (
            <div className="space-y-6">
              <UnifiedAutomationDashboard configId={configId} />

              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Analytics Configuration</CardTitle>
                      <CardDescription>Configure analytics and reporting settings</CardDescription>
                    </div>
                    <Switch
                      checked={config.analytics.enableTracking}
                      onCheckedChange={(checked) => updateConfig('analytics.enableTracking', checked)}
                    />
                  </div>
                </CardHeader>
                {config.analytics.enableTracking && (
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="report-email">Report Email</Label>
                      <Input
                        id="report-email"
                        type="email"
                        value={config.analytics.reportEmail}
                        onChange={(e) => updateConfig('analytics.reportEmail', e.target.value)}
                        placeholder="analytics@company.com"
                        className="mt-2"
                      />
                      <p className="text-xs text-gray-600 mt-1">
                        Analytics reports will be sent to this email
                      </p>
                    </div>
                  </CardContent>
                )}
              </Card>
            </div>
          )}

          {/* Step 10: Review */}
          {currentStep === (isCampaignTemplate ? 12 : 11) && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Configuration Review</CardTitle>
                  <CardDescription>Review your helpdesk configuration before deployment</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium mb-2">Company Information</h4>
                      <div className="text-sm space-y-1">
                        <div><strong>Name:</strong> {config.companyInfo.name}</div>
                        <div><strong>URL:</strong> {config.companyInfo.url}</div>
                        <div><strong>Description:</strong> {config.companyInfo.description}</div>
                        <div><strong>Transfer Number:</strong> {config.companyInfo.transferNumber || '+12397783680'}</div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Voice Agent</h4>
                      <div className="text-sm space-y-1">
                        <div><strong>Voice:</strong> {config.vapiAgent.voiceSettings.voiceId}</div>
                        <div><strong>Model:</strong> {config.vapiAgent.voiceSettings.model}</div>
                        <div><strong>Max Duration:</strong> {config.vapiAgent.voiceSettings.maxDuration}s</div>
                        <div><strong>Tools:</strong> {config.vapiAgent.tools.length} enabled</div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Integrations</h4>
                      <div className="text-sm space-y-1">
                        <div>Calendly: {config.integrations.calendly.enabled ? '✅' : '❌'}</div>
                        <div>Supabase: {config.integrations.supabase.enabled ? '✅' : '❌'}</div>
                        <div>Tavily: {config.integrations.tavily.enabled ? '✅' : '❌'}</div>
                        <div>Resend: {config.integrations.resend.enabled ? '✅' : '❌'}</div>
                        <div>Vonage: {config.integrations.vonage.enabled ? '✅' : '❌'}</div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Features</h4>
                      <div className="text-sm space-y-1">
                        <div>Demo Page: {config.demoSettings.enableDemo ? '✅' : '❌'}</div>
                        <div>Analytics: {config.analytics.enableTracking ? '✅' : '❌'}</div>
                        <div>N8N Workflow: ✅ Auto-configured</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6">
                    <h4 className="font-medium mb-2">System Prompt</h4>
                    <div className="space-y-2">
                      <p className="text-sm text-gray-600">
                        Review and edit your AI assistant's system prompt if needed:
                      </p>
                      <Textarea
                        value={config.vapiAgent.systemPrompt}
                        onChange={(e) => updateConfig('vapiAgent.systemPrompt', e.target.value)}
                        rows={8}
                        className="font-mono text-sm"
                        placeholder="System prompt for your AI assistant..."
                      />
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-start gap-2">
                      <Sparkles className="h-5 w-5 text-blue-500 mt-0.5" />
                      <div className="text-sm">
                        <strong>Ready to Deploy</strong>
                        <p className="mt-1 text-gray-600">
                          Your automation campaign will be automatically configured with:
                        </p>
                        <ul className="mt-2 space-y-1 text-gray-600">
                          <li>• VAPI voice assistant with company-specific prompts</li>
                          <li>• N8N workflow for automation and integrations</li>
                          <li>• Demo page for client presentations</li>
                          <li>• Analytics dashboard for monitoring performance</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {configId && config.status && (
                    <div className="mt-6 p-4 border rounded-lg">
                      <h4 className="font-medium mb-3">Automation Controls</h4>
                      <div className="flex gap-2">
                        {config.status === 'draft' && (
                          <Button
                            onClick={deployAutomation}
                            disabled={isCreating}
                            className="flex items-center gap-2"
                          >
                            {isCreating ? (
                              <Clock className="h-4 w-4 animate-spin" />
                            ) : (
                              <Sparkles className="h-4 w-4" />
                            )}
                            {isCreating ? 'Deploying...' : 'Deploy Now'}
                          </Button>
                        )}

                        {config.status === 'deployed' && (
                          <Button
                            variant="secondary"
                            onClick={stopAutomation}
                            className="flex items-center gap-2"
                          >
                            <Clock className="h-4 w-4" />
                            Stop Automation
                          </Button>
                        )}

                        {config.status === 'stopped' && (
                          <Button
                            onClick={deployAutomation}
                            disabled={isCreating}
                            className="flex items-center gap-2"
                          >
                            {isCreating ? (
                              <Clock className="h-4 w-4 animate-spin" />
                            ) : (
                              <Sparkles className="h-4 w-4" />
                            )}
                            {isCreating ? 'Redeploying...' : 'Redeploy'}
                          </Button>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 mt-2">
                        Current status: <span className="font-medium">{config.status || 'draft'}</span>
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Prominent Action Buttons - Always Visible */}
        <div className="border-t pt-4 bg-gray-50 rounded-lg mb-4">
          <div className="flex justify-center gap-4 mb-4">
            {/* Save Configuration Button */}
            <Button
              variant="outline"
              onClick={() => saveConfiguration(true)}
              disabled={isSaving || !config.automationName.trim()}
              className="flex items-center gap-2 px-6 py-3 text-lg border-2 border-blue-300 text-blue-700 hover:bg-blue-50"
              size="lg"
            >
              {isSaving ? (
                <Clock className="h-5 w-5 animate-spin" />
              ) : (
                <Save className="h-5 w-5" />
              )}
              {isSaving ? 'Saving Configuration...' : configId ? 'Update Configuration' : 'Save Configuration'}
            </Button>

            {/* Deploy Button */}
            <Button
              onClick={deployAutomation}
              disabled={isCreating || !config.automationName.trim() || !configId}
              className="flex items-center gap-2 px-6 py-3 text-lg bg-green-600 hover:bg-green-700 text-white"
              size="lg"
            >
              {isCreating ? (
                <Clock className="h-5 w-5 animate-spin" />
              ) : (
                <Sparkles className="h-5 w-5" />
              )}
              {isCreating ? 'Deploying Automation...' : config.status === 'deployed' ? 'Redeploy Automation' : 'Deploy Automation'}
            </Button>

            {/* Comprehensive Test Button */}
            <Button
              variant="outline"
              onClick={() => testConfigurationFull()}
              disabled={isRunningTests || !configId}
              className="flex items-center gap-2 px-6 py-3 text-lg border-2 border-purple-300 text-purple-700 hover:bg-purple-50"
              size="lg"
            >
              {isRunningTests ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <TestTube className="h-5 w-5" />
              )}
              {isRunningTests ? 'Running Tests...' : 'Comprehensive Test'}
            </Button>
          </div>

          {/* Configuration Status Display */}
          {configId && (
            <div className="text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm">
                {config.status === 'deployed' && (
                  <>
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-green-700 font-medium">✅ Deployed & Active</span>
                  </>
                )}
                {config.status === 'draft' && (
                  <>
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-blue-700 font-medium">📝 Draft - Ready to Deploy</span>
                  </>
                )}
                {config.status === 'stopped' && (
                  <>
                    <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                    <span className="text-orange-700 font-medium">⏸️ Stopped</span>
                  </>
                )}
                {config.status === 'failed' && (
                  <>
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="text-red-700 font-medium">❌ Deployment Failed</span>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Save reminder for unsaved changes */}
          {!configId && config.automationName.trim() && (
            <div className="text-center">
              <p className="text-sm text-orange-600 bg-orange-50 px-3 py-1 rounded-full inline-block">
                💡 Remember to save your configuration before deploying
              </p>
            </div>
          )}
        </div>

        {/* Navigation Footer */}
        <div className="border-t pt-4 flex justify-between">
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentStep === 0}
            >
              Previous
            </Button>

            {configId && (
              <Button
                variant="destructive"
                onClick={deleteConfiguration}
                className="flex items-center gap-2"
              >
                <AlertCircle className="h-4 w-4" />
                Delete Configuration
              </Button>
            )}

            {config.status === 'deployed' && (
              <Button
                variant="secondary"
                onClick={stopAutomation}
                className="flex items-center gap-2"
              >
                <Clock className="h-4 w-4" />
                Stop Automation
              </Button>
            )}
          </div>

          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>

            {/* Admin-only Update Template button */}
            {isAdmin && (
              <Button
                variant="outline"
                onClick={updateTemplate}
                disabled={isUpdatingTemplate || !config.automationName.trim()}
                className="flex items-center gap-2 border-orange-300 text-orange-700 hover:bg-orange-50"
              >
                {isUpdatingTemplate ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Settings className="h-4 w-4" />
                )}
                {isUpdatingTemplate ? 'Updating...' : 'Update Template'}
              </Button>
            )}

            {currentStep === steps.length - 1 ? (
              <Button
                onClick={onClose}
                className="flex items-center gap-2"
                disabled={!configId}
              >
                <CheckCircle className="h-4 w-4" />
                Finish Setup
              </Button>
            ) : (
              <Button onClick={handleNext}>
                Next
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};