import React, { useState, useRef, useEffect } from 'react';
import {
  X,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Square,
  Play,
  Pause,
  Wifi,
  WifiOff,
  Download
} from 'lucide-react';
import { useWebSocketChat } from '@/hooks/useWebSocketChat';
import { conversationSessionService, ConversationSession } from '@/services/conversation-session';

interface ConversationMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  audio?: string;
}

interface VoiceConversationWSProps {
  isOpen: boolean;
  onClose: () => void;
  assistantName: string;
  assistantId: string;
  assistant?: any;
}

export const VoiceConversationWS: React.FC<VoiceConversationWSProps> = ({
  isOpen,
  onClose,
  assistantName,
  assistantId,
  assistant
}) => {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [currentPartialText, setCurrentPartialText] = useState('');
  const [audioEnergy, setAudioEnergy] = useState(0);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [status, setStatus] = useState('Connecting...');
  const [textInput, setTextInput] = useState('');
  const [session, setSession] = useState<ConversationSession | null>(null);
  const [currentLanguage, setCurrentLanguage] = useState<'en' | 'tw' | 'yo'>('en');
  const [showLanguageMenu, setShowLanguageMenu] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showReadyIndicator, setShowReadyIndicator] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioQueueRef = useRef<string[]>([]);
  const isPlayingRef = useRef(false);

  // Use WebSocket hook (now includes isSpeaking and stopSpeaking)
  // Note: We pass assistantId || 'invalid' to avoid hook being called conditionally
  const {
    isConnected,
    isRecording,
    isSpeaking,
    sendTextMessage,
    startRecording,
    stopRecording,
    stopSpeaking,
    playAudio,
    disconnect
  } = useWebSocketChat({
    assistantId,
    onTranscription: (text, isFinal) => {
      if (isFinal) {
        // Add user message
        const userMessage: ConversationMessage = {
          id: `user-${Date.now()}`,
          type: 'user',
          content: text,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, userMessage]);
        setCurrentPartialText('');

        // Add to session
        if (session) {
          conversationSessionService.addMessage(session.id, 'user', text);
        }
      } else {
        // Show partial transcription
        setCurrentPartialText(text);
      }
    },
    onTextResponse: (text) => {
      console.log('[VoiceConv] Received text response:', text);

      // Check if this is an error response from the server
      if (text && text.includes('I apologize, but I encountered an error')) {
        console.error('[VoiceConv] Server error response detected');

        // Log assistant configuration for debugging
        console.log('[VoiceConv] Assistant config:', {
          id: assistantId,
          name: assistantName,
          llm_provider: assistant?.llm_provider,
          llm_model: assistant?.llm_model,
          system_prompt: assistant?.system_prompt ? 'Set' : 'Not set',
          tts_provider: assistant?.tts_provider,
          stt_provider: assistant?.stt_provider
        });
      }

      // Add assistant message
      const assistantMessage: ConversationMessage = {
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: text,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Add to session
      if (session) {
        conversationSessionService.addMessage(session.id, 'assistant', text);
      }
    },
    onAudioChunk: (audioData) => {
      // Queue audio for playback
      audioQueueRef.current.push(audioData);
      processAudioQueue();
    },
    onAudioComplete: (metadata) => {
      console.log('Audio complete:', metadata);
      // isSpeaking is now managed by the hook
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      setStatus(`Error: ${error}`);

      // Show detailed error message
      const errorMessage = typeof error === 'string'
        ? error
        : (error as any)?.message || 'An unexpected error occurred';
      setErrorMessage(errorMessage);

      // Add error to messages for visibility
      const errorMsg: ConversationMessage = {
        id: `error-${Date.now()}`,
        type: 'assistant',
        content: `⚠️ Error: ${errorMessage}\n\nPlease check:\n1. Assistant configuration is complete\n2. LLM provider (${assistant?.llm_provider}) is properly configured\n3. System prompt is set`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);

      // Auto-clear error after 10 seconds
      setTimeout(() => setErrorMessage(null), 10000);
    },
    onStatusChange: (newStatus) => {
      setStatus(newStatus);
      // Show ready indicator when it's user's turn
      if (newStatus === 'Your turn - speak now') {
        setShowReadyIndicator(true);
        // Auto-hide after 2 seconds
        setTimeout(() => setShowReadyIndicator(false), 2000);
      } else {
        setShowReadyIndicator(false);
      }
    }
  });

  // Initialize conversation session when opening
  useEffect(() => {
    if (isOpen) {
      // Clear previous messages when reopening
      setMessages([]);
      setCurrentPartialText('');
      setErrorMessage(null);
      setStatus('Connecting...');

      // Auto-detect language from assistant configuration
      let detectedLanguage: 'en' | 'tw' | 'yo' = 'en';
      if (assistant?.language) {
        const lang = assistant.language.toLowerCase();
        if (lang.includes('twi') || lang.includes('tw') || lang.includes('akan')) {
          detectedLanguage = 'tw';
        } else if (lang.includes('yoruba') || lang.includes('yor') || lang === 'yo') {
          detectedLanguage = 'yo';
        }
      }
      setCurrentLanguage(detectedLanguage);
      console.log('[VoiceConv] Auto-detected language:', detectedLanguage, 'from assistant language:', assistant?.language);

      // Create new session
      const newSession = conversationSessionService.createSession(assistantId, assistantName, {
        language: detectedLanguage
      });
      setSession(newSession);
      console.log('[VoiceConv] Created conversation session:', newSession.id);
    }
  }, [isOpen, assistantId, assistantName, assistant?.language]);

  // Cleanup when closing
  useEffect(() => {
    if (!isOpen && session) {
      console.log('[VoiceConv] Closing conversation, cleaning up...');

      // Stop any ongoing recording
      if (isRecording) {
        console.log('[VoiceConv] Stopping recording...');
        stopRecording();
      }

      // Stop any ongoing audio playback
      if (isSpeaking) {
        console.log('[VoiceConv] Stopping audio playback...');
        stopSpeaking();
      }

      // Clear audio queue
      audioQueueRef.current = [];
      isPlayingRef.current = false;

      // Disconnect WebSocket
      if (isConnected) {
        console.log('[VoiceConv] Disconnecting WebSocket...');
        disconnect();
      }

      // End the session
      conversationSessionService.endSession(session.id);
      console.log('[VoiceConv] Ended conversation session:', session.id);
      setSession(null);
    }
  }, [isOpen, session, isRecording, isSpeaking, isConnected, stopRecording, stopSpeaking, disconnect]);

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      // Final cleanup if component unmounts while open
      if (isRecording) {
        stopRecording();
      }
      if (isSpeaking) {
        stopSpeaking();
      }
      if (isConnected) {
        disconnect();
      }
      if (session) {
        conversationSessionService.endSession(session.id);
        console.log('[VoiceConv] Component unmounting - ended conversation session:', session.id);
      }
    };
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Process audio queue
  const processAudioQueue = async () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) {
      return;
    }

    isPlayingRef.current = true;

    while (audioQueueRef.current.length > 0 && isAudioEnabled) {
      const audioData = audioQueueRef.current.shift();
      if (audioData) {
        await playAudio(audioData);
        // Small delay between chunks
        await new Promise(resolve => setTimeout(resolve, 50));
      }
    }

    isPlayingRef.current = false;
  };

  // Handle text input submission
  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim() && isConnected) {
      // Add user message
      const userMessage: ConversationMessage = {
        id: `user-${Date.now()}`,
        type: 'user',
        content: textInput,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);

      // Add to session
      if (session) {
        conversationSessionService.addMessage(session.id, 'user', textInput);
      }

      // Send through WebSocket
      sendTextMessage(textInput);
      setTextInput('');
    }
  };

  // Export conversation
  const handleExportConversation = () => {
    if (!session) return;

    const exportData = conversationSessionService.exportSession(session.id);
    if (exportData) {
      const blob = new Blob([exportData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation-${session.id}.json`;
      a.click();
      URL.revokeObjectURL(url);
      console.log('[VoiceConv] Exported conversation:', session.id);
    }
  };

  // Change language
  const handleLanguageChange = (language: 'en' | 'tw' | 'yo') => {
    setCurrentLanguage(language);
    setShowLanguageMenu(false);

    // Update session context
    if (session) {
      conversationSessionService.updateContext(session.id, { language });
    }

    // Note: Would send config update to WebSocket
    // updateConfig({ language, dialect: language === 'tw' ? 'asante' : undefined });
    console.log(`[VoiceConv] Changed language to: ${language}`);
  };

  // Toggle recording with automatic barge-in
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      // Automatic barge-in: stop assistant speaking when user starts talking
      if (isSpeaking) {
        console.log('[VoiceConv] 🎤 User starting to speak - triggering barge-in');
        stopSpeaking();
        // Clear audio queue
        audioQueueRef.current = [];
        isPlayingRef.current = false;
      }
      startRecording();
    }
  };

  // Manual stop speaking button handler
  const handleStopSpeaking = () => {
    console.log('[VoiceConv] 🛑 Manual stop speaking triggered');
    stopSpeaking();
    // Clear audio queue
    audioQueueRef.current = [];
    isPlayingRef.current = false;
  };

  // Toggle audio output
  const toggleAudio = () => {
    setIsAudioEnabled(!isAudioEnabled);
    if (!isAudioEnabled) {
      // Clear audio queue if disabling
      audioQueueRef.current = [];
    }
  };

  // Visualize audio energy
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

  // Validate assistant ID after all hooks are called
  if (!assistantId || assistantId.trim() === '') {
    console.error('❌ CRITICAL ERROR: VoiceConversationWS received invalid assistantId:', assistantId);
    console.error('Assistant data:', assistant);
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
        <div className="bg-card border border-border rounded-lg p-6 max-w-md">
          <h3 className="text-lg font-semibold text-red-600 mb-4">Configuration Error</h3>
          <p className="text-gray-600 mb-4">
            Cannot start conversation: Invalid assistant configuration. The assistant ID is missing.
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

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-card border border-border rounded-lg w-full max-w-4xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold">{assistantName}</h3>
            <div className="flex items-center gap-2">
              {isConnected ? (
                <Wifi className="w-4 h-4 text-green-500" />
              ) : (
                <WifiOff className="w-4 h-4 text-red-500" />
              )}
              <span className="text-sm text-gray-600">{status}</span>
            </div>
            {session && session.metadata.totalMessages > 0 && (
              <span className="text-xs text-gray-500">
                {session.metadata.totalMessages} messages • {Math.floor(session.metadata.duration / 60000)}:{((session.metadata.duration % 60000) / 1000).toFixed(0).padStart(2, '0')}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* Language Toggle */}
            <div className="relative">
              <button
                onClick={() => setShowLanguageMenu(!showLanguageMenu)}
                className="px-3 py-1 text-sm bg-accent hover:bg-accent/80 rounded-md transition-colors flex items-center gap-1"
                title="Change language"
              >
                <span className="font-medium">
                  {currentLanguage === 'en' ? '🇬🇧 EN' : currentLanguage === 'tw' ? '🇬🇭 TW' : '🇳🇬 YO'}
                </span>
              </button>

              {showLanguageMenu && (
                <div className="absolute right-0 mt-2 w-32 bg-card border border-border rounded-md shadow-lg z-10">
                  <button
                    onClick={() => handleLanguageChange('en')}
                    className={`w-full px-3 py-2 text-left text-sm hover:bg-accent transition-colors ${
                      currentLanguage === 'en' ? 'bg-accent font-medium' : ''
                    }`}
                  >
                    🇬🇧 English
                  </button>
                  <button
                    onClick={() => handleLanguageChange('tw')}
                    className={`w-full px-3 py-2 text-left text-sm hover:bg-accent transition-colors ${
                      currentLanguage === 'tw' ? 'bg-accent font-medium' : ''
                    }`}
                  >
                    🇬🇭 Twi
                  </button>
                  <button
                    onClick={() => handleLanguageChange('yo')}
                    className={`w-full px-3 py-2 text-left text-sm hover:bg-accent transition-colors ${
                      currentLanguage === 'yo' ? 'bg-accent font-medium' : ''
                    }`}
                  >
                    🇳🇬 Yoruba
                  </button>
                </div>
              )}
            </div>

            <button
              onClick={handleExportConversation}
              disabled={!session || session.metadata.totalMessages === 0}
              className="p-2 hover:bg-accent rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Export conversation"
            >
              <Download className="w-5 h-5" />
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-accent rounded-md transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Error Banner */}
        {errorMessage && (
          <div className="mx-4 mt-4 p-3 bg-red-100 border border-red-300 text-red-800 rounded-md flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Error:</span>
              <span className="text-sm">{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="p-1 hover:bg-red-200 rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Ready to Speak Indicator */}
        {showReadyIndicator && !isSpeaking && (
          <div className="mx-4 mt-4 p-4 bg-green-100 border-2 border-green-400 text-green-800 rounded-md flex items-center justify-center gap-3 animate-pulse">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-ping" />
              <div className="w-3 h-3 bg-green-500 rounded-full absolute" />
            </div>
            <span className="text-base font-semibold">Your turn - Speak now</span>
            <Mic className="w-5 h-5" />
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
                    ? 'bg-indigo-600 text-primary-foreground'
                    : 'bg-muted'
                }`}
              >
                <p className="text-sm">{message.content}</p>
                <span className="text-xs opacity-70">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}
          
          {/* Partial transcription */}
          {currentPartialText && (
            <div className="flex justify-end">
              <div className="max-w-[70%] rounded-lg p-3 bg-primary/50 text-primary-foreground">
                <p className="text-sm italic">{currentPartialText}...</p>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Audio Visualization & Status */}
        {(isRecording || isSpeaking) && (
          <div className="px-4 py-3 border-t border-border bg-muted/30">
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0 text-sm font-medium">
                {isRecording && <span className="text-red-500">🎤 Recording...</span>}
                {isSpeaking && !isRecording && <span className="text-primary">🔊 Speaking...</span>}
              </div>
              <div className="flex-1 h-8 bg-muted rounded-full overflow-hidden relative">
                <div
                  className={`h-full transition-all duration-100 ${
                    isRecording ? 'bg-red-500' : 'bg-primary'
                  }`}
                  style={{ width: `${isRecording ? audioEnergy : 50}%` }}
                />
                {isSpeaking && !isRecording && (
                  <div className="absolute inset-0 bg-primary/50 animate-pulse" />
                )}
              </div>
            </div>
          </div>
        )}

        {/* Text Input */}
        <form onSubmit={handleTextSubmit} className="px-4 py-2 border-t border-border">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Type a message..."
              className="flex-1 px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              disabled={!isConnected}
            />
            <button
              type="submit"
              disabled={!isConnected || !textInput.trim()}
              className="px-4 py-2 bg-indigo-600 text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
        </form>

        {/* Controls */}
        <div className="flex items-center justify-center gap-4 p-4 border-t border-border">
          <button
            onClick={toggleRecording}
            disabled={!isConnected || (isSpeaking && !isRecording)}
            className={`p-4 rounded-full transition-all ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                : 'bg-indigo-600 hover:bg-primary/90 text-primary-foreground'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            title={
              isSpeaking && !isRecording
                ? 'Assistant is speaking...'
                : isRecording
                  ? 'Stop Recording'
                  : 'Start Recording'
            }
          >
            {isRecording ? <Square className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
          </button>

          {/* Stop Speaking Button (Barge-in) */}
          {isSpeaking && (
            <button
              onClick={handleStopSpeaking}
              className="p-4 rounded-full bg-orange-500 hover:bg-orange-600 text-white transition-colors animate-pulse"
              title="Stop Speaking (Barge-in)"
            >
              <Square className="w-6 h-6" />
            </button>
          )}

          <button
            onClick={toggleAudio}
            className={`p-3 rounded-full transition-colors ${
              isAudioEnabled
                ? 'bg-accent hover:bg-accent/80'
                : 'bg-muted hover:bg-muted/80'
            }`}
            title={isAudioEnabled ? 'Mute Audio' : 'Unmute Audio'}
          >
            {isAudioEnabled ? (
              <Volume2 className="w-5 h-5" />
            ) : (
              <VolumeX className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};