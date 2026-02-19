/**
 * Live Transcription Panel Component
 *
 * Real-time speech-to-text transcription panel with microphone input.
 */

import React, { useState, useRef, useEffect } from 'react';
import { ASRProvider } from '../../config/asr-providers';
import { API_ENDPOINTS } from '../../config/api-config';

interface LiveTranscriptionPanelProps {
  provider: ASRProvider;
  onTranscribe: (request: any) => Promise<any>;
  isLoading: boolean;
  error: string | null;
}

interface TranscriptionSegment {
  text: string;
  timestamp: number;
  isFinal: boolean;
}

export const LiveTranscriptionPanel: React.FC<LiveTranscriptionPanelProps> = ({
  provider,
  onTranscribe,
  isLoading,
  error,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [segments, setSegments] = useState<TranscriptionSegment[]>([]);
  const [currentSegment, setCurrentSegment] = useState<string>('');
  const [recordingTime, setRecordingTime] = useState(0);
  const [language, setLanguage] = useState<string>('auto');

  const audioContextRef = useRef<AudioContext | null>(null);
  const audioWorkletNodeRef = useRef<AudioWorkletNode | null>(null);
  const recordingIntervalRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const segmentsEndRef = useRef<HTMLDivElement>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const useWebSocketStreaming = provider.id === 'akan_whisper_giftmark'; // Use WebSocket for Akan model
  const lastTranscriptionRef = useRef<string>(''); // Track last transcription to avoid duplicates
  const segmentTimerRef = useRef<number | null>(null); // Timer to auto-finalize segments

  // Auto-scroll to bottom when new segments are added
  useEffect(() => {
    segmentsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [segments, currentSegment]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording();
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
      if (segmentTimerRef.current) {
        clearTimeout(segmentTimerRef.current);
      }
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, []);

  const initializeWebSocket = () => {
    if (websocketRef.current) {
      websocketRef.current.close();
    }

    const ws = new WebSocket(API_ENDPOINTS.voice.lab.streamWs);

    ws.onopen = () => {
      console.log('WebSocket connected for Akan streaming');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'partial_transcript') {
          const newText = data.text || '';

          // Skip empty transcriptions
          if (!newText.trim()) {
            return;
          }

          // Check if this is a new transcription (different from last one)
          if (newText !== lastTranscriptionRef.current) {
            // Just update the current segment - don't finalize intermediate results
            setCurrentSegment(newText);
            lastTranscriptionRef.current = newText;

            // Clear any existing auto-finalize timer
            if (segmentTimerRef.current) {
              clearTimeout(segmentTimerRef.current);
            }

            // Auto-finalize after 3 seconds of no new transcriptions
            // This gives time for the model to send better results
            segmentTimerRef.current = window.setTimeout(() => {
              if (newText && newText === lastTranscriptionRef.current) {
                // Only finalize if this is still the current text
                setSegments((prev) => [
                  ...prev,
                  {
                    text: newText,
                    timestamp: Date.now(),
                    isFinal: true,
                  },
                ]);
                setCurrentSegment('');
                lastTranscriptionRef.current = '';
              }
            }, 3000);
          }
        } else if (data.type === 'error') {
          console.error('WebSocket error:', data.message);
          setError(data.message || 'Streaming error');
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection failed');
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
    };

    websocketRef.current = ws;
  };

  const sendPCMAudioViaWebSocket = (pcmData: Int16Array) => {
    if (!websocketRef.current || websocketRef.current.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected');
      return;
    }

    try {
      // Convert Int16Array to base64 for transmission
      const uint8Array = new Uint8Array(pcmData.buffer);
      const base64Audio = btoa(String.fromCharCode.apply(null, Array.from(uint8Array)));

      const message = {
        type: 'audio_chunk',
        audio: base64Audio,
        dialect: language === 'auto' ? 'asante' : language,
        format: 'pcm_s16le',  // Indicate raw PCM format
        sample_rate: 16000,
        channels: 1,
      };
      websocketRef.current.send(JSON.stringify(message));
    } catch (err) {
      console.error('Failed to send PCM audio chunk:', err);
    }
  };

  const startRecording = async () => {
    try {
      // Initialize WebSocket for streaming
      if (useWebSocketStreaming) {
        initializeWebSocket();
      }

      // Get microphone stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      // Create AudioContext
      const audioContext = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = audioContext;

      // Load AudioWorklet processor
      await audioContext.audioWorklet.addModule('/audio-processor.js');

      // Create audio source from microphone
      const source = audioContext.createMediaStreamSource(stream);

      // Create AudioWorkletNode
      const workletNode = new AudioWorkletNode(audioContext, 'audio-processor');
      audioWorkletNodeRef.current = workletNode;

      // Handle PCM data from AudioWorklet
      workletNode.port.onmessage = (event) => {
        if (event.data.type === 'pcm_data') {
          const pcmData: Int16Array = event.data.data;

          // Send PCM data via WebSocket for real-time streaming
          if (useWebSocketStreaming) {
            sendPCMAudioViaWebSocket(pcmData);
          }
        }
      };

      // Start recording in the AudioWorklet
      workletNode.port.postMessage({ command: 'START_RECORDING' });

      // Connect audio graph
      source.connect(workletNode);
      workletNode.connect(audioContext.destination);

      setIsRecording(true);
      setRecordingTime(0);
      setSegments([]);
      setCurrentSegment('');
      lastTranscriptionRef.current = '';

      // Clear any existing timer
      if (segmentTimerRef.current) {
        clearTimeout(segmentTimerRef.current);
        segmentTimerRef.current = null;
      }

      // Start recording timer
      recordingIntervalRef.current = window.setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Could not access microphone. Please grant microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (isRecording) {
      setIsRecording(false);

      // Stop recording in AudioWorklet
      if (audioWorkletNodeRef.current) {
        audioWorkletNodeRef.current.port.postMessage({ command: 'STOP_RECORDING' });
        audioWorkletNodeRef.current.disconnect();
        audioWorkletNodeRef.current.port.close();
        audioWorkletNodeRef.current = null;
      }

      // Close AudioContext
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }

      // Stop all audio tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }

      // Clear recording timer
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
        recordingIntervalRef.current = null;
      }

      // Clear segment auto-finalize timer
      if (segmentTimerRef.current) {
        clearTimeout(segmentTimerRef.current);
        segmentTimerRef.current = null;
      }

      // Close WebSocket
      if (useWebSocketStreaming && websocketRef.current) {
        websocketRef.current.send(JSON.stringify({ type: 'close' }));
        websocketRef.current.close();
        websocketRef.current = null;
      }

      // Finalize current segment
      if (currentSegment) {
        setSegments((prev) => [
          ...prev,
          {
            text: currentSegment,
            timestamp: Date.now(),
            isFinal: true,
          },
        ]);
        setCurrentSegment('');
      }

      // Reset last transcription ref
      lastTranscriptionRef.current = '';
    }
  };


  const finalizeSegment = () => {
    if (currentSegment) {
      // Clear any pending auto-finalize timer
      if (segmentTimerRef.current) {
        clearTimeout(segmentTimerRef.current);
        segmentTimerRef.current = null;
      }

      setSegments((prev) => [
        ...prev,
        {
          text: currentSegment,
          timestamp: Date.now(),
          isFinal: true,
        },
      ]);
      setCurrentSegment('');
      lastTranscriptionRef.current = '';
    }
  };

  const clearTranscription = () => {
    // Clear any pending timer
    if (segmentTimerRef.current) {
      clearTimeout(segmentTimerRef.current);
      segmentTimerRef.current = null;
    }

    setSegments([]);
    setCurrentSegment('');
    lastTranscriptionRef.current = '';
  };

  const exportTranscription = () => {
    const fullText = segments.map((seg) => seg.text).join(' ');
    const blob = new Blob([fullText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `live-transcription-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Check if provider supports real-time
  if (!provider.capabilities?.realtime) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-full">
          <div className="text-center bg-yellow-50 border border-yellow-200 rounded-lg p-8 max-w-md">
            <div className="text-6xl mb-4">⚠️</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Real-time Not Supported
            </h3>
            <p className="text-gray-600">
              The selected provider <strong>{provider.name}</strong> does not support real-time
              transcription. Please select a provider with real-time capability like{' '}
              <strong>Faster Whisper</strong> or <strong>Whisper Streaming</strong>.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 h-full flex flex-col">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Live Transcription</h2>

      {/* Controls */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4 mb-6">
        {/* Language Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={isRecording}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <option value="auto">Auto-detect</option>
            {provider.languageList?.slice(0, 20).map((lang) => (
              <option key={lang} value={lang}>
                {lang.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Recording Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {!isRecording ? (
              <button
                onClick={startRecording}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2 font-medium"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <circle cx="10" cy="10" r="8" />
                </svg>
                <span>Start Live Transcription</span>
              </button>
            ) : (
              <>
                <button
                  onClick={stopRecording}
                  className="px-6 py-3 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition-colors flex items-center space-x-2 font-medium"
                >
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <rect x="6" y="6" width="8" height="8" />
                  </svg>
                  <span>Stop Recording</span>
                </button>

                <button
                  onClick={finalizeSegment}
                  className="px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
                >
                  Finalize Segment
                </button>
              </>
            )}
          </div>

          {isRecording && (
            <div className="flex items-center space-x-3">
              <div className="flex space-x-1">
                <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse"></div>
                <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse delay-100"></div>
                <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse delay-200"></div>
              </div>
              <span className="text-lg font-bold text-gray-900">
                {formatDuration(recordingTime)}
              </span>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        {segments.length > 0 && (
          <div className="flex items-center space-x-2 pt-4 border-t">
            <button
              onClick={exportTranscription}
              disabled={isRecording}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Export Transcription
            </button>
            <button
              onClick={clearTranscription}
              disabled={isRecording}
              className="px-4 py-2 border border-red-300 rounded-lg text-sm font-medium text-red-700 hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Clear All
            </button>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Transcription Display */}
      <div className="flex-1 bg-white rounded-lg border border-gray-200 overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h3 className="text-lg font-semibold text-gray-900">Live Transcription</h3>
          <p className="text-sm text-gray-500 mt-1">
            {isRecording
              ? 'Speaking now... (Transcription appears below in real-time)'
              : 'Start recording to see live transcription'}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {segments.length === 0 && !currentSegment && !isRecording && (
            <div className="text-center text-gray-400 py-12">
              <div className="text-6xl mb-4">🎤</div>
              <p className="text-lg">No transcription yet</p>
              <p className="text-sm mt-2">Click "Start Live Transcription" to begin</p>
            </div>
          )}

          {/* Finalized Segments */}
          {segments.map((segment, idx) => (
            <div
              key={idx}
              className="bg-gray-50 border border-gray-200 rounded-lg p-4 animate-fade-in"
            >
              <div className="flex items-start justify-between mb-2">
                <span className="text-xs text-gray-500">
                  {new Date(segment.timestamp).toLocaleTimeString()}
                </span>
                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-800 rounded">
                  Final
                </span>
              </div>
              <p className="text-gray-900">{segment.text}</p>
            </div>
          ))}

          {/* Current Segment (Live) */}
          {currentSegment && (
            <div className="bg-indigo-50 border-2 border-indigo-300 rounded-lg p-4 animate-pulse-slow">
              <div className="flex items-start justify-between mb-2">
                <span className="text-xs text-indigo-600 font-medium">
                  {new Date().toLocaleTimeString()}
                </span>
                <span className="text-xs px-2 py-0.5 bg-indigo-200 text-indigo-800 rounded flex items-center space-x-1">
                  <span className="w-2 h-2 bg-indigo-600 rounded-full animate-pulse"></span>
                  <span>Live</span>
                </span>
              </div>
              <p className="text-gray-900 font-medium">{currentSegment}</p>
            </div>
          )}

          <div ref={segmentsEndRef} />
        </div>
      </div>
    </div>
  );
};
