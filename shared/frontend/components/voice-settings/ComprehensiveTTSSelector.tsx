/**
 * Comprehensive TTS Provider Selector
 *
 * Advanced TTS provider selection component with:
 * - All 14+ TTS providers from @shared/tts/config.py
 * - Capability badges (voice cloning, multilingual, etc.)
 * - Model selection for multi-model providers (TTS-WebUI)
 * - Voice/Speaker selection with preview
 * - Speed, pitch, and language controls
 * - Status indicators (online, offline, degraded)
 * - Deployment location (RunPod, Local Docker, etc.)
 *
 * Can be used in: Voice Agent, ChurchFlow, InkWave, StudyFlow, etc.
 */

import React, { useState, useEffect } from 'react';

export interface TTSCapabilities {
  voice_cloning?: boolean;
  multi_language?: boolean;
  speed_control?: boolean;
  pitch_control?: boolean;
  multi_speaker?: boolean;
  multi_model?: boolean;
  emotion_control?: boolean;
  real_time_conversation?: boolean;
  ssml_support?: boolean;
  streaming?: boolean;
  supported_languages?: string[];
  supported_formats?: string[];
  available_models?: string[];
}

export interface TTSProviderInfo {
  id: string;
  name: string;
  description: string;
  status: 'online' | 'offline' | 'degraded';
  deployment: 'runpod' | 'local' | 'cloud';
  endpoint: string;
  capabilities: TTSCapabilities;
  languages?: Record<string, string>;
  speakers?: Record<string, string>;
  icon?: string;
}

export interface ComprehensiveTTSSelectorProps {
  // Provider selection
  providers: TTSProviderInfo[];
  selectedProviderId: string | null;
  onSelectProvider: (providerId: string) => void;

  // Model selection (for multi-model providers like TTS-WebUI)
  selectedModel?: string | null;
  onSelectModel?: (model: string) => void;

  // Voice/Speaker selection
  selectedVoice?: string | null;
  onSelectVoice?: (voice: string) => void;

  // Language selection
  selectedLanguage?: string;
  onSelectLanguage?: (language: string) => void;

  // Voice controls
  speed?: number;
  onSpeedChange?: (speed: number) => void;
  pitch?: number;
  onPitchChange?: (pitch: number) => void;

  // Preview
  onPreview?: (text: string) => void;
  previewLoading?: boolean;
  previewText?: string;
  onPreviewTextChange?: (text: string) => void;

  // State
  isLoading?: boolean;
  disabled?: boolean;
  showOnlineOnly?: boolean;
  showAdvanced?: boolean;
  className?: string;

  // Theme
  variant?: 'light' | 'dark';
}

export const ComprehensiveTTSSelector: React.FC<ComprehensiveTTSSelectorProps> = ({
  providers,
  selectedProviderId,
  onSelectProvider,
  selectedModel,
  onSelectModel,
  selectedVoice,
  onSelectVoice,
  selectedLanguage = 'en',
  onSelectLanguage,
  speed = 1.0,
  onSpeedChange,
  pitch = 0.0,
  onPitchChange,
  onPreview,
  previewLoading = false,
  previewText: controlledPreviewText,
  onPreviewTextChange,
  isLoading = false,
  disabled = false,
  showOnlineOnly = false,
  showAdvanced = false,
  className = '',
  variant = 'light',
}) => {
  // Use controlled preview text if provided, otherwise use local state
  const [localPreviewText, setLocalPreviewText] = useState('Hello, this is a preview of the selected voice.');
  const previewText = controlledPreviewText !== undefined ? controlledPreviewText : localPreviewText;
  const setPreviewText = onPreviewTextChange || setLocalPreviewText;
  const [expandedView, setExpandedView] = useState(false);

  // Theme-aware classes
  const isDark = variant === 'dark';
  const theme = {
    text: isDark ? 'text-gray-100' : 'text-gray-900',
    textMuted: isDark ? 'text-gray-400' : 'text-gray-600',
    textLabel: isDark ? 'text-gray-300' : 'text-gray-700',
    bg: isDark ? 'bg-gray-800' : 'bg-white',
    bgMuted: isDark ? 'bg-gray-700' : 'bg-gray-50',
    border: isDark ? 'border-gray-600' : 'border-gray-300',
    borderMuted: isDark ? 'border-gray-700' : 'border-gray-200',
    input: isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300 text-gray-900',
    select: isDark ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-300 text-gray-900',
    cardSelected: isDark ? 'border-indigo-400 bg-indigo-900/30' : 'border-indigo-500 bg-indigo-50',
    cardDefault: isDark ? 'border-gray-600 bg-gray-800 hover:border-gray-500' : 'border-gray-200 bg-white hover:border-gray-300',
    link: isDark ? 'text-indigo-400 hover:text-indigo-300' : 'text-indigo-600 hover:text-indigo-700',
  };

  // Get selected provider
  const selectedProvider = providers.find(p => p.id === selectedProviderId);

  // Filter providers
  const filteredProviders = showOnlineOnly
    ? providers.filter(p => p.status === 'online')
    : providers;

  // Get status styling
  const getStatusBadge = (status: TTSProviderInfo['status']) => {
    const styles = {
      online: 'bg-green-100 text-green-800 border-green-200',
      offline: 'bg-red-100 text-red-800 border-red-200',
      degraded: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    };
    const icons = {
      online: '✅',
      offline: '❌',
      degraded: '⚠️',
    };
    return { style: styles[status], icon: icons[status] };
  };

  // Get deployment badge
  const getDeploymentBadge = (deployment: TTSProviderInfo['deployment']) => {
    const configs = {
      runpod: { label: 'RunPod GPU', icon: '🚀', style: 'bg-purple-100 text-purple-800' },
      local: { label: 'Local Docker', icon: '🖥️', style: 'bg-blue-100 text-blue-800' },
      cloud: { label: 'Cloud', icon: '☁️', style: 'bg-cyan-100 text-cyan-800' },
    };
    return configs[deployment];
  };

  if (isLoading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="animate-pulse space-y-3">
          <div className={`h-10 rounded-md ${isDark ? 'bg-gray-700' : 'bg-gray-200'}`}></div>
          <div className={`h-32 rounded-md ${isDark ? 'bg-gray-700' : 'bg-gray-200'}`}></div>
          <div className={`h-10 rounded-md ${isDark ? 'bg-gray-700' : 'bg-gray-200'}`}></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Provider Selection */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className={`block text-sm font-medium ${theme.textLabel}`}>
            TTS Provider
          </label>
          <button
            type="button"
            onClick={() => setExpandedView(!expandedView)}
            className={`text-xs ${theme.link}`}
          >
            {expandedView ? 'Compact View' : 'Detailed View'}
          </button>
        </div>

        {/* Compact Select View */}
        {!expandedView && (
          <select
            value={selectedProviderId || ''}
            onChange={(e) => onSelectProvider(e.target.value)}
            disabled={disabled}
            className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm disabled:opacity-50 ${theme.select}`}
          >
            <option value="">Select TTS Provider...</option>
            {filteredProviders.map((provider) => (
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

        {/* Expanded Grid View */}
        {expandedView && (
          <div className={`grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto border rounded-md p-3 ${theme.border}`}>
            {filteredProviders.map((provider) => {
              const statusBadge = getStatusBadge(provider.status);
              const deploymentBadge = getDeploymentBadge(provider.deployment);
              const isSelected = provider.id === selectedProviderId;

              return (
                <button
                  key={provider.id}
                  type="button"
                  onClick={() => onSelectProvider(provider.id)}
                  disabled={disabled || provider.status === 'offline'}
                  className={`
                    p-3 border-2 rounded-lg text-left transition-all
                    ${isSelected ? theme.cardSelected : theme.cardDefault}
                    ${provider.status === 'offline' ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                  `}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {provider.icon && <span className="text-xl">{provider.icon}</span>}
                      <span className={`font-medium text-sm ${theme.text}`}>{provider.name}</span>
                    </div>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs border ${statusBadge.style}`}>
                      {statusBadge.icon} {provider.status}
                    </span>
                  </div>

                  {/* Description */}
                  <p className={`text-xs mb-2 line-clamp-2 ${theme.textMuted}`}>
                    {provider.description}
                  </p>

                  {/* Deployment Badge */}
                  <div className="mb-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs ${deploymentBadge.style}`}>
                      {deploymentBadge.icon} {deploymentBadge.label}
                    </span>
                  </div>

                  {/* Capabilities */}
                  <div className="flex flex-wrap gap-1">
                    {provider.capabilities.voice_cloning && (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-purple-100 text-purple-700" title="Voice Cloning">
                        🎭
                      </span>
                    )}
                    {provider.capabilities.multi_language && (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-green-100 text-green-700" title="Multi-Language">
                        🌍
                      </span>
                    )}
                    {provider.capabilities.multi_speaker && (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-blue-100 text-blue-700" title="Multi-Speaker">
                        👥
                      </span>
                    )}
                    {provider.capabilities.emotion_control && (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-pink-100 text-pink-700" title="Emotion Control">
                        😊
                      </span>
                    )}
                    {provider.capabilities.streaming && (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-indigo-100 text-indigo-700" title="Streaming">
                        ⚡
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Selected Provider Details */}
      {selectedProvider && (
        <div className={`border rounded-lg p-4 space-y-4 ${theme.borderMuted} ${theme.bgMuted}`}>
          {/* Provider Info */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                {selectedProvider.icon && <span className="text-2xl">{selectedProvider.icon}</span>}
                <h3 className={`font-semibold ${theme.text}`}>{selectedProvider.name}</h3>
              </div>
              <div className="flex items-center gap-2">
                {(() => {
                  const statusBadge = getStatusBadge(selectedProvider.status);
                  return (
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs border ${statusBadge.style}`}>
                      {statusBadge.icon} {selectedProvider.status}
                    </span>
                  );
                })()}
              </div>
            </div>
            <p className={`text-sm ${theme.textMuted}`}>{selectedProvider.description}</p>
          </div>

          {/* Model Selection (for multi-model providers like TTS-WebUI) */}
          {selectedProvider.capabilities.multi_model && selectedProvider.capabilities.available_models && onSelectModel && (
            <div>
              <label className={`block text-sm font-medium mb-1 ${theme.textLabel}`}>
                TTS Model
              </label>
              <select
                value={selectedModel || ''}
                onChange={(e) => onSelectModel(e.target.value)}
                disabled={disabled}
                className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm ${theme.select}`}
              >
                <option value="">Select model...</option>
                {selectedProvider.capabilities.available_models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
              <p className={`text-xs mt-1 ${theme.textMuted}`}>
                {selectedProvider.capabilities.available_models.length} models available
              </p>
            </div>
          )}

          {/* Voice/Speaker Selection */}
          {selectedProvider.speakers && Object.keys(selectedProvider.speakers).length > 0 && onSelectVoice && (
            <div>
              <label className={`block text-sm font-medium mb-1 ${theme.textLabel}`}>
                Voice/Speaker
              </label>
              <select
                value={selectedVoice || ''}
                onChange={(e) => onSelectVoice(e.target.value)}
                disabled={disabled}
                className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm ${theme.select}`}
              >
                <option value="">Select voice...</option>
                {Object.entries(selectedProvider.speakers).map(([id, label]) => (
                  <option key={id} value={id}>
                    {label}
                  </option>
                ))}
              </select>
              <p className={`text-xs mt-1 ${theme.textMuted}`}>
                {Object.keys(selectedProvider.speakers).length} voices available
              </p>
            </div>
          )}

          {/* Language Selection */}
          {selectedProvider.capabilities.multi_language && selectedProvider.languages && onSelectLanguage && (
            <div>
              <label className={`block text-sm font-medium mb-1 ${theme.textLabel}`}>
                Language
              </label>
              <select
                value={selectedLanguage}
                onChange={(e) => onSelectLanguage(e.target.value)}
                disabled={disabled}
                className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm ${theme.select}`}
              >
                {Object.entries(selectedProvider.languages).map(([code, name]) => (
                  <option key={code} value={code}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Advanced Controls */}
          {showAdvanced && (
            <div className={`space-y-3 pt-3 border-t ${theme.border}`}>
              {/* Speed Control */}
              {selectedProvider.capabilities.speed_control && onSpeedChange && (
                <div>
                  <label className={`block text-sm font-medium mb-1 ${theme.textLabel}`}>
                    Speed: {speed.toFixed(1)}x
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="2.0"
                    step="0.1"
                    value={speed}
                    onChange={(e) => onSpeedChange(parseFloat(e.target.value))}
                    disabled={disabled}
                    className="w-full"
                  />
                  <div className={`flex justify-between text-xs mt-1 ${theme.textMuted}`}>
                    <span>Slower (0.5x)</span>
                    <span>Normal (1.0x)</span>
                    <span>Faster (2.0x)</span>
                  </div>
                </div>
              )}

              {/* Pitch Control */}
              {selectedProvider.capabilities.pitch_control && onPitchChange && (
                <div>
                  <label className={`block text-sm font-medium mb-1 ${theme.textLabel}`}>
                    Pitch: {pitch > 0 ? '+' : ''}{pitch.toFixed(1)}
                  </label>
                  <input
                    type="range"
                    min="-20"
                    max="20"
                    step="1"
                    value={pitch}
                    onChange={(e) => onPitchChange(parseFloat(e.target.value))}
                    disabled={disabled}
                    className="w-full"
                  />
                  <div className={`flex justify-between text-xs mt-1 ${theme.textMuted}`}>
                    <span>Lower (-20)</span>
                    <span>Normal (0)</span>
                    <span>Higher (+20)</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Preview */}
          {onPreview && (
            <div className={`pt-3 border-t ${theme.border}`}>
              <label className={`block text-sm font-medium mb-1 ${theme.textLabel}`}>
                Preview
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={previewText}
                  onChange={(e) => setPreviewText(e.target.value)}
                  placeholder="Enter text to preview..."
                  disabled={disabled || previewLoading}
                  className={`flex-1 px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${theme.input}`}
                />
                <button
                  type="button"
                  onClick={() => onPreview(previewText)}
                  disabled={disabled || previewLoading || !previewText}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {previewLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Loading...
                    </>
                  ) : (
                    <>
                      🔊 Preview
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Capabilities Summary */}
          <div className={`pt-3 border-t ${theme.border}`}>
            <p className={`text-xs font-medium mb-2 ${theme.textLabel}`}>Capabilities:</p>
            <div className="flex flex-wrap gap-2">
              {selectedProvider.capabilities.voice_cloning && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-purple-100 text-purple-700">
                  🎭 Voice Cloning
                </span>
              )}
              {selectedProvider.capabilities.multi_language && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-green-100 text-green-700">
                  🌍 {selectedProvider.capabilities.supported_languages?.length || 0} Languages
                </span>
              )}
              {selectedProvider.capabilities.multi_speaker && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-700">
                  👥 Multi-Speaker
                </span>
              )}
              {selectedProvider.capabilities.emotion_control && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-pink-100 text-pink-700">
                  😊 Emotion Control
                </span>
              )}
              {selectedProvider.capabilities.streaming && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-indigo-100 text-indigo-700">
                  ⚡ Streaming
                </span>
              )}
              {selectedProvider.capabilities.ssml_support && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-yellow-100 text-yellow-700">
                  📝 SSML
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* No Providers Message */}
      {filteredProviders.length === 0 && (
        <div className={`text-center py-8 ${theme.textMuted}`}>
          <p className="text-sm">No TTS providers available</p>
          <p className="text-xs mt-1">Please configure TTS providers or disable "show online only"</p>
        </div>
      )}
    </div>
  );
};
