import React, { useState, useEffect } from 'react';
import { X, Globe, Wand2, Phone, Settings, Zap, Calendar, Mail, Database, Bot, ExternalLink, Copy, CheckCircle, AlertCircle, Loader2, Plus, Minus, Upload, FileText, Trash2, ChevronDown, ChevronRight, Code, MessageSquare, ShoppingCart, CreditCard, Video, FileIcon, Calculator } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { getAuthHeaders } from '@/lib/auth-utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useConfirmationHelpers } from '@/hooks/use-confirmation';
import { SystemPromptGenerator } from '@/components/shared/SystemPromptGenerator';

interface CreateVapiAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAgentCreated: () => void;
  apiBaseUrl: string;
}

interface Integration {
  id: string;
  name: string;
  category: string;
  icon: string;
  isConfigured: boolean;
  description: string;
}

interface ToolCategory {
  id: string;
  name: string;
  icon: string;
  description: string;
  tools: Tool[];
}

interface Tool {
  id: string;
  name: string;
  description: string;
  icon: string;
  isConfigured?: boolean;
  isCustom?: boolean;
  webhook_url?: string;
}

interface VapiAgentConfig {
  // Basic Info
  name: string;
  description: string;
  agentType: string;
  
  // System Prompt
  systemPrompt: string;
  promptSource: 'manual' | 'website' | 'template';
  websiteUrl: string;
  
  // Knowledge Base / Documents
  uploadedFiles: Array<{
    id: string;
    name: string;
    size: number;
    type: string;
    url?: string;
    uploadStatus: 'pending' | 'uploading' | 'uploaded' | 'failed';
  }>;
  enableKnowledgeBase: boolean;
  
  // VAPI Configuration
  vapiPhoneId: string;
  vapiAssistantId?: string;
  callType: 'inbound' | 'outbound' | 'both';
  
  // Voice Settings
  voice: string;
  language: string;
  speed: number;
  
  // Integrations & Tools
  selectedIntegrations: string[];
  customTools: Array<{
    name: string;
    description: string;
    webhook_url: string;
  }>;
  
  // Advanced Settings
  maxDuration: number;
  silenceTimeout: number;
  interruptible: boolean;
  recordCalls: boolean;
  
  // Webhook Settings
  webhookUrl?: string;
  enableWebhooks: boolean;
}

const AGENT_TYPES = [
  { id: 'helpdesk', name: 'Helpdesk Agent', description: 'Customer support and troubleshooting', icon: '🛠️' },
  { id: 'sales', name: 'Sales Agent', description: 'Lead qualification and sales conversations', icon: '💼' },
  { id: 'political', name: 'Political Campaign', description: 'Voter outreach and campaign assistance', icon: '🗳️' },
  { id: 'church', name: 'Church Follow-up', description: 'Member engagement and pastoral care', icon: '⛪' },
  { id: 'survey', name: 'Survey Assistant', description: 'Data collection and research', icon: '📋' },
  { id: 'appointment', name: 'Appointment Booking', description: 'Schedule and manage appointments', icon: '📅' },
  { id: 'lead_gen', name: 'Lead Generation', description: 'Prospect identification and qualification', icon: '🎯' },
  { id: 'education', name: 'Educational Assistant', description: 'Student support and tutoring', icon: '🎓' },
  { id: 'healthcare', name: 'Healthcare Assistant', description: 'Patient support and health information', icon: '🏥' },
  { id: 'custom', name: 'Custom Agent', description: 'Build your own specialized agent', icon: '⚙️' }
];

const VOICE_OPTIONS = [
  { id: 'alloy', name: 'Alloy', description: 'Clear and professional', preview: 'https://platform.openai.com/docs/guides/text-to-speech' },
  { id: 'echo', name: 'Echo', description: 'Warm and engaging', preview: '' },
  { id: 'fable', name: 'Fable', description: 'Storytelling voice', preview: '' },
  { id: 'onyx', name: 'Onyx', description: 'Deep and authoritative', preview: '' },
  { id: 'nova', name: 'Nova', description: 'Energetic and youthful', preview: '' },
  { id: 'shimmer', name: 'Shimmer', description: 'Gentle and soothing', preview: '' }
];

const LANGUAGE_OPTIONS = [
  { id: 'en', name: 'English', flag: '🇺🇸' },
  { id: 'es', name: 'Spanish', flag: '🇪🇸' },
  { id: 'fr', name: 'French', flag: '🇫🇷' },
  { id: 'de', name: 'German', flag: '🇩🇪' },
  { id: 'it', name: 'Italian', flag: '🇮🇹' },
  { id: 'pt', name: 'Portuguese', flag: '🇵🇹' },
  { id: 'nl', name: 'Dutch', flag: '🇳🇱' },
  { id: 'pl', name: 'Polish', flag: '🇵🇱' },
  { id: 'ru', name: 'Russian', flag: '🇷🇺' },
  { id: 'ja', name: 'Japanese', flag: '🇯🇵' },
  { id: 'ko', name: 'Korean', flag: '🇰🇷' },
  { id: 'zh', name: 'Chinese', flag: '🇨🇳' }
];

const AVAILABLE_TOOL_CATEGORIES: ToolCategory[] = [
  {
    id: 'communication',
    name: 'Communication',
    icon: '💬',
    description: 'Tools for messaging, emails, and notifications',
    tools: [
      { id: 'email', name: 'Email', description: 'Send emails via configured providers', icon: '📧' },
      { id: 'sms', name: 'SMS', description: 'Send text messages', icon: '📱' },
      { id: 'slack', name: 'Slack', description: 'Send Slack messages', icon: '📞' },
      { id: 'discord', name: 'Discord', description: 'Discord bot integration', icon: '🎮' },
      { id: 'whatsapp', name: 'WhatsApp', description: 'WhatsApp Business API', icon: '💚' },
    ]
  },
  {
    id: 'calendar',
    name: 'Calendar & Scheduling',
    icon: '📅',
    description: 'Appointment booking and calendar management',
    tools: [
      { id: 'google_calendar', name: 'Google Calendar', description: 'Schedule Google Calendar events', icon: '🗓️' },
      { id: 'outlook', name: 'Outlook Calendar', description: 'Microsoft Outlook integration', icon: '📅' },
      { id: 'calendly', name: 'Calendly', description: 'Calendly booking links', icon: '⏰' },
      { id: 'acuity', name: 'Acuity Scheduling', description: 'Acuity appointment booking', icon: '📋' },
    ]
  },
  {
    id: 'crm',
    name: 'CRM & Sales',
    icon: '🤝',
    description: 'Customer relationship and sales management',
    tools: [
      { id: 'hubspot', name: 'HubSpot', description: 'HubSpot CRM integration', icon: '🧡' },
      { id: 'salesforce', name: 'Salesforce', description: 'Salesforce CRM', icon: '☁️' },
      { id: 'pipedrive', name: 'Pipedrive', description: 'Pipedrive CRM', icon: '🔄' },
      { id: 'freshsales', name: 'Freshsales', description: 'Freshworks CRM', icon: '🌿' },
    ]
  },
  {
    id: 'payments',
    name: 'Payments & Commerce',
    icon: '💳',
    description: 'Payment processing and e-commerce',
    tools: [
      { id: 'stripe', name: 'Stripe', description: 'Process payments via Stripe', icon: '💎' },
      { id: 'paypal', name: 'PayPal', description: 'PayPal payment processing', icon: '💰' },
      { id: 'square', name: 'Square', description: 'Square payment terminal', icon: '⬜' },
      { id: 'shopify', name: 'Shopify', description: 'Shopify store integration', icon: '🛍️' },
    ]
  },
  {
    id: 'data',
    name: 'Data & Analytics',
    icon: '📊',
    description: 'Database access and analytics tools',
    tools: [
      { id: 'google_sheets', name: 'Google Sheets', description: 'Read/write Google Sheets', icon: '📗' },
      { id: 'airtable', name: 'Airtable', description: 'Airtable database', icon: '🗃️' },
      { id: 'mysql', name: 'MySQL', description: 'MySQL database access', icon: '🐬' },
      { id: 'postgresql', name: 'PostgreSQL', description: 'PostgreSQL database', icon: '🐘' },
      { id: 'mongodb', name: 'MongoDB', description: 'MongoDB database', icon: '🍃' },
    ]
  },
  {
    id: 'productivity',
    name: 'Productivity',
    icon: '⚡',
    description: 'Productivity and workflow automation',
    tools: [
      { id: 'notion', name: 'Notion', description: 'Notion workspace integration', icon: '📝' },
      { id: 'trello', name: 'Trello', description: 'Trello board management', icon: '📋' },
      { id: 'asana', name: 'Asana', description: 'Asana project management', icon: '🎯' },
      { id: 'zapier', name: 'Zapier', description: 'Zapier automation', icon: '⚡' },
    ]
  },
  {
    id: 'ai_tools',
    name: 'AI & ML Tools',
    icon: '🤖',
    description: 'AI and machine learning integrations',
    tools: [
      { id: 'openai', name: 'OpenAI', description: 'OpenAI GPT models', icon: '🧠' },
      { id: 'claude', name: 'Claude', description: 'Anthropic Claude AI', icon: '🎭' },
      { id: 'gemini', name: 'Google Gemini', description: 'Google Gemini AI', icon: '💎' },
      { id: 'midjourney', name: 'Midjourney', description: 'AI image generation', icon: '🎨' },
    ]
  },
  {
    id: 'custom',
    name: 'Custom Tools',
    icon: '🔧',
    description: 'Your custom webhook-based tools',
    tools: [] // This will be populated with user's custom tools
  }
];

export const CreateVapiAgentModal: React.FC<CreateVapiAgentModalProps> = ({
  isOpen,
  onClose,
  onAgentCreated,
  apiBaseUrl
}) => {
  const { toast } = useToast();
  const { confirmCancel, ConfirmationDialog } = useConfirmationHelpers();
  const [currentStep, setCurrentStep] = useState(0);
  const [isCreating, setIsCreating] = useState(false);
  const [isGeneratingPrompt, setIsGeneratingPrompt] = useState(false);
  const [availableIntegrations, setAvailableIntegrations] = useState<Integration[]>([]);
  const [generatedWebhookUrl, setGeneratedWebhookUrl] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [selectedTools, setSelectedTools] = useState<Set<string>>(new Set());
  const [toolCategories, setToolCategories] = useState<ToolCategory[]>(AVAILABLE_TOOL_CATEGORIES);
  
  const [config, setConfig] = useState<VapiAgentConfig>({
    name: '',
    description: '',
    agentType: '',
    systemPrompt: '',
    promptSource: 'manual',
    websiteUrl: '',
    uploadedFiles: [],
    enableKnowledgeBase: false,
    vapiPhoneId: '',
    callType: 'both',
    voice: 'alloy',
    language: 'en',
    speed: 1.0,
    selectedIntegrations: [],
    customTools: [],
    maxDuration: 600,
    silenceTimeout: 10,
    interruptible: true,
    recordCalls: true,
    enableWebhooks: true
  });

  // Load available integrations
  useEffect(() => {
    if (isOpen) {
      loadIntegrations();
      generateWebhookUrl();
    }
  }, [isOpen]);

  const loadIntegrations = async () => {
    try {
      // Load available integrations from account-based API
      const response = await fetch(`${apiBaseUrl}/vapi/integrations/available`, {
        headers: {
          'Authorization': (await getAuthHeaders())['Authorization']
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const mappedIntegrations: Integration[] = data.integrations.map((i: any) => ({
          id: i.id,
          name: i.name,
          category: i.category,
          icon: i.icon || '🔧',
          isConfigured: i.is_configured,
          description: i.description
        }));
        setAvailableIntegrations(mappedIntegrations);
      } else {
        // Fallback to default integrations if API fails
        setAvailableIntegrations([
          {
            id: 'calendar_basic',
            name: 'Basic Calendar',
            category: 'productivity',
            icon: '📅',
            isConfigured: false,
            description: 'Basic calendar functionality for scheduling'
          },
          {
            id: 'email_basic',
            name: 'Basic Email',
            category: 'communication',
            icon: '📧',
            isConfigured: false,
            description: 'Basic email sending functionality'
          }
        ]);
      }
    } catch (error) {
      console.error('Error loading integrations:', error);
      // Set fallback integrations on error
      setAvailableIntegrations([
        {
          id: 'calendar_basic',
          name: 'Basic Calendar',
          category: 'productivity',
          icon: '📅',
          isConfigured: false,
          description: 'Basic calendar functionality for scheduling'
        },
        {
          id: 'email_basic',
          name: 'Basic Email',
          category: 'communication',
          icon: '📧',
          isConfigured: false,
          description: 'Basic email sending functionality'
        }
      ]);
    }
  };

  const generateWebhookUrl = () => {
    const accountId = localStorage.getItem('tenant_id') || 'default';
    const agentId = crypto.randomUUID();
    const webhookUrl = `${apiBaseUrl}/webhooks/vapi/${accountId}/${agentId}`;
    setGeneratedWebhookUrl(webhookUrl);
    setConfig(prev => ({ ...prev, webhookUrl }));
  };


  // Helper functions for tool management
  const toggleCategory = (categoryId: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId);
      } else {
        newSet.add(categoryId);
      }
      return newSet;
    });
  };

  const toggleTool = (toolId: string) => {
    setSelectedTools(prev => {
      const newSet = new Set(prev);
      if (newSet.has(toolId)) {
        newSet.delete(toolId);
      } else {
        newSet.add(toolId);
      }
      return newSet;
    });
  };

  const addCustomTool = () => {
    const customCategory = toolCategories.find(cat => cat.id === 'custom');
    if (customCategory) {
      const newTool: Tool = {
        id: crypto.randomUUID(),
        name: '',
        description: '',
        icon: '🔧',
        isCustom: true,
        webhook_url: ''
      };

      const updatedCategories = toolCategories.map(cat =>
        cat.id === 'custom'
          ? { ...cat, tools: [...cat.tools, newTool] }
          : cat
      );

      setToolCategories(updatedCategories);

      // Auto-expand custom category
      setExpandedCategories(prev => new Set([...prev, 'custom']));
    }
  };

  const updateCustomTool = (toolId: string, field: keyof Tool, value: string) => {
    const updatedCategories = toolCategories.map(cat => ({
      ...cat,
      tools: cat.tools.map(tool =>
        tool.id === toolId ? { ...tool, [field]: value } : tool
      )
    }));
    setToolCategories(updatedCategories);
  };

  const removeCustomTool = (toolId: string) => {
    const updatedCategories = toolCategories.map(cat => ({
      ...cat,
      tools: cat.tools.filter(tool => tool.id !== toolId)
    }));
    setToolCategories(updatedCategories);

    // Also remove from selected tools
    setSelectedTools(prev => {
      const newSet = new Set(prev);
      newSet.delete(toolId);
      return newSet;
    });
  };



  const createVapiAgent = async () => {
    if (!config.name.trim()) {
      toast({
        title: "Name required",
        description: "Please enter a name for your VAPI agent",
        variant: "destructive"
      });
      return;
    }

    if (!config.systemPrompt.trim()) {
      toast({
        title: "System prompt required",
        description: "Please provide a system prompt for your agent",
        variant: "destructive"
      });
      return;
    }

    setIsCreating(true);

    try {
      // Create the VAPI agent configuration
      const vapiAgentData = {
        name: config.name,
        description: config.description,
        agent_type: config.agentType,
        system_prompt: config.systemPrompt,
        
        // VAPI specific settings
        vapi_phone_id: config.vapiPhoneId,
        call_type: config.callType,
        
        // Voice settings
        voice: config.voice,
        language: config.language,
        speed: config.speed,
        
        // Selected tools and integrations
        selected_tools: Array.from(selectedTools),
        tool_configurations: toolCategories.flatMap(cat =>
          cat.tools.filter(tool => selectedTools.has(tool.id))
        ),
        
        // Advanced settings
        max_duration: config.maxDuration,
        silence_timeout: config.silenceTimeout,
        interruptible: config.interruptible,
        record_calls: config.recordCalls,
        
        // Webhook configuration
        webhook_url: config.webhookUrl,
        enable_webhooks: config.enableWebhooks,
        
        // Metadata
        created_with: 'kasaai_platform',
        tenant_id: localStorage.getItem('tenant_id') || 'default',
        created_at: new Date().toISOString()
      };

      // Create agent on VAPI
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${apiBaseUrl}/vapi/agents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders
        },
        body: JSON.stringify(vapiAgentData)
      });

      if (!response.ok) {
        throw new Error(`Failed to create VAPI agent: ${response.statusText}`);
      }

      const newAgent = await response.json();
      
      toast({
        title: "VAPI agent created",
        description: `${newAgent.name} has been created successfully with VAPI integration.`
      });

      onAgentCreated();
      handleClose();
      
    } catch (error) {
      console.error('Error creating VAPI agent:', error);
      toast({
        title: "Failed to create agent",
        description: error instanceof Error ? error.message : "Please try again later.",
        variant: "destructive"
      });
    } finally {
      setIsCreating(false);
    }
  };

  const hasUnsavedChanges = () => {
    return (
      config.name.trim() !== '' ||
      config.description.trim() !== '' ||
      config.agentType !== '' ||
      config.systemPrompt.trim() !== '' ||
      config.websiteUrl.trim() !== '' ||
      config.vapiPhoneId.trim() !== '' ||
      selectedTools.size > 0 ||
      config.uploadedFiles.length > 0 ||
      config.enableKnowledgeBase ||
      currentStep > 0
    );
  };

  const resetForm = () => {
    setCurrentStep(0);
    setIsGeneratingPrompt(false);
    setConfig({
      name: '',
      description: '',
      agentType: '',
      systemPrompt: '',
      promptSource: 'manual',
      websiteUrl: '',
      uploadedFiles: [],
      enableKnowledgeBase: false,
      vapiPhoneId: '',
      callType: 'both',
      voice: 'alloy',
      language: 'en',
      speed: 1.0,
      selectedIntegrations: [],
      customTools: [],
      maxDuration: 600,
      silenceTimeout: 10,
      interruptible: true,
      recordCalls: true,
      enableWebhooks: true
    });
    setGeneratedWebhookUrl('');
    setIsGeneratingPrompt(false);
  };

  const handleClose = async () => {
    if (hasUnsavedChanges() && !isCreating) {
      const confirmed = await confirmCancel();
      if (confirmed) {
        resetForm();
        onClose();
      }
    } else {
      resetForm();
      onClose();
    }
  };


  const copyWebhookUrl = () => {
    navigator.clipboard.writeText(generatedWebhookUrl);
    toast({
      title: "Copied to clipboard",
      description: "Webhook URL has been copied."
    });
  };

  const handleFileUpload = async (files: FileList) => {
    const supportedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'text/csv',
      'text/markdown',
      'application/json',
      'text/xml'
    ];

    for (const file of Array.from(files)) {
      if (!supportedTypes.includes(file.type)) {
        toast({
          title: "Unsupported file type",
          description: `${file.name} is not a supported file type. Supported: PDF, Word, TXT, CSV, Markdown, JSON, XML`,
          variant: "destructive"
        });
        continue;
      }

      if (file.size > 300 * 1024) { // 300KB limit
        toast({
          title: "File too large",
          description: `${file.name} exceeds the 300KB limit. Please use a smaller file.`,
          variant: "destructive"
        });
        continue;
      }

      const fileId = Math.random().toString(36).substr(2, 9);
      const newFile = {
        id: fileId,
        name: file.name,
        size: file.size,
        type: file.type,
        uploadStatus: 'uploading' as const
      };

      // Add file to the list with uploading status
      setConfig(prev => ({
        ...prev,
        uploadedFiles: [...prev.uploadedFiles, newFile]
      }));

      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${apiBaseUrl}/vapi/upload-file`, {
          method: 'POST',
          headers: {
            'Authorization': (await getAuthHeaders())['Authorization']
          },
          body: formData
        });

        if (!response.ok) {
          throw new Error('Upload failed');
        }

        const result = await response.json();

        // Update file status to uploaded
        setConfig(prev => ({
          ...prev,
          uploadedFiles: prev.uploadedFiles.map(f => 
            f.id === fileId 
              ? { ...f, uploadStatus: 'uploaded', url: result.url }
              : f
          )
        }));

        toast({
          title: "File uploaded",
          description: `${file.name} uploaded successfully.`
        });

      } catch (error) {
        // Update file status to failed
        setConfig(prev => ({
          ...prev,
          uploadedFiles: prev.uploadedFiles.map(f => 
            f.id === fileId 
              ? { ...f, uploadStatus: 'failed' }
              : f
          )
        }));

        toast({
          title: "Upload failed",
          description: `Failed to upload ${file.name}. Please try again.`,
          variant: "destructive"
        });
      }
    }
  };

  const removeFile = (fileId: string) => {
    setConfig(prev => ({
      ...prev,
      uploadedFiles: prev.uploadedFiles.filter(f => f.id !== fileId)
    }));
  };

  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return '📄';
    if (type.includes('word') || type.includes('document')) return '📝';
    if (type.includes('text')) return '📃';
    if (type.includes('csv')) return '📊';
    return '📄';
  };

  if (!isOpen) return null;

  const steps = [
    { id: 'basics', title: 'Basic Info', icon: Bot },
    { id: 'prompt', title: 'System Prompt', icon: Wand2 },
    { id: 'knowledge', title: 'Knowledge Base', icon: FileText },
    { id: 'vapi', title: 'VAPI Setup', icon: Phone },
    { id: 'voice', title: 'Voice Settings', icon: Settings },
    { id: 'integrations', title: 'Integrations', icon: Zap },
    { id: 'advanced', title: 'Advanced', icon: Settings }
  ];

  const currentStepData = steps[currentStep];
  const StepIcon = currentStepData.icon;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-card border border-border rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <StepIcon className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold">Create VAPI Agent</h3>
                <p className="text-sm text-gray-600">
                  Step {currentStep + 1} of {steps.length}: {currentStepData.title}
                </p>
              </div>
            </div>
            <Button variant="ghost" size="icon" onClick={handleClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center gap-2 mt-4 overflow-x-auto">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.id}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors whitespace-nowrap ${
                    index === currentStep
                      ? 'bg-indigo-600 text-primary-foreground'
                      : index < currentStep
                      ? 'bg-green-100 text-green-800'
                      : 'bg-muted text-gray-600'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span className="text-sm font-medium">{step.title}</span>
                  {index < currentStep && <CheckCircle className="h-4 w-4" />}
                </div>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Step 0: Basic Info */}
          {currentStep === 0 && (
            <div className="space-y-6">
              <div>
                <Label htmlFor="agent-name" className="text-base font-medium">
                  Agent Name *
                </Label>
                <Input
                  id="agent-name"
                  value={config.name}
                  onChange={(e) => setConfig(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Customer Support Assistant"
                  className="mt-2"
                />
              </div>

              <div>
                <Label htmlFor="agent-description" className="text-base font-medium">
                  Description
                </Label>
                <Textarea
                  id="agent-description"
                  value={config.description}
                  onChange={(e) => setConfig(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe what this agent does..."
                  rows={3}
                  className="mt-2"
                />
              </div>

              <div>
                <Label className="text-base font-medium mb-4 block">
                  Agent Type *
                </Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {AGENT_TYPES.map((type) => (
                    <Card
                      key={type.id}
                      className={`cursor-pointer transition-all hover:shadow-md ${
                        config.agentType === type.id
                          ? 'border-primary bg-primary/5'
                          : 'hover:border-muted-foreground'
                      }`}
                      onClick={() => setConfig(prev => ({ ...prev, agentType: type.id }))}
                    >
                      <CardHeader className="pb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{type.icon}</span>
                          <CardTitle className="text-sm">{type.name}</CardTitle>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <CardDescription className="text-xs">
                          {type.description}
                        </CardDescription>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 1: System Prompt */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <Label className="text-base font-medium mb-4 block">
                  How would you like to create the system prompt?
                </Label>
                <Tabs
                  value={config.promptSource}
                  onValueChange={(value) => setConfig(prev => ({ ...prev, promptSource: value as any }))}
                >
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="manual">Manual</TabsTrigger>
                    <TabsTrigger value="website">From Website</TabsTrigger>
                  </TabsList>

                  <TabsContent value="manual" className="mt-4">
                    <div>
                      <Label htmlFor="system-prompt" className="text-sm font-medium">
                        System Prompt *
                      </Label>
                      <Textarea
                        id="system-prompt"
                        value={config.systemPrompt}
                        onChange={(e) => setConfig(prev => ({ ...prev, systemPrompt: e.target.value }))}
                        placeholder="You are a helpful AI assistant. Your role is to..."
                        rows={8}
                        className="mt-2"
                      />
                    </div>
                  </TabsContent>

                  <TabsContent value="website" className="mt-4 space-y-6">
                    <SystemPromptGenerator
                      primaryUrl={config.websiteUrl}
                      onUrlChange={(url) => setConfig(prev => ({ ...prev, websiteUrl: url }))}
                      onPromptGenerated={(prompt, extractedInfo) => {
                        setConfig(prev => ({
                          ...prev,
                          systemPrompt: prompt,
                          description: extractedInfo?.aboutText || prev.description
                        }));
                      }}
                      initialPrompt={config.systemPrompt}
                      showDocumentUpload={true}
                      showMultipleUrls={true}
                      apiBaseUrl={apiBaseUrl}
                      additionalContext={{
                        agentType: config.agentType,
                        language: config.language,
                        companyName: config.name
                      }}
                    />
                  </TabsContent>

                </Tabs>
              </div>
            </div>
          )}

          {/* Step 2: Knowledge Base */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Switch
                    id="enable-kb"
                    checked={config.enableKnowledgeBase}
                    onCheckedChange={(checked) => setConfig(prev => ({ ...prev, enableKnowledgeBase: checked }))}
                  />
                  <Label htmlFor="enable-kb" className="text-base font-medium">
                    Enable Knowledge Base
                  </Label>
                </div>
                <p className="text-sm text-gray-600 mb-6">
                  Upload documents to give your agent domain-specific knowledge. Supports PDF, Word, TXT, CSV, Markdown, JSON, and XML files.
                </p>
              </div>

              {config.enableKnowledgeBase && (
                <div className="space-y-4">
                  <div className="border-2 border-dashed border-muted-foreground rounded-lg p-6 text-center">
                    <Upload className="h-8 w-8 text-gray-600 mx-auto mb-2" />
                    <p className="text-sm font-medium mb-1">Drop files here or click to browse</p>
                    <p className="text-xs text-gray-600 mb-4">
                      Maximum file size: 300KB. Supported formats: PDF, Word, TXT, CSV, Markdown, JSON, XML
                    </p>
                    <input
                      type="file"
                      multiple
                      accept=".pdf,.doc,.docx,.txt,.csv,.md,.json,.xml"
                      onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                      className="hidden"
                      id="file-upload"
                    />
                    <Button 
                      variant="outline" 
                      onClick={() => document.getElementById('file-upload')?.click()}
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      Browse Files
                    </Button>
                  </div>

                  {config.uploadedFiles.length > 0 && (
                    <div className="space-y-3">
                      <Label className="text-sm font-medium">Uploaded Files</Label>
                      {config.uploadedFiles.map((file) => (
                        <div key={file.id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                          <div className="flex items-center gap-3">
                            <span className="text-lg">{getFileIcon(file.type)}</span>
                            <div>
                              <p className="text-sm font-medium">{file.name}</p>
                              <p className="text-xs text-gray-600">
                                {(file.size / 1024).toFixed(1)}KB • {file.uploadStatus}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {file.uploadStatus === 'uploading' && (
                              <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                            )}
                            {file.uploadStatus === 'uploaded' && (
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            )}
                            {file.uploadStatus === 'failed' && (
                              <AlertCircle className="h-4 w-4 text-red-500" />
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeFile(file.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {!config.enableKnowledgeBase && (
                    <div className="p-4 bg-muted/50 rounded-lg">
                      <p className="text-sm text-gray-600">
                        Knowledge Base is disabled. Your agent will use only the system prompt for context.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Step 3: VAPI Setup */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <Label htmlFor="vapi-phone-id" className="text-base font-medium">
                  VAPI Phone ID
                </Label>
                <Input
                  id="vapi-phone-id"
                  value={config.vapiPhoneId}
                  onChange={(e) => setConfig(prev => ({ ...prev, vapiPhoneId: e.target.value }))}
                  placeholder="Enter your VAPI phone number ID"
                  className="mt-2"
                />
                <p className="text-xs text-gray-600 mt-1">
                  The phone number ID from your VAPI dashboard
                </p>
              </div>

              <div>
                <Label className="text-base font-medium mb-2 block">
                  Call Type
                </Label>
                <Select
                  value={config.callType}
                  onValueChange={(value) => setConfig(prev => ({ ...prev, callType: value as any }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="inbound">Inbound Only</SelectItem>
                    <SelectItem value="outbound">Outbound Only</SelectItem>
                    <SelectItem value="both">Both Inbound & Outbound</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Globe className="h-4 w-4" />
                    Webhook Configuration
                  </CardTitle>
                  <CardDescription>
                    This webhook URL will receive call events and analytics from VAPI
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="enable-webhooks"
                      checked={config.enableWebhooks}
                      onCheckedChange={(checked) => setConfig(prev => ({ ...prev, enableWebhooks: checked }))}
                    />
                    <Label htmlFor="enable-webhooks">Enable webhooks</Label>
                  </div>

                  {config.enableWebhooks && (
                    <div>
                      <Label className="text-sm font-medium">Webhook URL</Label>
                      <div className="flex gap-2 mt-1">
                        <Input
                          value={generatedWebhookUrl}
                          readOnly
                          className="font-mono text-xs"
                        />
                        <Button variant="outline" size="sm" onClick={copyWebhookUrl}>
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                      <p className="text-xs text-gray-600 mt-1">
                        Use this URL in your VAPI assistant configuration
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 4: Voice Settings */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div>
                <Label className="text-base font-medium mb-4 block">
                  Voice Selection
                </Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {VOICE_OPTIONS.map((voice) => (
                    <Card
                      key={voice.id}
                      className={`cursor-pointer transition-all hover:shadow-md ${
                        config.voice === voice.id
                          ? 'border-primary bg-primary/5'
                          : 'hover:border-muted-foreground'
                      }`}
                      onClick={() => setConfig(prev => ({ ...prev, voice: voice.id }))}
                    >
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">{voice.name}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <CardDescription className="text-xs">
                          {voice.description}
                        </CardDescription>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-base font-medium mb-2 block">
                  Language
                </Label>
                <Select
                  value={config.language}
                  onValueChange={(value) => setConfig(prev => ({ ...prev, language: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {LANGUAGE_OPTIONS.map((lang) => (
                      <SelectItem key={lang.id} value={lang.id}>
                        {lang.flag} {lang.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="speed-slider" className="text-base font-medium mb-2 block">
                  Speaking Speed: {config.speed}x
                </Label>
                <input
                  id="speed-slider"
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={config.speed}
                  onChange={(e) => setConfig(prev => ({ ...prev, speed: parseFloat(e.target.value) }))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-600 mt-1">
                  <span>0.5x (Slow)</span>
                  <span>1.0x (Normal)</span>
                  <span>2.0x (Fast)</span>
                </div>
              </div>
            </div>
          )}

          {/* Step 5: Tools & Integrations */}
          {currentStep === 5 && (
            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <Label className="text-base font-medium">
                      Available Tools & Integrations
                    </Label>
                    <p className="text-sm text-gray-600 mt-1">
                      Select tools to enable for your voice agent. Click categories to expand and explore available tools.
                    </p>
                  </div>
                  {selectedTools.size > 0 && (
                    <Badge variant="secondary">
                      {selectedTools.size} tools selected
                    </Badge>
                  )}
                </div>

                <div className="space-y-2">
                  {toolCategories.map((category) => (
                    <Card key={category.id} className="overflow-hidden">
                      <CardHeader
                        className="pb-2 cursor-pointer hover:bg-muted/50 transition-colors"
                        onClick={() => toggleCategory(category.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            {expandedCategories.has(category.id) ? (
                              <ChevronDown className="h-4 w-4 text-gray-600" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-gray-600" />
                            )}
                            <span className="text-lg">{category.icon}</span>
                            <div>
                              <CardTitle className="text-sm">{category.name}</CardTitle>
                              <CardDescription className="text-xs">
                                {category.description}
                              </CardDescription>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs">
                              {category.tools.length} {category.tools.length === 1 ? 'tool' : 'tools'}
                            </Badge>
                            {category.id === 'custom' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  addCustomTool();
                                }}
                              >
                                <Plus className="h-3 w-3 mr-1" />
                                Add
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardHeader>

                      {expandedCategories.has(category.id) && (
                        <CardContent className="pt-0">
                          {category.tools.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                              {category.tools.map((tool) => (
                                <div key={tool.id}>
                                  {tool.isCustom ? (
                                    // Custom tool editing interface
                                    <Card className="border-dashed">
                                      <CardContent className="p-3">
                                        <div className="space-y-2">
                                          <div className="flex items-center justify-between">
                                            <span className="text-xs font-medium">Custom Tool</span>
                                            <Button
                                              variant="ghost"
                                              size="sm"
                                              onClick={() => removeCustomTool(tool.id)}
                                            >
                                              <Trash2 className="h-3 w-3" />
                                            </Button>
                                          </div>
                                          <Input
                                            placeholder="Tool name"
                                            value={tool.name}
                                            onChange={(e) => updateCustomTool(tool.id, 'name', e.target.value)}
                                            className="text-xs"
                                          />
                                          <Input
                                            placeholder="Description"
                                            value={tool.description}
                                            onChange={(e) => updateCustomTool(tool.id, 'description', e.target.value)}
                                            className="text-xs"
                                          />
                                          <Input
                                            placeholder="Webhook URL"
                                            value={tool.webhook_url || ''}
                                            onChange={(e) => updateCustomTool(tool.id, 'webhook_url', e.target.value)}
                                            className="text-xs"
                                          />
                                          {tool.name && tool.description && tool.webhook_url && (
                                            <div className="flex items-center gap-2 pt-1">
                                              <Button
                                                variant={selectedTools.has(tool.id) ? "default" : "outline"}
                                                size="sm"
                                                onClick={() => toggleTool(tool.id)}
                                                className="text-xs h-6"
                                              >
                                                {selectedTools.has(tool.id) ? (
                                                  <>
                                                    <CheckCircle className="h-3 w-3 mr-1" />
                                                    Selected
                                                  </>
                                                ) : (
                                                  'Select Tool'
                                                )}
                                              </Button>
                                            </div>
                                          )}
                                        </div>
                                      </CardContent>
                                    </Card>
                                  ) : (
                                    // Standard tool selection
                                    <Card
                                      className={`cursor-pointer transition-all hover:shadow-sm ${
                                        selectedTools.has(tool.id)
                                          ? 'border-primary bg-primary/5'
                                          : 'hover:border-muted-foreground'
                                      }`}
                                      onClick={() => toggleTool(tool.id)}
                                    >
                                      <CardContent className="p-3">
                                        <div className="flex items-start gap-2">
                                          <span className="text-sm">{tool.icon}</span>
                                          <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                              <span className="text-xs font-medium truncate">{tool.name}</span>
                                              {selectedTools.has(tool.id) && (
                                                <CheckCircle className="h-3 w-3 text-indigo-600 flex-shrink-0" />
                                              )}
                                            </div>
                                            <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                                              {tool.description}
                                            </p>
                                          </div>
                                        </div>
                                      </CardContent>
                                    </Card>
                                  )}
                                </div>
                              ))}
                            </div>
                          ) : (
                            category.id === 'custom' ? (
                              <div className="text-center py-6">
                                <Code className="h-8 w-8 text-gray-600 mx-auto mb-2" />
                                <p className="text-sm text-gray-600 mb-3">
                                  No custom tools added yet
                                </p>
                                <Button variant="outline" size="sm" onClick={addCustomTool}>
                                  <Plus className="h-4 w-4 mr-2" />
                                  Add Your First Custom Tool
                                </Button>
                              </div>
                            ) : (
                              <p className="text-sm text-gray-600 text-center py-4">
                                No tools available in this category yet
                              </p>
                            )
                          )}
                        </CardContent>
                      )}
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 6: Advanced Settings */}
          {currentStep === 6 && (
            <div className="space-y-6">
              <div>
                <Label htmlFor="max-duration" className="text-base font-medium">
                  Maximum Call Duration (seconds)
                </Label>
                <Input
                  id="max-duration"
                  type="number"
                  value={config.maxDuration}
                  onChange={(e) => setConfig(prev => ({ ...prev, maxDuration: parseInt(e.target.value) || 600 }))}
                  className="mt-2"
                />
              </div>

              <div>
                <Label htmlFor="silence-timeout" className="text-base font-medium">
                  Silence Timeout (seconds)
                </Label>
                <Input
                  id="silence-timeout"
                  type="number"
                  value={config.silenceTimeout}
                  onChange={(e) => setConfig(prev => ({ ...prev, silenceTimeout: parseInt(e.target.value) || 10 }))}
                  className="mt-2"
                />
              </div>

              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="interruptible"
                    checked={config.interruptible}
                    onCheckedChange={(checked) => setConfig(prev => ({ ...prev, interruptible: checked }))}
                  />
                  <Label htmlFor="interruptible">Allow interruptions during speech</Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="record-calls"
                    checked={config.recordCalls}
                    onCheckedChange={(checked) => setConfig(prev => ({ ...prev, recordCalls: checked }))}
                  />
                  <Label htmlFor="record-calls">Record calls for quality assurance</Label>
                </div>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Summary</CardTitle>
                  <CardDescription>
                    Review your VAPI agent configuration
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div><strong>Name:</strong> {config.name}</div>
                  <div><strong>Type:</strong> {AGENT_TYPES.find(t => t.id === config.agentType)?.name}</div>
                  <div><strong>Voice:</strong> {VOICE_OPTIONS.find(v => v.id === config.voice)?.name}</div>
                  <div><strong>Language:</strong> {LANGUAGE_OPTIONS.find(l => l.id === config.language)?.name}</div>
                  <div><strong>Selected Tools:</strong> {selectedTools.size} tools enabled</div>
                  {selectedTools.size > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {Array.from(selectedTools).map(toolId => {
                        const tool = toolCategories.flatMap(cat => cat.tools).find(t => t.id === toolId);
                        return tool ? (
                          <Badge key={toolId} variant="secondary" className="text-xs">
                            {tool.icon} {tool.name}
                          </Badge>
                        ) : null;
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-border">
          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
              disabled={currentStep === 0}
            >
              Previous
            </Button>
            
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              
              {currentStep === steps.length - 1 ? (
                <Button onClick={createVapiAgent} disabled={isCreating}>
                  {isCreating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Creating...
                    </>
                  ) : (
                    'Create VAPI Agent'
                  )}
                </Button>
              ) : (
                <Button
                  onClick={() => setCurrentStep(Math.min(steps.length - 1, currentStep + 1))}
                >
                  Next
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      <ConfirmationDialog />
    </div>
  );
};