/**
 * Recurring Service Setup Component
 *
 * Modal/dialog for configuring automatic generation of recurring weekly services.
 * Allows selection of branch, number of weeks ahead, and preview of dates to be generated.
 */

import { useState } from 'react'
import { Calendar, X, Loader, CheckCircle, AlertCircle } from 'lucide-react'
import { getApiUrl } from '../lib/api'

interface RecurringServiceSetupProps {
  onClose: () => void
  onSuccess: () => void
}

interface PreviewService {
  date: string
  service_type: string
  day_label: string
}

export default function RecurringServiceSetup({ onClose, onSuccess }: RecurringServiceSetupProps) {
  const [weeksAhead, setWeeksAhead] = useState(8)
  const [preview, setPreview] = useState<PreviewService[]>([])
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const generatePreview = () => {
    const previewServices: PreviewService[] = []
    const today = new Date()
    const endDate = new Date(today.getTime() + weeksAhead * 7 * 24 * 60 * 60 * 1000)

    let currentDate = new Date(today)

    while (currentDate <= endDate) {
      const dayOfWeek = currentDate.getDay()

      // Sunday (0)
      if (dayOfWeek === 0) {
        previewServices.push({
          date: currentDate.toISOString().split('T')[0],
          service_type: 'sunday_8am',
          day_label: currentDate.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'short',
            day: 'numeric',
            year: 'numeric',
          }),
        })
        previewServices.push({
          date: currentDate.toISOString().split('T')[0],
          service_type: 'sunday_10am',
          day_label: currentDate.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'short',
            day: 'numeric',
            year: 'numeric',
          }),
        })
      }

      // Wednesday (3)
      if (dayOfWeek === 3) {
        previewServices.push({
          date: currentDate.toISOString().split('T')[0],
          service_type: 'midweek',
          day_label: currentDate.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'short',
            day: 'numeric',
            year: 'numeric',
          }),
        })
      }

      currentDate = new Date(currentDate.getTime() + 24 * 60 * 60 * 1000)
    }

    setPreview(previewServices)
  }

  const handleGenerate = async () => {
    setGenerating(true)
    setError('')

    try {
      const token = localStorage.getItem('access_token')
      const organizationId = localStorage.getItem('current_organization_id')

      const response = await fetch(getApiUrl('services/generate-recurring'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          organization_id: organizationId,
          weeks_ahead: weeksAhead,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess(true)
        setTimeout(() => {
          onSuccess()
          onClose()
        }, 2000)
      } else {
        setError(data.detail || 'Failed to generate services')
      }
    } catch (err: any) {
      console.error('Generate error:', err)
      setError('Network error. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  const formatServiceType = (type: string) => {
    const labels: Record<string, string> = {
      sunday_8am: 'Sunday 8:00 AM Service',
      sunday_10am: 'Sunday 10:00 AM Service',
      midweek: 'Midweek Service (Wednesday 7:00 PM)',
    }
    return labels[type] || type
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Calendar className="w-6 h-6 text-white" />
            <h2 className="text-xl font-semibold text-white">Generate Recurring Services</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {success ? (
            <div className="flex flex-col items-center justify-center py-12">
              <CheckCircle className="w-16 h-16 text-green-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Services Generated!</h3>
              <p className="text-gray-600 text-center">
                Recurring services have been created successfully.
              </p>
            </div>
          ) : (
            <>
              {/* Configuration */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Number of Weeks Ahead
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="1"
                    max="16"
                    value={weeksAhead}
                    onChange={(e) => setWeeksAhead(Number(e.target.value))}
                    className="flex-1"
                  />
                  <div className="w-16 text-center">
                    <span className="text-2xl font-bold text-purple-600">{weeksAhead}</span>
                    <span className="text-sm text-gray-500 block">weeks</span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  This will generate Sunday (8am & 10am) and Wednesday midweek services for the next{' '}
                  {weeksAhead} weeks.
                </p>
              </div>

              {/* Preview Button */}
              <button
                onClick={generatePreview}
                disabled={loading}
                className="w-full mb-4 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
              >
                {loading ? 'Loading...' : 'Preview Dates'}
              </button>

              {/* Preview List */}
              {preview.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">
                    Preview ({preview.length} services)
                  </h4>
                  <div className="border border-gray-200 rounded-lg max-h-64 overflow-y-auto">
                    {preview.map((service, index) => (
                      <div
                        key={index}
                        className="px-4 py-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-gray-900 text-sm">
                              {service.day_label}
                            </p>
                            <p className="text-xs text-gray-500 mt-0.5">
                              {formatServiceType(service.service_type)}
                            </p>
                          </div>
                          <div className="text-xs text-gray-400">{service.date}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Note: Services that already exist will be skipped.
                  </p>
                </div>
              )}

              {/* Error Display */}
              {error && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-red-900">Error</p>
                    <p className="text-sm text-red-700 mt-1">{error}</p>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  disabled={generating}
                  className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleGenerate}
                  disabled={generating || preview.length === 0}
                  className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {generating ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin" />
                      <span>Generating...</span>
                    </>
                  ) : (
                    <span>Generate Services</span>
                  )}
                </button>
              </div>

              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs text-blue-800">
                  <strong>Tip:</strong> Click "Preview Dates" to see exactly which services will be
                  created before generating.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
