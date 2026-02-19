import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Edit, Calendar, MapPin, Users, Clock, Trash2, RefreshCw, List, ChevronLeft, ChevronRight } from 'lucide-react'
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
  recurrence_rule: any
  created_at: string
  updated_at: string
  created_by: string | null
}

interface Branch {
  id: string
  name: string
}

export default function ServiceManagement() {
  const navigate = useNavigate()
  const [services, setServices] = useState<Service[]>([])
  const [branches, setBranches] = useState<Branch[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showRecurringModal, setShowRecurringModal] = useState(false)
  const [editingService, setEditingService] = useState<Service | null>(null)
  const [filterBranch, setFilterBranch] = useState<string>('')
  const [filterType, setFilterType] = useState<string>('')
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [viewMode, setViewMode] = useState<'list' | 'calendar'>('list')
  const [currentMonth, setCurrentMonth] = useState(new Date())

  const [formData, setFormData] = useState({
    service_type: 'sunday_8am',
    branch_id: '',
    sermon_title: '',
    series_name: '',
    scripture_reference: '',
    speaker: '',
    sermon_recording_url: '',
    sermon_notes_url: '',
    livestream_link: '',
    service_date: '',
    start_time: '08:00',
    end_time: '10:30',
    status: 'upcoming',
    expected_attendance: null as number | null
  })

  const [recurringFormData, setRecurringFormData] = useState({
    branch_id: '',
    organization_id: '',
    weeks_ahead: 8
  })

  useEffect(() => {
    fetchBranches()
    fetchServices()
  }, [filterBranch, filterType, filterStatus])

  const fetchBranches = async () => {
    const token = localStorage.getItem('access_token')

    try {
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(getApiUrl('branches'), {
        headers
      })

      if (response.ok) {
        const data = await response.json()
        setBranches(data)
      }
    } catch (err) {
      console.error('Failed to fetch branches:', err)
    }
  }

  const fetchServices = async () => {
    const token = localStorage.getItem('access_token')

    try {
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const params = new URLSearchParams()
      if (filterBranch) params.append('branch_id', filterBranch)
      if (filterType) params.append('service_type', filterType)
      if (filterStatus) params.append('status', filterStatus)
      params.append('limit', '100')

      const response = await fetch(getApiUrl(`services?${params.toString()}`), {
        headers
      })

      if (response.ok) {
        const data = await response.json()
        setServices(data.services || [])
      }
    } catch (err) {
      console.error('Failed to fetch services:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateService = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem('access_token')

    if (!token) {
      alert('Please login to create services')
      window.location.href = '/login'
      return
    }

    try {
      const response = await fetch(getApiUrl('services'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        alert('Service created successfully!')
        setShowCreateModal(false)
        fetchServices()
        resetForm()
      } else {
        const error = await response.json()
        alert(`Failed to create service: ${error.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Error creating service:', err)
      alert('Failed to create service')
    }
  }

  const handleUpdateService = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem('access_token')

    if (!token || !editingService) {
      alert('Please login to update services')
      return
    }

    try {
      const response = await fetch(getApiUrl(`services/${editingService.id}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        alert('Service updated successfully!')
        setShowEditModal(false)
        fetchServices()
        setEditingService(null)
        resetForm()
      } else {
        const error = await response.json()
        alert(`Failed to update service: ${error.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Error updating service:', err)
      alert('Failed to update service')
    }
  }

  const handleGenerateRecurring = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem('access_token')

    if (!token) {
      alert('Please login to generate services')
      return
    }

    try {
      const response = await fetch(getApiUrl('services/generate-recurring'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(recurringFormData)
      })

      if (response.ok) {
        const data = await response.json()
        alert(`${data.message}\n\nSunday 8am: ${data.stats.sunday_8am}\nSunday 10am: ${data.stats.sunday_10am}\nMidweek: ${data.stats.midweek}`)
        setShowRecurringModal(false)
        fetchServices()
      } else {
        const error = await response.json()
        alert(`Failed to generate services: ${error.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Error generating services:', err)
      alert('Failed to generate services')
    }
  }

  const handleDeleteService = async (serviceId: string) => {
    if (!confirm('Are you sure you want to delete this service?')) {
      return
    }

    const token = localStorage.getItem('access_token')

    try {
      const response = await fetch(getApiUrl(`services/${serviceId}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        alert('Service deleted successfully!')
        fetchServices()
      } else {
        const error = await response.json()
        alert(`Failed to delete service: ${error.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Error deleting service:', err)
      alert('Failed to delete service')
    }
  }

  const handleEditClick = (service: Service) => {
    setEditingService(service)
    setFormData({
      service_type: service.service_type,
      branch_id: service.branch_id,
      sermon_title: service.sermon_title || '',
      series_name: service.series_name || '',
      scripture_reference: service.scripture_reference || '',
      speaker: service.speaker || '',
      sermon_recording_url: service.sermon_recording_url || '',
      sermon_notes_url: service.sermon_notes_url || '',
      livestream_link: service.livestream_link || '',
      service_date: service.service_date.split('T')[0],
      start_time: service.start_time,
      end_time: service.end_time,
      status: service.status,
      expected_attendance: service.expected_attendance
    })
    setShowEditModal(true)
  }

  const resetForm = () => {
    setFormData({
      service_type: 'sunday_8am',
      branch_id: '',
      sermon_title: '',
      series_name: '',
      scripture_reference: '',
      speaker: '',
      sermon_recording_url: '',
      sermon_notes_url: '',
      livestream_link: '',
      service_date: '',
      start_time: '08:00',
      end_time: '10:30',
      status: 'upcoming',
      expected_attendance: null
    })
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
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  // Calendar helper functions
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startDayOfWeek = firstDay.getDay()

    return { daysInMonth, startDayOfWeek, year, month }
  }

  const getServicesForDate = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0]
    return services.filter(service => service.service_date.split('T')[0] === dateStr)
  }

  const previousMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))
  }

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))
  }

  const goToToday = () => {
    setCurrentMonth(new Date())
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Service Management</h1>
        <div className="flex gap-3">
          <button
            onClick={() => setShowRecurringModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <RefreshCw className="w-5 h-5" />
            Generate Recurring
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            <Plus className="w-5 h-5" />
            Create Service
          </button>
        </div>
      </div>

      {/* View Switcher */}
      <div className="flex justify-end gap-2 mb-4">
        <button
          onClick={() => setViewMode('list')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            viewMode === 'list'
              ? 'bg-purple-600 text-white'
              : 'bg-white text-gray-700 border hover:bg-gray-50'
          }`}
        >
          <List className="w-4 h-4" />
          List View
        </button>
        <button
          onClick={() => setViewMode('calendar')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            viewMode === 'calendar'
              ? 'bg-purple-600 text-white'
              : 'bg-white text-gray-700 border hover:bg-gray-50'
          }`}
        >
          <Calendar className="w-4 h-4" />
          Calendar View
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Branch</label>
            <select
              value={filterBranch}
              onChange={(e) => setFilterBranch(e.target.value)}
              className="w-full p-2 border rounded-lg"
            >
              <option value="">All Branches</option>
              {branches.map(branch => (
                <option key={branch.id} value={branch.id}>{branch.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Service Type</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full p-2 border rounded-lg"
            >
              <option value="">All Types</option>
              <option value="sunday_8am">Sunday 8:00 AM</option>
              <option value="sunday_10am">Sunday 10:00 AM</option>
              <option value="midweek">Midweek</option>
              <option value="special">Special</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full p-2 border rounded-lg"
            >
              <option value="">All Status</option>
              <option value="upcoming">Upcoming</option>
              <option value="ongoing">Ongoing</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => {
                setFilterBranch('')
                setFilterType('')
                setFilterStatus('')
              }}
              className="w-full px-4 py-2 text-gray-700 border rounded-lg hover:bg-gray-50"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* List View */}
      {viewMode === 'list' && (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gradient-to-r from-purple-50 to-blue-50 border-b-2 border-purple-200">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">
                Service
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">
                Date & Time
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">
                Speaker/Title
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">
                Attendance
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-4 text-right text-xs font-bold text-purple-900 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {services.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                  No services found. Create one to get started!
                </td>
              </tr>
            ) : (
              services.map(service => (
                <tr key={service.id} className="hover:bg-gradient-to-r hover:from-purple-50 hover:to-blue-50 transition-all duration-200 cursor-pointer group" onClick={() => navigate(`/services/${service.id}`)}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Calendar className="w-5 h-5 text-purple-600 mr-2" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {getServiceTypeLabel(service.service_type)}
                        </div>
                        {service.is_recurring && (
                          <div className="text-xs text-gray-500">Recurring</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{formatDate(service.service_date)}</div>
                    <div className="text-xs text-gray-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {service.start_time} - {service.end_time}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">{service.speaker || 'TBA'}</div>
                    <div className="text-xs text-gray-500">{service.sermon_title || 'No title'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-1 text-sm text-gray-900">
                      <Users className="w-4 h-4 text-gray-400" />
                      {service.actual_attendance}
                      {service.expected_attendance && ` / ${service.expected_attendance}`}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(service.status)}`}>
                      {service.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleEditClick(service)
                      }}
                      className="text-purple-600 hover:text-purple-900 mr-3"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteService(service.id)
                      }}
                      className="text-red-600 hover:text-red-900"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        </div>
      )}

      {/* Calendar View */}
      {viewMode === 'calendar' && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          {/* Calendar Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              {currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={goToToday}
                className="px-3 py-2 text-sm text-gray-700 border rounded-lg hover:bg-gray-50"
              >
                Today
              </button>
              <button
                onClick={previousMonth}
                className="p-2 text-gray-700 border rounded-lg hover:bg-gray-50"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={nextMonth}
                className="p-2 text-gray-700 border rounded-lg hover:bg-gray-50"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-1">
            {/* Day headers */}
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="text-center font-semibold text-gray-700 py-2 text-sm">
                {day}
              </div>
            ))}

            {/* Calendar days */}
            {(() => {
              const { daysInMonth, startDayOfWeek, year, month } = getDaysInMonth(currentMonth)
              const days = []

              // Empty cells for days before month starts
              for (let i = 0; i < startDayOfWeek; i++) {
                days.push(
                  <div key={`empty-${i}`} className="min-h-[120px] bg-gray-50 border border-gray-200" />
                )
              }

              // Actual calendar days
              for (let day = 1; day <= daysInMonth; day++) {
                const date = new Date(year, month, day)
                const dayServices = getServicesForDate(date)
                const isToday =
                  new Date().toISOString().split('T')[0] === date.toISOString().split('T')[0]

                days.push(
                  <div
                    key={day}
                    className={`min-h-[120px] border border-gray-200 p-2 ${
                      isToday ? 'bg-purple-50 border-purple-300' : 'bg-white hover:bg-gray-50'
                    }`}
                  >
                    <div className={`text-sm font-semibold mb-2 ${
                      isToday ? 'text-purple-600' : 'text-gray-700'
                    }`}>
                      {day}
                    </div>
                    <div className="space-y-1">
                      {dayServices.map(service => (
                        <div
                          key={service.id}
                          onClick={() => navigate(`/services/${service.id}`)}
                          className="text-xs p-1 rounded cursor-pointer bg-purple-100 hover:bg-purple-200 border-l-2 border-purple-600"
                        >
                          <div className="font-medium text-purple-900 truncate">
                            {getServiceTypeLabel(service.service_type)}
                          </div>
                          <div className="text-purple-700 truncate flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {service.start_time}
                          </div>
                          {service.speaker && (
                            <div className="text-purple-600 truncate">
                              {service.speaker}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )
              }

              return days
            })()}
          </div>

          {/* Calendar Legend */}
          <div className="mt-6 flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-purple-50 border border-purple-300"></div>
              <span className="text-gray-700">Today</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-purple-100 border-l-2 border-purple-600"></div>
              <span className="text-gray-700">Service</span>
            </div>
          </div>
        </div>
      )}

      {/* Create Service Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 my-8">
            <h2 className="text-2xl font-bold mb-4">Create Service</h2>
            <form onSubmit={handleCreateService} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Service Type</label>
                  <select
                    value={formData.service_type}
                    onChange={(e) => setFormData({ ...formData, service_type: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    required
                  >
                    <option value="sunday_8am">Sunday 8:00 AM</option>
                    <option value="sunday_10am">Sunday 10:00 AM</option>
                    <option value="midweek">Midweek Service</option>
                    <option value="special">Special Service</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Branch</label>
                  <select
                    value={formData.branch_id}
                    onChange={(e) => setFormData({ ...formData, branch_id: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    required
                  >
                    <option value="">Select branch</option>
                    {branches.map(branch => (
                      <option key={branch.id} value={branch.id}>{branch.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Service Date</label>
                  <input
                    type="date"
                    value={formData.service_date}
                    onChange={(e) => setFormData({ ...formData, service_date: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                  >
                    <option value="upcoming">Upcoming</option>
                    <option value="ongoing">Ongoing</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                  <input
                    type="time"
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">End Time</label>
                  <input
                    type="time"
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    required
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Speaker</label>
                  <input
                    type="text"
                    value={formData.speaker}
                    onChange={(e) => setFormData({ ...formData, speaker: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="Speaker name"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sermon Title</label>
                  <input
                    type="text"
                    value={formData.sermon_title}
                    onChange={(e) => setFormData({ ...formData, sermon_title: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="Sermon title"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Series Name</label>
                  <input
                    type="text"
                    value={formData.series_name}
                    onChange={(e) => setFormData({ ...formData, series_name: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="Series name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Scripture Reference</label>
                  <input
                    type="text"
                    value={formData.scripture_reference}
                    onChange={(e) => setFormData({ ...formData, scripture_reference: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="e.g., John 3:16"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Livestream Link</label>
                  <input
                    type="url"
                    value={formData.livestream_link}
                    onChange={(e) => setFormData({ ...formData, livestream_link: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="https://..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Expected Attendance</label>
                  <input
                    type="number"
                    value={formData.expected_attendance || ''}
                    onChange={(e) => setFormData({ ...formData, expected_attendance: e.target.value ? parseInt(e.target.value) : null })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="Optional"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false)
                    resetForm()
                  }}
                  className="px-4 py-2 text-gray-700 border rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                >
                  Create Service
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Service Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 my-8">
            <h2 className="text-2xl font-bold mb-4">Edit Service</h2>
            <form onSubmit={handleUpdateService} className="space-y-4">
              {/* Same form fields as create modal */}
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Speaker</label>
                  <input
                    type="text"
                    value={formData.speaker}
                    onChange={(e) => setFormData({ ...formData, speaker: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="Speaker name"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sermon Title</label>
                  <input
                    type="text"
                    value={formData.sermon_title}
                    onChange={(e) => setFormData({ ...formData, sermon_title: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="Sermon title"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Series Name</label>
                  <input
                    type="text"
                    value={formData.series_name}
                    onChange={(e) => setFormData({ ...formData, series_name: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="Series name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Scripture Reference</label>
                  <input
                    type="text"
                    value={formData.scripture_reference}
                    onChange={(e) => setFormData({ ...formData, scripture_reference: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="e.g., John 3:16"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sermon Recording URL</label>
                  <input
                    type="url"
                    value={formData.sermon_recording_url}
                    onChange={(e) => setFormData({ ...formData, sermon_recording_url: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="https://..."
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sermon Notes URL</label>
                  <input
                    type="url"
                    value={formData.sermon_notes_url}
                    onChange={(e) => setFormData({ ...formData, sermon_notes_url: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="https://..."
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Livestream Link</label>
                  <input
                    type="url"
                    value={formData.livestream_link}
                    onChange={(e) => setFormData({ ...formData, livestream_link: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                    placeholder="https://..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
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
                  onClick={() => {
                    setShowEditModal(false)
                    setEditingService(null)
                    resetForm()
                  }}
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
          </div>
        </div>
      )}

      {/* Generate Recurring Services Modal */}
      {showRecurringModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold mb-4">Generate Recurring Services</h2>
            <form onSubmit={handleGenerateRecurring} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Branch</label>
                <select
                  value={recurringFormData.branch_id}
                  onChange={(e) => setRecurringFormData({ ...recurringFormData, branch_id: e.target.value })}
                  className="w-full p-2 border rounded-lg"
                  required
                >
                  <option value="">Select branch</option>
                  {branches.map(branch => (
                    <option key={branch.id} value={branch.id}>{branch.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Weeks Ahead</label>
                <input
                  type="number"
                  value={recurringFormData.weeks_ahead}
                  onChange={(e) => setRecurringFormData({ ...recurringFormData, weeks_ahead: parseInt(e.target.value) })}
                  className="w-full p-2 border rounded-lg"
                  min="1"
                  max="52"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Will generate Sunday 8am, 10am, and Wednesday 7pm services
                </p>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowRecurringModal(false)}
                  className="px-4 py-2 text-gray-700 border rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Generate Services
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
