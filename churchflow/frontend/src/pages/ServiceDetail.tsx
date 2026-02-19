import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Calendar,
  Clock,
  Users,
  Edit3,
  QrCode,
  UserCheck,
  Download,
  ExternalLink,
  Church,
  BookOpen,
  Mic,
  Video,
  FileText
} from 'lucide-react'
import { getApiUrl } from '../config/api-config'

interface Service {
  id: string
  service_type: string
  branch_id: string
  organization_id: string
  sermon_title: string | null
  series_name: string | null
  scripture_reference: string | null
  speaker: string | null
  sermon_recording_url: string | null
  sermon_notes_url: string | null
  livestream_link: string | null
  service_date: string
  start_time: string
  end_time: string
  status: string
  expected_attendance: number | null
  actual_attendance: number
  qr_code: string | null
  venue_checkin_radius: number
  is_recurring: boolean
  created_at: string
  updated_at: string
}

interface AttendanceSummary {
  service_id: string
  total_attendees: number
  members: number
  visitors: number
  first_timers: number
}

interface Attendee {
  id: string
  user_id: string
  user_name: string
  user_phone: string
  member_status: string
  checked_in_at: string
  check_in_method: string
}

type TabId = 'overview' | 'attendance' | 'edit'

export default function ServiceDetail() {
  const { serviceId } = useParams<{ serviceId: string }>()
  const navigate = useNavigate()
  const [service, setService] = useState<Service | null>(null)
  const [attendanceSummary, setAttendanceSummary] = useState<AttendanceSummary | null>(null)
  const [attendees, setAttendees] = useState<Attendee[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const [filterMemberStatus, setFilterMemberStatus] = useState<string>('')
  const [editMode, setEditMode] = useState(false)

  const [editFormData, setEditFormData] = useState({
    speaker: '',
    sermon_title: '',
    series_name: '',
    scripture_reference: '',
    sermon_recording_url: '',
    sermon_notes_url: '',
    livestream_link: '',
    status: 'upcoming'
  })

  useEffect(() => {
    if (serviceId) {
      fetchService(serviceId)
      fetchAttendanceSummary(serviceId)
    }
  }, [serviceId])

  useEffect(() => {
    if (activeTab === 'attendance' && serviceId) {
      fetchAttendees(serviceId)
    }
  }, [activeTab, serviceId, filterMemberStatus])

  const fetchService = async (id: string) => {
    setLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(getApiUrl(`services/${id}`), { headers })
      if (response.ok) {
        const data = await response.json()
        setService(data)
        setEditFormData({
          speaker: data.speaker || '',
          sermon_title: data.sermon_title || '',
          series_name: data.series_name || '',
          scripture_reference: data.scripture_reference || '',
          sermon_recording_url: data.sermon_recording_url || '',
          sermon_notes_url: data.sermon_notes_url || '',
          livestream_link: data.livestream_link || '',
          status: data.status
        })
      }
    } catch (err) {
      console.error('Failed to load service:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchAttendanceSummary = async (id: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(getApiUrl(`services/${id}/attendance`), { headers })
      if (response.ok) {
        const data = await response.json()
        setAttendanceSummary(data)
      }
    } catch (err) {
      console.error('Failed to load attendance summary:', err)
    }
  }

  const fetchAttendees = async (id: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const params = new URLSearchParams()
      if (filterMemberStatus) params.append('member_status', filterMemberStatus)

      const response = await fetch(getApiUrl(`services/${id}/attendees?${params.toString()}`), { headers })
      if (response.ok) {
        const data = await response.json()
        setAttendees(data.attendees || [])
      }
    } catch (err) {
      console.error('Failed to load attendees:', err)
    }
  }

  const handleUpdateService = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem('access_token')

    if (!token || !serviceId) {
      alert('Please login to update services')
      return
    }

    try {
      const response = await fetch(getApiUrl(`services/${serviceId}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(editFormData)
      })

      if (response.ok) {
        alert('Service updated successfully!')
        setEditMode(false)
        fetchService(serviceId)
      } else {
        const error = await response.json()
        alert(`Failed to update service: ${error.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Error updating service:', err)
      alert('Failed to update service')
    }
  }

  const exportAttendees = () => {
    if (attendees.length === 0) {
      alert('No attendees to export')
      return
    }

    const csv = [
      ['Name', 'Phone', 'Member Status', 'Check-in Time', 'Check-in Method'],
      ...attendees.map(a => [
        a.user_name,
        a.user_phone,
        a.member_status,
        new Date(a.checked_in_at).toLocaleString(),
        a.check_in_method
      ])
    ]
      .map(row => row.join(','))
      .join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `service-${serviceId}-attendees.csv`
    a.click()
  }

  const getServiceTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'sunday_8am': 'Sunday 8:00 AM',
      'sunday_10am': 'Sunday 10:00 AM',
      'midweek': 'Midweek Service',
      'special': 'Special Service'
    }
    return labels[type] || type
  }

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      'upcoming': 'bg-blue-100 text-blue-800',
      'ongoing': 'bg-green-100 text-green-800',
      'completed': 'bg-gray-100 text-gray-800',
      'cancelled': 'bg-red-100 text-red-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  if (!serviceId) {
    return (
      <div className="p-6">
        <p className="text-gray-600">No service selected.</p>
      </div>
    )
  }

  if (loading || !service) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm text-gray-500">Loading service...</p>
        </div>
      </div>
    )
  }

  const tabs: { id: TabId; label: string; icon: any }[] = [
    { id: 'overview', label: 'Overview', icon: Church },
    { id: 'attendance', label: 'Attendance', icon: Users },
    { id: 'edit', label: 'Edit Details', icon: Edit3 }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/admin/services')}
            className="text-xs text-gray-500 hover:text-gray-700 mb-2"
          >
            ← Back to Services
          </button>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Church className="w-8 h-8 text-purple-600" />
            {getServiceTypeLabel(service.service_type)}
          </h1>
          <p className="text-gray-600 mt-1 flex flex-wrap items-center gap-3 text-sm">
            <span className="inline-flex items-center gap-1">
              <Calendar className="w-4 h-4 text-gray-400" />
              {formatDate(service.service_date)}
            </span>
            <span className="inline-flex items-center gap-1">
              <Clock className="w-4 h-4 text-gray-400" />
              {service.start_time} - {service.end_time}
            </span>
            <span className="inline-flex items-center gap-1">
              <Users className="w-4 h-4 text-gray-400" />
              {service.actual_attendance} attendees
            </span>
            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(service.status)}`}>
              {service.status}
            </span>
          </p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="border-b border-gray-200 px-4 pt-4">
            <div className="flex flex-wrap gap-2">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-purple-50 text-purple-700 border border-purple-200'
                        : 'text-gray-600 hover:bg-gray-50 border border-transparent'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="p-4 md:p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Service Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-2 flex items-center gap-2">
                        <Mic className="w-4 h-4" />
                        Speaker
                      </h3>
                      <p className="text-lg font-semibold text-gray-900">{service.speaker || 'TBA'}</p>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-2 flex items-center gap-2">
                        <BookOpen className="w-4 h-4" />
                        Sermon Title
                      </h3>
                      <p className="text-lg text-gray-900">{service.sermon_title || 'No title'}</p>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-2">Series</h3>
                      <p className="text-gray-900">{service.series_name || 'N/A'}</p>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-2">Scripture Reference</h3>
                      <p className="text-gray-900">{service.scripture_reference || 'N/A'}</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {/* Attendance Stats */}
                    {attendanceSummary && (
                      <div className="bg-purple-50 p-4 rounded-lg">
                        <h3 className="text-sm font-medium text-gray-700 mb-3">Attendance Summary</h3>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <p className="text-xs text-gray-600">Total</p>
                            <p className="text-2xl font-bold text-purple-600">{attendanceSummary.total_attendees}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600">Members</p>
                            <p className="text-2xl font-bold text-gray-900">{attendanceSummary.members}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600">Visitors</p>
                            <p className="text-2xl font-bold text-gray-900">{attendanceSummary.visitors}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600">First Timers</p>
                            <p className="text-2xl font-bold text-green-600">{attendanceSummary.first_timers}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Media Links */}
                    <div className="space-y-2">
                      <h3 className="text-sm font-medium text-gray-500 mb-2">Media & Resources</h3>

                      {service.livestream_link && (
                        <a
                          href={service.livestream_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700"
                        >
                          <Video className="w-4 h-4" />
                          Livestream Link
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}

                      {service.sermon_recording_url && (
                        <a
                          href={service.sermon_recording_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700"
                        >
                          <Mic className="w-4 h-4" />
                          Sermon Recording
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}

                      {service.sermon_notes_url && (
                        <a
                          href={service.sermon_notes_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700"
                        >
                          <FileText className="w-4 h-4" />
                          Sermon Notes
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}

                      {!service.livestream_link && !service.sermon_recording_url && !service.sermon_notes_url && (
                        <p className="text-sm text-gray-500">No media available</p>
                      )}
                    </div>

                    {/* QR Code */}
                    {service.qr_code && (
                      <div>
                        <h3 className="text-sm font-medium text-gray-500 mb-2 flex items-center gap-2">
                          <QrCode className="w-4 h-4" />
                          QR Code for Check-in
                        </h3>
                        <p className="text-xs text-gray-500 font-mono bg-gray-50 p-2 rounded">
                          {service.qr_code}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Attendance Tab */}
            {activeTab === 'attendance' && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <div className="flex gap-3">
                    <select
                      value={filterMemberStatus}
                      onChange={(e) => setFilterMemberStatus(e.target.value)}
                      className="p-2 border rounded-lg text-sm"
                    >
                      <option value="">All Attendees</option>
                      <option value="active_member">Members Only</option>
                      <option value="visitor">Visitors Only</option>
                    </select>
                  </div>

                  <button
                    onClick={exportAttendees}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
                  >
                    <Download className="w-4 h-4" />
                    Export CSV
                  </button>
                </div>

                <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Check-in Time</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Method</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {attendees.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                            No attendees found
                          </td>
                        </tr>
                      ) : (
                        attendees.map(attendee => (
                          <tr key={attendee.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {attendee.user_name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {attendee.user_phone}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                attendee.member_status === 'active_member'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-blue-100 text-blue-800'
                              }`}>
                                {attendee.member_status === 'active_member' ? 'Member' : 'Visitor'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(attendee.checked_in_at).toLocaleString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {attendee.check_in_method}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Edit Tab */}
            {activeTab === 'edit' && (
              <div className="space-y-4">
                {!editMode && (
                  <button
                    onClick={() => setEditMode(true)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                  >
                    Edit Service Details
                  </button>
                )}

                {editMode && (
                  <form onSubmit={handleUpdateService} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Speaker</label>
                        <input
                          type="text"
                          value={editFormData.speaker}
                          onChange={(e) => setEditFormData({ ...editFormData, speaker: e.target.value })}
                          className="w-full p-2 border rounded-lg"
                          placeholder="Speaker name"
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Sermon Title</label>
                        <input
                          type="text"
                          value={editFormData.sermon_title}
                          onChange={(e) => setEditFormData({ ...editFormData, sermon_title: e.target.value })}
                          className="w-full p-2 border rounded-lg"
                          placeholder="Sermon title"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Series Name</label>
                        <input
                          type="text"
                          value={editFormData.series_name}
                          onChange={(e) => setEditFormData({ ...editFormData, series_name: e.target.value })}
                          className="w-full p-2 border rounded-lg"
                          placeholder="Series name"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Scripture Reference</label>
                        <input
                          type="text"
                          value={editFormData.scripture_reference}
                          onChange={(e) => setEditFormData({ ...editFormData, scripture_reference: e.target.value })}
                          className="w-full p-2 border rounded-lg"
                          placeholder="e.g., John 3:16"
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Sermon Recording URL</label>
                        <input
                          type="url"
                          value={editFormData.sermon_recording_url}
                          onChange={(e) => setEditFormData({ ...editFormData, sermon_recording_url: e.target.value })}
                          className="w-full p-2 border rounded-lg"
                          placeholder="https://..."
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Sermon Notes URL</label>
                        <input
                          type="url"
                          value={editFormData.sermon_notes_url}
                          onChange={(e) => setEditFormData({ ...editFormData, sermon_notes_url: e.target.value })}
                          className="w-full p-2 border rounded-lg"
                          placeholder="https://..."
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Livestream Link</label>
                        <input
                          type="url"
                          value={editFormData.livestream_link}
                          onChange={(e) => setEditFormData({ ...editFormData, livestream_link: e.target.value })}
                          className="w-full p-2 border rounded-lg"
                          placeholder="https://..."
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                        <select
                          value={editFormData.status}
                          onChange={(e) => setEditFormData({ ...editFormData, status: e.target.value })}
                          className="w-full p-2 border rounded-lg"
                        >
                          <option value="upcoming">Upcoming</option>
                          <option value="ongoing">Ongoing</option>
                          <option value="completed">Completed</option>
                          <option value="cancelled">Cancelled</option>
                        </select>
                      </div>
                    </div>

                    <div className="flex justify-end gap-3 mt-6">
                      <button
                        type="button"
                        onClick={() => setEditMode(false)}
                        className="px-4 py-2 text-gray-700 border rounded-lg hover:bg-gray-50"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                      >
                        Update Service
                      </button>
                    </div>
                  </form>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
