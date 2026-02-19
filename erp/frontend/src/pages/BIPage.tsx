/**
 * BIPage Component
 *
 * Full CRUD interface for Business Intelligence & Analytics:
 * - Reports: Manage business reports
 * - Dashboards: Configure analytics dashboards
 * - KPIs: Track key performance indicators
 */

import { useState, useEffect } from 'react'
import { FileText, LayoutDashboard, TrendingUp, Plus } from 'lucide-react'
import DataTable, { Column } from '../components/DataTable'
import FormModal from '../components/FormModal'
import DeleteConfirmation from '../components/DeleteConfirmation'
import DetailModal, { DetailField } from '../components/DetailModal'
import api from '../services/api'

type Tab = 'reports' | 'dashboards' | 'kpis'

interface Report {
  id: string
  report_name: string
  description?: string
  report_type: string
  data_source?: string
  filters?: object
  is_public: boolean
}

interface Dashboard {
  id: string
  dashboard_name: string
  description?: string
  layout?: object
  widgets?: object[]
  is_public: boolean
}

interface KPI {
  id: string
  kpi_name: string
  description?: string
  category: string
  target_value: number
  current_value: number
  unit: string
  is_active: boolean
}

export default function BIPage() {
  const [activeTab, setActiveTab] = useState<Tab>('reports')
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
      const response = await api.get(`/bi/${activeTab}`, {
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
      case 'reports':
        return [
          { label: 'Report Name', value: item.report_name },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Report Type', value: item.report_type },
          { label: 'Data Source', value: item.data_source || '-' },
          { label: 'Filters', value: item.filters ? JSON.stringify(item.filters, null, 2) : '-', fullWidth: true },
          { label: 'Is Public', value: item.is_public ? 'Yes' : 'No' },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
          { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
        ]
      case 'dashboards':
        return [
          { label: 'Dashboard Name', value: item.dashboard_name },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Layout', value: item.layout ? JSON.stringify(item.layout, null, 2) : '-', fullWidth: true },
          { label: 'Widgets', value: item.widgets ? JSON.stringify(item.widgets, null, 2) : '-', fullWidth: true },
          { label: 'Is Public', value: item.is_public ? 'Yes' : 'No' },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
          { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
        ]
      case 'kpis':
        return [
          { label: 'KPI Name', value: item.kpi_name },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Category', value: item.category },
          { label: 'Target Value', value: `${item.target_value} ${item.unit || ''}` },
          { label: 'Current Value', value: `${item.current_value} ${item.unit || ''}` },
          { label: 'Progress', value: item.target_value > 0 ? `${((item.current_value / item.target_value) * 100).toFixed(1)}%` : '-' },
          { label: 'Unit', value: item.unit },
          { label: 'Is Active', value: item.is_active ? 'Yes' : 'No' },
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
      const endpoint = `/bi/${activeTab}`
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
      await api.delete(`/bi/${activeTab}/${selectedItem.id}`)
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
      case 'reports':
        return {
          report_name: '',
          description: '',
          report_type: 'financial',
          data_source: '',
          is_public: false
        }
      case 'dashboards':
        return {
          dashboard_name: '',
          description: '',
          is_public: false
        }
      case 'kpis':
        return {
          kpi_name: '',
          description: '',
          category: 'sales',
          target_value: 0,
          current_value: 0,
          unit: 'currency',
          is_active: true
        }
      default:
        return {}
    }
  }

  const getColumns = (): Column<any>[] => {
    switch (activeTab) {
      case 'reports':
        return [
          { key: 'report_name', label: 'Report Name' },
          { key: 'report_type', label: 'Type' },
          { key: 'data_source', label: 'Data Source' },
          {
            key: 'is_public',
            label: 'Visibility',
            render: (item: Report) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.is_public ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {item.is_public ? 'Public' : 'Private'}
              </span>
            )
          }
        ]
      case 'dashboards':
        return [
          { key: 'dashboard_name', label: 'Dashboard Name' },
          {
            key: 'description',
            label: 'Description',
            render: (item: Dashboard) => item.description || '-'
          },
          {
            key: 'is_public',
            label: 'Visibility',
            render: (item: Dashboard) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.is_public ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {item.is_public ? 'Public' : 'Private'}
              </span>
            )
          }
        ]
      case 'kpis':
        return [
          { key: 'kpi_name', label: 'KPI Name' },
          { key: 'category', label: 'Category' },
          {
            key: 'current_value',
            label: 'Current',
            render: (item: KPI) => `${item.current_value} ${item.unit}`
          },
          {
            key: 'target_value',
            label: 'Target',
            render: (item: KPI) => `${item.target_value} ${item.unit}`
          },
          {
            key: 'progress',
            label: 'Progress',
            render: (item: KPI) => {
              const progress = (item.current_value / item.target_value) * 100
              return (
                <span className={`px-2 py-1 rounded-full text-xs ${
                  progress >= 100 ? 'bg-green-100 text-green-800' :
                  progress >= 75 ? 'bg-blue-100 text-blue-800' :
                  progress >= 50 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {progress.toFixed(0)}%
                </span>
              )
            }
          },
          {
            key: 'is_active',
            label: 'Status',
            render: (item: KPI) => (
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
      case 'reports':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Report Name *
              </label>
              <input
                type="text"
                value={formData.report_name || ''}
                onChange={(e) => setFormData({ ...formData, report_name: e.target.value })}
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

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
                <select
                  value={formData.report_type || 'financial'}
                  onChange={(e) => setFormData({ ...formData, report_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="financial">Financial</option>
                  <option value="sales">Sales</option>
                  <option value="operational">Operational</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Source
                </label>
                <input
                  type="text"
                  value={formData.data_source || ''}
                  onChange={(e) => setFormData({ ...formData, data_source: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_public ?? false}
                  onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Public Report</span>
              </label>
            </div>
          </>
        )

      case 'dashboards':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dashboard Name *
              </label>
              <input
                type="text"
                value={formData.dashboard_name || ''}
                onChange={(e) => setFormData({ ...formData, dashboard_name: e.target.value })}
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
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_public ?? false}
                  onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Public Dashboard</span>
              </label>
            </div>
          </>
        )

      case 'kpis':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">KPI Name *</label>
              <input
                type="text"
                value={formData.kpi_name || ''}
                onChange={(e) => setFormData({ ...formData, kpi_name: e.target.value })}
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
                rows={2}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                <select
                  value={formData.category || 'sales'}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="sales">Sales</option>
                  <option value="marketing">Marketing</option>
                  <option value="operations">Operations</option>
                  <option value="finance">Finance</option>
                  <option value="customer_service">Customer Service</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Unit *</label>
                <select
                  value={formData.unit || 'currency'}
                  onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="currency">Currency</option>
                  <option value="percentage">Percentage</option>
                  <option value="count">Count</option>
                  <option value="days">Days</option>
                  <option value="hours">Hours</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Current Value *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.current_value || ''}
                  onChange={(e) => setFormData({ ...formData, current_value: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Value *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.target_value || ''}
                  onChange={(e) => setFormData({ ...formData, target_value: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
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
    { id: 'reports' as Tab, label: 'Reports', icon: FileText },
    { id: 'dashboards' as Tab, label: 'Dashboards', icon: LayoutDashboard },
    { id: 'kpis' as Tab, label: 'KPIs', icon: TrendingUp }
  ]

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Business Intelligence & Analytics</h1>
        <p className="text-gray-600 mt-2">Manage reports, dashboards, and KPIs</p>
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
        itemName={
          selectedItem
            ? activeTab === 'reports'
              ? selectedItem.report_name
              : activeTab === 'dashboards'
              ? selectedItem.dashboard_name
              : selectedItem.kpi_name
            : ''
        }
        isDeleting={isDeleting}
      />

      {/* Detail Modal */}
      <DetailModal
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        title={`${activeTab === 'reports' ? 'Report' : activeTab === 'dashboards' ? 'Dashboard' : 'KPI'} Details`}
        fields={getDetailFields(detailItem)}
        onEdit={() => detailItem && handleEdit(detailItem)}
      />
    </div>
  )
}
