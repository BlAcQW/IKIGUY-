/**
 * Session Manager Component
 *
 * Manages conference sessions - create, edit, delete sessions for a conference.
 * Organized by day for easy management.
 */

import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { useNavigate } from 'react-router-dom'
import { Plus, Edit, Trash2, X, Calendar, MapPin, FileText, CalendarDays, UserCheck, Users, Search, QrCode, Clock, CheckCircle, XCircle, Phone, MessageSquare } from 'lucide-react'
import CameraQRScanner from './CameraQRScanner'
import GreetingAudioPlayer from './GreetingAudioPlayer'
import ConfirmDialog from './ConfirmDialog'
import TimePicker from './TimePicker'
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
}

interface Conference {
  id: string
  name: string
  start_date: string
  end_date: string
}

interface ConferenceDay {
  day_number: number
  day_label: string
  date: string
  date_display: string
}

interface SessionManagerProps {
  conference: Conference
  onClose?: () => void
}

interface Attendee {
  id: string
  user_name: string
  user_phone: string
  checked_in_at: string
  check_in_method: string
}

interface SearchResult {
  id: string
  user_name: string
  user_phone: string
  registration_code: string
}

interface GreetingAudio {
  audio_url: string
  text: string
  duration_seconds?: number
  provider_used: string
  cost_usd?: number
  is_fallback?: boolean
}

interface CheckInResult {
  id: string
  session_name: string
  user_name: string
  user_phone: string
  checked_in_at: string
  message: string
  greeting_audio?: GreetingAudio
}

export default function SessionManager({ conference, onClose }: SessionManagerProps) {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<Session[]>([])
  const [days, setDays] = useState<ConferenceDay[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingSession, setEditingSession] = useState<Session | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    location: '',
    day_number: 1,
    day_label: 'Day 1',
    session_date: '',
    start_time: '09:00',
    end_time: '10:00',
    order: 0,
    sms_confirmation_enabled: false,
    sms_confirmation_template: ''
  })

  // Check-in related state
  const [checkInSession, setCheckInSession] = useState<Session | null>(null)
  const [checkInTab, setCheckInTab] = useState<'qr' | 'search' | 'phone'>('qr')
  const [registrationCode, setRegistrationCode] = useState('')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [attendees, setAttendees] = useState<Attendee[]>([])
  const [checkInResult, setCheckInResult] = useState<CheckInResult | null>(null)
  const [checkInError, setCheckInError] = useState('')
  const [checkInLoading, setCheckInLoading] = useState(false)
  const [showScanner, setShowScanner] = useState(false)
  // Delete confirmation dialog state
  const [deleteDialog, setDeleteDialog] = useState<{
    isOpen: boolean;
    sessionId: string | null;
    sessionName: string;
    isLoading: boolean;
  }>({ isOpen: false, sessionId: null, sessionName: '', isLoading: false })

  // Info/notification dialog state
  const [infoDialog, setInfoDialog] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    variant: 'success' | 'danger' | 'warning' | 'info';
  }>({ isOpen: false, title: '', message: '', variant: 'info' })

  const showNotification = (title: string, message: string, variant: 'success' | 'danger' | 'warning' | 'info' = 'info') => {
    setInfoDialog({ isOpen: true, title, message, variant })
  }

  useEffect(() => {
    fetchDays()
    fetchSessions()
  }, [conference.id])

  const fetchDays = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/conferences/${conference.id}/days`)
      if (response.ok) {
        const data = await response.json()
        setDays(data.days)
      }
    } catch (err) {
      console.error('Failed to fetch days:', err)
    }
  }

  const fetchSessions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/conferences/${conference.id}/sessions`)
      if (response.ok) {
        const data = await response.json()
        setSessions(data.sessions)
      }
    } catch (err) {
      console.error('Failed to fetch sessions:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem('access_token')
    if (!token) {
      showNotification('Authentication Required', 'Please login to manage sessions', 'warning')
      return
    }

    const url = editingSession
      ? `${API_BASE_URL}/api/v1/conferences/${conference.id}/sessions/${editingSession.id}`
      : `${API_BASE_URL}/api/v1/conferences/${conference.id}/sessions`

    const method = editingSession ? 'PUT' : 'POST'

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...formData,
          session_date: new Date(formData.session_date).toISOString()
        })
      })

      if (response.ok) {
        // No confirmation notification - session appears in the list immediately
        setShowForm(false)
        setEditingSession(null)
        resetForm()
        fetchSessions()
      } else {
        const err = await response.json().catch(() => ({ detail: 'Error' }))
        showNotification('Failed to Save', err.detail || 'An error occurred while saving the session.', 'danger')
      }
    } catch (err) {
      console.error('Failed to save session:', err)
      showNotification('Error', 'Failed to save session. Please try again.', 'danger')
    }
  }

  // Open delete confirmation dialog
  const openDeleteDialog = (session: Session) => {
    setDeleteDialog({
      isOpen: true,
      sessionId: session.id,
      sessionName: session.name,
      isLoading: false,
    })
  }

  // Handle confirmed delete
  const handleDelete = async () => {
    if (!deleteDialog.sessionId) return

    const token = localStorage.getItem('access_token')
    if (!token) return

    setDeleteDialog(prev => ({ ...prev, isLoading: true }))

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/conferences/${conference.id}/sessions/${deleteDialog.sessionId}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      if (response.ok) {
        setDeleteDialog({ isOpen: false, sessionId: null, sessionName: '', isLoading: false })
        showNotification('Session Deleted', 'The session has been deleted successfully.', 'success')
        fetchSessions()
      } else {
        showNotification('Delete Failed', 'Failed to delete session. Please try again.', 'danger')
        setDeleteDialog(prev => ({ ...prev, isLoading: false }))
      }
    } catch (err) {
      console.error('Failed to delete:', err)
      showNotification('Error', 'Failed to delete session. Please try again.', 'danger')
      setDeleteDialog(prev => ({ ...prev, isLoading: false }))
    }
  }

  const openCreateForm = (dayNumber: number) => {
    const day = days.find(d => d.day_number === dayNumber) || days[0]
    setEditingSession(null)
    setFormData({
      name: '',
      description: '',
      location: '',
      day_number: day.day_number,
      day_label: day.day_label,
      session_date: day.date + 'T09:00',
      start_time: '09:00',
      end_time: '10:00',
      order: 0,
      sms_confirmation_enabled: false,
      sms_confirmation_template: ''
    })
    setShowForm(true)
  }

  const openEditForm = (session: Session) => {
    setEditingSession(session)
    setFormData({
      name: session.name,
      description: session.description || '',
      location: session.location || '',
      day_number: session.day_number,
      day_label: session.day_label,
      session_date: session.session_date.substring(0, 16),
      start_time: session.start_time || '09:00',
      end_time: session.end_time || '10:00',
      order: session.order,
      sms_confirmation_enabled: session.sms_confirmation_enabled || false,
      sms_confirmation_template: session.sms_confirmation_template || ''
    })
    setShowForm(true)
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      location: '',
      day_number: 1,
      day_label: 'Day 1',
      session_date: '',
      order: 0,
      sms_confirmation_enabled: false,
      sms_confirmation_template: ''
    })
  }

  // Fetch attendance when check-in session changes
  useEffect(() => {
    if (checkInSession) {
      fetchAttendance(checkInSession.id)
    }
  }, [checkInSession])

  const fetchAttendance = async (sessionId: string) => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      console.warn('No auth token available for fetching attendance')
      return
    }

    try {
      const url = `${API_BASE_URL}/api/v1/conferences/${conference.id}/sessions/${sessionId}/attendance`
      console.log('Fetching attendance from:', url)
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('Attendance response:', {
          total_checked_in: data.total_checked_in,
          attendees_count: data.attendees?.length || 0,
          session_id: data.session_id,
          session_name: data.session_name
        })
        setAttendees(data.attendees || [])
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        console.error('Failed to fetch attendance:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData
        })
        setAttendees([])
      }
    } catch (err) {
      console.error('Failed to fetch attendance:', err)
      setAttendees([])
    }
  }

  const handleQRCheckIn = async (code: string) => {
    if (!checkInSession || !code) return

    // Extract registration code from URL if scanned value is a URL
    // QR codes contain: https://churchflow.ailabsafrica.com/self-checkin?code=REG-XXXXXXXX
    let registrationCode = code
    if (code.includes('code=')) {
      try {
        const url = new URL(code)
        registrationCode = url.searchParams.get('code') || code
      } catch {
        // If URL parsing fails, try regex extraction
        const match = code.match(/code=([^&]+)/)
        if (match) registrationCode = match[1]
      }
    }

    setCheckInLoading(true)
    setCheckInError('')
    setCheckInResult(null)

    const token = localStorage.getItem('access_token')
    if (!token) {
      setCheckInError('Please login to check in attendees')
      setCheckInLoading(false)
      return
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/conferences/${conference.id}/sessions/${checkInSession.id}/check-in`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ registration_code: registrationCode })
        }
      )

      const data = await response.json()

      if (response.ok) {
        setCheckInResult(data)
        setRegistrationCode('')
        fetchAttendance(checkInSession.id)
        // Refresh sessions to update attendance counts
        fetchSessions()
        setTimeout(() => setCheckInResult(null), 5000)
      } else {
        setCheckInError(data.detail || 'Check-in failed')
      }
    } catch (err: any) {
      setCheckInError(err.message || 'Check-in failed')
    } finally {
      setCheckInLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery || searchQuery.length < 2) return

    setSearching(true)
    const token = localStorage.getItem('access_token')
    if (!token) return

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/conferences/${conference.id}/registrations/search?q=${encodeURIComponent(searchQuery)}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )
      if (response.ok) {
        const data = await response.json()
        setSearchResults(data)
      }
    } catch (err) {
      console.error('Search failed:', err)
    } finally {
      setSearching(false)
    }
  }

  const handleManualCheckIn = async (registrationId: string) => {
    if (!checkInSession) return

    setCheckInLoading(true)
    setCheckInError('')

    const token = localStorage.getItem('access_token')
    if (!token) return

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/conferences/${conference.id}/sessions/${checkInSession.id}/check-in/manual`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ registration_id: registrationId })
        }
      )

      const data = await response.json()

      if (response.ok) {
        setCheckInResult(data)
        setSearchResults([])
        setSearchQuery('')
        fetchAttendance(checkInSession.id)
        // Refresh sessions to update attendance counts
        fetchSessions()
        setTimeout(() => setCheckInResult(null), 5000)
      } else {
        setCheckInError(data.detail || 'Check-in failed')
      }
    } catch (err: any) {
      setCheckInError(err.message || 'Check-in failed')
    } finally {
      setCheckInLoading(false)
    }
  }

  const handlePhoneCheckIn = async (phone: string) => {
    if (!checkInSession || !phone) return

    setCheckInLoading(true)
    setCheckInError('')
    setCheckInResult(null)

    const token = localStorage.getItem('access_token')
    if (!token) {
      setCheckInError('Please login to check in attendees')
      setCheckInLoading(false)
      return
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/conferences/${conference.id}/sessions/${checkInSession.id}/check-in/phone`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ phone })
        }
      )

      const data = await response.json()

      if (response.ok) {
        setCheckInResult(data)
        setPhoneNumber('')
        fetchAttendance(checkInSession.id)
        // Refresh sessions to update attendance counts
        fetchSessions()
        setTimeout(() => setCheckInResult(null), 5000)
      } else {
        setCheckInError(data.detail || 'Check-in failed')
      }
    } catch (err: any) {
      setCheckInError(err.message || 'Check-in failed')
    } finally {
      setCheckInLoading(false)
    }
  }

  const openCheckIn = (session: Session) => {
    setCheckInSession(session)
    setCheckInTab('qr')
    setRegistrationCode('')
    setPhoneNumber('')
    setSearchQuery('')
    setSearchResults([])
    setCheckInResult(null)
    setCheckInError('')
    setAttendees([])
  }

  const closeCheckIn = () => {
    setCheckInSession(null)
    setCheckInResult(null)
    setCheckInError('')
    setSearchResults([])
    setSearchQuery('')
    setRegistrationCode('')
    setPhoneNumber('')
    setAttendees([])
  }

  const sessionsByDay = sessions.reduce((acc, session) => {
    if (!acc[session.day_number]) acc[session.day_number] = []
    acc[session.day_number].push(session)
    return acc
  }, {} as Record<number, Session[]>)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Manage Sessions</h2>
          <p className="text-sm text-gray-500 mt-1">Create and manage conference sessions by day</p>
        </div>
      </div>

      {/* Content */}
      <div>
          {loading ? (
            <div className="text-center py-12 text-gray-500">Loading sessions...</div>
          ) : days.length === 0 ? (
            <div className="text-center py-12 text-gray-500">No conference days found</div>
          ) : (
            <div className="space-y-4">
              {days.map(day => (
                <div key={day.day_number} className="card">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h3 className="font-semibold text-gray-900">{day.day_label}</h3>
                      <p className="text-sm text-gray-500">{day.date_display}</p>
                    </div>
                    <button
                      onClick={() => openCreateForm(day.day_number)}
                      className="btn-primary btn-sm flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add Session
                    </button>
                  </div>

                  {/* Sessions for this day */}
                  <div className="space-y-3">
                    {(sessionsByDay[day.day_number] || []).map(session => (
                      <div
                        key={session.id}
                        className="bg-gray-50 p-4 rounded-lg border border-gray-100 flex justify-between items-start hover:border-gray-200 transition-colors cursor-pointer"
                        onClick={() => navigate(`/sessions/${session.id}`)}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4 className="font-medium text-gray-900">{session.name}</h4>
                            {(session.start_time || session.end_time) && (
                              <span className="text-sm text-gray-600 inline-flex items-center gap-1">
                                <Clock className="w-3.5 h-3.5" />
                                {session.start_time && session.end_time
                                  ? `${session.start_time} - ${session.end_time}`
                                  : session.start_time || session.end_time
                                }
                              </span>
                            )}
                            {session.attendance_count !== undefined && session.attendance_count !== null && (
                              <span className="badge-purple inline-flex items-center gap-1">
                                <Users className="w-3 h-3" />
                                {session.attendance_count} checked in
                              </span>
                            )}
                          </div>
                          {session.description && (
                            <p className="text-sm text-gray-500 mt-1">{session.description}</p>
                          )}
                          {session.location && (
                            <div className="flex items-center gap-1.5 text-sm text-gray-500 mt-2">
                              <MapPin className="w-3.5 h-3.5" />
                              {session.location}
                            </div>
                          )}
                          {session.sms_confirmation_enabled && (
                            <span className="badge-green mt-2 inline-flex items-center gap-1">
                              <MessageSquare className="w-3 h-3" />
                              SMS enabled
                            </span>
                          )}
                        </div>
                        <div className="flex gap-1 ml-4" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => openCheckIn(session)}
                            className="p-2 hover:bg-green-50 rounded-lg transition-colors"
                            title="Check In Attendees"
                          >
                            <UserCheck className="w-4 h-4 text-green-600" />
                          </button>
                          <button
                            onClick={() => openEditForm(session)}
                            className="p-2 hover:bg-purple-50 rounded-lg transition-colors"
                            title="Edit Session"
                          >
                            <Edit className="w-4 h-4 text-purple-600" />
                          </button>
                          <button
                            onClick={() => openDeleteDialog(session)}
                            className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete Session"
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </button>
                        </div>
                      </div>
                    ))}
                    {(!sessionsByDay[day.day_number] || sessionsByDay[day.day_number].length === 0) && (
                      <p className="text-sm text-gray-400 text-center py-6">No sessions yet</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Session Check-In Modal - Rendered via Portal to avoid clipping */}
        {checkInSession && createPortal(
          <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-[60] animate-fade-in">
            <div className="modal-content modal-content-lg animate-modal-enter">
              {/* Modal Header */}
              <div className="modal-header">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Session Check-In</h3>
                  <p className="text-sm text-gray-500 mt-0.5">{checkInSession.name}</p>
                </div>
                <button
                  onClick={closeCheckIn}
                  className="btn-icon-sm"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="modal-body">
                {/* Success Message */}
                {checkInResult && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4 animate-fade-in">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <h4 className="font-medium text-green-900">Check-In Successful!</h4>
                        <p className="text-sm text-green-700">{checkInResult.user_name}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Voice Greeting Audio Player */}
                {checkInResult?.greeting_audio && (
                  <div className="mb-4">
                    <GreetingAudioPlayer
                      greetingAudio={checkInResult.greeting_audio}
                      autoPlay={true}
                      onPlaybackComplete={() => {
                        // Optionally clear the result after playback
                      }}
                    />
                  </div>
                )}

                {/* Error Message */}
                {checkInError && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 animate-fade-in">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <XCircle className="w-5 h-5 text-red-600" />
                      </div>
                      <div>
                        <h4 className="font-medium text-red-900">Check-In Failed</h4>
                        <p className="text-sm text-red-700">{checkInError}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab Navigation */}
                <div className="flex gap-1 mb-4 p-1 bg-gray-100 rounded-lg">
                  <button
                    onClick={() => setCheckInTab('qr')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                      checkInTab === 'qr'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <QrCode className="w-4 h-4" />
                    QR Code
                  </button>
                  <button
                    onClick={() => setCheckInTab('phone')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                      checkInTab === 'phone'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <Phone className="w-4 h-4" />
                    Phone
                  </button>
                  <button
                    onClick={() => setCheckInTab('search')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                      checkInTab === 'search'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <Search className="w-4 h-4" />
                    Search
                  </button>
                </div>

                {/* QR Tab Content */}
                {checkInTab === 'qr' && (
                  <div className="card mb-4">
                    <div className="space-y-3">
                      <input
                        type="text"
                        value={registrationCode}
                        onChange={(e) => setRegistrationCode(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleQRCheckIn(registrationCode)}
                        className="input text-lg font-mono"
                        placeholder="Enter or scan registration code..."
                      />
                      <div className="flex gap-3">
                        <button
                          onClick={() => handleQRCheckIn(registrationCode)}
                          disabled={checkInLoading || !registrationCode}
                          className="btn-primary flex-1 py-3"
                        >
                          {checkInLoading ? 'Checking In...' : 'Check In'}
                        </button>
                        <button
                          onClick={() => setShowScanner(true)}
                          className="btn-secondary px-5"
                          title="Open Camera Scanner"
                        >
                          <QrCode className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Phone Tab Content */}
                {checkInTab === 'phone' && (
                  <div className="card mb-4">
                    <div className="space-y-3">
                      <input
                        type="tel"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handlePhoneCheckIn(phoneNumber)}
                        className="input text-lg"
                        placeholder="Enter phone number (e.g., +233244123456)"
                      />
                      <button
                        onClick={() => handlePhoneCheckIn(phoneNumber)}
                        disabled={checkInLoading || phoneNumber.length < 6}
                        className="btn-primary w-full py-3"
                      >
                        {checkInLoading ? 'Checking In...' : 'Check In'}
                      </button>
                    </div>
                  </div>
                )}

                {/* Search Tab Content */}
                {checkInTab === 'search' && (
                  <div className="card mb-4">
                    <div className="flex gap-2 mb-4">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        className="input flex-1"
                        placeholder="Search by name or phone..."
                      />
                      <button
                        onClick={handleSearch}
                        disabled={searching || searchQuery.length < 2}
                        className="btn-primary"
                      >
                        {searching ? 'Searching...' : 'Search'}
                      </button>
                    </div>

                    {/* Search Results */}
                    {searchResults.length > 0 && (
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {searchResults.map((r) => (
                          <div
                            key={r.id}
                            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100"
                          >
                            <div>
                              <p className="font-medium text-gray-900">{r.user_name}</p>
                              <p className="text-sm text-gray-500">{r.user_phone}</p>
                            </div>
                            <button
                              onClick={() => handleManualCheckIn(r.id)}
                              disabled={checkInLoading}
                              className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                            >
                              Check In
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Attendance List */}
                <div className="card">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                      <Users className="w-4 h-4 text-purple-600" />
                    </div>
                    <h4 className="font-medium text-gray-900">
                      Attendance <span className="badge-purple ml-2">{attendees.length}</span>
                    </h4>
                  </div>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {attendees.map((a) => (
                      <div
                        key={a.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100"
                      >
                        <div>
                          <p className="font-medium text-gray-900">{a.user_name}</p>
                          <p className="text-sm text-gray-500">{a.user_phone}</p>
                        </div>
                        <div className="text-xs text-gray-400 flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {new Date(a.checked_in_at).toLocaleTimeString()}
                        </div>
                      </div>
                    ))}
                    {attendees.length === 0 && (
                      <p className="text-center text-gray-400 py-6 text-sm">No check-ins yet</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>,
          document.body
        )}

        {/* Camera QR Scanner Modal */}
        {showScanner && (
          <CameraQRScanner
            onScan={(code) => {
              setShowScanner(false)
              setRegistrationCode(code)
              handleQRCheckIn(code)
            }}
            onClose={() => setShowScanner(false)}
          />
        )}

        {/* Session Form Modal - Rendered via Portal to avoid clipping */}
        {showForm && createPortal(
          <div
            className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-[60] animate-fade-in"
            onKeyDown={(e) => {
              if (e.key === 'Escape') {
                setShowForm(false);
                setEditingSession(null);
                resetForm();
              }
            }}
          >
            <div className="modal-content modal-content-md animate-modal-enter">
              <div className="modal-header">
                <h3 className="text-lg font-semibold text-gray-900">
                  {editingSession ? 'Edit Session' : 'New Session'}
                </h3>
                <button
                  type="button"
                  onClick={() => { setShowForm(false); setEditingSession(null); resetForm(); }}
                  className="btn-icon-sm"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <form onSubmit={handleSubmit} className="modal-body space-y-4">
                <div>
                  <label className="label">Session Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                    className="input"
                    required
                    autoFocus
                  />
                </div>

                <div>
                  <label className="label">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                    className="input"
                    rows={3}
                  />
                </div>

                <div>
                  <label className="label">Location</label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={e => setFormData({ ...formData, location: e.target.value })}
                    className="input"
                    placeholder="e.g., Main Auditorium, Room 101"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <TimePicker
                    value={formData.start_time}
                    onChange={(value) => setFormData({ ...formData, start_time: value })}
                    label="Start Time"
                    required
                    maxTime={formData.end_time}
                  />
                  <TimePicker
                    value={formData.end_time}
                    onChange={(value) => setFormData({ ...formData, end_time: value })}
                    label="End Time"
                    required
                    minTime={formData.start_time}
                  />
                </div>

                <div>
                  <label className="label">Day Label</label>
                  <input
                    type="text"
                    value={formData.day_label}
                    onChange={e => setFormData({ ...formData, day_label: e.target.value })}
                    className="input"
                    required
                  />
                </div>

                {/* SMS Confirmation Settings */}
                <div className="border-t border-gray-100 pt-4 mt-4">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                      <MessageSquare className="w-4 h-4 text-purple-600" />
                    </div>
                    <h4 className="font-medium text-gray-900">SMS Confirmation</h4>
                  </div>

                  <label className="flex items-center gap-2 mb-3 cursor-pointer">
                    <input
                      type="checkbox"
                      id="sms_confirmation_enabled"
                      checked={formData.sms_confirmation_enabled}
                      onChange={e => setFormData({ ...formData, sms_confirmation_enabled: e.target.checked })}
                      className="w-4 h-4 text-purple-600 rounded border-gray-300 focus:ring-purple-500"
                    />
                    <span className="text-sm text-gray-700">
                      Send SMS when attendees check in to this session
                    </span>
                  </label>

                  {formData.sms_confirmation_enabled && (
                    <div>
                      <label className="label">SMS Message Template</label>
                      <textarea
                        value={formData.sms_confirmation_template}
                        onChange={e => setFormData({ ...formData, sms_confirmation_template: e.target.value })}
                        placeholder="Hi {name}, you're checked in to {session_name}. Welcome to {day_label}!"
                        className="input"
                        rows={3}
                        maxLength={160}
                      />
                      <div className="flex justify-between items-center mt-1.5">
                        <p className="text-xs text-gray-400">
                          Placeholders: {'{name}'}, {'{session_name}'}, {'{day_label}'}, {'{location}'}
                        </p>
                        <p className="text-xs text-gray-400">
                          {(formData.sms_confirmation_template || '').length}/160
                        </p>
                      </div>
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    onClick={() => {
                      setShowForm(false)
                      setEditingSession(null)
                      resetForm()
                    }}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                  >
                    {editingSession ? 'Update' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          </div>,
          document.body
        )}

        {/* Delete Confirmation Dialog */}
        <ConfirmDialog
          isOpen={deleteDialog.isOpen}
          onClose={() => setDeleteDialog({ isOpen: false, sessionId: null, sessionName: '', isLoading: false })}
          onConfirm={handleDelete}
          title="Delete Session"
          message="Are you sure you want to delete this session? All attendance records for this session will also be removed."
          itemName={deleteDialog.sessionName}
          confirmText="Delete Session"
          cancelText="Keep Session"
          variant="danger"
          isLoading={deleteDialog.isLoading}
        />

        {/* Info/Notification Dialog */}
        <ConfirmDialog
          isOpen={infoDialog.isOpen}
          onClose={() => setInfoDialog({ ...infoDialog, isOpen: false })}
          onConfirm={() => setInfoDialog({ ...infoDialog, isOpen: false })}
          title={infoDialog.title}
          message={infoDialog.message}
          confirmText="OK"
          cancelText=""
          variant={infoDialog.variant}
        />
    </div>
  )
}
