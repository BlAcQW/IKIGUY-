import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Globe,
  Bot,
  Phone,
  Zap,
  CheckCircle,
  AlertTriangle,
  Loader2,
  ExternalLink,
  Copy,
  Play,
  Settings,
  BarChart3,
  Users,
  Headphones,
  Calendar,
  Ticket,
  Heart,
  Sparkles
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  automationOrchestrationService,
  type AutomationTemplate,
  type AutomationConfig,
  type DeploymentResult
} from '@/services/AutomationOrchestrationService';
import { SystemPromptGenerator } from '@/components/shared/SystemPromptGenerator';
import { getAuthHeaders } from '@/lib/auth-utils';
import CustomToolsSelector from '@/components/automation/CustomToolsSelector';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


interface CustomTool {
  id: string;
  name: string;
  client_id: string;
  industry: string;
  category: string;
  description: string;
  endpoint: string;
  method: string;
  schema: any;
  active: boolean;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
  vapi_tool_id?: string;
}

interface CompanyInfo {
  name: string;
  description: string;
  services: string[];
  businessHours: string;
  contactInfo: {
    phone?: string;
    email?: string;
    address?: string;
  };
  aboutText: string;
}

// Using API_BASE_URL from api-config;

// Template for no-hallucination system prompts
const NO_HALLUCINATION_TEMPLATE = `You are a helpful assistant for this company. You must ONLY provide information that is explicitly stated in the company information provided below. If you don't have specific information about something, you should say "I don't have that specific information, but I can connect you with someone who can help" or direct them to the appropriate contact method.

IMPORTANT: Do not make up or infer any information that isn't explicitly provided. Always be honest about what you know and don't know.`;

const automationTypes = [
  {
    id: 'sales',
    name: 'Sales Assistant',
    description: 'AI sales representative for lead qualification and opportunity management',
    icon: Users,
    personality: 'professional',
    integrations: ['hubspot_crm', 'resend_email', 'calendly_scheduling', 'tavily_search']
  },
  {
    id: 'helpdesk',
    name: 'Helpdesk Support',
    description: 'Customer support assistant for issue resolution and ticket management',
    icon: Headphones,
    personality: 'empathetic',
    integrations: ['freshdesk_support', 'resend_email', 'tavily_search', 'supabase_database']
  },
  {
    id: 'healthcare',
    name: 'Healthcare Assistant',
    description: 'HIPAA-compliant healthcare support for appointments and provider information',
    icon: Heart,
    personality: 'empathetic',
    integrations: ['calendly_scheduling', 'resend_email', 'tavily_search', 'hubspot_crm']
  },
  {
    id: 'lead_generation',
    name: 'Lead Generation',
    description: 'Focused lead generation and qualification for B2B sales',
    icon: Zap,
    personality: 'friendly',
    integrations: ['hubspot_crm', 'resend_email', 'tavily_search', 'calendly_scheduling']
  },
  {
    id: 'appointment_booking',
    name: 'Appointment Booking',
    description: 'Dedicated appointment scheduling and calendar management',
    icon: Calendar,
    personality: 'professional',
    integrations: ['calendly_scheduling', 'resend_email', 'vonage_sms', 'hubspot_crm']
  },
  {
    id: 'customer_support',
    name: 'Customer Success',
    description: 'Proactive customer support for retention and growth',
    icon: Ticket,
    personality: 'friendly',
    integrations: ['hubspot_crm', 'resend_email', 'freshdesk_support', 'tavily_search']
  }
];

const industries = [
  'Technology', 'Healthcare', 'Finance', 'Retail', 'Education', 'Manufacturing',
  'Real Estate', 'Consulting', 'Legal', 'Marketing', 'E-commerce', 'Other'
];

const personalities = [
  { id: 'professional', name: 'Professional', description: 'Formal, business-focused' },
  { id: 'friendly', name: 'Friendly', description: 'Warm, approachable' },
  { id: 'empathetic', name: 'Empathetic', description: 'Understanding, patient' },
  { id: 'authoritative', name: 'Authoritative', description: 'Confident, decisive' },
  { id: 'casual', name: 'Casual', description: 'Relaxed, informal' },
  { id: 'technical', name: 'Technical', description: 'Precise, analytical' }
];

// Helper function to clean company names from markdown and invalid characters
const cleanCompanyName = (name: string): string => {
  if (!name || typeof name !== 'string') {
    return 'Your Company';
  }

  return name
    // Remove markdown links [text](url)
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    // Remove leading hyphens and dashes
    .replace(/^[-–—\s]+/, '')
    // Remove trailing hyphens and dashes
    .replace(/[-–—\s]+$/, '')
    // Remove extra whitespace
    .replace(/\s+/g, ' ')
    // Trim and fallback to default if empty
    .trim() || 'Your Company';
};

export default function QuickAutomationDeployment() {
  const { toast } = useToast();
  const [step, setStep] = useState<'configure' | 'extracting' | 'deploying' | 'completed'>('configure');
  const [companyUrl, setCompanyUrl] = useState('');
  const [automationType, setAutomationType] = useState('');
  const [industry, setIndustry] = useState('');
  const [personality, setPersonality] = useState('');
  const [customInstructions, setCustomInstructions] = useState('');
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null);
  const [deploymentResult, setDeploymentResult] = useState<DeploymentResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [extractionComplete, setExtractionComplete] = useState(false);
  const [configId, setConfigId] = useState<string | null>(null);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [assistantName, setAssistantName] = useState<string>('');
  const [vapiAssistantId, setVapiAssistantId] = useState<string | null>(null);
  const [selectedTools, setSelectedTools] = useState<CustomTool[]>([]);
  const [availableTools, setAvailableTools] = useState<CustomTool[]>([]);
  const [toolsLoading, setToolsLoading] = useState(false);
  const [extractedWebsiteContent, setExtractedWebsiteContent] = useState<string>('');

  // Extract company info and generate VAPI-optimized system prompt using simplified backend
  const extractCompanyInfoAndGeneratePrompt = async (url: string): Promise<{extractedData: any, vapiPrompt: string}> => {
    console.log('🚀 Starting company extraction for:', url);
    console.log('📋 Using automation type:', automationType, 'industry:', industry);

    // Use the new simplified backend endpoint that combines extraction and prompt generation
    const response = await fetch(`${API_BASE_URL}/vapi-consolidated/quick-deploy-extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...await getAuthHeaders()
      },
      body: JSON.stringify({
        url: url,
        automation_type: automationType,
        company_name: null, // Let the backend extract this
        assistant_name: assistantName || null, // Custom assistant name
        industry: industry || null
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('❌ Quick deploy extraction failed:', errorData);
      throw new Error(errorData.error || 'Failed to extract company information and generate prompt');
    }

    const data = await response.json();
    console.log('✅ Extraction response received:', data);
    console.log('🔍 Debugging response structure:', {
      success: data.success,
      hasExtractedData: !!data.extracted_data,
      extractedDataKeys: data.extracted_data ? Object.keys(data.extracted_data) : [],
      hasSystemPrompt: !!data.system_prompt,
      systemPromptLength: data.system_prompt ? data.system_prompt.length : 0,
      systemPromptPreview: data.system_prompt ? data.system_prompt.substring(0, 100) + '...' : 'null'
    });

    if (!data.success) {
      console.error('❌ Backend reported extraction failure:', data.error);
      throw new Error(data.error || 'Extraction failed');
    }

    if (!data.extracted_data || !data.system_prompt) {
      console.error('❌ Missing data in response:', {
        hasExtractedData: !!data.extracted_data,
        hasSystemPrompt: !!data.system_prompt,
        extractedData: data.extracted_data,
        systemPrompt: data.system_prompt
      });
      throw new Error('Incomplete response from extraction service');
    }

    console.log('🎉 Extraction completed successfully!');
    console.log('📊 Extraction method used:', data.extraction_details?.method);
    console.log('🏢 Company found:', data.extracted_data.companyName);

    return {
      extractedData: data.extracted_data,
      vapiPrompt: data.system_prompt
    };
  };

  // Generate enhanced system prompt using the same logic as AutomationDeploymentWizard
  const generateEnhancedSystemPrompt = (extractedInfo: any, companyName: string, customDescription?: string) => {
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
${extractedInfo?.aboutText || customDescription || 'Please refer to our official documentation for detailed information about our company.'}

## Knowledge Base:
Use only the information provided above when answering questions about ${companyName}. For any information not explicitly stated here, direct customers to our official contact points.`;
  };

  // Default tools configuration (6 tools as specified)
  const DEFAULT_TOOL_IDS = [
    'abc528ae-e1f1-4e9c-a939-bc859e5e7d88', // send_notification_email
    'fc1ca495-9083-492e-854a-aeee6e5b3f64', // send_sms_vonage
    '83635498-8f71-453a-9a15-7e00e1e494a2', // create_support_ticket
    'd7f97ff5-e4ce-46fd-a75c-8bb0cf76454b', // search_web_with_ai
    '7a894aca-6633-429c-ba36-1a8fe4fbd6bf', // book_google_calendar_appointment
    '11692713-925f-4e77-a335-ba54c4d48db9'  // check_google_calendar_availability
  ];

  // Load available tools from the backend
  const loadAvailableTools = async () => {
    setToolsLoading(true);
    try {
      const headers = await getAuthHeaders();
      console.log('🔐 Loading custom tools with headers:', {
        url: buildApiUrl('/custom-tools/'),
        hasAuth: !!headers.Authorization,
        hasServiceToken: !!headers['x-service-token'],
        authSnippet: headers.Authorization?.substring(0, 20) + '...',
        timestamp: new Date().toISOString()
      });

      const response = await fetch(buildApiUrl('/custom-tools/'), {
        headers: {
          'Content-Type': 'application/json',
          ...headers
        }
      });

      console.log('📥 Custom tools API response:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        timestamp: new Date().toISOString()
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Custom tools API error:', {
          status: response.status,
          statusText: response.statusText,
          errorText,
          timestamp: new Date().toISOString()
        });
        throw new Error(`Failed to load custom tools: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      const tools = data.tools || [];
      setAvailableTools(tools);

      // Auto-select default tools
      const defaultTools = tools.filter((tool: CustomTool) =>
        tool.vapi_tool_id && DEFAULT_TOOL_IDS.includes(tool.vapi_tool_id)
      );
      setSelectedTools(defaultTools);

      console.log('📋 Loaded tools:', {
        totalTools: tools.length,
        defaultToolsFound: defaultTools.length,
        defaultToolNames: defaultTools.map((t: CustomTool) => t.name)
      });

    } catch (error) {
      console.error('❌ Failed to load custom tools:', {
        error: error instanceof Error ? error.message : error,
        timestamp: new Date().toISOString()
      });
      toast({
        title: "Failed to load tools",
        description: "Using fallback tool configuration",
        variant: "destructive",
      });
    } finally {
      setToolsLoading(false);
    }
  };

  // Get relevant tool IDs based on automation type
  const getToolsForAutomationType = (automationType: string): string[] => {
    const toolMappings = {
      'sales': [
        '1e59ec6d-e2ec-4707-9e71-7dbceb51da0d', // create_hubspot_contact
        'abc528ae-e1f1-4e9c-a939-bc859e5e7d88', // send_notification_email
        '3f6ddf13-5121-4127-8aec-bdc4dfda6f7d', // check_calendly_availability
        'd1c30e08-aae8-49b1-b06e-ba3a3e634f18', // book_calendly_appointment
        'd7f97ff5-e4ce-46fd-a75c-8bb0cf76454b', // search_web_with_ai
        'bb90890c-750d-429f-9a40-836140c70d1c'  // call_logging_supabase
      ],
      'helpdesk': [
        '83635498-8f71-453a-9a15-7e00e1e494a2', // create_support_ticket
        '457d5d87-a0ed-44ab-b6d6-ce3ec912ba01', // escalate_to_support
        '86e8b665-ddf8-4695-872f-772cb303d54d', // email_notification
        'd7f97ff5-e4ce-46fd-a75c-8bb0cf76454b', // search_web_with_ai
        'bb90890c-750d-429f-9a40-836140c70d1c', // call_logging_supabase
        '6eb24d57-16ef-4262-a587-a5cd1e038629'  // ai_transcript_summarization
      ],
      'healthcare': [
        '91680cf0-fc9d-4a59-b65a-8ea2ececcac7', // search_healthcare_providers
        '74e8e539-776f-4fc6-ba2f-46aa241722be', // get_emergency_providers
        'f0f98b68-ade8-4a01-ae0a-d09a9dc39c6f', // get_provider_details
        'c3b245ff-a8ee-42ed-b39d-6e50d0fc09e0', // get_available_areas
        '23954934-c55e-4faa-b0ca-23ed45ce5289', // get_available_specialties
        '3f6ddf13-5121-4127-8aec-bdc4dfda6f7d', // check_calendly_availability
        'd1c30e08-aae8-49b1-b06e-ba3a3e634f18', // book_calendly_appointment
        '457d5d87-a0ed-44ab-b6d6-ce3ec912ba01', // escalate_to_support
        'abc528ae-e1f1-4e9c-a939-bc859e5e7d88', // send_notification_email
        '271078e4-1fae-4b7c-a36d-eb810fe8724d', // get_providers_by_area
        '57b96294-2181-4a44-be58-96c932f33839', // get_providers_by_specialty
        'ef047f51-e523-43a6-a832-d1c55f473a03', // send_provider_info_email
        'cd6dde17-2a84-4bdd-b3c6-a0d11a5d33eb', // send_provider_info_sms
        'b333d4d3-210c-4bc9-9ed7-6fc12d85f364'  // send_call_summary_email
      ],
      'lead_generation': [
        '1e59ec6d-e2ec-4707-9e71-7dbceb51da0d', // create_hubspot_contact
        'abc528ae-e1f1-4e9c-a939-bc859e5e7d88', // send_notification_email
        'fc1ca495-9083-492e-854a-aeee6e5b3f64', // send_sms_vonage
        'd7f97ff5-e4ce-46fd-a75c-8bb0cf76454b', // search_web_with_ai
        '3f6ddf13-5121-4127-8aec-bdc4dfda6f7d', // check_calendly_availability
        'bb90890c-750d-429f-9a40-836140c70d1c'  // call_logging_supabase
      ],
      'appointment_booking': [
        '3f6ddf13-5121-4127-8aec-bdc4dfda6f7d', // check_calendly_availability
        'd1c30e08-aae8-49b1-b06e-ba3a3e634f18', // book_calendly_appointment
        'abc528ae-e1f1-4e9c-a939-bc859e5e7d88', // send_notification_email
        'fc1ca495-9083-492e-854a-aeee6e5b3f64', // send_sms_vonage
        '1e59ec6d-e2ec-4707-9e71-7dbceb51da0d', // create_hubspot_contact
        'bb90890c-750d-429f-9a40-836140c70d1c'  // call_logging_supabase
      ],
      'customer_support': [
        '83635498-8f71-453a-9a15-7e00e1e494a2', // create_support_ticket
        '457d5d87-a0ed-44ab-b6d6-ce3ec912ba01', // escalate_to_support
        '1e59ec6d-e2ec-4707-9e71-7dbceb51da0d', // create_hubspot_contact
        '86e8b665-ddf8-4695-872f-772cb303d54d', // email_notification
        'd7f97ff5-e4ce-46fd-a75c-8bb0cf76454b', // search_web_with_ai
        'bb90890c-750d-429f-9a40-836140c70d1c'  // call_logging_supabase
      ]
    };

    return toolMappings[automationType as keyof typeof toolMappings] || [
      // Default tools for any automation type
      'abc528ae-e1f1-4e9c-a939-bc859e5e7d88', // send_notification_email
      'd7f97ff5-e4ce-46fd-a75c-8bb0cf76454b', // search_web_with_ai
      'bb90890c-750d-429f-9a40-836140c70d1c'  // call_logging_supabase
    ];
  };

  // Create VAPI agent with the enhanced system prompt
  const createVAPIAgent = async (companyInfo: CompanyInfo, systemPrompt: string): Promise<{success: boolean, agent_id?: string, error?: string}> => {
    const startTime = Date.now();
    try {
      const agentName = assistantName || `${companyInfo.name} Assistant`;
      const description = `AI voice assistant for ${companyInfo.name} specializing in ${automationType} support`;

      // Generate dynamic first message based on company and automation type
      const automationTypeDisplayName = selectedAutomationType?.name || automationType;
      const firstMessage = `Hello, this is Ama, ${automationTypeDisplayName} from ${companyInfo.name}. How are you today?`;

      // Get tools based on user selection and validate they have VAPI IDs
      const toolsWithVapiId = selectedTools.filter(tool => tool.vapi_tool_id);
      const toolsWithoutVapiId = selectedTools.filter(tool => !tool.vapi_tool_id);

      const toolIds = toolsWithVapiId.map(tool => tool.vapi_tool_id!);

      // Warn user if some tools are being filtered out
      if (toolsWithoutVapiId.length > 0) {
        const excludedToolNames = toolsWithoutVapiId.map(t => t.name).join(', ');
        toast.warning(
          `${toolsWithoutVapiId.length} tool(s) excluded (missing VAPI ID): ${excludedToolNames}`,
          { duration: 5000 }
        );
        console.warn('⚠️ Tools without VAPI ID excluded:', toolsWithoutVapiId);
      }

      console.log('🤖 Creating VAPI agent...', {
        agentName,
        description,
        firstMessage,
        systemPromptLength: systemPrompt.length,
        automationType,
        companyName: companyInfo.name,
        toolIds: toolIds,
        toolCount: toolIds.length,
        excludedTools: toolsWithoutVapiId.length,
        integrations: selectedAutomationType?.integrations || [],
        timestamp: new Date().toISOString()
      });

      // Transform custom tools to only include vapi_tool_id for VAPI validation
      const customTools = toolIds;

      // Create payload structure that matches the backend VapiAgentCreateRequest model
      const requestPayload = {
        name: agentName,
        description: description,
        system_prompt: systemPrompt, // Move system prompt to top level
        voice: "alloy", // Valid OpenAI TTS voice ID
        language: "en",
        speed: 1.0,
        call_type: "both",
        max_duration: 600,
        silence_timeout: 10,
        interruptible: true,
        record_calls: true,
        integrations: selectedAutomationType?.integrations || [],
        custom_tools: customTools,
        tenant_id: "default",
        // Additional VAPI-specific configuration for advanced features
        vapi_config: {
          firstMessage: firstMessage,
          voicemailMessage: "Please call back when you're available.",
          endCallFunctionEnabled: true,
          endCallMessage: "Goodbye.",
          transcriber: {
            model: "nova-3-general",
            language: "en",
            numerals: true,
            provider: "deepgram"
          },
          serverMessages: [
            "end-of-call-report",
            "function-call",
            "tool-calls"
          ],
          dialKeypadFunctionEnabled: true,
          analysisPlan: {
            minMessagesThreshold: 2,
            summaryPlan: {
              messages: [
                {
                  content: "Make an extensive summary of this conversation. Tell us what the sentiment was of the caller. Also try to substract email adresses and phone numbers. Sometimes phone numbers are weirdly formatted so you have to desihper them, same with email adresses. Do it as best you can. Put them in the correct formatting in your summary like E164 for phone numbers.",
                  role: "system"
                },
                {
                  content: "Here is the transcript:\\n\\n\\n\\n. Here is the ended reason of the call:\\n\\n\\n\\n",
                  role: "user"
                }
              ],
              timeoutSeconds: 22
            },
            structuredDataPlan: {
              enabled: true,
              schema: {
                type: "object",
                required: [
                  "score",
                  "result",
                  "intention",
                  "sentiment",
                  "actions_taken",
                  "suggested_improvements"
                ],
                properties: {
                  email: {
                    description: "Email given by the caller",
                    type: "string"
                  },
                  score: {
                    description: "Rate the conversation from a customer service pov on a scale of 1 to 10",
                    type: "number"
                  },
                  result: {
                    description: "In a single sentence the result of the call",
                    type: "string"
                  },
                  full_name: {
                    description: "Full name given by the caller",
                    type: "string"
                  },
                  intention: {
                    description: "In a single sentence why they were calling",
                    type: "string"
                  },
                  sentiment: {
                    description: "Explain in a single sentence the mood and sentiment of the caller",
                    type: "string"
                  },
                  company_name: {
                    description: "Company name given by the caller",
                    type: "string"
                  },
                  phone_number: {
                    description: "Phone number given by the caller",
                    type: "string"
                  },
                  actions_taken: {
                    description: "In a single sentence which actions the AI has performed",
                    type: "string"
                  },
                  suggested_improvements: {
                    description: "In a single sentence how the AI could improve its interactions in a next conversation.",
                    type: "string"
                  }
                }
              },
              messages: [
                {
                  content: "You will get the transcription and summary of our conversation. I want you to extract some analysis datapoints from it. Follow the instructions and example clearly. \\n\\nJson Schema:\\n\\n\\nOnly respond with the JSON.",
                  role: "system"
                },
                {
                  content: "Here is the transcript:\\n\\n\\n\\n. Here is the ended reason of the call:\\n\\n\\n\\n",
                  role: "user"
                }
              ],
              timeoutSeconds: 38
            },
            successEvaluationPlan: {
              rubric: "PassFail",
              messages: [
                {
                  content: "You have to evaluater conversations. Always enter true here, unless the caller was actually really upset that they were called. If that's the case, enter false.\\n\\nRubric:\\n\\n\\n\\nOnly respond with the evaluation result.",
                  role: "system"
                },
                {
                  content: "Here is the transcript of the call:\\n\\n\\n\\n. Here is the ended reason of the call:\\n\\n\\n\\n",
                  role: "user"
                },
                {
                  content: "Here was the system prompt of the call:\\n\\n\\n\\n",
                  role: "user"
                }
              ],
              timeoutSeconds: 17
            }
          },
          voicemailDetection: {
            provider: "vapi",
            backoffPlan: {
              maxRetries: 6,
              startAtSeconds: 5,
              frequencySeconds: 5
            },
            beepMaxAwaitSeconds: 0
          },
          backgroundDenoisingEnabled: true,
          artifactPlan: {
            recordingFormat: "mp3"
          },
          messagePlan: {
            idleMessages: [
              "Is there anything else you need help with?",
              "I'm ready to help whenever you are.",
              "Let me know if there's anything you need.",
              "Feel free to ask me any questions.",
              "How can I assist you further?"
            ]
          },
          startSpeakingPlan: {
            smartEndpointingPlan: {
              provider: "vapi"
            }
          }
        }
      };

      console.log('📤 VAPI Agent request payload:', {
        ...requestPayload,
        system_prompt: `${systemPrompt.substring(0, 200)}...` // Truncate for logging
      });

      const headers = await getAuthHeaders();
      console.log('🔐 Request headers:', {
        'Content-Type': 'application/json',
        ...headers,
        Authorization: headers.Authorization ? `${headers.Authorization.substring(0, 20)}...` : 'Not set'
      });

      const response = await fetch(`${API_BASE_URL}/vapi-consolidated/agents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headers
        },
        body: JSON.stringify(requestPayload)
      });

      console.log('📥 VAPI Agent API response:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        url: response.url,
        headers: Object.fromEntries(response.headers.entries())
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ VAPI Agent creation failed:', {
          status: response.status,
          statusText: response.statusText,
          errorText,
          responseHeaders: Object.fromEntries(response.headers.entries())
        });

        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { error: errorText };
        }

        throw new Error(errorData.detail || errorData.error || errorText || 'Failed to create VAPI agent');
      }

      const resultText = await response.text();
      console.log('📋 VAPI Agent raw response:', resultText);

      let result;
      try {
        result = JSON.parse(resultText);
      } catch (parseError) {
        console.error('❌ Failed to parse VAPI response:', parseError);
        throw new Error('Invalid JSON response from VAPI API');
      }

      console.log('✅ VAPI Agent created successfully:', {
        success: result.success,
        agent_id: result.agent?.agent_id || result.agent_id,
        agent_details: result.agent,
        full_result: result,
        processing_time: Date.now() - startTime
      });

      const agentId = result.agent?.agent_id || result.agent_id || result.id;
      if (!agentId) {
        console.error('❌ No agent ID found in response:', result);
        throw new Error('VAPI agent created but no agent ID returned');
      }

      return {
        success: true,
        agent_id: agentId
      };
    } catch (error) {
      const processingTime = Date.now() - startTime;
      console.error('❌ VAPI Agent creation error:', {
        error: error instanceof Error ? error.message : error,
        errorStack: error instanceof Error ? error.stack : undefined,
        processingTime,
        companyInfo,
        systemPromptLength: systemPrompt?.length,
        automationType,
        timestamp: new Date().toISOString()
      });

      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error creating VAPI agent'
      };
    }
  };

  // Generate demo HTML page
  const generateDemoHTML = (companyInfo: CompanyInfo, vapiAssistantId: string): string => {
    const companyName = companyInfo.name;
    const services = companyInfo.services.join(', ') || 'our services';
    const businessHours = companyInfo.businessHours;
    const phone = companyInfo.contactInfo?.phone || '+1-234-567-8900';

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${companyName} - AI Voice Assistant Demo</title>
    <script src="https://vapi.ai/sdk/web"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            max-width: 600px;
            width: 100%;
            text-align: center;
        }
        .logo {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .call-button {
            background: linear-gradient(45deg, #ff6b6b, #feca57);
            border: none;
            border-radius: 50px;
            padding: 20px 40px;
            font-size: 1.2em;
            font-weight: bold;
            color: white;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 20px 0;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }
        .call-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        .call-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .info-section {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
            text-align: left;
        }
        .info-item {
            margin: 15px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status {
            font-size: 0.9em;
            color: #666;
            margin-top: 15px;
        }
        .phone-icon, .clock-icon, .service-icon {
            width: 20px;
            height: 20px;
            fill: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">${companyName}</div>
        <div class="subtitle">AI Voice Assistant Demo</div>

        <button id="callButton" class="call-button">
            📞 Talk to Our AI Assistant
        </button>

        <div class="info-section">
            <h3>Company Information</h3>
            <div class="info-item">
                <svg class="service-icon" viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <span><strong>Services:</strong> ${services}</span>
            </div>
            <div class="info-item">
                <svg class="clock-icon" viewBox="0 0 24 24">
                    <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M16.2,16.2L11,13V7H12.5V12.2L17,14.7L16.2,16.2Z"/>
                </svg>
                <span><strong>Hours:</strong> ${businessHours}</span>
            </div>
            <div class="info-item">
                <svg class="phone-icon" viewBox="0 0 24 24">
                    <path d="M6.62,10.79C8.06,13.62 10.38,15.94 13.21,17.38L15.41,15.18C15.69,14.9 16.08,14.82 16.43,14.93C17.55,15.3 18.75,15.5 20,15.5A1,1 0 0,1 21,16.5V20A1,1 0 0,1 20,21A17,17 0 0,1 3,4A1,1 0 0,1 4,3H7.5A1,1 0 0,1 8.5,4C8.5,5.25 8.7,6.45 9.07,7.57C9.18,7.92 9.1,8.31 8.82,8.59L6.62,10.79Z"/>
                </svg>
                <span><strong>Phone:</strong> ${phone}</span>
            </div>
        </div>

        <div class="status" id="status">Click the button above to start a voice conversation with our AI assistant</div>
    </div>

    <script>
        const vapi = new Vapi('${vapiAssistantId}');
        const callButton = document.getElementById('callButton');
        const status = document.getElementById('status');

        callButton.addEventListener('click', async () => {
            try {
                callButton.disabled = true;
                callButton.textContent = '🔄 Connecting...';
                status.textContent = 'Connecting to voice assistant...';

                await vapi.start();

                callButton.textContent = '🎙️ Speaking...';
                status.textContent = 'Connected! You can now speak with our AI assistant.';
            } catch (error) {
                console.error('Failed to start call:', error);
                callButton.disabled = false;
                callButton.textContent = '📞 Talk to Our AI Assistant';
                status.textContent = 'Connection failed. Please try again.';
            }
        });

        vapi.on('call-end', () => {
            callButton.disabled = false;
            callButton.textContent = '📞 Talk to Our AI Assistant';
            status.textContent = 'Call ended. Click the button to start a new conversation.';
        });

        vapi.on('error', (error) => {
            console.error('VAPI error:', error);
            callButton.disabled = false;
            callButton.textContent = '📞 Talk to Our AI Assistant';
            status.textContent = 'An error occurred. Please try again.';
        });
    </script>
</body>
</html>`;
  };

  // Deploy demo HTML page using Gemini AI generation
  const deployDemoPage = async (companyInfo: CompanyInfo, vapiAssistantId: string, extractedContent: string = ''): Promise<{success: boolean, demoUrl?: string, error?: string}> => {
    try {
      console.log('🎨 Generating demo HTML with Gemini AI...', {
        companyName: companyInfo.name,
        assistantId: vapiAssistantId,
        automationType,
        contentLength: extractedContent.length
      });

      // Generate demo HTML using Gemini AI
      const generateResponse = await fetch(`${API_BASE_URL}/vapi-consolidated/generate-demo-html`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...await getAuthHeaders()
        },
        body: JSON.stringify({
          company_info: companyInfo,
          vapi_assistant_id: vapiAssistantId,
          automation_type: automationType,
          extracted_content: extractedContent
        })
      });

      if (!generateResponse.ok) {
        const errorData = await generateResponse.json();
        console.error('❌ Gemini HTML generation failed:', errorData);
        throw new Error(errorData.error || 'Failed to generate demo HTML');
      }

      const generateResult = await generateResponse.json();

      if (!generateResult.success) {
        throw new Error(generateResult.error || 'Demo HTML generation failed');
      }

      const demoHtml = generateResult.html;
      const generationMethod = generateResult.generation_method;
      const notification = generateResult.notification;

      console.log('✅ Demo HTML generated successfully:', {
        method: generationMethod,
        htmlLength: demoHtml.length,
        companyName: companyInfo.name,
        notification: notification?.message
      });

      // Display notification to user about generation method
      if (notification) {
        const notificationTitle = notification.type === 'success' ? 'Demo Generated' :
                                 notification.type === 'warning' ? 'Fallback Used' : 'Generation Issue';

        toast({
          title: notificationTitle,
          description: notification.message,
          variant: notification.type === 'error' ? 'destructive' : 'default',
        });
      }

      // Generate unique filename based on company name and timestamp
      const companySlug = companyInfo.name
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
      const timestamp = Date.now();
      const fileName = `${companySlug}-vapi-demo-${timestamp}.html`;

      // Deploy the generated HTML
      const deployResponse = await fetch(`${API_BASE_URL}/deploy-demo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...await getAuthHeaders()
        },
        body: JSON.stringify({
          fileName: fileName,
          html: demoHtml
        })
      });

      if (!deployResponse.ok) {
        const errorData = await deployResponse.json();
        throw new Error(errorData.error || 'Failed to deploy demo page');
      }

      const deployResult = await deployResponse.json();

      console.log('🚀 Demo page deployed successfully:', {
        demoUrl: deployResult.demoUrl,
        generationMethod,
        fileName
      });

      return {
        success: true,
        demoUrl: deployResult.demoUrl
      };
    } catch (error) {
      console.error('❌ Demo deployment error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error deploying demo'
      };
    }
  };

  // Save automation configuration to MongoDB
  const saveAutomationConfig = async (
    companyInfo: CompanyInfo,
    vapiAssistantId: string,
    demoUrl: string,
    systemPrompt: string
  ): Promise<{id: string, success: boolean, error?: string}> => {
    try {
      const configData = {
        automation_name: `${companyInfo.name} VAPI Quick Deploy`,
        company_info: {
          name: companyInfo.name,
          description: companyInfo.description,
          url: companyUrl,
          extracted_info: {
            services: companyInfo.services,
            businessHours: companyInfo.businessHours,
            contactInfo: companyInfo.contactInfo,
            aboutText: companyInfo.aboutText
          }
        },
        vapi_agent: {
          assistant_id: vapiAssistantId,
          phone_number_id: "",
          system_prompt: systemPrompt,
          voice_settings: {
            voice_id: "jennifer",
            model: "nova-2",
            max_duration: 600
          },
          tools: []
        },
        n8n_workflow: {
          workflow_id: "",
          workflow_name: "Default Workflow",
          webhook_url: "",
          endpoints: {
            calendar: "/calendar/availability",
            tickets: "/tickets/create",
            availability: "/availability/check",
            escalation: "/escalation/route",
            analytics: "/analytics/track"
          }
        },
        demo_settings: {
          enable_demo: true,
          demo_url: demoUrl,
          html_template: ""
        },
        template_id: automationType || "vapi_quick_deploy"
      };

      const response = await fetch(`${API_BASE_URL}/automation-configs/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...await getAuthHeaders()
        },
        body: JSON.stringify(configData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save automation configuration');
      }

      const result = await response.json();
      return {
        id: result.id,
        success: true
      };
    } catch (error) {
      console.error('Error saving automation config:', error);
      return {
        id: '',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error saving configuration'
      };
    }
  };

  // Create automation configuration using the correct model structure
  const createAutomationConfig = (template: any, extractedInfo: any): any => {
    const selectedTemplate = automationTypes.find(t => t.id === automationType);
    const companyName = extractedInfo?.companyName || extractedInfo?.name || 'Your Company';

    // Map integration names to the model structure
    const integrationConfig: any = {
      calendly: { enabled: false, apiKey: "" },
      supabase: { enabled: false, projectId: "" },
      tavily: { enabled: false, apiKey: "" },
      resend: { enabled: false, apiKey: "" },
      vonage: { enabled: false, apiKey: "" }
    };

    // Enable integrations based on selected template
    selectedTemplate?.integrations.forEach(integration => {
      if (integration.includes('calendly')) {
        integrationConfig.calendly.enabled = true;
      } else if (integration.includes('supabase')) {
        integrationConfig.supabase.enabled = true;
      } else if (integration.includes('tavily')) {
        integrationConfig.tavily.enabled = true;
      } else if (integration.includes('resend')) {
        integrationConfig.resend.enabled = true;
      } else if (integration.includes('vonage')) {
        integrationConfig.vonage.enabled = true;
      }
    });

    return {
      automation_name: `${companyName} ${selectedTemplate?.name || 'Automation'}`,
      company_info: {
        name: companyName,
        description: extractedInfo?.description || extractedInfo?.aboutText || '',
        url: companyUrl,
        extracted_info: extractedInfo
      },
      vapi_agent: {
        assistant_id: "",
        assistant_name: assistantName || `${companyName} Assistant`,
        phone_number_id: "",
        system_prompt: systemPrompt,
        voice_settings: {
          voice_id: 'jennifer',
          model: 'claude-3-5-sonnet-20241022',
          max_duration: 600
        },
        tools: selectedTemplate?.integrations || []
      },
      n8n_workflow: {
        workflow_id: "",
        workflow_name: `${companyName} ${selectedTemplate?.name || 'Workflow'}`,
        webhook_url: "",
        endpoints: {
          calendar: "/calendar/availability",
          tickets: "/tickets/create",
          availability: "/availability/check",
          escalation: "/escalation/route",
          analytics: "/analytics/track"
        }
      },
      integrations: integrationConfig,
      custom_tools: {
        enabled: false,
        selected_tools: [],
        available_tools: []
      },
      demo_settings: {
        enable_demo: true,
        demo_url: "",
        html_template: ""
      },
      analytics: {
        enable_tracking: true,
        webhook_url: "",
        report_email: ""
      },
      status: "draft",
      template_id: template?.id || null
    };
  };

  const selectedAutomationType = automationTypes.find(type => type.id === automationType);

  // Load available tools when component mounts
  React.useEffect(() => {
    loadAvailableTools();
  }, []);

  const handleExtractCompanyInfo = async () => {
    if (!companyUrl || !automationType) {
      toast({
        title: "Missing Information",
        description: "Please provide both company URL and automation type",
        variant: "destructive",
      });
      return;
    }

    setStep('extracting');
    setIsLoading(true);

    try {
      // Extract company info and generate VAPI-optimized system prompt
      const { extractedData, vapiPrompt } = await extractCompanyInfoAndGeneratePrompt(companyUrl);
      console.log('🔍 Debugging extraction result:', {
        hasExtractedData: !!extractedData,
        hasVapiPrompt: !!vapiPrompt,
        extractedDataCompanyName: extractedData?.companyName || extractedData?.name,
        vapiPromptLength: vapiPrompt ? vapiPrompt.length : 0
      });

      if (extractedData && vapiPrompt) {
        // Clean and validate company name
        const rawCompanyName = extractedData.companyName || extractedData.name || 'Your Company';
        const companyName = cleanCompanyName(rawCompanyName);
        console.log('🧹 Company name cleaned:', { raw: rawCompanyName, cleaned: companyName });

        // Validate that we have valid data before proceeding
        if (!companyName || companyName === 'Your Company' || !vapiPrompt || vapiPrompt.length < 10) {
          console.error('❌ Invalid extraction data:', {
            companyName,
            companyNameLength: companyName?.length,
            vapiPromptLength: vapiPrompt?.length,
            extractedDataKeys: Object.keys(extractedData)
          });
          throw new Error('Extracted data validation failed - company name or system prompt is invalid');
        }

        // Set company info state
        setCompanyInfo({
          name: companyName,
          description: extractedData.description || extractedData.aboutText || '',
          services: extractedData.services || [],
          businessHours: extractedData.businessHours || 'Standard business hours',
          contactInfo: extractedData.contactInfo || {},
          aboutText: extractedData.aboutText || ''
        });

        // Auto-detect industry if not selected
        if (!industry && extractedData.description) {
          const description = extractedData.description.toLowerCase();
          if (description.includes('health') || description.includes('medical')) {
            setIndustry('Healthcare');
          } else if (description.includes('tech') || description.includes('software')) {
            setIndustry('Technology');
          } else if (description.includes('finance') || description.includes('bank')) {
            setIndustry('Finance');
          }
        }

        // Auto-set personality based on automation type
        if (!personality && selectedAutomationType) {
          setPersonality(selectedAutomationType.personality);
        }

        // Use the VAPI-optimized system prompt from MASTER_TEMPLATE.md integration
        setSystemPrompt(vapiPrompt);

        // Store the extracted website content for demo generation
        const websiteContent = extractedData.aboutText || extractedData.description || '';
        setExtractedWebsiteContent(websiteContent);

        setExtractionComplete(true);

        toast({
          title: "Company Info Extracted & System Prompt Generated",
          description: `Successfully extracted information for ${companyName} with ${extractedData.extraction_method} and generated AI system prompt with master template integration`,
        });

        // Auto-proceed to deployment with extracted data
        console.log('🔧 Starting auto-deployment preparation...', {
          companyName,
          hasExtractedData: !!extractedData,
          extractedDataKeys: Object.keys(extractedData || {}),
          vapiPromptLength: vapiPrompt?.length
        });

        const finalCompanyInfo = {
          name: companyName,
          description: extractedData.description || extractedData.aboutText || '',
          services: extractedData.services || [],
          businessHours: extractedData.businessHours || 'Standard business hours',
          contactInfo: extractedData.contactInfo || {},
          aboutText: extractedData.aboutText || ''
        };

        console.log('✅ finalCompanyInfo created:', finalCompanyInfo);
        console.log('🚀 About to trigger VAPI deployment with data:', {
          finalCompanyInfo,
          vapiPromptLength: vapiPrompt?.length,
          vapiPromptPreview: vapiPrompt?.substring(0, 200) + '...'
        });

        setTimeout(() => {
          console.log('⏰ setTimeout callback executing after 1 second delay');
          console.log('🔍 Checking captured variables in setTimeout:', {
            finalCompanyInfo: finalCompanyInfo ? 'PRESENT' : 'NULL',
            vapiPrompt: vapiPrompt ? `${vapiPrompt.length} chars` : 'NULL',
            finalCompanyInfoName: finalCompanyInfo?.name,
            vapiPromptPreview: vapiPrompt?.substring(0, 100) + '...'
          });

          if (!finalCompanyInfo || !vapiPrompt) {
            console.error('❌ Cannot proceed with deployment - missing data in setTimeout:', {
              hasFinalCompanyInfo: !!finalCompanyInfo,
              hasVapiPrompt: !!vapiPrompt,
              finalCompanyInfo,
              vapiPromptLength: vapiPrompt?.length
            });
            toast({
              title: "Deployment Error",
              description: "Missing required data for deployment. Please try the extraction again.",
              variant: "destructive",
            });
            setStep('configure');
            return;
          }

          console.log('🚀 About to call handleVAPIDeployment with parameters:', {
            companyName: finalCompanyInfo.name,
            promptLength: vapiPrompt.length
          });
          handleVAPIDeployment(finalCompanyInfo, vapiPrompt);
        }, 1000);
      } else {
        throw new Error("Failed to extract company information or generate VAPI prompt");
      }
    } catch (error) {
      console.error('Enhanced extraction failed:', error);

      // Provide more specific error messages based on the type of failure
      let errorTitle = "Extraction Failed";
      let errorDescription = "Failed to extract company information";

      if (error instanceof Error) {
        if (error.message.includes('extract company information') || error.message.includes('Extraction failed')) {
          errorTitle = "Website Extraction Failed";
          errorDescription = "Failed to extract company information from the website. This might be due to Firecrawl API issues, website access restrictions, or complex content structure. Please try a different URL or try again later.";
        } else if (error.message.includes('generate prompt') || error.message.includes('prompt generation failed')) {
          errorTitle = "System Prompt Generation Failed";
          errorDescription = "Successfully extracted company information but failed to generate the AI assistant's system prompt. Please try again.";
        } else if (error.message.includes('Incomplete response')) {
          errorTitle = "Incomplete Extraction";
          errorDescription = "The extraction service returned incomplete data. Please try again or contact support if the issue persists.";
        } else {
          errorDescription = error.message;
        }
      }

      toast({
        title: errorTitle,
        description: errorDescription,
        variant: "destructive",
      });
      setStep('configure');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVAPIDeployment = async (deployCompanyInfo?: CompanyInfo, deploySystemPrompt?: string) => {
    console.log('🎯 handleVAPIDeployment called with:', {
      deployCompanyInfo,
      deploySystemPrompt: deploySystemPrompt ? `${deploySystemPrompt.length} chars` : 'null',
      currentCompanyInfo: companyInfo,
      currentSystemPrompt: systemPrompt ? `${systemPrompt.length} chars` : 'null'
    });

    // Use provided parameters or fall back to state
    const activeCompanyInfo = deployCompanyInfo || companyInfo;
    const activeSystemPrompt = deploySystemPrompt || systemPrompt;

    console.log('🚀 Starting VAPI deployment...', {
      hasCompanyInfo: !!activeCompanyInfo,
      hasSystemPrompt: !!activeSystemPrompt,
      companyName: activeCompanyInfo?.name,
      systemPromptLength: activeSystemPrompt?.length
    });

    if (!activeCompanyInfo || !activeSystemPrompt) {
      console.error('❌ VAPI deployment failed - missing requirements:', {
        companyInfo: !!activeCompanyInfo,
        systemPrompt: !!activeSystemPrompt,
        companyInfoDetails: activeCompanyInfo,
        systemPromptPreview: activeSystemPrompt ? activeSystemPrompt.substring(0, 100) + '...' : null
      });
      toast({
        title: "Missing Information",
        description: "Company information and system prompt are required",
        variant: "destructive",
      });
      return;
    }

    setStep('deploying');
    setIsLoading(true);

    try {
      // Step 1: Create VAPI Agent
      toast({
        title: "Creating VAPI Agent",
        description: "Creating voice AI agent with MASTER_TEMPLATE integration...",
      });

      const vapiResult = await createVAPIAgent(activeCompanyInfo, activeSystemPrompt);

      if (!vapiResult.success || !vapiResult.agent_id) {
        throw new Error(vapiResult.error || 'Failed to create VAPI agent');
      }

      // Step 2: Deploy Demo HTML Page
      toast({
        title: "Deploying Demo Page",
        description: "Creating live demo with voice AI integration...",
      });

      const demoResult = await deployDemoPage(activeCompanyInfo, vapiResult.agent_id, extractedWebsiteContent);

      if (!demoResult.success || !demoResult.demoUrl) {
        throw new Error(demoResult.error || 'Failed to deploy demo page');
      }

      // Step 3: Save Automation Config to MongoDB
      toast({
        title: "Saving Configuration",
        description: "Persisting automation configuration to database...",
      });

      const automationConfig = await saveAutomationConfig(
        activeCompanyInfo,
        vapiResult.agent_id,
        demoResult.demoUrl,
        activeSystemPrompt
      );

      if (!automationConfig.success) {
        console.warn('Failed to save automation config:', automationConfig.error);
        // Continue with deployment even if persistence fails
      }

      // Step 4: Set Deployment Result
      const finalResult = {
        success: true,
        automation_config_id: automationConfig.id,
        vapi_assistant_id: vapiResult.agent_id,
        demo_url: demoResult.demoUrl,
        company_info: activeCompanyInfo,
        system_prompt: activeSystemPrompt,
        deployment_type: 'vapi_quick_deploy',
        timestamp: new Date().toISOString()
      };

      setDeploymentResult(finalResult);
      setVapiAssistantId(vapiResult.agent_id);
      setStep('completed');

      const successMessage = automationConfig.success
        ? `Your AI voice assistant for ${activeCompanyInfo.name} is live and ready to use! Configuration saved with ID: ${automationConfig.id}`
        : `Your AI voice assistant for ${activeCompanyInfo.name} is live and ready to use! (Configuration save failed: ${automationConfig.error})`;

      toast({
        title: "🎉 VAPI Deployment Complete!",
        description: successMessage,
      });

    } catch (error) {
      toast({
        title: "Deployment Failed",
        description: error instanceof Error ? error.message : "Unknown deployment error",
        variant: "destructive",
      });
      setStep('configure');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeploy = async () => {
    if (!companyInfo || !automationType || !systemPrompt) {
      toast({
        title: "Missing Configuration",
        description: "Please complete extraction first",
        variant: "destructive",
      });
      return;
    }

    setStep('deploying');
    setIsLoading(true);

    try {
      // First, get the master Vapi template
      const masterTemplatesResponse = await fetch(`${API_BASE_URL}/automation-orchestration/master-templates?template_type=master_vapi`, {
        method: 'GET',
        headers: await getAuthHeaders(),
      });

      if (!masterTemplatesResponse.ok) {
        throw new Error('Failed to get master templates');
      }

      const masterTemplatesData = await masterTemplatesResponse.json();
      const masterTemplate = masterTemplatesData.templates[0];

      if (!masterTemplate) {
        throw new Error('Master Vapi template not found');
      }

      // Create automation configuration using the same structure as AutomationDeploymentWizard
      const configData = createAutomationConfig(template, companyInfo);

      // Save configuration first
      const saveResult = await automationOrchestrationService.createConfiguration(configData);

      if (!saveResult || !saveResult.configuration) {
        throw new Error("Failed to create automation configuration");
      }

      const currentConfigId = saveResult.configuration.id;
      setConfigId(currentConfigId);

      // Deploy the configuration using the same method as AutomationDeploymentWizard
      const deployResult = await automationOrchestrationService.deployConfiguration(currentConfigId);

      if (deployResult.success) {
        setDeploymentResult(deployResult);
        setStep('completed');

        // Run post-deployment tests
        try {
          const testResult = await automationOrchestrationService.testConfiguration(
            currentConfigId,
            'deployment_verification'
          );

          if (testResult.success && testResult.summary.failed === 0) {
            toast({
              title: "🎉 Automation Deployed Successfully",
              description: `Your ${selectedAutomationType?.name} is live and fully functional!`,
            });
          } else {
            toast({
              title: "Deployment Complete with Warnings",
              description: `Automation deployed but some tests failed. Check the results for details.`,
              variant: "destructive",
            });
          }
        } catch (testError) {
          // Tests failed but deployment succeeded
          toast({
            title: "Deployment Successful",
            description: `Your ${selectedAutomationType?.name} is deployed but post-deployment tests failed`,
          });
        }
      } else {
        throw new Error(deployResult.error || "Deployment failed");
      }
    } catch (error) {
      toast({
        title: "Deployment Failed",
        description: error instanceof Error ? error.message : "Failed to deploy automation",
        variant: "destructive",
      });
      setStep('configure');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied",
      description: "Copied to clipboard",
    });
  };

  const renderConfigurationStep = () => (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-4">
          <div>
            <Label htmlFor="companyUrl">Company Website URL *</Label>
            <Input
              id="companyUrl"
              type="url"
              placeholder="https://company.com"
              value={companyUrl}
              onChange={(e) => setCompanyUrl(e.target.value)}
              className="mt-1"
            />
            <p className="text-sm text-gray-600 mt-1">
              We'll extract company information to customize your automation
            </p>
          </div>

          <div>
            <Label htmlFor="automationType">Automation Type *</Label>
            <Select value={automationType} onValueChange={setAutomationType}>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Select automation type" />
              </SelectTrigger>
              <SelectContent>
                {automationTypes.map((type) => {
                  const Icon = type.icon;
                  return (
                    <SelectItem key={type.id} value={type.id}>
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4" />
                        <div>
                          <div className="font-medium">{type.name}</div>
                          <div className="text-xs text-gray-600">{type.description}</div>
                        </div>
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          {selectedAutomationType && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <selectedAutomationType.icon className="h-4 w-4" />
                  {selectedAutomationType.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-sm text-gray-600 mb-3">
                  {selectedAutomationType.description}
                </p>
                <div className="space-y-2">
                  <div className="text-xs font-medium">Included Integrations:</div>
                  <div className="flex flex-wrap gap-1">
                    {selectedAutomationType.integrations.map((integration) => (
                      <Badge key={integration} variant="secondary" className="text-xs">
                        {integration.replace('_', ' ')}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          <div>
            <Label htmlFor="industry">Industry</Label>
            <Select value={industry} onValueChange={setIndustry}>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Select industry (auto-detected)" />
              </SelectTrigger>
              <SelectContent>
                {industries.map((ind) => (
                  <SelectItem key={ind} value={ind}>{ind}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="personality">Voice Personality</Label>
            <Select value={personality} onValueChange={setPersonality}>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Select personality (auto-suggested)" />
              </SelectTrigger>
              <SelectContent>
                {personalities.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    <div>
                      <div className="font-medium">{p.name}</div>
                      <div className="text-xs text-gray-600">{p.description}</div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="assistantName">Assistant Name</Label>
            <Input
              id="assistantName"
              placeholder={companyInfo ? `${companyInfo.name} Assistant` : "e.g., Sarah from Acme Corp"}
              value={assistantName}
              onChange={(e) => setAssistantName(e.target.value)}
              className="mt-1"
            />
            <p className="text-sm text-gray-600 mt-1">
              This name will be used when creating your VAPI assistant
            </p>
          </div>

          <div>
            <Label htmlFor="customInstructions">Custom Instructions (Optional)</Label>
            <Textarea
              id="customInstructions"
              placeholder="Any specific instructions for your automation..."
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              className="mt-1 min-h-[100px]"
            />
          </div>
        </div>
      </div>

      {/* Custom Tools Selection */}
      <div className="space-y-4">
        <div>
          <Label className="text-base font-medium">Select Tools for Your Agent</Label>
          <p className="text-sm text-gray-600 mt-1">
            Choose which tools your voice agent will have access to. Default tools are pre-selected.
          </p>
        </div>

        {toolsLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2 text-sm text-gray-600">Loading available tools...</span>
          </div>
        ) : (
          <CustomToolsSelector
            selectedTools={selectedTools}
            onToolsChange={setSelectedTools}
            availableTools={availableTools}
            showAnalytics={false}
            maxHeight="300px"
          />
        )}

        {selectedTools.length > 0 && (
          <div className="text-sm text-gray-600">
            {selectedTools.length} tool{selectedTools.length !== 1 ? 's' : ''} selected
            {selectedTools.filter(t => t.vapi_tool_id).length !== selectedTools.length && (
              <span className="text-yellow-600 ml-2">
                ({selectedTools.filter(t => !t.vapi_tool_id).length} without VAPI ID)
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex gap-3">
        <Button
          onClick={handleExtractCompanyInfo}
          disabled={!companyUrl || !automationType || selectedTools.filter(t => t.vapi_tool_id).length === 0}
          className="flex-1"
        >
          <Globe className="h-4 w-4 mr-2" />
          Extract Company Info & Deploy
        </Button>
      </div>
    </div>
  );

  const renderExtractionStep = () => (
    <div className="text-center space-y-6">
      <div className="flex justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
      </div>
      <div>
        <h3 className="text-lg font-semibold">AI-Powered Content Extraction</h3>
        <p className="text-gray-600">
          Using advanced AI to intelligently analyze your website content...
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <div className="p-4 bg-blue-50 rounded-lg border">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-5 w-5 text-blue-600" />
            <span className="font-medium text-blue-800">AI Processing</span>
          </div>
          <p className="text-sm text-blue-600">
            Advanced language models extract structured business information
          </p>
        </div>

        <div className="p-4 bg-green-50 rounded-lg border">
          <div className="flex items-center gap-2 mb-2">
            <Globe className="h-5 w-5 text-green-600" />
            <span className="font-medium text-green-800">Multi-Page Crawling</span>
          </div>
          <p className="text-sm text-green-600">
            Analyzing up to 3 pages for comprehensive company insights
          </p>
        </div>

        <div className="p-4 bg-purple-50 rounded-lg border">
          <div className="flex items-center gap-2 mb-2">
            <Bot className="h-5 w-5 text-purple-600" />
            <span className="font-medium text-purple-800">System Prompt Generation</span>
          </div>
          <p className="text-sm text-purple-600">
            Generating AI assistant prompts with master template integration
          </p>
        </div>
      </div>
    </div>
  );

  const renderDeployingStep = () => (
    <div className="space-y-6">
      {companyInfo && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              Company Information Extracted
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h4 className="font-medium">{companyInfo.name}</h4>
                <p className="text-sm text-gray-600">{companyInfo.description}</p>
              </div>
              <div>
                <div className="text-sm">
                  <strong>Services:</strong> {companyInfo.services.join(', ')}
                </div>
                <div className="text-sm">
                  <strong>Business Hours:</strong> {companyInfo.businessHours}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="text-center space-y-4">
        <div className="flex justify-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Deploying Your Automation</h3>
          <p className="text-gray-600">
            Setting up voice assistant, integrations, and workflows...
          </p>
        </div>
      </div>

      <div className="bg-muted/50 rounded-lg p-4 space-y-2">
        <div className="flex items-center gap-2 text-sm">
          <Bot className="h-4 w-4" />
          Creating AI assistant with {selectedAutomationType?.name} capabilities
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Settings className="h-4 w-4" />
          Configuring {selectedAutomationType?.integrations.length} integrations
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Phone className="h-4 w-4" />
          Provisioning phone number and voice settings
        </div>
      </div>
    </div>
  );

  const renderCompletedStep = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex justify-center mb-4">
          <div className="h-16 w-16 bg-green-100 rounded-full flex items-center justify-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <h3 className="text-xl font-semibold">Automation Deployed Successfully!</h3>
        <p className="text-gray-600">
          Your {selectedAutomationType?.name} is now live and ready to handle calls
        </p>
      </div>

      {deploymentResult && (
        <Tabs defaultValue="details" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="integrations">Integrations</TabsTrigger>
            <TabsTrigger value="testing">Testing</TabsTrigger>
          </TabsList>

          <TabsContent value="details" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Deployment Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {deploymentResult.phone_number_id && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Phone className="h-4 w-4" />
                      <span className="font-medium">Phone Number</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono">{deploymentResult.phone_number_id}</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => copyToClipboard(deploymentResult.phone_number_id!)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                )}

                {deploymentResult.vapi_assistant_id && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4" />
                      <span className="font-medium">Assistant ID</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">{deploymentResult.vapi_assistant_id}</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => copyToClipboard(deploymentResult.vapi_assistant_id!)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                )}
                {deploymentResult.automation_config_id && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Settings className="h-4 w-4" />
                      <span className="font-medium">Automation Config ID</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">{deploymentResult.automation_config_id}</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => copyToClipboard(deploymentResult.automation_config_id!)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                )}

                {deploymentResult.n8n_workflow_id && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Settings className="h-4 w-4" />
                      <span className="font-medium">N8N Workflow ID</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">{deploymentResult.n8n_workflow_id}</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => copyToClipboard(deploymentResult.n8n_workflow_id!)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                )}

                {deploymentResult.demo_url && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ExternalLink className="h-4 w-4" />
                      <span className="font-medium">Demo URL</span>
                    </div>
                    <Button size="sm" variant="outline" asChild>
                      <a href={deploymentResult.demo_url} target="_blank" rel="noopener noreferrer">
                        Open Demo
                      </a>
                    </Button>
                  </div>
                )}

                {deploymentResult.automation_config_id && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        <div>
                          <span className="font-medium text-green-800">Automation Configuration Saved</span>
                          <p className="text-sm text-green-600 mt-1">
                            Your automation has been persisted to the database and can be managed, duplicated, or modified.
                          </p>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-green-300 text-green-700 hover:bg-green-100"
                        onClick={() => {
                          // Navigate to automation management page with the config ID
                          window.open(`/automations/manage?config=${deploymentResult.automation_config_id}`, '_blank');
                        }}
                      >
                        <Settings className="h-4 w-4 mr-1" />
                        Manage Automation
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="integrations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Active Integrations</CardTitle>
                <CardDescription>
                  These integrations are ready to use with your voice assistant
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2">
                  {selectedAutomationType?.integrations.map((integration) => (
                    <div key={integration} className="flex items-center justify-between py-2 border-b last:border-0">
                      <span className="capitalize">{integration.replace('_', ' ')}</span>
                      <Badge variant="default">Active</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {deploymentResult.webhook_urls && Object.keys(deploymentResult.webhook_urls).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Webhook URLs</CardTitle>
                  <CardDescription>
                    Integration endpoints for your automation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(deploymentResult.webhook_urls).map(([name, url]) => (
                      <div key={name} className="flex items-center justify-between text-sm">
                        <span className="capitalize">{name}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs truncate max-w-xs">{url}</span>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => copyToClipboard(url)}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="testing" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Test Your Automation</CardTitle>
                <CardDescription>
                  Try calling your automation to test its functionality
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {deploymentResult.phone_number_id && (
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Phone className="h-5 w-5 text-green-600" />
                      <span className="font-medium">Call Now to Test</span>
                    </div>
                    <p className="text-2xl font-mono text-green-700 mb-2">
                      {deploymentResult.phone_number_id}
                    </p>
                    <p className="text-sm text-green-600">
                      Your {selectedAutomationType?.name} is ready to handle calls
                    </p>
                  </div>
                )}

                <div className="space-y-2">
                  <h4 className="font-medium">Test Scenarios:</h4>
                  {automationType === 'sales' && (
                    <ul className="text-sm space-y-1 text-gray-600">
                      <li>• "I'm interested in your services"</li>
                      <li>• "Can you tell me about pricing?"</li>
                      <li>• "I'd like to schedule a demo"</li>
                    </ul>
                  )}
                  {automationType === 'helpdesk' && (
                    <ul className="text-sm space-y-1 text-gray-600">
                      <li>• "I'm having trouble with my account"</li>
                      <li>• "I need technical support"</li>
                      <li>• "Can you create a support ticket?"</li>
                    </ul>
                  )}
                  {automationType === 'healthcare' && (
                    <ul className="text-sm space-y-1 text-gray-600">
                      <li>• "I need to schedule an appointment"</li>
                      <li>• "Can you help me find a doctor?"</li>
                      <li>• "What are your office hours?"</li>
                    </ul>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      <div className="flex gap-3">
        <Button
          onClick={() => {
            setStep('configure');
            setCompanyUrl('');
            setAutomationType('');
            setIndustry('');
            setPersonality('');
            setCustomInstructions('');
            setCompanyInfo(null);
            setDeploymentResult(null);
            setExtractionComplete(false);
          }}
          variant="outline"
          className="flex-1"
        >
          Deploy Another
        </Button>
        <Button variant="default" className="flex-1" asChild>
          <a href="/dashboard" target="_blank">
            <BarChart3 className="h-4 w-4 mr-2" />
            View Analytics
          </a>
        </Button>
      </div>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Quick VAPI Deployment</h1>
        <p className="text-gray-600 text-lg">
          Turn any company website into a working VAPI voice assistant with master template integration in minutes
        </p>
      </div>

      {/* Progress Indicator */}
      <div className="flex items-center justify-center space-x-4 mb-8">
        <div className={`flex items-center space-x-2 ${step === 'configure' ? 'text-blue-600' : step !== 'configure' ? 'text-green-600' : 'text-gray-600'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'configure' ? 'bg-blue-100 text-blue-600' : step !== 'configure' ? 'bg-green-100 text-green-600' : 'bg-muted text-gray-600'}`}>
            1
          </div>
          <span className="font-medium">Configure</span>
        </div>
        <div className={`w-8 h-0.5 ${step === 'extracting' || step === 'deploying' || step === 'completed' ? 'bg-green-600' : 'bg-muted'}`} />
        <div className={`flex items-center space-x-2 ${step === 'extracting' || step === 'deploying' ? 'text-blue-600' : step === 'completed' ? 'text-green-600' : 'text-gray-600'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'extracting' || step === 'deploying' ? 'bg-blue-100 text-blue-600' : step === 'completed' ? 'bg-green-100 text-green-600' : 'bg-muted text-gray-600'}`}>
            2
          </div>
          <span className="font-medium">Deploy</span>
        </div>
        <div className={`w-8 h-0.5 ${step === 'completed' ? 'bg-green-600' : 'bg-muted'}`} />
        <div className={`flex items-center space-x-2 ${step === 'completed' ? 'text-green-600' : 'text-gray-600'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'completed' ? 'bg-green-100 text-green-600' : 'bg-muted text-gray-600'}`}>
            3
          </div>
          <span className="font-medium">Complete</span>
        </div>
      </div>

      <Card>
        <CardContent className="p-8">
          {step === 'configure' && renderConfigurationStep()}
          {step === 'extracting' && renderExtractionStep()}
          {step === 'deploying' && renderDeployingStep()}
          {step === 'completed' && renderCompletedStep()}
        </CardContent>
      </Card>

      {deploymentResult?.warnings && deploymentResult.warnings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-600">
              <AlertTriangle className="h-5 w-5" />
              Deployment Warnings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {deploymentResult.warnings.map((warning, index) => (
                <li key={index} className="text-sm text-amber-600">• {warning}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}