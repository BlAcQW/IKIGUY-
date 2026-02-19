/**
 * Shared Voice Testing Panel Component
 *
 * A complete voice testing panel that allows testing voice conversations
 * with both WebSocket and WebRTC transports. Designed to be integrated
 * into any app's voice settings page.
 *
 * Note: Uses inline SVG icons to avoid external dependencies.
 */

import React, { useState } from 'react';
import { VoiceConversationWS } from './VoiceConversationWS';
import { VoiceConversationRTC } from './VoiceConversationRTC';

export interface VoiceTestingPanelProps {
  assistantId: string;
  assistantName: string;
  apiBaseUrl: string;
  wsBaseUrl: string;
  getAuthToken: () => Promise<string>;
  assistant?: {
    language?: string;
    llm_provider?: string;
    llm_model?: string;
    tts_provider?: string;
    stt_provider?: string;
  };
  languages?: Array<{ code: string; name: string; flag: string }>;
  className?: string;
  disabled?: boolean;
  disabledReason?: string;
}

type TransportType = 'websocket' | 'webrtc';

const DEFAULT_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'tw', name: 'Twi', flag: '🇬🇭' },
  { code: 'yo', name: 'Yoruba', flag: '🇳🇬' }
];

// Inline SVG Icons to avoid dependency on lucide-react
const Icons = {
  MessageSquare: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  ),
  Wifi: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
      <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
      <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
      <line x1="12" y1="20" x2="12.01" y2="20"/>
    </svg>
  ),
  Radio: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="2"/>
      <path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"/>
    </svg>
  ),
  Mic: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" y1="19" x2="12" y2="22"/>
    </svg>
  ),
  Play: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="5 3 19 12 5 21 5 3"/>
    </svg>
  ),
};

export const VoiceTestingPanel: React.FC<VoiceTestingPanelProps> = ({
  assistantId,
  assistantName,
  apiBaseUrl,
  wsBaseUrl,
  getAuthToken,
  assistant,
  languages = DEFAULT_LANGUAGES,
  className = '',
  disabled = false,
  disabledReason
}) => {
  const [selectedTransport, setSelectedTransport] = useState<TransportType>('websocket');
  const [showConversation, setShowConversation] = useState(false);

  const handleStartConversation = () => {
    if (!assistantId) {
      console.error('[VoiceTestingPanel] No assistant selected');
      return;
    }
    setShowConversation(true);
  };

  const handleCloseConversation = () => {
    setShowConversation(false);
  };

  const isReady = !!assistantId && !disabled;

  return (
    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <span className="text-indigo-600"><Icons.MessageSquare /></span>
          <h3 className="text-lg font-semibold">Test Voice Conversation</h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Test your voice assistant with live conversation
        </p>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Transport Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Transport Protocol
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setSelectedTransport('websocket')}
              className={`flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition-all ${
                selectedTransport === 'websocket'
                  ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
              }`}
            >
              <Icons.Wifi />
              <div className="text-left">
                <div className="font-medium">WebSocket</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">PCM Streaming</div>
              </div>
            </button>

            <button
              onClick={() => setSelectedTransport('webrtc')}
              className={`flex items-center justify-center gap-2 p-3 rounded-lg border-2 transition-all ${
                selectedTransport === 'webrtc'
                  ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
              }`}
            >
              <Icons.Radio />
              <div className="text-left">
                <div className="font-medium">WebRTC</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Low Latency</div>
              </div>
            </button>
          </div>
        </div>

        {/* Assistant Info */}
        {assistant && (
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Configuration
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {assistant.llm_provider && (
                <div>
                  <span className="text-gray-500 dark:text-gray-400">LLM:</span>{' '}
                  <span className="font-medium">{assistant.llm_provider}</span>
                </div>
              )}
              {assistant.tts_provider && (
                <div>
                  <span className="text-gray-500 dark:text-gray-400">TTS:</span>{' '}
                  <span className="font-medium">{assistant.tts_provider}</span>
                </div>
              )}
              {assistant.stt_provider && (
                <div>
                  <span className="text-gray-500 dark:text-gray-400">ASR:</span>{' '}
                  <span className="font-medium">{assistant.stt_provider}</span>
                </div>
              )}
              {assistant.language && (
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Language:</span>{' '}
                  <span className="font-medium">{assistant.language}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Disabled Reason */}
        {disabled && disabledReason && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-3">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">{disabledReason}</p>
          </div>
        )}

        {/* Start Button */}
        <button
          onClick={handleStartConversation}
          disabled={!isReady}
          className={`w-full flex items-center justify-center gap-2 p-4 rounded-lg font-medium transition-all ${
            isReady
              ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
          }`}
        >
          {selectedTransport === 'websocket' ? <Icons.Mic /> : <Icons.Radio />}
          <span>
            Start {selectedTransport === 'websocket' ? 'WebSocket' : 'WebRTC'} Conversation
          </span>
          <Icons.Play />
        </button>

        {/* Help Text */}
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          {selectedTransport === 'websocket'
            ? 'WebSocket provides reliable streaming with PCM audio chunks'
            : 'WebRTC provides ultra-low latency peer-to-peer audio'}
        </p>
      </div>

      {/* Conversation Modals */}
      {selectedTransport === 'websocket' ? (
        <VoiceConversationWS
          isOpen={showConversation}
          onClose={handleCloseConversation}
          assistantId={assistantId}
          assistantName={assistantName}
          wsBaseUrl={wsBaseUrl}
          getAuthToken={getAuthToken}
          assistant={assistant}
          languages={languages}
        />
      ) : (
        <VoiceConversationRTC
          isOpen={showConversation}
          onClose={handleCloseConversation}
          assistantId={assistantId}
          assistantName={assistantName}
          apiBaseUrl={apiBaseUrl}
          getAuthToken={getAuthToken}
          assistant={assistant}
          languages={languages}
        />
      )}
    </div>
  );
};

export default VoiceTestingPanel;
