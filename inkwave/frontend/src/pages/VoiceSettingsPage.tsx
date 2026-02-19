/**
 * VoiceSettingsPage
 * Voice preferences configuration for TTS, ASR, and LLM
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Mic, Volume2, Brain, Star, Save, RotateCcw, CheckCircle, MessageSquare } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { API_BASE_URL, CORE_API_URL, WS_BASE_URL, INKWAVE_API_URL } from '../config/api-config';
import { VoiceGallery } from '../components/voice-library';
import { useVoiceLibrary } from '../hooks/useVoiceLibrary';
import { ReferenceAudioList } from '../../../../shared/frontend/components/reference-audio';
import { ComprehensiveTTSSelector } from '../../../../shared/frontend/components/voice-settings/ComprehensiveTTSSelector';
import { useComprehensiveTTS } from '../../../../shared/frontend/hooks/useComprehensiveTTS';
import { VoiceTestingPanel } from '../../../../shared/frontend/components/VoiceTestingPanel';
import { LLMChatTestPanel } from '../../../../shared/frontend/components/voice-settings/LLMChatTestPanel';
import { ASRStreamingTestPanel } from '../../../../shared/frontend/components/voice-settings/ASRStreamingTestPanel';
import { getAuthHeaders, getAuthToken } from '../lib/auth-utils';

interface VoiceSettings {
  user_id: string;
  organization_id: string;
  tts: {
    default_provider: string;
    default_voice: string | null;
    speed: number;
    pitch: number;
  };
  asr: {
    default_provider: string;
    language: string;
    task: string;
  };
  llm: {
    default_model: string;
    temperature: number;
    max_tokens: number;
  };
  voices: {
    favorite_voices: string[];
    custom_voices: string[];
  };
}

export default function VoiceSettingsPage() {
	useEffect(() => {
		document.title = 'Voice Settings - InkWave';
	}, []);

  const [settings, setSettings] = useState<VoiceSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [activeTab, setActiveTab] = useState<'tts' | 'asr' | 'llm' | 'voices' | 'reference-audio' | 'test'>('tts');
  const { addToFavorites, removeFromFavorites, getFavorites } = useVoiceLibrary();
  const [favoriteVoices, setFavoriteVoices] = useState<string[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewAudio, setPreviewAudio] = useState<HTMLAudioElement | null>(null);

  // ASR providers state
  const [asrProviders, setAsrProviders] = useState<Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
    status: string;
    languages?: number;
    metadata?: Record<string, any>;
  }>>([]);
  const [loadingASRProviders, setLoadingASRProviders] = useState(false);

  // LLM providers state
  const [llmProviders, setLlmProviders] = useState<Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
    status: string;
    languages?: number;
    languageList?: string[];
    capabilities?: Record<string, any>;
    metadata?: Record<string, any>;
  }>>([]);
  const [loadingLLMProviders, setLoadingLLMProviders] = useState(false);

  // Use comprehensive TTS hook for provider selection
  const {
    providers: comprehensiveTTSProviders,
    loading: loadingComprehensiveTTS,
    error: comprehensiveTTSError
  } = useComprehensiveTTS(API_BASE_URL, undefined, {
    onlineOnly: false,
    autoFetch: true,
    endpointPath: '/api/tts/providers',
    skipWalletBalance: true,
    getAuthHeaders
  });

  // Handle voice preview
  const handlePreviewVoice = async (previewText: string) => {
    if (!settings?.tts.default_provider) {
      toast.error('Please select a TTS provider first');
      return;
    }

    // Stop any currently playing audio
    if (previewAudio) {
      previewAudio.pause();
      previewAudio.currentTime = 0;
    }

    setPreviewLoading(true);

    try {
      // Use unified TTS API - accepts both field name formats (provider_id/provider, voice_id/speaker)
      const synthesisRequest = {
        provider_id: settings.tts.default_provider,
        text: previewText,
        language: 'en',
        voice_id: settings.tts.default_voice || undefined,
        speed: settings.tts.speed || 1.0,
        pitch: settings.tts.pitch || 0.0,
        output_format: 'wav'
      };

      const authHeaders = await getAuthHeaders();

      // Use preview endpoint (no billing required)
      const response = await fetch(`${API_BASE_URL}/api/tts/preview`, {
        method: 'POST',
        headers: {
          ...authHeaders,
          'Content-Type': 'application/json',
        },
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
        toast.success(`Voice preview played • ${data.provider_id}`);
      } else {
        throw new Error('No audio data returned from TTS service');
      }
    } catch (error: any) {
      console.error('TTS preview failed:', error);
      toast.error(error.message || 'Preview failed');
    } finally {
      setPreviewLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
    loadFavorites();
    loadProviders();
  }, []);

  const loadProviders = async () => {
    try {
      setLoadingASRProviders(true);
      setLoadingLLMProviders(true);
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/v1/voice-settings/providers`, {
        headers: authHeaders,
      });

      if (!response.ok) {
        throw new Error('Failed to load providers');
      }

      const data = await response.json();
      if (data.asr_providers && Array.isArray(data.asr_providers)) {
        setAsrProviders(data.asr_providers);
      }
      if (data.llm_providers && Array.isArray(data.llm_providers)) {
        setLlmProviders(data.llm_providers);
      }
    } catch (error) {
      console.error('Failed to load providers:', error);
    } finally {
      setLoadingASRProviders(false);
      setLoadingLLMProviders(false);
    }
  };

  const loadFavorites = async () => {
    try {
      const favorites = await getFavorites();
      setFavoriteVoices(favorites.map((v: any) => v.voice_id));
    } catch (error) {
      console.error('Failed to load favorite voices:', error);
    }
  };

  const loadSettings = async () => {
    try {
      setIsLoading(true);
      const response = await api.voiceSettings.getMySettings();
      const data = response.data;
      // Set default providers if not already set (for better UX)
      const settingsWithDefaults = {
        ...data,
        tts: {
          ...data.tts,
          default_provider: data.tts.default_provider || 'coqui_tts',
        },
        asr: {
          ...data.asr,
          default_provider: data.asr.default_provider || 'faster_whisper_large',
          language: data.asr.language || 'en',
        },
        llm: {
          ...data.llm,
          default_model: data.llm.default_model || 'gemini-2.5-flash',
          temperature: data.llm.temperature ?? 0.7,
          max_tokens: data.llm.max_tokens ?? 1000,
        },
      };
      setSettings(settingsWithDefaults);
      setIsDirty(false);
    } catch (error: any) {
      console.error('Failed to load voice settings:', error);
      toast.error(error.response?.data?.detail || 'Failed to load voice settings');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings || !isDirty) return;

    try {
      setIsSaving(true);
      await api.voiceSettings.updateMySettings({
        tts: settings.tts,
        asr: settings.asr,
        llm: settings.llm,
        voices: settings.voices,
      });
      toast.success('Voice settings saved successfully');
      setIsDirty(false);
    } catch (error: any) {
      console.error('Failed to save voice settings:', error);
      toast.error(error.response?.data?.detail || 'Failed to save voice settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (window.confirm('Are you sure you want to reset your changes?')) {
      loadSettings();
    }
  };

  const updateSettings = (updates: Partial<VoiceSettings>) => {
    if (!settings) return;
    setSettings({ ...settings, ...updates });
    setIsDirty(true);
  };

  const handleFavoriteToggle = async (voiceId: string, isFavorite: boolean) => {
    try {
      if (isFavorite) {
        await removeFromFavorites(voiceId);
        setFavoriteVoices(prev => prev.filter(id => id !== voiceId));
        toast.success('Removed from favorites');
      } else {
        await addToFavorites(voiceId);
        setFavoriteVoices(prev => [...prev, voiceId]);
        toast.success('Added to favorites');
      }
    } catch (error) {
      toast.error('Failed to update favorites');
    }
  };

  const tabs = [
    { id: 'tts' as const, label: 'Text-to-Speech', icon: Volume2, color: 'purple' },
    { id: 'asr' as const, label: 'Speech Recognition', icon: Mic, color: 'blue' },
    { id: 'llm' as const, label: 'Language Model', icon: Brain, color: 'green' },
    { id: 'voices' as const, label: 'Voice Library', icon: Star, color: 'pink' },
    { id: 'reference-audio' as const, label: 'Reference Audio', icon: Volume2, color: 'purple' },
    { id: 'test' as const, label: 'Test Conversation', icon: MessageSquare, color: 'cyan' },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading voice settings...</p>
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-950">
        <div className="text-center">
          <p className="text-gray-400">Failed to load voice settings</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-gray-950 py-12 px-4"
    >
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Voice Settings</h1>
            <p className="text-gray-400">Configure your voice preferences for TTS, ASR, and LLM</p>
          </div>
        </div>

        {/* Dirty Indicator */}
        {isDirty && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4"
          >
            <p className="text-yellow-400 text-sm">
              ⚠️ You have unsaved changes
            </p>
          </motion.div>
        )}

        {/* Tabs */}
        <div className="bg-gray-800/50 rounded-xl border border-gray-700/50">
          <div className="flex space-x-1 p-2 border-b border-gray-700/50">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-3 rounded-lg transition ${
                    activeTab === tab.id
                      ? `bg-${tab.color}-500/20 text-${tab.color}-400`
                      : 'text-gray-400 hover:text-gray-300 hover:bg-gray-700/50'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {/* TTS Tab */}
            {activeTab === 'tts' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-semibold text-white mb-1">Text-to-Speech Settings</h2>
                    <p className="text-gray-400 text-sm">
                      Choose your preferred TTS provider and voice for audiobook narration
                    </p>
                  </div>
                </div>

                {/* Comprehensive TTS Selector */}
                <ComprehensiveTTSSelector
                  providers={comprehensiveTTSProviders}
                  selectedProviderId={settings.tts.default_provider}
                  onSelectProvider={(providerId) => {
                    updateSettings({
                      tts: { ...settings.tts, default_provider: providerId }
                    });
                  }}
                  selectedVoice={settings.tts.default_voice || undefined}
                  onSelectVoice={(voice) => {
                    updateSettings({
                      tts: { ...settings.tts, default_voice: voice }
                    });
                  }}
                  speed={settings.tts.speed}
                  onSpeedChange={(speed) => {
                    updateSettings({
                      tts: { ...settings.tts, speed }
                    });
                  }}
                  pitch={settings.tts.pitch}
                  onPitchChange={(pitch) => {
                    updateSettings({
                      tts: { ...settings.tts, pitch }
                    });
                  }}
                  showAdvanced={true}
                  showOnlineOnly={false}
                  isLoading={loadingComprehensiveTTS}
                  onPreview={handlePreviewVoice}
                  previewLoading={previewLoading}
                  variant="dark"
                />

                {comprehensiveTTSError && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                    <p className="text-red-400 text-sm">
                      ⚠️ Error loading TTS providers: {comprehensiveTTSError}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* ASR Tab */}
            {activeTab === 'asr' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-white mb-4">Speech Recognition Settings</h2>

                {/* ASR Provider Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    ASR Provider
                  </label>
                  <p className="text-sm text-gray-500 mb-4">
                    Choose your preferred speech recognition provider for audiobook transcription.
                  </p>
                  {loadingASRProviders ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                      <span className="ml-3 text-gray-400">Loading providers...</span>
                    </div>
                  ) : asrProviders.length === 0 ? (
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                      <p className="text-sm text-yellow-400">
                        No ASR providers available. Please check your configuration.
                      </p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {asrProviders.map((provider) => {
                        const isSelected = settings.asr.default_provider === provider.id;
                        return (
                          <button
                            key={provider.id}
                            onClick={() => updateSettings({
                              asr: { ...settings.asr, default_provider: provider.id }
                            })}
                            className={`relative flex items-start p-4 rounded-xl border-2 transition-all text-left ${
                              isSelected
                                ? 'border-blue-500 bg-blue-500/10 ring-2 ring-blue-500/30'
                                : 'border-gray-700 hover:border-gray-600 hover:bg-gray-700/50'
                            }`}
                          >
                            {isSelected && (
                              <div className="absolute top-2 right-2">
                                <CheckCircle className="w-5 h-5 text-blue-400" />
                              </div>
                            )}
                            <div className="flex-shrink-0 text-2xl mr-3">
                              {provider.icon || '🎤'}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-white">
                                {provider.name}
                              </div>
                              <div className="text-sm text-gray-400 mt-1 line-clamp-2">
                                {provider.description}
                              </div>
                              {provider.metadata && (
                                <div className="flex flex-wrap gap-2 mt-2">
                                  {provider.metadata.latency && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-500/20 text-green-400">
                                      {provider.metadata.latency}
                                    </span>
                                  )}
                                  {provider.metadata.cost_per_hour && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-500/20 text-blue-400">
                                      {provider.metadata.cost_per_hour}/hr
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Language Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Language
                  </label>
                  <select
                    value={settings.asr.language}
                    onChange={(e) => updateSettings({
                      asr: { ...settings.asr, language: e.target.value }
                    })}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="it">Italian</option>
                    <option value="pt">Portuguese</option>
                    <option value="zh">Chinese</option>
                    <option value="ja">Japanese</option>
                    <option value="ko">Korean</option>
                    <option value="ar">Arabic</option>
                    <option value="hi">Hindi</option>
                    <option value="ru">Russian</option>
                    <option value="tw">Twi (Akan)</option>
                  </select>
                </div>

                {/* Task Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Task
                  </label>
                  <select
                    value={settings.asr.task}
                    onChange={(e) => updateSettings({
                      asr: { ...settings.asr, task: e.target.value }
                    })}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="transcribe">Transcribe (same language)</option>
                    <option value="translate">Translate to English</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Translation is available with Groq Whisper Large v3 and OpenAI Whisper.
                  </p>
                </div>

                {/* Current Selection Summary */}
                {settings.asr.default_provider && (
                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                    <h4 className="text-sm font-medium text-gray-300 mb-2">Current Selection</h4>
                    <div className="flex items-center gap-2">
                      <span className="text-lg">
                        {asrProviders.find(p => p.id === settings.asr.default_provider)?.icon || '🎤'}
                      </span>
                      <span className="font-medium text-white">
                        {asrProviders.find(p => p.id === settings.asr.default_provider)?.name || settings.asr.default_provider}
                      </span>
                    </div>
                  </div>
                )}

                {/* ASR Test Panel */}
                <div className="mt-6 pt-6 border-t border-gray-700">
                  <h4 className="text-sm font-medium text-gray-300 mb-4">Test Speech Recognition</h4>
                  <ASRStreamingTestPanel
                    apiBaseUrl={API_BASE_URL}
                    wsBaseUrl={WS_BASE_URL}
                    getAuthToken={getAuthToken}
                    selectedProvider={settings.asr.default_provider}
                    language={settings.asr.language}
                    defaultMode="realtime"
                    disabled={!settings.asr.default_provider}
                    disabledReason="Select an ASR provider to test speech recognition"
                    languages={[
                      { code: 'en', name: 'English', flag: '🇬🇧' },
                      { code: 'tw', name: 'Twi', flag: '🇬🇭' },
                      { code: 'yo', name: 'Yoruba', flag: '🇳🇬' },
                      { code: 'es', name: 'Spanish', flag: '🇪🇸' },
                      { code: 'fr', name: 'French', flag: '🇫🇷' },
                    ]}
                  />
                </div>
              </div>
            )}

            {/* LLM Tab */}
            {activeTab === 'llm' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-white mb-4">Language Model Settings</h2>

                {/* LLM Provider Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    LLM Provider
                  </label>
                  <p className="text-sm text-gray-500 mb-4">
                    Choose your preferred language model for AI-powered audiobook features.
                  </p>
                  {loadingLLMProviders ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
                      <span className="ml-3 text-gray-400">Loading providers...</span>
                    </div>
                  ) : llmProviders.length === 0 ? (
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                      <p className="text-sm text-yellow-400">
                        No LLM providers available. Please check your configuration.
                      </p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {llmProviders.map((provider) => {
                        const isSelected = settings.llm.default_model === provider.id;
                        return (
                          <button
                            key={provider.id}
                            onClick={() => updateSettings({
                              llm: { ...settings.llm, default_model: provider.id }
                            })}
                            className={`relative flex items-start p-4 rounded-xl border-2 transition-all text-left ${
                              isSelected
                                ? 'border-green-500 bg-green-500/10 ring-2 ring-green-500/30'
                                : 'border-gray-700 hover:border-gray-600 hover:bg-gray-700/50'
                            }`}
                          >
                            {isSelected && (
                              <div className="absolute top-2 right-2">
                                <CheckCircle className="w-5 h-5 text-green-400" />
                              </div>
                            )}
                            <div className="flex-shrink-0 text-2xl mr-3">
                              {provider.icon || '🤖'}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-white">
                                {provider.name}
                              </div>
                              <div className="text-sm text-gray-400 mt-1 line-clamp-2">
                                {provider.description}
                              </div>
                              {provider.metadata && (
                                <div className="flex flex-wrap gap-2 mt-2">
                                  {provider.metadata.contextWindow && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-500/20 text-purple-400">
                                      {(provider.metadata.contextWindow / 1000).toFixed(0)}K context
                                    </span>
                                  )}
                                  {provider.metadata.pricing?.inputPer1kTokens !== undefined && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-500/20 text-green-400">
                                      {provider.metadata.pricing.inputPer1kTokens === 0 ? 'Free' : `$${provider.metadata.pricing.inputPer1kTokens}/1K`}
                                    </span>
                                  )}
                                  {provider.capabilities?.streaming && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-500/20 text-blue-400">
                                      Streaming
                                    </span>
                                  )}
                                  {provider.capabilities?.functionCalling && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-500/20 text-orange-400">
                                      Functions
                                    </span>
                                  )}
                                </div>
                              )}
                              {provider.languageList && provider.languageList.length > 0 && (
                                <div className="text-xs text-gray-500 mt-1">
                                  Languages: {provider.languageList.slice(0, 5).join(', ')}{provider.languageList.length > 5 ? ` +${provider.languageList.length - 5} more` : ''}
                                </div>
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Current Selection Summary */}
                {settings.llm.default_model && (
                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                    <h4 className="text-sm font-medium text-gray-300 mb-2">Current Selection</h4>
                    <div className="flex items-center gap-2">
                      <span className="text-lg">
                        {llmProviders.find(p => p.id === settings.llm.default_model)?.icon || '🤖'}
                      </span>
                      <span className="font-medium text-white">
                        {llmProviders.find(p => p.id === settings.llm.default_model)?.name || settings.llm.default_model}
                      </span>
                    </div>
                  </div>
                )}

                {/* Temperature Setting */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Temperature: {settings.llm.temperature.toFixed(2)}
                  </label>
                  <input
                    type="range"
                    min="0.0"
                    max="2.0"
                    step="0.1"
                    value={settings.llm.temperature}
                    onChange={(e) => updateSettings({
                      llm: { ...settings.llm, temperature: parseFloat(e.target.value) }
                    })}
                    className="w-full accent-green-500"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Focused (0.0)</span>
                    <span>Creative (2.0)</span>
                  </div>
                </div>

                {/* Max Tokens Setting */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Max Tokens: {settings.llm.max_tokens.toLocaleString()}
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100000"
                    step="100"
                    value={settings.llm.max_tokens}
                    onChange={(e) => updateSettings({
                      llm: { ...settings.llm, max_tokens: parseInt(e.target.value) }
                    })}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Maximum number of tokens in the response. Higher values allow longer responses but cost more.
                  </p>
                </div>

                {/* LLM Chat Test Panel */}
                <div className="mt-6 pt-6 border-t border-gray-700">
                  <h4 className="text-sm font-medium text-gray-300 mb-4">Test Language Model</h4>
                  <LLMChatTestPanel
                    apiBaseUrl={API_BASE_URL}
                    getAuthToken={getAuthToken}
                    selectedModel={settings.llm.default_model}
                    temperature={settings.llm.temperature}
                    maxTokens={settings.llm.max_tokens}
                    disabled={!settings.llm.default_model}
                    disabledReason="Select an LLM model to test chat"
                  />
                </div>
              </div>
            )}

            {/* Voices Tab */}
            {activeTab === 'voices' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-semibold text-white mb-1">Voice Library</h2>
                    <p className="text-gray-400 text-sm">
                      Browse and manage voices for audiobook narration
                    </p>
                  </div>
                  <div className="text-sm text-gray-400">
                    <Star className="h-4 w-4 inline mr-1 text-pink-400" />
                    {favoriteVoices.length} Favorites
                  </div>
                </div>

                <VoiceGallery
                  onVoiceSelect={(voice) => {
                    // Update default voice in settings
                    updateSettings({
                      tts: { ...settings.tts, default_voice: voice.voice_id }
                    });
                    toast.success(`Selected "${voice.name}" as default narration voice`);
                  }}
                  selectedVoiceId={settings.tts.default_voice || undefined}
                  showFilters={true}
                  showStats={true}
                  showActions={true}
                  defaultLayout="grid"
                  defaultFilters={{
                    categories: ['Narration', 'Audiobook'],
                  }}
                  pageSize={12}
                  onFavoriteToggle={handleFavoriteToggle}
                  favoriteVoiceIds={favoriteVoices}
                />
              </div>
            )}

            {/* Reference Audio Tab */}
            {activeTab === 'reference-audio' && (
              <div className="space-y-6">
                <ReferenceAudioList
                  apiBaseUrl={INKWAVE_API_URL}
                  getAuthHeaders={async () => {
                    const headers = await getAuthHeaders();
                    return headers as Record<string, string>;
                  }}
                  onSelect={(audio) => {
                    toast.success(`Selected "${audio.name}" reference audio`);
                    // Can link to voice settings if needed
                  }}
                  showUpload={true}
                />
              </div>
            )}

            {/* Test Voice Tab */}
            {activeTab === 'test' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-semibold text-white mb-1">Test Voice Conversation</h2>
                    <p className="text-gray-400 text-sm">
                      Test your voice settings with a live AI conversation
                    </p>
                  </div>
                </div>

                {/* Configuration Summary */}
                <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                  <h4 className="text-sm font-medium text-gray-300 mb-3">Current Configuration</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">TTS:</span>{' '}
                      <span className="font-medium text-white">{settings.tts.default_provider || 'Not set'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">ASR:</span>{' '}
                      <span className="font-medium text-white">{settings.asr.default_provider || 'Not set'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">LLM:</span>{' '}
                      <span className="font-medium text-white">{settings.llm.default_model || 'Not set'}</span>
                    </div>
                  </div>
                </div>

                <VoiceTestingPanel
                  assistantId="inkwave-narrator"
                  assistantName="InkWave AI Narrator"
                  apiBaseUrl={CORE_API_URL}
                  wsBaseUrl={WS_BASE_URL}
                  getAuthToken={getAuthToken}
                  assistant={{
                    language: settings.asr.language,
                    llm_provider: settings.llm.default_model,
                    tts_provider: settings.tts.default_provider,
                    stt_provider: settings.asr.default_provider,
                  }}
                  languages={[
                    { code: 'en', name: 'English', flag: '🇬🇧' },
                    { code: 'tw', name: 'Twi', flag: '🇬🇭' },
                    { code: 'yo', name: 'Yoruba', flag: '🇳🇬' },
                    { code: 'es', name: 'Spanish', flag: '🇪🇸' },
                    { code: 'fr', name: 'French', flag: '🇫🇷' },
                    { code: 'de', name: 'German', flag: '🇩🇪' },
                  ]}
                  disabled={!settings.tts.default_provider || !settings.asr.default_provider || !settings.llm.default_model}
                  disabledReason={
                    !settings.tts.default_provider || !settings.asr.default_provider || !settings.llm.default_model
                      ? 'Please configure TTS, ASR, and LLM providers before testing'
                      : undefined
                  }
                />
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons - Bottom */}
        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-700/50">
          <button
            onClick={handleReset}
            disabled={!isDirty || isSaving}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Reset</span>
          </button>
          <button
            onClick={handleSave}
            disabled={!isDirty || isSaving}
            className="flex items-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
          >
            <Save className="h-4 w-4" />
            <span>{isSaving ? 'Saving...' : 'Save Changes'}</span>
          </button>
        </div>
      </div>
    </motion.div>
  );
}
