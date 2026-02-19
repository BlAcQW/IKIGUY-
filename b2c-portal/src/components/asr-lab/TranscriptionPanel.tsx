/**
 * Transcription Panel Component
 *
 * Main panel for transcribing audio files.
 */

import React, { useState, useRef, useEffect } from 'react';
import { ASRProvider } from '../../config/asr-providers';

interface TranscriptionPanelProps {
  provider: ASRProvider;
  onTranscribe: (request: any) => Promise<any>;
  isLoading: boolean;
  error: string | null;
  getLanguages: () => Promise<string[]>;
}

export const TranscriptionPanel: React.FC<TranscriptionPanelProps> = ({
  provider,
  onTranscribe,
  isLoading,
  error,
  getLanguages,
}) => {
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [language, setLanguage] = useState<string>('auto');
  const [enableDiarization, setEnableDiarization] = useState(false);
  const [enableTimestamps, setEnableTimestamps] = useState(true);
  const [enableWordTimestamps, setEnableWordTimestamps] = useState(false);
  const [transcriptionResult, setTranscriptionResult] = useState<any>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioSource, setAudioSource] = useState<'file' | 'microphone'>('file');

  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingIntervalRef = useRef<number | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAudioFile(file);
      setTranscriptionResult(null);

      // Create audio URL for playback
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      const url = URL.createObjectURL(file);
      setAudioUrl(url);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const audioFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
        setAudioFile(audioFile);

        // Create audio URL for playback
        if (audioUrl) {
          URL.revokeObjectURL(audioUrl);
        }
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      setTranscriptionResult(null);

      // Start recording timer
      recordingIntervalRef.current = window.setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Could not access microphone. Please grant microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
        recordingIntervalRef.current = null;
      }
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
    };
  }, [audioUrl]);

  const handleTranscribe = async () => {
    if (!audioFile) return;

    const result = await onTranscribe({
      audio: audioFile,
      language: language === 'auto' ? undefined : language,
      enableDiarization,
      enableTimestamps,
      enableWordTimestamps,
    });

    if (result) {
      setTranscriptionResult(result);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTimestamp = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(2);
    return `${mins}:${secs.padStart(5, '0')}`;
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Transcribe Audio</h2>

      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
        {/* Audio Source Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Audio Source
          </label>
          <div className="flex space-x-4">
            <button
              onClick={() => setAudioSource('file')}
              className={`flex-1 px-4 py-3 border rounded-lg transition-colors ${
                audioSource === 'file'
                  ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                  : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              <span className="text-lg mr-2">📁</span>
              Upload File
            </button>
            <button
              onClick={() => setAudioSource('microphone')}
              className={`flex-1 px-4 py-3 border rounded-lg transition-colors ${
                audioSource === 'microphone'
                  ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                  : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              <span className="text-lg mr-2">🎤</span>
              Record Audio
            </button>
          </div>
        </div>

        {/* File Upload */}
        {audioSource === 'file' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Audio File
            </label>
            <div className="flex items-center space-x-4">
              <input
                ref={fileInputRef}
                type="file"
                accept="audio/*"
                onChange={handleFileSelect}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Choose Audio File
              </button>
              {audioFile && audioSource === 'file' && (
                <span className="text-sm text-gray-600">
                  {audioFile.name} ({(audioFile.size / 1024 / 1024).toFixed(2)} MB)
                </span>
              )}
            </div>
          </div>
        )}

        {/* Microphone Recording */}
        {audioSource === 'microphone' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Record Audio
            </label>
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                {!isRecording ? (
                  <button
                    onClick={startRecording}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <circle cx="10" cy="10" r="8" />
                    </svg>
                    <span>Start Recording</span>
                  </button>
                ) : (
                  <button
                    onClick={stopRecording}
                    className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition-colors flex items-center space-x-2"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <rect x="6" y="6" width="8" height="8" />
                    </svg>
                    <span>Stop Recording</span>
                  </button>
                )}
                {isRecording && (
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse delay-100"></div>
                      <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse delay-200"></div>
                    </div>
                    <span className="text-sm text-gray-700 font-medium">
                      {Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')}
                    </span>
                  </div>
                )}
              </div>
              {audioFile && audioSource === 'microphone' && !isRecording && (
                <p className="text-sm text-green-600">
                  ✓ Recording complete ({Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')})
                </p>
              )}
            </div>
          </div>
        )}

        {/* Audio Player */}
        {audioUrl && !isRecording && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Preview Audio
            </label>
            <audio
              ref={audioRef}
              src={audioUrl}
              controls
              className="w-full"
            />
          </div>
        )}

        {/* Language Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Language
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="auto">Auto-detect</option>
            {provider.languageList?.slice(0, 20).map((lang) => (
              <option key={lang} value={lang}>
                {lang.toUpperCase()}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Supports {provider.languages}+ languages
          </p>
        </div>

        {/* Options */}
        <div className="space-y-3">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Transcription Options
          </label>

          {provider.capabilities.diarization && (
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="diarization"
                checked={enableDiarization}
                onChange={(e) => setEnableDiarization(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="diarization" className="text-sm text-gray-700">
                Enable Speaker Diarization (who spoke when)
              </label>
            </div>
          )}

          {provider.capabilities.timestamps && (
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="timestamps"
                checked={enableTimestamps}
                onChange={(e) => setEnableTimestamps(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="timestamps" className="text-sm text-gray-700">
                Include Timestamps
              </label>
            </div>
          )}

          {provider.capabilities.wordLevelTimestamps && (
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="word-timestamps"
                checked={enableWordTimestamps}
                onChange={(e) => setEnableWordTimestamps(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="word-timestamps" className="text-sm text-gray-700">
                Word-level Timestamps (more detailed)
              </label>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Transcribe Button */}
        <button
          onClick={handleTranscribe}
          disabled={!audioFile || isLoading}
          className="w-full px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
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
              Transcribing...
            </span>
          ) : (
            'Transcribe Audio'
          )}
        </button>

        {/* Transcription Result */}
        {transcriptionResult && (
          <div className="mt-6 space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Transcription Result</h3>

            {/* Full Text */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Full Text</h4>
              <p className="text-gray-900 whitespace-pre-wrap">{transcriptionResult.text}</p>
            </div>

            {/* Metadata */}
            <div className="grid grid-cols-2 gap-4">
              {transcriptionResult.language && (
                <div className="text-sm">
                  <span className="text-gray-500">Detected Language:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    {transcriptionResult.language.toUpperCase()}
                  </span>
                </div>
              )}
              {transcriptionResult.duration && (
                <div className="text-sm">
                  <span className="text-gray-500">Duration:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    {formatDuration(transcriptionResult.duration)}
                  </span>
                </div>
              )}
            </div>

            {/* Segments with Timestamps */}
            {transcriptionResult.segments && transcriptionResult.segments.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">Segments</h4>
                <div className="max-h-96 overflow-y-auto space-y-2">
                  {transcriptionResult.segments.map((segment: any, idx: number) => (
                    <div key={idx} className="bg-white border border-gray-200 rounded-lg p-3">
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-xs text-gray-500">
                          {formatTimestamp(segment.start)} → {formatTimestamp(segment.end)}
                        </span>
                        {segment.speaker && (
                          <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-800 rounded">
                            {segment.speaker}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-900">{segment.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Export Options */}
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  const blob = new Blob([transcriptionResult.text], { type: 'text/plain' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'transcription.txt';
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Export as TXT
              </button>
              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(transcriptionResult, null, 2)], {
                    type: 'application/json',
                  });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'transcription.json';
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Export as JSON
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
