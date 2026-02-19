/**
 * LLM Lab Page
 *
 * Main interface for testing and using different LLM models.
 * Layout consistent with TTSLab.tsx
 */

import React, { useState } from 'react';
import { useLLMModel } from '../hooks/useLLMModel';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { LLMSidebar } from '../components/llm-lab/LLMSidebar';
import { ChatPanel } from '../components/llm-lab/ChatPanel';

type TabType = 'chat' | 'settings';

export const LLMLab: React.FC = () => {
  const {
    selectedModel,
    setSelectedModel,
    isLoading,
    error,
    chat,
    chatStream,
    checkHealth,
    getModelInfo,
  } = useLLMModel();

  const [activeTab, setActiveTab] = useState<TabType>('chat');

  const availableTabs = [
    { id: 'chat' as TabType, label: 'Chat', icon: '💬' },
    { id: 'settings' as TabType, label: 'Settings', icon: '⚙️' },
  ];

  const renderTabContent = () => {
    if (!selectedModel) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-6xl mb-4">💬</div>
            <h3 className="text-xl font-semibold text-gray-900">No Model Selected</h3>
            <p className="text-gray-500 mt-2">
              Please select an LLM model from the sidebar to get started
            </p>
          </div>
        </div>
      );
    }

    switch (activeTab) {
      case 'chat':
        return (
          <ChatPanel
            model={selectedModel}
            onChat={chat}
            onChatStream={chatStream}
            isLoading={isLoading}
            error={error}
          />
        );

      case 'settings':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Model Settings</h2>

            {/* Model Info */}
            <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  {selectedModel.name}
                </h3>
                <p className="text-gray-600">{selectedModel.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  <p className="font-medium text-gray-900">
                    {selectedModel.status === 'online' && '🟢 Online'}
                    {selectedModel.status === 'training' && '🔵 Training'}
                    {selectedModel.status === 'building' && '🟡 Building'}
                    {selectedModel.status === 'offline' && '🔴 Offline'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Endpoint</p>
                  <p className="font-mono text-sm text-gray-900 truncate">
                    {selectedModel.endpoint}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Base Model</p>
                  <p className="font-mono text-sm text-gray-900 truncate">
                    {selectedModel.baseModel}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Model Size</p>
                  <p className="font-medium text-gray-900">
                    {selectedModel.modelSize}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Context Window</p>
                  <p className="font-medium text-gray-900">
                    {selectedModel.contextWindow
                      ? selectedModel.contextWindow >= 100000
                        ? `${(selectedModel.contextWindow / 1000).toFixed(0)}K`
                        : selectedModel.contextWindow.toLocaleString()
                      : 'N/A'}{' '}
                    tokens
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Max Tokens</p>
                  <p className="font-medium text-gray-900">
                    {selectedModel.maxTokens?.toLocaleString() || 'N/A'} tokens
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Languages</p>
                  <p className="font-medium text-gray-900">
                    {selectedModel.languages} supported
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Model ID</p>
                  <p className="font-mono text-sm text-gray-900">
                    {selectedModel.id}
                  </p>
                </div>
              </div>

              {/* Cost Information */}
              {selectedModel.cost && (
                <div className="pt-4 border-t">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Pricing</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-blue-50 rounded-lg p-3">
                      <p className="text-xs text-blue-600 font-medium mb-1">Input</p>
                      <p className="text-lg font-bold text-blue-900">
                        ${selectedModel.cost.input}
                      </p>
                      <p className="text-xs text-blue-600">per 1K tokens</p>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-3">
                      <p className="text-xs text-purple-600 font-medium mb-1">Output</p>
                      <p className="text-lg font-bold text-purple-900">
                        ${selectedModel.cost.output}
                      </p>
                      <p className="text-xs text-purple-600">per 1K tokens</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Fine-tuning Info */}
              {selectedModel.fineTuned && selectedModel.trainingData && (
                <div className="pt-4 border-t">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Fine-tuning Details</h4>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-purple-600">🇬🇭</span>
                      <span className="text-sm font-medium text-purple-900">
                        Ghanaian Cultural Fine-tuning
                      </span>
                    </div>
                    <p className="text-sm text-purple-800">{selectedModel.trainingData}</p>
                  </div>
                </div>
              )}

              {/* Capabilities */}
              <div className="pt-4 border-t">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Capabilities</h4>
                <div className="grid grid-cols-2 gap-2">
                  <div
                    className={`
                      flex items-center space-x-2 px-3 py-2 rounded-lg
                      ${
                        selectedModel.capabilities.streaming
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                      }
                    `}
                  >
                    <span>{selectedModel.capabilities.streaming ? '✓' : '✗'}</span>
                    <span className="text-sm">Streaming</span>
                  </div>
                  <div
                    className={`
                      flex items-center space-x-2 px-3 py-2 rounded-lg
                      ${
                        selectedModel.capabilities.multiLanguage
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                      }
                    `}
                  >
                    <span>{selectedModel.capabilities.multiLanguage ? '✓' : '✗'}</span>
                    <span className="text-sm">Multi-Language</span>
                  </div>
                  <div
                    className={`
                      flex items-center space-x-2 px-3 py-2 rounded-lg
                      ${
                        selectedModel.capabilities.culturalContext
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                      }
                    `}
                  >
                    <span>{selectedModel.capabilities.culturalContext ? '✓' : '✗'}</span>
                    <span className="text-sm">Cultural Context</span>
                  </div>
                  <div
                    className={`
                      flex items-center space-x-2 px-3 py-2 rounded-lg
                      ${
                        selectedModel.capabilities.functionCalling
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                      }
                    `}
                  >
                    <span>{selectedModel.capabilities.functionCalling ? '✓' : '✗'}</span>
                    <span className="text-sm">Function Calling</span>
                  </div>
                  <div
                    className={`
                      flex items-center space-x-2 px-3 py-2 rounded-lg
                      ${
                        selectedModel.capabilities.reasoning
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                      }
                    `}
                  >
                    <span>{selectedModel.capabilities.reasoning ? '✓' : '✗'}</span>
                    <span className="text-sm">Reasoning</span>
                  </div>
                  <div
                    className={`
                      flex items-center space-x-2 px-3 py-2 rounded-lg
                      ${
                        selectedModel.capabilities.codeGeneration
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                      }
                    `}
                  >
                    <span>{selectedModel.capabilities.codeGeneration ? '✓' : '✗'}</span>
                    <span className="text-sm">Code Generation</span>
                  </div>
                  <div
                    className={`
                      flex items-center space-x-2 px-3 py-2 rounded-lg
                      ${
                        selectedModel.capabilities.vision
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                      }
                    `}
                  >
                    <span>{selectedModel.capabilities.vision ? '✓' : '✗'}</span>
                    <span className="text-sm">Vision</span>
                  </div>
                </div>
              </div>

              {/* Health Check */}
              <div className="pt-4 border-t">
                <button
                  onClick={async () => {
                    const healthy = await checkHealth();
                    alert(healthy ? '✓ Model is healthy' : '✗ Model is not responding');
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

      {/* Secondary Sidebar - LLM Models */}
      <LLMSidebar
        selectedModelId={selectedModel?.id || null}
        onSelectModel={setSelectedModel}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">LLM Lab</h1>
              <p className="text-sm text-gray-500 mt-1">
                {selectedModel
                  ? `Chatting with ${selectedModel.name}`
                  : 'Select a model to get started'}
              </p>
            </div>

            {selectedModel && (
              <div className="flex items-center space-x-2">
                <span
                  className={`
                    inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
                    ${
                      selectedModel.status === 'online'
                        ? 'bg-green-100 text-green-800'
                        : selectedModel.status === 'training'
                        ? 'bg-blue-100 text-blue-800'
                        : selectedModel.status === 'building'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }
                  `}
                >
                  {selectedModel.status === 'online' && '🟢 Online'}
                  {selectedModel.status === 'training' && '🔵 Training'}
                  {selectedModel.status === 'building' && '🟡 Building'}
                  {selectedModel.status === 'offline' && '🔴 Offline'}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        {selectedModel && (
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
        <div className="flex-1 overflow-hidden bg-gray-50">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

export default LLMLab;
