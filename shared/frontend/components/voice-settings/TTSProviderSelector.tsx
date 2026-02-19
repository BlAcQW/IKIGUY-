/**
 * TTS Provider Selector Component
 *
 * Compact selector for choosing TTS provider in settings.
 * Part of @kasaai/shared-frontend library.
 */

import React from 'react';

export interface TTSProvider {
  id: string;
  name: string;
  description?: string;
  status: 'online' | 'offline' | 'building';
  icon?: string;
  languages?: number;
  capabilities?: {
    voiceCloning?: boolean;
    multiLanguage?: boolean;
    multiSpeaker?: boolean;
    emotionControl?: boolean;
  };
}

export interface TTSProviderSelectorProps {
  providers: TTSProvider[];
  selectedProviderId: string | null;
  onSelectProvider: (providerId: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  showOnlineOnly?: boolean;
  className?: string;
}

export const TTSProviderSelector: React.FC<TTSProviderSelectorProps> = ({
  providers,
  selectedProviderId,
  onSelectProvider,
  isLoading = false,
  disabled = false,
  showOnlineOnly = false,
  className = '',
}) => {
  // Filter providers based on showOnlineOnly
  const filteredProviders = showOnlineOnly
    ? providers.filter((p) => p.status === 'online')
    : providers;

  const getStatusColor = (status: TTSProvider['status']) => {
    switch (status) {
      case 'online':
        return 'bg-green-100 text-green-800';
      case 'offline':
        return 'bg-red-100 text-red-800';
      case 'building':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className={`space-y-2 ${className}`}>
        <label className="block text-sm font-medium text-gray-700">
          TTS Provider
        </label>
        <div className="animate-pulse bg-gray-200 h-10 rounded-md"></div>
      </div>
    );
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        TTS Provider
      </label>

      <select
        value={selectedProviderId || ''}
        onChange={(e) => onSelectProvider(e.target.value)}
        disabled={disabled}
        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <option value="">Select a provider...</option>
        {filteredProviders.map((provider) => (
          <option
            key={provider.id}
            value={provider.id}
            disabled={provider.status !== 'online'}
          >
            {provider.icon ? `${provider.icon} ` : ''}
            {provider.name}
            {provider.status !== 'online' ? ` (${provider.status})` : ''}
            {provider.languages ? ` - ${provider.languages} languages` : ''}
          </option>
        ))}
      </select>

      {/* Provider Info Card (shown when provider is selected) */}
      {selectedProviderId && filteredProviders.find((p) => p.id === selectedProviderId) && (
        <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-md">
          {(() => {
            const selected = filteredProviders.find((p) => p.id === selectedProviderId);
            if (!selected) return null;

            return (
              <>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {selected.icon && <span className="text-xl">{selected.icon}</span>}
                    <span className="font-medium text-gray-900">{selected.name}</span>
                  </div>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(
                      selected.status
                    )}`}
                  >
                    {selected.status}
                  </span>
                </div>

                {selected.description && (
                  <p className="text-sm text-gray-600 mb-2">{selected.description}</p>
                )}

                {selected.capabilities && (
                  <div className="flex items-center space-x-3 text-xs text-gray-500">
                    {selected.capabilities.voiceCloning && (
                      <span title="Voice Cloning" className="flex items-center">
                        🎭 Voice Cloning
                      </span>
                    )}
                    {selected.capabilities.multiLanguage && (
                      <span title="Multi-Language" className="flex items-center">
                        🌍 Multi-Language
                      </span>
                    )}
                    {selected.capabilities.multiSpeaker && (
                      <span title="Multi-Speaker" className="flex items-center">
                        👥 Multi-Speaker
                      </span>
                    )}
                    {selected.capabilities.emotionControl && (
                      <span title="Emotion Control" className="flex items-center">
                        😊 Emotion Control
                      </span>
                    )}
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}

      {filteredProviders.length === 0 && (
        <p className="text-sm text-gray-500 italic">
          No providers available. Please configure TTS providers first.
        </p>
      )}
    </div>
  );
};
