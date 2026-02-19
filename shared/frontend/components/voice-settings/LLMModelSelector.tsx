/**
 * LLM Model Selector Component
 *
 * Compact selector for choosing LLM model in settings.
 * Part of @kasaai/shared-frontend library.
 */

import React from 'react';

export interface LLMModel {
  id: string;
  name: string;
  description?: string;
  provider: string;
  contextWindow?: number;
  icon?: string;
  capabilities?: {
    functionCalling?: boolean;
    streaming?: boolean;
    multimodal?: boolean;
    json?: boolean;
  };
  pricing?: {
    inputCostPer1M?: number;
    outputCostPer1M?: number;
  };
}

export interface LLMModelSelectorProps {
  models: LLMModel[];
  selectedModelId: string | null;
  onSelectModel: (modelId: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  groupByProvider?: boolean;
  className?: string;
}

export const LLMModelSelector: React.FC<LLMModelSelectorProps> = ({
  models,
  selectedModelId,
  onSelectModel,
  isLoading = false,
  disabled = false,
  groupByProvider = true,
  className = '',
}) => {
  // Group models by provider if requested
  const groupedModels = React.useMemo(() => {
    if (!groupByProvider) return { All: models };

    const groups: Record<string, LLMModel[]> = {};
    models.forEach((model) => {
      if (!groups[model.provider]) {
        groups[model.provider] = [];
      }
      groups[model.provider].push(model);
    });
    return groups;
  }, [models, groupByProvider]);

  const formatContextWindow = (tokens?: number) => {
    if (!tokens) return '';
    if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`;
    if (tokens >= 1000) return `${(tokens / 1000).toFixed(0)}K`;
    return tokens.toString();
  };

  if (isLoading) {
    return (
      <div className={`space-y-2 ${className}`}>
        <label className="block text-sm font-medium text-gray-700">
          LLM Model
        </label>
        <div className="animate-pulse bg-gray-200 h-10 rounded-md"></div>
      </div>
    );
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        LLM Model
      </label>

      <select
        value={selectedModelId || ''}
        onChange={(e) => onSelectModel(e.target.value)}
        disabled={disabled}
        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <option value="">Select a model...</option>
        {Object.entries(groupedModels).map(([provider, providerModels]) => (
          <optgroup key={provider} label={provider}>
            {providerModels.map((model) => (
              <option key={model.id} value={model.id}>
                {model.icon ? `${model.icon} ` : ''}
                {model.name}
                {model.contextWindow
                  ? ` (${formatContextWindow(model.contextWindow)} ctx)`
                  : ''}
              </option>
            ))}
          </optgroup>
        ))}
      </select>

      {/* Model Info Card (shown when model is selected) */}
      {selectedModelId && models.find((m) => m.id === selectedModelId) && (
        <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-md">
          {(() => {
            const selected = models.find((m) => m.id === selectedModelId);
            if (!selected) return null;

            return (
              <>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {selected.icon && <span className="text-xl">{selected.icon}</span>}
                    <div>
                      <span className="font-medium text-gray-900">{selected.name}</span>
                      <p className="text-xs text-gray-500">{selected.provider}</p>
                    </div>
                  </div>
                  {selected.contextWindow && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      {formatContextWindow(selected.contextWindow)} context
                    </span>
                  )}
                </div>

                {selected.description && (
                  <p className="text-sm text-gray-600 mb-2">{selected.description}</p>
                )}

                {selected.capabilities && (
                  <div className="flex flex-wrap gap-2 text-xs text-gray-500 mb-2">
                    {selected.capabilities.functionCalling && (
                      <span className="flex items-center bg-white px-2 py-1 rounded border border-gray-200">
                        🔧 Function Calling
                      </span>
                    )}
                    {selected.capabilities.streaming && (
                      <span className="flex items-center bg-white px-2 py-1 rounded border border-gray-200">
                        ⚡ Streaming
                      </span>
                    )}
                    {selected.capabilities.multimodal && (
                      <span className="flex items-center bg-white px-2 py-1 rounded border border-gray-200">
                        🖼️ Multimodal
                      </span>
                    )}
                    {selected.capabilities.json && (
                      <span className="flex items-center bg-white px-2 py-1 rounded border border-gray-200">
                        📋 JSON Mode
                      </span>
                    )}
                  </div>
                )}

                {selected.pricing && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <p className="text-xs text-gray-500 mb-1">Pricing:</p>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {selected.pricing.inputCostPer1M !== undefined && (
                        <div>
                          <span className="text-gray-500">Input:</span>{' '}
                          <span className="font-medium">
                            ${selected.pricing.inputCostPer1M.toFixed(2)}/1M tokens
                          </span>
                        </div>
                      )}
                      {selected.pricing.outputCostPer1M !== undefined && (
                        <div>
                          <span className="text-gray-500">Output:</span>{' '}
                          <span className="font-medium">
                            ${selected.pricing.outputCostPer1M.toFixed(2)}/1M tokens
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}

      {models.length === 0 && (
        <p className="text-sm text-gray-500 italic">
          No LLM models available. Please configure LLM models first.
        </p>
      )}
    </div>
  );
};
