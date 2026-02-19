import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Users, MapPin } from 'lucide-react'
import ConfirmDialog from '../components/ConfirmDialog'

interface BusRoute {
  id: string
  conference_id: string
  name?: string
  route_name?: string
  pickup_location: string
  departure_time?: string | null
  capacity?: number
  registered_count: number
  status: string
  gate_number?: string | null
}

export default function BusManagement() {
  const [routes, setRoutes] = useState<BusRoute[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingRoute, setEditingRoute] = useState<BusRoute | null>(null)
  const [formData, setFormData] = useState({
    conference_id: '676152636e3d31f15c01caf2',
    route_name: '',
    pickup_location: ''
  })
  const [editFormData, setEditFormData] = useState({
    route_name: '',
    pickup_location: '',
    status: 'active'
  })
  // Delete confirmation dialog state
  const [deleteDialog, setDeleteDialog] = useState<{
    isOpen: boolean;
    routeId: string | null;
    routeName: string;
    isLoading: boolean;
  }>({ isOpen: false, routeId: null, routeName: '', isLoading: false })

  useEffect(() => {
    fetchRoutes()
  }, [])

  const fetchRoutes = async () => {
    const token = localStorage.getItem('access_token')

    try {
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('/api/v1/buses/routes', {
        headers
      })

      if (response.ok) {
        const data = await response.json()
        console.log('=== FETCHED ROUTES DEBUG ===')
        console.log('Number of routes:', data.length)
        console.log('First route sample:', data[0])
        console.log('First route ID:', data[0]?.id)
        setRoutes(data)
      }
    } catch (err) {
      console.error('Failed to fetch routes:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateRoute = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem('access_token')

    if (!token) {
      alert('Please login to create routes')
      return
    }

    try {
      const response = await fetch('/api/v1/buses/routes', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        setShowCreateModal(false)
        setFormData({
          conference_id: '676152636e3d31f15c01caf2',
          route_name: '',
          pickup_location: ''
        })
        fetchRoutes()
      } else if (response.status === 401) {
        alert('Session expired. Please login again.')
      } else if (response.status === 403) {
        alert('Access denied. Only administrators and coordinators can create bus routes.')
      } else if (response.status === 404) {
        alert('User profile not found. Please complete your profile or contact support.')
      } else {
        alert('Failed to create route. Please try again.')
      }
    } catch (err) {
      console.error('Failed to create route:', err)
      alert('Failed to create route. Please try again.')
    }
  }

  // Open delete confirmation dialog
  const openDeleteDialog = (route: BusRoute) => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      alert('Please login to delete routes')
      return
    }

    // Validate route ID
    if (!route.id || route.id === 'undefined' || route.id === 'null' || route.id === 'None') {
      alert('Invalid route ID. Please refresh the page and try again.')
      return
    }

    setDeleteDialog({
      isOpen: true,
      routeId: route.id,
      routeName: route.name || route.route_name || route.pickup_location,
      isLoading: false,
    })
  }

  // Handle confirmed delete
  const handleDeleteRoute = async () => {
    if (!deleteDialog.routeId) return

    const token = localStorage.getItem('access_token')
    if (!token) return

    setDeleteDialog(prev => ({ ...prev, isLoading: true }))

    try {
      const response = await fetch(`/api/v1/buses/routes/${deleteDialog.routeId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        setDeleteDialog({ isOpen: false, routeId: null, routeName: '', isLoading: false })
        fetchRoutes()
      } else if (response.status === 401) {
        alert('Session expired. Please login again.')
        setDeleteDialog(prev => ({ ...prev, isLoading: false }))
      } else if (response.status === 403) {
        alert('Access denied. Only administrators can delete bus routes.')
        setDeleteDialog(prev => ({ ...prev, isLoading: false }))
      } else if (response.status === 404) {
        alert('Bus route not found.')
        setDeleteDialog(prev => ({ ...prev, isLoading: false }))
      } else {
        alert('Failed to delete route. Please try again.')
        setDeleteDialog(prev => ({ ...prev, isLoading: false }))
      }
    } catch (err) {
      console.error('Failed to delete route:', err)
      alert('Failed to delete route. Please try again.')
      setDeleteDialog(prev => ({ ...prev, isLoading: false }))
    }
  }

  const handleEditClick = (route: BusRoute) => {
    setEditingRoute(route)
    setEditFormData({
      route_name: route.route_name || route.name || '',
      pickup_location: route.pickup_location,
      status: route.status
    })
    setShowEditModal(true)
  }

  const handleUpdateRoute = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem('access_token')

    if (!token || !editingRoute) {
      alert('Please login to update routes')
      return
    }

    try {
      const response = await fetch(`/api/v1/buses/routes/${editingRoute.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editFormData)
      })

      if (response.ok) {
        setShowEditModal(false)
        setEditingRoute(null)
        setEditFormData({
          route_name: '',
          pickup_location: '',
          status: 'active'
        })
        fetchRoutes()
      } else if (response.status === 401) {
        alert('Session expired. Please login again.')
      } else if (response.status === 403) {
        alert('Access denied. Only administrators and coordinators can edit bus routes.')
      } else if (response.status === 404) {
        alert('Bus route not found.')
      } else {
        alert('Failed to update route. Please try again.')
      }
    } catch (err) {
      console.error('Failed to update route:', err)
      alert('Failed to update route. Please try again.')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-700'
      case 'full': return 'bg-orange-100 text-orange-700'
      case 'cancelled': return 'bg-red-100 text-red-700'
      case 'completed': return 'bg-gray-100 text-gray-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Bus Route Management</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center gap-2 min-h-[44px] touch-manipulation whitespace-nowrap"
        >
          <Plus className="w-4 h-4" />
          <span>Create Route</span>
        </button>
      </div>

      {/* Bus Routes Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {routes.map((route) => (
          <div key={route.id} className="card">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{route.route_name || route.name || 'Unnamed Route'}</h3>
                <span className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(route.status)}`}>
                  {(route.status || 'pending').toUpperCase()}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEditClick(route)}
                  className="btn-icon-sm min-h-[44px] min-w-[44px] touch-manipulation"
                >
                  <Edit className="w-4 h-4" />
                </button>
                <button
                  onClick={() => openDeleteDialog(route)}
                  className="btn-icon-sm hover:bg-red-50 hover:text-red-600 min-h-[44px] min-w-[44px] touch-manipulation"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <MapPin className="w-4 h-4" />
                <span>{route.pickup_location}</span>
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Users className="w-4 h-4" />
                <span>{route.registered_count} registered</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {routes.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No bus routes created yet.</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 text-purple-600 hover:underline"
          >
            Create your first route
          </button>
        </div>
      )}

      {/* Create Route Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 overflow-y-auto animate-fade-in" onClick={() => setShowCreateModal(false)}>
          <div className="min-h-full flex items-end sm:items-center justify-center p-0 sm:p-4">
            <div className="modal-content w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl animate-modal-enter" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header px-4 sm:px-6 py-4">
              <h2 className="text-lg font-semibold">Create Bus Route</h2>
            </div>

            <form onSubmit={handleCreateRoute}>
              <div className="modal-body space-y-4 px-4 sm:px-6">
                <div>
                  <label className="label">
                    Route Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.route_name}
                    onChange={(e) => setFormData({ ...formData, route_name: e.target.value })}
                    className="input"
                    placeholder="e.g., Legon Bus #1"
                    required
                  />
                </div>

                <div>
                  <label className="label">
                    Pickup Location <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.pickup_location}
                    onChange={(e) => setFormData({ ...formData, pickup_location: e.target.value })}
                    className="input"
                    placeholder="e.g., Legon Campus Main Gate"
                    required
                  />
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-800">
                    <strong>Note:</strong> This bus route allows unlimited bookings. No capacity or time restrictions apply.
                  </p>
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
                  Create Route
                </button>
              </div>
            </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Route Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 overflow-y-auto animate-fade-in" onClick={() => { setShowEditModal(false); setEditingRoute(null); }}>
          <div className="min-h-full flex items-end sm:items-center justify-center p-0 sm:p-4">
            <div className="modal-content w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl animate-modal-enter" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header px-4 sm:px-6 py-4">
              <h2 className="text-lg font-semibold">Edit Bus Route</h2>
            </div>

            <form onSubmit={handleUpdateRoute}>
              <div className="modal-body space-y-4 px-4 sm:px-6">
                <div>
                  <label className="label">
                    Route Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={editFormData.route_name}
                    onChange={(e) => setEditFormData({ ...editFormData, route_name: e.target.value })}
                    className="input"
                    placeholder="e.g., Legon Bus #1"
                    required
                  />
                </div>

                <div>
                  <label className="label">
                    Pickup Location <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={editFormData.pickup_location}
                    onChange={(e) => setEditFormData({ ...editFormData, pickup_location: e.target.value })}
                    className="input"
                    placeholder="e.g., Legon Campus Main Gate"
                    required
                  />
                </div>

                <div>
                  <label className="label">
                    Status <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={editFormData.status}
                    onChange={(e) => setEditFormData({ ...editFormData, status: e.target.value })}
                    className="input"
                    required
                  >
                    <option value="active">Active</option>
                    <option value="full">Full</option>
                    <option value="cancelled">Cancelled</option>
                    <option value="completed">Completed</option>
                  </select>
                </div>
              </div>

              <div className="modal-footer px-4 sm:px-6 py-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false)
                    setEditingRoute(null)
                  }}
                  className="btn-secondary flex-1 min-h-[44px] touch-manipulation"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1 min-h-[44px] touch-manipulation"
                >
                  Update Route
                </button>
              </div>
            </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, routeId: null, routeName: '', isLoading: false })}
        onConfirm={handleDeleteRoute}
        title="Delete Bus Route"
        message="Are you sure you want to delete this bus route? Passengers who have booked this route will need to be notified."
        itemName={deleteDialog.routeName}
        confirmText="Delete Route"
        cancelText="Keep Route"
        variant="danger"
        isLoading={deleteDialog.isLoading}
      />
    </div>
  )
}
