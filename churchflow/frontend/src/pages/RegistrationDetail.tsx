import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Edit, Trash2, User, Phone, Mail, MapPin, Bus, Calendar, CheckCircle, XCircle, QrCode, AlertCircle } from 'lucide-react'
import { getApiUrl } from '../config'
import { encodeHeaderValue } from '../lib/header-utils';

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
  qr_code?: string
  requires_bus: boolean
  bus_route_id?: string
  bus_route_name?: string
  pickup_location?: string
  special_needs?: string
  emergency_contact?: string
  checked_in: boolean
  checked_in_at?: string
  created_at: string
  status: string
  venue?: string
  venue_latitude?: number
  venue_longitude?: number
  venue_checkin_radius?: number
  self_checkin_enabled?: boolean
  conference_start_date?: string
  conference_end_date?: string
}

export default function RegistrationDetail() {
  const { registrationId } = useParams<{ registrationId: string }>()
  const navigate = useNavigate()

  const [registration, setRegistration] = useState<Registration | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isAdmin, setIsAdmin] = useState(false)

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false)
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

  // Delete modal state
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [deleteError, setDeleteError] = useState('')
  const [confirmText, setConfirmText] = useState('')

  useEffect(() => {
    checkAdminStatus()
    fetchRegistration()
  }, [registrationId])

  const checkAdminStatus = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setIsAdmin(false)
        return
      }

      const response = await fetch(getApiUrl('auth/me'), {
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

  const fetchRegistration = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const headers: any = {}

      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const orgId = localStorage.getItem('current_organization_id')
      if (orgId) {
        headers['X-Organization-ID'] = encodeHeaderValue(orgId) || ''
      }

      const response = await fetch(getApiUrl(`registrations/${registrationId}`), { headers })

      if (!response.ok) {
        throw new Error('Failed to load registration')
      }

      const data = await response.json()
      setRegistration(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load registration')
    } finally {
      setLoading(false)
    }
  }

  const handleEditClick = () => {
    if (!registration) return

    setEditFormData({
      user_name: registration.user_name,
      user_phone: registration.user_phone,
      user_email: registration.user_email || '',
      church_name: registration.church_name || registration.branch_name || '',
      special_needs: registration.special_needs || ''
    })
    setShowEditModal(true)
    setEditError('')
    setEditSuccess('')
  }

  const handleEditSave = async () => {
    if (!registration) return

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

      const response = await fetch(getApiUrl(`registrations/${registration.id}`), {
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

      const updatedData = await response.json()
      setRegistration(updatedData)
      setEditSuccess(`Successfully updated registration for ${editFormData.user_name}`)

      setTimeout(() => {
        setShowEditModal(false)
        setEditSuccess('')
      }, 1500)
    } catch (err: any) {
      setEditError(err.message || 'Failed to update registration')
    } finally {
      setEditLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!registration || confirmText !== 'DELETE') return

    setDeleteLoading(true)
    setDeleteError('')

    try {
      const token = localStorage.getItem('access_token')
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const orgId = localStorage.getItem('current_organization_id')
      if (orgId) {
        headers['X-Organization-ID'] = encodeHeaderValue(orgId) || ''
      }

      const response = await fetch(getApiUrl(`registrations/${registration.id}`), {
        method: 'DELETE',
        headers
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to delete registration')
      }

      // Navigate back to list after successful delete
      navigate('/registered-members')
    } catch (err: any) {
      setDeleteError(err.message || 'Failed to delete registration')
    } finally {
      setDeleteLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading registration details...</p>
        </div>
      </div>
    )
  }

  if (error || !registration) {
    return (
      <div className="max-w-2xl mx-auto p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle className="w-5 h-5" />
            <p>{error || 'Registration not found'}</p>
          </div>
          <button
            onClick={() => navigate('/registered-members')}
            className="mt-4 text-purple-600 hover:text-purple-700 font-medium"
          >
            ← Back to Registrations
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/registered-members')}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="hidden sm:inline">Back to Registrations</span>
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
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center text-2xl font-bold">
                {registration.user_name.charAt(0).toUpperCase()}
              </div>
              <div>
                <h1 className="text-2xl font-bold">{registration.user_name}</h1>
                <p className="text-purple-100 mt-1">{registration.conference_name}</p>
              </div>
            </div>

            {/* Status Badge */}
            <div className="mt-4 flex flex-wrap gap-2">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                registration.status === 'confirmed'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {registration.status}
              </span>
              {registration.checked_in && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  <CheckCircle className="w-4 h-4 mr-1" />
                  Checked In
                </span>
              )}
            </div>
          </div>

          {/* Registration Code & QR */}
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <p className="text-sm text-gray-600">Registration Code</p>
                <code className="text-lg font-mono font-bold text-gray-900">
                  {registration.registration_code}
                </code>
              </div>
              {registration.qr_code && (
                <div className="flex items-center gap-2">
                  <QrCode className="w-5 h-5 text-gray-600" />
                  <img
                    src={registration.qr_code}
                    alt="QR Code"
                    className="w-24 h-24 border-2 border-gray-300 rounded"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Contact Information */}
          <div className="px-6 py-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h2>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <Phone className="w-5 h-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-600">Phone Number</p>
                  <p className="font-medium text-gray-900">{registration.user_phone}</p>
                </div>
              </div>

              {registration.user_email && (
                <div className="flex items-start gap-3">
                  <Mail className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-600">Email Address</p>
                    <p className="font-medium text-gray-900">{registration.user_email}</p>
                  </div>
                </div>
              )}

              {(registration.branch_name || registration.church_name) && (
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-600">Branch/Church</p>
                    <p className="font-medium text-gray-900">
                      {registration.branch_name || registration.church_name}
                    </p>
                  </div>
                </div>
              )}

              {registration.emergency_contact && (
                <div className="flex items-start gap-3">
                  <Phone className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-600">Emergency Contact</p>
                    <p className="font-medium text-gray-900">{registration.emergency_contact}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Bus Transportation */}
          {registration.requires_bus && (
            <div className="px-6 py-6 bg-blue-50 border-t border-blue-100">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Bus className="w-5 h-5" />
                Bus Transportation
              </h2>
              <div className="space-y-2">
                {registration.bus_route_name && (
                  <div>
                    <p className="text-sm text-gray-600">Route</p>
                    <p className="font-medium text-gray-900">{registration.bus_route_name}</p>
                  </div>
                )}
                {registration.pickup_location && (
                  <div>
                    <p className="text-sm text-gray-600">Pickup Location</p>
                    <p className="font-medium text-gray-900">{registration.pickup_location}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Special Needs */}
          {registration.special_needs && (
            <div className="px-6 py-6 border-t border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Special Needs</h2>
              <p className="text-gray-700">{registration.special_needs}</p>
            </div>
          )}

          {/* Check-in Details */}
          <div className="px-6 py-6 border-t border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Registration Details</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Registered On</p>
                <p className="font-medium text-gray-900">
                  {new Date(registration.created_at).toLocaleString()}
                </p>
              </div>
              {registration.checked_in && registration.checked_in_at && (
                <div>
                  <p className="text-sm text-gray-600">Checked In At</p>
                  <p className="font-medium text-gray-900">
                    {new Date(registration.checked_in_at).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Conference Details */}
          {registration.venue && (
            <div className="px-6 py-6 bg-gray-50 border-t border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Conference Venue</h2>
              <div className="flex items-start gap-3">
                <MapPin className="w-5 h-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900">{registration.venue}</p>
                  {registration.conference_start_date && registration.conference_end_date && (
                    <p className="text-sm text-gray-600 mt-2">
                      {new Date(registration.conference_start_date).toLocaleDateString()} - {new Date(registration.conference_end_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
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

      {/* Delete Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
          <div className="bg-white rounded-t-2xl sm:rounded-lg shadow-xl max-w-md w-full p-4 sm:p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Delete Registration</h3>
                <p className="text-sm text-gray-600">This action cannot be undone</p>
              </div>
            </div>

            <div className="mb-4">
              <p className="text-gray-700 mb-3">
                Are you sure you want to permanently delete this registration?
              </p>
              <div className="bg-gray-50 p-3 rounded-lg mb-3">
                <p className="font-semibold text-gray-900">{registration.user_name}</p>
                <p className="text-sm text-gray-600">{registration.user_phone}</p>
                <p className="text-xs text-gray-500 mt-1">Code: {registration.registration_code}</p>
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
                {deleteLoading ? 'Deleting...' : 'Delete Registration'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
