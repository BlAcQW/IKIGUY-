import { useState, useEffect } from 'react'
import { useOrganization } from '@/contexts/OrganizationContext'
import api from '@/lib/api'
import { Building2, Users, Plus, Settings } from 'lucide-react'
import OrganizationEditModal from '@/components/OrganizationEditModal'

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'organizations' | 'users'>('organizations')

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Administration</h1>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('organizations')}
            className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'organizations'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Building2 className="w-5 h-5" />
            <span>Organizations</span>
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'users'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Users className="w-5 h-5" />
            <span>Users</span>
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'organizations' && <OrganizationsTab />}
      {activeTab === 'users' && <UsersTab />}
    </div>
  )
}

function OrganizationsTab() {
  const { organizations, currentOrganization, setCurrentOrganization, refreshOrganizations } = useOrganization()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [formData, setFormData] = useState({ display_name: '', description: '' })
  const [loading, setLoading] = useState(false)
  const [editingOrganization, setEditingOrganization] = useState<any>(null)

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/organizations', formData)
      await refreshOrganizations()
      setShowCreateForm(false)
      setFormData({ display_name: '', description: '' })
    } catch (error) {
      console.error('Failed to create organization:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">Organizations</h2>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          <span>New Organization</span>
        </button>
      </div>

      {showCreateForm && (
        <form onSubmit={handleCreate} className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-semibold mb-4">Create New Organization</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Organization Name</label>
              <input
                type="text"
                required
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                rows={3}
              />
            </div>
            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create'}
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Organization
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Your Role
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {organizations.map((membership) => (
              <tr key={membership.organization.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {membership.organization.display_name}
                  </div>
                  <div className="text-sm text-gray-500">{membership.organization.name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                    {membership.role}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {currentOrganization?.id === membership.organization.id ? (
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      Active
                    </span>
                  ) : (
                    <span className="text-sm text-gray-500">Inactive</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm space-x-3">
                  {currentOrganization?.id !== membership.organization.id && (
                    <button
                      onClick={() => setCurrentOrganization(membership.organization.id)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Switch
                    </button>
                  )}
                  {(membership.role === 'admin' || membership.role === 'universal_admin') && (
                    <button
                      onClick={() => setEditingOrganization(membership.organization)}
                      className="text-gray-600 hover:text-gray-900"
                    >
                      <Settings className="w-4 h-4 inline" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Edit Organization Modal */}
      {editingOrganization && (
        <OrganizationEditModal
          organization={editingOrganization}
          isOpen={!!editingOrganization}
          onClose={() => setEditingOrganization(null)}
          onSave={() => {
            refreshOrganizations()
            setEditingOrganization(null)
          }}
        />
      )}
    </div>
  )
}

function UsersTab() {
  const { currentOrganization } = useOrganization()
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (currentOrganization) {
      fetchUsers()
    }
  }, [currentOrganization])

  const fetchUsers = async () => {
    try {
      const response = await api.get(`/organizations/${currentOrganization?.id}/users`)
      setUsers(response.data)
    } catch (error) {
      console.error('Failed to fetch users:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!currentOrganization) {
    return <div className="text-gray-500">Please select an organization first.</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">Users in {currentOrganization.display_name}</h2>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading...</div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Joined</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{user.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {user.is_active ? (
                      <span className="px-2 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(user.joined_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
