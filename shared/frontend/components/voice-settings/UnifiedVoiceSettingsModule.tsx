/**
 * Unified Voice Settings Module
 *
 * A complete drop-in voice settings module with all tabs:
 * - TTS (Text-to-Speech) with ComprehensiveTTSSelector
 * - ASR (Speech Recognition) with streaming test
 * - LLM (Language Model) with chat test
 * - Voices (Voice Library)
 * - Test (Full voice conversation testing)
 *
 * This module is self-contained and can be dropped into any app.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { ComprehensiveTTSSelector, TTSProviderInfo } from './ComprehensiveTTSSelector';
import { ASRProviderSelector, ASRProvider } from './ASRProviderSelector';
import { LLMModelSelector, LLMModel } from './LLMModelSelector';
import { LLMChatTestPanel } from './LLMChatTestPanel';
import { ASRStreamingTestPanel } from './ASRStreamingTestPanel';
import { VoiceTestingPanel } from '../VoiceTestingPanel';
import { ReferenceAudioList } from '../reference-audio';
import { VoiceLibrarySelector, ClonedVoice } from './VoiceLibrarySelector';

// Types
export interface VoiceSettings {
  tts: {
    default_provider: string | null;
    default_voice: string | null;
    speed: number;
    pitch: number;
  };
  asr: {
    default_provider: string | null;
    language: string;
    task: string;
  };
  llm: {
    default_model: string | null;
    temperature: number;
    max_tokens: number | null;
  };
  voices: {
    favorite_voices: string[];
    custom_voices: string[];
  };
}

export interface VAPISettings {
  voice?: {
    provider?: string;
    voiceId?: string;
    model?: string;
    speed?: number;
    pitch?: number;
  };
  transcriber?: {
    provider?: string;
    model?: string;
    language?: string;
  };
  model?: {
    provider?: string;
    model?: string;
    temperature?: number;
    maxTokens?: number;
  };
}

export interface UnifiedVoiceSettingsModuleProps {
  // API Configuration
  apiBaseUrl: string;
  wsBaseUrl: string;
  coreApiUrl?: string;
  getAuthToken: () => Promise<string>;
  getAuthHeaders?: () => Promise<Record<string, string>>;

  // Assistant Configuration (for voice test)
  assistantId: string;
  assistantName: string;

  // Feature Toggles
  enabledTabs?: ('tts' | 'asr' | 'llm' | 'voices' | 'test' | 'reference-audio')[];

  // Voice Library Configuration
  voiceCategories?: string[];
  clonedVoices?: ClonedVoice[];
  favoriteVoiceIds?: string[];

  // Language Options
  languages?: Array<{ code: string; name: string; flag?: string }>;

  // Initial Settings
  initialSettings?: Partial<VoiceSettings>;

  // VAPI Settings Support
  showVAPISettings?: boolean;
  useCustomSettings?: boolean;
  onUseCustomSettingsChange?: (useCustom: boolean) => void;
  vapiSettings?: VAPISettings;

  // Reference Audio Support
  showReferenceAudio?: boolean;
  referenceVoiceId?: string | null;
  onReferenceVoiceChange?: (audioId: string | null) => void;

  // Custom Output Format Callback (for custom_settings_override)
  onCustomSettingsChange?: (settings: {
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
  }) => void;

  // Callbacks
  onSettingsChange?: (settings: VoiceSettings) => void;
  onError?: (error: Error) => void;

  // Styling
  theme?: 'light' | 'dark' | 'auto';
  className?: string;
}

type TabType = 'tts' | 'asr' | 'llm' | 'voices' | 'test' | 'reference-audio';

// Default settings
const DEFAULT_SETTINGS: VoiceSettings = {
  tts: {
    default_provider: null,
    default_voice: null,
    speed: 1.0,
    pitch: 1.0,
  },
  asr: {
    default_provider: 'faster_whisper_large',
    language: 'en',
    task: 'transcribe',
  },
  llm: {
    default_model: 'gemini-2.5-flash',
    temperature: 0.7,
    max_tokens: null,
  },
  voices: {
    favorite_voices: [],
    custom_voices: [],
  },
};

// Default languages
const DEFAULT_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'tw', name: 'Twi', flag: '🇬🇭' },
  { code: 'yo', name: 'Yoruba', flag: '🇳🇬' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
  { code: 'es', name: 'Spanish', flag: '🇪🇸' },
];

// Inline SVG Icons
const Icons = {
  Volume2: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
    </svg>
  ),
  Mic: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" y1="19" x2="12" y2="22"/>
    </svg>
  ),
  Brain: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-1.54Z"/>
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-1.54Z"/>
    </svg>
  ),
  Star: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
    </svg>
  ),
  MessageSquare: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  ),
  Loader: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="animate-spin">
      <line x1="12" y1="2" x2="12" y2="6"/>
      <line x1="12" y1="18" x2="12" y2="22"/>
      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
      <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
      <line x1="2" y1="12" x2="6" y2="12"/>
      <line x1="18" y1="12" x2="22" y2="12"/>
      <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>
      <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
    </svg>
  ),
  AlertCircle: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
  ),
};

// Additional icons
const IconsExtended = {
  ...Icons,
  Info: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="16" x2="12" y2="12"/>
      <line x1="12" y1="8" x2="12.01" y2="8"/>
    </svg>
  ),
  CheckCircle: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
      <polyline points="22 4 12 14.01 9 11.01"/>
    </svg>
  ),
  Settings: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M12 1v6m0 6v6m9-9h-6M6 12H0"/>
    </svg>
  ),
  MicRecord: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" y1="19" x2="12" y2="22"/>
      <line x1="8" y1="22" x2="16" y2="22"/>
    </svg>
  ),
};

// Tab configuration
const TAB_CONFIG: Record<TabType, { icon: React.FC; label: string }> = {
  tts: { icon: Icons.Volume2, label: 'TTS' },
  asr: { icon: Icons.Mic, label: 'ASR' },
  llm: { icon: Icons.Brain, label: 'LLM' },
  voices: { icon: Icons.Star, label: 'Voices' },
  test: { icon: Icons.MessageSquare, label: 'Test' },
  'reference-audio': { icon: IconsExtended.MicRecord, label: 'Reference Audio' },
};

export const UnifiedVoiceSettingsModule: React.FC<UnifiedVoiceSettingsModuleProps> = ({
  apiBaseUrl,
  wsBaseUrl,
  coreApiUrl,
  getAuthToken,
  getAuthHeaders,
  assistantId,
  assistantName,
  enabledTabs = ['tts', 'asr', 'llm', 'voices', 'test'],
  voiceCategories,
  clonedVoices = [],
  favoriteVoiceIds = [],
  languages = DEFAULT_LANGUAGES,
  initialSettings,
  showVAPISettings = false,
  useCustomSettings: controlledUseCustomSettings,
  onUseCustomSettingsChange,
  vapiSettings,
  showReferenceAudio = false,
  referenceVoiceId,
  onReferenceVoiceChange,
  onCustomSettingsChange,
  onSettingsChange,
  onError,
  theme = 'auto',
  className = '',
}) => {
  // State
  const [activeTab, setActiveTab] = useState<TabType>(enabledTabs[0] || 'tts');
  const [settings, setSettings] = useState<VoiceSettings>({ ...DEFAULT_SETTINGS, ...initialSettings });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // TTS Preview state
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewAudio, setPreviewAudio] = useState<HTMLAudioElement | null>(null);

  // Use controlled prop if provided, otherwise maintain local state
  const [internalUseCustomSettings, setInternalUseCustomSettings] = useState(true);
  const useCustomSettings = controlledUseCustomSettings !== undefined ? controlledUseCustomSettings : internalUseCustomSettings;

  // Provider data
  const [ttsProviders, setTtsProviders] = useState<TTSProviderInfo[]>([]);
  const [asrProviders, setAsrProviders] = useState<ASRProvider[]>([]);
  const [llmModels, setLlmModels] = useState<LLMModel[]>([]);

  // Fetch providers on mount
  useEffect(() => {
    fetchProviders();
  }, []);

  const fetchProviders = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = await getAuthToken();
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };

      // Fetch all providers in parallel
      const [ttsRes, asrRes, llmRes] = await Promise.all([
        fetch(`${apiBaseUrl}/api/tts/providers`, { headers }).catch(() => null),
        fetch(`${apiBaseUrl}/api/asr/providers`, { headers }).catch(() => null),
        fetch(`${apiBaseUrl}/api/llm/providers`, { headers }).catch(() => null),
      ]);

      // Process TTS providers
      if (ttsRes?.ok) {
        try {
          const ttsData = await ttsRes.json();
          let providers: TTSProviderInfo[] = [];

          if (Array.isArray(ttsData)) {
            providers = ttsData;
          } else if (ttsData?.providers) {
            // Handle object format: { providers: {...} } or array format: { providers: [...] }
            const providersValue = ttsData.providers;
            providers = Array.isArray(providersValue)
              ? providersValue
              : Object.values(providersValue);
          }

          // Ensure it's an array
          if (!Array.isArray(providers)) {
            providers = [];
          }

          // Normalize capabilities from camelCase to snake_case (API returns camelCase)
          providers = providers.map((p: any) => {
            const caps = p.capabilities || {};
            return {
              ...p,
              // Set default deployment if not present
              deployment: p.deployment || 'cloud',
              // Normalize languages dict to Record<string, string>
              languages: p.languagesDict || p.languages || {},
              capabilities: {
                voice_cloning: caps.voiceCloning ?? caps.voice_cloning ?? false,
                multi_language: caps.multiLanguage ?? caps.multi_language ?? false,
                speed_control: caps.speedControl ?? caps.speed_control ?? true,
                pitch_control: caps.pitchControl ?? caps.pitch_control ?? true,
                multi_speaker: caps.multiSpeaker ?? caps.multi_speaker ?? false,
                multi_model: caps.multiModel ?? caps.multi_model ?? false,
                emotion_control: caps.emotionControl ?? caps.emotion_control ?? false,
                real_time_conversation: caps.realTimeConversation ?? caps.real_time_conversation ?? false,
                ssml_support: caps.ssmlSupport ?? caps.ssml_support ?? false,
                streaming: caps.streaming ?? false,
                supported_languages: caps.supportedLanguages ?? caps.supported_languages ?? p.languageList ?? [],
                available_models: caps.availableModels ?? caps.available_models ?? [],
              },
            };
          });

          setTtsProviders(providers);
        } catch (err) {
          console.error('Failed to parse TTS providers:', err);
          setTtsProviders([]);
        }
      }

      // Process ASR providers
      if (asrRes?.ok && asrRes.status !== 204) {
        try {
          const asrData = await asrRes.json();
          let providers: ASRProvider[] = [];
          
          if (Array.isArray(asrData)) {
            providers = asrData as ASRProvider[];
          } else if (asrData?.providers) {
            // Handle object format: { providers: {...} } or array format: { providers: [...] }
            const providersValue = asrData.providers;
            const providersArray = Array.isArray(providersValue) 
              ? providersValue 
              : Object.values(providersValue);
            providers = providersArray as ASRProvider[];
          }
          
          // Ensure it's an array
          if (!Array.isArray(providers)) {
            providers = [];
          }
          
          setAsrProviders(providers);

          // Validate current ASR provider exists in fetched list
          // If not, auto-select the default or first available provider
          const currentAsrProvider = settings.asr.default_provider;
          const providerExists = Array.isArray(providers) && currentAsrProvider && providers.some((p: any) => p.id === currentAsrProvider);
          
          // Only auto-select if current provider is missing AND we have providers available
          // Handle null/undefined gracefully without showing 'null' in warnings
          if (!providerExists && Array.isArray(providers) && providers.length > 0) {
            // Find the default provider or use first online provider
            const defaultProvider = providers.find((p: any) => p.id === 'faster_whisper_large');
            const firstOnline = providers.find((p: any) => p.status === 'online');
            const fallbackProvider = defaultProvider || firstOnline || providers[0];
            if (fallbackProvider) {
              // Only warn if currentAsrProvider is a non-null value that doesn't exist
              // If it's null/undefined, silently set the default
              if (currentAsrProvider) {
                console.warn(
                  `[VoiceSettings] ASR provider '${currentAsrProvider}' not found, ` +
                  `falling back to '${(fallbackProvider as any).id}'`
                );
              }
              setSettings(prev => ({
                ...prev,
                asr: { ...prev.asr, default_provider: (fallbackProvider as any).id }
              }));
            }
          }
          // If current provider is null and we have providers, set a default
          else if (!currentAsrProvider && Array.isArray(providers) && providers.length > 0) {
            const defaultProvider = providers.find((p: any) => p.id === 'faster_whisper_large');
            const firstOnline = providers.find((p: any) => p.status === 'online');
            const fallbackProvider = defaultProvider || firstOnline || providers[0];
            if (fallbackProvider) {
              setSettings(prev => ({
                ...prev,
                asr: { ...prev.asr, default_provider: (fallbackProvider as any).id }
              }));
            }
          }
        } catch (err) {
          console.error('Failed to parse ASR providers:', err);
          setAsrProviders([]);
        }
      } else if (asrRes?.status === 204) {
        // Handle No Content response
        console.warn('ASR providers endpoint returned 204 No Content');
        setAsrProviders([]);
      }

      // Process LLM providers
      if (llmRes?.ok) {
        const llmData = await llmRes.json();
        const providers = llmData.providers ? Object.values(llmData.providers) : [];
        setLlmModels(providers.map((p: any) => ({
          id: p.id,
          name: p.name,
          description: p.description,
          provider: p.id.startsWith('gemini') ? 'Gemini' : 'Ollama',
          contextWindow: p.context_length,
          capabilities: p.capabilities,
        })) as LLMModel[]);
      }

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load providers';
      setError(errorMsg);
      onError?.(err instanceof Error ? err : new Error(errorMsg));
    } finally {
      setLoading(false);
    }
  };

  // Handler for toggle click
  const handleToggleCustomSettings = useCallback(() => {
    const newValue = !useCustomSettings;
    if (onUseCustomSettingsChange) {
      onUseCustomSettingsChange(newValue);
    } else {
      setInternalUseCustomSettings(newValue);
    }
  }, [useCustomSettings, onUseCustomSettingsChange]);

  // Update settings handler
  const updateSettings = useCallback((updates: Partial<VoiceSettings>) => {
    setSettings(prev => {
      const newSettings = { ...prev, ...updates };
      onSettingsChange?.(newSettings);
      
      // Also emit custom settings format if callback provided
      if (onCustomSettingsChange) {
        onCustomSettingsChange({
          tts: {
            provider: newSettings.tts.default_provider,
            voice: newSettings.tts.default_voice,
            speed: newSettings.tts.speed,
            pitch: newSettings.tts.pitch,
          },
          asr: {
            provider: newSettings.asr.default_provider,
            language: newSettings.asr.language,
          },
          llm: {
            model: newSettings.llm.default_model,
            temperature: newSettings.llm.temperature,
            maxTokens: newSettings.llm.max_tokens || undefined,
          },
          referenceVoice: referenceVoiceId || null,
        });
      }
      
      return newSettings;
    });
  }, [onSettingsChange, onCustomSettingsChange, referenceVoiceId]);
  
  // Handle reference voice change
  const handleReferenceVoiceChange = useCallback((audioId: string | null) => {
    onReferenceVoiceChange?.(audioId);
    if (onCustomSettingsChange) {
      onCustomSettingsChange({
        tts: {
          provider: settings.tts.default_provider,
          voice: audioId ? `ref_audio_${audioId}` : settings.tts.default_voice,
          speed: settings.tts.speed,
          pitch: settings.tts.pitch,
        },
        asr: {
          provider: settings.asr.default_provider,
          language: settings.asr.language,
        },
        llm: {
          model: settings.llm.default_model,
          temperature: settings.llm.temperature,
          maxTokens: settings.llm.max_tokens || undefined,
        },
        referenceVoice: audioId,
      });
    }
  }, [onReferenceVoiceChange, onCustomSettingsChange, settings]);

  // TTS handlers
  const handleTTSProviderChange = useCallback((providerId: string) => {
    updateSettings({
      tts: { ...settings.tts, default_provider: providerId }
    });
  }, [settings.tts, updateSettings]);

  const handleTTSSpeedChange = useCallback((speed: number) => {
    updateSettings({
      tts: { ...settings.tts, speed }
    });
  }, [settings.tts, updateSettings]);

  const handleTTSPitchChange = useCallback((pitch: number) => {
    updateSettings({
      tts: { ...settings.tts, pitch }
    });
  }, [settings.tts, updateSettings]);

  // ASR handlers
  const handleASRProviderChange = useCallback((providerId: string) => {
    updateSettings({
      asr: { ...settings.asr, default_provider: providerId }
    });
  }, [settings.asr, updateSettings]);

  const handleASRLanguageChange = useCallback((language: string) => {
    updateSettings({
      asr: { ...settings.asr, language }
    });
  }, [settings.asr, updateSettings]);

  // LLM handlers
  const handleLLMModelChange = useCallback((modelId: string) => {
    updateSettings({
      llm: { ...settings.llm, default_model: modelId }
    });
  }, [settings.llm, updateSettings]);

  const handleLLMTemperatureChange = useCallback((temperature: number) => {
    updateSettings({
      llm: { ...settings.llm, temperature }
    });
  }, [settings.llm, updateSettings]);

  const handleLLMMaxTokensChange = useCallback((maxTokens: number | null) => {
    updateSettings({
      llm: { ...settings.llm, max_tokens: maxTokens }
    });
  }, [settings.llm, updateSettings]);

  // TTS Preview handler
  const handlePreviewVoice = useCallback(async (previewText: string) => {
    if (!settings.tts.default_provider) {
      setError('Please select a TTS provider first');
      return;
    }

    // Stop any currently playing audio
    if (previewAudio) {
      previewAudio.pause();
      previewAudio.currentTime = 0;
    }

    setPreviewLoading(true);

    try {
      const token = await getAuthToken();
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };

      // Use unified TTS API preview endpoint
      const synthesisRequest = {
        provider_id: settings.tts.default_provider,
        text: previewText,
        language: 'en',
        voice_id: settings.tts.default_voice || undefined,
        speed: settings.tts.speed || 1.0,
        pitch: settings.tts.pitch || 0.0,
        output_format: 'wav'
      };

      const response = await fetch(`${apiBaseUrl}/api/tts/preview`, {
        method: 'POST',
        headers,
        body: JSON.stringify(synthesisRequest),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || 'TTS synthesis failed');
      }

      const data = await response.json();

      if (data.audio_base64) {
        const audioBlob = await fetch(`data:audio/wav;base64,${data.audio_base64}`).then(r => r.blob());
        const audioUrl = URL.createObjectURL(audioBlob);

        const audio = new Audio(audioUrl);
        setPreviewAudio(audio);

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
        };

        await audio.play();
      } else {
        throw new Error('No audio data returned from TTS service');
      }
    } catch (err) {
      console.error('TTS preview failed:', err);
      setError(err instanceof Error ? err.message : 'Preview failed');
    } finally {
      setPreviewLoading(false);
    }
  }, [settings.tts, apiBaseUrl, getAuthToken, previewAudio]);

  // Check if testing is ready
  const isTestReady = settings.tts.default_provider && settings.asr.default_provider && settings.llm.default_model;

  // Theme classes
  const themeClasses = theme === 'dark'
    ? 'bg-gray-900 text-white'
    : theme === 'light'
      ? 'bg-white text-gray-900'
      : 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white';

  if (loading) {
    return (
      <div className={`${themeClasses} border border-gray-200 dark:border-gray-700 rounded-lg p-8 ${className}`}>
        <div className="flex flex-col items-center justify-center">
          <Icons.Loader />
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">Loading voice settings...</p>
        </div>
      </div>
    );
  }

  // Build effective tabs list (include reference-audio if enabled)
  const effectiveTabs = showReferenceAudio && !enabledTabs.includes('reference-audio' as TabType)
    ? [...enabledTabs, 'reference-audio' as TabType]
    : enabledTabs;

  // Show VAPI settings if enabled and not using custom settings
  if (showVAPISettings && !useCustomSettings && vapiSettings) {
    return (
      <div className={`${themeClasses} border border-gray-200 dark:border-gray-700 rounded-lg ${className}`}>
        {/* VAPI Settings Display */}
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">VAPI Assistant Settings</h3>
            {onUseCustomSettingsChange && (
              <button
                onClick={() => {
                  setUseCustomSettings(true);
              handleToggleCustomSettings();
            }}
            className="px-4 py-2 text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            Switch to Custom Settings
          </button>
            )}
          </div>
          
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300 mb-2">
              <IconsExtended.Info />
              <span className="text-sm font-medium">Using VAPI Assistant Settings</span>
            </div>
            <p className="text-sm text-blue-600 dark:text-blue-400">
              Current settings are from the imported VAPI assistant. Toggle to use custom settings instead.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* VAPI Voice Settings */}
            {vapiSettings.voice && (
              <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Icons.Volume2 />
                  <span className="font-medium">TTS (Voice)</span>
                </div>
                <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  <div><strong>Provider:</strong> {vapiSettings.voice.provider || 'Not set'}</div>
                  <div><strong>Voice ID:</strong> {vapiSettings.voice.voiceId || 'Not set'}</div>
                  {vapiSettings.voice.model && <div><strong>Model:</strong> {vapiSettings.voice.model}</div>}
                  {vapiSettings.voice.speed && <div><strong>Speed:</strong> {vapiSettings.voice.speed}x</div>}
                </div>
              </div>
            )}

            {/* VAPI Transcriber Settings */}
            {vapiSettings.transcriber && (
              <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Icons.Mic />
                  <span className="font-medium">ASR (Transcriber)</span>
                </div>
                <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  <div><strong>Provider:</strong> {vapiSettings.transcriber.provider || 'Not set'}</div>
                  {vapiSettings.transcriber.model && <div><strong>Model:</strong> {vapiSettings.transcriber.model}</div>}
                  <div><strong>Language:</strong> {vapiSettings.transcriber.language || 'Not set'}</div>
                </div>
              </div>
            )}

            {/* VAPI Model Settings */}
            {vapiSettings.model && (
              <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Icons.Brain />
                  <span className="font-medium">LLM (Model)</span>
                </div>
                <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  <div><strong>Provider:</strong> {vapiSettings.model.provider || 'Not set'}</div>
                  <div><strong>Model:</strong> {vapiSettings.model.model || 'Not set'}</div>
                  {vapiSettings.model.temperature !== undefined && (
                    <div><strong>Temperature:</strong> {vapiSettings.model.temperature}</div>
                  )}
                  {vapiSettings.model.maxTokens && (
                    <div><strong>Max Tokens:</strong> {vapiSettings.model.maxTokens}</div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${themeClasses} border border-gray-200 dark:border-gray-700 rounded-lg ${className}`}>
      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-700">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
            <Icons.AlertCircle />
            <span className="text-sm">{error}</span>
            <button
              onClick={fetchProviders}
              className="ml-auto text-sm underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* VAPI Toggle (if enabled) */}
      {showVAPISettings && onUseCustomSettingsChange && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between bg-gray-50 dark:bg-gray-800/50">
          <div>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">Settings Mode</span>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {useCustomSettings ? 'Using custom voice settings' : 'Using VAPI assistant settings'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-xs font-medium ${!useCustomSettings ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}`}>
              VAPI
            </span>
            <button
              onClick={handleToggleCustomSettings}
              className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                useCustomSettings 
                  ? 'bg-indigo-600 shadow-lg shadow-indigo-500/50' 
                  : 'bg-gray-400 dark:bg-gray-500 shadow-md'
              }`}
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full shadow-lg transition-transform ${
                  useCustomSettings 
                    ? 'translate-x-6 bg-white' 
                    : 'translate-x-1 bg-gray-100 dark:bg-gray-200'
                }`}
              />
            </button>
            <span className={`text-xs font-medium ${useCustomSettings ? 'text-indigo-700 dark:text-indigo-400' : 'text-gray-500 dark:text-gray-400'}`}>
              Custom
            </span>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex overflow-x-auto">
          {effectiveTabs.map(tab => {
            const config = TAB_CONFIG[tab as TabType];
            if (!config) return null;
            const IconComponent = config.icon;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as TabType)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === tab
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                }`}
              >
                <IconComponent />
                {config.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-4">
        {/* TTS Tab */}
        {activeTab === 'tts' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold mb-4">Text-to-Speech Settings</h3>
            <ComprehensiveTTSSelector
              providers={ttsProviders}
              selectedProviderId={settings.tts.default_provider}
              onSelectProvider={handleTTSProviderChange}
              selectedVoice={settings.tts.default_voice || undefined}
              onSelectVoice={(voice) => updateSettings({ tts: { ...settings.tts, default_voice: voice } })}
              speed={settings.tts.speed}
              onSpeedChange={handleTTSSpeedChange}
              pitch={settings.tts.pitch}
              onPitchChange={handleTTSPitchChange}
              showAdvanced={true}
              isLoading={loading}
              onPreview={handlePreviewVoice}
              previewLoading={previewLoading}
              variant={theme === 'dark' ? 'dark' : 'light'}
            />
            
            {/* Reference Audio for Zero-Shot Cloning */}
            {showReferenceAudio && settings.tts.default_provider && 
             Array.isArray(ttsProviders) && ttsProviders.length > 0 && 
             (() => {
               // Double-check that ttsProviders is still an array before calling find
               if (!Array.isArray(ttsProviders)) return false;
               const provider = ttsProviders.find(p => p && p.id === settings.tts.default_provider);
               return provider?.capabilities?.voice_cloning;
             })() && 
             getAuthHeaders && (
              <div className="pt-4 mt-4 border-t border-gray-200 dark:border-gray-700">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Reference Audio for Zero-Shot Voice Cloning
                </label>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                  Select reference audio to use with {settings.tts.default_provider}. This provider supports zero-shot voice cloning from audio samples.
                </p>
                <ReferenceAudioList
                  apiBaseUrl={apiBaseUrl}
                  getAuthHeaders={getAuthHeaders}
                  onSelect={(audio) => {
                    handleReferenceVoiceChange(audio.reference_audio_id);
                    updateSettings({ 
                      tts: { 
                        ...settings.tts, 
                        default_voice: `ref_audio_${audio.reference_audio_id}` 
                      } 
                    });
                  }}
                  selectedId={referenceVoiceId || undefined}
                  showUpload={true}
                />
              </div>
            )}
          </div>
        )}

        {/* ASR Tab */}
        {activeTab === 'asr' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Speech Recognition Settings</h3>
              <ASRProviderSelector
                providers={asrProviders}
                selectedProviderId={settings.asr.default_provider}
                onSelectProvider={handleASRProviderChange}
              />

              {/* Language Selection */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Default Language
                </label>
                <select
                  value={settings.asr.language}
                  onChange={(e) => handleASRLanguageChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">Auto-detect</option>
                  {languages.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.flag ? `${lang.flag} ` : ''}{lang.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* ASR Test Panel */}
            <ASRStreamingTestPanel
              apiBaseUrl={apiBaseUrl}
              wsBaseUrl={wsBaseUrl}
              getAuthToken={getAuthToken}
              selectedProvider={settings.asr.default_provider || undefined}
              language={settings.asr.language}
              defaultMode="realtime"
              disabled={!settings.asr.default_provider}
              disabledReason="Select an ASR provider to test"
              languages={languages}
            />
          </div>
        )}

        {/* LLM Tab */}
        {activeTab === 'llm' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Language Model Settings</h3>
              <LLMModelSelector
                models={llmModels}
                selectedModelId={settings.llm.default_model}
                onSelectModel={handleLLMModelChange}
              />

              {/* Temperature Control */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Temperature: {settings.llm.temperature.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={settings.llm.temperature}
                  onChange={(e) => handleLLMTemperatureChange(parseFloat(e.target.value))}
                  className="w-full"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Lower values make responses more focused, higher values more creative
                </p>
              </div>

              {/* Max Tokens Control */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Max Tokens: {settings.llm.max_tokens ? settings.llm.max_tokens.toLocaleString() : 'Unlimited'}
                </label>
                <input
                  type="number"
                  min="100"
                  max="100000"
                  step="100"
                  value={settings.llm.max_tokens || ''}
                  onChange={(e) => handleLLMMaxTokensChange(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Unlimited"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Maximum number of tokens in the response (leave empty for unlimited)
                </p>
              </div>
            </div>

            {/* LLM Chat Test Panel */}
            <LLMChatTestPanel
              apiBaseUrl={apiBaseUrl}
              getAuthToken={getAuthToken}
              selectedModel={settings.llm.default_model || undefined}
              temperature={settings.llm.temperature}
              maxTokens={settings.llm.max_tokens || undefined}
              disabled={!settings.llm.default_model}
              disabledReason="Select an LLM model to test"
            />
          </div>
        )}

        {/* Voices Tab */}
        {activeTab === 'voices' && (
          <div className="space-y-6">
            {/* Reference Audio for Zero-Shot Cloning */}
            {showReferenceAudio && getAuthHeaders && (
              <div>
                <div className="mb-2">
                  <h3 className="text-lg font-semibold mb-1">Reference Audio (Zero-Shot Voice Cloning)</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Upload reference audio files to use with zero-shot TTS providers (F5-TTS, StyleTTS2, Coqui XTTS, OpenVoice). 
                    These providers can clone voices from short audio samples without training.
                  </p>
                </div>
                <ReferenceAudioList
                  apiBaseUrl={apiBaseUrl}
                  getAuthHeaders={getAuthHeaders}
                  onSelect={(audio) => {
                    handleReferenceVoiceChange(audio.reference_audio_id);
                  }}
                  selectedId={referenceVoiceId || undefined}
                  showUpload={true}
                />
              </div>
            )}
            
            {/* Cloned Voices (Pre-trained Voice Library) */}
            {clonedVoices.length > 0 && (
              <div className={showReferenceAudio ? "pt-4 border-t border-gray-200 dark:border-gray-700" : ""}>
                <div className="mb-2">
                  <h3 className="text-lg font-semibold mb-1">Cloned Voices (Pre-trained)</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Select from pre-trained voice clones that have been trained on longer audio samples.
                  </p>
                </div>
                <VoiceLibrarySelector
                  voices={clonedVoices}
                  favoriteVoiceIds={favoriteVoiceIds}
                  onToggleFavorite={() => {
                    // TODO: Implement favorite toggle
                  }}
                  onPreviewVoice={() => {
                    // TODO: Implement voice preview
                  }}
                  isLoading={loading}
                  disabled={false}
                />
              </div>
            )}
            
            {/* Empty state */}
            {clonedVoices.length === 0 && !showReferenceAudio && (
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-8 text-center">
                <Icons.Star />
                <p className="mt-2 text-gray-500 dark:text-gray-400">
                  Voice library is managed per-app. Configure favorites in your app's voice settings.
                </p>
                {settings.voices.favorite_voices.length > 0 && (
                  <p className="mt-2 text-sm text-indigo-600 dark:text-indigo-400">
                    {settings.voices.favorite_voices.length} favorite voice(s) saved
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Reference Audio Tab (standalone) */}
        {activeTab === 'reference-audio' && showReferenceAudio && getAuthHeaders && (
          <div>
            <h3 className="text-lg font-semibold mb-4">Reference Audio Library</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Upload and manage reference audio files for zero-shot voice cloning with TTS providers like F5-TTS, StyleTTS2, Coqui XTTS, and OpenVoice.
            </p>
            <ReferenceAudioList
              apiBaseUrl={apiBaseUrl}
              getAuthHeaders={getAuthHeaders}
              onSelect={(audio) => {
                handleReferenceVoiceChange(audio.reference_audio_id);
              }}
              selectedId={referenceVoiceId || undefined}
              showUpload={true}
            />
          </div>
        )}

        {/* Test Tab */}
        {activeTab === 'test' && (
          <div>
            <h3 className="text-lg font-semibold mb-4">Test Voice Conversation</h3>
            <VoiceTestingPanel
              assistantId={assistantId}
              assistantName={assistantName}
              apiBaseUrl={coreApiUrl || apiBaseUrl}
              wsBaseUrl={wsBaseUrl}
              getAuthToken={getAuthToken}
              assistant={{
                language: settings.asr.language,
                llm_provider: settings.llm.default_model || undefined,
                tts_provider: settings.tts.default_provider || undefined,
                stt_provider: settings.asr.default_provider || undefined,
              }}
              languages={languages}
              disabled={!isTestReady}
              disabledReason={
                !settings.tts.default_provider ? 'Select a TTS provider first' :
                !settings.asr.default_provider ? 'Select an ASR provider first' :
                !settings.llm.default_model ? 'Select an LLM model first' : undefined
              }
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default UnifiedVoiceSettingsModule;
