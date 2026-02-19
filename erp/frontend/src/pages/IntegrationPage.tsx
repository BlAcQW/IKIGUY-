/**
 * IntegrationPage Component
 *
 * Full CRUD interface for System Administration:
 * - Integrations: Manage third-party integrations
 * - Workflows: Configure automated workflows
 */

import { useState, useEffect } from 'react'
import { Plug, Workflow, Plus } from 'lucide-react'
import DataTable, { Column } from '../components/DataTable'
import FormModal from '../components/FormModal'
import DeleteConfirmation from '../components/DeleteConfirmation'
import DetailModal, { DetailField } from '../components/DetailModal'
import api from '../services/api'

type Tab = 'integrations' | 'workflows'

interface Integration {
  id: string
  name: string
  description?: string
  integration_type: string
  is_active: boolean
  config?: object
}

interface WorkflowItem {
  id: string
  name: string
  description?: string
  trigger_type: string
  is_active: boolean
  steps?: object[]
}

export default function IntegrationPage() {
  const [activeTab, setActiveTab] = useState<Tab>('integrations')
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [formData, setFormData] = useState<any>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  // Detail modal
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [detailItem, setDetailItem] = useState<any>(null)

  // Pagination
  const [page, setPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const pageSize = 10

  useEffect(() => {
    fetchData()
  }, [activeTab, page, searchQuery])

  const fetchData = async () => {
    setLoading(true)
    try {
      const skip = (page - 1) * pageSize
      const response = await api.get(`/system/${activeTab}`, {
        params: { skip, limit: pageSize, search: searchQuery || undefined }
      })
      setData(response.data)
      setTotalItems(response.data.length)
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setSelectedItem(null)
    setFormData(getEmptyFormData())
    setIsModalOpen(true)
  }

  const handleEdit = (item: any) => {
    setSelectedItem(item)
    setFormData(item)
    setIsModalOpen(true)
  }

  const handleDelete = (item: any) => {
    setSelectedItem(item)
    setIsDeleteModalOpen(true)
  }

  const handleRowClick = (item: any) => {
    setDetailItem(item)
    setIsDetailOpen(true)
  }

  const getDetailFields = (item: any): DetailField[] => {
    if (!item) return []

    switch (activeTab) {
      case 'integrations':
        return [
          { label: 'Name', value: item.name },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Integration Type', value: item.integration_type },
          { label: 'Is Active', value: item.is_active ? 'Yes' : 'No' },
          { label: 'Configuration', value: item.config ? JSON.stringify(item.config, null, 2) : '-', fullWidth: true },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
          { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
        ]
      case 'workflows':
        return [
          { label: 'Name', value: item.name },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Trigger Type', value: item.trigger_type },
          { label: 'Is Active', value: item.is_active ? 'Yes' : 'No' },
          { label: 'Steps', value: item.steps ? JSON.stringify(item.steps, null, 2) : '-', fullWidth: true },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
          { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
        ]
      default:
        return []
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const endpoint = `/system/${activeTab}`
      if (selectedItem) {
        await api.patch(`${endpoint}/${selectedItem.id}`, formData)
      } else {
        await api.post(endpoint, formData)
      }
      setIsModalOpen(false)
      setFormData({})
      fetchData()
    } catch (error) {
      console.error('Failed to save:', error)
      alert('Failed to save. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const confirmDelete = async () => {
    if (!selectedItem) return

    setIsDeleting(true)
    try {
      await api.delete(`/system/${activeTab}/${selectedItem.id}`)
      setIsDeleteModalOpen(false)
      setSelectedItem(null)
      fetchData()
    } catch (error) {
      console.error('Failed to delete:', error)
      alert('Failed to delete. Please try again.')
    } finally {
      setIsDeleting(false)
    }
  }

  const getEmptyFormData = () => {
    switch (activeTab) {
      case 'integrations':
        return {
          name: '',
          description: '',
          integration_type: 'crm',
          is_active: true
        }
      case 'workflows':
        return {
          name: '',
          description: '',
          trigger_type: 'manual',
          is_active: true
        }
      default:
        return {}
    }
  }

  const getColumns = (): Column<any>[] => {
    switch (activeTab) {
      case 'integrations':
        return [
          { key: 'name', label: 'Integration Name' },
          {
            key: 'integration_type',
            label: 'Type',
            render: (item: Integration) => (
              <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                {item.integration_type}
              </span>
            )
          },
          {
            key: 'description',
            label: 'Description',
            render: (item: Integration) => item.description || '-'
          },
          {
            key: 'is_active',
            label: 'Status',
            render: (item: Integration) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {item.is_active ? 'Active' : 'Inactive'}
              </span>
            )
          }
        ]
      case 'workflows':
        return [
          { key: 'name', label: 'Workflow Name' },
          {
            key: 'trigger_type',
            label: 'Trigger',
            render: (item: WorkflowItem) => (
              <span className="px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-800">
                {item.trigger_type}
              </span>
            )
          },
          {
            key: 'description',
            label: 'Description',
            render: (item: WorkflowItem) => item.description || '-'
          },
          {
            key: 'is_active',
            label: 'Status',
            render: (item: WorkflowItem) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {item.is_active ? 'Active' : 'Inactive'}
              </span>
            )
          }
        ]
      default:
        return []
    }
  }

  const getFormTitle = () => {
    const action = selectedItem ? 'Edit' : 'Create'
    const entity = activeTab.slice(0, -1).charAt(0).toUpperCase() + activeTab.slice(1, -1)
    return `${action} ${entity}`
  }

  const renderForm = () => {
    switch (activeTab) {
      case 'integrations':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Integration Name *
              </label>
              <input
                type="text"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
              <select
                value={formData.integration_type || 'crm'}
                onChange={(e) => setFormData({ ...formData, integration_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="crm">CRM</option>
                <option value="accounting">Accounting</option>
                <option value="marketing">Marketing</option>
                <option value="communication">Communication</option>
                <option value="api">API</option>
                <option value="webhook">Webhook</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_active ?? true}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Active</span>
              </label>
            </div>
          </>
        )

      case 'workflows':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Workflow Name *
              </label>
              <input
                type="text"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Trigger Type *
              </label>
              <select
                value={formData.trigger_type || 'manual'}
                onChange={(e) => setFormData({ ...formData, trigger_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="manual">Manual</option>
                <option value="schedule">Schedule</option>
                <option value="event">Event</option>
                <option value="webhook">Webhook</option>
              </select>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_active ?? true}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Active</span>
              </label>
            </div>
          </>
        )

      default:
        return null
    }
  }

  const tabs = [
    { id: 'integrations' as Tab, label: 'Integrations', icon: Plug },
    { id: 'workflows' as Tab, label: 'Workflows', icon: Workflow }
  ]

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold">System Administration</h1>
        <p className="text-gray-600 mt-2">Manage integrations and automated workflows</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-6 border-b border-gray-200">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id)
                setPage(1)
              }}
              className={`flex items-center px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon className="w-4 h-4 mr-2" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Action Button */}
      <div className="mb-4 flex justify-end">
        <button
          onClick={handleCreate}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add {activeTab.slice(0, -1).charAt(0).toUpperCase() + activeTab.slice(1, -1)}
        </button>
      </div>

      {/* Data Table */}
      <DataTable
        data={data}
        columns={getColumns()}
        loading={loading}
        searchPlaceholder={`Search ${activeTab}...`}
        onSearch={setSearchQuery}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onRowClick={handleRowClick}
        pagination={{
          page,
          pageSize,
          total: totalItems,
          onPageChange: setPage
        }}
        emptyMessage={`No ${activeTab} found`}
      />

      {/* Form Modal */}
      <FormModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setFormData({})
        }}
        title={getFormTitle()}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
      >
        <div className="space-y-4">{renderForm()}</div>
      </FormModal>

      {/* Delete Confirmation */}
      <DeleteConfirmation
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setIsDeleteModalOpen(false)
          setSelectedItem(null)
        }}
        onConfirm={confirmDelete}
        itemName={selectedItem?.name || ''}
        isDeleting={isDeleting}
      />

      {/* Detail Modal */}
      <DetailModal
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        title={`${activeTab === 'integrations' ? 'Integration' : 'Workflow'} Details`}
        fields={getDetailFields(detailItem)}
        onEdit={() => detailItem && handleEdit(detailItem)}
      />
    </div>
  )
}
