import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Edit, Trash2, MapPin, Users, Phone, X, Loader2, Eye, ChevronRight } from 'lucide-react'
import ConfirmDialog from '../components/ConfirmDialog'
import { getApiUrl } from '../config/api-config'
import { encodeHeaderValue } from '../lib/header-utils'

interface Branch {
  id: string
  name: string
  location: string
  address?: string
  contact_person?: string
  contact_phone?: string
  capacity?: number
  status: string
  created_at: string
}

interface BranchMember {
  id: string
  full_name?: string
  name?: string
  phone: string
  email?: string
  roles?: string[]
  member_status?: string
  created_at?: string
}

export default function BranchManagement() {
  const navigate = useNavigate()
  const [branches, setBranches] = useState<Branch[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingBranch, setEditingBranch] = useState<Branch | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    address: '',
    contact_person: '',
    contact_phone: '',
    capacity: 100,
    status: 'active'
  })
  // Delete confirmation dialog state
  const [deleteDialog, setDeleteDialog] = useState<{
    isOpen: boolean;
    branchId: string | null;
    branchName: string;
    isLoading: boolean;
  }>({ isOpen: false, branchId: null, branchName: '', isLoading: false })

  // Branch members modal state
  const [selectedBranch, setSelectedBranch] = useState<Branch | null>(null)
  const [branchMembers, setBranchMembers] = useState<BranchMember[]>([])
  const [loadingMembers, setLoadingMembers] = useState(false)

  useEffect(() => {
    fetchBranches()
  }, [])

  const fetchBranches = async () => {
    const token = localStorage.getItem('access_token')

    try {
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('/api/v1/branches', {
        headers
      })

      if (response.ok) {
        const data = await response.json()
        setBranches(data)
      }
    } catch (err) {
      console.error('Failed to fetch branches:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateBranch = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem('access_token')

    if (!token) {
      alert('Please login to create branches')
      return
    }

    try {
      const response = await fetch('/api/v1/branches', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        alert('Branch created successfully!')
        setShowCreateModal(false)
        setFormData({
          name: '',
          location: '',
          address: '',
          contact_person: '',
          contact_phone: '',
          capacity: 100,
          status: 'active'
        })
        fetchBranches()
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        alert(`Failed to create branch: ${errorData.detail || 'Please try again'}`)
      }
    } catch (err) {
      console.error('Failed to create branch:', err)
      alert('Failed to create branch. Please check your connection and try again.')
    }
  }

  const handleUpdateBranch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingBranch) return

    const token = localStorage.getItem('access_token')

    try {
      const response = await fetch(`/api/v1/branches/${editingBranch.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        alert('Branch updated successfully!')
        setEditingBranch(null)
        setFormData({
          name: '',
          location: '',
          address: '',
          contact_person: '',
          contact_phone: '',
          capacity: 100,
          status: 'active'
        })
        fetchBranches()
      } else {
        alert('Failed to update branch')
      }
    } catch (err) {
      console.error('Failed to update branch:', err)
      alert('Failed to update branch')
    }
  }

  // Open delete confirmation dialog
  const openDeleteDialog = (branch: Branch) => {
    setDeleteDialog({
      isOpen: true,
      branchId: branch.id,
      branchName: branch.name,
      isLoading: false,
    })
  }

  // Handle confirmed delete
  const handleDeleteBranch = async () => {
    if (!deleteDialog.branchId) return

    const token = localStorage.getItem('access_token')
    if (!token) return

    setDeleteDialog(prev => ({ ...prev, isLoading: true }))

    try {
      const response = await fetch(`/api/v1/branches/${deleteDialog.branchId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        setDeleteDialog({ isOpen: false, branchId: null, branchName: '', isLoading: false })
        fetchBranches()
      } else {
        alert('Failed to delete branch')
        setDeleteDialog(prev => ({ ...prev, isLoading: false }))
      }
    } catch (err) {
      console.error('Failed to delete branch:', err)
      alert('Failed to delete branch')
      setDeleteDialog(prev => ({ ...prev, isLoading: false }))
    }
  }

  const openEditModal = (branch: Branch) => {
    setEditingBranch(branch)
    setFormData({
      name: branch.name,
      location: branch.location,
      address: branch.address || '',
      contact_person: branch.contact_person || '',
      contact_phone: branch.contact_phone || '',
      capacity: branch.capacity || 100,
      status: branch.status
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-700'
      case 'inactive': return 'bg-gray-100 text-gray-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const fetchBranchMembers = async (branch: Branch) => {
    setSelectedBranch(branch)
    setLoadingMembers(true)
    setBranchMembers([])

    try {
      const token = localStorage.getItem('access_token')
      const orgId = localStorage.getItem('current_organization_id')

      // Fetch users with this branch_id
      const response = await fetch(getApiUrl(`member-portal/directory?branch_id=${branch.id}&page_size=100`), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Organization-ID': encodeHeaderValue(orgId) || '',
        },
      })

      if (response.ok) {
        const data = await response.json()
        const members = data.members || data.items || []
        setBranchMembers(members.map((m: any) => ({
          id: m.id || m._id,
          full_name: m.full_name || m.name,
          name: m.name,
          phone: m.phone,
          email: m.email,
          roles: m.roles,
          member_status: m.member_status,
          created_at: m.created_at,
        })))
      }
    } catch (err) {
      console.error('Failed to fetch branch members:', err)
    } finally {
      setLoadingMembers(false)
    }
  }

  const closeMembersModal = () => {
    setSelectedBranch(null)
    setBranchMembers([])
  }

  const viewMemberProfile = (memberId: string) => {
    navigate(`/admin/members/${memberId}`)
    closeMembersModal()
  }

  if (loading) {
    return <div className="p-8">Loading branches...</div>
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Branch Management</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Create Branch
        </button>
      </div>

      {/* Branches Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {branches.map((branch) => (
          <div key={branch.id} className="card card-hover">
            {/* Clickable area to view members */}
            <div
              className="cursor-pointer"
              onClick={() => fetchBranchMembers(branch)}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1 flex items-center gap-2">
                    {branch.name}
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  </h3>
                  <div className="flex items-center gap-1 text-sm text-gray-600">
                    <MapPin className="w-4 h-4" />
                    {branch.location}
                  </div>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(branch.status)}`}>
                  {branch.status}
                </span>
              </div>

              {branch.address && (
                <p className="text-sm text-gray-600 mb-3">{branch.address}</p>
              )}

              <div className="space-y-2 mb-4">
                {branch.contact_person && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Users className="w-4 h-4" />
                    <span>{branch.contact_person}</span>
                  </div>
                )}
                {branch.contact_phone && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Phone className="w-4 h-4" />
                    <span>{branch.contact_phone}</span>
                  </div>
                )}
                {branch.capacity && (
                  <div className="text-sm text-gray-600">
                    <strong>Capacity:</strong> {branch.capacity} people
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-2 pt-4 border-t">
              <button
                onClick={() => openEditModal(branch)}
                className="btn-ghost-purple btn-sm flex-1"
              >
                <Edit className="w-4 h-4" />
                Edit
              </button>
              <button
                onClick={() => openDeleteDialog(branch)}
                className="btn-ghost btn-sm flex-1 text-red-600 hover:bg-red-50 hover:text-red-700"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        ))}

        {branches.length === 0 && (
          <div className="col-span-full text-center py-12 text-gray-500">
            No branches found. Create your first branch to get started!
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {(showCreateModal || editingBranch) && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 overflow-y-auto animate-fade-in" onClick={() => { setShowCreateModal(false); setEditingBranch(null); }}>
          <div className="min-h-full flex items-center justify-center p-4">
            <div className="modal-content modal-content-lg animate-modal-enter" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="text-lg font-semibold">
                {editingBranch ? 'Edit Branch' : 'Create New Branch'}
              </h2>
            </div>

            <form onSubmit={editingBranch ? handleUpdateBranch : handleCreateBranch}>
              <div className="modal-body">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="label">Branch Name *</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="input"
                      required
                      placeholder="e.g., Main Branch, East Branch"
                    />
                  </div>

                  <div>
                    <label className="label">Location *</label>
                    <input
                      type="text"
                      value={formData.location}
                      onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                      className="input"
                      required
                      placeholder="e.g., Accra, Kumasi"
                    />
                  </div>

                  <div>
                    <label className="label">Capacity</label>
                    <input
                      type="number"
                      value={formData.capacity}
                      onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value) })}
                      className="input"
                      placeholder="100"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="label">Address</label>
                    <input
                      type="text"
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      className="input"
                      placeholder="Full address"
                    />
                  </div>

                  <div>
                    <label className="label">Contact Person</label>
                    <input
                      type="text"
                      value={formData.contact_person}
                      onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                      className="input"
                      placeholder="Branch leader name"
                    />
                  </div>

                  <div>
                    <label className="label">Contact Phone</label>
                    <input
                      type="tel"
                      value={formData.contact_phone}
                      onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                      className="input"
                      placeholder="+233XXXXXXXXX"
                    />
                  </div>

                  <div>
                    <label className="label">Status</label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      className="input"
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false)
                    setEditingBranch(null)
                    setFormData({
                      name: '',
                      location: '',
                      address: '',
                      contact_person: '',
                      contact_phone: '',
                      capacity: 100,
                      status: 'active'
                    })
                  }}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1"
                >
                  {editingBranch ? 'Update Branch' : 'Create Branch'}
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
        onClose={() => setDeleteDialog({ isOpen: false, branchId: null, branchName: '', isLoading: false })}
        onConfirm={handleDeleteBranch}
        title="Delete Branch"
        message="Are you sure you want to delete this branch? Members associated with this branch will need to be reassigned."
        itemName={deleteDialog.branchName}
        confirmText="Delete Branch"
        cancelText="Keep Branch"
        variant="danger"
        isLoading={deleteDialog.isLoading}
      />

      {/* Branch Members Modal */}
      {selectedBranch && (
        <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl shadow-2xl w-full sm:max-w-2xl max-h-[85vh] overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/20 rounded-xl">
                    <Users className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-white">{selectedBranch.name} Members</h2>
                    <p className="text-purple-100 text-sm">{selectedBranch.location}</p>
                  </div>
                </div>
                <button
                  onClick={closeMembersModal}
                  className="p-2 hover:bg-white/20 rounded-xl transition-colors"
                >
                  <X className="w-5 h-5 text-white" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(85vh-80px)]">
              {loadingMembers ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
                  <span className="ml-3 text-gray-600">Loading members...</span>
                </div>
              ) : branchMembers.length === 0 ? (
                <div className="text-center py-12">
                  <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No members found in this branch</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-gray-500 mb-4">{branchMembers.length} member(s) found</p>
                  {branchMembers.map((member) => (
                    <div
                      key={member.id}
                      onClick={() => viewMemberProfile(member.id)}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-purple-50 cursor-pointer transition-colors group"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                          <span className="text-purple-600 font-semibold">
                            {(member.full_name || member.name || '?').charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{member.full_name || member.name || 'Unknown'}</p>
                          <p className="text-sm text-gray-500">{member.phone}</p>
                          {member.email && (
                            <p className="text-xs text-gray-400">{member.email}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {member.roles && member.roles.length > 0 && (
                          <span className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-700 rounded-full">
                            {member.roles[0]}
                          </span>
                        )}
                        <Eye className="w-4 h-4 text-gray-400 group-hover:text-purple-600 transition-colors" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
