/**
 * VoiceSelector Component
 *
 * Voice selection interface with audio previews and metadata.
 * Shows available voices, allows preview listening, and supports custom voice upload.
 */

import { useState } from 'react'
import { Play, Pause, User, Upload, Volume2, Mic } from 'lucide-react'
import VoiceUploadDialog from './VoiceUploadDialog'

interface VoiceSelectorProps {
  selectedVoice: string
  provider: string
  onChange: (voiceId: string) => void
}

interface Voice {
  id: string
  name: string
  description: string
  gender: 'male' | 'female'
  language: string
  style: string
  previewUrl?: string
}

export default function VoiceSelector({ selectedVoice, provider, onChange }: VoiceSelectorProps) {
  const [playingVoice, setPlayingVoice] = useState<string | null>(null)
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null)

  // Available voices based on the files in /opt/kasaai/apps/voice-lab/voices/
  const voices: Voice[] = [
    {
      id: 'archbishop_1',
      name: 'Archbishop Duncan-Williams',
      description: 'Authoritative, inspirational voice perfect for church events',
      gender: 'male',
      language: 'English',
      style: 'Formal, Inspiring',
      previewUrl: '/api/v1/voice-greetings/voices/preview/archbishop_1'
    },
    {
      id: 'archbishop_2',
      name: 'Archbishop (Alternative)',
      description: 'Alternative recording of Archbishop Duncan-Williams',
      gender: 'male',
      language: 'English',
      style: 'Formal, Warm',
      previewUrl: '/api/v1/voice-greetings/voices/preview/archbishop_2'
    },
    {
      id: 'nana_aba',
      name: 'Nana Aba',
      description: 'Professional female Ghanaian English voice',
      gender: 'female',
      language: 'English (Ghana)',
      style: 'Professional, Friendly',
      previewUrl: '/api/v1/voice-greetings/voices/preview/nana_aba'
    },
    {
      id: 'adom_okyere',
      name: 'Adom Okyere',
      description: 'Warm male Ghanaian English voice',
      gender: 'male',
      language: 'English (Ghana)',
      style: 'Warm, Welcoming',
      previewUrl: '/api/v1/voice-greetings/voices/preview/adom_okyere'
    },
    {
      id: 'juliet_bawuah',
      name: 'Juliet Bawuah',
      description: 'Professional female voice for formal events',
      gender: 'female',
      language: 'English',
      style: 'Professional, Clear',
      previewUrl: '/api/v1/voice-greetings/voices/preview/juliet_bawuah'
    }
  ]

  const handlePlayPreview = (voiceId: string, previewUrl?: string) => {
    // Stop any currently playing audio
    if (audioElement) {
      audioElement.pause()
      audioElement.currentTime = 0
    }

    if (playingVoice === voiceId) {
      setPlayingVoice(null)
      return
    }

    if (!previewUrl) {
      alert('Preview not available for this voice')
      return
    }

    const audio = new Audio(previewUrl)
    audio.addEventListener('ended', () => setPlayingVoice(null))
    audio.addEventListener('error', () => {
      alert('Failed to load voice preview')
      setPlayingVoice(null)
    })

    setAudioElement(audio)
    audio.play()
    setPlayingVoice(voiceId)
  }

  const handleVoiceUploaded = (voiceId: string, voiceName: string) => {
    // Add the new voice to the list and select it
    onChange(voiceId)
    setShowUploadDialog(false)
    alert(`Custom voice "${voiceName}" uploaded successfully!`)
  }

  const getGenderIcon = (gender: 'male' | 'female') => {
    return gender === 'male' ? '👨' : '👩'
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <label className="block text-sm font-medium text-gray-700">
          Voice Selection
        </label>
        <button
          type="button"
          onClick={() => setShowUploadDialog(true)}
          className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700"
        >
          <Upload className="w-4 h-4" />
          Upload Custom Voice
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {voices.map((voice) => (
          <button
            key={voice.id}
            type="button"
            onClick={() => onChange(voice.id)}
            className={`relative p-4 border-2 rounded-lg text-left transition-all group ${
              selectedVoice === voice.id
                ? 'border-purple-600 bg-purple-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            {/* Voice Info */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{getGenderIcon(voice.gender)}</span>
                <div>
                  <div className="font-medium text-gray-900 text-sm">{voice.name}</div>
                  <div className="text-xs text-gray-500">{voice.language}</div>
                </div>
              </div>

              {/* Play Preview Button */}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  handlePlayPreview(voice.id, voice.previewUrl)
                }}
                className={`p-2 rounded-lg transition-colors ${
                  playingVoice === voice.id
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-purple-100 hover:text-purple-600'
                }`}
                title="Preview voice"
              >
                {playingVoice === voice.id ? (
                  <Pause className="w-4 h-4" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
              </button>
            </div>

            <p className="text-xs text-gray-600 mb-2">{voice.description}</p>

            {/* Voice Characteristics */}
            <div className="flex items-center gap-2 text-xs">
              <span className="px-2 py-1 bg-gray-100 rounded text-gray-600">
                {voice.gender === 'male' ? 'Male' : 'Female'}
              </span>
              <span className="px-2 py-1 bg-gray-100 rounded text-gray-600">
                {voice.style}
              </span>
            </div>

            {/* Selected Indicator */}
            {selectedVoice === voice.id && (
              <div className="absolute top-2 right-2">
                <div className="w-3 h-3 bg-purple-600 rounded-full"></div>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Provider-specific Note */}
      {(provider === 'f5tts' || provider === 'coqui_xtts' || provider === 'styletts2') && (
        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start gap-2">
            <Mic className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-blue-800">
              <strong>Voice Cloning Enabled:</strong> {provider} will clone the selected voice's characteristics
              and apply them to your custom greeting text.
            </div>
          </div>
        </div>
      )}

      {/* Voice Upload Dialog */}
      {showUploadDialog && (
        <VoiceUploadDialog
          onClose={() => setShowUploadDialog(false)}
          onUploadSuccess={handleVoiceUploaded}
        />
      )}
    </div>
  )
}
