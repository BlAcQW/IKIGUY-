/**
 * ASR Lab Sidebar Component
 *
 * Displays available ASR providers similar to TTS Lab sidebar.
 */

import React from 'react';
import { ASRProvider, ASR_PROVIDERS } from '../../config/asr-providers';

interface ASRSidebarProps {
  selectedProviderId: string | null;
  onSelectProvider: (providerId: string) => void;
}

export const ASRSidebar: React.FC<ASRSidebarProps> = ({
  selectedProviderId,
  onSelectProvider,
}) => {
  const providers = Object.values(ASR_PROVIDERS);

  const getStatusBadge = (status: ASRProvider['status']) => {
    const badges = {
      online: (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
          Online
        </span>
      ),
      offline: (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
          Offline
        </span>
      ),
      building: (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
          Building
        </span>
      ),
    };
    return badges[status];
  };

  const getCapabilityIcons = (capabilities: ASRProvider['capabilities']) => {
    const icons = [];
    // Guard against undefined capabilities
    if (!capabilities) return icons;

    if (capabilities.realtime) {
      icons.push(
        <span key="realtime" title="Real-time" className="text-green-600">
          ⚡
        </span>
      );
    }
    if (capabilities.multiLanguage) {
      icons.push(
        <span key="lang" title="Multi-Language" className="text-blue-600">
          🌍
        </span>
      );
    }
    if (capabilities.diarization) {
      icons.push(
        <span key="diarization" title="Speaker Diarization" className="text-purple-600">
          👥
        </span>
      );
    }
    if (capabilities.wordLevelTimestamps) {
      icons.push(
        <span key="timestamps" title="Word-level Timestamps" className="text-orange-600">
          ⏱️
        </span>
      );
    }
    return icons;
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900">ASR Providers</h2>
        <p className="mt-1 text-sm text-gray-500">
          Select an ASR provider to get started
        </p>
      </div>

      {/* Provider List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {providers.map((provider) => (
          <div
            key={provider.id}
            onClick={() => onSelectProvider(provider.id)}
            className={`
              p-4 rounded-lg cursor-pointer transition-all duration-200
              ${
                selectedProviderId === provider.id
                  ? 'bg-indigo-50 border-2 border-indigo-500 shadow-md'
                  : 'bg-white border border-gray-200 hover:border-indigo-300 hover:shadow-sm'
              }
              ${provider.status !== 'online' ? 'opacity-60' : ''}
            `}
          >
            {/* Provider Header */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">{provider.icon}</span>
                <h3 className="font-semibold text-gray-900">{provider.name}</h3>
              </div>
              {getStatusBadge(provider.status)}
            </div>

            {/* Provider Description */}
            <p className="text-xs text-gray-600 mb-3 line-clamp-2">
              {provider.description}
            </p>

            {/* Provider Stats */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="text-xs">
                <span className="text-gray-500">Languages:</span>
                <span className="ml-1 font-medium text-gray-900">
                  {provider.languages}+
                </span>
              </div>
              {provider.latency && (
                <div className="text-xs">
                  <span className="text-gray-500">Latency:</span>
                  <span className="ml-1 font-medium text-gray-900">
                    {provider.latency}
                  </span>
                </div>
              )}
            </div>

            {/* Capabilities */}
            <div className="flex items-center space-x-2">
              {getCapabilityIcons(provider.capabilities)}
            </div>
          </div>
        ))}
      </div>

      {/* Footer Stats */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-xs text-gray-600">
          <div className="flex justify-between mb-1">
            <span>Online Providers:</span>
            <span className="font-medium text-green-600">
              {providers.filter(p => p.status === 'online').length}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Total Providers:</span>
            <span className="font-medium text-gray-900">{providers.length}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
