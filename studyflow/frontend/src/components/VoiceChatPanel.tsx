/**
 * VoiceChatPanel Component
 *
 * Browser-based voice chat interface for interacting with study materials.
 * Supports two modes:
 * - VoiceAgent (default): Real-time streaming with server-side VAD, hands-free operation
 * - Classic: Request/response model with client-side recording
 *
 * Features:
 * - Audio recording with visual feedback
 * - Chat history display
 * - Audio playback for responses
 * - Cost tracking
 * - Settings link for voice configuration
 * - Hands-free mode with auto-resume listening
 * - Barge-in support for interrupting responses
 *
 * Author: AI Labs Africa
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Mic,
  MicOff,
  Send,
  Play,
  Pause,
  Trash2,
  Settings,
  Volume2,
  VolumeX,
  Loader2,
  AlertCircle,
  MessageSquare,
  X,
  ChevronDown,
  ChevronUp,
  Radio,
  Hand,
  Zap,
} from 'lucide-react';
import { useVoiceRecorder } from '../hooks/useVoiceRecorder';
import { useVoiceAgent } from '../hooks/useVoiceAgent';
import { materialVoiceApi, type MaterialVoiceResponse, type ChatHistoryEntry } from '../lib/api';

type VoiceChatMode = 'voiceagent' | 'classic';

interface VoiceChatPanelProps {
  materialId: string;
  materialTitle: string;
  isOpen: boolean;
  onClose: () => void;
  mode?: VoiceChatMode;  // Default: 'voiceagent'
  sessionId?: string;  // Optional session ID for VoiceAgent mode
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  text: string;
  audioBase64?: string;
  audioDuration?: number;
  timestamp: Date;
  costBreakdown?: {
    asr: number;
    llm: number;
    tts: number;
    total: number;
  };
}

export default function VoiceChatPanel({
  materialId,
  materialTitle,
  isOpen,
  onClose,
  mode = 'voiceagent',  // Default to VoiceAgent mode
  sessionId,
}: VoiceChatPanelProps) {
  const navigate = useNavigate();

  // State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState<boolean | null>(null);
  const [playingAudioId, setPlayingAudioId] = useState<string | null>(null);
  const [totalCost, setTotalCost] = useState(0);
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(false);
  const [handsFreeEnabled, setHandsFreeEnabled] = useState(true);
  const [statusMessage, setStatusMessage] = useState<string>('');

  // Generate session ID once (memoized to prevent new connections on each render)
  const [effectiveSessionId] = useState(() =>
    sessionId || `material-${materialId}-${Date.now()}`
  );

  // Refs
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // VoiceAgent hook (only used in voiceagent mode)
  const voiceAgent = useVoiceAgent({
    sessionId: mode === 'voiceagent' ? effectiveSessionId : '',
    materialId: materialId,
    handsFree: handsFreeEnabled,
    onTranscription: (text, isFinal) => {
      if (isFinal && text) {
        // Add user message when transcription is final
        const userMessage: ChatMessage = {
          id: `user-${Date.now()}`,
          type: 'user',
          text: text,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);
      }
    },
    onTextResponse: (text) => {
      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        text: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    },
    onStatusChange: (status) => {
      setStatusMessage(status);
      // Update processing state based on status
      if (status === 'Processing...' || status === 'Thinking...') {
        setIsProcessing(true);
      } else if (status === 'Ready to listen' || status === 'Connected' || status === 'Listening...') {
        setIsProcessing(false);
      }
    },
    onError: (err) => {
      setError(err);
      setIsProcessing(false);
    },
    onConversationStateChange: (state) => {
      console.log('[VoiceChatPanel] Conversation state:', state);
    },
    onVADEvent: (event, data) => {
      console.log(`[VoiceChatPanel] VAD event: ${event}`, data);
    },
  });

  // Classic mode voice recorder hook
  const voiceRecorder = useVoiceRecorder({
    maxDuration: 60,
    onRecordingComplete: handleClassicRecordingComplete,
    onError: (err) => setError(err),
  });

  // Determine which recording state to use based on mode
  const isRecording = mode === 'voiceagent' ? voiceAgent.isRecording : voiceRecorder.isRecording;
  const isSpeaking = mode === 'voiceagent' ? voiceAgent.isSpeaking : playingAudioId !== null;

  // Check if material is ready for voice chat
  useEffect(() => {
    if (isOpen) {
      checkMaterialReady();
      loadChatHistory();
      if (mode === 'classic') {
        voiceRecorder.checkPermission();
      }
    }
  }, [isOpen, materialId, mode]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  async function checkMaterialReady() {
    try {
      const result = await materialVoiceApi.checkReady(materialId);
      setIsReady(result.ready);
      if (!result.ready) {
        setError(result.reason || 'Material is not ready for voice chat');
      }
    } catch (err) {
      console.error('Error checking material:', err);
      setIsReady(false);
      setError('Failed to check material status');
    }
  }

  async function loadChatHistory() {
    try {
      const result = await materialVoiceApi.getHistory(materialId, 50);
      if (result.history && result.history.length > 0) {
        const loadedMessages: ChatMessage[] = [];
        let cost = 0;

        result.history.forEach((entry: ChatHistoryEntry) => {
          // Add user message
          loadedMessages.push({
            id: `${entry.id}-q`,
            type: 'user',
            text: entry.question_text,
            timestamp: new Date(entry.created_at),
          });

          // Add assistant response
          loadedMessages.push({
            id: entry.id,
            type: 'assistant',
            text: entry.answer_text,
            timestamp: new Date(entry.created_at),
            costBreakdown: entry.cost_breakdown,
          });

          if (entry.cost_breakdown) {
            cost += entry.cost_breakdown.total;
          }
        });

        setMessages(loadedMessages);
        setTotalCost(cost);
      }
    } catch (err) {
      console.error('Error loading chat history:', err);
    }
  }

  // Classic mode recording handler
  async function handleClassicRecordingComplete(audioBase64: string, blob: Blob) {
    setIsProcessing(true);
    setError(null);

    try {
      // Send voice question to backend
      const response: MaterialVoiceResponse = await materialVoiceApi.ask(
        materialId,
        audioBase64
      );

      // Add user message (transcribed)
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        type: 'user',
        text: response.transcribed_text,
        timestamp: new Date(),
      };

      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: response.chat_id,
        type: 'assistant',
        text: response.response_text,
        audioBase64: response.response_audio_base64,
        audioDuration: response.audio_duration,
        timestamp: new Date(),
        costBreakdown: response.cost_breakdown,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setTotalCost((prev) => prev + response.cost_breakdown.total);

      // Auto-play response audio
      playAudio(response.response_audio_base64, response.chat_id);
    } catch (err) {
      console.error('Error processing voice question:', err);
      setError(err instanceof Error ? err.message : 'Failed to process voice question');
    } finally {
      setIsProcessing(false);
    }
  }

  function playAudio(audioBase64: string, messageId: string) {
    // Stop any currently playing audio
    if (audioRef.current) {
      audioRef.current.pause();
    }

    // Create audio element
    const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
    audioRef.current = audio;
    setPlayingAudioId(messageId);

    audio.onended = () => {
      setPlayingAudioId(null);
    };

    audio.onerror = () => {
      setPlayingAudioId(null);
      // Try with mp3 format as fallback
      audio.src = `data:audio/mp3;base64,${audioBase64}`;
      audio.play().catch(console.error);
    };

    audio.play().catch((err) => {
      console.error('Error playing audio:', err);
      setPlayingAudioId(null);
    });
  }

  function pauseAudio() {
    if (audioRef.current) {
      audioRef.current.pause();
      setPlayingAudioId(null);
    }
  }

  async function clearHistory() {
    if (!confirm('Clear all chat history for this material?')) return;

    try {
      await materialVoiceApi.clearHistory(materialId);
      setMessages([]);
      setTotalCost(0);
    } catch (err) {
      console.error('Error clearing history:', err);
      setError('Failed to clear history');
    }
  }

  function formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function formatCost(cost: number): string {
    return `$${cost.toFixed(4)}`;
  }

  // Handle recording toggle for VoiceAgent mode
  function handleVoiceAgentRecordingToggle() {
    if (voiceAgent.isRecording) {
      voiceAgent.stopRecording();
    } else {
      voiceAgent.startRecording();
    }
  }

  // Handle barge-in (stop speaking)
  function handleBargeIn() {
    if (mode === 'voiceagent') {
      voiceAgent.stopAudio();
    } else {
      pauseAudio();
    }
  }

  if (!isOpen) return null;

  const permissionGranted = mode === 'classic' ? voiceRecorder.permissionGranted : true;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="w-full max-w-2xl h-[80vh] flex flex-col bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg">
              {mode === 'voiceagent' ? (
                <Zap className="h-5 w-5" />
              ) : (
                <MessageSquare className="h-5 w-5" />
              )}
            </div>
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2">
                Voice Chat
                {mode === 'voiceagent' && (
                  <span className="text-xs bg-green-500/20 text-green-100 px-2 py-0.5 rounded-full">
                    Real-time
                  </span>
                )}
              </h2>
              <p className="text-sm text-blue-100 truncate max-w-[300px]">{materialTitle}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Hands-free toggle (VoiceAgent mode only) */}
            {mode === 'voiceagent' && (
              <button
                onClick={() => setHandsFreeEnabled(!handsFreeEnabled)}
                className={`p-2 rounded-lg transition-colors ${
                  handsFreeEnabled ? 'bg-green-500/30 hover:bg-green-500/40' : 'hover:bg-white/20'
                }`}
                title={handsFreeEnabled ? 'Hands-free ON' : 'Hands-free OFF'}
              >
                <Hand className="h-5 w-5" />
              </button>
            )}
            <button
              onClick={() => navigate('/voice-settings')}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title="Voice Settings"
            >
              <Settings className="h-5 w-5" />
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Connection Status (VoiceAgent mode) */}
        {mode === 'voiceagent' && (
          <div className={`px-4 py-2 text-xs flex items-center gap-2 ${
            voiceAgent.isConnected ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-700'
          }`}>
            <Radio className={`h-3 w-3 ${voiceAgent.isConnected ? 'text-green-500' : 'text-yellow-500 animate-pulse'}`} />
            {voiceAgent.isConnected ? 'Connected' : 'Connecting...'}
            {statusMessage && <span className="ml-2 text-gray-500">| {statusMessage}</span>}
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="px-4 py-3 bg-red-50 border-b border-red-200 flex items-center gap-2 text-red-700">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <p className="text-sm flex-1">{error}</p>
            <button
              onClick={() => setError(null)}
              className="p-1 hover:bg-red-100 rounded"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Permission Warning */}
        {permissionGranted === false && (
          <div className="px-4 py-3 bg-yellow-50 border-b border-yellow-200 flex items-center gap-2 text-yellow-800">
            <MicOff className="h-5 w-5 flex-shrink-0" />
            <p className="text-sm">
              Microphone access is required.{' '}
              <button
                onClick={voiceRecorder.checkPermission}
                className="underline font-medium hover:text-yellow-900"
              >
                Grant permission
              </button>
            </p>
          </div>
        )}

        {/* Not Ready State */}
        {isReady === false && (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Material Not Ready</h3>
              <p className="text-gray-600 mb-4">
                This material needs to be processed before voice chat is available.
              </p>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        )}

        {/* Chat Messages */}
        {isReady && (
          <div
            ref={chatContainerRef}
            className="flex-1 overflow-y-auto p-4 space-y-4"
          >
            {messages.length === 0 && !isProcessing && (
              <div className="text-center py-12 text-gray-500">
                <Mic className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium text-gray-600 mb-2">
                  {mode === 'voiceagent' ? 'Start Speaking' : 'Start a Voice Conversation'}
                </p>
                <p className="text-sm">
                  {mode === 'voiceagent'
                    ? 'Press the microphone and speak - I\'ll respond automatically'
                    : 'Press the microphone button and ask a question about this material'}
                </p>
                {mode === 'voiceagent' && handsFreeEnabled && (
                  <p className="text-xs text-green-600 mt-2">
                    Hands-free mode: I'll keep listening after responding
                  </p>
                )}
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white rounded-br-md'
                      : 'bg-gray-100 text-gray-900 rounded-bl-md'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.text}</p>

                  {/* Audio playback for assistant messages (classic mode) */}
                  {message.type === 'assistant' && message.audioBase64 && mode === 'classic' && (
                    <div className="mt-2 pt-2 border-t border-gray-200 flex items-center gap-2">
                      <button
                        onClick={() =>
                          playingAudioId === message.id
                            ? pauseAudio()
                            : playAudio(message.audioBase64!, message.id)
                        }
                        className="p-1.5 bg-white rounded-full shadow-sm hover:shadow transition-shadow"
                      >
                        {playingAudioId === message.id ? (
                          <Pause className="h-4 w-4 text-blue-600" />
                        ) : (
                          <Play className="h-4 w-4 text-blue-600" />
                        )}
                      </button>
                      <div className="flex-1 h-1 bg-gray-300 rounded-full overflow-hidden">
                        <div
                          className={`h-full bg-blue-500 transition-all duration-300 ${
                            playingAudioId === message.id ? 'animate-pulse' : ''
                          }`}
                          style={{ width: playingAudioId === message.id ? '50%' : '0%' }}
                        />
                      </div>
                      {message.audioDuration && (
                        <span className="text-xs text-gray-500">
                          {formatDuration(message.audioDuration)}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Cost info */}
                  {message.costBreakdown && (
                    <div className="mt-2 text-xs opacity-60">
                      Cost: {formatCost(message.costBreakdown.total)}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Processing indicator */}
            {isProcessing && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex items-center gap-2 text-gray-600">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">
                      {mode === 'voiceagent' ? statusMessage || 'Processing...' : 'Processing your question...'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Recording Controls */}
        {isReady && (
          <div className="border-t border-gray-200 p-4">
            {/* Stats bar */}
            <div className="flex items-center justify-between mb-3 text-xs text-gray-500">
              <button
                onClick={() => setIsHistoryExpanded(!isHistoryExpanded)}
                className="flex items-center gap-1 hover:text-gray-700"
              >
                {isHistoryExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronUp className="h-3 w-3" />}
                {messages.length} messages
              </button>
              <span>Session cost: {formatCost(totalCost)}</span>
              {messages.length > 0 && (
                <button
                  onClick={clearHistory}
                  className="flex items-center gap-1 text-red-500 hover:text-red-600"
                >
                  <Trash2 className="h-3 w-3" />
                  Clear
                </button>
              )}
            </div>

            {/* Recording UI */}
            <div className="flex items-center justify-center gap-4">
              {/* VoiceAgent Mode Controls */}
              {mode === 'voiceagent' ? (
                <>
                  {/* Speaking indicator - tap to interrupt */}
                  {isSpeaking && (
                    <button
                      onClick={handleBargeIn}
                      className="flex items-center gap-2 px-4 py-2 bg-orange-100 hover:bg-orange-200 text-orange-700 rounded-full transition-colors"
                    >
                      <VolumeX className="h-4 w-4" />
                      <span className="text-sm">Tap to interrupt</span>
                    </button>
                  )}

                  {/* Recording button */}
                  {!isSpeaking && (
                    <>
                      <button
                        onClick={handleVoiceAgentRecordingToggle}
                        disabled={!voiceAgent.isConnected || isProcessing}
                        className={`p-5 rounded-full transition-all duration-200 ${
                          isRecording
                            ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse shadow-lg shadow-red-500/50'
                            : !voiceAgent.isConnected || isProcessing
                            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl hover:scale-105'
                        }`}
                        title={isRecording ? 'Stop recording' : 'Start recording'}
                      >
                        {isProcessing ? (
                          <Loader2 className="h-8 w-8 animate-spin" />
                        ) : isRecording ? (
                          <MicOff className="h-8 w-8" />
                        ) : (
                          <Mic className="h-8 w-8" />
                        )}
                      </button>

                      <div className="text-center">
                        <p className="text-sm text-gray-600">
                          {isRecording
                            ? 'Listening... (tap to stop)'
                            : isProcessing
                            ? statusMessage || 'Processing...'
                            : 'Tap to start speaking'}
                        </p>
                        {!isRecording && !isProcessing && (
                          <p className="text-xs text-gray-400 mt-1">
                            {handsFreeEnabled ? 'Hands-free mode enabled' : 'Tap to record'}
                          </p>
                        )}
                      </div>
                    </>
                  )}
                </>
              ) : (
                // Classic Mode Controls
                <>
                  {voiceRecorder.isRecording ? (
                    <>
                      {/* Recording indicator */}
                      <div className="flex items-center gap-3">
                        <div className="relative">
                          <div
                            className="absolute inset-0 bg-red-500 rounded-full animate-ping opacity-75"
                            style={{ transform: `scale(${1 + voiceRecorder.audioLevel * 0.5})` }}
                          />
                          <div className="relative p-4 bg-red-500 rounded-full">
                            <Mic className="h-6 w-6 text-white" />
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-mono font-bold text-gray-900">
                            {formatDuration(voiceRecorder.duration)}
                          </div>
                          <div className="text-xs text-gray-500">Recording...</div>
                        </div>
                      </div>

                      {/* Audio level bars */}
                      <div className="flex items-end gap-1 h-8">
                        {[0, 0.2, 0.4, 0.6, 0.8].map((threshold, i) => (
                          <div
                            key={i}
                            className={`w-1.5 rounded-full transition-all duration-75 ${
                              voiceRecorder.audioLevel > threshold ? 'bg-red-500' : 'bg-gray-300'
                            }`}
                            style={{
                              height: `${20 + i * 10}%`,
                            }}
                          />
                        ))}
                      </div>

                      {/* Stop buttons */}
                      <div className="flex gap-2">
                        <button
                          onClick={voiceRecorder.cancelRecording}
                          className="p-3 bg-gray-200 hover:bg-gray-300 rounded-full transition-colors"
                          title="Cancel"
                        >
                          <X className="h-5 w-5 text-gray-600" />
                        </button>
                        <button
                          onClick={voiceRecorder.stopRecording}
                          className="p-3 bg-blue-600 hover:bg-blue-700 rounded-full transition-colors"
                          title="Send"
                        >
                          <Send className="h-5 w-5 text-white" />
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      {/* Start recording button */}
                      <button
                        onClick={voiceRecorder.startRecording}
                        disabled={isProcessing || permissionGranted === false}
                        className={`p-5 rounded-full transition-all duration-200 ${
                          isProcessing || permissionGranted === false
                            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl hover:scale-105'
                        }`}
                        title="Hold to record"
                      >
                        {isProcessing ? (
                          <Loader2 className="h-8 w-8 animate-spin" />
                        ) : (
                          <Mic className="h-8 w-8" />
                        )}
                      </button>

                      <div className="text-center">
                        <p className="text-sm text-gray-600">
                          {isProcessing
                            ? 'Processing...'
                            : 'Tap to start recording'}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          Uses your{' '}
                          <button
                            onClick={() => navigate('/voice-settings')}
                            className="text-blue-600 hover:underline"
                          >
                            voice settings
                          </button>
                        </p>
                      </div>
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
