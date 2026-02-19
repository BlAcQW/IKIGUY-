/**
 * Voice Configuration Panel for InkWave Books
 *
 * Allows users to configure LLM, TTS, and ASR settings on a per-book basis.
 * Settings persist across sessions and override user defaults.
 */

import React, { useState, useEffect } from 'react';
import { X, Save, RotateCcw, Loader2 } from 'lucide-react';
import { ComprehensiveTTSSelector } from '../../../../shared/frontend/components/voice-settings/ComprehensiveTTSSelector';
import { useComprehensiveTTS } from '../../../../shared/frontend/hooks/useComprehensiveTTS';
import { useBookVoiceSettings, BookVoiceSettings } from '../hooks/useBookVoiceSettings';

export interface VoiceConfigPanelProps {
  bookId: string;
  onClose: () => void;
  onSave?: (settings: BookVoiceSettings) => void;
}

// LLM provider options
const LLM_PROVIDERS = [
  { id: 'gemini', name: 'Google Gemini', icon: '🔷' },
  { id: 'openai', name: 'OpenAI', icon: '🟢' },
  { id: 'anthropic', name: 'Anthropic', icon: '🟣' },
  { id: 'ollama', name: 'Ollama (Local)', icon: '🦙' },
];

// LLM models by provider
const LLM_MODELS: Record<string, { id: string; name: string }[]> = {
  gemini: [
    { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash (Recommended)' },
    { id: 'gemini-2.0-flash-exp', name: 'Gemini 2.0 Flash Experimental' },
    { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro' },
  ],
  openai: [
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini (Recommended)' },
    { id: 'gpt-4o', name: 'GPT-4o' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
  ],
  anthropic: [
    { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet (Recommended)' },
    { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku' },
  ],
  ollama: [
    { id: 'llama3.2:3b', name: 'Llama 3.2 3B (Recommended)' },
    { id: 'llama3.1:8b', name: 'Llama 3.1 8B' },
    { id: 'mistral:7b', name: 'Mistral 7B' },
  ],
};

export const VoiceConfigPanel: React.FC<VoiceConfigPanelProps> = ({
  bookId,
  onClose,
  onSave,
}) => {
  const {
    settings: savedSettings,
    hasSettings,
    loading: loadingSettings,
    updateSettings,
    clearSettings,
  } = useBookVoiceSettings(bookId);

  const [activeTab, setActiveTab] = useState<'llm' | 'voice' | 'transcriber'>('llm');
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // LLM settings state
  const [llmProvider, setLlmProvider] = useState<string>('gemini');
  const [llmModel, setLlmModel] = useState<string>('gemini-2.5-flash');
  const [temperature, setTemperature] = useState<number>(0.7);
  const [systemPrompt, setSystemPrompt] = useState<string>('');

  // TTS settings (using shared hook)
  const {
    selectedProvider,
    selectedVoice,
    setProvider,
    setVoice,
    providers,
    voices,
    isLoadingProviders,
    isLoadingVoices,
  } = useComprehensiveTTS();

  // Load saved settings into state
  useEffect(() => {
    if (savedSettings) {
      // LLM settings
      if (savedSettings.llm_provider) setLlmProvider(savedSettings.llm_provider);
      if (savedSettings.llm_model) setLlmModel(savedSettings.llm_model);
      if (savedSettings.llm_temperature !== undefined) setTemperature(savedSettings.llm_temperature);
      if (savedSettings.system_prompt) setSystemPrompt(savedSettings.system_prompt);

      // TTS settings
      if (savedSettings.tts_provider) setProvider(savedSettings.tts_provider);
      if (savedSettings.tts_voice) setVoice(savedSettings.tts_voice);
    }
  }, [savedSettings, setProvider, setVoice]);

  // Handle save
  const handleSave = async () => {
    setSaving(true);

    try {
      const updates: Partial<BookVoiceSettings> = {
        llm_provider: llmProvider,
        llm_model: llmModel,
        llm_temperature: temperature,
        system_prompt: systemPrompt || undefined,
        tts_provider: selectedProvider || undefined,
        tts_voice: selectedVoice || undefined,
      };

      await updateSettings(updates);
      setHasChanges(false);

      if (onSave) {
        onSave(updates as BookVoiceSettings);
      }

      // Show success message
      alert('Settings saved successfully!');
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  // Handle reset
  const handleReset = async () => {
    if (!confirm('Are you sure you want to clear all book-specific settings? This will revert to your user defaults.')) {
      return;
    }

    setSaving(true);

    try {
      await clearSettings();
      setHasChanges(false);

      // Reset to defaults
      setLlmProvider('gemini');
      setLlmModel('gemini-2.5-flash');
      setTemperature(0.7);
      setSystemPrompt('');

      alert('Settings cleared successfully!');
    } catch (error) {
      console.error('Failed to clear settings:', error);
      alert('Failed to clear settings. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  // Track changes
  useEffect(() => {
    setHasChanges(true);
  }, [llmProvider, llmModel, temperature, systemPrompt, selectedProvider, selectedVoice]);

  // Get available models for current provider
  const availableModels = LLM_MODELS[llmProvider] || [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Voice Settings
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 px-6">
          {(['llm', 'voice', 'transcriber'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab === 'llm' && 'AI Assistant'}
              {tab === 'voice' && 'Voice'}
              {tab === 'transcriber' && 'Transcriber'}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loadingSettings ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="animate-spin text-indigo-600" size={32} />
            </div>
          ) : (
            <>
              {/* LLM Tab */}
              {activeTab === 'llm' && (
                <div className="space-y-6">
                  {/* LLM Provider */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      LLM Provider
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {LLM_PROVIDERS.map((provider) => (
                        <button
                          key={provider.id}
                          onClick={() => {
                            setLlmProvider(provider.id);
                            // Set default model for this provider
                            setLlmModel(LLM_MODELS[provider.id]?.[0]?.id || '');
                          }}
                          className={`px-4 py-3 rounded-lg border-2 transition-all ${
                            llmProvider === provider.id
                              ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                              : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                          }`}
                        >
                          <span className="mr-2">{provider.icon}</span>
                          {provider.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* LLM Model */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Model
                    </label>
                    <select
                      value={llmModel}
                      onChange={(e) => setLlmModel(e.target.value)}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      {availableModels.map((model) => (
                        <option key={model.id} value={model.id}>
                          {model.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Temperature */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Temperature: {temperature.toFixed(2)}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="2"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value))}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Precise</span>
                      <span>Balanced</span>
                      <span>Creative</span>
                    </div>
                  </div>

                  {/* System Prompt */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Custom System Prompt (Optional)
                    </label>
                    <textarea
                      value={systemPrompt}
                      onChange={(e) => setSystemPrompt(e.target.value)}
                      placeholder="Enter a custom system prompt to customize how the AI responds to questions about this book..."
                      rows={4}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Leave empty to use the default prompt
                    </p>
                  </div>
                </div>
              )}

              {/* Voice Tab */}
              {activeTab === 'voice' && (
                <div className="space-y-6">
                  <ComprehensiveTTSSelector
                    selectedProvider={selectedProvider}
                    selectedVoice={selectedVoice}
                    onProviderChange={setProvider}
                    onVoiceChange={setVoice}
                    providers={providers}
                    voices={voices}
                    isLoadingProviders={isLoadingProviders}
                    isLoadingVoices={isLoadingVoices}
                  />
                </div>
              )}

              {/* Transcriber Tab */}
              {activeTab === 'transcriber' && (
                <div className="space-y-6">
                  <div className="text-center py-12 text-gray-500">
                    <p>Transcriber settings coming soon...</p>
                    <p className="text-sm mt-2">
                      Currently using Faster Whisper (medium model)
                    </p>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center space-x-2">
            {hasSettings && (
              <button
                onClick={handleReset}
                disabled={saving}
                className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RotateCcw size={16} className="mr-2" />
                Reset to Defaults
              </button>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !hasChanges}
              className="flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? (
                <>
                  <Loader2 size={16} className="mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save size={16} className="mr-2" />
                  Save Settings
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
