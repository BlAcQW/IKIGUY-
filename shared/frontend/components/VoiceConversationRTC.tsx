/**
 * Shared WebRTC Voice Conversation Component
 *
 * A reusable voice conversation modal that uses WebRTC transport.
 * Provides low-latency voice conversations.
 *
 * Note: Uses inline SVG icons to avoid external dependencies.
 */

import React, { useState, useRef, useEffect } from 'react';
import { useVoiceWebRTC } from '../hooks/useVoiceWebRTC';
import { conversationSessionService, ConversationSession } from '../services/conversation-session';

interface ConversationMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface VoiceConversationRTCProps {
  isOpen: boolean;
  onClose: () => void;
  assistantName: string;
  assistantId: string;
  apiBaseUrl: string;
  getAuthToken: () => Promise<string>;
  assistant?: {
    language?: string;
    llm_provider?: string;
    llm_model?: string;
  };
  languages?: Array<{ code: string; name: string; flag: string }>;
}

const DEFAULT_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'tw', name: 'Twi', flag: '🇬🇭' },
  { code: 'yo', name: 'Yoruba', flag: '🇳🇬' }
];

// Inline SVG Icons
const Icons = {
  X: ({ className = 'w-5 h-5' }: { className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
  ),
  Mic: ({ className = 'w-6 h-6' }: { className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" y1="19" x2="12" y2="22"/>
    </svg>
  ),
  Volume2: ({ className = 'w-5 h-5' }: { className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
    </svg>
  ),
  VolumeX: ({ className = 'w-5 h-5' }: { className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
      <line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>
    </svg>
  ),
  Square: ({ className = 'w-6 h-6' }: { className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
    </svg>
  ),
  Radio: ({ className = 'w-4 h-4' }: { className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="2"/>
      <path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"/>
    </svg>
  ),
  WifiOff: ({ className = 'w-4 h-4' }: { className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="1" y1="1" x2="23" y2="23"/>
      <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
      <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
      <path d="M10.71 5.05A16 16 0 0 1 22.58 9"/>
      <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
      <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
      <line x1="12" y1="20" x2="12.01" y2="20"/>
    </svg>
  ),
  Download: ({ className = 'w-5 h-5' }: { className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  ),
  Send: ({ className = 'w-5 h-5' }: { className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13"/>
      <polygon points="22 2 15 22 11 13 2 9 22 2"/>
    </svg>
  ),
};

export const VoiceConversationRTC: React.FC<VoiceConversationRTCProps> = ({
  isOpen,
  onClose,
  assistantName,
  assistantId,
  apiBaseUrl,
  getAuthToken,
  assistant,
  languages = DEFAULT_LANGUAGES
}) => {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [currentPartialText, setCurrentPartialText] = useState('');
  const [audioEnergy, setAudioEnergy] = useState(0);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [status, setStatus] = useState('Connecting...');
  const [textInput, setTextInput] = useState('');
  const [session, setSession] = useState<ConversationSession | null>(null);
  const [currentLanguage, setCurrentLanguage] = useState(languages[0]?.code || 'en');
  const [showLanguageMenu, setShowLanguageMenu] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showReadyIndicator, setShowReadyIndicator] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    isConnected,
    isRecording,
    isSpeaking,
    sendTextMessage,
    startRecording,
    stopRecording,
    stopSpeaking,
    disconnect
  } = useVoiceWebRTC({
    apiBaseUrl,
    assistantId,
    getAuthToken,
    assistant,
    onTranscription: (text, isFinal) => {
      if (isFinal) {
        const userMessage: ConversationMessage = {
          id: `user-${Date.now()}`,
          type: 'user',
          content: text,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, userMessage]);
        setCurrentPartialText('');

        if (session) {
          conversationSessionService.addMessage(session.id, 'user', text);
        }
      } else {
        setCurrentPartialText(text);
      }
    },
    onTextResponse: (text) => {
      const assistantMessage: ConversationMessage = {
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: text,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);

      if (session) {
        conversationSessionService.addMessage(session.id, 'assistant', text);
      }
    },
    onError: (error) => {
      console.error('[VoiceConvRTC] Error:', error);
      setStatus(`Error: ${error}`);
      setErrorMessage(error);

      const errorMsg: ConversationMessage = {
        id: `error-${Date.now()}`,
        type: 'assistant',
        content: `Error: ${error}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);

      setTimeout(() => setErrorMessage(null), 10000);
    },
    onStatusChange: (newStatus) => {
      setStatus(newStatus);
      if (newStatus === 'Your turn - speak now') {
        setShowReadyIndicator(true);
        setTimeout(() => setShowReadyIndicator(false), 2000);
      } else {
        setShowReadyIndicator(false);
      }
    }
  });

  // Initialize session
  useEffect(() => {
    if (isOpen) {
      setMessages([]);
      setCurrentPartialText('');
      setErrorMessage(null);
      setStatus('Connecting...');

      let detectedLanguage = languages[0]?.code || 'en';
      if (assistant?.language) {
        const lang = assistant.language.toLowerCase();
        const matched = languages.find(l =>
          lang.includes(l.code) || lang.includes(l.name.toLowerCase())
        );
        if (matched) {
          detectedLanguage = matched.code;
        }
      }
      setCurrentLanguage(detectedLanguage);

      const newSession = conversationSessionService.createSession(assistantId, assistantName, {
        language: detectedLanguage,
        transport: 'webrtc'
      });
      setSession(newSession);
    }
  }, [isOpen, assistantId, assistantName, assistant?.language, languages]);

  // Cleanup
  useEffect(() => {
    if (!isOpen && session) {
      if (isRecording) stopRecording();
      if (isSpeaking) stopSpeaking();
      if (isConnected) disconnect();
      conversationSessionService.endSession(session.id);
      setSession(null);
    }
  }, [isOpen, session]);

  useEffect(() => {
    return () => {
      if (session) {
        conversationSessionService.endSession(session.id);
      }
    };
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim() && isConnected) {
      const userMessage: ConversationMessage = {
        id: `user-${Date.now()}`,
        type: 'user',
        content: textInput,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);

      if (session) {
        conversationSessionService.addMessage(session.id, 'user', textInput);
      }

      sendTextMessage(textInput);
      setTextInput('');
    }
  };

  const handleExportConversation = () => {
    if (!session) return;
    const exportData = conversationSessionService.exportSession(session.id);
    if (exportData) {
      const blob = new Blob([exportData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation-rtc-${session.id}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleLanguageChange = (langCode: string) => {
    setCurrentLanguage(langCode);
    setShowLanguageMenu(false);
    if (session) {
      conversationSessionService.updateContext(session.id, { language: langCode });
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      if (isSpeaking) {
        stopSpeaking();
      }
      startRecording();
    }
  };

  const handleStopSpeaking = () => {
    stopSpeaking();
  };

  const toggleAudio = () => {
    setIsAudioEnabled(!isAudioEnabled);
  };

  useEffect(() => {
    if (isRecording) {
      const interval = setInterval(() => {
        setAudioEnergy(Math.random() * 100);
      }, 100);
      return () => clearInterval(interval);
    } else {
      setAudioEnergy(0);
    }
  }, [isRecording]);

  if (!isOpen) return null;

  if (!assistantId || assistantId.trim() === '') {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 max-w-md">
          <h3 className="text-lg font-semibold text-red-600 mb-4">Configuration Error</h3>
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            Cannot start conversation: Invalid assistant configuration.
          </p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  const currentLang = languages.find(l => l.code === currentLanguage) || languages[0];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg w-full max-w-4xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold">{assistantName}</h3>
            <div className="flex items-center gap-2">
              {isConnected ? (
                <>
                  <span className="text-green-500 animate-pulse"><Icons.Radio /></span>
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                    WebRTC
                  </span>
                </>
              ) : (
                <span className="text-red-500"><Icons.WifiOff /></span>
              )}
              <span className="text-sm text-gray-600 dark:text-gray-400">{status}</span>
            </div>
            {session && session.metadata.totalMessages > 0 && (
              <span className="text-xs text-gray-500">
                {session.metadata.totalMessages} messages
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* Language Toggle */}
            {languages.length > 1 && (
              <div className="relative">
                <button
                  onClick={() => setShowLanguageMenu(!showLanguageMenu)}
                  className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
                >
                  {currentLang?.flag} {currentLang?.code.toUpperCase()}
                </button>

                {showLanguageMenu && (
                  <div className="absolute right-0 mt-2 w-32 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg z-10">
                    {languages.map(lang => (
                      <button
                        key={lang.code}
                        onClick={() => handleLanguageChange(lang.code)}
                        className={`w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                          currentLanguage === lang.code ? 'bg-gray-100 dark:bg-gray-700 font-medium' : ''
                        }`}
                      >
                        {lang.flag} {lang.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <button
              onClick={handleExportConversation}
              disabled={!session || session.metadata.totalMessages === 0}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors disabled:opacity-50"
              title="Export conversation"
            >
              <Icons.Download />
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
            >
              <Icons.X />
            </button>
          </div>
        </div>

        {/* Error Banner */}
        {errorMessage && (
          <div className="mx-4 mt-4 p-3 bg-red-100 border border-red-300 text-red-800 rounded-md flex items-center justify-between">
            <span className="text-sm">{errorMessage}</span>
            <button onClick={() => setErrorMessage(null)} className="p-1 hover:bg-red-200 rounded">
              <Icons.X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Ready Indicator */}
        {showReadyIndicator && !isSpeaking && (
          <div className="mx-4 mt-4 p-4 bg-green-100 border-2 border-green-400 text-green-800 rounded-md flex items-center justify-center gap-3 animate-pulse">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-ping" />
            <span className="font-semibold">Your turn - Speak now</span>
            <Icons.Mic className="w-5 h-5" />
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] rounded-lg p-3 ${
                  message.type === 'user'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700'
                }`}
              >
                <p className="text-sm">{message.content}</p>
                <span className="text-xs opacity-70">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}

          {currentPartialText && (
            <div className="flex justify-end">
              <div className="max-w-[70%] rounded-lg p-3 bg-indigo-400 text-white">
                <p className="text-sm italic">{currentPartialText}...</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Audio Visualization */}
        {(isRecording || isSpeaking) && (
          <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium">
                {isRecording ? '🎤 Recording...' : '🔊 Speaking...'}
              </span>
              <div className="flex-1 h-8 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-100 ${
                    isRecording ? 'bg-red-500' : 'bg-indigo-500'
                  }`}
                  style={{ width: `${isRecording ? audioEnergy : 50}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Text Input */}
        <form onSubmit={handleTextSubmit} className="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Type a message..."
              className="flex-1 px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={!isConnected}
            />
            <button
              type="submit"
              disabled={!isConnected || !textInput.trim()}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              <Icons.Send />
            </button>
          </div>
        </form>

        {/* Controls */}
        <div className="flex items-center justify-center gap-4 p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={toggleRecording}
            disabled={!isConnected}
            className={`p-4 rounded-full transition-all ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                : 'bg-indigo-600 hover:bg-indigo-700 text-white'
            } disabled:opacity-50`}
            title={isRecording ? 'Stop Recording' : 'Start Recording'}
          >
            {isRecording ? <Icons.Square /> : <Icons.Mic />}
          </button>

          {isSpeaking && (
            <button
              onClick={handleStopSpeaking}
              className="p-4 rounded-full bg-orange-500 hover:bg-orange-600 text-white animate-pulse"
              title="Stop Speaking (Barge-in)"
            >
              <Icons.Square />
            </button>
          )}

          <button
            onClick={toggleAudio}
            className={`p-3 rounded-full transition-colors ${
              isAudioEnabled
                ? 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
                : 'bg-gray-200 dark:bg-gray-600'
            }`}
            title={isAudioEnabled ? 'Mute Audio' : 'Unmute Audio'}
          >
            {isAudioEnabled ? <Icons.Volume2 /> : <Icons.VolumeX />}
          </button>
        </div>
      </div>
    </div>
  );
};
