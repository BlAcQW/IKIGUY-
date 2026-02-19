/**
 * ASR Lab Page
 *
 * Main interface for testing and using different ASR providers.
 * Layout consistent with TTSLab.tsx
 */

import React, { useState } from 'react';
import { useASRProvider } from '../hooks/useASRProvider';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { ASRSidebar } from '../components/asr-lab/ASRSidebar';
import { TranscriptionPanel } from '../components/asr-lab/TranscriptionPanel';
import { LiveTranscriptionPanel } from '../components/asr-lab/LiveTranscriptionPanel';
import { getStatusStyle } from '@/lib/status-utils';
import { ProviderSettings } from '../components/asr-lab/ProviderSettings';
import { withErrorBoundary } from '@/components/ErrorBoundary';

type TabType = 'transcribe' | 'live' | 'settings';

const ASRLabComponent: React.FC = () => {
  const {
    selectedProvider,
    setSelectedProvider,
    isLoading,
    error,
    transcribe,
    getLanguages,
    checkHealth,
  } = useASRProvider();

  const [activeTab, setActiveTab] = useState<TabType>('live');

  const availableTabs = [
    { id: 'live' as TabType, label: 'Live Transcription', icon: '🎤' },
    { id: 'transcribe' as TabType, label: 'Transcribe File', icon: '📁' },
    { id: 'settings' as TabType, label: 'Settings', icon: '⚙️' },
  ];

  const renderTabContent = () => {
    if (!selectedProvider) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-6xl mb-4">🎤</div>
            <h3 className="text-xl font-semibold text-gray-900">No Provider Selected</h3>
            <p className="text-gray-500 mt-2">
              Please select an ASR provider from the sidebar to get started
            </p>
          </div>
        </div>
      );
    }

    switch (activeTab) {
      case 'transcribe':
        return (
          <TranscriptionPanel
            provider={selectedProvider}
            onTranscribe={transcribe}
            isLoading={isLoading}
            error={error}
            getLanguages={getLanguages}
          />
        );

      case 'live':
        return (
          <LiveTranscriptionPanel
            provider={selectedProvider}
            onTranscribe={transcribe}
            isLoading={isLoading}
            error={error}
          />
        );

      case 'settings':
        return <ProviderSettings provider={selectedProvider} onCheckHealth={checkHealth} />;

      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Sidebar */}
      <DashboardSidebar />

      {/* Secondary Sidebar - ASR Providers */}
      <ASRSidebar
        selectedProviderId={selectedProvider?.id || null}
        onSelectProvider={setSelectedProvider}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">ASR Lab</h1>
              <p className="text-sm text-gray-500 mt-1">
                {selectedProvider
                  ? `Testing ${selectedProvider.name}`
                  : 'Select a provider to get started'}
              </p>
            </div>

            {selectedProvider && (() => {
              const statusStyle = getStatusStyle(selectedProvider.status);
              return (
                <div className="flex items-center space-x-2">
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusStyle.badge}`}
                  >
                    {statusStyle.dot} {statusStyle.label}
                  </span>
                </div>
              );
            })()}
          </div>
        </div>

        {/* Tabs */}
        {selectedProvider && (
          <div className="bg-white border-b border-gray-200">
            <div className="flex space-x-1 px-6">
              {availableTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    px-4 py-3 text-sm font-medium border-b-2 transition-colors
                    ${
                      activeTab === tab.id
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto bg-gray-50">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

// Wrap with ErrorBoundary for crash protection
export const ASRLab = withErrorBoundary(ASRLabComponent, {
  fallback: (
    <div className="flex items-center justify-center h-screen bg-gray-50">
      <div className="text-center p-6">
        <div className="text-6xl mb-4">⚠️</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">ASR Lab Error</h2>
        <p className="text-gray-600">
          Something went wrong with the ASR Lab. Please refresh the page to try again.
        </p>
      </div>
    </div>
  ),
});

export default ASRLab;
