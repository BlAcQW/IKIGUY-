/**
 * LLM Lab Sidebar Component
 *
 * Displays available LLM models similar to TTS Lab sidebar.
 */

import React from 'react';
import { LLMModel, LLM_MODELS } from '../../config/llm-models';

interface LLMSidebarProps {
  selectedModelId: string | null;
  onSelectModel: (modelId: string) => void;
}

export const LLMSidebar: React.FC<LLMSidebarProps> = ({
  selectedModelId,
  onSelectModel,
}) => {
  const models = Object.values(LLM_MODELS);

  // Group models by type
  const fineTunedModels = models.filter(m => m.fineTuned);
  const baseModels = models.filter(m => !m.fineTuned);

  const getStatusBadge = (status: LLMModel['status']) => {
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
      training: (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
          Training
        </span>
      ),
    };
    return badges[status];
  };

  const getCapabilityIcons = (capabilities: LLMModel['capabilities']) => {
    const icons = [];
    if (capabilities.streaming) {
      icons.push(
        <span key="streaming" title="Streaming" className="text-blue-600">
          🌊
        </span>
      );
    }
    if (capabilities.culturalContext) {
      icons.push(
        <span key="cultural" title="Cultural Context" className="text-purple-600">
          🇬🇭
        </span>
      );
    }
    if (capabilities.functionCalling) {
      icons.push(
        <span key="function" title="Function Calling" className="text-green-600">
          🔧
        </span>
      );
    }
    if (capabilities.vision) {
      icons.push(
        <span key="vision" title="Vision" className="text-pink-600">
          👁️
        </span>
      );
    }
    if (capabilities.codeGeneration) {
      icons.push(
        <span key="code" title="Code Generation" className="text-orange-600">
          💻
        </span>
      );
    }
    return icons;
  };

  const renderModelGroup = (title: string, modelList: LLMModel[]) => {
    if (modelList.length === 0) return null;

    return (
      <div className="mb-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide px-2 mb-2">
          {title}
        </h3>
        <div className="space-y-2">
          {modelList.map((model) => (
            <div
              key={model.id}
              onClick={() => onSelectModel(model.id)}
              className={`
                p-4 rounded-lg cursor-pointer transition-all duration-200
                ${
                  selectedModelId === model.id
                    ? 'bg-indigo-50 border-2 border-indigo-500 shadow-md'
                    : 'bg-white border border-gray-200 hover:border-indigo-300 hover:shadow-sm'
                }
                ${model.status !== 'online' ? 'opacity-60' : ''}
              `}
            >
              {/* Model Header */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{model.icon}</span>
                  <div>
                    <h4 className="font-semibold text-gray-900 text-sm">{model.name}</h4>
                    {model.fineTuned && (
                      <span className="text-xs text-purple-600 font-medium">Fine-tuned</span>
                    )}
                  </div>
                </div>
                {getStatusBadge(model.status)}
              </div>

              {/* Model Description */}
              <p className="text-xs text-gray-600 mb-3 line-clamp-2">
                {model.description}
              </p>

              {/* Model Stats */}
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div className="text-xs">
                  <span className="text-gray-500">Size:</span>
                  <span className="ml-1 font-medium text-gray-900">
                    {model.modelSize}
                  </span>
                </div>
                <div className="text-xs">
                  <span className="text-gray-500">Context:</span>
                  <span className="ml-1 font-medium text-gray-900">
                    {model.contextWindow
                      ? model.contextWindow >= 100000
                        ? `${(model.contextWindow / 1000).toFixed(0)}K`
                        : model.contextWindow.toLocaleString()
                      : 'N/A'}
                  </span>
                </div>
                <div className="text-xs">
                  <span className="text-gray-500">Languages:</span>
                  <span className="ml-1 font-medium text-gray-900">
                    {model.languages}
                  </span>
                </div>
                {model.cost && (
                  <div className="text-xs">
                    <span className="text-gray-500">Cost:</span>
                    <span className="ml-1 font-medium text-gray-900">
                      ${model.cost.input}/1K
                    </span>
                  </div>
                )}
              </div>

              {/* Capabilities */}
              <div className="flex items-center space-x-2">
                {getCapabilityIcons(model.capabilities)}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900">LLM Models</h2>
        <p className="mt-1 text-sm text-gray-500">
          Select an LLM model to chat
        </p>
      </div>

      {/* Model List */}
      <div className="flex-1 overflow-y-auto p-4">
        {renderModelGroup('🇬🇭 Fine-tuned Ghanaian Models', fineTunedModels)}
        {renderModelGroup('🌐 Base Models', baseModels)}
      </div>

      {/* Footer Stats */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-xs text-gray-600">
          <div className="flex justify-between mb-1">
            <span>Fine-tuned Models:</span>
            <span className="font-medium text-purple-600">
              {fineTunedModels.length}
            </span>
          </div>
          <div className="flex justify-between mb-1">
            <span>Online Models:</span>
            <span className="font-medium text-green-600">
              {models.filter(m => m.status === 'online').length}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Total Models:</span>
            <span className="font-medium text-gray-900">{models.length}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
