/**
 * Voice Settings Panel Component
 *
 * Master component that combines all voice settings selectors.
 * Provides complete voice preferences management UI.
 * Part of @kasaai/shared-frontend library.
 */

import React, { useState, useEffect } from 'react';
import { TTSProviderSelector, TTSProvider } from './TTSProviderSelector';
import { ASRProviderSelector, ASRProvider } from './ASRProviderSelector';
import { LLMModelSelector, LLMModel } from './LLMModelSelector';
import { VoiceLibrarySelector, ClonedVoice } from './VoiceLibrarySelector';
import { ReferenceAudioList } from '../reference-audio';

export interface VoiceSettingsPanelProps {
  // TTS Provider
  ttsProviders: TTSProvider[];
  selectedTTSProviderId: string | null;
  onSelectTTSProvider: (providerId: string) => void;

  // ASR Provider
  asrProviders: ASRProvider[];
  selectedASRProviderId: string | null;
  onSelectASRProvider: (providerId: string) => void;

  // LLM Model
  llmModels: LLMModel[];
  selectedLLMModelId: string | null;
  onSelectLLMModel: (modelId: string) => void;

  // Voice Library
  clonedVoices: ClonedVoice[];
  favoriteVoiceIds: string[];
  onToggleFavoriteVoice: (voiceId: string) => void;
  onPreviewVoice?: (voiceId: string) => void;

  // Additional Settings
  ttsSpeed?: number;
  onTTSSpeedChange?: (speed: number) => void;
  ttsPitch?: number;
  onTTSPitchChange?: (pitch: number) => void;
  asrLanguage?: string;
  onASRLanguageChange?: (language: string) => void;
  llmTemperature?: number;
  onLLMTemperatureChange?: (temperature: number) => void;
  llmMaxTokens?: number;
  onLLMMaxTokensChange?: (maxTokens: number) => void;

  // Save/Reset Actions
  onSave?: () => void;
  onReset?: () => void;
  onResetToOrgDefaults?: () => void;

  // Reference Audio (optional)
  apiBaseUrl?: string;
  getAuthHeaders?: () => Promise<Record<string, string>>;
  showReferenceAudio?: boolean;

  // State
  isLoading?: boolean;
  isDirty?: boolean;
  disabled?: boolean;
  showAdvanced?: boolean;
  variant?: 'light' | 'dark';
  className?: string;
}

export const VoiceSettingsPanel: React.FC<VoiceSettingsPanelProps> = ({
  // TTS
  ttsProviders,
  selectedTTSProviderId,
  onSelectTTSProvider,

  // ASR
  asrProviders,
  selectedASRProviderId,
  onSelectASRProvider,

  // LLM
  llmModels,
  selectedLLMModelId,
  onSelectLLMModel,

  // Voice Library
  clonedVoices,
  favoriteVoiceIds,
  onToggleFavoriteVoice,
  onPreviewVoice,

  // Additional Settings
  ttsSpeed = 1.0,
  onTTSSpeedChange,
  ttsPitch = 0.0,
  onTTSPitchChange,
  asrLanguage = 'en',
  onASRLanguageChange,
  llmTemperature = 0.7,
  onLLMTemperatureChange,
  llmMaxTokens = 2000,
  onLLMMaxTokensChange,

  // Actions
  onSave,
  onReset,
  onResetToOrgDefaults,

  // State
  isLoading = false,
  isDirty = false,
  disabled = false,
  showAdvanced = false,
  variant = 'light',
  className = '',
}) => {
  const [activeTab, setActiveTab] = useState<'tts' | 'asr' | 'llm' | 'voices' | 'reference-audio'>('tts');

  const tabs = [
    { id: 'tts' as const, label: 'Text-to-Speech', icon: '🎵' },
    { id: 'asr' as const, label: 'Speech Recognition', icon: '🎤' },
    { id: 'llm' as const, label: 'Language Model', icon: '🤖' },
    { id: 'voices' as const, label: 'Voice Library', icon: '🎭' },
    ...(showReferenceAudio ? [{ id: 'reference-audio' as const, label: 'Reference Audio', icon: '🎙️' }] : []),
  ];

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Voice Settings</h2>
            <p className="text-sm text-gray-500 mt-1">
              Configure your voice preferences for TTS, ASR, and LLM
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            {onResetToOrgDefaults && (
              <button
                onClick={onResetToOrgDefaults}
                disabled={disabled || isLoading}
                className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Reset to Org Defaults
              </button>
            )}

            {onReset && (
              <button
                onClick={onReset}
                disabled={disabled || isLoading || !isDirty}
                className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Reset
              </button>
            )}

            {onSave && (
              <button
                onClick={onSave}
                disabled={disabled || isLoading || !isDirty}
                className="px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Saving...' : 'Save Changes'}
              </button>
            )}
          </div>
        </div>

        {/* Dirty Indicator */}
        {isDirty && (
          <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-sm text-yellow-800">
              ⚠️ You have unsaved changes
            </p>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-4 px-6" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center space-x-2 px-3 py-3 text-sm font-medium border-b-2 transition-colors
                ${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {/* TTS Tab */}
        {activeTab === 'tts' && (
          <div className="space-y-6">
            <TTSProviderSelector
              providers={ttsProviders}
              selectedProviderId={selectedTTSProviderId}
              onSelectProvider={onSelectTTSProvider}
              isLoading={isLoading}
              disabled={disabled}
              showOnlineOnly={true}
            />

            {/* TTS Advanced Settings */}
            {showAdvanced && onTTSSpeedChange && (
              <div className="space-y-4 pt-4 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-900">Advanced TTS Settings</h3>

                {/* Speed Control */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Speed: {ttsSpeed.toFixed(2)}x
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="2.0"
                    step="0.1"
                    value={ttsSpeed}
                    onChange={(e) => onTTSSpeedChange(parseFloat(e.target.value))}
                    disabled={disabled}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Slower (0.5x)</span>
                    <span>Faster (2.0x)</span>
                  </div>
                </div>

                {/* Pitch Control */}
                {onTTSPitchChange && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Pitch: {ttsPitch > 0 ? '+' : ''}{ttsPitch.toFixed(1)}
                    </label>
                    <input
                      type="range"
                      min="-1.0"
                      max="1.0"
                      step="0.1"
                      value={ttsPitch}
                      onChange={(e) => onTTSPitchChange(parseFloat(e.target.value))}
                      disabled={disabled}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Lower (-1.0)</span>
                      <span>Higher (+1.0)</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ASR Tab */}
        {activeTab === 'asr' && (
          <div className="space-y-6">
            <ASRProviderSelector
              providers={asrProviders}
              selectedProviderId={selectedASRProviderId}
              onSelectProvider={onSelectASRProvider}
              isLoading={isLoading}
              disabled={disabled}
              showOnlineOnly={true}
            />

            {/* ASR Language Setting */}
            {showAdvanced && onASRLanguageChange && (
              <div className="pt-4 border-t border-gray-200">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Default Language
                </label>
                <select
                  value={asrLanguage}
                  onChange={(e) => onASRLanguageChange(e.target.value)}
                  disabled={disabled}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="zh">Chinese</option>
                  <option value="ar">Arabic</option>
                  <option value="hi">Hindi</option>
                </select>
              </div>
            )}
          </div>
        )}

        {/* LLM Tab */}
        {activeTab === 'llm' && (
          <div className="space-y-6">
            <LLMModelSelector
              models={llmModels}
              selectedModelId={selectedLLMModelId}
              onSelectModel={onSelectLLMModel}
              isLoading={isLoading}
              disabled={disabled}
              groupByProvider={true}
            />

            {/* LLM Advanced Settings */}
            {showAdvanced && (
              <div className="space-y-4 pt-4 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-900">Advanced LLM Settings</h3>

                {/* Temperature Control */}
                {onLLMTemperatureChange && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Temperature: {llmTemperature.toFixed(2)}
                    </label>
                    <input
                      type="range"
                      min="0.0"
                      max="2.0"
                      step="0.1"
                      value={llmTemperature}
                      onChange={(e) => onLLMTemperatureChange(parseFloat(e.target.value))}
                      disabled={disabled}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Focused (0.0)</span>
                      <span>Creative (2.0)</span>
                    </div>
                  </div>
                )}

                {/* Max Tokens Control */}
                {onLLMMaxTokensChange && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Tokens: {llmMaxTokens.toLocaleString()}
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="100000"
                      step="100"
                      value={llmMaxTokens}
                      onChange={(e) => onLLMMaxTokensChange(parseInt(e.target.value))}
                      disabled={disabled}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Voice Library Tab */}
        {activeTab === 'voices' && (
          <div>
            <VoiceLibrarySelector
              voices={clonedVoices}
              favoriteVoiceIds={favoriteVoiceIds}
              onToggleFavorite={onToggleFavoriteVoice}
              onPreviewVoice={onPreviewVoice}
              isLoading={isLoading}
              disabled={disabled}
              maxFavorites={10}
              variant={variant}
            />
          </div>
        )}

        {/* Reference Audio Tab */}
        {showReferenceAudio && activeTab === 'reference-audio' && apiBaseUrl && (
          <div>
            <ReferenceAudioList
              apiBaseUrl={apiBaseUrl}
              getAuthHeaders={getAuthHeaders}
              showUpload={true}
            />
          </div>
        )}
      </div>
    </div>
  );
};
