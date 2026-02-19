/**
 * useLLMChat Hook
 *
 * React hook for LLM chat functionality with streaming support.
 * Designed for testing LLM providers in voice settings pages.
 *
 * Features:
 * - Streaming responses via SSE
 * - Fallback to non-streaming for unsupported models
 * - Message history management
 * - Cancel in-progress requests
 * - Error handling
 */

import { useState, useCallback, useRef, useEffect } from 'react';

export interface ChatMessage {
  id: string;
  role: 'system' | 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export interface UseLLMChatOptions {
  apiBaseUrl: string;
  getAuthToken: () => Promise<string>;
  modelId?: string;
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  onError?: (error: Error) => void;
}

export interface UseLLMChatResult {
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
  cancelStream: () => void;
  setModelId: (modelId: string) => void;
  setSystemPrompt: (prompt: string) => void;
  setTemperature: (temp: number) => void;
}

function generateId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export function useLLMChat({
  apiBaseUrl,
  getAuthToken,
  modelId: initialModelId = 'gemini-2.5-flash',
  systemPrompt: initialSystemPrompt,
  temperature: initialTemperature = 0.7,
  maxTokens,
  onError,
}: UseLLMChatOptions): UseLLMChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modelId, setModelId] = useState(initialModelId);
  const [systemPrompt, setSystemPrompt] = useState(initialSystemPrompt);
  const [temperature, setTemperature] = useState(initialTemperature);

  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesRef = useRef<ChatMessage[]>([]);

  // Keep messagesRef in sync with messages state
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isStreaming) return;

    setError(null);

    // Add user message
    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    // Create placeholder for assistant response
    const assistantMessageId = generateId();
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };

    // Update messages state with both user and assistant placeholder
    const updatedMessages = [...messagesRef.current, userMessage, assistantMessage];
    setMessages(updatedMessages);
    messagesRef.current = updatedMessages;
    setIsStreaming(true);

    try {
      const token = await getAuthToken();

      // Prepare messages for API (include system prompt if set)
      const apiMessages: Array<{ role: string; content: string }> = [];

      if (systemPrompt) {
        apiMessages.push({ role: 'system', content: systemPrompt });
      }

      // Add conversation history (excluding the placeholder assistant message)
      // Use messagesRef to get the latest state including the user message we just added
      const conversationHistory = messagesRef.current.filter(msg => msg.id !== assistantMessageId);
      conversationHistory.forEach(msg => {
        if (msg.role !== 'system' && msg.content) {
          apiMessages.push({ role: msg.role, content: msg.content });
        }
      });

      // Create abort controller for cancellation
      abortControllerRef.current = new AbortController();

      // Try streaming first
      const streamUrl = `${apiBaseUrl}/api/llm/chat/stream`;

      const response = await fetch(streamUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          model_id: modelId,
          messages: apiMessages,
          temperature,
          max_tokens: maxTokens,
          stream: true,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        // Fallback to non-streaming if streaming not available
        if (response.status === 400 || response.status === 501) {
          await sendNonStreaming(content, apiMessages, token, assistantMessageId);
          return;
        }

        const errorText = await response.text().catch(() => 'Unknown error');
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { detail: errorText || `Request failed: ${response.status}` };
        }
        console.error('LLM chat stream error:', response.status, errorData);
        throw new Error(errorData.detail || errorData.message || `Request failed: ${response.status}`);
      }

      // Process SSE stream
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let fullContent = '';
      let streamingNotImplemented = false;

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();

            if (data === '[DONE]') {
              continue;
            }

            try {
              const parsed = JSON.parse(data);

              if (parsed.error) {
                // Check if streaming is not implemented - fallback to non-streaming
                const errorLower = parsed.error.toLowerCase();
                if (errorLower.includes('streaming not') ||
                    errorLower.includes('not implemented') ||
                    errorLower.includes('not yet implemented') ||
                    errorLower.includes('not found')) {
                  console.log('Streaming issue, falling back to non-streaming:', parsed.error);
                  streamingNotImplemented = true;
                  break;
                }
                // For other errors, set streamingNotImplemented to trigger fallback
                console.warn('Streaming error, will try non-streaming:', parsed.error);
                streamingNotImplemented = true;
                break;
              }

              if (parsed.content !== undefined) {
                fullContent += parsed.content;

                // Update message with streamed content
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: fullContent }
                    : msg
                ));
              }
            } catch (parseError) {
              // JSON parse error - skip invalid lines
              if (data && data !== '[DONE]') {
                console.warn('Failed to parse SSE data:', data);
              }
            }
          }
        }

        // Break outer loop if we need to fallback
        if (streamingNotImplemented) break;
      }

      // Fallback to non-streaming if streaming not implemented
      if (streamingNotImplemented) {
        reader.cancel();
        await sendNonStreaming(content, apiMessages, token, assistantMessageId);
        return;
      }

      // Mark streaming as complete
      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, isStreaming: false }
          : msg
      ));

    } catch (err) {
      console.error('LLM chat error:', err);
      if (err instanceof Error && err.name === 'AbortError') {
        // Request was cancelled, keep partial content
        setMessages(prev => prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, isStreaming: false, content: msg.content || '(Cancelled)' }
            : msg
        ));
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        console.error('LLM chat error message:', errorMessage);
        setError(errorMessage);
        onError?.(err instanceof Error ? err : new Error(errorMessage));

        // Remove the placeholder message on error
        setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId));
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, [apiBaseUrl, getAuthToken, modelId, systemPrompt, temperature, maxTokens, isStreaming, onError]);

  const sendNonStreaming = async (
    content: string,
    apiMessages: Array<{ role: string; content: string }>,
    token: string,
    assistantMessageId: string
  ) => {
    const nonStreamUrl = `${apiBaseUrl}/api/llm/chat`;

    const response = await fetch(nonStreamUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        model_id: modelId,
        messages: apiMessages,
        temperature,
        max_tokens: maxTokens,
        stream: false,
      }),
      signal: abortControllerRef.current?.signal,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Request failed: ${response.status}`);
    }

    const data = await response.json();

    setMessages(prev => prev.map(msg =>
      msg.id === assistantMessageId
        ? { ...msg, content: data.message, isStreaming: false }
        : msg
    ));
  };

  const clearMessages = useCallback(() => {
    cancelStream();
    setMessages([]);
    setError(null);
  }, []);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  return {
    messages,
    isStreaming,
    error,
    sendMessage,
    clearMessages,
    cancelStream,
    setModelId,
    setSystemPrompt,
    setTemperature,
  };
}

export default useLLMChat;
