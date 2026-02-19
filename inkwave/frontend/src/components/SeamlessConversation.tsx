/**
 * SeamlessConversation Component
 *
 * Provides seamless, streaming conversation experience with:
 * - WebSocket-based real-time voice chat (VoiceAgent approach)
 * - Server-side VAD for hands-free operation (works in ALL browsers)
 * - Progressive text display
 * - Streaming TTS responses
 *
 * This component uses server-side speech recognition via WebSocket,
 * which works in ALL browsers (Firefox, Chrome, Safari, mobile).
 *
 * Author: AI Labs Africa
 * Updated: November 30, 2025
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Volume2, VolumeX, Loader2, MessageSquare, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { useWebSocketVoiceChat } from '../hooks/useWebSocketVoiceChat';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface SeamlessConversationProps {
  bookId: string;
  interactionId: string;
  onClose?: () => void;
}

export default function SeamlessConversation({
  bookId,
  interactionId,
  onClose
}: SeamlessConversationProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<string>('Connecting...');
  const [textInput, setTextInput] = useState('');
  const [showTextInput, setShowTextInput] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Memoize voice settings to prevent re-renders
  const voiceSettings = useMemo(() => ({
    provider_id: 'kokoro',
    voice_id: 'am_adam',
    speed: 1.0,
    language: 'en'
  }), []);

  // Memoize callbacks to prevent re-renders causing reconnection loops
  const handleTranscription = useCallback((text: string, isFinal: boolean) => {
    console.log('[SeamlessConversation] Transcription:', text, 'Final:', isFinal);
    if (isFinal && text.trim()) {
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: text,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);
    }
  }, []);

  const handleTextResponse = useCallback((text: string) => {
    console.log('[SeamlessConversation] AI Response:', text.substring(0, 100) + '...');
    const assistantMessage: Message = {
      id: Date.now().toString() + '_ai',
      role: 'assistant',
      content: text,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, assistantMessage]);
  }, []);

  const handleStatusChange = useCallback((newStatus: string) => {
    console.log('[SeamlessConversation] Status:', newStatus);
    setStatus(newStatus);
  }, []);

  const handleError = useCallback((error: string) => {
    console.error('[SeamlessConversation] Error:', error);
    toast.error(error);
  }, []);

  const handleConversationStateChange = useCallback((state: any) => {
    console.log('[SeamlessConversation] State:', state);
  }, []);

  const handleVADEvent = useCallback((event: 'speech_start' | 'utterance_complete', data?: any) => {
    console.log('[SeamlessConversation] VAD Event:', event, data);
    if (event === 'speech_start') {
      setStatus('Speech detected...');
    } else if (event === 'utterance_complete') {
      setStatus('Processing...');
    }
  }, []);

  // Use WebSocket-based voice chat hook (works in ALL browsers)
  const {
    isConnected,
    isRecording,
    isSpeaking,
    transcription,
    response,
    conversationState,
    startRecording,
    stopRecording,
    stopAudio,
    sendTextMessage,
    connect,
    disconnect
  } = useWebSocketVoiceChat({
    bookId,
    handsFree: true,  // Enable hands-free mode with server-side VAD
    voiceSettings,
    onTranscription: handleTranscription,
    onTextResponse: handleTextResponse,
    onStatusChange: handleStatusChange,
    onError: handleError,
    onConversationStateChange: handleConversationStateChange,
    onVADEvent: handleVADEvent
  });

  // Connect WebSocket on mount
  useEffect(() => {
    console.log('[SeamlessConversation] Connecting WebSocket for book:', bookId);
    connect();
  }, [connect]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Toggle recording
  const toggleListening = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  // Handle text input submission
  const handleTextSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim() || !isConnected) return;

    // Add user message immediately
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: textInput,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    // Send via WebSocket
    sendTextMessage(textInput);
    setTextInput('');
    setShowTextInput(false);
  }, [textInput, isConnected, sendTextMessage]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return (
    <div className="flex flex-col h-full bg-gray-900 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gray-800 px-4 py-3 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">
            Ask About This Book
          </h3>
          <div className="flex items-center gap-2">
            {/* Connection status indicator */}
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />

            {isSpeaking && (
              <button
                onClick={stopAudio}
                className="p-2 rounded-full bg-blue-600 hover:bg-blue-700 transition-colors"
                title="Stop speaking"
              >
                <VolumeX className="w-4 h-4 text-white" />
              </button>
            )}

            {/* Toggle text input */}
            <button
              onClick={() => setShowTextInput(!showTextInput)}
              className="p-2 rounded-full bg-gray-700 hover:bg-gray-600 transition-colors"
              title="Type instead"
            >
              <MessageSquare className="w-4 h-4 text-white" />
            </button>

            {onClose && (
              <button
                onClick={onClose}
                className="p-2 rounded-full bg-gray-700 hover:bg-gray-600 transition-colors"
                title="Close"
              >
                <X className="w-4 h-4 text-white" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Welcome message if no messages */}
        {messages.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-400 mb-2">
              {isConnected ? 'Ready to chat!' : 'Connecting...'}
            </p>
            <p className="text-gray-500 text-sm">
              Tap the microphone and ask me anything about this book.
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
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-100'
                }`}
              >
                {message.isStreaming && (
                  <div className="flex items-center gap-2 mb-2">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span className="text-xs opacity-70">Typing...</span>
                  </div>
                )}
                <p className="whitespace-pre-wrap">{message.content}</p>
                <p className="text-xs opacity-60 mt-2">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Show transcription in progress */}
        {transcription && isRecording && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-end"
          >
            <div className="max-w-[80%] rounded-lg px-4 py-3 bg-blue-500/30 text-white border border-blue-500/50">
              <p className="whitespace-pre-wrap italic">{transcription}</p>
              <p className="text-xs opacity-60 mt-2">Listening...</p>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Text Input (optional) */}
      {showTextInput && (
        <div className="px-4 py-2 border-t border-gray-700">
          <form onSubmit={handleTextSubmit} className="flex gap-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Type your question..."
              className="flex-1 bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500"
              disabled={!isConnected}
            />
            <button
              type="submit"
              disabled={!textInput.trim() || !isConnected}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </form>
        </div>
      )}

      {/* Controls */}
      <div className="bg-gray-800 px-4 py-4 border-t border-gray-700">
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={toggleListening}
            disabled={!isConnected || isSpeaking}
            className={`p-6 rounded-full transition-all ${
              isRecording
                ? 'bg-red-600 hover:bg-red-700 animate-pulse'
                : 'bg-blue-600 hover:bg-blue-700'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            title={isRecording ? 'Stop listening' : 'Start listening'}
          >
            {isRecording ? (
              <MicOff className="w-8 h-8 text-white" />
            ) : (
              <Mic className="w-8 h-8 text-white" />
            )}
          </button>

          {isSpeaking && (
            <button
              onClick={stopAudio}
              className="flex items-center gap-2 px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600"
            >
              <Volume2 className="w-5 h-5 text-blue-400 animate-pulse" />
              <span className="text-sm text-white">Stop</span>
            </button>
          )}
        </div>

        <div className="mt-3 text-center">
          <p className="text-sm text-gray-400">
            {!isConnected ? (
              <span className="text-yellow-400">Connecting...</span>
            ) : isRecording ? (
              <span className="text-green-400">Listening - Ask me anything!</span>
            ) : status.includes('Processing') || status.includes('Thinking') ? (
              <span className="text-blue-400">Processing your question...</span>
            ) : isSpeaking ? (
              <span className="text-purple-400">Speaking... (tap to interrupt)</span>
            ) : (
              <span>Tap the microphone to start talking</span>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
