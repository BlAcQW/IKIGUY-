import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Edit, Users, Calendar, MapPin, CheckCircle, Mic, CalendarDays, ClipboardList, List, Grid } from 'lucide-react'
import VoiceSettingsModal from '../components/VoiceSettingsModal'
import SessionManager from '../components/SessionManager'
import AttendanceReport from '../components/AttendanceReport'
import MapPicker from '../components/MapPicker'

interface Conference {
  id: string
  name: string
  description: string | null
  venue: string
  venue_latitude: number | null
  venue_longitude: number | null
  venue_checkin_radius: number
  start_date: string
  end_date: string
  registration_open: boolean
  self_checkin_enabled?: boolean
  allow_repeat_checkin?: boolean
  location_checkin_required?: boolean
  max_attendees: number | null
  current_attendees: number
  status: string
}

export default function ConferenceManagement() {
  const navigate = useNavigate()
  const [conferences, setConferences] = useState<Conference[]>([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<'list' | 'card'>('list') // Default to list view
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingConference, setEditingConference] = useState<Conference | null>(null)
  const [voiceSettingsConference, setVoiceSettingsConference] = useState<Conference | null>(null)
  const [sessionManagerConference, setSessionManagerConference] = useState<Conference | null>(null)
  const [attendanceReportConference, setAttendanceReportConference] = useState<Conference | null>(null)
  // Delete confirmation dialog state
  const [deleteDialog, setDeleteDialog] = useState<{
    isOpen: boolean;
    conferenceId: string | null;
    conferenceName: string;
    isLoading: boolean;
  }>({ isOpen: false, conferenceId: null, conferenceName: '', isLoading: false })
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    venue: '',
    venue_latitude: null as number | null,
    venue_longitude: null as number | null,
    venue_checkin_radius: 1000,
    start_date: '',
    end_date: '',
    registration_open: true,
    self_checkin_enabled: true,
    allow_repeat_checkin: true,
    location_checkin_required: true,
    max_attendees: 500
  })

  useEffect(() => {
    fetchConferences()
  }, [])

  const fetchConferences = async () => {
    const token = localStorage.getItem('access_token')

    try {
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('/api/v1/conferences', {
        headers
      })

      if (response.ok) {
        const data = await response.json()
        setConferences(data)
      }
    } catch (err) {
      console.error('Failed to fetch conferences:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateConference = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem('access_token')

    if (!token) {
      alert('Please login as a supervisor to create conferences')
      window.location.href = '/login'
      return
    }

    try {
      const response = await fetch('/api/v1/conferences', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...formData,
          start_date: new Date(formData.start_date).toISOString(),
          end_date: new Date(formData.end_date).toISOString()
        })
      })

      if (response.ok) {
        alert('Conference created successfully!')
        setShowCreateModal(false)
        setFormData({
          name: '',
          description: '',
          venue: '',
          venue_latitude: null,
          venue_longitude: null,
          venue_checkin_radius: 1000,
          start_date: '',
          end_date: '',
          registration_open: true,
          self_checkin_enabled: true,
          allow_repeat_checkin: true,
          location_checkin_required: true,
          max_attendees: 500
        })
        fetchConferences()
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        alert(`Failed to create conference: ${errorData.detail || 'Please try again'}`)
      }
    } catch (err) {
      console.error('Failed to create conference:', err)
      alert('Failed to create conference. Please check your connection and try again.')
    }
  }

  // Open delete confirmation dialog
  const openDeleteDialog = (conference: Conference) => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      alert('Please login as a supervisor to delete conferences')
      window.location.href = '/login'
      return
    }
    setDeleteDialog({
      isOpen: true,
      conferenceId: conference.id,
      conferenceName: conference.name,
      isLoading: false,
    })
  }

  // Handle confirmed delete
  const handleDeleteConference = async () => {
    if (!deleteDialog.conferenceId) return

    const token = localStorage.getItem('access_token')
    if (!token) return

    setDeleteDialog(prev => ({ ...prev, isLoading: true }))

    try {
      const response = await fetch(`/api/v1/conferences/${deleteDialog.conferenceId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        setDeleteDialog({ isOpen: false, conferenceId: null, conferenceName: '', isLoading: false })
        fetchConferences()
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        alert(`Failed to delete conference: ${errorData.detail || 'Please try again'}`)
        setDeleteDialog(prev => ({ ...prev, isLoading: false }))
      }
    } catch (err) {
      console.error('Failed to delete conference:', err)
      alert('Failed to delete conference. Please check your connection and try again.')
      setDeleteDialog(prev => ({ ...prev, isLoading: false }))
    }
  }

  const formatDatetimeForInput = (isoString: string): string => {
    // Convert ISO datetime to format required by datetime-local input
    // "2025-11-15T09:00:00Z" → "2025-11-15T09:00"
    return isoString.substring(0, 16)
  }

  const openEditModal = (conference: Conference) => {
    setEditingConference(conference)
    setFormData({
      name: conference.name,
      description: conference.description || '',
      venue: conference.venue,
      venue_latitude: conference.venue_latitude,
      venue_longitude: conference.venue_longitude,
      venue_checkin_radius: conference.venue_checkin_radius || 1000,
      start_date: formatDatetimeForInput(conference.start_date),
      end_date: formatDatetimeForInput(conference.end_date),
      registration_open: conference.registration_open,
      self_checkin_enabled: conference.self_checkin_enabled ?? true,
      allow_repeat_checkin: conference.allow_repeat_checkin ?? true,
      location_checkin_required: conference.location_checkin_required ?? true,
      max_attendees: conference.max_attendees || 500
    })
    setShowEditModal(true)
  }

  const handleUpdateConference = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem('access_token')

    if (!token) {
      alert('Please login as a supervisor to update conferences')
      window.location.href = '/login'
      return
    }

    if (!editingConference) return

    try {
      const response = await fetch(`/api/v1/conferences/${editingConference.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...formData,
          start_date: new Date(formData.start_date).toISOString(),
          end_date: new Date(formData.end_date).toISOString()
        })
      })

      if (response.ok) {
        alert('Conference updated successfully!')
        setShowEditModal(false)
        setEditingConference(null)
        setFormData({
          name: '',
          description: '',
          venue: '',
          venue_latitude: null,
          venue_longitude: null,
          venue_checkin_radius: 1000,
          start_date: '',
          end_date: '',
          registration_open: true,
          self_checkin_enabled: true,
          allow_repeat_checkin: true,
          location_checkin_required: true,
          max_attendees: 500
        })
        fetchConferences()
      } else if (response.status === 401) {
        // Handle unauthorized - token expired or invalid
        alert('Your session has expired. Please login again.')
        localStorage.removeItem('access_token')
        window.location.href = '/login?redirect=/conference-management'
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        alert(`Failed to update conference: ${errorData.detail || 'Please try again'}`)
      }
    } catch (err) {
      console.error('Failed to update conference:', err)
      alert('Failed to update conference. Please check your connection and try again.')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'upcoming': return 'bg-blue-100 text-blue-700'
      case 'ongoing': return 'bg-green-100 text-green-700'
      case 'completed': return 'bg-gray-100 text-gray-700'
      case 'cancelled': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Conference Management</h1>
        <div className="flex gap-3">
          {/* View Mode Toggle */}
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-md transition-all ${
                viewMode === 'list'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              title="List View"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('card')}
              className={`p-2 rounded-md transition-all ${
                viewMode === 'card'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              title="Card View"
            >
              <Grid className="w-4 h-4" />
            </button>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create Conference
          </button>
        </div>
      </div>

      {/* Conferences List View */}
      {viewMode === 'list' && (
        <div className="space-y-3">
          {conferences.map((conference) => (
            <div
              key={conference.id}
              className="card cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/conferences/${conference.id}`)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-gray-900">{conference.name}</h3>
                      <span className={`badge ${getStatusColor(conference.status)}`}>
                        {conference.status.toUpperCase()}
                      </span>
                      {conference.registration_open && (
                        <span className="badge-green">Registration Open</span>
                      )}
                    </div>
                    {conference.description && (
                      <p className="text-sm text-gray-600 mt-1">{conference.description}</p>
                    )}
                    <div className="flex items-center gap-6 mt-2 text-sm text-gray-600">
                      <div className="flex items-center gap-1.5">
                        <MapPin className="w-4 h-4" />
                        <span>{conference.venue}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-4 h-4" />
                        <span>
                          {new Date(conference.start_date).toLocaleDateString()} - {new Date(conference.end_date).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Users className="w-4 h-4" />
                        <span>
                          {conference.current_attendees} registered
                          {conference.max_attendees && ` / ${conference.max_attendees} max`}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => setVoiceSettingsConference(conference)}
                    className="btn-icon-sm hover:bg-purple-50 text-purple-600"
                    title="Voice Greeting Settings"
                  >
                    <Mic className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setSessionManagerConference(conference)}
                    className="btn-icon-sm hover:bg-blue-50 text-blue-600"
                    title="Manage Sessions"
                  >
                    <CalendarDays className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setAttendanceReportConference(conference)}
                    className="btn-icon-sm hover:bg-green-50 text-green-600"
                    title="Attendance Report"
                  >
                    <ClipboardList className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => openEditModal(conference)}
                    className="btn-icon-sm"
                    title="Edit Conference"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Conferences Card View */}
      {viewMode === 'card' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {conferences.map((conference) => (
          <div
            key={conference.id}
            className="card cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => navigate(`/conferences/${conference.id}`)}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{conference.name}</h3>
                <span className={`badge mt-2 ${getStatusColor(conference.status)}`}>
                  {conference.status.toUpperCase()}
                </span>
              </div>
              <div className="flex gap-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setVoiceSettingsConference(conference)
                  }}
                  className="btn-icon-sm hover:bg-purple-50 text-purple-600"
                  title="Voice Greeting Settings"
                >
                  <Mic className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setSessionManagerConference(conference)
                  }}
                  className="btn-icon-sm hover:bg-blue-50 text-blue-600"
                  title="Manage Sessions"
                >
                  <CalendarDays className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setAttendanceReportConference(conference)
                  }}
                  className="btn-icon-sm hover:bg-green-50 text-green-600"
                  title="Attendance Report"
                >
                  <ClipboardList className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    openEditModal(conference)
                  }}
                  className="btn-icon-sm"
                  title="Edit Conference"
                >
                  <Edit className="w-4 h-4" />
                </button>
              </div>
            </div>

            {conference.description && (
              <p className="text-sm text-gray-600 mb-4">{conference.description}</p>
            )}

            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <MapPin className="w-4 h-4" />
                <span>{conference.venue}</span>
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Calendar className="w-4 h-4" />
                <span>
                  {new Date(conference.start_date).toLocaleDateString()} - {new Date(conference.end_date).toLocaleDateString()}
                </span>
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Users className="w-4 h-4" />
                <span>
                  {conference.current_attendees} registered
                  {conference.max_attendees && ` / ${conference.max_attendees} max`}
                </span>
              </div>

              {conference.registration_open && (
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <CheckCircle className="w-4 h-4" />
                  <span>Registration Open</span>
                </div>
              )}
            </div>

            {conference.max_attendees && (
              <div className="mt-4 pt-4 border-t">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${(conference.current_attendees / conference.max_attendees) * 100}%` }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {Math.round((conference.current_attendees / conference.max_attendees) * 100)}% capacity
                </p>
              </div>
            )}
          </div>
        ))}
        </div>
      )}

      {conferences.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No conferences created yet.</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 text-purple-600 hover:underline"
          >
            Create your first conference
          </button>
        </div>
      )}

      {/* Create Conference Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 overflow-y-auto animate-fade-in" onClick={() => setShowCreateModal(false)}>
          <div className="min-h-full flex items-end sm:items-center justify-center p-0 sm:p-4">
            <form onSubmit={handleCreateConference} className="modal-content modal-content-lg animate-modal-enter w-full sm:max-w-2xl rounded-t-2xl sm:rounded-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header px-4 sm:px-6 py-4">
              <h2 className="text-lg font-semibold">Create Conference</h2>
            </div>

              <div className="modal-body space-y-4 px-4 sm:px-6">
                <div>
                  <label className="label">Conference Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input"
                    placeholder="e.g., Impact Conference 2025"
                    required
                  />
                </div>

                <div>
                  <label className="label">Description (Optional)</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="input"
                    placeholder="Conference description"
                    rows={3}
                  />
                </div>

                <div>
                  <label className="label">Venue</label>
                  <input
                    type="text"
                    value={formData.venue}
                    onChange={(e) => setFormData({ ...formData, venue: e.target.value })}
                    className="input"
                    placeholder="e.g., National Theatre, Accra"
                    required
                  />
                </div>

                <div>
                  <label className="label">Venue Location (GPS Coordinates)</label>
                  <div className="mb-3">
                    <MapPicker
                      latitude={formData.venue_latitude}
                      longitude={formData.venue_longitude}
                      onLocationSelect={(lat, lng) => setFormData({
                        ...formData,
                        venue_latitude: lat,
                        venue_longitude: lng
                      })}
                      height="200px"
                    />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="label-sm">Latitude</label>
                      <input
                        type="number"
                        step="any"
                        value={formData.venue_latitude || ''}
                        onChange={(e) => setFormData({
                          ...formData,
                          venue_latitude: e.target.value ? parseFloat(e.target.value) : null
                        })}
                        className="input min-h-[44px]"
                        placeholder="5.6037"
                      />
                    </div>
                    <div>
                      <label className="label-sm">Longitude</label>
                      <input
                        type="number"
                        step="any"
                        value={formData.venue_longitude || ''}
                        onChange={(e) => setFormData({
                          ...formData,
                          venue_longitude: e.target.value ? parseFloat(e.target.value) : null
                        })}
                        className="input min-h-[44px]"
                        placeholder="-0.1870"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="label">Check-in Radius (meters)</label>
                  <input
                    type="number"
                    value={formData.venue_checkin_radius}
                    onChange={(e) => setFormData({ ...formData, venue_checkin_radius: parseInt(e.target.value) })}
                    className="input"
                    min="50"
                    max="5000"
                    step="50"
                    required
                  />
                  <p className="helper-text">
                    Members must be within this distance to self-check-in (50m - 5000m)
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                  <div>
                    <label className="label">Start Date</label>
                    <input
                      type="datetime-local"
                      value={formData.start_date}
                      onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                      className="input min-h-[44px]"
                      required
                    />
                  </div>
                  <div>
                    <label className="label">End Date</label>
                    <input
                      type="datetime-local"
                      value={formData.end_date}
                      onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                      className="input min-h-[44px]"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="label">Maximum Attendees</label>
                  <input
                    type="number"
                    value={formData.max_attendees}
                    onChange={(e) => setFormData({ ...formData, max_attendees: parseInt(e.target.value) })}
                    className="input"
                    min="1"
                    required
                  />
                </div>

                <div className="space-y-2 pt-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.registration_open}
                      onChange={(e) => setFormData({ ...formData, registration_open: e.target.checked })}
                      className="w-4 h-4 text-purple-600 rounded"
                    />
                    <span className="text-sm text-gray-700">Open for registration</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.self_checkin_enabled}
                      onChange={(e) => setFormData({ ...formData, self_checkin_enabled: e.target.checked })}
                      className="w-4 h-4 text-purple-600 rounded"
                    />
                    <span className="text-sm text-gray-700">Allow self-service check-in</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.allow_repeat_checkin}
                      onChange={(e) => setFormData({ ...formData, allow_repeat_checkin: e.target.checked })}
                      className="w-4 h-4 text-purple-600 rounded"
                    />
                    <span className="text-sm text-gray-700">Allow repeat check-ins</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.location_checkin_required}
                      onChange={(e) => setFormData({ ...formData, location_checkin_required: e.target.checked })}
                      className="w-4 h-4 text-purple-600 rounded"
                    />
                    <span className="text-sm text-gray-700">Require location verification</span>
                  </label>
                </div>
              </div>

              <div className="modal-footer px-4 sm:px-6 py-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary flex-1 min-h-[44px] touch-manipulation"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1 min-h-[44px] touch-manipulation"
                >
                  Create Conference
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Conference Modal - Enhanced with Sections */}
      {showEditModal && editingConference && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 overflow-y-auto animate-fade-in" onClick={() => { setShowEditModal(false); setEditingConference(null); }}>
          <div className="min-h-full flex items-end sm:items-center justify-center p-0 sm:p-4">
            <form onSubmit={handleUpdateConference} className="modal-content modal-content-lg animate-modal-enter w-full sm:max-w-2xl rounded-t-2xl sm:rounded-2xl" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header border-b border-gray-200 px-4 sm:px-6 py-4">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Edit Conference</h2>
                  <p className="text-sm text-gray-500 mt-1">Update conference details and settings</p>
                </div>
              </div>

              <div className="modal-body space-y-6 max-h-[70vh] overflow-y-auto px-4 sm:px-6">
                {/* Section 1: Basic Information */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
                    <Calendar className="w-4 h-4 text-purple-600" />
                    <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Basic Information</h3>
                  </div>

                  <div>
                    <label className="label">Conference Name</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="input"
                      placeholder="e.g., Impact Conference 2025"
                      required
                    />
                  </div>

                  <div>
                    <label className="label">Description</label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      className="input"
                      placeholder="Describe the conference theme, purpose, and highlights..."
                      rows={3}
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="label">Start Date & Time</label>
                      <input
                        type="datetime-local"
                        value={formData.start_date}
                        onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                        className="input min-h-[44px]"
                        required
                      />
                    </div>
                    <div>
                      <label className="label">End Date & Time</label>
                      <input
                        type="datetime-local"
                        value={formData.end_date}
                        onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                        className="input min-h-[44px]"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="label">Maximum Attendees</label>
                    <input
                      type="number"
                      value={formData.max_attendees}
                      onChange={(e) => setFormData({ ...formData, max_attendees: parseInt(e.target.value) })}
                      className="input"
                      min="1"
                      required
                    />
                    <p className="helper-text">
                      Currently {editingConference.current_attendees} registered
                    </p>
                  </div>
                </div>

                {/* Section 2: Venue & Location */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
                    <MapPin className="w-4 h-4 text-green-600" />
                    <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Venue & Location</h3>
                  </div>

                  <div>
                    <label className="label">Venue Name</label>
                    <input
                      type="text"
                      value={formData.venue}
                      onChange={(e) => setFormData({ ...formData, venue: e.target.value })}
                      className="input"
                      placeholder="e.g., National Theatre, Accra"
                      required
                    />
                  </div>

                  <div>
                    <label className="label">Venue GPS Location</label>
                    <p className="text-xs text-gray-500 mb-2">Click on the map or enter coordinates manually</p>
                    <div className="mb-3 rounded-lg overflow-hidden border border-gray-200">
                      <MapPicker
                        latitude={formData.venue_latitude}
                        longitude={formData.venue_longitude}
                        onLocationSelect={(lat, lng) => setFormData({
                          ...formData,
                          venue_latitude: lat,
                          venue_longitude: lng
                        })}
                        height="180px"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="label-sm">Latitude</label>
                        <input
                          type="number"
                          step="any"
                          value={formData.venue_latitude || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            venue_latitude: e.target.value ? parseFloat(e.target.value) : null
                          })}
                          className="input text-sm"
                          placeholder="5.6037"
                        />
                      </div>
                      <div>
                        <label className="label-sm">Longitude</label>
                        <input
                          type="number"
                          step="any"
                          value={formData.venue_longitude || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            venue_longitude: e.target.value ? parseFloat(e.target.value) : null
                          })}
                          className="input text-sm"
                          placeholder="-0.1870"
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="label">Check-in Radius</label>
                    <div className="flex items-center gap-3">
                      <input
                        type="range"
                        value={formData.venue_checkin_radius}
                        onChange={(e) => setFormData({ ...formData, venue_checkin_radius: parseInt(e.target.value) })}
                        className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                        min="50"
                        max="5000"
                        step="50"
                      />
                      <div className="w-24">
                        <input
                          type="number"
                          value={formData.venue_checkin_radius}
                          onChange={(e) => setFormData({ ...formData, venue_checkin_radius: parseInt(e.target.value) || 50 })}
                          className="input text-sm text-center"
                          min="50"
                          max="5000"
                        />
                      </div>
                      <span className="text-sm text-gray-500 w-8">m</span>
                    </div>
                    <p className="helper-text mt-1">
                      Members must be within {formData.venue_checkin_radius}m of venue to self-check-in
                    </p>
                  </div>
                </div>

                {/* Section 3: Check-in Settings */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
                    <CheckCircle className="w-4 h-4 text-blue-600" />
                    <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Check-in Settings</h3>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <label className="flex items-start gap-3 cursor-pointer group">
                      <input
                        type="checkbox"
                        checked={formData.self_checkin_enabled}
                        onChange={(e) => setFormData({ ...formData, self_checkin_enabled: e.target.checked })}
                        className="w-5 h-5 text-purple-600 rounded mt-0.5"
                      />
                      <div>
                        <span className="text-sm font-medium text-gray-700 group-hover:text-purple-600">Allow self-service check-in</span>
                        <p className="text-xs text-gray-500 mt-0.5">Members can check themselves in from their phone</p>
                      </div>
                    </label>

                    <label className="flex items-start gap-3 cursor-pointer group">
                      <input
                        type="checkbox"
                        checked={formData.location_checkin_required}
                        onChange={(e) => setFormData({ ...formData, location_checkin_required: e.target.checked })}
                        className="w-5 h-5 text-purple-600 rounded mt-0.5"
                      />
                      <div>
                        <span className="text-sm font-medium text-gray-700 group-hover:text-purple-600">Require GPS location verification</span>
                        <p className="text-xs text-gray-500 mt-0.5">Members must be physically present at venue to check in</p>
                      </div>
                    </label>

                    <label className="flex items-start gap-3 cursor-pointer group">
                      <input
                        type="checkbox"
                        checked={formData.allow_repeat_checkin}
                        onChange={(e) => setFormData({ ...formData, allow_repeat_checkin: e.target.checked })}
                        className="w-5 h-5 text-purple-600 rounded mt-0.5"
                      />
                      <div>
                        <span className="text-sm font-medium text-gray-700 group-hover:text-purple-600">Allow repeat check-ins</span>
                        <p className="text-xs text-gray-500 mt-0.5">Members can check in multiple times across sessions</p>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Section 4: Conference Status */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
                    <Users className="w-4 h-4 text-orange-600" />
                    <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Conference Status</h3>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <label className="flex items-start gap-3 cursor-pointer group">
                      <input
                        type="checkbox"
                        checked={formData.registration_open}
                        onChange={(e) => setFormData({ ...formData, registration_open: e.target.checked })}
                        className="w-5 h-5 text-purple-600 rounded mt-0.5"
                      />
                      <div>
                        <span className="text-sm font-medium text-gray-700 group-hover:text-purple-600">Open for registration</span>
                        <p className="text-xs text-gray-500 mt-0.5">New members can register for this conference</p>
                      </div>
                    </label>
                  </div>

                  <div className="flex items-center gap-3 pt-2">
                    <span className="text-sm text-gray-600">Current Status:</span>
                    <span className={`badge ${getStatusColor(editingConference.status)}`}>
                      {editingConference.status.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="modal-footer border-t border-gray-200 bg-gray-50 px-4 sm:px-6 py-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false)
                    setEditingConference(null)
                  }}
                  className="btn-secondary flex-1 min-h-[44px] touch-manipulation"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1 min-h-[44px] touch-manipulation"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Voice Settings Modal */}
      {voiceSettingsConference && (
        <VoiceSettingsModal
          conferenceId={voiceSettingsConference.id}
          conferenceName={voiceSettingsConference.name}
          onClose={() => setVoiceSettingsConference(null)}
          onSave={() => {
            setVoiceSettingsConference(null)
            alert('Voice greeting settings saved successfully!')
          }}
        />
      )}

      {/* Session Manager Modal */}
      {sessionManagerConference && (
        <SessionManager
          conference={sessionManagerConference}
          onClose={() => setSessionManagerConference(null)}
        />
      )}

      {/* Attendance Report Modal */}
      {attendanceReportConference && (
        <AttendanceReport
          conferenceId={attendanceReportConference.id}
          conferenceName={attendanceReportConference.name}
          onClose={() => setAttendanceReportConference(null)}
        />
      )}

    </div>
  )
}
