/**
 * ProviderSelector Component
 *
 * TTS provider selection with status indicators, capabilities, and cost estimates.
 * Shows online/offline status and provider-specific features.
 */

import { useState, useEffect } from 'react'
import { Server, Zap, Globe, Mic, DollarSign, AlertCircle, CheckCircle, Clock } from 'lucide-react'

interface ProviderSelectorProps {
  selectedProvider: string
  onChange: (providerId: string) => void
}

interface Provider {
  id: string
  name: string
  description: string
  status: 'online' | 'offline' | 'degraded'
  capabilities: string[]
  costPer1000Chars: number
  latency: string
}

export default function ProviderSelector({ selectedProvider, onChange }: ProviderSelectorProps) {
  const [providerStatuses, setProviderStatuses] = useState<Record<string, 'online' | 'offline' | 'degraded'>>({})

  // Available TTS providers
  const providers: Provider[] = [
    {
      id: 'f5tts',
      name: 'F5-TTS',
      description: 'Flow-matching TTS with excellent voice cloning quality',
      status: providerStatuses['f5tts'] || 'online',
      capabilities: ['Voice Cloning', 'Multi-language', 'High Quality'],
      costPer1000Chars: 0.015,
      latency: '2-3s'
    },
    {
      id: 'coqui_xtts',
      name: 'Coqui XTTS',
      description: 'Multi-lingual voice cloning with 17 language support',
      status: providerStatuses['coqui_xtts'] || 'online',
      capabilities: ['Voice Cloning', '17 Languages', 'Fast'],
      costPer1000Chars: 0.012,
      latency: '1-2s'
    },
    {
      id: 'styletts2',
      name: 'StyleTTS2',
      description: 'Expressive TTS with emotion control',
      status: providerStatuses['styletts2'] || 'online',
      capabilities: ['Voice Cloning', 'Emotion Control', 'Expressive'],
      costPer1000Chars: 0.018,
      latency: '2-3s'
    },
    {
      id: 'melotts',
      name: 'MeloTTS',
      description: 'Fast, efficient TTS with good quality',
      status: providerStatuses['melotts'] || 'online',
      capabilities: ['Fast Generation', 'Multi-language', 'Efficient'],
      costPer1000Chars: 0.008,
      latency: '<1s'
    },
    {
      id: 'openvoice',
      name: 'OpenVoice',
      description: 'Voice cloning with tone color conversion',
      status: providerStatuses['openvoice'] || 'offline',
      capabilities: ['Voice Cloning', 'Tone Control', 'Emotion'],
      costPer1000Chars: 0.020,
      latency: '3-4s'
    },
    {
      id: 'kokoro',
      name: 'Kokoro TTS',
      description: 'Lightweight, fast TTS engine',
      status: providerStatuses['kokoro'] || 'online',
      capabilities: ['Ultra Fast', 'Lightweight', 'Efficient'],
      costPer1000Chars: 0.005,
      latency: '<1s'
    }
  ]

  // Fetch provider statuses from API
  useEffect(() => {
    fetchProviderStatuses()
  }, [])

  const fetchProviderStatuses = async () => {
    try {
      // This would call the health check endpoint
      // For now, we'll use default statuses
      // In production, call: /api/v1/voice-greetings/providers/status
    } catch (err) {
      console.error('Failed to fetch provider statuses:', err)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-100 text-green-700 border-green-200'
      case 'degraded':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'offline':
        return 'bg-red-100 text-red-700 border-red-200'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="w-4 h-4" />
      case 'degraded':
        return <AlertCircle className="w-4 h-4" />
      case 'offline':
        return <AlertCircle className="w-4 h-4" />
      default:
        return <Server className="w-4 h-4" />
    }
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        TTS Provider
      </label>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {providers.map((provider) => (
          <button
            key={provider.id}
            type="button"
            onClick={() => provider.status !== 'offline' && onChange(provider.id)}
            disabled={provider.status === 'offline'}
            className={`relative p-4 border-2 rounded-lg text-left transition-all ${
              selectedProvider === provider.id
                ? 'border-purple-600 bg-purple-50'
                : provider.status === 'offline'
                ? 'border-gray-200 bg-gray-50 opacity-60 cursor-not-allowed'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            {/* Status Badge */}
            <div className="absolute top-2 right-2">
              <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs border ${getStatusColor(provider.status)}`}>
                {getStatusIcon(provider.status)}
                <span className="capitalize">{provider.status}</span>
              </div>
            </div>

            {/* Provider Info */}
            <div className="pr-20">
              <div className="flex items-center gap-2 mb-2">
                <Server className="w-5 h-5 text-purple-600" />
                <div className="font-medium text-gray-900">{provider.name}</div>
              </div>

              <p className="text-xs text-gray-600 mb-3">{provider.description}</p>

              {/* Capabilities */}
              <div className="flex flex-wrap gap-1 mb-3">
                {provider.capabilities.map((capability) => (
                  <span
                    key={capability}
                    className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded border border-blue-200"
                  >
                    {capability}
                  </span>
                ))}
              </div>

              {/* Stats */}
              <div className="flex items-center gap-3 text-xs text-gray-600">
                <div className="flex items-center gap-1">
                  <DollarSign className="w-3 h-3" />
                  <span>${provider.costPer1000Chars}/1k</span>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>{provider.latency}</span>
                </div>
              </div>
            </div>

            {/* Selected Indicator */}
            {selectedProvider === provider.id && (
              <div className="absolute bottom-2 right-2">
                <div className="w-3 h-3 bg-purple-600 rounded-full"></div>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Provider Recommendation */}
      <div className="mt-3 p-3 bg-purple-50 border border-purple-200 rounded-lg">
        <div className="flex items-start gap-2">
          <Zap className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-purple-800">
            <strong>Recommended:</strong> F5-TTS offers the best voice cloning quality for the Archbishop's voice.
            Coqui XTTS is faster and supports more languages.
          </div>
        </div>
      </div>
    </div>
  )
}
