/**
 * VoiceSettingsDropdown Component
 *
 * Compact voice and playback settings for the audio player.
 * Allows users to select TTS provider, voice, and playback speed.
 */

import React, { useState, useEffect, useRef } from 'react';
import { api } from '../lib/api';
import { Settings2, Volume2, Gauge, Mic2, X } from 'lucide-react';

interface VoiceSettings {
  provider_id?: string;
  voice_id?: string;
  speed?: number;
  language?: string;
}

interface Provider {
  id: string;
  name: string;
  description?: string;
  voices?: { id: string; name: string; language?: string }[];
}

interface VoiceSettingsDropdownProps {
  settings: VoiceSettings;
  onChange: (settings: VoiceSettings) => void;
  disabled?: boolean;
  className?: string;
}

// Default TTS providers with some common voices
// Kokoro first as it's currently the most reliable provider
const DEFAULT_PROVIDERS: Provider[] = [
  {
    id: 'kokoro',
    name: 'Kokoro',
    description: 'Fast and natural TTS (recommended)',
    voices: [
      { id: 'af_heart', name: 'Heart (Female)', language: 'en' },
      { id: 'af_sky', name: 'Sky (Female)', language: 'en' },
      { id: 'am_adam', name: 'Adam (Male)', language: 'en' },
      { id: 'am_michael', name: 'Michael (Male)', language: 'en' },
    ],
  },
  {
    id: 'styletts2',
    name: 'StyleTTS2',
    description: 'High-quality neural TTS',
    voices: [
      { id: 'default', name: 'Default', language: 'en' },
    ],
  },
  {
    id: 'f5tts',
    name: 'F5-TTS',
    description: 'Flow-based TTS',
    voices: [
      { id: 'default', name: 'Default', language: 'en' },
    ],
  },
  {
    id: 'melotts',
    name: 'MeloTTS',
    description: 'Multilingual TTS',
    voices: [
      { id: 'en-default', name: 'English', language: 'en' },
      { id: 'zh-default', name: 'Chinese', language: 'zh' },
    ],
  },
];

const SPEED_PRESETS = [
  { value: 0.75, label: '0.75x' },
  { value: 1.0, label: '1x' },
  { value: 1.25, label: '1.25x' },
  { value: 1.5, label: '1.5x' },
  { value: 1.75, label: '1.75x' },
  { value: 2.0, label: '2x' },
];

export const VoiceSettingsDropdown: React.FC<VoiceSettingsDropdownProps> = ({
  settings,
  onChange,
  disabled = false,
  className = '',
}) => {
  const [providers, setProviders] = useState<Provider[]>(DEFAULT_PROVIDERS);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [open]);

  // Load available providers on mount
  useEffect(() => {
    const loadProviders = async () => {
      try {
        setLoading(true);
        const response = await api.audiobook.getProviders();
        if (response.data?.providers) {
          // Backend returns providers as an object, convert to array
          const providersData = response.data.providers;
          if (Array.isArray(providersData)) {
            setProviders(providersData);
          } else if (typeof providersData === 'object') {
            // Convert object to array format
            const providersArray: Provider[] = Object.entries(providersData).map(([id, data]: [string, any]) => ({
              id,
              name: data.name || id,
              description: data.description,
              voices: data.voices || [],
            }));
            setProviders(providersArray);
          }
        }
      } catch (err) {
        console.warn('Failed to load TTS providers, using defaults');
        // Keep default providers
      } finally {
        setLoading(false);
      }
    };

    loadProviders();
  }, []);

  const currentProvider = providers.find((p) => p.id === settings.provider_id) || providers[0];
  const currentVoice = currentProvider?.voices?.find((v) => v.id === settings.voice_id);
  const currentSpeed = settings.speed || 1.0;

  const handleProviderChange = (providerId: string) => {
    const provider = providers.find((p) => p.id === providerId);
    const defaultVoice = provider?.voices?.[0]?.id;
    onChange({
      ...settings,
      provider_id: providerId,
      voice_id: defaultVoice,
    });
  };

  const handleVoiceChange = (voiceId: string) => {
    onChange({
      ...settings,
      voice_id: voiceId,
    });
  };

  const handleSpeedChange = (value: number) => {
    onChange({
      ...settings,
      speed: value,
    });
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setOpen(!open)}
        disabled={disabled}
        className={`p-2 rounded-full text-gray-300 hover:text-white transition-all ${className}`}
        title="Voice Settings"
      >
        <Settings2 className="h-5 w-5" />
      </button>

      {/* Dropdown Panel */}
      {open && (
        <div className="absolute right-0 bottom-full mb-2 w-80 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-700">
            <div className="font-semibold text-sm flex items-center gap-2 text-white">
              <Settings2 className="h-4 w-4 text-purple-400" />
              Voice Settings
            </div>
            <button
              onClick={() => setOpen(false)}
              className="p-1 text-gray-500 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="p-4 space-y-4">
            {/* Provider Selection */}
            <div className="space-y-2">
              <label className="text-xs flex items-center gap-1 text-gray-400">
                <Mic2 className="h-3 w-3" />
                TTS Provider
              </label>
              <select
                value={settings.provider_id || 'kokoro'}
                onChange={(e) => handleProviderChange(e.target.value)}
                disabled={loading}
                className="w-full h-9 px-3 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-purple-500"
              >
                {providers.map((provider) => (
                  <option key={provider.id} value={provider.id}>
                    {provider.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Voice Selection */}
            {currentProvider?.voices && currentProvider.voices.length > 0 && (
              <div className="space-y-2">
                <label className="text-xs flex items-center gap-1 text-gray-400">
                  <Volume2 className="h-3 w-3" />
                  Voice
                </label>
                <select
                  value={settings.voice_id || currentProvider.voices[0]?.id}
                  onChange={(e) => handleVoiceChange(e.target.value)}
                  className="w-full h-9 px-3 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-purple-500"
                >
                  {currentProvider.voices.map((voice) => (
                    <option key={voice.id} value={voice.id}>
                      {voice.name}
                      {voice.language && ` (${voice.language})`}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Speed Control */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs flex items-center gap-1 text-gray-400">
                  <Gauge className="h-3 w-3" />
                  Playback Speed
                </label>
                <span className="text-xs font-medium text-white">{currentSpeed.toFixed(2)}x</span>
              </div>
              <input
                type="range"
                value={currentSpeed}
                onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
                min={0.5}
                max={2}
                step={0.05}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0.5x</span>
                <span>1x</span>
                <span>2x</span>
              </div>
              {/* Quick presets */}
              <div className="flex gap-1 flex-wrap">
                {SPEED_PRESETS.map((preset) => (
                  <button
                    key={preset.value}
                    onClick={() => handleSpeedChange(preset.value)}
                    className={`h-6 px-2 text-xs rounded ${
                      currentSpeed === preset.value
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    } transition-colors`}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Current Settings Summary */}
            <div className="pt-2 border-t border-gray-700 text-xs text-gray-400">
              <p>
                Using <strong className="text-white">{currentProvider?.name || 'StyleTTS2'}</strong>
                {currentVoice && (
                  <> with <strong className="text-white">{currentVoice.name}</strong> voice</>
                )}
                {' at '}
                <strong className="text-white">{currentSpeed}x</strong> speed
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceSettingsDropdown;
