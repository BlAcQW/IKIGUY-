/**
 * Voice Settings Override Component
 * 
 * Allows users to either use VAPI assistant settings directly or override
 * with custom TTS, ASR, LLM, and reference voice settings from our platform.
 * 
 * Now uses UnifiedVoiceSettingsModule from @kasaai/shared-frontend for all voice settings.
 */

import React, { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Settings } from 'lucide-react';
import { UnifiedVoiceSettingsModule, VAPISettings } from '@kasaai/shared-frontend/components/voice-settings/UnifiedVoiceSettingsModule';
import type { TTSProviderInfo } from '@kasaai/shared-frontend/components/voice-settings/ComprehensiveTTSSelector';
import type { ASRProvider } from '@kasaai/shared-frontend/components/voice-settings/ASRProviderSelector';
import type { LLMModel } from '@kasaai/shared-frontend/components/voice-settings/LLMModelSelector';
import type { ClonedVoice } from '@kasaai/shared-frontend/components/voice-settings/VoiceLibrarySelector';

export interface VAPIVoiceSettings {
  provider?: string;
  voiceId?: string;
  model?: string;
  speed?: number;
  pitch?: number;
}

export interface VAPITranscriberSettings {
  provider?: string;
  model?: string;
  language?: string;
}

export interface VAPIModelSettings {
  provider?: string;
  model?: string;
  temperature?: number;
  maxTokens?: number;
}

export interface VoiceSettingsOverrideProps {
  // VAPI Settings (from imported assistant)
  vapiVoiceSettings?: VAPIVoiceSettings;
  vapiTranscriberSettings?: VAPITranscriberSettings;
  vapiModelSettings?: VAPIModelSettings;
  
  // Custom Settings Override
  useCustomSettings: boolean;
  onUseCustomSettingsChange: (useCustom: boolean) => void;
  
  // Custom TTS Settings
  customTTSProvider?: string | null;
  customTTSVoice?: string | null;
  customTTSSpeed?: number;
  customTTSPitch?: number;
  onCustomTTSChange?: (settings: {
    provider?: string;
    voice?: string;
    speed?: number;
    pitch?: number;
  }) => void;
  
  // Custom ASR Settings
  customASRProvider?: string | null;
  customASRLanguage?: string;
  onCustomASRChange?: (settings: {
    provider?: string;
    language?: string;
  }) => void;
  
  // Custom LLM Settings
  customLLMModel?: string | null;
  customLLMTemperature?: number;
  customLLMMaxTokens?: number;
  onCustomLLMChange?: (settings: {
    model?: string;
    temperature?: number;
    maxTokens?: number;
  }) => void;
  
  // Reference Voice (for zero-shot cloning)
  customReferenceVoiceId?: string | null;
  onCustomReferenceVoiceChange?: (referenceAudioId: string | null) => void;
  
  // Data Sources (optional - UnifiedVoiceSettingsModule will fetch if not provided)
  ttsProviders?: TTSProviderInfo[];
  asrProviders?: ASRProvider[];
  llmModels?: LLMModel[];
  clonedVoices?: ClonedVoice[];
  favoriteVoiceIds?: string[];
  
  // API Configuration
  apiBaseUrl: string;
  getAuthHeaders?: () => Promise<Record<string, string>>;
  getAuthToken?: () => Promise<string>;
  wsBaseUrl?: string;
  
  // State
  isLoading?: boolean;
  disabled?: boolean;
  className?: string;
}

export const VoiceSettingsOverride: React.FC<VoiceSettingsOverrideProps> = ({
  vapiVoiceSettings,
  vapiTranscriberSettings,
  vapiModelSettings,
  useCustomSettings,
  onUseCustomSettingsChange,
  customTTSProvider,
  customTTSVoice,
  customTTSSpeed = 1.0,
  customTTSPitch = 0.0,
  onCustomTTSChange,
  customASRProvider,
  customASRLanguage = 'en',
  onCustomASRChange,
  customLLMModel,
  customLLMTemperature = 0.7,
  customLLMMaxTokens = 2000,
  onCustomLLMChange,
  customReferenceVoiceId,
  onCustomReferenceVoiceChange,
  clonedVoices = [],
  favoriteVoiceIds = [],
  apiBaseUrl,
  getAuthHeaders,
  getAuthToken,
  wsBaseUrl,
  isLoading = false,
  disabled = false,
  className = '',
}) => {
  // Convert VAPI settings to UnifiedVoiceSettingsModule format
  const vapiSettings: VAPISettings | undefined = useMemo(() => {
    if (!vapiVoiceSettings && !vapiTranscriberSettings && !vapiModelSettings) {
      return undefined;
    }
    return {
      voice: vapiVoiceSettings ? {
        provider: vapiVoiceSettings.provider,
        voiceId: vapiVoiceSettings.voiceId,
        model: vapiVoiceSettings.model,
        speed: vapiVoiceSettings.speed,
        pitch: vapiVoiceSettings.pitch,
      } : undefined,
      transcriber: vapiTranscriberSettings ? {
        provider: vapiTranscriberSettings.provider,
        model: vapiTranscriberSettings.model,
        language: vapiTranscriberSettings.language,
      } : undefined,
      model: vapiModelSettings ? {
        provider: vapiModelSettings.provider,
        model: vapiModelSettings.model,
        temperature: vapiModelSettings.temperature,
        maxTokens: vapiModelSettings.maxTokens,
      } : undefined,
    };
  }, [vapiVoiceSettings, vapiTranscriberSettings, vapiModelSettings]);

  // Convert WebSocket URL
  const effectiveWsBaseUrl = wsBaseUrl || apiBaseUrl.replace('https://', 'wss://').replace('http://', 'ws://');

  // Get auth token function
  const getAuthTokenFn = async (): Promise<string> => {
    if (getAuthToken) {
      return await getAuthToken();
    }
    if (getAuthHeaders) {
      const headers = await getAuthHeaders();
      return headers.Authorization?.replace('Bearer ', '') || '';
    }
    return '';
  };

  // Handle custom settings changes
  const handleCustomSettingsChange = (settings: {
    tts?: {
      provider?: string | null;
      voice?: string | null;
      speed?: number;
      pitch?: number;
    };
    asr?: {
      provider?: string | null;
      language?: string;
    };
    llm?: {
      model?: string | null;
      temperature?: number;
      maxTokens?: number;
    };
    referenceVoice?: string | null;
  }) => {
    // Emit individual callbacks for backwards compatibility
    if (settings.tts && onCustomTTSChange) {
      onCustomTTSChange({
        provider: settings.tts.provider || undefined,
        voice: settings.tts.voice || undefined,
        speed: settings.tts.speed,
        pitch: settings.tts.pitch,
      });
    }
    if (settings.asr && onCustomASRChange) {
      onCustomASRChange({
        provider: settings.asr.provider || undefined,
        language: settings.asr.language,
      });
    }
    if (settings.llm && onCustomLLMChange) {
      onCustomLLMChange({
        model: settings.llm.model || undefined,
        temperature: settings.llm.temperature,
        maxTokens: settings.llm.maxTokens,
      });
    }
    if (settings.referenceVoice !== undefined && onCustomReferenceVoiceChange) {
      onCustomReferenceVoiceChange(settings.referenceVoice);
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Voice Settings
            </CardTitle>
            <CardDescription>
              Choose to use VAPI assistant settings or override with custom voice, ASR, and LLM configurations
            </CardDescription>
          </div>
          <div className="flex items-center gap-3">
            <Label htmlFor="use-custom-settings" className="text-sm font-medium">
              {useCustomSettings ? 'Custom Settings' : 'VAPI Settings'}
            </Label>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border bg-gray-50">
              <span className={`text-xs font-medium ${!useCustomSettings ? 'text-gray-700' : 'text-gray-400'}`}>
                VAPI
              </span>
              <Switch
                id="use-custom-settings"
                checked={useCustomSettings}
                onCheckedChange={onUseCustomSettingsChange}
                disabled={disabled || isLoading}
                className="data-[state=checked]:bg-indigo-600 data-[state=unchecked]:bg-gray-400 dark:data-[state=unchecked]:bg-gray-500"
              />
              <span className={`text-xs font-medium ${useCustomSettings ? 'text-indigo-700' : 'text-gray-400'}`}>
                Custom
              </span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <UnifiedVoiceSettingsModule
          apiBaseUrl={apiBaseUrl}
          wsBaseUrl={effectiveWsBaseUrl}
          getAuthToken={getAuthTokenFn}
          getAuthHeaders={getAuthHeaders}
          assistantId="automation-voice-assistant"
          assistantName="Automation Voice Assistant"
          enabledTabs={['tts', 'asr', 'llm', 'voices', 'test']}
          clonedVoices={clonedVoices}
          favoriteVoiceIds={favoriteVoiceIds}
          showVAPISettings={!!vapiSettings}
          useCustomSettings={useCustomSettings}
          onUseCustomSettingsChange={onUseCustomSettingsChange}
          vapiSettings={vapiSettings}
          showReferenceAudio={true}
          referenceVoiceId={customReferenceVoiceId}
          onReferenceVoiceChange={onCustomReferenceVoiceChange}
          onCustomSettingsChange={handleCustomSettingsChange}
          initialSettings={{
            tts: {
              default_provider: customTTSProvider || null,
              default_voice: customTTSVoice || null,
              speed: customTTSSpeed,
              pitch: customTTSPitch,
            },
            asr: {
              default_provider: customASRProvider || null,
              language: customASRLanguage,
              task: 'transcribe',
            },
            llm: {
              default_model: customLLMModel || null,
              temperature: customLLMTemperature,
              max_tokens: customLLMMaxTokens || null,
            },
            voices: {
              favorite_voices: favoriteVoiceIds,
              custom_voices: [],
            },
          }}
          languages={[
            { code: 'en', name: 'English', flag: '🇬🇧' },
            { code: 'tw', name: 'Twi', flag: '🇬🇭' },
            { code: 'yo', name: 'Yoruba', flag: '🇳🇬' },
            { code: 'es', name: 'Spanish', flag: '🇪🇸' },
            { code: 'fr', name: 'French', flag: '🇫🇷' },
            { code: 'de', name: 'German', flag: '🇩🇪' },
            { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
            { code: 'ar', name: 'Arabic', flag: '🇸🇦' },
            { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
            { code: 'ak', name: 'Akan', flag: '🇬🇭' },
          ]}
          theme="light"
          className="border-0 shadow-none"
        />
      </CardContent>
    </Card>
  );
};
