/**
 * ActivityLogForm Component
 *
 * Quick-add form for logging activities (calls, emails, meetings, notes)
 */

import { X } from 'lucide-react'
import { useState } from 'react'
import api from '@/lib/api'

interface ActivityLogFormProps {
  isOpen: boolean
  onClose: () => void
  entityType: 'lead' | 'customer' | 'opportunity' | 'contact'
  entityId: string
  onSuccess: () => void
}

export default function ActivityLogForm({
  isOpen,
  onClose,
  entityType,
  entityId,
  onSuccess
}: ActivityLogFormProps) {
  const [formData, setFormData] = useState({
    activity_type: 'call',
    subject: '',
    description: '',
    duration_minutes: '',
    call_outcome: '',
    email_subject: '',
    email_sent: true,
    meeting_location: '',
    requires_follow_up: false,
    follow_up_date: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError('')

    try {
      const payload = {
        entity_type: entityType,
        entity_id: entityId,
        activity_type: formData.activity_type,
        subject: formData.subject,
        description: formData.description || undefined,
        duration_minutes: formData.duration_minutes ? parseInt(formData.duration_minutes) : undefined,
        call_outcome: formData.activity_type === 'call' ? formData.call_outcome : undefined,
        email_subject: formData.activity_type === 'email' ? formData.email_subject : undefined,
        email_sent: formData.activity_type === 'email' ? formData.email_sent : undefined,
        meeting_location: formData.activity_type === 'meeting' ? formData.meeting_location : undefined,
        requires_follow_up: formData.requires_follow_up,
        follow_up_date: formData.requires_follow_up && formData.follow_up_date ? new Date(formData.follow_up_date).toISOString() : undefined
      }

      await api.post('/crm/activities', payload)
      onSuccess()
      onClose()
      resetForm()
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to log activity')
    } finally {
      setIsSubmitting(false)
    }
  }

  const resetForm = () => {
    setFormData({
      activity_type: 'call',
      subject: '',
      description: '',
      duration_minutes: '',
      call_outcome: '',
      email_subject: '',
      email_sent: true,
      meeting_location: '',
      requires_follow_up: false,
      follow_up_date: ''
    })
    setError('')
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>

      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium leading-6 text-gray-900">
                Log Activity
              </h3>
              <button
                onClick={onClose}
                className="rounded-md text-gray-400 hover:text-gray-500"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {error && (
              <div className="mb-4 rounded-md bg-red-50 p-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Activity Type *
                </label>
                <select
                  required
                  value={formData.activity_type}
                  onChange={(e) => setFormData({ ...formData, activity_type: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                >
                  <option value="call">📞 Call</option>
                  <option value="email">✉️ Email</option>
                  <option value="meeting">📅 Meeting</option>
                  <option value="note">📝 Note</option>
                  <option value="demo">🎥 Demo</option>
                  <option value="proposal">📄 Proposal</option>
                  <option value="follow_up">🔔 Follow-up</option>
                  <option value="other">🔧 Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Subject *
                </label>
                <input
                  type="text"
                  required
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  placeholder="Brief description of the activity"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  placeholder="Detailed notes..."
                />
              </div>

              {/* Call-specific fields */}
              {formData.activity_type === 'call' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Duration (minutes)
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={formData.duration_minutes}
                      onChange={(e) => setFormData({ ...formData, duration_minutes: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Call Outcome
                    </label>
                    <select
                      value={formData.call_outcome}
                      onChange={(e) => setFormData({ ...formData, call_outcome: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    >
                      <option value="">Select outcome...</option>
                      <option value="answered">Answered</option>
                      <option value="voicemail">Voicemail</option>
                      <option value="no_answer">No Answer</option>
                      <option value="busy">Busy</option>
                      <option value="callback_requested">Callback Requested</option>
                    </select>
                  </div>
                </>
              )}

              {/* Email-specific fields */}
              {formData.activity_type === 'email' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Email Subject
                    </label>
                    <input
                      type="text"
                      value={formData.email_subject}
                      onChange={(e) => setFormData({ ...formData, email_subject: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Direction
                    </label>
                    <select
                      value={formData.email_sent ? 'sent' : 'received'}
                      onChange={(e) => setFormData({ ...formData, email_sent: e.target.value === 'sent' })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    >
                      <option value="sent">📤 Sent</option>
                      <option value="received">📥 Received</option>
                    </select>
                  </div>
                </>
              )}

              {/* Meeting-specific fields */}
              {formData.activity_type === 'meeting' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Duration (minutes)
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={formData.duration_minutes}
                      onChange={(e) => setFormData({ ...formData, duration_minutes: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Location / Meeting Link
                    </label>
                    <input
                      type="text"
                      value={formData.meeting_location}
                      onChange={(e) => setFormData({ ...formData, meeting_location: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                      placeholder="Conference room or Zoom link"
                    />
                  </div>
                </>
              )}

              {/* Follow-up section */}
              <div className="border-t pt-4">
                <div className="flex items-center mb-3">
                  <input
                    type="checkbox"
                    checked={formData.requires_follow_up}
                    onChange={(e) => setFormData({ ...formData, requires_follow_up: e.target.checked })}
                    className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label className="ml-2 block text-sm font-medium text-gray-700">
                    Requires follow-up
                  </label>
                </div>

                {formData.requires_follow_up && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Follow-up Date
                    </label>
                    <input
                      type="datetime-local"
                      value={formData.follow_up_date}
                      onChange={(e) => setFormData({ ...formData, follow_up_date: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    />
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="mt-5 sm:mt-6 sm:flex sm:flex-row-reverse gap-3">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex w-full justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-base font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Logging...' : 'Log Activity'}
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isSubmitting}
                  className="mt-3 inline-flex w-full justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-base font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:mt-0 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
