import React, { useState, useEffect } from 'react';
import { Settings, Mic, Volume2, MessageSquare, BarChart3, Phone, Upload } from 'lucide-react';
import { Assistant } from './AssistantList';
import { VapiAnalyticsDashboard } from './VapiAnalyticsDashboard';
import { PhoneTestingPanel } from '@/components/phone/PhoneTestingPanel';
import { API_BASE_URL, WS_BASE_URL } from '@/config/api-config';
import { useToast } from '@/hooks/use-toast';
import { getAuthHeaders } from '@/lib/auth-utils';
import {
  LLM_MODELS_BY_PROVIDER,
  ASR_MODELS_BY_PROVIDER,
  TTS_VOICES_BY_PROVIDER,
  LLM_PROVIDERS,
  ASR_PROVIDERS,
  TTS_PROVIDERS,
} from '@/config/voice-agent-providers';
import { LLM_MODELS } from '@/config/llm-models';
import { useTTSProvider } from '@/hooks/useTTSProvider';
import { useASRProvider } from '@/hooks/useASRProvider';
import { ComprehensiveTTSSelector } from '../../../../shared/frontend/components/voice-settings/ComprehensiveTTSSelector';
import { useComprehensiveTTS } from '../../../../shared/frontend/hooks/useComprehensiveTTS';
import { ASRProviderSelector } from '../../../../shared/frontend/components/voice-settings/ASRProviderSelector';
import { LLMModelSelector, LLMModel } from '../../../../shared/frontend/components/voice-settings/LLMModelSelector';
import { LLMChatTestPanel } from '../../../../shared/frontend/components/voice-settings/LLMChatTestPanel';
import { ASRStreamingTestPanel } from '../../../../shared/frontend/components/voice-settings/ASRStreamingTestPanel';
import { ReferenceAudioList } from '../../../../shared/frontend/components/voice-settings';

interface ConfigurationData {
  llm_provider: string;
  llm_model: string;
  tts_provider: string;
  tts_model: string;
  tts_voice: string;
  stt_provider: string;
  stt_model: string;
  language: string;
  country: string;
  system_prompt: string;
  first_message_mode: string;
  first_message: string;
  // Voice parameters
  stability: number;
  clarity_similarity: number;
  speed: number;
  style_exaggeration: number;
  optimize_streaming_latency: number;
  voice_description?: string; // Parler-TTS voice description
}

interface AssistantConfigurationProps {
  assistant: Assistant | null;
  onConfigurationChange: (config: Partial<ConfigurationData>) => void;
  onPublish: () => void;
}

type ConfigTab = 'llm' | 'voice' | 'transcriber' | 'analytics' | 'testing' | 'reference-audio';

export const AssistantConfiguration: React.FC<AssistantConfigurationProps> = ({
  assistant,
  onConfigurationChange,
  onPublish
}) => {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<ConfigTab>('llm');
  const [ttsModels, setTtsModels] = useState<Array<{ value: string; label: string }>>([]);
  const [availableLanguages, setAvailableLanguages] = useState<Array<{ value: string; label: string }>>([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewAudio, setPreviewAudio] = useState<HTMLAudioElement | null>(null);
  
  // LLM models state
  const [llmModels, setLlmModels] = useState<LLMModel[]>([]);
  const [isLoadingLLMProviders, setIsLoadingLLMProviders] = useState(false);
  
  // ASR providers as array for selector
  const [asrProvidersArray, setAsrProvidersArray] = useState<Array<{
    id: string;
    name: string;
    description?: string;
    status: 'online' | 'offline' | 'building';
    icon?: string;
    languages?: string[];
  }>>([]);

  // Normalize old ASR provider IDs to new structure
  const normalizeAsrProviderId = (providerId: string): string => {
    // Map old provider IDs to new ones
    if (providerId?.includes('whisper') || providerId?.includes('akan') || providerId?.includes('faster')) {
      return 'whisper';
    }
    return providerId || 'whisper';
  };

  // Use the TTS provider hook to get actual providers from API
  const {
    providers: ttsProviders,
    isLoadingProviders,
    getSpeakers
  } = useTTSProvider();

  // Use useASRProvider hook for dynamic ASR providers
  const {
    providers: asrProviders,
    isLoading: isLoadingASRProviders
  } = useASRProvider();
  
  // Transform ASR providers to array format for selector
  useEffect(() => {
    if (asrProviders && Object.keys(asrProviders).length > 0) {
      const providersArray = Object.values(asrProviders).map(p => ({
        id: p.id,
        name: p.name,
        description: p.description,
        status: p.status,
        icon: p.icon,
        languages: p.languages
      }));
      setAsrProvidersArray(providersArray);
    }
  }, [asrProviders]);
  
  // Fetch LLM providers and transform to models
  useEffect(() => {
    const fetchLLMProviders = async () => {
      setIsLoadingLLMProviders(true);
      try {
        const authHeaders = await getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/api/llm/providers`, {
          headers: {
            ...authHeaders,
            'Content-Type': 'application/json',
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          const providers = data.providers ? Object.values(data.providers) : [];
          
          // Transform providers to LLMModel format
          const models: LLMModel[] = providers.map((p: any) => ({
            id: p.id,
            name: p.name,
            description: p.description,
            provider: p.id.split('_')[0] || p.id, // Extract provider name from ID
            contextWindow: p.context_length,
            capabilities: p.capabilities || {},
            icon: '🤖'
          }));
          
          setLlmModels(models);
        }
      } catch (error) {
        console.error('Failed to fetch LLM providers:', error);
      } finally {
        setIsLoadingLLMProviders(false);
      }
    };
    
    fetchLLMProviders();
  }, []);

  // Use comprehensive TTS hook for the new selector
  const {
    providers: comprehensiveTTSProviders,
    loading: loadingComprehensiveTTS,
    error: comprehensiveTTSError
  } = useComprehensiveTTS(API_BASE_URL, undefined, {
    onlineOnly: false,
    autoFetch: true,
    endpointPath: '/api/tts/providers'  // Fixed: Use correct endpoint with /api prefix
  });

  // Use centralized provider configurations
  const modelsByProvider = LLM_MODELS_BY_PROVIDER;
  const voicesByProvider = TTS_VOICES_BY_PROVIDER;
  const sttModelsByProvider = ASR_MODELS_BY_PROVIDER;

  // Preview TTS voice handler
  const handlePreviewVoice = async (previewText: string) => {
    if (!assistant || !assistant.tts_provider) {
      toast({
        title: "Cannot preview voice",
        description: "Please select a TTS provider first",
        variant: "destructive"
      });
      return;
    }

    // Stop any currently playing audio
    if (previewAudio) {
      previewAudio.pause();
      previewAudio.currentTime = 0;
    }

    setPreviewLoading(true);

    try {
      // Build synthesis request
      const synthesisRequest = {
        provider_id: assistant.tts_provider,
        text: previewText,
        language: assistant.language || 'en',
        voice_id: assistant.tts_voice || undefined,
        speed: assistant.speed || 1.0,
        pitch: assistant.pitch || 0.0,
        output_format: 'wav'
        // Note: user_id is extracted from JWT token by backend auth
      };

      console.log('🔊 Preview TTS synthesis:', synthesisRequest);

      // Get auth headers using the app's auth utility
      const authHeaders = await getAuthHeaders();

      // Call TTS synthesis API
      const response = await fetch(`${API_BASE_URL}/api/tts/synthesize`, {
        method: 'POST',
        headers: {
          ...authHeaders,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(synthesisRequest),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));

        // Handle different error formats
        let errorMessage = 'TTS synthesis failed';
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          // FastAPI validation errors
          errorMessage = errorData.detail.map((err: any) => err.msg).join(', ');
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else {
          errorMessage = response.statusText;
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();

      // Decode base64 audio
      if (data.audio_base64) {
        const audioBlob = await fetch(`data:audio/wav;base64,${data.audio_base64}`).then(r => r.blob());
        const audioUrl = URL.createObjectURL(audioBlob);

        // Create and play audio
        const audio = new Audio(audioUrl);
        setPreviewAudio(audio);

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
        };

        await audio.play();

        console.log('✅ TTS preview played successfully:', {
          duration: data.duration,
          cost: data.cost,
          provider: data.provider_id
        });

        // Show success toast
        toast({
          title: "Voice preview played",
          description: `Provider: ${data.provider_id} • Duration: ${data.duration?.toFixed(2)}s • Cost: $${data.cost?.toFixed(4) || '0.0000'}`,
        });
      } else {
        throw new Error('No audio data returned from TTS service');
      }
    } catch (error: any) {
      console.error('❌ TTS preview failed:', error);
      toast({
        title: "Preview failed",
        description: error.message || 'Unknown error occurred',
        variant: "destructive"
      });
    } finally {
      setPreviewLoading(false);
    }
  };

  // Fetch TTS models for the selected provider
  useEffect(() => {
    const fetchTtsModels = async () => {
      if (!assistant?.tts_provider || !ttsProviders[assistant.tts_provider]) {
        setTtsModels([]);
        return;
      }

      const provider = ttsProviders[assistant.tts_provider];

      // Get models based on provider type
      if (provider.id === 'meta_mms') {
        setTtsModels([
          { value: 'meta_mms', label: 'Meta MMS (Multilingual)' },
          { value: 'meta_tts_aka', label: 'Meta TTS AKA (Twi/Akan)' }
        ]);
      } else if (provider.id === 'coqui_xtts' || provider.id === 'xtts') {
        // Coqui XTTS models
        setTtsModels([
          { value: 'tts_models/multilingual/multi-dataset/xtts_v2', label: 'XTTS v2 Multilingual' },
          { value: 'tts_models/multilingual/multi-dataset/your_tts', label: 'YourTTS Multilingual' },
          { value: 'xtts_twi_v1', label: 'XTTS Twi v1 (Fine-tuned)' },
          { value: 'tts_models/en/vctk/vits', label: 'VCTK VITS (Multi-speaker)' },
          { value: 'tts_models/en/ljspeech/tacotron2-DDC', label: 'LJSpeech Tacotron2' },
          { value: 'tts_models/en/ljspeech/glow-tts', label: 'LJSpeech Glow-TTS' }
        ]);
      } else if (provider.id === 'f5tts') {
        setTtsModels([
          { value: 'f5_tts_base', label: 'F5-TTS Base' },
          { value: 'f5_tts_small', label: 'F5-TTS Small' },
          { value: 'e2_tts', label: 'E2-TTS Enhanced' }
        ]);
      } else if (provider.id === 'styletts2') {
        setTtsModels([
          { value: 'styletts2_base', label: 'StyleTTS2 Base' },
          { value: 'styletts2_ljspeech', label: 'StyleTTS2 LJSpeech' }
        ]);
      } else if (provider.id === 'melotts') {
        setTtsModels([
          { value: 'melo_en', label: 'MeloTTS English' },
          { value: 'melo_zh', label: 'MeloTTS Chinese' },
          { value: 'melo_jp', label: 'MeloTTS Japanese' },
          { value: 'melo_kr', label: 'MeloTTS Korean' },
          { value: 'melo_es', label: 'MeloTTS Spanish' },
          { value: 'melo_fr', label: 'MeloTTS French' },
          { value: 'melo_de', label: 'MeloTTS German' },
          { value: 'melo_multi', label: 'MeloTTS Multilingual' }
        ]);
      } else if (provider.id === 'openvoice') {
        setTtsModels([
          { value: 'openvoice_base', label: 'OpenVoice Base' },
          { value: 'openvoice_v2', label: 'OpenVoice v2' }
        ]);
      } else if (provider.id === 'kokoro') {
        setTtsModels([
          { value: 'kokoro_v0_19', label: 'Kokoro v0.19' }
        ]);
      } else if (provider.id === 'moshi') {
        setTtsModels([
          { value: 'moshi-tts-real-time', label: 'Moshi Real-time' }
        ]);
      } else if (provider.id === 'elevenlabs') {
        setTtsModels([
          { value: 'eleven_multilingual_v2', label: 'Multilingual v2' },
          { value: 'eleven_turbo_v2', label: 'Turbo v2' }
        ]);
      } else if (provider.id === 'openai') {
        setTtsModels([
          { value: 'tts-1', label: 'TTS-1' },
          { value: 'tts-1-hd', label: 'TTS-1 HD' }
        ]);
      } else {
        // Default/fallback models
        setTtsModels([
          { value: 'default', label: 'Default Model' }
        ]);
      }
    };

    fetchTtsModels();
  }, [assistant?.tts_provider, ttsProviders]);

  // Fetch available languages for the selected TTS provider
  useEffect(() => {
    const fetchLanguages = async () => {
      if (!assistant?.tts_provider || !ttsProviders[assistant.tts_provider]) {
        setAvailableLanguages([]);
        return;
      }

      const provider = ttsProviders[assistant.tts_provider];

      // Get languages based on provider and its language list
      if (provider.languageList && provider.languageList.length > 0) {
        const languages = provider.languageList.map(lang => {
          // Map language codes to readable labels
          const languageMap: Record<string, string> = {
            'en': 'English',
            'EN': 'English',
            'es': 'Spanish',
            'ES': 'Spanish',
            'fr': 'French',
            'FR': 'French',
            'de': 'German',
            'DE': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'pl': 'Polish',
            'tr': 'Turkish',
            'ru': 'Russian',
            'nl': 'Dutch',
            'cs': 'Czech',
            'ar': 'Arabic',
            'zh': 'Chinese',
            'zh-cn': 'Chinese (Simplified)',
            'ZH': 'Chinese',
            'hu': 'Hungarian',
            'ko': 'Korean',
            'KR': 'Korean',
            'ja': 'Japanese',
            'JP': 'Japanese',
            'hi': 'Hindi',
            'tw': 'Twi/Akan',
            'ee': 'Ewe',
            'gaa': 'Ga',
            'yo': 'Yoruba',
            'ha': 'Hausa',
            'ig': 'Igbo',
            'sw': 'Swahili',
            'multi': 'Multi-language'
          };

          return {
            value: lang.toLowerCase(),
            label: languageMap[lang] || lang
          };
        });

        // Add multi-language option for providers that support multiple languages
        if (provider.capabilities?.multiLanguage && !languages.find(l => l.value === 'multi')) {
          languages.unshift({ value: 'multi', label: 'Multi-language' });
        }

        setAvailableLanguages(languages);
      } else if (provider.id === 'akan_mms' || provider.id === 'meta_mms') {
        // Special handling for Meta MMS providers (Ghanaian languages)
        setAvailableLanguages([
          { value: 'multi', label: 'Multi-language' },
          { value: 'tw', label: 'Twi/Akan' },
          { value: 'ee', label: 'Ewe' },
          { value: 'gaa', label: 'Ga' },
          { value: 'dag', label: 'Dagbani' },
          { value: 'yo', label: 'Yoruba' },
          { value: 'ha', label: 'Hausa' },
          { value: 'ig', label: 'Igbo' },
          { value: 'sw', label: 'Swahili' },
          { value: 'en', label: 'English' }
        ]);
      } else {
        // Default languages for providers without specific language lists
        setAvailableLanguages([
          { value: 'multi', label: 'Multi-language' },
          { value: 'en', label: 'English' }
        ]);
      }
    };

    fetchLanguages();
  }, [assistant?.tts_provider, assistant?.tts_model, ttsProviders]);

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (previewAudio) {
        previewAudio.pause();
        previewAudio.currentTime = 0;
      }
    };
  }, [previewAudio]);

  const configTabs = [
    { id: 'llm' as const, label: 'LLM', icon: MessageSquare },
    { id: 'voice' as const, label: 'Voice', icon: Volume2 },
    { id: 'transcriber' as const, label: 'Transcriber', icon: Mic },
    { id: 'reference-audio' as const, label: 'Reference Audio', icon: Upload },
    { id: 'analytics' as const, label: 'Analytics', icon: BarChart3 },
    { id: 'testing' as const, label: 'Testing', icon: Phone }
  ];

  const renderTabContent = () => {
    if (!assistant) {
      return (
        <div className="text-center py-12">
          <Settings className="w-12 h-12 mx-auto mb-4 text-gray-600/50" />
          <div className="text-gray-600">Select an assistant to configure</div>
        </div>
      );
    }

    switch (activeTab) {
      case 'llm':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">Assistant Settings</h3>

              <div className="space-y-3 sm:space-y-4 mb-6">
                <div>
                  <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">Assistant Name</label>
                  <input
                    type="text"
                    value={assistant.name || ''}
                    onChange={(e) => onConfigurationChange({ name: e.target.value })}
                    placeholder="Enter assistant name"
                    className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">Description</label>
                  <textarea
                    value={assistant.description || ''}
                    onChange={(e) => onConfigurationChange({ description: e.target.value })}
                    placeholder="Describe what this assistant does"
                    rows={2}
                    className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  />
                </div>
              </div>

              <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">Language Model Configuration</h3>

              {/* Shared LLM Model Selector */}
              <div className="space-y-3 sm:space-y-4">
                <LLMModelSelector
                  models={llmModels}
                  selectedModelId={assistant.llm_model || null}
                  onSelectModel={(modelId) => {
                    // Extract provider from model ID (format: provider_model)
                    const provider = modelId.split('_')[0] || modelId;
                    onConfigurationChange({
                      llm_provider: provider,
                      llm_model: modelId
                    });
                  }}
                  isLoading={isLoadingLLMProviders}
                  disabled={false}
                  groupByProvider={true}
                  className="mb-4"
                />

                <div>
                  <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">System Prompt</label>
                  <textarea 
                    value={assistant.system_prompt}
                    onChange={(e) => onConfigurationChange({ system_prompt: e.target.value })}
                    className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    rows={4}
                    placeholder="Define how the assistant should behave..."
                  />
                </div>

                <div>
                  <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">First Message Mode</label>
                  <select
                    value={assistant.first_message_mode || 'assistant_speaks_first'}
                    onChange={(e) => onConfigurationChange({ first_message_mode: e.target.value })}
                    className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="assistant_speaks_first">Assistant speaks first</option>
                    <option value="assistant_waits">Assistant waits for user</option>
                    <option value="assistant_speaks_first_with_model_message">Assistant speaks first with model-generated message</option>
                  </select>
                  <p className="text-xs text-gray-600 mt-1">
                    Choose how the conversation begins: with a predefined message, waiting for user input, or with an AI-generated greeting.
                  </p>
                </div>

                <div>
                  <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">First Message</label>
                  <input
                    type="text"
                    value={assistant.first_message}
                    onChange={(e) => onConfigurationChange({ first_message: e.target.value })}
                    className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="How should the assistant greet users?"
                    disabled={assistant.first_message_mode === 'assistant_speaks_first_with_model_message'}
                  />
                  <p className="text-xs text-gray-600 mt-1">
                    {assistant.first_message_mode === 'assistant_speaks_first_with_model_message'
                      ? 'The AI will generate a greeting based on the system prompt'
                      : 'The predefined message the assistant will use to start the conversation'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 'voice':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">Voice Configuration</h3>

              <div className="space-y-3 sm:space-y-4">
                {/* Comprehensive TTS Selector */}
                <ComprehensiveTTSSelector
                  providers={comprehensiveTTSProviders}
                  selectedProviderId={assistant.tts_provider}
                  onSelectProvider={(providerId) => {
                    // Auto-select appropriate language based on provider
                    const selectedProvider = comprehensiveTTSProviders.find(p => p.id === providerId);
                    let defaultLanguage = 'en'; // Default to English, not 'multi'

                    if (selectedProvider) {
                      if (selectedProvider.languages) {
                        const langs = Object.keys(selectedProvider.languages);
                        if (langs.includes('tw')) {
                          defaultLanguage = 'tw';
                        } else if (langs.length === 1) {
                          defaultLanguage = langs[0];
                        } else if (langs.includes('en')) {
                          defaultLanguage = 'en';
                        } else {
                          // Pick the first available language
                          defaultLanguage = langs[0];
                        }
                      }
                    }
                    onConfigurationChange({
                      tts_provider: providerId,
                      language: defaultLanguage,
                      tts_voice: undefined  // Clear voice when provider changes to avoid incompatibility
                    });
                  }}
                  selectedModel={assistant.tts_model}
                  onSelectModel={(model) => {
                    let updateData: any = { tts_model: model };
                    // Auto-adjust language based on specific models
                    if (model === 'meta_tts_aka' || model === 'xtts_twi_v1') {
                      updateData.language = 'tw';
                    } else if (model.includes('_en')) {
                      updateData.language = 'en';
                    } else if (model.includes('_zh') || model.includes('chinese')) {
                      updateData.language = 'zh';
                    } else if (model.includes('_es') || model.includes('spanish')) {
                      updateData.language = 'es';
                    }
                    onConfigurationChange(updateData);
                  }}
                  selectedVoice={assistant.tts_voice}
                  onSelectVoice={(voice) => onConfigurationChange({ tts_voice: voice })}
                  selectedLanguage={assistant.language}
                  onSelectLanguage={(language) => onConfigurationChange({ language })}
                  speed={assistant.speed}
                  onSpeedChange={(speed) => onConfigurationChange({ speed })}
                  pitch={assistant.pitch}
                  onPitchChange={(pitch) => onConfigurationChange({ pitch })}
                  showAdvanced={true}
                  showOnlineOnly={false}
                  isLoading={loadingComprehensiveTTS}
                  onPreview={handlePreviewVoice}
                  previewLoading={previewLoading}
                />

                {/* Country selection - keep this separate */}
                <div>
                  <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">Country</label>
                  <select
                    value={assistant.country}
                    onChange={(e) => onConfigurationChange({ country: e.target.value })}
                    className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="Ghana">Ghana</option>
                    <option value="Nigeria">Nigeria</option>
                    <option value="Kenya">Kenya</option>
                    <option value="US">United States</option>
                  </select>
                </div>

                {/* Voice Description for Parler-TTS - keep this for backward compatibility */}
                <div>
                  <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">Voice Description (Parler-TTS)</label>
                  <select
                    value={assistant.voice_description || "A clear, friendly voice with natural intonation"}
                    onChange={(e) => onConfigurationChange({ voice_description: e.target.value })}
                    className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="A clear, friendly voice with natural intonation">Default (Clear & Friendly)</option>
                    <option value="A clear, neutral voice">Neutral</option>
                    <option value="A friendly female voice with a warm tone">Friendly Female</option>
                    <option value="A professional male voice with clear pronunciation">Professional Male</option>
                    <option value="An enthusiastic, energetic voice">Enthusiastic</option>
                    <option value="A calm, soothing voice">Calm & Soothing</option>
                    <option value="A quick-paced voice">Fast-paced</option>
                    <option value="A slow, deliberate voice">Slow & Deliberate</option>
                  </select>
                  <p className="text-xs text-gray-600 mt-1">
                    Voice style for Parler-TTS (used when speed = 1.0). Describes voice characteristics in natural language.
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 'transcriber':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">Speech Recognition Configuration</h3>

              <div className="space-y-3 sm:space-y-4">
                {/* Shared ASR Provider Selector */}
                <ASRProviderSelector
                  providers={asrProvidersArray}
                  selectedProviderId={normalizeAsrProviderId(assistant.stt_provider)}
                  onSelectProvider={(providerId) => {
                    const availableModels = sttModelsByProvider[providerId] || [];
                    // Reset model to first available option when provider changes
                    const firstModel = availableModels[0]?.value || '';
                    onConfigurationChange({
                      stt_provider: providerId,
                      stt_model: firstModel
                    });
                  }}
                  isLoading={isLoadingASRProviders}
                  disabled={false}
                  showOnlineOnly={false}
                  className="mb-4"
                />

                <div>
                  <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">Model</label>
                  <select
                    value={assistant.stt_model}
                    onChange={(e) => onConfigurationChange({ stt_model: e.target.value })}
                    className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    {(sttModelsByProvider[normalizeAsrProviderId(assistant.stt_provider)] || []).map(model => (
                      <option key={model.value} value={model.value}>
                        {model.badge ? `${model.badge} ${model.label}` : model.label}
                      </option>
                    ))}
                  </select>
                  {(() => {
                    const selectedModel = (sttModelsByProvider[normalizeAsrProviderId(assistant.stt_provider)] || []).find(m => m.value === assistant.stt_model);
                    return selectedModel?.description ? (
                      <p className="text-xs text-gray-600 mt-1">{selectedModel.description}</p>
                    ) : null;
                  })()}
                </div>

                <div>
                  <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">Transcription Language</label>
                  <select
                    value={assistant.stt_language || assistant.language || 'auto'}
                    onChange={(e) => onConfigurationChange({ stt_language: e.target.value })}
                    className="w-full px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="auto">Auto-detect</option>
                    <option value="tw">Twi/Akan</option>
                    <option value="en">English</option>
                    <option value="ee">Ewe</option>
                    <option value="gaa">Ga</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="zh">Chinese</option>
                    <option value="ja">Japanese</option>
                    <option value="ko">Korean</option>
                    <option value="ar">Arabic</option>
                    <option value="hi">Hindi</option>
                    <option value="multi">Multi-language</option>
                  </select>
                  <p className="text-xs text-gray-600 mt-1">
                    Select the primary language for transcription or use auto-detect
                  </p>
                </div>

                <div className="bg-muted/50 p-3 sm:p-4 rounded-lg">
                  <h4 className="text-sm sm:text-base font-medium mb-1 sm:mb-2">Provider Information</h4>
                  <div className="text-xs sm:text-sm text-gray-600">
                    {assistant.stt_provider && asrProviders[normalizeAsrProviderId(assistant.stt_provider)] ? (
                      <>
                        <p className="mb-2">
                          <strong>Endpoint:</strong> {asrProviders[normalizeAsrProviderId(assistant.stt_provider)].endpoint || 'N/A'}
                        </p>
                        {asrProviders[normalizeAsrProviderId(assistant.stt_provider)].error_message && (
                          <p className="mb-2 text-red-600">
                            <strong>Error:</strong> {asrProviders[normalizeAsrProviderId(assistant.stt_provider)].error_message}
                          </p>
                        )}
                        <p>Language support varies by provider:</p>
                        <ul className="list-disc list-inside mt-1 space-y-1">
                          {normalizeAsrProviderId(assistant.stt_provider) === 'meta_mms' && (
                            <>
                              <li>1000+ languages supported</li>
                              <li>Specialized for Akan/Twi, Ewe</li>
                            </>
                          )}
                          {normalizeAsrProviderId(assistant.stt_provider) === 'whisper' && (
                            <>
                              <li>99+ languages supported</li>
                              <li>GiftMark Akan model (92.9% accuracy)</li>
                              <li>Multiple model sizes available</li>
                              <li>Faster Whisper optimizations</li>
                            </>
                          )}
                          {(normalizeAsrProviderId(assistant.stt_provider) === 'openai' ||
                            normalizeAsrProviderId(assistant.stt_provider) === 'google' ||
                            normalizeAsrProviderId(assistant.stt_provider) === 'deepgram') && (
                            <>
                              <li>Cloud-based service</li>
                              <li>Multiple language support</li>
                              <li>Requires API credentials</li>
                            </>
                          )}
                        </ul>
                      </>
                    ) : (
                      <>
                        <p>Select an ASR provider to see language support information.</p>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'analytics':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">Voice Agent Analytics</h3>
              <p className="text-xs sm:text-sm text-gray-600 mb-4">
                View call performance, costs, and integration usage for this voice agent.
              </p>

              {/* Render VapiAnalyticsDashboard */}
              {assistant && assistant.id ? (
                <VapiAnalyticsDashboard
                  agentId={assistant.id}
                  tenantId="default"
                  apiBaseUrl={API_BASE_URL}
                />
              ) : (
                <div className="text-center py-12 text-gray-600">
                  No agent selected for analytics
                </div>
              )}
            </div>
          </div>
        );

      case 'testing':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">Testing & Validation</h3>
              
              {/* LLM Chat Test Panel */}
              <div className="mb-6">
                <h4 className="text-sm font-medium mb-2">Test LLM Chat</h4>
                <p className="text-xs text-gray-600 mb-3">
                  Test the language model with a chat interface to verify responses and behavior.
                </p>
                <LLMChatTestPanel
                  apiBaseUrl={API_BASE_URL}
                  getAuthToken={async () => {
                    const headers = await getAuthHeaders();
                    return headers.Authorization?.replace('Bearer ', '') || '';
                  }}
                  selectedModel={assistant.llm_model}
                  systemPrompt={assistant.system_prompt}
                  temperature={0.7}
                  className="border border-border rounded-lg p-4"
                />
              </div>

              {/* ASR Streaming Test Panel */}
              <div className="mb-6">
                <h4 className="text-sm font-medium mb-2">Test Speech Recognition</h4>
                <p className="text-xs text-gray-600 mb-3">
                  Test the speech recognition provider with real-time streaming or file-based transcription.
                </p>
                <ASRStreamingTestPanel
                  apiBaseUrl={API_BASE_URL}
                  wsBaseUrl={WS_BASE_URL}
                  getAuthToken={async () => {
                    const headers = await getAuthHeaders();
                    return headers.Authorization?.replace('Bearer ', '') || '';
                  }}
                  selectedProvider={normalizeAsrProviderId(assistant.stt_provider)}
                  language={assistant.stt_language || assistant.language || 'en'}
                  defaultMode="realtime"
                  className="border border-border rounded-lg p-4"
                />
              </div>

              {/* Phone Testing Panel */}
              <div className="mb-6">
                <h4 className="text-sm font-medium mb-2">Phone Testing</h4>
                <p className="text-xs text-gray-600 mb-3">
                  Generate temporary test phone numbers and shareable links to test this assistant.
                </p>
                {assistant && assistant.id ? (
                  <PhoneTestingPanel
                    assistantId={assistant.id}
                    assistantName={assistant.name}
                  />
                ) : (
                  <div className="text-center py-8 text-muted-foreground border border-border rounded-lg">
                    No assistant selected for phone testing
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 'reference-audio':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">Reference Audio</h3>
              <p className="text-xs sm:text-sm text-gray-600 mb-4">
                Upload and manage reference audio files for zero-shot voice cloning. These can be used with providers like StyleTTS2, Coqui XTTS, OpenVoice, and F5-TTS.
              </p>

              {/* Render Reference Audio List */}
              <ReferenceAudioList
                apiBaseUrl={API_BASE_URL}
                getAuthHeaders={getAuthHeaders}
              />
            </div>
          </div>
        );

      default:
        return (
          <div className="text-center py-12">
            <div className="text-gray-600">Configuration for {activeTab} coming soon...</div>
          </div>
        );
    }
  };

  return (
    <div className="flex-1 bg-background p-3 sm:p-4 lg:p-6 overflow-y-auto">
      {/* Configuration Tabs */}
      <div className="flex space-x-1 mb-3 sm:mb-6 bg-muted p-1 rounded-lg overflow-x-auto">
        {configTabs.map((tab) => (
          <button
            key={tab.id}
            className={`flex items-center space-x-1 sm:space-x-2 px-2 sm:px-4 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-background text-foreground shadow-sm'
                : 'text-gray-600 hover:text-foreground'
            }`}
            onClick={() => setActiveTab(tab.id)}
          >
            <tab.icon className="w-3 h-3 sm:w-4 sm:h-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="w-full max-w-2xl">
        {renderTabContent()}
      </div>

      {/* Publish Button */}
      {assistant && (
        <div className="mt-4 sm:mt-8 pt-4 sm:pt-6 border-t border-border">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0">
            <div className="text-sm text-gray-600">
              Last updated: {new Date(assistant.updated_at).toLocaleString()}
            </div>
            <button
              onClick={onPublish}
              className="bg-indigo-600 hover:bg-primary/90 text-primary-foreground px-4 sm:px-6 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-colors w-full sm:w-auto"
            >
              Publish Changes
            </button>
          </div>
        </div>
      )}
    </div>
  );
};