/**
 * VoiceBookChat Component
 *
 * Real-time voice interaction with books using:
 * - WebSocket: Reliable, ~100-200ms latency
 * - WebRTC: Low-latency, <50ms latency (experimental)
 *
 * Features:
 * - Transport mode toggle (WebSocket vs WebRTC)
 * - PCM audio streaming with 16kHz resampling
 * - Streaming TTS playback
 * - Barge-in support
 * - RAG-powered book Q&A
 *
 * Author: AI Labs Africa
 * Created: November 30, 2025
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Loader2,
  X,
  Radio,
  Wifi,
  Send,
  Settings,
  MessageSquare
} from 'lucide-react';
import { useWebSocketVoiceChat } from '@/hooks/useWebSocketVoiceChat';
import { useWebRTCVoiceChat } from '@/hooks/useWebRTCVoiceChat';
import { VoiceConfigPanel } from './VoiceConfigPanel';
import toast from 'react-hot-toast';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface VoiceSettings {
  provider_id?: string;
  voice_id?: string;
  speed?: number;
  language?: string;
}

interface VoiceBookChatProps {
  bookId: string;
  bookTitle?: string;
  voiceSettings?: VoiceSettings;
  onClose?: () => void;
}

type TransportMode = 'websocket' | 'webrtc';

export default function VoiceBookChat({
  bookId,
  bookTitle,
  voiceSettings,
  onClose
}: VoiceBookChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [textInput, setTextInput] = useState('');
  const [transportMode, setTransportMode] = useState<TransportMode>('websocket');
  const [showSettings, setShowSettings] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // WebSocket hook
  const wsChat = useWebSocketVoiceChat({
    bookId,
    voiceSettings,
    onTranscription: (text, isFinal) => {
      if (isFinal && text.trim()) {
        addMessage('user', text);
      }
    },
    onTextResponse: (text) => {
      addMessage('assistant', text);
    },
    onStatusChange: (status) => {
      console.log('[VoiceBookChat] Status:', status);
    },
    onError: (error) => {
      toast.error(error);
    }
  });

  // WebRTC hook
  const rtcChat = useWebRTCVoiceChat({
    bookId,
    voiceSettings,
    onTranscription: (text, isFinal) => {
      if (isFinal && text.trim()) {
        addMessage('user', text);
      }
    },
    onTextResponse: (text) => {
      addMessage('assistant', text);
    },
    onStatusChange: (status) => {
      console.log('[VoiceBookChat] Status:', status);
    },
    onError: (error) => {
      toast.error(error);
    }
  });

  // Current chat based on transport mode
  const chat = transportMode === 'websocket' ? wsChat : rtcChat;

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Connect WebSocket on mount and when switching to websocket mode
  useEffect(() => {
    if (transportMode === 'websocket' && !wsChat.isConnected && bookId) {
      console.log('[VoiceBookChat] Connecting WebSocket...');
      wsChat.connect();
    }
  }, [transportMode, wsChat.isConnected, wsChat.connect, bookId]);

  // Connect WebRTC when mode changes
  useEffect(() => {
    if (transportMode === 'webrtc' && !rtcChat.isConnected) {
      rtcChat.connect();
    }
  }, [transportMode, rtcChat.isConnected, rtcChat.connect]);

  // Add message to list
  const addMessage = useCallback((role: 'user' | 'assistant', content: string) => {
    const message: Message = {
      id: `${Date.now()}_${role}`,
      role,
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, message]);
  }, []);

  // Handle text input submission
  const handleSubmitText = (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;

    addMessage('user', textInput);
    chat.sendTextMessage(textInput);
    setTextInput('');
  };

  // Toggle recording
  const toggleRecording = () => {
    if (chat.isRecording) {
      chat.stopRecording();
    } else {
      chat.startRecording();
    }
  };

  // Get status text
  const getStatusText = () => {
    if (!chat.isConnected) return 'Connecting...';
    if (chat.isRecording) return '🎤 Listening...';
    if (chat.isSpeaking) return '🔊 Speaking...';
    return 'Tap microphone to speak';
  };

  // Get status color
  const getStatusColor = () => {
    if (!chat.isConnected) return 'text-yellow-400';
    if (chat.isRecording) return 'text-green-400';
    if (chat.isSpeaking) return 'text-purple-400';
    return 'text-gray-400';
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-gray-900 to-gray-950 rounded-xl overflow-hidden shadow-2xl border border-gray-800">
      {/* Header */}
      <div className="bg-gray-800/80 backdrop-blur-sm px-4 py-3 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-600/20">
              <MessageSquare className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">
                Ask about this book
              </h3>
              {bookTitle && (
                <p className="text-xs text-gray-400 truncate max-w-[200px]">
                  {bookTitle}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Transport Toggle */}
            <div className="flex items-center gap-1 bg-gray-700/50 rounded-lg p-1">
              <button
                onClick={() => setTransportMode('websocket')}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
                  transportMode === 'websocket'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
                title="WebSocket (reliable)"
              >
                <Wifi className="w-3 h-3" />
                WS
              </button>
              <button
                onClick={() => setTransportMode('webrtc')}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
                  transportMode === 'webrtc'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
                title="WebRTC (low latency)"
              >
                <Radio className="w-3 h-3" />
                RTC
              </button>
            </div>

            {/* Settings button */}
            <button
              onClick={() => setShowSettings(true)}
              className="p-2 rounded-lg bg-gray-700/50 hover:bg-gray-700 transition-colors"
              title="Voice settings"
            >
              <Settings className="w-4 h-4 text-gray-300" />
            </button>

            {/* Connection indicator */}
            <div
              className={`w-2 h-2 rounded-full ${
                chat.isConnected ? 'bg-green-500' : 'bg-yellow-500 animate-pulse'
              }`}
              title={chat.isConnected ? 'Connected' : 'Connecting...'}
            />

            {/* Stop speaking button */}
            {chat.isSpeaking && (
              <button
                onClick={chat.stopAudio}
                className="p-2 rounded-lg bg-red-600/20 hover:bg-red-600/30 transition-colors"
                title="Stop speaking"
              >
                <VolumeX className="w-4 h-4 text-red-400" />
              </button>
            )}

            {/* Close button */}
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 rounded-lg bg-gray-700/50 hover:bg-gray-700 transition-colors"
                title="Close"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <MessageSquare className="w-12 h-12 mb-4 opacity-30" />
            <p className="text-lg font-medium">Start a conversation</p>
            <p className="text-sm mt-1">
              Ask questions about the book using voice or text
            </p>
          </div>
        )}

        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-sm'
                    : 'bg-gray-800 text-gray-100 rounded-bl-sm'
                }`}
              >
                {message.isStreaming && (
                  <div className="flex items-center gap-2 mb-2">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span className="text-xs opacity-70">Typing...</span>
                  </div>
                )}
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {message.content}
                </p>
                <p className="text-xs opacity-50 mt-2">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Live transcription */}
        {chat.isRecording && chat.transcription && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-end"
          >
            <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-blue-500/20 text-blue-200 border border-blue-500/30 rounded-br-sm">
              <p className="whitespace-pre-wrap text-sm italic">
                {chat.transcription}
              </p>
              <p className="text-xs opacity-60 mt-2 flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                Listening...
              </p>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Controls */}
      <div className="bg-gray-800/80 backdrop-blur-sm px-4 py-4 border-t border-gray-700/50">
        {/* Text input */}
        <form onSubmit={handleSubmitText} className="flex items-center gap-2 mb-4">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Type a question..."
            disabled={chat.isRecording || chat.isSpeaking}
            className="flex-1 bg-gray-700/50 border border-gray-600 rounded-xl px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50 text-sm"
          />
          <button
            type="submit"
            disabled={!textInput.trim() || chat.isRecording || chat.isSpeaking}
            className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5 text-white" />
          </button>
        </form>

        {/* Voice control */}
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={toggleRecording}
            disabled={!chat.isConnected || chat.isSpeaking}
            className={`p-5 rounded-full transition-all transform hover:scale-105 ${
              chat.isRecording
                ? 'bg-red-600 hover:bg-red-700 animate-pulse shadow-lg shadow-red-600/30'
                : 'bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-600/30'
            } disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none`}
            title={chat.isRecording ? 'Stop recording' : 'Start recording'}
          >
            {chat.isRecording ? (
              <MicOff className="w-7 h-7 text-white" />
            ) : (
              <Mic className="w-7 h-7 text-white" />
            )}
          </button>

          {chat.isSpeaking && (
            <div className="flex items-center gap-2 text-purple-400">
              <Volume2 className="w-5 h-5 animate-pulse" />
              <span className="text-sm font-medium">AI Speaking...</span>
            </div>
          )}
        </div>

        {/* Status */}
        <div className="mt-3 text-center">
          <p className={`text-sm font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {transportMode === 'websocket' ? 'WebSocket mode' : 'WebRTC mode'}
            {' '}• {chat.isConnected ? 'Connected' : 'Connecting...'}
          </p>
        </div>
      </div>

      {/* Voice Configuration Panel */}
      {showSettings && (
        <VoiceConfigPanel
          bookId={bookId}
          onClose={() => setShowSettings(false)}
          onSave={(settings) => {
            console.log('[VoiceBookChat] Settings saved:', settings);
            setShowSettings(false);
            // Optionally reload connection with new settings
            // chat.disconnect();
            // chat.connect();
          }}
        />
      )}
    </div>
  );
}
