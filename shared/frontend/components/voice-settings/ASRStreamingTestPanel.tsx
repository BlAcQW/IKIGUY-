/**
 * ASR Streaming Test Panel Component
 *
 * A speech recognition testing interface with both real-time
 * streaming and file-based transcription modes.
 *
 * Features:
 * - Mode toggle: Real-time vs File-based
 * - Microphone recording with waveform
 * - Live transcription display
 * - Language selector
 * - Copy and clear buttons
 * - Recording time indicator
 */

import React, { useState, useRef, useEffect } from 'react';
import { useASRStreaming, ASRMode } from '../../hooks/useASRStreaming';

export interface ASRStreamingTestPanelProps {
  apiBaseUrl: string;
  wsBaseUrl: string;
  getAuthToken: () => Promise<string>;
  selectedProvider?: string;
  language?: string;
  defaultMode?: ASRMode;
  disabled?: boolean;
  disabledReason?: string;
  className?: string;
  languages?: Array<{ code: string; name: string; flag?: string }>;
}

// Default language options
const DEFAULT_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'tw', name: 'Twi', flag: '🇬🇭' },
  { code: 'yo', name: 'Yoruba', flag: '🇳🇬' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
  { code: 'es', name: 'Spanish', flag: '🇪🇸' },
  { code: 'de', name: 'German', flag: '🇩🇪' },
  { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
  { code: 'ar', name: 'Arabic', flag: '🇸🇦' },
];

// Inline SVG Icons - using currentColor for proper theme support
const Icons = {
  Mic: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" y1="19" x2="12" y2="22"/>
    </svg>
  ),
  MicOff: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="2" y1="2" x2="22" y2="22"/>
      <path d="M18.89 13.23A7.12 7.12 0 0 0 19 12v-2"/>
      <path d="M5 10v2a7 7 0 0 0 12 5"/>
      <path d="M15 9.34V5a3 3 0 0 0-5.68-1.33"/>
      <path d="M9 9v3a3 3 0 0 0 5.12 2.12"/>
      <line x1="12" y1="19" x2="12" y2="22"/>
    </svg>
  ),
  Stop: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="6" y="6" width="12" height="12" rx="1" ry="1"/>
    </svg>
  ),
  Waveform: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 10v3"/>
      <path d="M6 6v11"/>
      <path d="M10 3v18"/>
      <path d="M14 8v7"/>
      <path d="M18 5v13"/>
      <path d="M22 10v3"/>
    </svg>
  ),
  Copy: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>
  ),
  Trash: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6"/>
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
    </svg>
  ),
  Wifi: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
      <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
      <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
      <line x1="12" y1="20" x2="12.01" y2="20"/>
    </svg>
  ),
  FileAudio: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.5 22h.5c.5 0 1-.2 1.4-.6.4-.4.6-.9.6-1.4V7.5L14.5 2H6c-.5 0-1 .2-1.4.6C4.2 3 4 3.5 4 4v3"/>
      <polyline points="14 2 14 8 20 8"/>
      <path d="M10 20v-1a2 2 0 1 1 4 0v1a2 2 0 1 1-4 0Z"/>
      <path d="M6 20v-1a2 2 0 1 0-4 0v1a2 2 0 1 0 4 0Z"/>
      <path d="M2 19v-3a6 6 0 0 1 12 0v3"/>
    </svg>
  ),
  AlertCircle: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
  ),
  Check: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  ),
  Loader: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="animate-spin">
      <line x1="12" y1="2" x2="12" y2="6"/>
      <line x1="12" y1="18" x2="12" y2="22"/>
      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
      <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
      <line x1="2" y1="12" x2="6" y2="12"/>
      <line x1="18" y1="12" x2="22" y2="12"/>
      <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>
      <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
    </svg>
  ),
};

// Format recording time
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Simple waveform visualization
const WaveformVisualization: React.FC<{
  isRecording: boolean;
  isListening?: boolean;
  isSpeaking?: boolean;
  volume?: number;
}> = ({ isRecording, isListening, isSpeaking, volume = 0 }) => {
  const bars = 20;
  const isActive = isRecording || isListening;

  return (
    <div className="flex items-center justify-center gap-1 h-12">
      {Array.from({ length: bars }).map((_, i) => {
        // For VAD mode, use actual volume level
        const barHeight = isActive
          ? isSpeaking
            ? 20 + Math.sin(i + Date.now() / 100) * 15 + (volume / 100) * 20
            : 8 + (volume / 100) * 10
          : 8;

        return (
          <div
            key={i}
            className={`w-1 rounded-full transition-all duration-150 ${
              isSpeaking
                ? 'bg-green-500'
                : isRecording
                  ? 'bg-red-500 animate-pulse'
                  : isListening
                    ? 'bg-indigo-400'
                    : 'bg-gray-300 dark:bg-gray-600'
            }`}
            style={{
              height: `${barHeight}px`,
              animationDelay: `${i * 50}ms`,
            }}
          />
        );
      })}
    </div>
  );
};

export const ASRStreamingTestPanel: React.FC<ASRStreamingTestPanelProps> = ({
  apiBaseUrl,
  wsBaseUrl,
  getAuthToken,
  selectedProvider = 'faster_whisper_large',
  language: initialLanguage = 'en',
  defaultMode = 'realtime', // Default to real-time streaming mode
  disabled = false,
  disabledReason,
  className = '',
  languages = DEFAULT_LANGUAGES,
}) => {
  const [selectedLanguage, setSelectedLanguage] = useState(initialLanguage);
  const [copied, setCopied] = useState(false);

  const {
    isRecording,
    isConnected,
    isProcessing,
    isListening,
    isSpeaking,
    volume,
    transcript,
    interimTranscript,
    error,
    status,
    mode,
    recordingTime,
    startRecording,
    stopRecording,
    clearTranscript,
    setMode,
    setLanguage,
    setProviderId,
  } = useASRStreaming({
    apiBaseUrl,
    wsBaseUrl,
    getAuthToken,
    providerId: selectedProvider,
    language: selectedLanguage,
    mode: defaultMode, // Pass defaultMode directly to hook
  });

  // Update hook state when props change
  useEffect(() => {
    setProviderId(selectedProvider);
  }, [selectedProvider, setProviderId]);

  useEffect(() => {
    setLanguage(selectedLanguage);
  }, [selectedLanguage, setLanguage]);

  // Ensure mode is set correctly on mount and when defaultMode changes
  useEffect(() => {
    if (defaultMode && mode !== defaultMode) {
      console.log('[ASRStreamingTestPanel] Setting mode to:', defaultMode, 'from:', mode);
      setMode(defaultMode);
    }
  }, [defaultMode, mode, setMode]);

  // Log mode on mount for debugging
  useEffect(() => {
    console.log('[ASRStreamingTestPanel] Initialized with mode:', mode, 'defaultMode prop:', defaultMode);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleModeChange = (newMode: ASRMode) => {
    if (!isRecording) {
      setMode(newMode);
    }
  };

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedLanguage(e.target.value);
  };

  const handleCopy = async () => {
    if (transcript) {
      await navigator.clipboard.writeText(transcript);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleToggleRecording = async () => {
    if (isRecording) {
      stopRecording();
    } else if (!disabled) {
      await startRecording();
    }
  };

  const isReady = !disabled && selectedProvider;
  const displayText = transcript + (interimTranscript ? ` ${interimTranscript}` : '');

  return (
    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="24" 
              height="24" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              className="text-indigo-600 dark:text-indigo-400 flex-shrink-0"
              style={{ display: 'block' }}
            >
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="22"/>
            </svg>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Test Speech Recognition</h3>
          </div>

          {/* Mode toggle */}
          <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => handleModeChange('vad')}
              disabled={isRecording}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                mode === 'vad'
                  ? 'bg-white dark:bg-gray-600 text-green-600 dark:text-green-300 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
              } ${isRecording ? 'opacity-50 cursor-not-allowed' : ''}`}
              title="Hands-free with Voice Activity Detection"
            >
              <Icons.Waveform />
              <span className="hidden sm:inline">VAD</span>
            </button>
            <button
              onClick={() => handleModeChange('file')}
              disabled={isRecording}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                mode === 'file'
                  ? 'bg-white dark:bg-gray-600 text-indigo-600 dark:text-indigo-300 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
              } ${isRecording ? 'opacity-50 cursor-not-allowed' : ''}`}
              title="Record then transcribe"
            >
              <Icons.FileAudio />
              <span className="hidden sm:inline">File</span>
            </button>
            <button
              onClick={() => handleModeChange('realtime')}
              disabled={isRecording}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                mode === 'realtime'
                  ? 'bg-white dark:bg-gray-600 text-indigo-600 dark:text-indigo-300 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
              } ${isRecording ? 'opacity-50 cursor-not-allowed' : ''}`}
              title="Real-time transcription with WebSocket"
            >
              <Icons.Wifi />
              <span className="hidden sm:inline">WS</span>
            </button>
          </div>
        </div>

        {/* Provider and Language info */}
        <div className="mt-2 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
          <span>Provider: <span className="font-medium text-gray-700 dark:text-gray-300">{selectedProvider}</span></span>
          <span>Mode: <span className="font-medium text-gray-700 dark:text-gray-300">{mode === 'vad' ? 'VAD (Hands-free)' : mode === 'realtime' ? 'Real-time' : 'File-based'}</span></span>
          {isConnected && (
            <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"/>
              Connected
            </span>
          )}
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

      {/* Controls */}
      <div className="p-6">
        {/* Language selector */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Language
          </label>
          <select
            value={selectedLanguage}
            onChange={handleLanguageChange}
            disabled={isRecording || disabled}
            className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
          >
            <option value="">Auto-detect</option>
            {languages.map(lang => (
              <option key={lang.code} value={lang.code}>
                {lang.flag ? `${lang.flag} ` : ''}{lang.name}
              </option>
            ))}
          </select>
        </div>

        {/* Waveform visualization */}
        <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <WaveformVisualization
            isRecording={isRecording}
            isListening={isListening}
            isSpeaking={isSpeaking}
            volume={volume}
          />
          {(isRecording || isListening) && (
            <div className="text-center mt-2">
              {mode === 'vad' ? (
                <span className={`text-sm font-medium ${isSpeaking ? 'text-green-600 dark:text-green-400' : 'text-indigo-600 dark:text-indigo-400'}`}>
                  {status || (isSpeaking ? 'Recording speech...' : 'Listening...')}
                </span>
              ) : (
                <span className="text-sm font-mono text-red-600 dark:text-red-400">
                  {formatTime(recordingTime)}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Record button */}
        <div className="flex justify-center mb-4">
          <button
            onClick={handleToggleRecording}
            disabled={disabled || isProcessing}
            className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
              isRecording
                ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
                : isReady
                  ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
                  : 'bg-gray-300 dark:bg-gray-600 text-gray-500 cursor-not-allowed'
            }`}
            title={isRecording ? 'Stop recording' : 'Start recording'}
          >
            {isProcessing ? (
              <Icons.Loader />
            ) : isRecording ? (
              <Icons.Stop />
            ) : (
              <Icons.Mic />
            )}
          </button>
        </div>

        <p className="text-center text-xs text-gray-500 dark:text-gray-400 mb-4">
          {isProcessing
            ? 'Processing audio...'
            : isRecording || isListening
              ? mode === 'vad'
                ? 'Listening... Click to stop'
                : 'Recording... Click to stop'
              : mode === 'vad'
                ? 'Click to start hands-free transcription'
                : mode === 'realtime'
                  ? 'Click to start real-time transcription'
                  : 'Click to start recording'}
        </p>
      </div>

      {/* Transcript area */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Transcript
          </label>
          <div className="flex items-center gap-2">
            {displayText && (
              <>
                <button
                  onClick={handleCopy}
                  className="p-1.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  title="Copy transcript"
                >
                  {copied ? <Icons.Check /> : <Icons.Copy />}
                </button>
                <button
                  onClick={clearTranscript}
                  className="p-1.5 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  title="Clear transcript"
                >
                  <Icons.Trash />
                </button>
              </>
            )}
          </div>
        </div>

        <div className="min-h-[100px] max-h-[200px] overflow-y-auto p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
          {displayText ? (
            <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
              {transcript}
              {interimTranscript && (
                <span className="text-gray-400 dark:text-gray-500 italic">
                  {' '}{interimTranscript}
                </span>
              )}
            </p>
          ) : (
            <p className="text-sm text-gray-400 dark:text-gray-500 italic">
              Transcribed text will appear here...
            </p>
          )}
        </div>
      </div>

      {/* Mode description */}
      <div className="px-4 pb-4">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          {mode === 'vad'
            ? 'VAD mode automatically detects speech and transcribes - hands-free!'
            : mode === 'realtime'
              ? 'Real-time mode streams audio via WebSocket (experimental)'
              : 'Record audio first, then transcribe with the selected provider'}
        </p>
      </div>
    </div>
  );
};

export default ASRStreamingTestPanel;
