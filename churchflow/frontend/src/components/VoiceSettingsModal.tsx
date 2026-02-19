/**
 * VoiceSettingsModal Component
 *
 * Complete voice greeting configuration interface for conferences and bus routes.
 * Includes enable/disable, template editing, provider/voice selection, controls, and preview.
 */

import { useState, useEffect } from 'react'
import { X, Volume2, Save, AlertCircle, HelpCircle, Play } from 'lucide-react'
import ConfirmDialog from './ConfirmDialog'
import type { VoiceGreetingConfig, GreetingAudio } from '../lib/api'
import {
  getConferenceVoiceGreeting,
  updateConferenceVoiceGreeting,
  previewConferenceVoiceGreeting
} from '../lib/api'
import { API_BASE_URL, CHURCHFLOW_API_URL } from '../config/api-config'
import TemplateHelper from './TemplateHelper'
import VoiceSelector from './VoiceSelector'
import PreviewPanel from './PreviewPanel'
import { ComprehensiveTTSSelector } from '../../../../shared/frontend/components/voice-settings/ComprehensiveTTSSelector'
import { useComprehensiveTTS } from '../../../../shared/frontend/hooks/useComprehensiveTTS'
import { getAuthHeaders } from '../lib/auth-utils'

interface VoiceSettingsModalProps {
  conferenceId: string
  conferenceName: string
  onClose: () => void
  onSave: () => void
}

export default function VoiceSettingsModal({
  conferenceId,
  conferenceName,
  onClose,
  onSave
}: VoiceSettingsModalProps) {
  // State for configuration
  const [config, setConfig] = useState<VoiceGreetingConfig>({
    enabled: true,
    greeting_type: 'personalized',
    message_template: 'Hello {user_name}, thank you for checking in for {event_name}',
    tts_provider: 'f5tts',
    voice_id: 'archbishop_1',
    speed: 1.0,
    pitch: 0.0,
    language: 'en',
    personalization_enabled: true
  })

  // UI state
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showHelper, setShowHelper] = useState(false)
  const [isDirty, setIsDirty] = useState(false)

  // Preview state
  const [previewAudio, setPreviewAudio] = useState<GreetingAudio | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  // State for TTS preview
  const [ttsPreviewLoading, setTtsPreviewLoading] = useState(false)
  const [ttsPreviewAudio, setTtsPreviewAudio] = useState<HTMLAudioElement | null>(null)
  const [showCloseDialog, setShowCloseDialog] = useState(false)

  // Use comprehensive TTS hook for provider selection
  const {
    providers: comprehensiveTTSProviders,
    loading: loadingComprehensiveTTS,
    error: comprehensiveTTSError
  } = useComprehensiveTTS(API_BASE_URL, undefined, {
    onlineOnly: false,
    autoFetch: true,
    endpointPath: '/api/tts/providers',
    skipWalletBalance: true,
    getAuthHeaders
  })

  // Handle TTS voice preview (text field in ComprehensiveTTSSelector)
  const handleTTSPreviewVoice = async (previewText: string) => {
    if (!config.tts_provider) {
      alert('Please select a TTS provider first')
      return
    }

    // Stop any currently playing audio
    if (ttsPreviewAudio) {
      ttsPreviewAudio.pause()
      ttsPreviewAudio.currentTime = 0
    }

    setTtsPreviewLoading(true)

    try {
      const synthesisRequest = {
        provider_id: config.tts_provider,
        text: previewText,
        language: config.language || 'en',
        voice_id: config.voice_id || undefined,
        speed: config.speed || 1.0,
        pitch: config.pitch || 0.0,
        output_format: 'wav'
      }

      const authHeaders = await getAuthHeaders()

      const response = await fetch(`${API_BASE_URL}/api/tts/synthesize`, {
        method: 'POST',
        headers: {
          ...authHeaders,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(synthesisRequest),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(errorData.detail || 'TTS synthesis failed')
      }

      const data = await response.json()

      if (data.audio_base64) {
        const audioBlob = await fetch(`data:audio/wav;base64,${data.audio_base64}`).then(r => r.blob())
        const audioUrl = URL.createObjectURL(audioBlob)

        const audio = new Audio(audioUrl)
        setTtsPreviewAudio(audio)

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl)
        }

        await audio.play()
      } else {
        throw new Error('No audio data returned from TTS service')
      }
    } catch (error: any) {
      console.error('TTS preview failed:', error)
      alert(error.message || 'Preview failed')
    } finally {
      setTtsPreviewLoading(false)
    }
  }

  // Load existing configuration
  useEffect(() => {
    loadConfiguration()
  }, [conferenceId])

  const loadConfiguration = async () => {
    setLoading(true)
    setError(null)

    try {
      const data = await getConferenceVoiceGreeting(conferenceId)
      setConfig(data)
    } catch (err: any) {
      console.error('Failed to load voice greeting configuration:', err)
      // If 404, use defaults (first time configuration)
      if (err.message.includes('404')) {
        // Keep default config
      } else {
        setError('Failed to load voice greeting configuration')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)

    try {
      await updateConferenceVoiceGreeting(conferenceId, config)
      alert('Voice greeting settings saved successfully!')
      setIsDirty(false)
      onSave() // Refresh parent
      onClose()
    } catch (err: any) {
      console.error('Failed to save voice greeting configuration:', err)
      setError(err.message || 'Failed to save voice greeting settings')
    } finally {
      setSaving(false)
    }
  }

  const handlePreview = async (sampleData: {
    user_name: string
    branch?: string
    volunteer_role?: string
  }) => {
    setPreviewLoading(true)
    setError(null)

    try {
      const audio = await previewConferenceVoiceGreeting(conferenceId, {
        message_template: config.message_template || '',
        tts_provider: config.tts_provider,
        voice_id: config.voice_id,
        speed: config.speed,
        pitch: config.pitch,
        language: config.language,
        sample_user_data: sampleData
      })
      setPreviewAudio(audio)
    } catch (err: any) {
      console.error('Failed to preview greeting:', err)
      setError(err.message || 'Failed to generate preview')
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleClose = () => {
    if (isDirty) {
      setShowCloseDialog(true)
      return
    }
    onClose()
  }

  const confirmClose = () => {
    setShowCloseDialog(false)
    onClose()
  }

  const updateConfig = <K extends keyof VoiceGreetingConfig>(
    key: K,
    value: VoiceGreetingConfig[K]
  ) => {
    setConfig(prev => ({ ...prev, [key]: value }))
    setIsDirty(true)
  }

  const insertVariable = (variable: string) => {
    const template = config.message_template || ''
    const newTemplate = template + (template ? ' ' : '') + variable
    updateConfig('message_template', newTemplate)
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-xl p-8 max-w-4xl w-full mx-4 my-8">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading voice settings...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full my-8">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Volume2 className="w-6 h-6 text-purple-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Voice Greeting Settings</h2>
              <p className="text-sm text-gray-600">{conferenceName}</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[calc(100vh-16rem)] overflow-y-auto">
          {/* Enable/Disable Toggle */}
          <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg">
            <div>
              <h3 className="font-medium text-gray-900">Enable Voice Greetings</h3>
              <p className="text-sm text-gray-600">Play personalized voice greetings when attendees check in</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={config.enabled}
                onChange={(e) => updateConfig('enabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[4px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          {config.enabled && (
            <>
              {/* Greeting Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Greeting Type
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => updateConfig('greeting_type', 'simple')}
                    className={`p-4 border-2 rounded-lg text-left transition-all ${
                      config.greeting_type === 'simple'
                        ? 'border-purple-600 bg-purple-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium text-gray-900">Simple</div>
                    <div className="text-sm text-gray-600">Same greeting for everyone</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => updateConfig('greeting_type', 'personalized')}
                    className={`p-4 border-2 rounded-lg text-left transition-all ${
                      config.greeting_type === 'personalized'
                        ? 'border-purple-600 bg-purple-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium text-gray-900">Personalized</div>
                    <div className="text-sm text-gray-600">Include user's name and details</div>
                  </button>
                </div>
              </div>

              {/* Message Template */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Message Template
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowHelper(!showHelper)}
                    className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700"
                  >
                    <HelpCircle className="w-4 h-4" />
                    {showHelper ? 'Hide' : 'Show'} Variables
                  </button>
                </div>
                <textarea
                  value={config.message_template || ''}
                  onChange={(e) => updateConfig('message_template', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-sm"
                  placeholder="Enter your greeting message..."
                  rows={3}
                  maxLength={500}
                />
                <div className="flex items-center justify-between mt-1">
                  <p className="text-xs text-gray-500">
                    {config.greeting_type === 'personalized'
                      ? 'Use variables like {user_name}, {branch}, {event_name}'
                      : 'Simple text without variables'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {config.message_template?.length || 0} / 500
                  </p>
                </div>

                {/* Template Helper */}
                {showHelper && (
                  <TemplateHelper
                    greetingType={config.greeting_type}
                    onInsertVariable={insertVariable}
                  />
                )}
              </div>

              {/* Comprehensive TTS Selector - replaces Provider, Voice, and Controls */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Voice Configuration
                </label>
                <ComprehensiveTTSSelector
                  providers={comprehensiveTTSProviders}
                  selectedProviderId={config.tts_provider}
                  onSelectProvider={(providerId) => updateConfig('tts_provider', providerId)}
                  selectedVoice={config.voice_id || undefined}
                  onSelectVoice={(voice) => updateConfig('voice_id', voice)}
                  selectedLanguage={config.language}
                  onSelectLanguage={(language) => updateConfig('language', language)}
                  speed={config.speed || 1.0}
                  onSpeedChange={(speed) => updateConfig('speed', speed)}
                  pitch={config.pitch || 0.0}
                  onPitchChange={(pitch) => updateConfig('pitch', pitch)}
                  showAdvanced={true}
                  showOnlineOnly={false}
                  isLoading={loadingComprehensiveTTS}
                  onPreview={handleTTSPreviewVoice}
                  previewLoading={ttsPreviewLoading}
                />
                {comprehensiveTTSError && (
                  <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-xs text-red-700">
                      ⚠️ Error loading providers: {comprehensiveTTSError}
                    </p>
                  </div>
                )}
              </div>

              {/* Personalization Toggle */}
              {config.greeting_type === 'personalized' && (
                <div className="flex items-center gap-2 p-4 bg-gray-50 rounded-lg">
                  <input
                    type="checkbox"
                    id="personalization_enabled"
                    checked={config.personalization_enabled}
                    onChange={(e) => updateConfig('personalization_enabled', e.target.checked)}
                    className="w-4 h-4 text-purple-600 rounded"
                  />
                  <label htmlFor="personalization_enabled" className="text-sm text-gray-700">
                    Include user details in greeting (name, branch, role)
                  </label>
                </div>
              )}

              {/* Preview Panel */}
              <PreviewPanel
                config={config}
                conferenceName={conferenceName}
                previewAudio={previewAudio}
                loading={previewLoading}
                onPreview={handlePreview}
              />
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t">
          <button
            type="button"
            onClick={handleClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            disabled={saving}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || !isDirty}
            className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Save Settings
              </>
            )}
          </button>
        </div>
      </div>

      {/* Unsaved Changes Dialog */}
      <ConfirmDialog
        isOpen={showCloseDialog}
        onClose={() => setShowCloseDialog(false)}
        onConfirm={confirmClose}
        title="Unsaved Changes"
        message="You have unsaved changes. Are you sure you want to close without saving?"
        confirmText="Discard Changes"
        cancelText="Keep Editing"
        variant="warning"
      />
    </div>
  )
}
