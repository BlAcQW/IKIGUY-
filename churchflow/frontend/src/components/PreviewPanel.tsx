/**
 * PreviewPanel Component
 *
 * Sample data form and preview functionality for testing voice greetings.
 * Allows users to test how greetings will sound before deploying.
 */

import { useState } from 'react'
import { Play, User, Building2, Briefcase } from 'lucide-react'
import type { VoiceGreetingConfig, GreetingAudio } from '../lib/api'
import GreetingAudioPlayer from './GreetingAudioPlayer'

interface PreviewPanelProps {
  config: VoiceGreetingConfig
  conferenceName: string
  previewAudio: GreetingAudio | null
  loading: boolean
  onPreview: (sampleData: {
    user_name: string
    branch?: string
    volunteer_role?: string
  }) => void
}

export default function PreviewPanel({
  config,
  conferenceName,
  previewAudio,
  loading,
  onPreview
}: PreviewPanelProps) {
  const [sampleData, setSampleData] = useState({
    user_name: 'John Mensah',
    branch: 'Legon Branch',
    volunteer_role: 'Usher'
  })

  const handlePreview = () => {
    if (!config.message_template) {
      alert('Please enter a message template first')
      return
    }

    // Only send personalization data if personalization is enabled
    const dataToSend = config.greeting_type === 'personalized' && config.personalization_enabled
      ? sampleData
      : { user_name: 'Guest' }

    onPreview(dataToSend)
  }

  // Generate preview text based on template and sample data
  const getPreviewText = () => {
    if (!config.message_template) {
      return 'No template configured'
    }

    let text = config.message_template

    if (config.greeting_type === 'personalized' && config.personalization_enabled) {
      text = text
        .replace('{user_name}', sampleData.user_name)
        .replace('{first_name}', sampleData.user_name.split(' ')[0])
        .replace('{branch}', sampleData.branch || '')
        .replace('{volunteer_role}', sampleData.volunteer_role || '')
        .replace('{event_name}', conferenceName)
        .replace('{venue}', 'Conference Venue')
    } else {
      text = text
        .replace('{event_name}', conferenceName)
        .replace('{venue}', 'Conference Venue')
    }

    return text
  }

  return (
    <div className="border-t pt-6">
      <h4 className="text-sm font-medium text-gray-900 mb-4 flex items-center gap-2">
        <Play className="w-4 h-4 text-purple-600" />
        Preview Greeting
      </h4>

      {/* Sample Data Form */}
      {config.greeting_type === 'personalized' && config.personalization_enabled && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600 mb-3">Enter sample data to test personalization:</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs text-gray-600 mb-1 flex items-center gap-1">
                <User className="w-3 h-3" />
                Name
              </label>
              <input
                type="text"
                value={sampleData.user_name}
                onChange={(e) => setSampleData({ ...sampleData, user_name: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="John Mensah"
              />
            </div>

            <div>
              <label className="block text-xs text-gray-600 mb-1 flex items-center gap-1">
                <Building2 className="w-3 h-3" />
                Branch (optional)
              </label>
              <input
                type="text"
                value={sampleData.branch}
                onChange={(e) => setSampleData({ ...sampleData, branch: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Legon Branch"
              />
            </div>

            <div>
              <label className="block text-xs text-gray-600 mb-1 flex items-center gap-1">
                <Briefcase className="w-3 h-3" />
                Role (optional)
              </label>
              <input
                type="text"
                value={sampleData.volunteer_role}
                onChange={(e) => setSampleData({ ...sampleData, volunteer_role: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Usher"
              />
            </div>
          </div>
        </div>
      )}

      {/* Preview Text */}
      <div className="mb-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
        <p className="text-xs text-gray-600 mb-2">This greeting will be spoken:</p>
        <p className="text-sm font-medium text-gray-900 italic">
          "{getPreviewText()}"
        </p>
      </div>

      {/* Preview Button */}
      <button
        type="button"
        onClick={handlePreview}
        disabled={loading || !config.message_template}
        className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            Generating Preview...
          </>
        ) : (
          <>
            <Play className="w-4 h-4" />
            Generate & Play Preview
          </>
        )}
      </button>

      {/* Audio Player */}
      {previewAudio && !loading && (
        <div className="mt-4">
          <GreetingAudioPlayer
            greetingAudio={previewAudio}
            autoPlay={true}
          />
        </div>
      )}

      {/* Preview Info */}
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-800">
          <strong>Preview Info:</strong> This preview uses your current settings (provider, voice, speed, pitch).
          The actual greeting will sound exactly like this when attendees check in.
        </p>
      </div>
    </div>
  )
}
