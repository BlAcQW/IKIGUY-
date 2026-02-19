import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Edit, Trash2, Calendar, MapPin, Clock, Users, CheckCircle, MessageSquare, FileText, AlertCircle } from 'lucide-react'
import TimePicker from '../components/TimePicker'
import { API_BASE_URL } from '../config/api-config'

interface Session {
  id: string
  conference_id: string
  name: string
  description: string | null
  location: string | null
  day_number: number
  day_label: string
  session_date: string
  start_time?: string | null
  end_time?: string | null
  order: number
  sms_confirmation_enabled?: boolean
  sms_confirmation_template?: string | null
  attendance_count?: number | null
  created_at?: string
  updated_at?: string
}

export default function SessionDetail() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isAdmin, setIsAdmin] = useState(false)

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false)
  const [editFormData, setEditFormData] = useState({
    name: '',
    description: '',
    location: '',
    day_label: '',
    start_time: '09:00',
    end_time: '10:00',
    sms_confirmation_enabled: false,
    sms_confirmation_template: ''
  })
  const [editLoading, setEditLoading] = useState(false)
  const [editError, setEditError] = useState('')
  const [editSuccess, setEditSuccess] = useState('')

  // Delete modal state
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [deleteError, setDeleteError] = useState('')
  const [confirmText, setConfirmText] = useState('')

  useEffect(() => {
    checkAdminStatus()
    fetchSession()
  }, [sessionId])

  const checkAdminStatus = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setIsAdmin(false)
        return
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const userData = await response.json()
        setIsAdmin(userData.role === 'admin' || userData.role === 'platform_admin')
      }
    } catch (err) {
      console.error('Failed to check admin status:', err)
      setIsAdmin(false)
    }
  }

  const fetchSession = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const headers: any = {}

      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}`, { headers })

      if (!response.ok) {
        throw new Error('Failed to load session')
      }

      const data = await response.json()
      setSession(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load session')
    } finally {
      setLoading(false)
    }
  }

  const handleEditClick = () => {
    if (!session) return

    setEditFormData({
      name: session.name,
      description: session.description || '',
      location: session.location || '',
      day_label: session.day_label,
      start_time: session.start_time || '09:00',
      end_time: session.end_time || '10:00',
      sms_confirmation_enabled: session.sms_confirmation_enabled || false,
      sms_confirmation_template: session.sms_confirmation_template || ''
    })
    setShowEditModal(true)
    setEditError('')
    setEditSuccess('')
  }

  const handleEditSave = async () => {
    if (!session) return

    setEditLoading(true)
    setEditError('')
    setEditSuccess('')

    try {
      const token = localStorage.getItem('access_token')
      const headers: any = { 'Content-Type': 'application/json' }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/conferences/${session.conference_id}/sessions/${session.id}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({
          name: editFormData.name,
          description: editFormData.description || null,
          location: editFormData.location || null,
          day_label: editFormData.day_label,
          start_time: editFormData.start_time || null,
          end_time: editFormData.end_time || null,
          sms_confirmation_enabled: editFormData.sms_confirmation_enabled,
          sms_confirmation_template: editFormData.sms_confirmation_template || null
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to update session')
      }

      const updatedData = await response.json()
      setSession(updatedData)
      setEditSuccess(`Successfully updated session`)

      setTimeout(() => {
        setShowEditModal(false)
        setEditSuccess('')
      }, 1500)
    } catch (err: any) {
      setEditError(err.message || 'Failed to update session')
    } finally {
      setEditLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!session || confirmText !== 'DELETE') return

    setDeleteLoading(true)
    setDeleteError('')

    try {
      const token = localStorage.getItem('access_token')
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/conferences/${session.conference_id}/sessions/${session.id}`, {
        method: 'DELETE',
        headers
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to delete session')
      }

      // Navigate back after successful delete
      navigate(-1)
    } catch (err: any) {
      setDeleteError(err.message || 'Failed to delete session')
    } finally {
      setDeleteLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading session details...</p>
        </div>
      </div>
    )
  }

  if (error || !session) {
    return (
      <div className="max-w-2xl mx-auto p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle className="w-5 h-5" />
            <p>{error || 'Session not found'}</p>
          </div>
          <button
            onClick={() => navigate(-1)}
            className="mt-4 text-purple-600 hover:text-purple-700 font-medium"
          >
            ← Go Back
          </button>
        </div>
      </div>
    )
  }

  const sessionDate = new Date(session.session_date)

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="hidden sm:inline">Back</span>
            </button>

            {isAdmin && (
              <div className="flex gap-2">
                <button
                  onClick={handleEditClick}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Edit className="w-4 h-4" />
                  <span className="hidden sm:inline">Edit</span>
                </button>
                <button
                  onClick={() => setShowDeleteModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  <span className="hidden sm:inline">Delete</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Main Info Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-8 text-white">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center text-2xl font-bold flex-shrink-0">
                <Calendar className="w-8 h-8" />
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="text-2xl font-bold mb-2">{session.name}</h1>
                <div className="flex flex-wrap gap-3 text-purple-100">
                  <span className="inline-flex items-center gap-1.5">
                    <Calendar className="w-4 h-4" />
                    {session.day_label}
                  </span>
                  <span>•</span>
                  <span>{sessionDate.toLocaleDateString()}</span>
                  {(session.start_time || session.end_time) && (
                    <>
                      <span>•</span>
                      <span className="inline-flex items-center gap-1.5">
                        <Clock className="w-4 h-4" />
                        {session.start_time && session.end_time
                          ? `${session.start_time} - ${session.end_time}`
                          : session.start_time || session.end_time
                        }
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Attendance Badge */}
            {session.attendance_count !== undefined && session.attendance_count !== null && (
              <div className="mt-4">
                <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-white/20 text-white">
                  <Users className="w-4 h-4 mr-1.5" />
                  {session.attendance_count} {session.attendance_count === 1 ? 'attendee' : 'attendees'} checked in
                </span>
              </div>
            )}
          </div>

          {/* Session Details */}
          <div className="px-6 py-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Session Information</h2>

            {session.description && (
              <div className="mb-6">
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-gray-600 font-medium mb-1">Description</p>
                    <p className="text-gray-900 whitespace-pre-wrap">{session.description}</p>
                  </div>
                </div>
              </div>
            )}

            {session.location && (
              <div className="mb-6">
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-gray-600 font-medium mb-1">Location</p>
                    <p className="text-gray-900">{session.location}</p>
                  </div>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-600 font-medium mb-1">Day Number</p>
                <p className="text-gray-900">Day {session.day_number}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 font-medium mb-1">Display Order</p>
                <p className="text-gray-900">{session.order}</p>
              </div>
            </div>
          </div>

          {/* SMS Confirmation Settings */}
          {session.sms_confirmation_enabled && (
            <div className="px-6 py-6 bg-green-50 border-t border-green-100">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-green-600" />
                SMS Confirmation Enabled
              </h2>
              {session.sms_confirmation_template && (
                <div>
                  <p className="text-sm text-gray-600 font-medium mb-2">Message Template:</p>
                  <div className="bg-white p-3 rounded border border-green-200">
                    <p className="text-gray-900 text-sm">{session.sms_confirmation_template}</p>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Sent automatically when attendees check in to this session
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Timestamps */}
          {(session.created_at || session.updated_at) && (
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                {session.created_at && (
                  <div>
                    <p className="text-gray-600 font-medium">Created</p>
                    <p className="text-gray-900">{new Date(session.created_at).toLocaleString()}</p>
                  </div>
                )}
                {session.updated_at && (
                  <div>
                    <p className="text-gray-600 font-medium">Last Updated</p>
                    <p className="text-gray-900">{new Date(session.updated_at).toLocaleString()}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4" onClick={() => {
          if (!editLoading) {
            setShowEditModal(false)
            setEditError('')
            setEditSuccess('')
          }
        }}>
          <div className="bg-white rounded-t-2xl sm:rounded-lg shadow-xl max-w-md w-full p-4 sm:p-6 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                <Edit className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Edit Session</h3>
                <p className="text-sm text-gray-600">Update session information</p>
              </div>
            </div>

            <div className="space-y-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Session Name *</label>
                <input
                  type="text"
                  value={editFormData.name}
                  onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                  className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={editLoading}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={editFormData.description}
                  onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                  className="w-full px-4 py-2 text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={editLoading}
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input
                  type="text"
                  value={editFormData.location}
                  onChange={(e) => setEditFormData({ ...editFormData, location: e.target.value })}
                  className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={editLoading}
                  placeholder="e.g., Main Auditorium"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <TimePicker
                  value={editFormData.start_time}
                  onChange={(value) => setEditFormData({ ...editFormData, start_time: value })}
                  label="Start Time"
                  required
                  disabled={editLoading}
                  maxTime={editFormData.end_time}
                />
                <TimePicker
                  value={editFormData.end_time}
                  onChange={(value) => setEditFormData({ ...editFormData, end_time: value })}
                  label="End Time"
                  required
                  disabled={editLoading}
                  minTime={editFormData.start_time}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Day Label *</label>
                <input
                  type="text"
                  value={editFormData.day_label}
                  onChange={(e) => setEditFormData({ ...editFormData, day_label: e.target.value })}
                  className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={editLoading}
                  required
                />
              </div>

              <div className="border-t border-gray-200 pt-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editFormData.sms_confirmation_enabled}
                    onChange={(e) => setEditFormData({ ...editFormData, sms_confirmation_enabled: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                    disabled={editLoading}
                  />
                  <span className="text-sm text-gray-700">Enable SMS confirmation on check-in</span>
                </label>

                {editFormData.sms_confirmation_enabled && (
                  <div className="mt-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">SMS Template</label>
                    <textarea
                      value={editFormData.sms_confirmation_template}
                      onChange={(e) => setEditFormData({ ...editFormData, sms_confirmation_template: e.target.value })}
                      className="w-full px-4 py-2 text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      disabled={editLoading}
                      rows={2}
                      maxLength={160}
                      placeholder="Hi {name}, you're checked in to {session_name}!"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {(editFormData.sms_confirmation_template || '').length}/160 characters
                    </p>
                  </div>
                )}
              </div>
            </div>

            {editError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {editError}
              </div>
            )}

            {editSuccess && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                {editSuccess}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setEditError('')
                  setEditSuccess('')
                }}
                className="flex-1 px-4 py-2 min-h-[44px] border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors touch-manipulation"
                disabled={editLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleEditSave}
                disabled={editLoading || !editFormData.name || !editFormData.day_label}
                className="flex-1 px-4 py-2 min-h-[44px] bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
              >
                {editLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
          <div className="bg-white rounded-t-2xl sm:rounded-lg shadow-xl max-w-md w-full p-4 sm:p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Delete Session</h3>
                <p className="text-sm text-gray-600">This action cannot be undone</p>
              </div>
            </div>

            <div className="mb-4">
              <p className="text-gray-700 mb-3">
                Are you sure you want to permanently delete this session?
              </p>
              <div className="bg-gray-50 p-3 rounded-lg mb-3">
                <p className="font-semibold text-gray-900">{session.name}</p>
                <p className="text-sm text-gray-600">{session.day_label}</p>
                {session.attendance_count !== undefined && session.attendance_count > 0 && (
                  <p className="text-sm text-orange-600 mt-1 font-medium">
                    ⚠️ {session.attendance_count} attendee(s) checked in
                  </p>
                )}
              </div>
              <p className="text-sm text-gray-600 mb-2">
                Type <strong>DELETE</strong> to confirm:
              </p>
              <input
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                className="w-full px-4 py-2 min-h-[44px] border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="Type DELETE"
                disabled={deleteLoading}
              />
            </div>

            {deleteError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {deleteError}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDeleteModal(false)
                  setConfirmText('')
                  setDeleteError('')
                }}
                className="flex-1 px-4 py-2 min-h-[44px] border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors touch-manipulation"
                disabled={deleteLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteLoading || confirmText !== 'DELETE'}
                className="flex-1 px-4 py-2 min-h-[44px] bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
              >
                {deleteLoading ? 'Deleting...' : 'Delete Session'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
