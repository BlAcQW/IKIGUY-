import React, { useState } from 'react';
import { X } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';

interface CreateAssistantModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAssistantCreated: () => void;
  apiBaseUrl: string;
}

export const CreateAssistantModal: React.FC<CreateAssistantModalProps> = ({
  isOpen,
  onClose,
  onAssistantCreated,
  apiBaseUrl
}) => {
  const { toast } = useToast();
  const { user, getTenantId } = useMongoAuth();
  const [isCreating, setIsCreating] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    language: 'en',
    template: 'custom'
  });

  const templates = [
    { id: 'custom', name: 'Custom Assistant', description: 'Start from scratch' },
    { id: 'customer_support', name: 'Customer Support', description: 'Pre-configured for customer service' },
    { id: 'sales', name: 'Sales Assistant', description: 'Optimized for sales conversations' },
    { id: 'twi', name: 'Twi Language Assistant', description: 'Configured for Twi/Akan speakers' },
    { id: 'technical', name: 'Technical Support', description: 'For technical troubleshooting' }
  ];

  const handleCreate = async () => {
    if (!formData.name.trim()) {
      toast({
        title: "Name required",
        description: "Please enter a name for your assistant",
        variant: "destructive"
      });
      return;
    }

    setIsCreating(true);
    
    try {
      // Prepare assistant data based on template
      let assistantData: any = {
        name: formData.name,
        description: formData.description || `A helpful ${formData.language} assistant`,
        user_id: 'user-123',
        template_id: formData.template,
        status: 'draft',
        language: formData.language,
        country: formData.language === 'twi' ? 'Ghana' : 'US',
        // Required fields for new API
        voice_provider_id: '',  // Will be set per template
        voice_id: '',  // Will be set per template
        llm_provider_id: '',  // Will be set per template
        llm_model_id: '',  // Will be set per template
      };

      // Set defaults based on template
      switch (formData.template) {
        case 'customer_support':
          assistantData = {
            ...assistantData,
            llm_provider: 'openai',
            llm_model: 'gpt-4o-mini',
            llm_provider_id: 'openai',
            llm_model_id: 'gpt-4o-mini',
            system_prompt: 'You are a helpful customer support agent. Be friendly, professional, and solution-oriented.',
            first_message: 'Hello! How can I assist you today?',
            tts_provider: 'openai',
            tts_voice: 'alloy',
            voice_provider_id: 'openai',
            voice_id: 'alloy',
            stt_provider: 'openai',
            stt_model: 'whisper-1'
          };
          break;
        case 'sales':
          assistantData = {
            ...assistantData,
            llm_provider: 'anthropic',
            llm_model: 'claude-3-5-sonnet-20241022',
            llm_provider_id: 'anthropic',
            llm_model_id: 'claude-3-5-sonnet-20241022',
            system_prompt: 'You are a professional sales assistant. Help qualify leads and guide customers.',
            first_message: 'Hi there! What brings you here today?',
            tts_provider: 'elevenlabs',
            tts_voice: 'rachel',
            voice_provider_id: 'elevenlabs',
            voice_id: 'rachel',
            stt_provider: 'openai',
            stt_model: 'whisper-1'
          };
          break;
        case 'twi':
          assistantData = {
            ...assistantData,
            language: 'twi',
            country: 'Ghana',
            llm_provider: 'gemini',
            llm_model: 'gemini-2.5-flash',
            llm_provider_id: 'gemini',
            llm_model_id: 'gemini-2.5-flash',
            system_prompt: 'You are a helpful assistant that speaks Twi (Akan). Always respond in Twi.',
            first_message: 'Akwaaba! Ɛdeɛn na me betumi ayɛ ama wo?',
            tts_provider: 'meta_mms',
            tts_voice: 'akan-mms',
            voice_provider_id: 'meta_mms',
            voice_id: 'akan-mms',
            stt_provider: 'meta_mms',
            stt_model: 'akan-whisper'
          };
          break;
        case 'technical':
          assistantData = {
            ...assistantData,
            llm_provider: 'gemini',
            llm_model: 'gemini-1.5-pro',
            llm_provider_id: 'gemini',
            llm_model_id: 'gemini-1.5-pro',
            system_prompt: 'You are a technical support specialist. Help users troubleshoot issues.',
            first_message: 'Hello! What technical issue can I help you with?',
            tts_provider: 'openai',
            tts_voice: 'echo',
            voice_provider_id: 'openai',
            voice_id: 'echo',
            stt_provider: 'openai',
            stt_model: 'whisper-1'
          };
          break;
        default:
          assistantData = {
            ...assistantData,
            llm_provider: 'gemini',
            llm_model: 'gemini-2.5-flash',
            llm_provider_id: 'gemini',
            llm_model_id: 'gemini-2.5-flash',
            system_prompt: `You are a helpful ${formData.language} assistant.`,
            first_message: 'Hello! How can I help you?',
            tts_provider: 'meta_mms',
            tts_voice: 'akan-mms',
            voice_provider_id: 'meta_mms',
            voice_id: 'akan-mms',
            stt_provider: 'meta_mms',
            stt_model: 'akan-whisper'
          };
      }

      // Add common fields
      assistantData.first_message_mode = 'assistant_first';
      assistantData.id = crypto.randomUUID();
      assistantData.tenant_id = user?.user_metadata?.tenant_id || user?.id || '';

      const response = await fetch(`${apiBaseUrl}/voice/assistants/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(assistantData)
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(error || `HTTP error! status: ${response.status}`);
      }

      const newAssistant = await response.json();
      
      toast({
        title: "Assistant created",
        description: `${newAssistant.name} has been created successfully.`,
      });

      onAssistantCreated();
      handleClose();
    } catch (error) {
      console.error('Error creating assistant:', error);
      toast({
        title: "Failed to create assistant",
        description: error instanceof Error ? error.message : "Please try again later.",
        variant: "destructive"
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      description: '',
      language: 'en',
      template: 'custom'
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-2 sm:p-4 z-50">
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full max-w-2xl mx-2 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base sm:text-lg font-semibold">Create New Assistant</h3>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-accent rounded-md transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Name Input */}
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1.5">
              Assistant Name <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g., Customer Support Bot"
            />
          </div>

          {/* Description Input */}
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1.5">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              rows={3}
              placeholder="Describe what this assistant does..."
            />
          </div>

          {/* Template Selection */}
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1.5">
              Template
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    formData.template === template.id
                      ? 'border-primary bg-primary/10'
                      : 'border-border hover:border-muted-foreground'
                  }`}
                  onClick={() => setFormData({ ...formData, template: template.id })}
                >
                  <div className="font-medium text-xs sm:text-sm">{template.name}</div>
                  <div className="text-xs text-gray-600 mt-0.5">
                    {template.description}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Language Selection */}
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1.5">
              Primary Language
            </label>
            <select
              value={formData.language}
              onChange={(e) => setFormData({ ...formData, language: e.target.value })}
              className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="en">English</option>
              <option value="twi">Twi</option>
              <option value="yoruba">Yoruba</option>
              <option value="swahili">Swahili</option>
              <option value="ewe">Ewe</option>
              <option value="ga">Ga</option>
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row justify-end gap-2 mt-6">
          <button
            onClick={handleClose}
            disabled={isCreating}
            className="px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md hover:bg-accent w-full sm:w-auto order-2 sm:order-1 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={isCreating}
            className="px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm bg-indigo-600 text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-auto order-1 sm:order-2 transition-colors"
          >
            {isCreating ? 'Creating...' : 'Create Assistant'}
          </button>
        </div>
      </div>
    </div>
  );
};