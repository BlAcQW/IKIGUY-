/**
 * Book Voice Settings Modal
 *
 * Allows users to configure voice settings (TTS, ASR, LLM) for a specific book.
 * These settings persist across all reading sessions for this book.
 * Includes provider/voice selection with audio preview before saving.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { X, Settings, Volume2, Mic, Brain, Save, RotateCcw, Play, Square } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { ComprehensiveTTSSelector } from '../../../../shared/frontend/components/voice-settings/ComprehensiveTTSSelector';
import { useComprehensiveTTS } from '../../../../shared/frontend/hooks/useComprehensiveTTS';
import { API_BASE_URL } from '../config/api-config';
import { getAuthHeaders } from '../lib/auth-utils';

interface BookVoiceSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  bookId: string;
  bookTitle: string;
}

interface BookVoiceSettings {
  tts_provider?: string;
  tts_voice?: string;
  tts_speed?: number;
  tts_pitch?: number;
  asr_provider?: string;
  asr_language?: string;
  asr_task?: string;
  llm_model?: string;
  llm_temperature?: number;
  llm_max_tokens?: number;
}

export default function BookVoiceSettingsModal({
  isOpen,
  onClose,
  bookId,
  bookTitle,
}: BookVoiceSettingsModalProps) {
  const [settings, setSettings] = useState<BookVoiceSettings>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [originalSettings, setOriginalSettings] = useState<BookVoiceSettings>({});

  // Local state for TTS selection - default to kokoro
  const [selectedProvider, setSelectedProvider] = useState<string>('kokoro');
  const [selectedVoice, setSelectedVoice] = useState<string>('');
  const [speed, setSpeed] = useState<number>(1.0);
  const [pitch, setPitch] = useState<number>(0);

  // Local state for ASR selection - default to faster_whisper_medium
  const [asrProvider, setAsrProvider] = useState<string>('faster_whisper_medium');
  const [asrLanguage, setAsrLanguage] = useState<string>('en');

  // Local state for LLM selection
  const [llmModel, setLlmModel] = useState<string>('');
  const [llmTemperature, setLlmTemperature] = useState<number>(0.7);
  const [llmMaxTokens, setLlmMaxTokens] = useState<number>(1000);

  // ASR and LLM providers state
  const [asrProviders, setAsrProviders] = useState<Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
    status: string;
  }>>([]);
  const [llmProviders, setLlmProviders] = useState<Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
    status: string;
  }>>([]);
  const [loadingProviders, setLoadingProviders] = useState(false);

  // Preview state
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewText, setPreviewText] = useState('Hello, this is a preview of the selected voice.');
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // TTS providers hook - must pass apiBaseUrl to avoid relative URL issues
  const {
    providers,
    loading: ttsLoading,
  } = useComprehensiveTTS(API_BASE_URL, undefined, {
    endpointPath: '/api/tts/providers',
  });

  // Get voices for selected provider
  const voices = selectedProvider ? providers.find(p => p.id === selectedProvider)?.speakers || {} : {};

  useEffect(() => {
    if (isOpen && bookId) {
      loadBookSettings();
      loadProviders();
    }
  }, [isOpen, bookId]);

  const loadProviders = async () => {
    try {
      setLoadingProviders(true);
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
        console.log('Loaded ASR providers:', data.asr_providers.map((p: any) => p.id));
      }
      if (data.llm_providers && Array.isArray(data.llm_providers)) {
        setLlmProviders(data.llm_providers);
        console.log('Loaded LLM providers:', data.llm_providers.map((p: any) => p.id));
      }
    } catch (error) {
      console.error('Failed to load providers:', error);
    } finally {
      setLoadingProviders(false);
    }
  };

  const loadBookSettings = async () => {
    try {
      setLoading(true);
      const response = await api.books.getVoiceSettings(bookId);
      const bookSettings = response.data?.voice_settings || {};
      
      setSettings(bookSettings);
      setOriginalSettings(bookSettings);
      setHasChanges(false);

      // Apply to TTS selector if available, otherwise use kokoro default
      if (bookSettings.tts_provider) {
        setSelectedProvider(bookSettings.tts_provider);
      } else {
        setSelectedProvider('kokoro');
      }
      if (bookSettings.tts_voice) {
        setSelectedVoice(bookSettings.tts_voice);
      }
      if (bookSettings.tts_speed !== undefined) {
        setSpeed(bookSettings.tts_speed);
      }
      if (bookSettings.tts_pitch !== undefined) {
        setPitch(bookSettings.tts_pitch);
      }
      
      // Apply ASR settings, default to faster_whisper_medium
      if (bookSettings.asr_provider) {
        setAsrProvider(bookSettings.asr_provider);
      } else {
        setAsrProvider('faster_whisper_medium');
      }
      if (bookSettings.asr_language) {
        setAsrLanguage(bookSettings.asr_language);
      }
      
      // Apply LLM settings
      if (bookSettings.llm_model) {
        setLlmModel(bookSettings.llm_model);
      }
      if (bookSettings.llm_temperature !== undefined) {
        setLlmTemperature(bookSettings.llm_temperature);
      }
      if (bookSettings.llm_max_tokens !== undefined) {
        setLlmMaxTokens(bookSettings.llm_max_tokens);
      }
    } catch (error: any) {
      console.error('Failed to load book voice settings:', error);
      // Not an error if settings don't exist yet
      if (error.response?.status !== 404) {
        toast.error('Failed to load voice settings');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);

      // Build update payload from current state
      const updates: BookVoiceSettings = {
        tts_provider: selectedProvider || undefined,
        tts_voice: selectedVoice || undefined,
        tts_speed: speed !== 1.0 ? speed : undefined,
        tts_pitch: pitch !== 0 ? pitch : undefined,
        asr_provider: asrProvider || undefined,
        asr_language: asrLanguage !== 'en' ? asrLanguage : undefined,
        llm_model: llmModel || undefined,
        llm_temperature: llmTemperature !== 0.7 ? llmTemperature : undefined,
        llm_max_tokens: llmMaxTokens !== 1000 ? llmMaxTokens : undefined,
      };

      // Remove undefined values
      Object.keys(updates).forEach((key) => {
        if (updates[key as keyof BookVoiceSettings] === undefined) {
          delete updates[key as keyof BookVoiceSettings];
        }
      });

      await api.books.updateVoiceSettings(bookId, updates);
      toast.success('Voice settings saved for this book');
      setOriginalSettings(updates);
      setHasChanges(false);
      onClose();
    } catch (error: any) {
      console.error('Failed to save book voice settings:', error);
      toast.error(error.response?.data?.detail || 'Failed to save voice settings');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    try {
      await api.books.deleteVoiceSettings(bookId);
      toast.success('Voice settings reset to defaults');
      await loadBookSettings();
    } catch (error: any) {
      console.error('Failed to reset book voice settings:', error);
      toast.error('Failed to reset voice settings');
    }
  };

  // Stop preview audio
  const stopPreview = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      // Revoke blob URL to free memory
      if (audioRef.current.src.startsWith('blob:')) {
        URL.revokeObjectURL(audioRef.current.src);
      }
    }
    setIsPlaying(false);
  }, []);

  // Handle TTS preview
  const handlePreview = useCallback(async (text: string) => {
    if (!selectedProvider || !text.trim()) {
      toast.error('Please select a provider and enter preview text');
      return;
    }

    // Stop any existing playback
    stopPreview();

    try {
      setPreviewLoading(true);
      const authHeaders = await getAuthHeaders();

      // Build TTS request payload - use provider_id and voice_id as expected by backend
      const payload: Record<string, any> = {
        text: text.trim(),
        provider_id: selectedProvider,
        speed: speed,
      };

      // Add voice_id if selected (backend expects voice_id, not speaker)
      if (selectedVoice) {
        payload.voice_id = selectedVoice;
      }

      console.log('TTS Preview request:', payload);

      // Use /api/tts/preview endpoint (no billing)
      const response = await fetch(`${API_BASE_URL}/api/tts/preview`, {
        method: 'POST',
        headers: {
          ...authHeaders,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `TTS request failed: ${response.status}`);
      }

      // Parse JSON response with audio_base64
      const data = await response.json();

      if (!data.audio_base64) {
        throw new Error('No audio data returned from TTS service');
      }

      // Convert base64 to blob and play
      const audioBlob = await fetch(`data:audio/wav;base64,${data.audio_base64}`).then(r => r.blob());
      const audioUrl = URL.createObjectURL(audioBlob);

      // Create and play audio
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };

      audio.onerror = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
        toast.error('Failed to play audio');
      };

      await audio.play();
      setIsPlaying(true);
      toast.success(`Preview: ${data.provider_id} • ${data.duration?.toFixed(1)}s`);
    } catch (error: any) {
      console.error('TTS preview error:', error);
      toast.error(error.message || 'Failed to generate preview');
    } finally {
      setPreviewLoading(false);
    }
  }, [selectedProvider, selectedVoice, speed, stopPreview]);

  // Cleanup audio on unmount or modal close
  useEffect(() => {
    return () => {
      stopPreview();
    };
  }, [stopPreview]);

  // Track changes
  useEffect(() => {
    const hasTTSChanges =
      selectedProvider !== originalSettings.tts_provider ||
      selectedVoice !== originalSettings.tts_voice ||
      speed !== (originalSettings.tts_speed ?? 1.0) ||
      pitch !== (originalSettings.tts_pitch ?? 0);
    
    const hasASRChanges =
      asrProvider !== originalSettings.asr_provider ||
      asrLanguage !== (originalSettings.asr_language ?? 'en');
    
    const hasLLMChanges =
      llmModel !== originalSettings.llm_model ||
      llmTemperature !== (originalSettings.llm_temperature ?? 0.7) ||
      llmMaxTokens !== (originalSettings.llm_max_tokens ?? 1000);

    setHasChanges(hasTTSChanges || hasASRChanges || hasLLMChanges);
  }, [selectedProvider, selectedVoice, speed, pitch, asrProvider, asrLanguage, llmModel, llmTemperature, llmMaxTokens, originalSettings]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-gray-800 border border-gray-700 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <div className="flex items-center gap-3">
              <Settings className="w-6 h-6 text-purple-400" />
              <div>
                <h2 className="text-xl font-bold text-white">Voice Settings</h2>
                <p className="text-sm text-gray-400">{bookTitle}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
              </div>
            ) : (
              <>
                {/* Info Banner */}
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                  <p className="text-sm text-blue-300">
                    These settings apply to all reading sessions for this book. They override your default voice settings but can be changed during playback.
                  </p>
                </div>

                {/* TTS Settings */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 mb-4">
                    <Volume2 className="w-5 h-5 text-purple-400" />
                    <h3 className="text-lg font-semibold text-white">Text-to-Speech</h3>
                  </div>

                  <ComprehensiveTTSSelector
                    providers={providers}
                    selectedProviderId={selectedProvider}
                    onSelectProvider={setSelectedProvider}
                    selectedVoice={selectedVoice}
                    onSelectVoice={setSelectedVoice}
                    speed={speed}
                    onSpeedChange={setSpeed}
                    pitch={pitch}
                    onPitchChange={setPitch}
                    onPreview={handlePreview}
                    previewLoading={previewLoading || isPlaying}
                    previewText={previewText}
                    onPreviewTextChange={setPreviewText}
                    isLoading={ttsLoading}
                    showAdvanced={true}
                    showOnlineOnly={true}
                    variant="dark"
                    className="bg-gray-900/50 rounded-lg p-4"
                  />

                  {/* Stop Preview Button (shown when playing) */}
                  {isPlaying && (
                    <button
                      onClick={stopPreview}
                      className="flex items-center gap-2 px-4 py-2 mt-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                    >
                      <Square className="w-4 h-4" />
                      Stop Preview
                    </button>
                  )}
                </div>

                {/* ASR Settings */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 mb-4">
                    <Mic className="w-5 h-5 text-purple-400" />
                    <h3 className="text-lg font-semibold text-white">Speech Recognition</h3>
                  </div>

                  <div className="bg-gray-900/50 rounded-lg p-4 space-y-4">
                    {/* ASR Provider */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        ASR Provider
                      </label>
                      {loadingProviders ? (
                        <div className="flex items-center justify-center py-4">
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-500" />
                        </div>
                      ) : (
                        <select
                          value={asrProvider}
                          onChange={(e) => setAsrProvider(e.target.value)}
                          className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                        >
                          <option value="">Select ASR provider...</option>
                          {asrProviders
                            .filter(p => p.status === 'online')
                            .map((provider) => (
                              <option key={provider.id} value={provider.id}>
                                {provider.icon ? `${provider.icon} ` : ''}
                                {provider.name}
                              </option>
                            ))}
                        </select>
                      )}
                    </div>

                    {/* ASR Language */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Language
                      </label>
                      <select
                        value={asrLanguage}
                        onChange={(e) => setAsrLanguage(e.target.value)}
                        className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                      >
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                        <option value="zh">Chinese</option>
                        <option value="ar">Arabic</option>
                        <option value="hi">Hindi</option>
                        <option value="tw">Twi</option>
                        <option value="yo">Yoruba</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* LLM Settings */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 mb-4">
                    <Brain className="w-5 h-5 text-purple-400" />
                    <h3 className="text-lg font-semibold text-white">Language Model</h3>
                  </div>

                  <div className="bg-gray-900/50 rounded-lg p-4 space-y-4">
                    {/* LLM Model */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        LLM Model
                      </label>
                      {loadingProviders ? (
                        <div className="flex items-center justify-center py-4">
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-500" />
                        </div>
                      ) : (
                        <select
                          value={llmModel}
                          onChange={(e) => setLlmModel(e.target.value)}
                          className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                        >
                          <option value="">Select LLM model...</option>
                          {llmProviders.map((provider) => (
                            <option 
                              key={provider.id} 
                              value={provider.id}
                              disabled={provider.status !== 'online'}
                            >
                              {provider.icon ? `${provider.icon} ` : ''}
                              {provider.name}
                              {provider.status !== 'online' ? ` (${provider.status})` : ''}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>

                    {/* LLM Temperature */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Temperature: {llmTemperature.toFixed(1)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={llmTemperature}
                        onChange={(e) => setLlmTemperature(parseFloat(e.target.value))}
                        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>Conservative (0)</span>
                        <span>Balanced (1)</span>
                        <span>Creative (2)</span>
                      </div>
                    </div>

                    {/* LLM Max Tokens */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Max Tokens
                      </label>
                      <input
                        type="number"
                        min="100"
                        max="4000"
                        step="100"
                        value={llmMaxTokens}
                        onChange={(e) => setLlmMaxTokens(parseInt(e.target.value))}
                        className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Maximum tokens in the response (100-4000)
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-gray-700 bg-gray-900/50">
            <button
              onClick={handleReset}
              disabled={saving || loading || (!originalSettings.tts_provider && !originalSettings.asr_provider && !originalSettings.llm_model)}
              className="flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Reset to Defaults
            </button>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                disabled={saving}
                className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || loading || !hasChanges}
                className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Save Settings
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

