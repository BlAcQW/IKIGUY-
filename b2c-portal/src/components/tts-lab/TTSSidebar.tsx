/**
 * TTS Lab Sidebar Component
 *
 * Displays available TTS providers with real-time status monitoring.
 */

import React, { useState, useEffect } from 'react';
import { TTSProvider } from '../../config/tts-providers';

interface TTSSidebarProps {
  selectedProviderId: string | null;
  onSelectProvider: (providerId: string) => void;
  providers: Record<string, TTSProvider>;
  isLoadingProviders?: boolean;
  onRefresh?: () => void;
}

// Helper function to format relative time
const getRelativeTime = (timestamp: string | undefined): string => {
  if (!timestamp) return 'Never';

  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now.getTime() - then.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);

  if (diffSeconds < 60) return 'Just now';
  if (diffMinutes === 1) return '1 minute ago';
  if (diffMinutes < 60) return `${diffMinutes} minutes ago`;
  if (diffHours === 1) return '1 hour ago';
  if (diffHours < 24) return `${diffHours} hours ago`;
  return then.toLocaleDateString();
};

export const TTSSidebar: React.FC<TTSSidebarProps> = ({
  selectedProviderId,
  onSelectProvider,
  providers,
  isLoadingProviders = false,
  onRefresh,
}) => {
  const providerList = Object.values(providers);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update relative time display every 30 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  const getStatusBadge = (provider: any, isChecking: boolean = false) => {
    const status = provider.status || 'offline';
    const responseTime = provider.responseTime;

    // Add pulsing animation when checking status
    const pulseClass = isChecking ? 'animate-pulse' : '';

    const badges = {
      online: (
        <div className="flex items-center space-x-1">
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 ${pulseClass}`}>
            <span className="w-2 h-2 bg-green-400 rounded-full mr-1.5 animate-pulse"></span>
            Online
          </span>
          {responseTime && (
            <span className="text-xs text-gray-500">{responseTime}ms</span>
          )}
        </div>
      ),
      offline: (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 ${pulseClass}`}>
          <span className="w-2 h-2 bg-red-400 rounded-full mr-1.5"></span>
          Offline
        </span>
      ),
      building: (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800 ${pulseClass}`}>
          <span className="w-2 h-2 bg-yellow-400 rounded-full mr-1.5 animate-pulse"></span>
          Building
        </span>
      ),
      degraded: (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800 ${pulseClass}`}>
          <span className="w-2 h-2 bg-orange-400 rounded-full mr-1.5 animate-pulse"></span>
          Degraded
        </span>
      ),
    };
    return badges[status] || badges.offline;
  };

  const getCapabilityIcons = (capabilities: TTSProvider['capabilities']) => {
    const icons = [];
    if (capabilities.voiceCloning) {
      icons.push(
        <span key="clone" title="Voice Cloning" className="text-purple-600">
          🎭
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
    if (capabilities.multiSpeaker) {
      icons.push(
        <span key="speaker" title="Multi-Speaker" className="text-green-600">
          👥
        </span>
      );
    }
    if (capabilities.emotionControl) {
      icons.push(
        <span key="emotion" title="Emotion Control" className="text-pink-600">
          😊
        </span>
      );
    }
    return icons;
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-2xl font-bold text-gray-900">TTS Providers</h2>
          {onRefresh && (
            <button
              onClick={() => onRefresh()}
              disabled={isLoadingProviders}
              className="p-1 text-gray-500 hover:text-gray-700 disabled:opacity-50 transition-colors"
              title="Refresh provider status"
            >
              <svg
                className={`w-5 h-5 ${isLoadingProviders ? 'animate-spin' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>
          )}
        </div>
        <p className="mt-1 text-sm text-gray-500">
          Select a TTS provider to get started
        </p>
        {/* Show last update time for any provider */}
        {providerList.length > 0 && providerList[0].lastChecked && (
          <p className="mt-2 text-xs text-gray-400 flex items-center">
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Status updated {getRelativeTime(providerList[0].lastChecked)}
          </p>
        )}
      </div>

      {/* Provider List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {isLoadingProviders && providerList.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-gray-500">Loading providers...</div>
          </div>
        ) : (
          providerList.map((provider) => (
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
                <div>
                  <h3 className="font-semibold text-gray-900">{provider.name}</h3>
                  {provider.languages > 0 && (
                    <p className="text-xs text-gray-500">
                      {provider.languages} languages
                    </p>
                  )}
                </div>
              </div>
              {getStatusBadge(provider, isLoadingProviders)}
            </div>

            {/* Provider Description */}
            <p className="text-xs text-gray-600 mb-3">{provider.description}</p>

            {/* Capabilities */}
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-500">Capabilities:</span>
              <div className="flex space-x-1">
                {getCapabilityIcons(provider.capabilities)}
              </div>
            </div>

            {/* Additional Info */}
            {selectedProviderId === provider.id && (
              <div className="mt-3 pt-3 border-t border-indigo-200">
                <div className="text-xs text-gray-600 space-y-1">
                  <div className="flex items-center justify-between">
                    <span>Endpoint:</span>
                    <span className="font-mono text-indigo-600 truncate ml-2">
                      {provider.endpoint.replace('https://', '')}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
          ))
        )}
      </div>

      {/* Footer with Legend */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-xs text-gray-600 space-y-1">
          <p className="font-semibold mb-2">Capability Icons:</p>
          <div className="grid grid-cols-2 gap-2">
            <div className="flex items-center space-x-1">
              <span>🎭</span>
              <span>Voice Cloning</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>🌍</span>
              <span>Multi-Language</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>👥</span>
              <span>Multi-Speaker</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>😊</span>
              <span>Emotion Control</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
