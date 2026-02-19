import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Download, Filter, Users as UsersIcon, Phone, Mail, Calendar, CheckCircle, XCircle, MapPin, Bus, Trash2, AlertTriangle, Edit } from 'lucide-react'
import { getApiUrl } from '../config'
import { encodeHeaderValue } from '../lib/header-utils';

interface Conference {
  id: string
  name: string
}

interface RegistrationStats {
  total: number
  confirmed: number
  pending: number
  cancelled: number
  checked_in: number
  requires_bus: number
}

interface Registration {
  id: string
  conference_id: string
  conference_name: string
  user_phone: string
  user_name: string
  user_email?: string
  branch_id?: string
  branch_name?: string
  church_name?: string
  registration_code: string
  requires_bus: boolean
  bus_route_id?: string
  bus_route_name?: string
  special_needs?: string
  emergency_contact?: string
  checked_in: boolean
  checked_in_at?: string
  created_at: string
  status: string
}

interface RegisteredMembersProps {
  initialCheckedInFilter?: string
  /** Optional conference to force-filter by (used in conference detail view). */
  conferenceId?: string
}

export default function RegisteredMembers({
  initialCheckedInFilter = 'all',
  conferenceId
}: RegisteredMembersProps) {
  const navigate = useNavigate()
  const [registrations, setRegistrations] = useState<Registration[]>([])
  const [conferences, setConferences] = useState<Conference[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('')
  const [filterConference, setFilterConference] = useState<string>(conferenceId || 'all')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterCheckedIn, setFilterCheckedIn] = useState<string>(initialCheckedInFilter)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')
  const [deleteSuccess, setDeleteSuccess] = useState('')
  const [isAdmin, setIsAdmin] = useState(false)
  const [selectedRegistration, setSelectedRegistration] = useState<Registration | null>(null)
  const [showIndividualDeleteModal, setShowIndividualDeleteModal] = useState(false)
  const [individualConfirmText, setIndividualConfirmText] = useState('')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [showBulkDeleteModal, setShowBulkDeleteModal] = useState(false)
  const [bulkConfirmText, setBulkConfirmText] = useState('')
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [total, setTotal] = useState(0)
  const [serverStats, setServerStats] = useState<RegistrationStats | null>(null)
  const LIMIT = 50

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingRegistration, setEditingRegistration] = useState<Registration | null>(null)
  const [editFormData, setEditFormData] = useState({
    user_name: '',
    user_phone: '',
    user_email: '',
    church_name: '',
    special_needs: ''
  })
  const [editLoading, setEditLoading] = useState(false)
  const [editError, setEditError] = useState('')
  const [editSuccess, setEditSuccess] = useState('')

  // Debounce search query to avoid excessive API calls
  // Reason: Only trigger search after user stops typing for 400ms
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery)
    }, 400)

    return () => clearTimeout(timer)
  }, [searchQuery])

  useEffect(() => {
    // Reset and fetch from beginning when filters change
    setOffset(0)
    setRegistrations([])
    setHasMore(true)
    fetchData(0)
    checkAdminRole()
  }, [filterConference, filterStatus, filterCheckedIn, debouncedSearchQuery])

  // Update filter when prop changes (e.g., navigating from dashboard)
  useEffect(() => {
    setFilterCheckedIn(initialCheckedInFilter)
  }, [initialCheckedInFilter])

  // When a conferenceId prop is provided (e.g., from ConferenceDetail),
  // keep the conference filter locked to that ID.
  useEffect(() => {
    if (conferenceId) {
      setFilterConference(conferenceId)
    }
  }, [conferenceId])

  const checkAdminRole = async () => {
    try {
      const token = localStorage.getItem('access_token')
      console.log('🔑 Token exists:', !!token)
      if (!token) {
        console.log('❌ No token found, user not logged in')
        return
      }

      console.log('📡 Fetching user data from /api/v1/users/me...')
      const response = await fetch(getApiUrl('users/me'), {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      console.log('📥 Response status:', response.status)
      if (response.ok) {
        const userData = await response.json()
        console.log('👤 User data:', userData)
        console.log('🔐 User roles:', userData.roles)
        // Check for both admin and universal_admin roles
        const isAdminUser = userData.roles && (userData.roles.includes('admin') || userData.roles.includes('universal_admin'))
        console.log('✅ Is Admin or Universal Admin?', isAdminUser)
        setIsAdmin(isAdminUser)
      } else {
        console.error('❌ Failed to fetch user data:', response.status, response.statusText)
      }
    } catch (err) {
      console.error('❌ Failed to check admin role:', err)
    }
  }

  const fetchData = async (currentOffset: number = offset, append: boolean = false) => {
    try {
      if (append) {
        setLoadingMore(true)
      } else {
        setLoading(true)
      }

      const token = localStorage.getItem('access_token')
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      // Fetch conferences only on initial load
      if (!append) {
        const confsResponse = await fetch(getApiUrl('conferences'), { headers })
        if (confsResponse.ok) {
          const confsData = await confsResponse.json()
          setConferences(confsData)
        }
      }

      // Build URL with pagination and filters
      const params = new URLSearchParams({
        limit: LIMIT.toString(),
        offset: currentOffset.toString()
      })

      if (filterConference !== 'all') {
        params.append('conference_id', filterConference)
      }

      if (filterStatus !== 'all') {
        params.append('status', filterStatus)
      }

      if (filterCheckedIn === 'checked_in') {
        params.append('checked_in', 'true')
      } else if (filterCheckedIn === 'not_checked_in') {
        params.append('checked_in', 'false')
      }

      if (debouncedSearchQuery) {
        params.append('search', debouncedSearchQuery)
      }

      const url = getApiUrl(`registrations?${params.toString()}`)

      const response = await fetch(url, { headers })
      if (response.ok) {
        const data = await response.json()

        // Update registrations (append or replace)
        if (append) {
          setRegistrations(prev => [...prev, ...data.items])
        } else {
          setRegistrations(data.items)
        }

        // Update pagination state
        setTotal(data.total)
        setHasMore(data.items.length === LIMIT && (currentOffset + LIMIT) < data.total)
        setOffset(currentOffset + data.items.length)

        // Store server-provided aggregate stats (only on initial load, not when appending)
        if (!append && data.stats) {
          setServerStats(data.stats)
        }
      }
    } catch (err) {
      console.error('Failed to fetch registrations:', err)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  const loadMore = () => {
    if (!loadingMore && hasMore) {
      fetchData(offset, true)
    }
  }

  // No client-side filtering needed - all filtering is done server-side
  const filteredRegistrations = registrations

  // Use server-provided aggregate stats for accurate counts across all registrations
  const stats = {
    total: serverStats?.total ?? total,
    confirmed: serverStats?.confirmed ?? 0,
    checkedIn: serverStats?.checked_in ?? 0,
    requiresBus: serverStats?.requires_bus ?? 0,
  }

  const exportToCSV = async () => {
    try {
      // Show loading state
      setLoading(true)

      const token = localStorage.getItem('access_token')
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      // Build URL with filters to export ALL matching registrations
      const params = new URLSearchParams()
      if (filterConference !== 'all') {
        params.append('conference_id', filterConference)
      }
      if (filterStatus !== 'all') {
        params.append('status', filterStatus)
      }
      if (filterCheckedIn === 'checked_in') {
        params.append('checked_in', 'true')
      } else if (filterCheckedIn === 'not_checked_in') {
        params.append('checked_in', 'false')
      }
      if (searchQuery) {
        params.append('search', searchQuery)
      }

      const url = getApiUrl(`registrations/export?${params.toString()}`)
      const response = await fetch(url, { headers })

      if (!response.ok) {
        throw new Error('Failed to fetch registrations for export')
      }

      const filteredData: Registration[] = await response.json()

      // Generate CSV
      const csvHeaders = ['Registration Code', 'Name', 'Phone', 'Email', 'Conference', 'Branch', 'Bus Route', 'Checked In', 'Status', 'Registered Date']
      const rows = filteredData.map(reg => [
        reg.registration_code,
        reg.user_name,
        reg.user_phone,
        reg.user_email || '',
        reg.conference_name,
        reg.branch_name || reg.church_name || '',
        reg.bus_route_name || '',
        reg.checked_in ? 'Yes' : 'No',
        reg.status,
        new Date(reg.created_at).toLocaleString()
      ])

      const csv = [csvHeaders, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `registrations_${new Date().toISOString().split('T')[0]}.csv`
      a.click()
      window.URL.revokeObjectURL(downloadUrl)

      // Show success message
      alert(`Exported ${filteredData.length} registrations to CSV`)
    } catch (err) {
      console.error('Failed to export registrations:', err)
      alert('Failed to export registrations. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteSingle = async () => {
    if (individualConfirmText !== 'DELETE') {
      setDeleteError('Please type DELETE to confirm')
      return
    }

    if (!selectedRegistration) {
      setDeleteError('No registration selected')
      return
    }

    setDeleting(true)
    setDeleteError('')
    setDeleteSuccess('')

    try {
      const token = localStorage.getItem('access_token')
      const headers: any = { 'Content-Type': 'application/json' }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(getApiUrl(`registrations/${selectedRegistration.id}`), {
        method: 'DELETE',
        headers
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to delete registration')
      }

      setDeleteSuccess(`Successfully deleted registration for ${selectedRegistration.user_name}`)
      setShowIndividualDeleteModal(false)
      setIndividualConfirmText('')
      setSelectedRegistration(null)

      // Refresh data from beginning
      setOffset(0)
      setRegistrations([])
      setHasMore(true)
      await fetchData(0)
    } catch (err: any) {
      setDeleteError(err.message || 'Failed to delete registration')
    } finally {
      setDeleting(false)
    }
  }

  const handleBulkDelete = async () => {
    if (bulkConfirmText !== 'DELETE') {
      setDeleteError('Please type DELETE to confirm')
      return
    }

    if (selectedIds.size === 0) {
      setDeleteError('No registrations selected')
      return
    }

    setDeleting(true)
    setDeleteError('')
    setDeleteSuccess('')

    try {
      const token = localStorage.getItem('access_token')
      const headers: any = { 'Content-Type': 'application/json' }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(getApiUrl('registrations/bulk-delete/selected'), {
        method: 'POST',
        headers,
        body: JSON.stringify({ registration_ids: Array.from(selectedIds) })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to delete selected registrations')
      }

      const data = await response.json()
      setDeleteSuccess(`Successfully deleted ${data.deleted_count} registration(s)`)
      setShowBulkDeleteModal(false)
      setBulkConfirmText('')
      setSelectedIds(new Set())

      // Refresh data from beginning
      setOffset(0)
      setRegistrations([])
      setHasMore(true)
      await fetchData(0)
    } catch (err: any) {
      setDeleteError(err.message || 'Failed to delete selected registrations')
    } finally {
      setDeleting(false)
    }
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === filteredRegistrations.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(filteredRegistrations.map(r => r.id)))
    }
  }

  const toggleSelectOne = (id: string) => {
    const newSet = new Set(selectedIds)
    if (newSet.has(id)) {
      newSet.delete(id)
    } else {
      newSet.add(id)
    }
    setSelectedIds(newSet)
  }

  // Handle edit registration
  const handleEditClick = (reg: Registration) => {
    setEditingRegistration(reg)
    setEditFormData({
      user_name: reg.user_name,
      user_phone: reg.user_phone,
      user_email: reg.user_email || '',
      church_name: reg.church_name || reg.branch_name || '',
      special_needs: reg.special_needs || ''
    })
    setShowEditModal(true)
    setEditError('')
    setEditSuccess('')
  }

  const handleEditSave = async () => {
    if (!editingRegistration) return

    setEditLoading(true)
    setEditError('')
    setEditSuccess('')

    try {
      const token = localStorage.getItem('access_token')
      const headers: any = { 'Content-Type': 'application/json' }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const orgId = localStorage.getItem('current_organization_id')
      if (orgId) {
        headers['X-Organization-ID'] = encodeHeaderValue(orgId) || ''
      }

      const response = await fetch(getApiUrl(`registrations/${editingRegistration.id}`), {
        method: 'PUT',
        headers,
        body: JSON.stringify({
          user_name: editFormData.user_name,
          user_phone: editFormData.user_phone,
          user_email: editFormData.user_email || null,
          church_name: editFormData.church_name || null,
          special_needs: editFormData.special_needs || null
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to update registration')
      }

      setEditSuccess(`Successfully updated registration for ${editFormData.user_name}`)

      // Refresh data from beginning
      setOffset(0)
      setRegistrations([])
      setHasMore(true)
      await fetchData(0)

      // Close modal after short delay
      setTimeout(() => {
        setShowEditModal(false)
        setEditingRegistration(null)
        setEditSuccess('')
      }, 1500)
    } catch (err: any) {
      setEditError(err.message || 'Failed to update registration')
    } finally {
      setEditLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading registrations...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Success/Error Notifications */}
      {deleteSuccess && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-center justify-between">
          <span>{deleteSuccess}</span>
          <button onClick={() => setDeleteSuccess('')} className="text-green-700 hover:text-green-900">
            <XCircle className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Conference Registrations</h1>
          <p className="text-sm sm:text-base text-gray-600 mt-1">View and manage all conference registrations</p>
          {isAdmin && selectedIds.size > 0 && (
            <p className="text-purple-600 mt-1 font-medium">
              {selectedIds.size} registration(s) selected
            </p>
          )}
        </div>
        <div className="flex gap-2 sm:gap-3">
          {isAdmin && selectedIds.size > 0 && (
            <button
              onClick={() => {
                setShowBulkDeleteModal(true)
                setDeleteError('')
                setBulkConfirmText('')
              }}
              className="flex items-center gap-2 bg-orange-600 hover:bg-orange-700 text-white px-3 sm:px-4 py-2 min-h-[44px] rounded-lg transition-colors font-medium shadow-md touch-manipulation"
            >
              <Trash2 className="w-4 h-4 sm:w-5 sm:h-5" />
              <span className="hidden sm:inline">Delete Selected ({selectedIds.size})</span>
              <span className="sm:hidden">Delete ({selectedIds.size})</span>
            </button>
          )}
          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-3 sm:px-4 py-2 min-h-[44px] rounded-lg transition-colors touch-manipulation"
          >
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Export CSV</span>
            <span className="sm:hidden">Export</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-500 text-sm font-medium">Total Registrations</p>
            <UsersIcon className="w-5 h-5 text-purple-600" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-500 text-sm font-medium">Confirmed</p>
            <CheckCircle className="w-5 h-5 text-green-600" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{stats.confirmed}</p>
          <p className="text-sm text-gray-500 mt-1">
            {stats.total > 0 ? Math.round((stats.confirmed / stats.total) * 100) : 0}% of total
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-500 text-sm font-medium">Checked In</p>
            <Calendar className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{stats.checkedIn}</p>
          <p className="text-sm text-gray-500 mt-1">
            {stats.total > 0 ? Math.round((stats.checkedIn / stats.total) * 100) : 0}% arrived
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-500 text-sm font-medium">Requires Bus</p>
            <Bus className="w-5 h-5 text-orange-600" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{stats.requiresBus}</p>
          <p className="text-sm text-gray-500 mt-1">Transportation needed</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-3 sm:p-4 rounded-lg shadow border border-gray-200">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
          {/* Search */}
          <div className="relative sm:col-span-2 md:col-span-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name, phone, code..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 sm:pl-10 pr-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          {/* Conference Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-gray-400 pointer-events-none" />
            <select
              value={filterConference}
              onChange={(e) => {
                if (conferenceId) return
                setFilterConference(e.target.value)
              }}
              disabled={!!conferenceId}
              className="w-full pl-9 sm:pl-10 pr-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none bg-white"
            >
              <option value="all">All Conferences</option>
              {conferences.map(conf => (
                <option key={conf.id} value={conf.id}>{conf.name}</option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none bg-white"
            >
              <option value="all">All Status</option>
              <option value="confirmed">Confirmed</option>
              <option value="pending">Pending</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          {/* Checked In Filter */}
          <div>
            <select
              value={filterCheckedIn}
              onChange={(e) => setFilterCheckedIn(e.target.value)}
              className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none bg-white"
            >
              <option value="all">All Check-ins</option>
              <option value="checked_in">Checked In</option>
              <option value="not_checked_in">Not Checked In</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-600">
        Showing {registrations.length} of {total} registrations
      </div>

      {/* Registrations Table */}
      <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
        {/* Desktop Table View */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-purple-50 to-blue-50 border-b-2 border-purple-200">
              <tr>
                {isAdmin && (
                  <th className="px-6 py-4 text-left">
                    <input
                      type="checkbox"
                      checked={filteredRegistrations.length > 0 && selectedIds.size === filteredRegistrations.length}
                      onChange={toggleSelectAll}
                      className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                      title="Select all"
                    />
                  </th>
                )}
                <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Reg. Code</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Name</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Contact</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Conference</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Branch</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Transport</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Registered</th>
                {isAdmin && (
                  <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">Actions</th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {filteredRegistrations.length === 0 ? (
                <tr>
                  <td colSpan={isAdmin ? 10 : 8} className="px-6 py-12 text-center text-gray-500">
                    No registrations found matching your filters
                  </td>
                </tr>
              ) : (
                filteredRegistrations.map((reg) => (
                  <tr
                    key={reg.id}
                    className={`hover:bg-gradient-to-r hover:from-purple-50 hover:to-blue-50 transition-all duration-200 cursor-pointer group ${selectedIds.has(reg.id) ? 'bg-purple-50' : ''}`}
                    onClick={() => navigate(`/registered-users/${reg.id}`)}
                  >
                    {isAdmin && (
                      <td className="px-6 py-4 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={selectedIds.has(reg.id)}
                          onChange={() => toggleSelectOne(reg.id)}
                          className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                        />
                      </td>
                    )}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <code className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                        {reg.registration_code}
                      </code>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                          <span className="text-purple-700 font-semibold text-sm">
                            {reg.user_name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div className="text-sm font-medium text-gray-900">{reg.user_name}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 flex items-center gap-1">
                        <Phone className="w-3 h-3 text-gray-400" />
                        {reg.user_phone}
                      </div>
                      {reg.user_email && (
                        <div className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                          <Mail className="w-3 h-3 text-gray-400" />
                          {reg.user_email}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{reg.conference_name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {reg.branch_name || reg.church_name ? (
                        <div className="text-sm text-gray-900 flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-gray-400" />
                          {reg.branch_name || reg.church_name}
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {reg.requires_bus ? (
                        <div className="text-sm text-gray-900">
                          <div className="flex items-center gap-1">
                            <Bus className="w-3 h-3 text-orange-600" />
                            <span className="text-xs">{reg.bus_route_name || 'Yes'}</span>
                          </div>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">No</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col gap-1">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            reg.status === 'confirmed'
                              ? 'bg-green-100 text-green-800'
                              : reg.status === 'pending'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {reg.status}
                        </span>
                        {reg.checked_in && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Checked In
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(reg.created_at).toLocaleDateString()}
                    </td>
                    {isAdmin && (
                      <td className="px-6 py-4 whitespace-nowrap text-sm" onClick={(e) => e.stopPropagation()}>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditClick(reg)}
                            className="bg-blue-600 hover:bg-blue-700 text-white transition-colors p-3 rounded-lg shadow-md border-2 border-blue-800 font-bold"
                            title="Edit this registration"
                          >
                            <Edit className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => {
                              setSelectedRegistration(reg)
                              setShowIndividualDeleteModal(true)
                              setDeleteError('')
                              setIndividualConfirmText('')
                            }}
                            className="bg-red-600 hover:bg-red-700 text-white transition-colors p-3 rounded-lg shadow-md border-2 border-red-800 font-bold"
                            title="Delete this registration"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile Card View */}
        <div className="md:hidden">
          {filteredRegistrations.length === 0 ? (
            <div className="px-4 py-12 text-center text-gray-500">
              No registrations found matching your filters
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {filteredRegistrations.map((reg) => (
                <div
                  key={reg.id}
                  className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${selectedIds.has(reg.id) ? 'bg-purple-50' : ''}`}
                  onClick={() => navigate(`/registered-users/${reg.id}`)}
                >
                  {/* Header Row with Checkbox and Name */}
                  <div className="flex items-start gap-3 mb-3">
                    {isAdmin && (
                      <input
                        type="checkbox"
                        checked={selectedIds.has(reg.id)}
                        onChange={() => toggleSelectOne(reg.id)}
                        onClick={(e) => e.stopPropagation()}
                        className="mt-1 w-5 h-5 text-purple-600 rounded focus:ring-purple-500 touch-manipulation"
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-purple-700 font-semibold text-xs">
                            {reg.user_name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div className="min-w-0">
                          <div className="text-sm font-semibold text-gray-900 truncate">{reg.user_name}</div>
                          <code className="text-xs font-mono bg-gray-100 px-1.5 py-0.5 rounded">
                            {reg.registration_code}
                          </code>
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col gap-1 items-end">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          reg.status === 'confirmed'
                            ? 'bg-green-100 text-green-800'
                            : reg.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {reg.status}
                      </span>
                      {reg.checked_in && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          <CheckCircle className="w-3 h-3 mr-0.5" />
                          Checked In
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Contact Info */}
                  <div className="space-y-2 mb-3 text-sm">
                    <div className="flex items-center gap-2 text-gray-700">
                      <Phone className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                      <span>{reg.user_phone}</span>
                    </div>
                    {reg.user_email && (
                      <div className="flex items-center gap-2 text-gray-700">
                        <Mail className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                        <span className="truncate">{reg.user_email}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-gray-700">
                      <Calendar className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                      <span className="text-xs">{reg.conference_name}</span>
                    </div>
                    {(reg.branch_name || reg.church_name) && (
                      <div className="flex items-center gap-2 text-gray-700">
                        <MapPin className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                        <span className="text-xs">{reg.branch_name || reg.church_name}</span>
                      </div>
                    )}
                    {reg.requires_bus && (
                      <div className="flex items-center gap-2 text-gray-700">
                        <Bus className="w-3.5 h-3.5 text-orange-600 flex-shrink-0" />
                        <span className="text-xs">{reg.bus_route_name || 'Bus required'}</span>
                      </div>
                    )}
                  </div>

                  {/* Footer with Date and Action Buttons */}
                  <div className="flex items-center justify-between pt-3 border-t border-gray-200">
                    <span className="text-xs text-gray-500">
                      Registered {new Date(reg.created_at).toLocaleDateString()}
                    </span>
                    {isAdmin && (
                      <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => handleEditClick(reg)}
                          className="bg-blue-600 hover:bg-blue-700 text-white transition-colors p-2 min-h-[44px] min-w-[44px] rounded-lg shadow-md border-2 border-blue-800 font-bold touch-manipulation"
                          title="Edit this registration"
                        >
                          <Edit className="w-4 h-4 mx-auto" />
                        </button>
                        <button
                          onClick={() => {
                            setSelectedRegistration(reg)
                            setShowIndividualDeleteModal(true)
                            setDeleteError('')
                            setIndividualConfirmText('')
                          }}
                          className="bg-red-600 hover:bg-red-700 text-white transition-colors p-2 min-h-[44px] min-w-[44px] rounded-lg shadow-md border-2 border-red-800 font-bold touch-manipulation"
                          title="Delete this registration"
                        >
                          <Trash2 className="w-4 h-4 mx-auto" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Load More Button */}
        {hasMore && !loading && (
          <div className="p-4 sm:p-6 border-t border-gray-200 bg-gray-50">
            <button
              onClick={loadMore}
              disabled={loadingMore}
              className="w-full px-6 py-3 min-h-[48px] bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium touch-manipulation"
            >
              {loadingMore ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Loading more...
                </span>
              ) : (
                `Load More (${total - registrations.length} remaining)`
              )}
            </button>
          </div>
        )}

        {/* End of results indicator */}
        {!hasMore && registrations.length > 0 && (
          <div className="p-4 text-center text-gray-500 border-t border-gray-200 bg-gray-50">
            <p className="text-sm">You've reached the end of the list ({total} total registrations)</p>
          </div>
        )}
      </div>

      {/* Individual Delete Modal */}
      {showIndividualDeleteModal && selectedRegistration && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4" onClick={() => {
          setShowIndividualDeleteModal(false)
          setIndividualConfirmText('')
          setDeleteError('')
          setSelectedRegistration(null)
        }}>
          <div className="bg-white rounded-t-2xl sm:rounded-lg shadow-xl max-w-md w-full p-4 sm:p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Delete Registration</h3>
                <p className="text-sm text-gray-600">This action cannot be undone</p>
              </div>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-700 mb-2">
                Are you sure you want to permanently delete the registration for:
              </p>
              <div className="bg-gray-50 p-3 rounded-lg mb-3">
                <p className="font-semibold text-gray-900">{selectedRegistration.user_name}</p>
                <p className="text-sm text-gray-600">{selectedRegistration.user_phone}</p>
                <p className="text-xs text-gray-500 mt-1">Code: {selectedRegistration.registration_code}</p>
              </div>
              <p className="text-sm text-gray-700 mb-3">
                Type <strong>DELETE</strong> to confirm:
              </p>
              <input
                type="text"
                value={individualConfirmText}
                onChange={(e) => setIndividualConfirmText(e.target.value)}
                className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="Type DELETE"
                disabled={deleting}
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
                  setShowIndividualDeleteModal(false)
                  setIndividualConfirmText('')
                  setDeleteError('')
                  setSelectedRegistration(null)
                }}
                className="flex-1 px-4 py-2 min-h-[44px] border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors touch-manipulation"
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteSingle}
                disabled={deleting || individualConfirmText !== 'DELETE'}
                className="flex-1 px-4 py-2 min-h-[44px] bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Delete Selected Modal */}
      {showBulkDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4" onClick={() => {
          setShowBulkDeleteModal(false)
          setBulkConfirmText('')
          setDeleteError('')
        }}>
          <div className="bg-white rounded-t-2xl sm:rounded-lg shadow-xl max-w-md w-full p-4 sm:p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-orange-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Delete Selected Registrations</h3>
                <p className="text-sm text-gray-600">This action cannot be undone</p>
              </div>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-700 mb-3">
                This will permanently delete <strong>{selectedIds.size}</strong> selected registration(s).
              </p>
              <p className="text-sm text-gray-700 mb-3">
                Type <strong>DELETE</strong> to confirm:
              </p>
              <input
                type="text"
                value={bulkConfirmText}
                onChange={(e) => setBulkConfirmText(e.target.value)}
                className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                placeholder="Type DELETE"
                disabled={deleting}
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
                  setShowBulkDeleteModal(false)
                  setBulkConfirmText('')
                  setDeleteError('')
                }}
                className="flex-1 px-4 py-2 min-h-[44px] border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors touch-manipulation"
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={deleting || bulkConfirmText !== 'DELETE'}
                className="flex-1 px-4 py-2 min-h-[44px] bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
              >
                {deleting ? 'Deleting...' : `Delete ${selectedIds.size} Registration(s)`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Registration Modal */}
      {showEditModal && editingRegistration && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4" onClick={() => {
          if (!editLoading) {
            setShowEditModal(false)
            setEditingRegistration(null)
            setEditError('')
            setEditSuccess('')
          }
        }}>
          <div className="bg-white rounded-t-2xl sm:rounded-lg shadow-xl max-w-md w-full p-4 sm:p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                <Edit className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Edit Registration</h3>
                <p className="text-sm text-gray-600">Update attendee information</p>
              </div>
            </div>

            <div className="space-y-4 mb-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={editFormData.user_name}
                  onChange={(e) => setEditFormData({ ...editFormData, user_name: e.target.value })}
                  className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={editLoading}
                />
              </div>

              {/* Phone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="tel"
                  value={editFormData.user_phone}
                  onChange={(e) => setEditFormData({ ...editFormData, user_phone: e.target.value })}
                  className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={editLoading}
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email (optional)</label>
                <input
                  type="email"
                  value={editFormData.user_email}
                  onChange={(e) => setEditFormData({ ...editFormData, user_email: e.target.value })}
                  className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={editLoading}
                  placeholder="email@example.com"
                />
              </div>

              {/* Church/Branch */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Church/Branch (optional)</label>
                <input
                  type="text"
                  value={editFormData.church_name}
                  onChange={(e) => setEditFormData({ ...editFormData, church_name: e.target.value })}
                  className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={editLoading}
                />
              </div>

              {/* Special Needs */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Special Needs (optional)</label>
                <textarea
                  value={editFormData.special_needs}
                  onChange={(e) => setEditFormData({ ...editFormData, special_needs: e.target.value })}
                  className="w-full px-4 py-2 text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={editLoading}
                  rows={3}
                />
              </div>
            </div>

            {editError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {editError}
              </div>
            )}

            {editSuccess && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
                {editSuccess}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setEditingRegistration(null)
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
                disabled={editLoading || !editFormData.user_name || !editFormData.user_phone}
                className="flex-1 px-4 py-2 min-h-[44px] bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
              >
                {editLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
