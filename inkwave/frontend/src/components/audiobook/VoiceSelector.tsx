/**
 * VoiceSelector Component
 *
 * Voice and provider selection for audiobook narration.
 * Supports OpenAI voices (alloy, echo, fable, onyx, nova, shimmer)
 * and other TTS providers.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Mic, Check, Sparkles } from 'lucide-react';

interface Voice {
  id: string;
  name: string;
  description: string;
  gender: string;
  accent?: string;
  bestFor?: string[];
}

interface Provider {
  id: string;
  name: string;
  description: string;
  voices: Voice[];
  recommended?: boolean;
  costPer1mChars?: number;
}

interface VoiceSelectorProps {
  currentProvider: string;
  currentVoice: string;
  onProviderChange: (provider: string) => void;
  onVoiceChange: (voice: string) => void;
}

// OpenAI voices with full metadata
const OPENAI_VOICES: Voice[] = [
  {
    id: 'alloy',
    name: 'Alloy',
    description: 'Balanced, neutral - great for general narration',
    gender: 'neutral',
    accent: 'American',
    bestFor: ['non-fiction', 'general', 'audiobooks'],
  },
  {
    id: 'echo',
    name: 'Echo',
    description: 'Deep, warm - male protagonists, non-fiction',
    gender: 'male',
    accent: 'American',
    bestFor: ['thrillers', 'business', 'biography'],
  },
  {
    id: 'fable',
    name: 'Fable',
    description: 'British, expressive - fiction, storytelling',
    gender: 'neutral',
    accent: 'British',
    bestFor: ['fiction', 'fantasy', "children's books"],
  },
  {
    id: 'onyx',
    name: 'Onyx',
    description: 'Deep, authoritative - business, self-help',
    gender: 'male',
    accent: 'American',
    bestFor: ['self-help', 'business', 'motivational'],
  },
  {
    id: 'nova',
    name: 'Nova',
    description: "Young, friendly - YA, children's books",
    gender: 'female',
    accent: 'American',
    bestFor: ['young adult', "children's", 'contemporary'],
  },
  {
    id: 'shimmer',
    name: 'Shimmer',
    description: 'Soft, gentle - romance, meditation',
    gender: 'female',
    accent: 'American',
    bestFor: ['romance', 'poetry', 'meditation'],
  },
];

// Available providers
const PROVIDERS: Provider[] = [
  {
    id: 'openai_tts',
    name: 'OpenAI TTS',
    description: 'High-quality voices - recommended for audiobooks',
    voices: OPENAI_VOICES,
    recommended: true,
    costPer1mChars: 15,
  },
  {
    id: 'openai_tts_hd',
    name: 'OpenAI TTS HD',
    description: 'Premium quality - enhanced clarity',
    voices: OPENAI_VOICES,
    costPer1mChars: 30,
  },
  {
    id: 'styletts2',
    name: 'StyleTTS2',
    description: 'Expressive, natural narration',
    voices: [
      {
        id: 'default',
        name: 'Default',
        description: 'Natural, expressive voice',
        gender: 'neutral',
      },
    ],
  },
  {
    id: 'kokoro',
    name: 'Kokoro',
    description: 'Fast, reliable synthesis',
    voices: [
      {
        id: 'af_sky',
        name: 'Sky',
        description: 'Clear, articulate voice',
        gender: 'female',
      },
      {
        id: 'am_adam',
        name: 'Adam',
        description: 'Warm, engaging voice',
        gender: 'male',
      },
    ],
  },
];

export default function VoiceSelector({
  currentProvider,
  currentVoice,
  onProviderChange,
  onVoiceChange,
}: VoiceSelectorProps) {
  const [isProviderOpen, setIsProviderOpen] = useState(false);
  const [isVoiceOpen, setIsVoiceOpen] = useState(false);
  const [voices, setVoices] = useState<Voice[]>([]);

  // Get current provider data
  const selectedProvider = PROVIDERS.find((p) => p.id === currentProvider) || PROVIDERS[0];

  // Fetch voices when provider changes
  useEffect(() => {
    fetchVoices(currentProvider);
  }, [currentProvider]);

  const fetchVoices = async (providerId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/audiobook/voices/${providerId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setVoices(data.voices);
      } else {
        // Fallback to static data
        const provider = PROVIDERS.find((p) => p.id === providerId);
        setVoices(provider?.voices || []);
      }
    } catch (error) {
      console.error('Failed to fetch voices:', error);
      const provider = PROVIDERS.find((p) => p.id === providerId);
      setVoices(provider?.voices || []);
    }
  };

  const handleProviderSelect = (providerId: string) => {
    onProviderChange(providerId);
    setIsProviderOpen(false);

    // Reset voice to first voice of new provider
    const provider = PROVIDERS.find((p) => p.id === providerId);
    if (provider && provider.voices.length > 0) {
      onVoiceChange(provider.voices[0].id);
    }
  };

  const handleVoiceSelect = (voiceId: string) => {
    onVoiceChange(voiceId);
    setIsVoiceOpen(false);
  };

  const selectedVoice = voices.find((v) => v.id === currentVoice) || voices[0];

  return (
    <div className="w-full bg-gray-800/50 rounded-xl p-4 border border-gray-700">
      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
        <Mic className="w-4 h-4 text-purple-400" />
        Voice Settings
      </h3>

      <div className="grid grid-cols-2 gap-3">
        {/* Provider Selector */}
        <div className="relative">
          <label className="text-xs text-gray-400 mb-1 block">Provider</label>
          <button
            onClick={() => {
              setIsProviderOpen(!isProviderOpen);
              setIsVoiceOpen(false);
            }}
            className="w-full flex items-center justify-between bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white transition"
          >
            <span className="flex items-center gap-2">
              {selectedProvider.recommended && (
                <Sparkles className="w-3 h-3 text-yellow-400" />
              )}
              {selectedProvider.name}
            </span>
            <ChevronDown
              className={`w-4 h-4 transition-transform ${
                isProviderOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          <AnimatePresence>
            {isProviderOpen && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute z-20 top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl overflow-hidden"
              >
                {PROVIDERS.map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => handleProviderSelect(provider.id)}
                    className={`w-full px-3 py-2 text-left hover:bg-gray-700 transition flex items-center justify-between ${
                      provider.id === currentProvider ? 'bg-gray-700' : ''
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-2 text-sm text-white">
                        {provider.recommended && (
                          <Sparkles className="w-3 h-3 text-yellow-400" />
                        )}
                        {provider.name}
                      </div>
                      <div className="text-[10px] text-gray-400">
                        {provider.description}
                      </div>
                    </div>
                    {provider.id === currentProvider && (
                      <Check className="w-4 h-4 text-purple-400" />
                    )}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Voice Selector */}
        <div className="relative">
          <label className="text-xs text-gray-400 mb-1 block">Voice</label>
          <button
            onClick={() => {
              setIsVoiceOpen(!isVoiceOpen);
              setIsProviderOpen(false);
            }}
            className="w-full flex items-center justify-between bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white transition"
          >
            <span>{selectedVoice?.name || 'Select voice'}</span>
            <ChevronDown
              className={`w-4 h-4 transition-transform ${
                isVoiceOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          <AnimatePresence>
            {isVoiceOpen && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute z-20 top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl overflow-hidden max-h-64 overflow-y-auto"
              >
                {voices.map((voice) => (
                  <button
                    key={voice.id}
                    onClick={() => handleVoiceSelect(voice.id)}
                    className={`w-full px-3 py-2 text-left hover:bg-gray-700 transition ${
                      voice.id === currentVoice ? 'bg-gray-700' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-white flex items-center gap-2">
                          {voice.name}
                          <span className="text-[10px] text-gray-500 bg-gray-700/50 px-1.5 py-0.5 rounded">
                            {voice.gender}
                          </span>
                        </div>
                        <div className="text-[10px] text-gray-400 mt-0.5">
                          {voice.description}
                        </div>
                      </div>
                      {voice.id === currentVoice && (
                        <Check className="w-4 h-4 text-purple-400 flex-shrink-0" />
                      )}
                    </div>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Cost indicator for OpenAI */}
      {selectedProvider.costPer1mChars && (
        <div className="mt-3 text-[10px] text-gray-500 text-center">
          Cost: ${selectedProvider.costPer1mChars}/1M characters
        </div>
      )}
    </div>
  );
}
