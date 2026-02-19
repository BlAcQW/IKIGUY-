/**
 * TTS Lab Page
 *
 * Main interface for testing and using different TTS providers.
 * Layout inspired by KnowledgeBase.tsx with sidebar for provider selection.
 */

import React, { useState } from 'react';
import { useTTSProvider } from '../hooks/useTTSProvider';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { TTSSidebar } from '../components/tts-lab/TTSSidebar';
import { SynthesizePanel } from '../components/tts-lab/SynthesizePanel';
import { VoiceCloningPanel } from '../components/tts-lab/VoiceCloningPanel';
import { BatchPanel } from '../components/tts-lab/BatchPanel';
import { VoiceComparisonPanel } from '../components/tts-lab/VoiceComparisonPanel';
import { ModelManagementPanel } from '../components/tts-lab/ModelManagementPanel';

type TabType = 'synthesize' | 'voice-cloning' | 'batch' | 'comparison' | 'conversation' | 'models' | 'settings' | 'advanced' | 'scraper';

export const TTSLab: React.FC = () => {
  const {
    selectedProvider,
    setSelectedProvider,
    providers,
    isLoading,
    error,
    isLoadingProviders,
    refreshProviders,
    synthesize,
    synthesizeWithVoiceCloning,
    estimateCost,
    getLanguages,
    getSpeakers,
    checkHealth,
  } = useTTSProvider();

  const [activeTab, setActiveTab] = useState<TabType>('synthesize');

  // Determine available tabs based on provider capabilities
  const getAvailableTabs = () => {
    if (!selectedProvider) return [];

    const tabs: { id: TabType; label: string; icon: string }[] = [];

    // Crawl4AI has different tabs - web scraping focused
    if (selectedProvider.id === 'crawl4ai') {
      tabs.push({ id: 'scraper', label: 'Web Scraper', icon: '🕷️' });
      tabs.push({ id: 'settings', label: 'Settings', icon: '⚙️' });
      return tabs;
    }

    // Standard TTS tabs
    tabs.push({ id: 'synthesize', label: 'Synthesize', icon: '🎵' });

    // Voice cloning tab for supported providers
    if (selectedProvider.capabilities.voiceCloning) {
      tabs.push({ id: 'voice-cloning', label: 'Voice Cloning', icon: '🎭' });
    }

    // Batch synthesis tab (available for all providers)
    tabs.push({ id: 'batch', label: 'Batch Synthesis', icon: '📋' });

    // Voice comparison tab (available for all providers)
    tabs.push({ id: 'comparison', label: 'Voice Comparison', icon: '🔀' });

    // Real-time conversation tab for Moshi
    if (selectedProvider.capabilities.realTimeConversation) {
      tabs.push({ id: 'conversation', label: 'Conversation', icon: '💬' });
    }

    // Advanced features tab for StyleTTS2, F5-TTS, Moshi
    if (['styletts2', 'f5tts', 'moshi'].includes(selectedProvider.id)) {
      tabs.push({ id: 'advanced', label: 'Advanced', icon: '⚙️' });
    }

    tabs.push({ id: 'models', label: 'Models', icon: '📦' });
    tabs.push({ id: 'settings', label: 'Settings', icon: '🔧' });

    return tabs;
  };

  const availableTabs = getAvailableTabs();

  // Ensure active tab is valid for current provider
  React.useEffect(() => {
    if (!availableTabs.find((tab) => tab.id === activeTab)) {
      // Set default tab based on provider type
      if (selectedProvider?.id === 'crawl4ai') {
        setActiveTab('scraper');
      } else {
        setActiveTab('synthesize');
      }
    }
  }, [selectedProvider?.id, activeTab, availableTabs]);

  const renderTabContent = () => {
    if (!selectedProvider) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-6xl mb-4">🎙️</div>
            <h3 className="text-xl font-semibold text-gray-900">No Provider Selected</h3>
            <p className="text-gray-500 mt-2">
              Please select a TTS provider from the sidebar to get started
            </p>
          </div>
        </div>
      );
    }

    switch (activeTab) {
      case 'synthesize':
        return (
          <SynthesizePanel
            provider={selectedProvider}
            onSynthesize={synthesize}
            isLoading={isLoading}
            error={error}
            getLanguages={getLanguages}
            getSpeakers={getSpeakers}
            estimateCost={estimateCost}
          />
        );

      case 'voice-cloning':
        return (
          <VoiceCloningPanel
            provider={selectedProvider}
            onSynthesize={synthesizeWithVoiceCloning}
            isLoading={isLoading}
            error={error}
            getLanguages={getLanguages}
          />
        );

      case 'batch':
        return (
          <BatchPanel
            provider={selectedProvider}
            getLanguages={getLanguages}
            getSpeakers={getSpeakers}
          />
        );

      case 'comparison':
        return (
          <VoiceComparisonPanel
            provider={selectedProvider}
            providers={providers}
            synthesize={synthesize}
            getLanguages={getLanguages}
            getSpeakers={getSpeakers}
          />
        );

      case 'conversation':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              ⚡ Real-Time Conversation
            </h2>

            {/* Success Message */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <span className="text-2xl mr-3">✅</span>
                <div>
                  <h4 className="font-semibold text-green-800 mb-1">Moshi Successfully Deployed</h4>
                  <p className="text-green-700 text-sm">
                    Moshi is now running on RunPod with NVIDIA A40 GPU (46GB VRAM).
                    Using approximately 15GB of GPU memory with both language model and Mimi audio codec loaded.
                    Ready for real-time bidirectional conversation via WebSocket at /ws/conversation.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200 p-8">
              <div className="text-center mb-6">
                <div className="text-6xl mb-4">💬</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Moshi - Full-Duplex Conversational AI
                </h3>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  Experience real-time bidirectional conversation with Moshi. Speak naturally while Moshi
                  listens and responds simultaneously, just like a human conversation.
                </p>
              </div>

              <div className="bg-white rounded-lg p-6 mb-6">
                <h4 className="font-semibold text-gray-900 mb-4">Features:</h4>
                <ul className="space-y-2 text-gray-700">
                  <li className="flex items-start">
                    <span className="text-green-500 mr-2">✓</span>
                    <span><strong>Ultra-Low Latency:</strong> Less than 200ms response time</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-green-500 mr-2">✓</span>
                    <span><strong>Full-Duplex:</strong> Speak and listen simultaneously</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-green-500 mr-2">✓</span>
                    <span><strong>Natural Interruption:</strong> Can interrupt and be interrupted naturally</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-green-500 mr-2">✓</span>
                    <span><strong>Streaming Audio:</strong> Real-time audio processing via WebSocket</span>
                  </li>
                </ul>
              </div>

              <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <span className="text-2xl">🔌</span>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-blue-700">
                      <strong>API Ready:</strong> The WebSocket endpoint is available at <code className="bg-blue-100 px-1 rounded">/ws/conversation</code>.
                      Full client interface implementation is in progress.
                    </p>
                  </div>
                </div>
              </div>

              <div className="text-center">
                <button
                  className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  onClick={() => {
                    alert('WebSocket endpoint ready at wss://moshi.ailabsafrica.com/ws/conversation\n\nClient interface coming soon!');
                  }}
                >
                  View WebSocket Details
                </button>
              </div>
            </div>
          </div>
        );

      case 'models':
        return <ModelManagementPanel provider={selectedProvider} />;

      case 'advanced':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Advanced Features</h2>

            <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
              {/* StyleTTS2 Advanced Features */}
              {selectedProvider.id === 'styletts2' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Style Control</h3>
                  <p className="text-gray-600 mb-4">
                    StyleTTS2 offers advanced prosody and emotion modeling for expressive speech synthesis.
                  </p>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Emotion Intensity
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        className="w-full"
                        disabled
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Control the emotional intensity of the generated speech
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Speaking Style
                      </label>
                      <select className="w-full px-3 py-2 border border-gray-300 rounded-lg" disabled>
                        <option>Neutral</option>
                        <option>Expressive</option>
                        <option>Calm</option>
                        <option>Energetic</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* F5-TTS Advanced Features */}
              {selectedProvider.id === 'f5tts' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Diffusion Parameters</h3>
                  <p className="text-gray-600 mb-4">
                    F5-TTS uses flow-matching for high-quality synthesis. Adjust sampling parameters.
                  </p>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Inference Steps
                      </label>
                      <input
                        type="number"
                        min="10"
                        max="100"
                        defaultValue="32"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        disabled
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        More steps = higher quality but slower generation
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Guidance Scale
                      </label>
                      <input
                        type="range"
                        min="1"
                        max="20"
                        defaultValue="7"
                        step="0.5"
                        className="w-full"
                        disabled
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Controls adherence to the text prompt
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Moshi Advanced Features */}
              {selectedProvider.id === 'moshi' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Real-Time Configuration</h3>
                  <p className="text-gray-600 mb-4">
                    Kyutai/Moshi is optimized for ultra-low latency real-time conversations.
                  </p>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Latency Mode
                      </label>
                      <select className="w-full px-3 py-2 border border-gray-300 rounded-lg" disabled>
                        <option>Ultra Low (50ms)</option>
                        <option>Low (100ms)</option>
                        <option>Balanced (200ms)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Streaming Chunk Size
                      </label>
                      <input
                        type="number"
                        min="256"
                        max="2048"
                        defaultValue="512"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        disabled
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Smaller chunks = lower latency but more overhead
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="pt-4 border-t">
                <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg">
                  ⚠️ Advanced features are currently in development and will be enabled once the
                  provider is fully deployed.
                </p>
              </div>
            </div>
          </div>
        );

      case 'scraper':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Web Content Scraper</h2>

            <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
              <div>
                <p className="text-gray-600 mb-4">
                  Extract clean text content from web pages for TTS processing. Crawl4AI handles
                  JavaScript rendering, DOM parsing, and content extraction.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  URL to Scrape
                </label>
                <input
                  type="url"
                  placeholder="https://example.com/article"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  disabled
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Content Extraction Mode
                </label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-lg" disabled>
                  <option>Main Content Only</option>
                  <option>Full Page Text</option>
                  <option>Article Body</option>
                  <option>Custom Selector</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <input type="checkbox" id="remove-ads" className="rounded" disabled />
                <label htmlFor="remove-ads" className="text-sm text-gray-700">
                  Remove advertisements and popups
                </label>
              </div>

              <div className="flex items-center space-x-2">
                <input type="checkbox" id="wait-js" className="rounded" disabled />
                <label htmlFor="wait-js" className="text-sm text-gray-700">
                  Wait for JavaScript to load (slower but more complete)
                </label>
              </div>

              <button
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled
              >
                Extract Content
              </button>

              <div className="pt-4 border-t">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Extracted Content</h4>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 min-h-[200px]">
                  <p className="text-sm text-gray-500 italic">
                    Extracted content will appear here...
                  </p>
                </div>
              </div>

              <div className="pt-4 border-t">
                <p className="text-sm text-blue-600 bg-blue-50 p-3 rounded-lg">
                  💡 Tip: Use Crawl4AI to extract article text, then paste into any TTS provider
                  for audio generation.
                </p>
              </div>
            </div>
          </div>
        );

      case 'settings':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Provider Settings</h2>

            {/* Provider Info */}
            <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  {selectedProvider.name}
                </h3>
                <p className="text-gray-600">{selectedProvider.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  <p className="font-medium text-gray-900">
                    {selectedProvider.status === 'online' ? '🟢 Online' : '🔴 Offline'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Endpoint</p>
                  <p className="font-mono text-sm text-gray-900 truncate">
                    {selectedProvider.endpoint}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Languages</p>
                  <p className="font-medium text-gray-900">
                    {selectedProvider.languages} supported
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Provider ID</p>
                  <p className="font-mono text-sm text-gray-900">
                    {selectedProvider.id}
                  </p>
                </div>
              </div>

              {/* Capabilities */}
              <div className="pt-4 border-t">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Capabilities</h4>
                <div className="grid grid-cols-2 gap-2">
                  <div
                    className={`
                      flex items-center space-x-2 px-3 py-2 rounded-lg
                      ${
                        selectedProvider.capabilities.voiceCloning
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                      }
                    `}
                  >
                    <span>{selectedProvider.capabilities.voiceCloning ? '✓' : '✗'}</span>
                    <span className="text-sm">Voice Cloning</span>
                  </div>
                  <div
                    className={`
                      flex items-center space-x-2 px-3 py-2 rounded-lg
                      ${
                        selectedProvider.capabilities.multiLanguage
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                      }
                    `}
                  >
                    <span>{selectedProvider.capabilities.multiLanguage ? '✓' : '✗'}</span>
                    <span className="text-sm">Multi-Language</span>
                  </div>
                  <div
                    className={`
                      flex items-center space-x-2 px-3 py-2 rounded-lg
                      ${
                        selectedProvider.capabilities.speedControl
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                      }
                    `}
                  >
                    <span>{selectedProvider.capabilities.speedControl ? '✓' : '✗'}</span>
                    <span className="text-sm">Speed Control</span>
                  </div>
                  <div
                    className={`
                      flex items-center space-x-2 px-3 py-2 rounded-lg
                      ${
                        selectedProvider.capabilities.multiSpeaker
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                      }
                    `}
                  >
                    <span>{selectedProvider.capabilities.multiSpeaker ? '✓' : '✗'}</span>
                    <span className="text-sm">Multi-Speaker</span>
                  </div>
                </div>
              </div>

              {/* Health Check */}
              <div className="pt-4 border-t">
                <button
                  onClick={async () => {
                    const healthy = await checkHealth();
                    alert(healthy ? '✓ Provider is healthy' : '✗ Provider is not responding');
                  }}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
                >
                  Run Health Check
                </button>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Sidebar */}
      <DashboardSidebar />

      {/* Secondary Sidebar - TTS Providers */}
      <TTSSidebar
        selectedProviderId={selectedProvider?.id || null}
        onSelectProvider={setSelectedProvider}
        providers={providers}
        isLoadingProviders={isLoadingProviders}
        onRefresh={() => refreshProviders(true)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">TTS Lab</h1>
              <p className="text-sm text-gray-500 mt-1">
                {selectedProvider
                  ? `Testing ${selectedProvider.name}`
                  : 'Select a provider to get started'}
              </p>
            </div>

            {selectedProvider && (
              <div className="flex items-center space-x-2">
                <span
                  className={`
                    inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
                    ${
                      selectedProvider.status === 'online'
                        ? 'bg-green-100 text-green-800'
                        : selectedProvider.status === 'building'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }
                  `}
                >
                  {selectedProvider.status === 'online' && '🟢 Online'}
                  {selectedProvider.status === 'building' && '🟡 Building'}
                  {selectedProvider.status === 'offline' && '🔴 Offline'}
                </span>
              </div>
            )}
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

export default TTSLab;
