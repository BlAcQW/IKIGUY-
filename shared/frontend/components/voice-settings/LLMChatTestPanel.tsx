/**
 * LLM Chat Test Panel Component
 *
 * A chat interface for testing LLM providers.
 * Uses inline SVG icons to avoid external dependencies.
 *
 * Features:
 * - Chat message display with user/assistant bubbles
 * - Text input with send button
 * - Streaming response display
 * - Model info display
 * - Clear conversation button
 * - Export conversation
 */

import React, { useState, useRef, useEffect } from 'react';
import { useLLMChat, ChatMessage } from '../../hooks/useLLMChat';

export interface LLMChatTestPanelProps {
  apiBaseUrl: string;
  getAuthToken: () => Promise<string>;
  selectedModel?: string;
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  disabled?: boolean;
  disabledReason?: string;
  className?: string;
}

// Inline SVG Icons
const Icons = {
  Send: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13"/>
      <polygon points="22 2 15 22 11 13 2 9 22 2"/>
    </svg>
  ),
  Trash: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6"/>
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
    </svg>
  ),
  Download: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  ),
  Stop: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
    </svg>
  ),
  User: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
  ),
  Bot: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="10" rx="2"/>
      <circle cx="12" cy="5" r="2"/>
      <path d="M12 7v4"/>
      <line x1="8" y1="16" x2="8" y2="16"/>
      <line x1="16" y1="16" x2="16" y2="16"/>
    </svg>
  ),
  MessageSquare: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  ),
  AlertCircle: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
  ),
};

// Typing indicator dots
const TypingIndicator: React.FC = () => (
  <div className="flex space-x-1">
    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}/>
    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}/>
    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}/>
  </div>
);

// Message bubble component
const MessageBubble: React.FC<{ message: ChatMessage }> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div className={`flex items-start gap-2 max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
        }`}>
          {isUser ? <Icons.User /> : <Icons.Bot />}
        </div>

        {/* Message content */}
        <div className={`rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-indigo-600 text-white'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
        }`}>
          {message.isStreaming && !message.content ? (
            <TypingIndicator />
          ) : (
            <div className="whitespace-pre-wrap break-words text-sm">
              {message.content}
              {message.isStreaming && (
                <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse"/>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const LLMChatTestPanel: React.FC<LLMChatTestPanelProps> = ({
  apiBaseUrl,
  getAuthToken,
  selectedModel = 'gemini-2.5-flash',
  systemPrompt,
  temperature = 0.7,
  maxTokens,
  disabled = false,
  disabledReason,
  className = '',
}) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const {
    messages,
    isStreaming,
    error,
    sendMessage,
    clearMessages,
    cancelStream,
    setModelId,
    setSystemPrompt: setHookSystemPrompt,
    setTemperature: setHookTemperature,
  } = useLLMChat({
    apiBaseUrl,
    getAuthToken,
    modelId: selectedModel,
    systemPrompt,
    temperature,
    maxTokens,
  });

  // Update hook state when props change
  useEffect(() => {
    setModelId(selectedModel);
  }, [selectedModel, setModelId]);

  useEffect(() => {
    if (systemPrompt !== undefined) {
      setHookSystemPrompt(systemPrompt);
    }
  }, [systemPrompt, setHookSystemPrompt]);

  useEffect(() => {
    setHookTemperature(temperature);
  }, [temperature, setHookTemperature]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (inputValue.trim() && !isStreaming && !disabled) {
      const message = inputValue;
      setInputValue('');
      await sendMessage(message);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleExport = () => {
    const exportData = {
      model: selectedModel,
      temperature,
      systemPrompt,
      messages: messages.map(m => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp.toISOString(),
      })),
      exportedAt: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-export-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const isReady = !disabled && selectedModel;

  return (
    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg flex flex-col ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-indigo-600 dark:text-indigo-400"><Icons.MessageSquare /></span>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Test LLM Chat</h3>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <>
                <button
                  onClick={handleExport}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  title="Export conversation"
                >
                  <Icons.Download />
                </button>
                <button
                  onClick={clearMessages}
                  className="p-2 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  title="Clear conversation"
                >
                  <Icons.Trash />
                </button>
              </>
            )}
          </div>
        </div>

        {/* Model info */}
        <div className="mt-2 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
          <span>Model: <span className="font-medium text-gray-700 dark:text-gray-300">{selectedModel}</span></span>
          <span>Temp: <span className="font-medium text-gray-700 dark:text-gray-300">{temperature}</span></span>
        </div>
      </div>

      {/* Disabled message */}
      {disabled && disabledReason && (
        <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-700">
          <div className="flex items-center gap-2 text-yellow-800 dark:text-yellow-200">
            <Icons.AlertCircle />
            <span className="text-sm">{disabledReason}</span>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="p-3 mx-4 mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-300 text-sm">
            <Icons.AlertCircle />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Messages area */}
      <div className="flex-1 min-h-[300px] max-h-[400px] overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
            <Icons.MessageSquare />
            <p className="mt-2 text-sm">Start a conversation to test the LLM</p>
            <p className="text-xs mt-1">Messages will appear here</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input area */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? disabledReason || 'Chat disabled' : 'Type a message...'}
            disabled={disabled || isStreaming}
            rows={1}
            className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
          />
          {isStreaming ? (
            <button
              onClick={cancelStream}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center gap-2"
              title="Stop generation"
            >
              <Icons.Stop />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || disabled}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 text-white disabled:text-gray-500 rounded-lg transition-colors flex items-center gap-2 disabled:cursor-not-allowed"
              title="Send message"
            >
              <Icons.Send />
            </button>
          )}
        </div>
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
};

export default LLMChatTestPanel;
