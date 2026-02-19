/**
 * Chat Panel Component
 *
 * Main panel for chatting with LLM models.
 */

import React, { useState, useRef, useEffect } from 'react';
import { LLMModel } from '../../config/llm-models';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

interface ChatPanelProps {
  model: LLMModel;
  onChat: (request: any) => Promise<any>;
  onChatStream: (request: any, onChunk: (chunk: string) => void) => Promise<any>;
  isLoading: boolean;
  error: string | null;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  model,
  onChat,
  onChatStream,
  isLoading,
  error,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1024);
  const [useStreaming, setUseStreaming] = useState(true);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Set default system prompt for cultural models
  useEffect(() => {
    if (model.capabilities.culturalContext && !systemPrompt) {
      setSystemPrompt(
        'You are a helpful assistant with deep knowledge of Ghanaian culture, languages, and customs. You understand proverbs, local knowledge, and can engage in natural code-switching between English and Ghanaian languages like Twi, Ga, and Ewe.'
      );
    }
  }, [model]);

  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');

    const chatMessages = [
      ...(systemPrompt
        ? [{ role: 'system' as const, content: systemPrompt }]
        : []),
      ...messages.map((m) => ({ role: m.role, content: m.content })),
      { role: 'user' as const, content: inputText },
    ];

    if (useStreaming && model.capabilities.streaming) {
      // Streaming response
      const assistantMessage: Message = {
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      let streamedContent = '';
      await onChatStream(
        {
          messages: chatMessages,
          temperature,
          maxTokens,
          streaming: true,
        },
        (chunk: string) => {
          streamedContent += chunk;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: streamedContent,
            };
            return updated;
          });
        }
      );
    } else {
      // Non-streaming response
      const result = await onChat({
        messages: chatMessages,
        temperature,
        maxTokens,
        streaming: false,
      });

      if (result) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: result.message,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  const exportChat = () => {
    const chatExport = {
      model: model.name,
      timestamp: new Date().toISOString(),
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp.toISOString(),
      })),
    };

    const blob = new Blob([JSON.stringify(chatExport, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${model.id}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{model.name}</h2>
            <p className="text-sm text-gray-500">{model.description}</p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              ⚙️ Settings
            </button>
            <button
              onClick={exportChat}
              disabled={messages.length === 0}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              📥 Export
            </button>
            <button
              onClick={clearChat}
              disabled={messages.length === 0}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              🗑️ Clear
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                System Prompt
              </label>
              <textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                placeholder="Optional system prompt to guide the model's behavior..."
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Temperature: {temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Lower = more focused, Higher = more creative
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Tokens: {maxTokens}
                </label>
                <input
                  type="range"
                  min="256"
                  max={model.maxTokens || 4096}
                  step="256"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Maximum response length
                </p>
              </div>

              {model.capabilities.streaming && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Streaming
                  </label>
                  <div className="flex items-center space-x-2 mt-2">
                    <input
                      type="checkbox"
                      id="streaming"
                      checked={useStreaming}
                      onChange={(e) => setUseStreaming(e.target.checked)}
                      className="rounded"
                    />
                    <label htmlFor="streaming" className="text-sm text-gray-700">
                      Enable streaming responses
                    </label>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 bg-gray-50 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <span className="text-6xl mb-4">{model.icon}</span>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Start a Conversation
            </h3>
            <p className="text-gray-500 max-w-md">
              {model.capabilities.culturalContext
                ? 'Ask questions about Ghanaian culture, proverbs, or have a conversation in Twi, Ga, or Ewe!'
                : 'Type a message below to start chatting with the model.'}
            </p>
          </div>
        ) : (
          <>
            {messages.map((message, idx) => (
              <div
                key={idx}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-900'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-sm font-medium">
                      {message.role === 'user' ? '👤 You' : `${model.icon} ${model.name}`}
                    </span>
                    <span
                      className={`text-xs ${
                        message.role === 'user' ? 'text-indigo-200' : 'text-gray-400'
                      }`}
                    >
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap text-sm">{message.content}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="flex space-x-2">
          <textarea
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Shift+Enter for new line)"
            rows={2}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
          />
          <button
            onClick={handleSend}
            disabled={!inputText.trim() || isLoading}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isLoading ? (
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            ) : (
              '▶'
            )}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send • Shift+Enter for new line • Context window:{' '}
          {model.contextWindow ? model.contextWindow.toLocaleString() : 'N/A'} tokens
        </p>
      </div>
    </div>
  );
};
