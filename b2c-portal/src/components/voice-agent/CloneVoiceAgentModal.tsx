import React, { useState, useEffect } from 'react';
import { X, Copy } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Assistant } from './AssistantList';

interface CloneVoiceAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAgentCloned: () => void;
  sourceAgent: Assistant | null;
  apiBaseUrl: string;
}

export const CloneVoiceAgentModal: React.FC<CloneVoiceAgentModalProps> = ({
  isOpen,
  onClose,
  onAgentCloned,
  sourceAgent,
  apiBaseUrl
}) => {
  const { toast } = useToast();
  const [isCloning, setIsCloning] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    system_prompt: '',
    first_message: '',
    url: ''
  });

  // Update form data when sourceAgent changes
  useEffect(() => {
    if (sourceAgent && isOpen) {
      setFormData({
        name: `${sourceAgent.name} (Copy)`,
        description: sourceAgent.description,
        system_prompt: sourceAgent.system_prompt || '',
        first_message: sourceAgent.first_message || '',
        url: ''
      });
    }
  }, [sourceAgent, isOpen]);

  const handleClone = async () => {
    if (!sourceAgent) {
      toast({
        title: "No source agent",
        description: "Please select a voice agent to clone",
        variant: "destructive"
      });
      return;
    }

    if (!formData.name.trim()) {
      toast({
        title: "Name required",
        description: "Please enter a name for the cloned agent",
        variant: "destructive"
      });
      return;
    }

    setIsCloning(true);

    try {
      // Create cloned assistant data based on source agent
      const clonedAssistantData = {
        ...sourceAgent,
        id: crypto.randomUUID(),
        name: formData.name.trim(),
        description: formData.description.trim() || sourceAgent.description,
        system_prompt: formData.system_prompt.trim() || sourceAgent.system_prompt,
        first_message: formData.first_message.trim() || sourceAgent.first_message,
        status: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        user_id: 'user-123',
        template_id: `cloned_from_${sourceAgent.id}`
      };

      // Add URL to metadata if provided
      if (formData.url.trim()) {
        clonedAssistantData.metadata = {
          ...clonedAssistantData.metadata,
          clone_source_id: sourceAgent.id,
          clone_source_name: sourceAgent.name,
          custom_url: formData.url.trim()
        };
      } else {
        clonedAssistantData.metadata = {
          ...clonedAssistantData.metadata,
          clone_source_id: sourceAgent.id,
          clone_source_name: sourceAgent.name
        };
      }

      const response = await fetch(`${apiBaseUrl}/voice/assistants/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(clonedAssistantData)
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(error || `HTTP error! status: ${response.status}`);
      }

      const clonedAgent = await response.json();

      toast({
        title: "Voice agent cloned",
        description: `${clonedAgent.name} has been created successfully from ${sourceAgent.name}.`,
      });

      onAgentCloned();
      handleClose();
    } catch (error) {
      console.error('Error cloning voice agent:', error);
      toast({
        title: "Failed to clone voice agent",
        description: error instanceof Error ? error.message : "Please try again later.",
        variant: "destructive"
      });
    } finally {
      setIsCloning(false);
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      description: '',
      system_prompt: '',
      first_message: '',
      url: ''
    });
    onClose();
  };

  if (!isOpen || !sourceAgent) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-2 sm:p-4 z-50">
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full max-w-2xl mx-2 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Copy className="h-5 w-5 text-indigo-600" />
            <h3 className="text-base sm:text-lg font-semibold">Clone Voice Agent</h3>
          </div>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-accent rounded-md transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Source Agent Info */}
        <div className="mb-4 p-3 bg-muted rounded-lg">
          <div className="text-sm font-medium text-gray-600 mb-1">
            Cloning from:
          </div>
          <div className="font-semibold">{sourceAgent.name}</div>
          <div className="text-sm text-gray-600">{sourceAgent.description}</div>
          <div className="flex items-center gap-2 mt-2">
            <span className={`px-2 py-1 text-xs rounded-full ${
              sourceAgent.status === 'published'
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
            }`}>
              {sourceAgent.status}
            </span>
            <span className="text-xs text-gray-600 capitalize">
              {sourceAgent.language}
            </span>
          </div>
        </div>

        <div className="space-y-4">
          {/* New Name Input */}
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1.5">
              New Agent Name <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g., Customer Support Bot (Copy)"
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
              rows={2}
              placeholder="Update the description for the cloned agent..."
            />
          </div>

          {/* System Prompt Input */}
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1.5">
              System Prompt
            </label>
            <textarea
              value={formData.system_prompt}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
              className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              rows={4}
              placeholder="Customize the system prompt for the cloned agent..."
            />
          </div>

          {/* First Message Input */}
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1.5">
              First Message
            </label>
            <input
              type="text"
              value={formData.first_message}
              onChange={(e) => setFormData({ ...formData, first_message: e.target.value })}
              className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Customize the greeting message..."
            />
          </div>

          {/* Custom URL Input */}
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1.5">
              Custom URL (Optional)
            </label>
            <input
              type="url"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="https://example.com/webhook"
            />
            <div className="text-xs text-gray-600 mt-1">
              Specify a custom webhook URL for this cloned agent
            </div>
          </div>

          {/* Configuration Notice */}
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-1">
              Configuration Copied
            </div>
            <div className="text-xs text-blue-700 dark:text-blue-400">
              All technical settings (LLM model, TTS/STT providers, language settings) will be copied from the original agent. You can modify these after cloning.
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row justify-end gap-2 mt-6">
          <button
            onClick={handleClose}
            disabled={isCloning}
            className="px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md hover:bg-accent w-full sm:w-auto order-2 sm:order-1 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleClone}
            disabled={isCloning}
            className="px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm bg-indigo-600 text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-auto order-1 sm:order-2 transition-colors flex items-center justify-center gap-2"
          >
            {isCloning ? (
              'Cloning...'
            ) : (
              <>
                <Copy className="h-3 w-3" />
                Clone Voice Agent
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};