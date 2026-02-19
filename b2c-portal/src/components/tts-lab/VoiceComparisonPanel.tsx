/**
 * Voice Comparison Panel Component
 *
 * Allows users to compare different voices side-by-side by synthesizing
 * the same text with multiple providers/voices.
 *
 * Created: 2025-10-27
 * Sprint 4: Advanced Features (Phase 9)
 */

import React, { useState, useRef, useEffect } from 'react';
import { TTSProvider } from '../../config/tts-providers';
import { ExportFormatModal } from './ExportFormatModal';

interface VoiceComparisonPanelProps {
  provider: TTSProvider;
  providers: Record<string, TTSProvider>;
  synthesize: (params: {
    text: string;
    language?: string;
    speaker?: string | number;
    speed?: number;
    pitch?: number;
  }) => Promise<Blob | null>;
  getLanguages: () => Promise<string[]>;
  getSpeakers: (language?: string) => Promise<string[]>;
}

interface ComparisonVoice {
  id: string;
  provider: TTSProvider;
  speaker?: string | number;
  audioUrl: string | null;
  audioBlob: Blob | null;
  isLoading: boolean;
  error: string | null;
  duration: number;
}

export const VoiceComparisonPanel: React.FC<VoiceComparisonPanelProps> = ({
  provider,
  providers,
  synthesize,
  getLanguages,
  getSpeakers,
}) => {
  const [text, setText] = useState('');
  const [language, setLanguage] = useState('en');
  const [speed, setSpeed] = useState(1.0);
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([]);
  const [availableSpeakers, setAvailableSpeakers] = useState<string[]>([]);

  // Comparison voices
  const [comparisonVoices, setComparisonVoices] = useState<ComparisonVoice[]>([]);
  const [selectedVoices, setSelectedVoices] = useState<string[]>([]);
  const [isPlayingAll, setIsPlayingAll] = useState(false);
  const [exportingVoiceId, setExportingVoiceId] = useState<string | null>(null);

  // Audio refs for synchronized playback
  const audioRefs = useRef<Map<string, HTMLAudioElement>>(new Map());

  // Load available languages
  useEffect(() => {
    const loadLanguages = async () => {
      const langs = await getLanguages();
      setAvailableLanguages(langs);
      if (langs.length > 0) {
        setLanguage(langs[0]);
      }
    };
    loadLanguages();
  }, [provider.id, getLanguages]);

  // Load available speakers for multi-speaker providers
  useEffect(() => {
    if (provider.capabilities.multiSpeaker) {
      const loadSpeakers = async () => {
        const speakers = await getSpeakers(language);
        setAvailableSpeakers(speakers);
      };
      loadSpeakers();
    }
  }, [language, provider.id, provider.capabilities.multiSpeaker, getSpeakers]);

  // Get available voices for comparison
  const getAvailableVoices = () => {
    const voices: { id: string; label: string; provider: TTSProvider; speaker?: string | number }[] = [];

    // Add voices from multi-speaker providers
    Object.values(providers).forEach((prov) => {
      if (prov.status === 'online' && prov.capabilities.multiSpeaker) {
        // For simplicity, add first 5 speakers
        for (let i = 0; i < Math.min(5, availableSpeakers.length || 5); i++) {
          voices.push({
            id: `${prov.id}_speaker_${i}`,
            label: `${prov.name} - Speaker ${i}`,
            provider: prov,
            speaker: i,
          });
        }
      } else if (prov.status === 'online') {
        // Single voice providers
        voices.push({
          id: `${prov.id}_default`,
          label: prov.name,
          provider: prov,
        });
      }
    });

    return voices;
  };

  const availableVoices = getAvailableVoices();

  const handleVoiceToggle = (voiceId: string) => {
    setSelectedVoices((prev) => {
      if (prev.includes(voiceId)) {
        return prev.filter((id) => id !== voiceId);
      } else {
        return [...prev, voiceId];
      }
    });
  };

  const handleCompare = async () => {
    if (!text.trim()) {
      alert('Please enter text to synthesize');
      return;
    }

    if (selectedVoices.length === 0) {
      alert('Please select at least one voice to compare');
      return;
    }

    if (selectedVoices.length > 6) {
      alert('Maximum 6 voices can be compared at once');
      return;
    }

    // Clear previous results
    setComparisonVoices([]);

    // Initialize comparison voices
    const newVoices: ComparisonVoice[] = selectedVoices.map((voiceId) => {
      const voice = availableVoices.find((v) => v.id === voiceId)!;
      return {
        id: voiceId,
        provider: voice.provider,
        speaker: voice.speaker,
        audioUrl: null,
        audioBlob: null,
        isLoading: true,
        error: null,
        duration: 0,
      };
    });

    setComparisonVoices(newVoices);

    // Synthesize each voice
    for (let i = 0; i < newVoices.length; i++) {
      const voice = newVoices[i];

      try {
        const audioBlob = await synthesize({
          text,
          language,
          speaker: voice.speaker,
          speed,
        });

        if (audioBlob) {
          const audioUrl = URL.createObjectURL(audioBlob);

          // Get audio duration
          const audio = new Audio(audioUrl);
          await new Promise<void>((resolve) => {
            audio.onloadedmetadata = () => {
              resolve();
            };
          });

          // Update comparison voice
          setComparisonVoices((prev) =>
            prev.map((v) =>
              v.id === voice.id
                ? {
                    ...v,
                    audioUrl,
                    audioBlob,
                    isLoading: false,
                    duration: audio.duration,
                  }
                : v
            )
          );
        } else {
          setComparisonVoices((prev) =>
            prev.map((v) =>
              v.id === voice.id
                ? {
                    ...v,
                    isLoading: false,
                    error: 'Synthesis failed',
                  }
                : v
            )
          );
        }
      } catch (err: any) {
        setComparisonVoices((prev) =>
          prev.map((v) =>
            v.id === voice.id
              ? {
                  ...v,
                  isLoading: false,
                  error: err.message || 'Unknown error',
                }
              : v
          )
        );
      }
    }
  };

  const handlePlayAll = () => {
    if (isPlayingAll) {
      // Stop all
      audioRefs.current.forEach((audio) => {
        audio.pause();
        audio.currentTime = 0;
      });
      setIsPlayingAll(false);
    } else {
      // Play all simultaneously
      audioRefs.current.forEach((audio) => {
        audio.currentTime = 0;
        audio.play();
      });
      setIsPlayingAll(true);
    }
  };

  const handleAudioRef = (voiceId: string, element: HTMLAudioElement | null) => {
    if (element) {
      audioRefs.current.set(voiceId, element);

      // Handle ended event
      element.onended = () => {
        // Check if all audios have ended
        const allEnded = Array.from(audioRefs.current.values()).every(
          (audio) => audio.ended || audio.paused
        );
        if (allEnded) {
          setIsPlayingAll(false);
        }
      };
    } else {
      audioRefs.current.delete(voiceId);
    }
  };

  const handleDownload = (voice: ComparisonVoice) => {
    if (!voice.audioUrl) return;

    const a = document.createElement('a');
    a.href = voice.audioUrl;
    a.download = `comparison_${voice.provider.id}_${Date.now()}.wav`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <span className="text-blue-600 text-xl">ℹ️</span>
          <div>
            <h4 className="font-medium text-blue-900 text-sm">Voice Comparison</h4>
            <p className="text-xs text-blue-700 mt-1">
              Compare different voices side-by-side by synthesizing the same text with multiple
              providers or speakers. Select up to 6 voices to compare.
            </p>
          </div>
        </div>
      </div>

      {/* Text Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Text to Synthesize
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter text to compare across different voices..."
          className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none text-gray-900 placeholder:text-gray-400"
        />
        <p className="mt-2 text-sm text-gray-500">{text.length} characters</p>
      </div>

      {/* Settings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Language Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900"
          >
            {availableLanguages.map((lang) => (
              <option key={lang} value={lang}>
                {lang.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Speed Control */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Speed: {speed.toFixed(1)}x
          </label>
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={speed}
            onChange={(e) => setSpeed(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
        </div>
      </div>

      {/* Voice Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Select Voices to Compare ({selectedVoices.length}/6)
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {availableVoices.slice(0, 12).map((voice) => (
            <button
              key={voice.id}
              onClick={() => handleVoiceToggle(voice.id)}
              disabled={!selectedVoices.includes(voice.id) && selectedVoices.length >= 6}
              className={`p-3 rounded-lg border-2 text-left transition-all ${
                selectedVoices.includes(voice.id)
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              } ${
                !selectedVoices.includes(voice.id) && selectedVoices.length >= 6
                  ? 'opacity-50 cursor-not-allowed'
                  : ''
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">{voice.label}</span>
                {selectedVoices.includes(voice.id) && (
                  <span className="text-indigo-600">✓</span>
                )}
              </div>
              <span className="text-xs text-gray-600 mt-1 block">
                {voice.provider.type}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Compare Button */}
      <div className="flex space-x-4">
        <button
          onClick={handleCompare}
          disabled={!text.trim() || selectedVoices.length === 0}
          className={`
            flex-1 px-6 py-3 rounded-lg font-medium text-white
            ${
              !text.trim() || selectedVoices.length === 0
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800'
            }
            transition-colors duration-200
          `}
        >
          Compare Voices
        </button>
      </div>

      {/* Comparison Results */}
      {comparisonVoices.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Comparison Results</h3>
            <button
              onClick={handlePlayAll}
              disabled={comparisonVoices.some((v) => v.isLoading || v.error)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm font-medium transition-colors"
            >
              {isPlayingAll ? '⏸️ Stop All' : '▶️ Play All'}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {comparisonVoices.map((voice) => (
              <div
                key={voice.id}
                className="bg-white border border-gray-200 rounded-lg p-4 space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">{voice.provider.name}</h4>
                    {voice.speaker !== undefined && (
                      <p className="text-xs text-gray-600">Speaker {voice.speaker}</p>
                    )}
                  </div>
                  {voice.duration > 0 && (
                    <span className="text-xs text-gray-500">
                      {voice.duration.toFixed(1)}s
                    </span>
                  )}
                </div>

                {voice.isLoading && (
                  <div className="flex items-center justify-center py-4">
                    <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                )}

                {voice.error && (
                  <div className="bg-red-50 border border-red-200 rounded p-2">
                    <p className="text-xs text-red-700">{voice.error}</p>
                  </div>
                )}

                {voice.audioUrl && !voice.isLoading && !voice.error && (
                  <>
                    <audio
                      ref={(el) => handleAudioRef(voice.id, el)}
                      controls
                      src={voice.audioUrl}
                      className="w-full"
                    />
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleDownload(voice)}
                        className="flex-1 px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-xs font-medium hover:bg-gray-200 transition-colors"
                      >
                        Download WAV
                      </button>
                      <button
                        onClick={() => setExportingVoiceId(voice.id)}
                        className="flex-1 px-3 py-1.5 bg-indigo-600 text-white rounded text-xs font-medium hover:bg-indigo-700 transition-colors"
                      >
                        Export As...
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Export Format Modal */}
      {exportingVoiceId && (
        <ExportFormatModal
          isOpen={true}
          onClose={() => setExportingVoiceId(null)}
          audioBlob={comparisonVoices.find((v) => v.id === exportingVoiceId)?.audioBlob || null}
          filename={`comparison_${comparisonVoices.find((v) => v.id === exportingVoiceId)?.provider.id}_${Date.now()}`}
        />
      )}
    </div>
  );
};
