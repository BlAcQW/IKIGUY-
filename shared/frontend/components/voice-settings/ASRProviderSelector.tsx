/**
 * ASR Provider Selector Component
 *
 * Compact selector for choosing ASR (Automatic Speech Recognition) provider in settings.
 * Part of @kasaai/shared-frontend library.
 */

import React from 'react';

export interface ASRProvider {
  id: string;
  name: string;
  description?: string;
  status: 'online' | 'offline' | 'building';
  icon?: string;
  languages?: string[];
  capabilities?: {
    realtime?: boolean;
    translation?: boolean;
    punctuation?: boolean;
    diarization?: boolean;
  };
}

export interface ASRProviderSelectorProps {
  providers: ASRProvider[];
  selectedProviderId: string | null;
  onSelectProvider: (providerId: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  showOnlineOnly?: boolean;
  className?: string;
}

export const ASRProviderSelector: React.FC<ASRProviderSelectorProps> = ({
  providers,
  selectedProviderId,
  onSelectProvider,
  isLoading = false,
  disabled = false,
  showOnlineOnly = false,
  className = '',
}) => {
  // Ensure providers is an array (defensive check)
  const providersArray = Array.isArray(providers) ? providers : [];

  // Filter providers based on showOnlineOnly
  const filteredProviders = showOnlineOnly
    ? providersArray.filter((p) => p.status === 'online')
    : providersArray;

  const getStatusColor = (status: ASRProvider['status']) => {
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
          ASR Provider (Speech Recognition)
        </label>
        <div className="animate-pulse bg-gray-200 h-10 rounded-md"></div>
      </div>
    );
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        ASR Provider (Speech Recognition)
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
            {provider.languages && provider.languages.length > 0
              ? ` - ${provider.languages.length} languages`
              : ''}
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
                  <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                    {selected.capabilities.realtime && (
                      <span title="Real-time transcription" className="flex items-center bg-white px-2 py-1 rounded border border-gray-200">
                        ⚡ Real-time
                      </span>
                    )}
                    {selected.capabilities.translation && (
                      <span title="Translation support" className="flex items-center bg-white px-2 py-1 rounded border border-gray-200">
                        🌐 Translation
                      </span>
                    )}
                    {selected.capabilities.punctuation && (
                      <span title="Automatic punctuation" className="flex items-center bg-white px-2 py-1 rounded border border-gray-200">
                        ✏️ Punctuation
                      </span>
                    )}
                    {selected.capabilities.diarization && (
                      <span title="Speaker diarization" className="flex items-center bg-white px-2 py-1 rounded border border-gray-200">
                        👥 Diarization
                      </span>
                    )}
                  </div>
                )}

                {selected.languages && selected.languages.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <p className="text-xs text-gray-500 mb-1">Supported Languages:</p>
                    <div className="flex flex-wrap gap-1">
                      {selected.languages.slice(0, 5).map((lang) => (
                        <span
                          key={lang}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-white border border-gray-200"
                        >
                          {lang}
                        </span>
                      ))}
                      {selected.languages.length > 5 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs text-gray-500">
                          +{selected.languages.length - 5} more
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}

      {filteredProviders.length === 0 && (
        <p className="text-sm text-gray-500 italic">
          No ASR providers available. Please configure ASR providers first.
        </p>
      )}
    </div>
  );
};
