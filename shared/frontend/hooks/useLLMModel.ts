/**
 * Custom hook for managing LLM model state and API calls
 *
 * Refactored to use centralized backend API with automatic billing and health monitoring.
 * All LLM requests now go through /api/llm/* endpoints instead of direct Ollama calls.
 */

import { useState, useCallback, useEffect } from 'react';
import { API_ENDPOINTS } from '../config/api-config';

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatRequest {
  messages: ChatMessage[];
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  streaming?: boolean;
  systemPrompt?: string;
}

interface ChatResponse {
  message: string;
  modelId: string;
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  finishReason: string;
  cost: number;
  transactionId?: string;
  processingTime: number;
}

interface LLMProvider {
  id: string;
  name: string;
  endpoint: string;
  status: 'online' | 'offline' | 'degraded';
  last_check: string;
  response_time_ms: number | null;
  error_message: string | null;
  provider_type: 'llm';
}

interface ProvidersResponse {
  providers: Record<string, LLMProvider>;
  count: number;
  online_count: number;
  offline_count: number;
}

interface UseLLMModelReturn {
  selectedModel: LLMProvider | null;
  providers: Record<string, LLMProvider>;
  setSelectedModel: (modelId: string) => void;
  isLoading: boolean;
  error: string | null;
  chat: (request: ChatRequest) => Promise<ChatResponse | null>;
  chatStream: (
    request: ChatRequest,
    onChunk: (chunk: string) => void
  ) => Promise<void>;
  refreshProviders: (forceRefresh?: boolean) => Promise<void>;
  estimateCost: (inputText: string) => Promise<number | null>;
}

export const useLLMModel = (): UseLLMModelReturn => {
  const [providers, setProviders] = useState<Record<string, LLMProvider>>({});
  const [selectedModel, setSelectedModelState] = useState<LLMProvider | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch providers on mount and set up auto-refresh
  useEffect(() => {
    refreshProviders(false);

    // Auto-refresh every 60 seconds (to match backend cache TTL)
    const interval = setInterval(() => {
      refreshProviders(false);
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  // Auto-select first online provider when providers load
  useEffect(() => {
    if (Object.keys(providers).length > 0 && !selectedModel) {
      // Find first online provider
      const onlineProvider = Object.values(providers).find(p => p.status === 'online');
      if (onlineProvider) {
        setSelectedModelState(onlineProvider);
      }
    }
  }, [providers, selectedModel]);

  const refreshProviders = useCallback(async (forceRefresh: boolean = false) => {
    try {
      const url = `${API_ENDPOINTS.llm.providers}${forceRefresh ? '?force_refresh=true' : ''}`;
      const response = await fetch(url, {
        credentials: 'include', // Include auth cookies
      });

      if (!response.ok) {
        throw new Error('Failed to fetch LLM providers');
      }

      const data: ProvidersResponse = await response.json();
      setProviders(data.providers);

    } catch (err: any) {
      console.error('Failed to fetch providers:', err);
      setError(err.message || 'Failed to load providers');
    }
  }, []);

  const setSelectedModel = useCallback((modelId: string) => {
    const model = providers[modelId];
    if (model) {
      setSelectedModelState(model);
      setError(null);
    } else {
      setError(`Model ${modelId} not found`);
    }
  }, [providers]);

  const estimateCost = useCallback(
    async (inputText: string): Promise<number | null> => {
      if (!selectedModel) {
        setError('No model selected');
        return null;
      }

      try {
        const response = await fetch(API_ENDPOINTS.llm.estimateCost, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            model_id: selectedModel.id,
            input_text: inputText,
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to estimate cost');
        }

        const data = await response.json();
        return data.estimated_cost;
      } catch (err: any) {
        console.error('Cost estimation error:', err);
        return null;
      }
    },
    [selectedModel]
  );

  const chat = useCallback(
    async (request: ChatRequest): Promise<ChatResponse | null> => {
      if (!selectedModel) {
        setError('No model selected');
        return null;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Call centralized backend API
        const response = await fetch(API_ENDPOINTS.llm.chat, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include', // Include auth cookies for billing
          body: JSON.stringify({
            model_id: selectedModel.id,
            messages: request.messages,
            temperature: request.temperature || 0.7,
            max_tokens: request.maxTokens,
            top_p: request.topP || 0.9,
            stream: false,
            system_prompt: request.systemPrompt,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Chat request failed' }));
          throw new Error(errorData.detail || 'Chat request failed');
        }

        const result: ChatResponse = await response.json();

        // Log cost information
        console.info(
          `💰 LLM Chat Cost: $${result.cost.toFixed(4)} | ` +
          `Tokens: ${result.usage.totalTokens} | ` +
          `Model: ${result.modelId} | ` +
          `Time: ${result.processingTime.toFixed(2)}s`
        );

        return result;
      } catch (err: any) {
        const errorMessage = err.message || 'Failed to generate response';
        setError(errorMessage);
        console.error('Chat error:', err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [selectedModel]
  );

  const chatStream = useCallback(
    async (
      request: ChatRequest,
      onChunk: (chunk: string) => void
    ): Promise<void> => {
      if (!selectedModel) {
        setError('No model selected');
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Call centralized backend streaming API
        const response = await fetch(API_ENDPOINTS.llm.chatStream, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include', // Include auth cookies for billing
          body: JSON.stringify({
            model_id: selectedModel.id,
            messages: request.messages,
            temperature: request.temperature || 0.7,
            max_tokens: request.maxTokens,
            top_p: request.topP || 0.9,
            stream: true,
            system_prompt: request.systemPrompt,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Chat stream failed' }));
          throw new Error(errorData.detail || 'Chat stream failed');
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('Response body is not readable');
        }

        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n').filter(line => line.trim() !== '');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const dataStr = line.slice(6); // Remove 'data: ' prefix
                const parsed = JSON.parse(dataStr);

                if (parsed.error) {
                  throw new Error(parsed.error);
                }

                if (parsed.content) {
                  onChunk(parsed.content);
                }

                if (parsed.done) {
                  return;
                }
              } catch (e) {
                console.error('Failed to parse streaming data:', e);
              }
            }
          }
        }
      } catch (err: any) {
        const errorMessage = err.message || 'Failed to stream response';
        setError(errorMessage);
        console.error('Chat stream error:', err);
      } finally {
        setIsLoading(false);
      }
    },
    [selectedModel]
  );

  return {
    selectedModel,
    providers,
    setSelectedModel,
    isLoading,
    error,
    chat,
    chatStream,
    refreshProviders,
    estimateCost,
  };
};
