/**
 * VoiceControlPanel Component
 *
 * Controls for voice speed, pitch, and language selection.
 * Provides sliders with real-time feedback and visual indicators.
 */

import { Gauge, Music, Globe } from 'lucide-react'

interface VoiceControlPanelProps {
  speed: number
  pitch: number
  language: string
  onSpeedChange: (speed: number) => void
  onPitchChange: (pitch: number) => void
  onLanguageChange: (language: string) => void
}

interface Language {
  code: string
  name: string
  flag: string
}

export default function VoiceControlPanel({
  speed,
  pitch,
  language,
  onSpeedChange,
  onPitchChange,
  onLanguageChange
}: VoiceControlPanelProps) {
  const languages: Language[] = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'tw', name: 'Twi (Akan)', flag: '🇬🇭' },
    { code: 'ga', name: 'Ga', flag: '🇬🇭' },
    { code: 'es', name: 'Spanish', flag: '🇪🇸' },
    { code: 'fr', name: 'French', flag: '🇫🇷' },
    { code: 'zh', name: 'Chinese', flag: '🇨🇳' }
  ]

  const getSpeedLabel = (value: number) => {
    if (value < 0.8) return 'Very Slow'
    if (value < 1.0) return 'Slow'
    if (value === 1.0) return 'Normal'
    if (value < 1.3) return 'Fast'
    return 'Very Fast'
  }

  const getPitchLabel = (value: number) => {
    if (value < -0.5) return 'Very Low'
    if (value < 0) return 'Low'
    if (value === 0) return 'Normal'
    if (value < 0.5) return 'High'
    return 'Very High'
  }

  return (
    <div className="space-y-6">
      <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
        <Gauge className="w-4 h-4" />
        Voice Controls
      </h4>

      {/* Speed Control */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm text-gray-700 flex items-center gap-2">
            <Gauge className="w-4 h-4 text-purple-600" />
            Speech Speed
          </label>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-purple-600">
              {getSpeedLabel(speed)}
            </span>
            <span className="text-xs text-gray-500">
              {speed.toFixed(1)}x
            </span>
          </div>
        </div>

        <div className="relative">
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={speed}
            onChange={(e) => onSpeedChange(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-purple"
          />
          {/* Speed Markers */}
          <div className="flex justify-between text-xs text-gray-400 mt-1 px-1">
            <span>0.5x</span>
            <span>1.0x</span>
            <span>1.5x</span>
            <span>2.0x</span>
          </div>
        </div>

        <p className="text-xs text-gray-500 mt-2">
          {speed < 1.0 && 'Slower speech for easier comprehension'}
          {speed === 1.0 && 'Natural speaking speed'}
          {speed > 1.0 && 'Faster speech for quicker greetings'}
        </p>
      </div>

      {/* Pitch Control */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm text-gray-700 flex items-center gap-2">
            <Music className="w-4 h-4 text-purple-600" />
            Voice Pitch
          </label>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-purple-600">
              {getPitchLabel(pitch)}
            </span>
            <span className="text-xs text-gray-500">
              {pitch > 0 ? '+' : ''}{pitch.toFixed(1)}
            </span>
          </div>
        </div>

        <div className="relative">
          <input
            type="range"
            min="-1.0"
            max="1.0"
            step="0.1"
            value={pitch}
            onChange={(e) => onPitchChange(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-purple"
          />
          {/* Pitch Markers */}
          <div className="flex justify-between text-xs text-gray-400 mt-1 px-1">
            <span>-1.0</span>
            <span>0</span>
            <span>+1.0</span>
          </div>
        </div>

        <p className="text-xs text-gray-500 mt-2">
          {pitch < 0 && 'Lower pitch for deeper voice tone'}
          {pitch === 0 && 'Natural voice pitch'}
          {pitch > 0 && 'Higher pitch for brighter voice tone'}
        </p>
      </div>

      {/* Language Selection */}
      <div>
        <label className="block text-sm text-gray-700 mb-2 flex items-center gap-2">
          <Globe className="w-4 h-4 text-purple-600" />
          Language
        </label>
        <select
          value={language}
          onChange={(e) => onLanguageChange(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          {languages.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.flag} {lang.name}
            </option>
          ))}
        </select>
        <p className="text-xs text-gray-500 mt-2">
          Select the language for text-to-speech synthesis
        </p>
      </div>

      {/* Control Tips */}
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-800">
          <strong>Tips:</strong> Start with normal settings (1.0x speed, 0 pitch) and adjust based on preview.
          Slight variations can significantly impact the greeting's feel.
        </p>
      </div>

      {/* Custom CSS for slider styling */}
      <style>{`
        .slider-purple::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #9333ea;
          cursor: pointer;
          border: 2px solid white;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .slider-purple::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #9333ea;
          cursor: pointer;
          border: 2px solid white;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .slider-purple::-webkit-slider-thumb:hover {
          background: #7c3aed;
        }

        .slider-purple::-moz-range-thumb:hover {
          background: #7c3aed;
        }
      `}</style>
    </div>
  )
}
