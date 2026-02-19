import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";
import { Badge } from "@/components/ui/badge";
import { X, Upload, FileText, ChevronLeft, ChevronRight, Globe, MessageSquare, Code, Sparkles, Edit, Save, RotateCcw } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import type { Json } from "@/integrations/supabase/types";
import VoiceAgentTemplates, { VoiceTemplate } from "@/components/VoiceAgentTemplates";
import TemplateCustomization, { CustomTemplate } from "@/components/TemplateCustomization";

// Minimal assistant types
const ASSISTANT_TYPES = [
  { value: "sales_cold_call", label: "Sales - Cold Call" },
  { value: "help_desk", label: "Help Desk" },
  { value: "follow_up", label: "Follow-up (e.g. Church)" },
  { value: "survey", label: "Survey" },
  { value: "appointment_booking", label: "Appointment Booking" },
  { value: "customer_service", label: "Customer Service" },
  { value: "lead_qualification", label: "Lead Qualification" },
  { value: "product_support", label: "Product Support" },
  { value: "order_tracking", label: "Order Tracking" },
  { value: "feedback_collection", label: "Feedback Collection" },
  { value: "technical_support", label: "Technical Support" },
  { value: "consultation", label: "Consultation" },
];

interface VoiceOption { id: string; name: string }

interface SiteInfo {
  title: string;
  description: string;
  content: string;
}

interface StepWizardProps {
  currentStep: number;
  totalSteps: number;
  onNext: () => void;
  onPrevious: () => void;
  canNext: boolean;
  isLoading?: boolean;
  onSaveProgress: () => void;
  onLoadProgress: () => void;
  onClearProgress: () => void;
  hasSavedProgress: boolean;
}

const StepWizard = ({ currentStep, totalSteps, onNext, onPrevious, canNext, isLoading, onSaveProgress, onLoadProgress, onClearProgress, hasSavedProgress }: StepWizardProps) => (
  <div className="space-y-4">
    {/* Progress indicator */}
    <div className="flex items-center justify-between">
      <Button 
        variant="outline" 
        onClick={onPrevious} 
        disabled={currentStep === 1 || isLoading}
        className="flex items-center gap-2"
      >
        <ChevronLeft className="h-4 w-4" />
        Previous
      </Button>
      
      <div className="flex items-center gap-2">
        {Array.from({ length: totalSteps }, (_, i) => (
          <div
            key={i}
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              i + 1 === currentStep
                ? "bg-primary text-primary-foreground"
                : i + 1 < currentStep
                ? "bg-green-500 text-white"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {i + 1}
          </div>
        ))}
      </div>
      
      <Button 
        onClick={onNext} 
        disabled={!canNext || isLoading}
        className="flex items-center gap-2"
      >
        {currentStep === totalSteps ? "Deploy" : "Next"}
        {currentStep !== totalSteps && <ChevronRight className="h-4 w-4" />}
      </Button>
    </div>

    {/* Save progress section */}
    <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
      <div className="flex items-center gap-2">
        <Save className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Save your progress at any time</span>
      </div>
      
      <div className="flex gap-2">
        {hasSavedProgress && (
          <Button
            variant="outline"
            size="sm"
            onClick={onLoadProgress}
            disabled={isLoading}
            className="flex items-center gap-2"
          >
            <RotateCcw className="h-3 w-3" />
            Load Progress
          </Button>
        )}
        
        <Button
          variant="outline"
          size="sm"
          onClick={onSaveProgress}
          disabled={isLoading}
          className="flex items-center gap-2"
        >
          <Save className="h-3 w-3" />
          {isLoading ? "Saving..." : "Save Progress"}
        </Button>
        
        {hasSavedProgress && (
          <Button
            variant="outline"
            size="sm"
            onClick={onClearProgress}
            disabled={isLoading}
            className="text-destructive hover:text-destructive"
          >
            Clear
          </Button>
        )}
      </div>
    </div>
  </div>
);

const CreateAssistant = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  // Form state
  const [assistantName, setAssistantName] = useState("");
  const [description, setDescription] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [assistantType, setAssistantType] = useState<string>(ASSISTANT_TYPES[0].value);
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [voiceId, setVoiceId] = useState<string>("");
  const [knowledgeBase, setKnowledgeBase] = useState<File[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<{id: string, name: string, size: number}[]>([]);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  
  // Wizard state
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [hasProgress, setHasProgress] = useState(false);
  const [isGuestMode, setIsGuestMode] = useState(false);
  const [siteInfo, setSiteInfo] = useState<SiteInfo | null>(null);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [htmlCode, setHtmlCode] = useState("");
  const [assistantId, setAssistantId] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState<VoiceTemplate | CustomTemplate | null>(null);
  const [useTemplate, setUseTemplate] = useState(false);
  const [showTemplateCustomization, setShowTemplateCustomization] = useState(false);

  // Debug state for development
  const [debugMode, setDebugMode] = useState(import.meta.env.DEV);
  const [debugInfo, setDebugInfo] = useState<string>("");

  const totalSteps = 6;

  // File upload functions
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    setUploadingFiles(true);
    const newFiles = Array.from(files);
    
    try {
      const uploadPromises = newFiles.map(async (file) => {
        // Check file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
          throw new Error(`File ${file.name} is too large. Maximum size is 10MB.`);
        }
        
        // Check file type
        const allowedTypes = [
          'application/pdf',
          'text/plain',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
          'application/msword', // .doc
          'text/csv',
          'application/json'
        ];
        
        if (!allowedTypes.includes(file.type)) {
          throw new Error(`File type ${file.type} is not supported. Supported types: PDF, TXT, DOC, DOCX, CSV, JSON`);
        }
        
        // Create FormData for upload
        const formData = new FormData();
        formData.append('file', file);
        
        // Upload to Vapi
        const response = await fetch('https://api.vapi.ai/file', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${import.meta.env.VITE_VAPI_PRIVATE_KEY}`
          },
          body: formData
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(`Upload failed: ${errorData.message || response.statusText}`);
        }
        
        const fileData = await response.json();
        return {
          id: fileData.id,
          name: file.name,
          size: file.size
        };
      });
      
      const uploadedFileData = await Promise.all(uploadPromises);
      setUploadedFiles(prev => [...prev, ...uploadedFileData]);
      setKnowledgeBase(prev => [...prev, ...newFiles]);
      
      toast({
        title: "Files Uploaded",
        description: `Successfully uploaded ${newFiles.length} file(s) to knowledge base.`,
        duration: 3000,
      });
    } catch (error) {
      console.error('File upload error:', error);
      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : "Failed to upload files.",
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      setUploadingFiles(false);
    }
  };

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    setKnowledgeBase(prev => prev.filter((_, index) => 
      !uploadedFiles.find(f => f.id === fileId) || 
      uploadedFiles.findIndex(f => f.id === fileId) !== index
    ));
  };

  useEffect(() => {
    document.title = "Create Voice AI Assistant | AI Labs Africa";
  }, []);

  // Save form state to localStorage
  const saveFormState = () => {
    const formData = {
      assistantName,
      description,
      websiteUrl,
      assistantType,
      useTemplate,
      selectedTemplate,
      voiceId,
      knowledgeBaseCount: knowledgeBase.length // Use knowledgeBase.length consistently
    };
    localStorage.setItem("create_assistant_form", JSON.stringify(formData));
  };

  // Save progress for current step
  const saveProgress = async () => {
    try {
      setLoading(true);
      
      const progressData = {
        step: currentStep,
        timestamp: new Date().toISOString(),
        data: {
          assistantName,
          description,
          websiteUrl,
          assistantType,
          useTemplate,
          selectedTemplate: selectedTemplate || null, // Remove unnecessary JSON.parse(JSON.stringify())
          voiceId,
          knowledgeBaseCount: knowledgeBase.length, // Use knowledgeBase.length consistently
          siteInfo,
          systemPrompt,
          htmlCode,
          assistantId
        }
      };

      // Save to localStorage for immediate access
      localStorage.setItem("create_assistant_progress", JSON.stringify(progressData));
      
      // Also save to database if user is authenticated (simplified for now)
      if (user) {
        try {
          const { error } = await supabase
            .from('assistant_drafts')
            .upsert({
              user_id: user.id,
              step: currentStep,
              data: progressData.data as Json, // Remove unnecessary JSON.parse(JSON.stringify())
              updated_at: new Date().toISOString()
            }, {
              onConflict: 'user_id'
            });
          
          if (error) {
            console.warn("Failed to save to database:", error);
          }
        } catch (dbError) {
          console.warn("Database save failed, using localStorage only:", dbError);
        }
      }

      toast({
        title: "Progress Saved",
        description: `Your progress has been saved at step ${currentStep}.`,
        duration: 3000,
      });
      
      // Update hasProgress state
      setHasProgress(true);
    } catch (error) {
      console.error("Failed to save progress:", error);
      toast({
        title: "Save Failed",
        description: "Failed to save progress. Please try again.",
        variant: "destructive",
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  // Load saved progress
  const loadProgress = async () => {
    try {
      // Try to load from database first (if authenticated)
      if (user) {
        const { data, error } = await supabase
          .from('assistant_drafts')
          .select('*')
          .eq('user_id', user.id)
          .single();
        
        if (data && !error) {
          const savedData = data.data as Record<string, unknown>; // Type assertion for database data
          setAssistantName((savedData.assistantName as string) || "");
          setDescription((savedData.description as string) || "");
          setWebsiteUrl((savedData.websiteUrl as string) || "");
          setAssistantType((savedData.assistantType as string) || ASSISTANT_TYPES[0].value);
          setUseTemplate((savedData.useTemplate as boolean) || false);
          setSelectedTemplate((savedData.selectedTemplate as VoiceTemplate | CustomTemplate) || null);
          setVoiceId((savedData.voiceId as string) || "");
          setSiteInfo((savedData.siteInfo as SiteInfo) || null);
          setSystemPrompt((savedData.systemPrompt as string) || "");
          setHtmlCode((savedData.htmlCode as string) || "");
          setAssistantId((savedData.assistantId as string) || "");
          setCurrentStep(data.step || 1);
          
          toast({
            title: "Progress Loaded",
            description: `Resumed from step ${data.step}.`,
            duration: 3000,
          });
          
          // Update hasProgress state
          setHasProgress(true);
          return;
        }
      }

      // Fallback to localStorage
      const cached = localStorage.getItem("create_assistant_progress");
      if (cached) {
        const progressData = JSON.parse(cached);
        const savedData = progressData.data;
        
        setAssistantName(savedData.assistantName || "");
        setDescription(savedData.description || "");
        setWebsiteUrl(savedData.websiteUrl || "");
        setAssistantType(savedData.assistantType || ASSISTANT_TYPES[0].value);
        setUseTemplate(savedData.useTemplate || false);
        setSelectedTemplate(savedData.selectedTemplate || null);
        setVoiceId(savedData.voiceId || "");
        setSiteInfo(savedData.siteInfo || null);
        setSystemPrompt(savedData.systemPrompt || "");
        setHtmlCode(savedData.htmlCode || "");
        setAssistantId(savedData.assistantId || "");
        setCurrentStep(progressData.step || 1);
        
        toast({
          title: "Progress Loaded",
          description: `Resumed from step ${progressData.step}.`,
          duration: 3000,
        });
        
        // Update hasProgress state
        setHasProgress(true);
      }
    } catch (error) {
      console.warn("Failed to load progress:", error);
    }
  };

  // Check if there's saved progress
  const hasSavedProgress = async () => {
    // Check localStorage first
    const localProgress = localStorage.getItem("create_assistant_progress");
    if (localProgress) {
      return true;
    }
    
    // Check database if user is authenticated
    if (user) {
      try {
        const { data, error } = await supabase
          .from('assistant_drafts')
          .select('id')
          .eq('user_id', user.id)
          .single();
        
        return !error && data !== null;
      } catch (error) {
        console.warn("Failed to check database progress:", error);
        return false;
      }
    }
    
    return false;
  };

  // Clear saved progress
  const clearProgress = async () => {
    localStorage.removeItem("create_assistant_progress");
    localStorage.removeItem("create_assistant_form");
    
    if (user) {
      try {
        await supabase
          .from('assistant_drafts')
          .delete()
          .eq('user_id', user.id);
        console.log("Cleared saved progress from database");
      } catch (error) {
        console.warn("Failed to clear database progress:", error);
      }
    }
    
    toast({
      title: "Progress Cleared",
      description: "All saved progress has been cleared.",
      duration: 3000,
    });
    
    // Update hasProgress state
    setHasProgress(false);
  };

  useEffect(() => {
    // Clear localStorage to remove any corrupted data
    localStorage.removeItem("create_assistant_form");
    
    // Check for saved progress
    const checkSavedProgress = async () => {
      const hasProgressResult = await hasSavedProgress();
      setHasProgress(hasProgressResult);
    };
    
    checkSavedProgress();
    
    // Restore cached form state
    const cached = localStorage.getItem("create_assistant_form");
    if (cached) {
      try {
        const data = JSON.parse(cached);
        setAssistantName(data.assistantName || "");
        setDescription(data.description || "");
        setWebsiteUrl(data.websiteUrl || "");
        setAssistantType(data.assistantType || ASSISTANT_TYPES[0].value);
        setUseTemplate(data.useTemplate || false);
        
        // Handle selectedTemplate restoration more carefully
        if (data.selectedTemplate) {
          // Only restore if it's a valid template with required properties
          if (data.selectedTemplate.icon && typeof data.selectedTemplate.icon === 'string') {
            const restoredTemplate = {
              ...data.selectedTemplate,
              icon: data.selectedTemplate.icon
            };
            setSelectedTemplate(restoredTemplate as VoiceTemplate | CustomTemplate);
          } else {
            setSelectedTemplate(null);
          }
        } else {
          setSelectedTemplate(null);
        }
        
        if (data.voiceId) setVoiceId(data.voiceId);
      } catch (error) {
        console.warn("Failed to restore cached form state:", error);
      }
    }
  }, []);

  // Save form state whenever relevant fields change
  useEffect(() => {
    if (assistantName || description || websiteUrl) {
      saveFormState();
    }
  }, [assistantName, description, websiteUrl, assistantType, useTemplate, voiceId, knowledgeBase.length, saveFormState]);

  // Save full progress when template is configured
  useEffect(() => {
    if (selectedTemplate && selectedTemplate.integrations) {
      // Template has been configured, save full progress
      saveProgress();
    }
  }, [selectedTemplate, saveProgress]);

  // Auto-generate system prompt when reaching step 4
  useEffect(() => {
    if (currentStep === 4 && !systemPrompt && !loading) {
      console.log("[CreateAssistant] Auto-generating system prompt for step 4");
      generateSystemPrompt();
    }
  }, [currentStep, systemPrompt, loading]);

  // Debug system prompt changes
  useEffect(() => {
    console.log("[CreateAssistant] System prompt changed:", {
      length: systemPrompt.length,
      isEmpty: systemPrompt === "",
      currentStep
    });
  }, [systemPrompt, currentStep]);

  useEffect(() => {
    // Load voices from Edge Function
    (async () => {
      try {
        const { data, error } = await supabase.functions.invoke("list-vapi-voices");
        if (error) throw error;
        const list = (data?.voices as VoiceOption[]) || [];
        setVoices(list);
        if (list.length) setVoiceId(list[0].id);
      } catch (e: unknown) {
        console.error("Failed to load voices", e);
        setVoices([{ id: "Paige", name: "Paige" }]);
        setVoiceId("Paige");
      }
    })();
  }, []);

  // Guest mode state
  const [guestEmail, setGuestEmail] = useState("");
  const [guestPassword, setGuestPassword] = useState("");

  // Removed ensureAuth function - authentication is now handled directly in handleNext

  const handleGuestModeSubmit = async () => {
    if (!guestEmail || !guestPassword) {
      toast({
        title: "Error",
        description: "Please enter both email and password for guest mode",
        variant: "destructive",
      });
      return;
    }

    if (guestPassword.length < 6) {
      toast({
        title: "Error",
        description: "Password must be at least 6 characters long",
        variant: "destructive",
      });
      return;
    }

    setIsGuestMode(false);
    
    // Now proceed to create the assistant
    try {
      console.log("[CreateAssistant] Guest mode setup complete, creating assistant...");
      await createVapiAssistant();
      console.log("[CreateAssistant] Guest assistant created, moving to step 5");
      setCurrentStep(5);
    } catch (error) {
      console.error("Failed to create assistant after guest mode setup:", error);
      toast({
        title: "Error",
        description: "Failed to create assistant. Please try again.",
        variant: "destructive",
      });
    }
  };



  const extractSiteInfo = async () => {
    if (!websiteUrl) {
      setSiteInfo({ title: "", description: "", content: "No website URL provided" });
      return;
    }

    setLoading(true);
    try {
      console.log("[CreateAssistant] Starting site extraction for:", websiteUrl);
      
      // Validate URL format
      let validUrl = websiteUrl;
      if (!websiteUrl.startsWith('http://') && !websiteUrl.startsWith('https://')) {
        validUrl = 'https://' + websiteUrl;
        console.log("[CreateAssistant] Added https:// prefix:", validUrl);
      }

      // Use the extract-site-info edge function to avoid CORS issues
      const { data, error } = await supabase.functions.invoke('extract-site-info', {
        body: { url: validUrl }
      });
      
      if (error) {
        console.error("[CreateAssistant] Edge function error:", error);
        throw new Error(`Edge function error: ${error.message || 'Unknown error'}`);
      }
      
      if (!data) {
        throw new Error('No data returned from site extraction');
      }
      
      console.log("[CreateAssistant] Site info extracted successfully:", {
        titleLength: data.title?.length || 0,
        descriptionLength: data.description?.length || 0,
        contentLength: data.content?.length || 0
      });
      
      setSiteInfo({
        title: data.title || assistantName,
        description: data.description || description,
        content: data.content || "No content extracted"
      });
      
    } catch (e: unknown) {
      console.error("[CreateAssistant] Site extraction error:", e);
      
      // Provide more specific error messages
      let errorMessage = "Failed to extract site information";
      const error = e as Error;
      if (error.message?.includes('Unauthorized')) {
        errorMessage = "Authentication required. Please sign in and try again.";
      } else if (error.message?.includes('fetch')) {
        errorMessage = "Unable to access the website. Please check the URL and try again.";
      } else if (error.message?.includes('CORS')) {
        errorMessage = "Website access blocked due to security restrictions.";
      } else if (error.message?.includes('timeout')) {
        errorMessage = "Website took too long to respond. Please try again.";
      } else {
        errorMessage = `Extraction failed: ${error.message}`;
      }
      
      // Set fallback information
      setSiteInfo({ 
        title: assistantName, 
        description: description, 
        content: `⚠️ ${errorMessage}\n\nPlease manually enter your company information below, or try again with a different website URL.` 
      });
      
      toast({ 
        title: "Site extraction failed", 
        description: errorMessage,
        variant: "destructive" 
      });
    } finally {
      setLoading(false);
    }
  };

  const generateSystemPrompt = async () => {
    setLoading(true);
    try {
      // Extract knowledge base content
      let knowledgeBaseContent = "";
      if (knowledgeBase.length > 0) {
        const contentPromises = knowledgeBase.map(async (file) => {
          try {
            const text = await file.text();
            return `### ${file.name}:\n${text}\n\n`;
          } catch (error) {
            console.error(`Error reading file ${file.name}:`, error);
            return `### ${file.name}:\n[Error reading file]\n\n`;
          }
        });
        
        const contents = await Promise.all(contentPromises);
        knowledgeBaseContent = contents.join("");
      }

      // If using a template, use the template's system prompt
      if (useTemplate && selectedTemplate) {
        let templatePrompt = 'systemPrompt' in selectedTemplate 
          ? selectedTemplate.systemPrompt 
          : selectedTemplate.system_prompt;
        
        // Replace placeholders with actual values
        templatePrompt = templatePrompt.replace(/{company_name}/g, assistantName);
        templatePrompt = templatePrompt.replace(/{business_name}/g, assistantName);
        templatePrompt = templatePrompt.replace(/{organization_name}/g, assistantName);
        templatePrompt = templatePrompt.replace(/{insurance_company}/g, assistantName);
        templatePrompt = templatePrompt.replace(/{real_estate_company}/g, assistantName);
        templatePrompt = templatePrompt.replace(/{medical_practice}/g, assistantName);
        templatePrompt = templatePrompt.replace(/{bank_name}/g, assistantName);
        
        // Add integration-specific instructions if configured
        if (selectedTemplate.integrations) {
          const integrations = selectedTemplate.integrations;
          let integrationInstructions = '\n\n---\n\n## 🔗 Integration Capabilities:\n';
          
          if (integrations.calendar?.type) {
            integrationInstructions += `- **Calendar Integration**: You can schedule appointments using the connected ${integrations.calendar.type} calendar\n`;
          }
          
          if (integrations.email?.provider) {
            integrationInstructions += `- **Email Integration**: You can send email confirmations and reminders using ${integrations.email.provider}\n`;
          }
          
          if (integrations.whatsapp?.enabled) {
            integrationInstructions += `- **WhatsApp Integration**: You can send WhatsApp messages for notifications and follow-ups\n`;
          }
          
          if (integrations.sheets?.enabled) {
            integrationInstructions += `- **Google Sheets Integration**: You can save appointment and contact data to Google Sheets\n`;
          }
          
          if (integrations.crm?.enabled) {
            integrationInstructions += `- **CRM Integration**: You can create and update customer records in the connected ${integrations.crm.provider} system\n`;
          }
          
          if (integrations.database?.enabled) {
            integrationInstructions += `- **Database Integration**: You can store all interaction data in the connected ${integrations.database.type} database\n`;
          }
          
          templatePrompt += integrationInstructions;
        }
        
        // Add company information if available
        if (siteInfo?.content) {
          templatePrompt += `\n\n---\n\n## 🏢 Company Information:\n${siteInfo.content.substring(0, 3000)}`;
        }
        
        // Add knowledge base content if available
        if (knowledgeBaseContent) {
          templatePrompt += `\n\n---\n\n## 📚 Additional Knowledge Base:\n${knowledgeBaseContent.substring(0, 2000)}`;
        }
        
        setSystemPrompt(templatePrompt);
        return;
      }

      // Base conversation guidelines for all assistants
      const baseGuidelines = `
## 🎯 Conversation Guidelines:
- **Speak slowly and clearly** - take your time with each response
- **Check in with the listener frequently** to ensure understanding and engagement
- **Mention numbers naturally** (e.g., "four thousand" instead of "four zero zero zero")
- **Keep conversations engaging** rather than delivering monologues
- **Format responses in markdown** when appropriate for better readability
- **Ask follow-up questions** to maintain dialogue flow
`;

      // Enhanced prompts with intelligent synthesis
      const typePrompts = {
        sales_cold_call: `You are ${assistantName}, a professional and friendly sales assistant. 
Your mission is to make calls to offer potential customers your company's products and services, 
answer questions, overcome objections, and guide customers toward quotes, claims, or sign-ups.

## 🎯 Your Role & Purpose:
${description ? `Based on your description: ${description}` : 'You are a professional sales assistant focused on helping customers find the right solutions for their needs.'}

---

${baseGuidelines}

## 💼 Sales-Specific Guidelines:
- **Warm, professional, and customer-centric approach**
- Always ask clarifying questions like:
  - "Would you like to know more about [specific product/service]?"
  - "Are you looking for personal or business solutions?"
- **Present information in small chunks** and check interest after each point
- **Build rapport** before presenting offers

---

## 🛡️ Common Objections & Rebuttals:

### "I don't have time now."
*"I understand. It takes less than a minute for me to share a quick highlight of our most popular solutions. Should I give you a brief overview?"*

### "I already have [similar service/product]."
*"That's great! Many customers choose us because we combine competitive pricing with exceptional service. Would you like me to share what makes our solutions stand out?"*

### "It's too expensive."
*"We have flexible, budget-friendly options available. Can I show you one of our affordable packages that might work for your situation?"*

### "I don't need [product/service]."
*"I understand. Our solutions are like a safety net—you may not need them now, but they protect you and your family in unexpected situations. Would you like to hear how this works?"*

### "I'm unsure if your company is reliable."
*"We're recognized as a trusted provider with a proven track record and smooth service delivery. Would you like to hear about our commitment to customer satisfaction?"*

### "What if I need support later?"
*"We're known for responsive, transparent support, and we make the process as easy as possible. Would you like me to explain how our support works?"*

---

## 🎯 Goals:
- Educate customers about products/services
- Overcome objections with confidence and clarity
- Direct customers to appropriate next steps (quotes, consultations, sign-ups)
- Build trust and rapport throughout the conversation`,

        help_desk: `You are ${assistantName}, a helpful customer support assistant. 
Your role is to assist customers with their questions, resolve issues, and provide excellent service.

## 🎯 Your Role & Purpose:
${description ? `Based on your description: ${description}` : 'You are a professional customer support assistant focused on helping customers resolve their issues efficiently and satisfactorily.'}

---

${baseGuidelines}

## 🤝 Support-Specific Guidelines:
- **Be patient, empathetic, and solution-focused**
- Listen carefully to customer concerns
- Provide clear, step-by-step assistance
- Escalate complex issues when necessary
- Follow up to ensure satisfaction
- Maintain a helpful and professional tone throughout`,

        follow_up: `You are ${assistantName}, a follow-up assistant focused on relationship building and progress tracking.

## 🎯 Your Role & Purpose:
${description ? `Based on your description: ${description}` : 'You are a professional follow-up assistant focused on maintaining relationships and tracking progress with customers.'}

---

${baseGuidelines}

## 📞 Follow-up Guidelines:
- **Maintain warm, personal connections**
- Check in on previous conversations and commitments
- Provide relevant updates and new information
- Ask about satisfaction and any new needs
- Keep interactions brief but meaningful`,

        survey: `You are ${assistantName}, a survey assistant focused on gathering valuable feedback and information.

## 🎯 Your Role & Purpose:
${description ? `Based on your description: ${description}` : 'You are a professional survey assistant focused on gathering valuable feedback and information from participants.'}

---

${baseGuidelines}

## 📊 Survey Guidelines:
- **Ask questions clearly and one at a time**
- Collect responses accurately and confirm understanding
- Maintain a professional yet friendly tone
- Thank participants for their time and input
- Keep surveys focused and efficient`,

        appointment_booking: `You are ${assistantName}, an appointment booking assistant focused on helping customers schedule and manage their appointments efficiently.

## 🎯 Your Role & Purpose:
${description ? `Based on your description: ${description}` : 'You are a professional appointment booking assistant focused on helping customers schedule and manage their appointments efficiently.'}

---

${baseGuidelines}

## 📅 Appointment Booking Guidelines:
- **Collect necessary information** (name, contact details, preferred date/time)
- **Confirm appointment details** clearly before finalizing
- **Provide confirmation** with all relevant details
- **Handle rescheduling and cancellations** professionally
- **Offer alternative times** when requested slots are unavailable`,

        customer_service: `You are ${assistantName}, a customer service assistant dedicated to providing excellent support and resolving customer inquiries.

## 🎯 Your Role & Purpose:
${description ? `Based on your description: ${description}` : 'You are a professional customer service assistant focused on providing excellent support and resolving customer inquiries efficiently.'}

---

${baseGuidelines}

## 🤝 Customer Service Guidelines:
- **Listen actively** to customer concerns and needs
- **Provide accurate information** about products, services, and policies
- **Resolve issues** promptly and effectively
- **Escalate complex problems** when necessary
- **Follow up** to ensure customer satisfaction
- **Maintain a positive, helpful attitude** throughout interactions`,

        lead_qualification: `You are ${assistantName}, a lead qualification assistant focused on identifying and qualifying potential customers for your business.

## 🎯 Your Role & Purpose:
${description ? `Based on your description: ${description}` : 'You are a professional lead qualification assistant focused on identifying and qualifying potential customers for your business.'}

---

${baseGuidelines}

## 🎯 Lead Qualification Guidelines:
- **Ask qualifying questions** to understand customer needs
- **Assess customer fit** for your products/services
- **Gather relevant information** (budget, timeline, decision-making process)
- **Score leads** based on qualification criteria
- **Route qualified leads** to appropriate sales representatives
- **Maintain professional rapport** while gathering information`,

        product_support: `You are ${assistantName}, a product support assistant focused on helping customers with product-related questions and issues.

## 🎯 Your Role & Purpose:
${description ? `Based on your description: ${description}` : 'You are a professional product support assistant focused on helping customers with product-related questions and issues.'}

---

${baseGuidelines}

## 🛠️ Product Support Guidelines:
- **Provide detailed product information** and specifications
- **Troubleshoot common issues** step-by-step
- **Guide customers through setup and usage** processes
- **Escalate technical problems** when necessary
- **Offer maintenance and care tips** when relevant
- **Ensure customer understanding** of solutions provided`,

        order_tracking: `You are ${assistantName}, an order tracking assistant focused on helping customers track and manage their orders.

## 🎯 Your Role & Purpose:
${description ? `Based on your description: ${description}` : 'You are a professional order tracking assistant focused on helping customers track and manage their orders efficiently.'}

---

${baseGuidelines}

## 📦 Order Tracking Guidelines:
- **Verify order information** and provide current status
- **Explain shipping and delivery** processes clearly
- **Handle order modifications** and cancellations professionally
- **Provide tracking numbers** and delivery updates
- **Address delivery concerns** and delays appropriately
- **Assist with returns and refunds** when needed`,

        feedback_collection: `You are ${assistantName}, a feedback collection assistant focused on gathering valuable customer feedback and insights.

## 🎯 Your Role & Purpose:
${description ? `Based on your description: ${description}` : 'You are a professional feedback collection assistant focused on gathering valuable customer feedback and insights.'}

---

${baseGuidelines}

## 📝 Feedback Collection Guidelines:
- **Ask specific, relevant questions** to gather meaningful feedback
- **Create a comfortable environment** for honest responses
- **Listen actively** and show appreciation for input
- **Probe for details** when responses are vague
- **Thank customers** for their time and feedback
- **Assure confidentiality** when appropriate`,

        technical_support: `You are ${assistantName}, a technical support assistant focused on resolving technical issues and providing technical guidance.

## 🎯 Your Role & Purpose:
${description ? `Based on your description: ${description}` : 'You are a professional technical support assistant focused on resolving technical issues and providing technical guidance.'}

---

${baseGuidelines}

## 🔧 Technical Support Guidelines:
- **Diagnose technical problems** systematically
- **Provide step-by-step solutions** in clear, simple terms
- **Verify problem resolution** before concluding
- **Escalate complex issues** to specialized technicians
- **Document solutions** for future reference
- **Maintain patience** with customers who may be frustrated`,

        consultation: `You are ${assistantName}, a consultation assistant focused on providing expert advice and guidance to clients.

## 🎯 Your Role & Purpose:
${description ? `Based on your description: ${description}` : 'You are a professional consultation assistant focused on providing expert advice and guidance to clients.'}

---

${baseGuidelines}

## 💼 Consultation Guidelines:
- **Listen carefully** to client needs and concerns
- **Ask clarifying questions** to understand requirements fully
- **Provide expert advice** based on best practices
- **Offer multiple options** when appropriate
- **Explain recommendations** clearly and thoroughly
- **Follow up** to ensure client satisfaction with advice provided`
      };

      let prompt = typePrompts[assistantType as keyof typeof typePrompts] || typePrompts.help_desk;
      
      if (siteInfo?.content) {
        prompt += `\n\n---\n\n## 🏢 Company Information:\n${siteInfo.content.substring(0, 3000)}`;
      }
      
      if (knowledgeBaseContent) {
        prompt += `\n\n---\n\n## 📚 Additional Knowledge Base:\n${knowledgeBaseContent.substring(0, 2000)}`;
      }

      // Ensure the prompt is not empty
      if (!prompt.trim()) {
        prompt = `You are ${assistantName}, a helpful AI assistant. ${description || 'You are here to help users with their questions and needs.'}`;
      }

      console.log("[CreateAssistant] Generated system prompt length:", prompt.length);
      console.log("[CreateAssistant] Setting system prompt:", prompt.substring(0, 100) + "...");
      setSystemPrompt(prompt);
    } catch (e: unknown) {
      console.error("[CreateAssistant] Error generating system prompt:", e);
      const error = e as Error;
      toast({ title: "Failed to generate prompt", description: error.message, variant: "destructive" });
      
      // Set a fallback prompt
      const fallbackPrompt = `You are ${assistantName}, a helpful AI assistant. ${description || 'You are here to help users with their questions and needs.'}`;
      setSystemPrompt(fallbackPrompt);
    } finally {
      setLoading(false);
    }
  };

  const createVapiAssistant = async () => {
    setLoading(true);
    try {
      console.log("[CreateAssistant] Starting VAPI assistant creation with data:", {
        assistantName,
        description,
        websiteUrl,
        assistantType,
        voiceId: voiceId || "Paige",
        systemPromptLength: systemPrompt.length,
        user: !!user,
        guestEmail: !!guestEmail,
        useTemplate: true // Always use template for new assistants
      });

      // First create the VAPI assistant
      const requestBody: {
        assistantName: string;
        description: string;
        websiteUrl: string;
        assistantType: string;
        voiceId: string;
        knowledgeBaseFileIds: string[];
        systemPromptOverride: string;
        useTemplate: boolean;
        guestEmail?: string;
        guestPassword?: string;
      } = {
        assistantName,
        description,
        websiteUrl,
        assistantType,
        voiceId: voiceId || "Paige",
        knowledgeBaseFileIds: uploadedFiles.map(f => f.id), // Include uploaded file IDs
        systemPromptOverride: systemPrompt,
        useTemplate: true // Always use template for new assistants
      };

      // Add guest credentials if in guest mode
      if (!user && guestEmail && guestPassword) {
        requestBody.guestEmail = guestEmail;
        requestBody.guestPassword = guestPassword;
      }

      const { data, error } = await supabase.functions.invoke("create-assistant", {
        body: requestBody
      });
      
      console.log("[CreateAssistant] Edge function response:", { data, error });
      
      if (error) {
        console.error("[CreateAssistant] Edge function error:", error);
        throw error;
      }
      
      setAssistantId(data.assistant_id);
      
      // Use the HTML generated by the edge function
      if (data.html) {
        setHtmlCode(data.html);
      } else {
        // Fallback only if no HTML is returned
        const html = generateHtmlCode(data.assistant_id);
        setHtmlCode(html);
      }

      // If in guest mode, save to guest database
      if (!user && guestEmail && guestPassword) {
        console.log("[CreateAssistant] Saving guest assistant data...");
        const guestData = {
          action: 'create',
          assistant_name: assistantName,
          assistant_type: assistantType,
          assistant_id: data.assistant_id,
          voice_id: voiceId || "Paige",
          voice_name: voices.find(v => v.id === voiceId)?.name || "Paige",
          description,
          website_url: websiteUrl,
          demo_url: data.demo_url || `https://your-domain.com/demo/${data.assistant_id}`,
          guest_email: guestEmail,
          guest_password: guestPassword
        };

        console.log("[CreateAssistant] Guest data:", guestData);

        const { data: guestResult, error: guestError } = await supabase.functions.invoke('guest-assistant-management', {
          body: guestData
        });

        console.log("[CreateAssistant] Guest save response:", { guestResult, guestError });

        if (guestError) {
          console.error('Guest save error:', guestError);
          toast({
            title: "Warning",
            description: "Assistant created but failed to save for guest access. Please note your assistant ID.",
            variant: "destructive",
          });
        }
      }
    } catch (error) {
      console.error("[CreateAssistant] Error creating assistant:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to create assistant. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const generateHtmlCode = (id: string) => {
    const slug = assistantName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${assistantName} - AI Voice Assistant Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 10px; }
        .description { text-align: center; color: #666; margin-bottom: 40px; font-size: 18px; }
        .demo-section { text-align: center; padding: 40px 0; }
        .call-button { background: #4F46E5; color: white; border: none; padding: 15px 30px; border-radius: 25px; font-size: 18px; cursor: pointer; transition: background 0.3s; }
        .call-button:hover { background: #3730A3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>${assistantName}</h1>
        <p class="description">${description}</p>
        
        <div class="demo-section">
            <p>Click the button below to start a voice conversation with ${assistantName}</p>
            <button class="call-button" onclick="startCall()">🎤 Talk to ${assistantName}</button>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/@vapi-ai/web@latest/dist/index.js"></script>
    <script>
        const vapi = new window.Vapi("${import.meta.env.VITE_VAPI_PUBLIC_KEY || ''}");
        
        function startCall() {
            vapi.start("${id}");
        }
        
        vapi.on('call-start', () => {
            console.log('Call started');
        });
        
        vapi.on('call-end', () => {
            console.log('Call ended');
        });
    </script>
</body>
</html>`;
  };

  const deployToServer = async () => {
    // Auth check is already done in handleNext for step 6
    setLoading(true);
    try {
      // Deploy the demo to the server
      toast({ title: "Deploying demo...", description: "Creating your demo page..." });
      
      // Since the assistant was already created in step 5, we just need to deploy the HTML
      // Call the deploy-demo-local function directly with the existing data
      const { data, error } = await supabase.functions.invoke('deploy-demo-local', {
        body: {
          assistantName,
          assistantId,
          assistantType,
          html: htmlCode,
          userEmail: user?.email || null,
          guestEmail: guestEmail || null
        }
      });

      if (error) {
        console.error('Deployment error:', error);
        throw new Error(error.message || 'Failed to deploy demo');
      }

      if (!data?.demo_url) {
        throw new Error('No demo URL returned from deployment');
      }

      // Insert DB record for the deployed demo
      const { error: insertError } = await supabase.from("custom_demos").insert({
        user_id: user?.id || null, // null for guest mode
        assistant_name: assistantName,
        assistant_type: assistantType,
        assistant_id: assistantId,
        voice_id: voiceId || "paige",
        voice_name: voiceId || "paige",
        description,
        website_url: websiteUrl,
        demo_url: data.demo_url,
        status: "published", // Always published since we're deploying locally
        tenant_id: user?.user_metadata?.tenant_id || user?.app_metadata?.tenant_id || null,
        // Guest mode fields
        guest_email: guestEmail || null,
        guest_password: guestPassword || null
      });

      if (insertError) {
        console.error('Database insert error:', insertError);
        // Don't throw error for DB insert failure, demo is still deployed
        toast({
          title: "Warning",
          description: "Demo deployed but failed to save to database. Please note your demo URL.",
          variant: "destructive",
        });
      }

      // Clear form data
      localStorage.removeItem("create_assistant_form");
      
      // Open the demo URL in a new tab
      if (data?.demo_url) {
        window.open(data.demo_url, '_blank');
      }
      
      // Navigate to user's list of demos instead of demo preview
      const demosListUrl = user ? `/voice-agents?success=true&newDemo=${assistantId}` : `/guest-dashboard?success=true&newDemo=${assistantId}`;
      navigate(demosListUrl);
      
      toast({ 
        title: "Demo deployed!", 
        description: `Your demo "${assistantName}" is now live and ready to use. The demo has been opened in a new tab for you to test!` 
      });
    } catch (e: unknown) {
      console.error(e);
      const error = e as Error;
      toast({ title: "Failed to deploy demo", description: error.message || "Please try again.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleNext = async () => {
    if (currentStep === 1) {
      if (!assistantName || !websiteUrl) {
        toast({ title: "Missing info", description: "Assistant name and website URL are required.", variant: "destructive" });
        return;
      }
      await extractSiteInfo();
      setCurrentStep(2);
    } else if (currentStep === 2) {
      // Template selection step - can proceed regardless of template choice
      setCurrentStep(3);
    } else if (currentStep === 3) {
      await generateSystemPrompt();
      setCurrentStep(4);
    } else if (currentStep === 4) {
      // Check auth before creating assistant
      if (!user && !guestEmail) {
        console.log("[CreateAssistant] No auth, showing guest mode");
        // Show guest mode option instead of redirecting to auth
        setIsGuestMode(true);
        return;
      }
      console.log("[CreateAssistant] Creating VAPI assistant...");
      await createVapiAssistant();
      console.log("[CreateAssistant] Moving to step 5");
      setCurrentStep(5);
    } else if (currentStep === 5) {
      setCurrentStep(6);
    } else if (currentStep === 6) {
      await deployToServer();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const canProceedToNext = (): boolean => {
    switch (currentStep) {
      case 1: return !!(assistantName && websiteUrl);
      case 2: return true; // Template step - can always proceed
      case 3: return siteInfo !== null;
      case 4: {
        const hasSystemPrompt = systemPrompt !== "";
        console.log("[CreateAssistant] Step 4 validation:", {
          hasSystemPrompt,
          systemPromptLength: systemPrompt.length,
          user: !!user,
          guestEmail: !!guestEmail,
          guestPasswordLength: guestPassword.length
        });
        // Only require system prompt for step 4 - authentication will be checked in step 5 when creating assistant
        return hasSystemPrompt;
      }
      case 5: return htmlCode !== "";
      case 6: return true;
      default: return false;
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-4">
              <MessageSquare className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Assistant Configuration</h3>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="name">Assistant Name</Label>
              <Input 
                id="name" 
                value={assistantName} 
                onChange={(e) => setAssistantName(e.target.value)} 
                placeholder="Abena from Ananse Ltd."
                required 
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="desc">Short Description (Optional)</Label>
              <Textarea id="desc" value={description} onChange={(e) => setDescription(e.target.value)} rows={4} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="url">Website URL</Label>
              <Input 
                id="url" 
                type="url" 
                placeholder="https://example.com" 
                value={websiteUrl} 
                onChange={(e) => setWebsiteUrl(e.target.value)} 
                required 
              />
            </div>

            <div className="space-y-2">
              <Label>Assistant Type (Optional)</Label>
              <Select value={assistantType} onValueChange={setAssistantType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {ASSISTANT_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Voice (Optional)</Label>
              <Select value={voiceId} onValueChange={setVoiceId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select voice" />
                </SelectTrigger>
                <SelectContent>
                  {voices.map((voice) => (
                    <SelectItem key={voice.id} value={voice.id}>{voice.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-4">
              <Label>Knowledge Base (Optional)</Label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.txt,.doc,.docx,.csv,.json"
                  onChange={(e) => handleFileUpload(e.target.files)}
                  className="hidden"
                  id="knowledge-upload"
                  disabled={uploadingFiles}
                />
                <label htmlFor="knowledge-upload" className={`cursor-pointer ${uploadingFiles ? 'opacity-50' : ''}`}>
                  <Upload className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-600">
                    {uploadingFiles ? 'Uploading...' : 'Click to upload documents (PDF, TXT, DOC, DOCX, CSV, JSON)'}
                  </p>
                  <p className="mt-1 text-xs text-gray-500">
                    Max file size: 10MB per file
                  </p>
                </label>
              </div>
              
              {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                  <Label>Uploaded Files:</Label>
                  <div className="space-y-2">
                    {uploadedFiles.map((file) => (
                      <div key={file.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                        <div className="flex items-center space-x-2">
                          <FileText className="h-4 w-4 text-gray-500" />
                          <span className="text-sm">{file.name}</span>
                          <Badge variant="secondary" className="text-xs">
                            {(file.size / 1024).toFixed(1)} KB
                          </Badge>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(file.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {!user && (
              <div className="rounded-md border p-4 text-sm">Please sign in to continue. We'll bring you back here.</div>
            )}
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Choose Template (Optional)</h3>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <Button
                    variant={useTemplate ? "default" : "outline"}
                    onClick={() => setUseTemplate(true)}
                    className="flex items-center gap-2"
                    disabled
                  >
                    <Sparkles className="h-4 w-4" />
                    Use Template
                  </Button>
                  <span className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 text-xs text-muted-foreground">
                    coming soon
                  </span>
                </div>
                <Button
                  variant={!useTemplate ? "default" : "outline"}
                  onClick={() => {
                    setUseTemplate(false);
                    setSelectedTemplate(null);
                  }}
                  className="flex items-center gap-2"
                >
                  <MessageSquare className="h-4 w-4" />
                  Custom Assistant
                </Button>
                <div className="relative">
                  <Button
                    variant="outline"
                    onClick={() => setShowTemplateCustomization(true)}
                    className="flex items-center gap-2"
                    disabled
                  >
                    <Edit className="h-4 w-4" />
                    Customize Templates
                  </Button>
                  <span className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 text-xs text-muted-foreground">
                    coming soon
                  </span>
                </div>
              </div>
              
              {useTemplate && (
                <VoiceAgentTemplates
                  onTemplateSelect={(template: VoiceTemplate) => setSelectedTemplate(template)}
                  selectedTemplate={selectedTemplate && 'icon' in selectedTemplate ? selectedTemplate as VoiceTemplate : null}
                />
              )}
              
              {!useTemplate && (
                <div className="text-center py-8 text-muted-foreground">
                  <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>You'll create a custom assistant from scratch in the next steps.</p>
                </div>
              )}

              {/* Template Customization Dialog */}
              <Dialog open={showTemplateCustomization} onOpenChange={setShowTemplateCustomization}>
                <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
                  <TemplateCustomization
                    selectedTemplate={selectedTemplate}
                    onTemplateSelect={(template) => {
                      setSelectedTemplate(template);
                      setUseTemplate(true);
                      setShowTemplateCustomization(false);
                    }}
                    onClose={() => setShowTemplateCustomization(false)}
                  />
                </DialogContent>
              </Dialog>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-4">
              <Globe className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Website Information</h3>
            </div>
            
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
                <p>Extracting website information...</p>
                <p className="text-sm text-muted-foreground mt-2">This may take a few moments</p>
              </div>
            ) : siteInfo ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="site-title">Website Title</Label>
                  {siteInfo.content?.includes('⚠️') && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={extractSiteInfo}
                      className="text-xs"
                    >
                      🔄 Retry Extraction
                    </Button>
                  )}
                </div>
                <Input
                  id="site-title"
                  value={siteInfo.title}
                  onChange={(e) => setSiteInfo({ ...siteInfo, title: e.target.value })}
                />
                
                <div className="space-y-2">
                  <Label htmlFor="site-description">Website Description</Label>
                  <Textarea
                    id="site-description"
                    value={siteInfo.description}
                    onChange={(e) => setSiteInfo({ ...siteInfo, description: e.target.value })}
                    rows={3}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="site-content">Website Content</Label>
                  <Textarea
                    id="site-content"
                    value={siteInfo.content}
                    onChange={(e) => setSiteInfo({ ...siteInfo, content: e.target.value })}
                    rows={10}
                    className="text-sm"
                  />
                </div>
                
                {siteInfo.content?.includes('⚠️') ? (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                    <p className="text-sm text-yellow-800">
                      <strong>Note:</strong> Site extraction encountered an issue. You can manually edit the information above, 
                      or click "Retry Extraction" to try again. The assistant will still work with manually entered information.
                    </p>
                  </div>
                ) : (
                  <div className="bg-green-50 border border-green-200 rounded-md p-4">
                    <p className="text-sm text-green-800">
                      ✅ Website information extracted successfully! Review and edit the content above as needed.
                    </p>
                  </div>
                )}
                
                <p className="text-sm text-muted-foreground">
                  Review and edit the extracted website information above. This will be used to generate the assistant's knowledge base.
                </p>
              </div>
            ) : null}
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-4">
              <MessageSquare className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">System Prompt</h3>
            </div>
            
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
                <p>Generating system prompt...</p>
              </div>
            ) : (
              <div className="space-y-4">
                {!systemPrompt && (
                  <div className="text-center py-4">
                    <Button 
                      onClick={generateSystemPrompt}
                      disabled={loading}
                      className="mb-4"
                    >
                      {loading ? "Generating..." : "Generate System Prompt"}
                    </Button>
                    <p className="text-sm text-muted-foreground">
                      Click the button above to generate your system prompt
                    </p>
                  </div>
                )}
                
                <div className="space-y-2">
                  <Label htmlFor="system-prompt">System Prompt</Label>
                  <Textarea
                    id="system-prompt"
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    rows={15}
                    className="text-sm font-mono"
                  />
                </div>
                
                {systemPrompt && (
                  <div className="flex gap-2">
                    <Button 
                      onClick={generateSystemPrompt}
                      disabled={loading}
                      variant="outline"
                      size="sm"
                    >
                      {loading ? "Regenerating..." : "Regenerate Prompt"}
                    </Button>
                    <p className="text-sm text-muted-foreground self-center">
                      Review and edit the generated system prompt above. This defines how your assistant will behave and respond.
                    </p>
                  </div>
                )}
                
                {debugMode && (
                  <div className="mt-4 p-3 bg-gray-100 rounded-md text-xs">
                    <strong>Debug Info:</strong><br/>
                    System Prompt Length: {systemPrompt.length}<br/>
                    Has System Prompt: {systemPrompt !== "" ? "Yes" : "No"}<br/>
                    Current Step: {currentStep}<br/>
                    Can Proceed: {canProceedToNext() ? "Yes" : "No"}
                  </div>
                )}
              </div>
            )}
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-4">
              <Code className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Demo Page Code</h3>
            </div>
            
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
                <p>Creating Vapi assistant and generating demo code...</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="html-code">HTML Demo Page Code</Label>
                  <Textarea
                    id="html-code"
                    value={htmlCode}
                    onChange={(e) => setHtmlCode(e.target.value)}
                    rows={20}
                    className="text-sm font-mono"
                  />
                </div>
                
                <p className="text-sm text-muted-foreground">
                  Review and edit the HTML code above. This will be deployed as your demo page.
                </p>
                
                {assistantId && (
                  <div className="p-4 bg-green-50 border border-green-200 rounded-md">
                    <p className="text-sm text-green-800">
                      ✅ Assistant created successfully! ID: <code className="bg-green-100 px-1 rounded">{assistantId}</code>
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        );

      case 6:
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-4">
              <ChevronRight className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Deploy</h3>
            </div>
            
            <div className="text-center py-8">
              <h4 className="text-lg font-semibold mb-4">Ready to Deploy!</h4>
              <p className="text-muted-foreground mb-6">
                Your assistant is configured and ready to be deployed. Click "Deploy" to publish your demo page.
              </p>
              
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4 text-left">
                <h5 className="font-semibold text-blue-800 mb-2">Summary:</h5>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Assistant Name: {assistantName}</li>
                  <li>• Type: {ASSISTANT_TYPES.find(t => t.value === assistantType)?.label}</li>
                  <li>• Voice: {voices.find(v => v.id === voiceId)?.name}</li>
                  <li>• Knowledge Base: {knowledgeBase.length} files</li>
                  <li>• Website: {websiteUrl || "None"}</li>
                  {useTemplate && selectedTemplate && (
                    <li>• Template: {selectedTemplate.name}</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  // Guest mode overlay
  if (isGuestMode) {
    return (
      <main className="container py-10">
        <section className="max-w-4xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>Guest Mode</CardTitle>
              <CardDescription>Create an assistant without signing up</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <h3 className="font-semibold text-blue-800 mb-2">How Guest Mode Works</h3>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Create assistants without creating an account</li>
                    <li>• Access your assistants using email and password</li>
                    <li>• All assistants are saved securely</li>
                    <li>• You can upgrade to a full account anytime</li>
                  </ul>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="guest-email">Email Address</Label>
                    <Input
                      id="guest-email"
                      type="email"
                      placeholder="Enter your email"
                      value={guestEmail}
                      onChange={(e) => setGuestEmail(e.target.value)}
                      required
                    />
                    <p className="text-sm text-muted-foreground">
                      This will be used to access your assistants later
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="guest-password">Password</Label>
                    <Input
                      id="guest-password"
                      type="password"
                      placeholder="Create a password (min 6 characters)"
                      value={guestPassword}
                      onChange={(e) => setGuestPassword(e.target.value)}
                      required
                    />
                    <p className="text-sm text-muted-foreground">
                      Remember this password - you'll need it to access your assistants
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button 
                    onClick={handleGuestModeSubmit}
                    disabled={!guestEmail || guestPassword.length < 6}
                    className="flex-1"
                  >
                    Continue with Guest Mode
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={() => {
                      setIsGuestMode(false);
                      navigate("/auth");
                    }}
                  >
                    Sign Up Instead
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </main>
    );
  }

  return (
    <main className="container py-10">
      <section className="max-w-4xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Create Voice AI Assistant</CardTitle>
            <CardDescription>Step-by-step wizard to create and deploy your voice assistant</CardDescription>
          </CardHeader>
          <CardContent>
            <StepWizard
              currentStep={currentStep}
              totalSteps={totalSteps}
              onNext={handleNext}
              onPrevious={handlePrevious}
              canNext={canProceedToNext()}
              isLoading={loading}
              onSaveProgress={saveProgress}
              onLoadProgress={loadProgress}
              onClearProgress={clearProgress}
              hasSavedProgress={hasProgress}
            />
            
            {renderStep()}
          </CardContent>
        </Card>
      </section>
    </main>
  );
};

export default CreateAssistant;