/**
 * Conversation Settings Modal
 * 
 * Modal component that shows voice settings override for an automation.
 * Allows users to configure TTS, ASR, LLM, and Reference Voice settings
 * that will override VAPI assistant settings when running campaigns.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { VoiceSettingsOverride } from './VoiceSettingsOverride';
import { useComprehensiveTTS } from '@kasaai/shared-frontend/hooks/useComprehensiveTTS';
import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL } from '@/config/api-config';
import type { AutomationConfig } from '@/services/AutomationOrchestrationService';

interface ConversationSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  automation: AutomationConfig | null;
  onSave?: () => void;
}

export const ConversationSettingsModal: React.FC<ConversationSettingsModalProps> = ({
  isOpen,
  onClose,
  automation,
  onSave,
}) => {
  const { toast } = useToast();
  const apiBaseUrl = API_BASE_URL || import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'https://api.ailabsafrica.com';
  
  // Use comprehensive TTS hook - same as inkwave
  const {
    providers: comprehensiveTTSProviders,
    loading: loadingComprehensiveTTS,
    error: comprehensiveTTSError
  } = useComprehensiveTTS(apiBaseUrl, undefined, {
    onlineOnly: false,
    autoFetch: true,
    endpointPath: '/api/tts/providers',
    skipWalletBalance: true,
    getAuthHeaders
  });
  
  // ASR and LLM providers state - same pattern as inkwave
  const [asrProviders, setAsrProviders] = useState<Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
    status: 'online' | 'offline' | 'building';
    languages?: string[];
    capabilities?: Record<string, any>;
  }>>([]);
  const [llmModels, setLlmModels] = useState<Array<{
    id: string;
    name: string;
    description: string;
    provider: string;
    contextWindow?: number;
    capabilities?: Record<string, any>;
  }>>([]);
  const [clonedVoices, setClonedVoices] = useState<Array<{
    id: string;
    name: string;
    description?: string;
  }>>([]);
  const [loadingASRProviders, setLoadingASRProviders] = useState(false);
  const [loadingLLMProviders, setLoadingLLMProviders] = useState(false);
  
  const [isSaving, setIsSaving] = useState(false);
  const [useCustomSettings, setUseCustomSettings] = useState(false);
  const [customVoiceSettings, setCustomVoiceSettings] = useState({
    tts: { provider: null as string | null, voice: null as string | null, speed: 1.0, pitch: 0.0 },
    asr: { provider: null as string | null, language: 'en' },
    llm: { model: null as string | null, temperature: 0.7, maxTokens: 2000 },
    referenceVoice: null as string | null,
  });
  
  // Load ASR and LLM providers - using core_backend endpoints
  useEffect(() => {
    const loadProviders = async () => {
      if (!isOpen) return;
      
      try {
        setLoadingASRProviders(true);
        setLoadingLLMProviders(true);
        const authHeaders = await getAuthHeaders();
        
        // Fetch ASR providers from /api/asr/providers
        try {
          const asrResponse = await fetch(`${apiBaseUrl}/api/asr/providers`, {
            headers: authHeaders,
          });
          
          if (asrResponse.ok) {
            const asrData = await asrResponse.json();
            // Handle both array and object formats
            const providersArray = Array.isArray(asrData.providers) 
              ? asrData.providers 
              : Object.values(asrData.providers || {});
            
            const formattedAsrProviders = providersArray.map((p: any) => ({
              id: p.id || p.provider_id,
              name: p.name || p.id?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
              description: p.description || `${p.id} ASR provider`,
              icon: p.icon || '🎤',
              status: (p.status === 'online' ? 'online' : p.status === 'offline' ? 'offline' : 'building') as 'online' | 'offline' | 'building',
              languages: p.languageList || (p.languages ? (typeof p.languages === 'number' ? [] : Array.isArray(p.languages) ? p.languages : [p.languages]) : ['en']),
              capabilities: p.capabilities || {},
            }));
            setAsrProviders(formattedAsrProviders);
          }
        } catch (asrError) {
          console.error('Failed to load ASR providers:', asrError);
        }
        
        // Fetch LLM providers from /api/llm/providers
        try {
          const llmResponse = await fetch(`${apiBaseUrl}/api/llm/providers`, {
            headers: authHeaders,
          });
          
          if (llmResponse.ok) {
            const llmData = await llmResponse.json();
            // Handle both array and object formats
            const providersArray = Array.isArray(llmData.providers) 
              ? llmData.providers 
              : Object.values(llmData.providers || {});
            
            // Convert to format expected by LLMModelSelector - flatten providers into models
            const models: Array<{
              id: string;
              name: string;
              description: string;
              provider: string;
              contextWindow?: number;
              capabilities?: Record<string, any>;
            }> = [];
            
            providersArray.forEach((provider: any) => {
              if (provider.models && Array.isArray(provider.models)) {
                provider.models.forEach((model: any) => {
                  models.push({
                    id: model.id || model.model_id,
                    name: model.name || model.id,
                    description: model.description || `${model.id} model`,
                    provider: provider.id || provider.provider_id,
                    contextWindow: model.context_window || model.max_tokens || 8000,
                    capabilities: model.capabilities || {},
                  });
                });
              } else {
                // Provider itself might be a model
                models.push({
                  id: provider.id || provider.provider_id,
                  name: provider.name || provider.id,
                  description: provider.description || `${provider.id} model`,
                  provider: provider.id || provider.provider_id || 'unknown',
                  contextWindow: provider.context_window || provider.max_tokens || 8000,
                  capabilities: provider.capabilities || {},
                });
              }
            });
            setLlmModels(models);
          }
        } catch (llmError) {
          console.error('Failed to load LLM providers:', llmError);
        }
      } catch (error) {
        console.error('Failed to load providers:', error);
        toast({
          title: "Failed to load providers",
          description: "Could not load ASR and LLM providers. Please refresh.",
          variant: "destructive",
        });
      } finally {
        setLoadingASRProviders(false);
        setLoadingLLMProviders(false);
      }
    };

    if (isOpen) {
      loadProviders();
    }
  }, [isOpen, apiBaseUrl, toast]);
  
  // Convert TTS providers to format expected by VoiceSettingsOverride
  const ttsProviders = comprehensiveTTSProviders.map(p => ({
    id: p.id,
    name: p.name,
    description: p.description || `${p.id} TTS provider`,
    status: p.status,
    deployment: p.deployment || 'cloud',
    endpoint: p.endpoint || '',
    icon: p.icon || '🔊',
    capabilities: p.capabilities || {
      voice_cloning: false,
      multi_language: false,
      speed_control: true,
      pitch_control: true,
      multi_speaker: false,
      streaming: false,
    },
  }));
  
  const providersLoading = loadingComprehensiveTTS || loadingASRProviders || loadingLLMProviders;

  // Load existing settings when automation changes
  useEffect(() => {
    if (automation && isOpen) {
      // Check multiple possible locations for vapi_agent data
      // Priority: top-level vapi_agent > config.vapi_agent > config.user_config.vapi_agent
      const vapiAgent = automation.vapi_agent
        || automation.vapiAgent
        || automation.config?.vapi_agent
        || automation.config?.vapiAgent
        || automation.config?.user_config?.vapi_agent
        || {};
      const override = vapiAgent.custom_settings_override || vapiAgent.customSettingsOverride;

      if (override) {
        setUseCustomSettings(true);
        setCustomVoiceSettings({
          tts: {
            provider: override.tts?.provider || null,
            voice: override.tts?.voice || null,
            speed: override.tts?.speed ?? 1.0,
            pitch: override.tts?.pitch ?? 0.0,
          },
          asr: {
            provider: override.asr?.provider || null,
            language: override.asr?.language || 'en',
          },
          llm: {
            model: override.llm?.model || null,
            temperature: override.llm?.temperature ?? 0.7,
            maxTokens: override.llm?.maxTokens ?? 2000,
          },
          referenceVoice: override.referenceVoice || null,
        });
      } else {
        setUseCustomSettings(false);
        // Reset to defaults when no override exists
        setCustomVoiceSettings({
          tts: { provider: null, voice: null, speed: 1.0, pitch: 0.0 },
          asr: { provider: null, language: 'en' },
          llm: { model: null, temperature: 0.7, maxTokens: 2000 },
          referenceVoice: null,
        });
      }
    }
  }, [automation, isOpen]);

  const handleSave = async () => {
    if (!automation) return;

    setIsSaving(true);
    try {
      const headers = await getAuthHeaders();
      
      // Build custom settings override object
      const customSettingsOverride = useCustomSettings ? {
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
      } : null;

      // Update automation config
      const response = await fetch(`${apiBaseUrl}/automation-configs/${automation.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
        body: JSON.stringify({
          vapi_agent: {
            custom_settings_override: customSettingsOverride,
          },
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to save settings' }));
        throw new Error(error.detail || 'Failed to save conversation settings');
      }

      toast({
        title: "Settings saved",
        description: "Conversation settings have been updated successfully.",
      });

      // Apply custom settings to VAPI assistant if configured
      if (useCustomSettings && customSettingsOverride) {
        try {
          const applyResponse = await fetch(
            `${apiBaseUrl}/api/vapi/assistant-update/${automation.id}/apply-custom-settings`,
            {
              method: 'POST',
              headers,
            }
          );
          
          if (applyResponse.ok) {
            toast({
              title: "VAPI assistant updated",
              description: "Custom settings have been applied to the VAPI assistant.",
            });
          }
        } catch (err) {
          console.warn('Failed to apply settings to VAPI assistant:', err);
          // Don't fail the save operation if this fails
        }
      }

      onSave?.();
      onClose();
    } catch (error) {
      console.error('Error saving conversation settings:', error);
      toast({
        title: "Failed to save settings",
        description: error instanceof Error ? error.message : 'An error occurred while saving.',
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (!automation) return null;

  const vapiAgent = automation.config?.vapi_agent || automation.config?.vapiAgent || {};

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Conversation Settings</DialogTitle>
          <DialogDescription>
            Configure voice, ASR, and LLM settings for {automation.automation_name}. 
            These settings will override VAPI assistant settings when running campaigns.
          </DialogDescription>
        </DialogHeader>
        
        <div className="flex-1 overflow-y-auto">
          <VoiceSettingsOverride
            vapiVoiceSettings={{
              provider: vapiAgent.voice_settings?.provider,
              voiceId: vapiAgent.voice_settings?.voice_id,
              model: vapiAgent.voice_settings?.model,
              speed: vapiAgent.voice_settings?.speed,
              pitch: vapiAgent.voice_settings?.pitch,
            }}
            vapiTranscriberSettings={{
              provider: vapiAgent.transcriber?.provider,
              model: vapiAgent.transcriber?.model,
              language: vapiAgent.transcriber?.language,
            }}
            vapiModelSettings={{
              provider: vapiAgent.model_settings?.provider,
              model: vapiAgent.model_settings?.model,
              temperature: vapiAgent.model_settings?.temperature,
              maxTokens: vapiAgent.model_settings?.max_tokens,
            }}
            useCustomSettings={useCustomSettings}
            onUseCustomSettingsChange={setUseCustomSettings}
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
            clonedVoices={clonedVoices || []}
            apiBaseUrl={apiBaseUrl}
            getAuthHeaders={async () => {
              const headers = await getAuthHeaders();
              return headers;
            }}
            getAuthToken={async () => {
              const headers = await getAuthHeaders();
              return headers.Authorization?.replace('Bearer ', '') || '';
            }}
            wsBaseUrl={apiBaseUrl.replace('https://', 'wss://').replace('http://', 'ws://')}
            isLoading={providersLoading}
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save Settings
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

