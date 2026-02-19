/**
 * ProjectsPage Component
 *
 * Full CRUD interface for Project Management:
 * - Projects: Manage project records
 * - Tasks: Track project tasks
 * - Resources: Manage project resources
 * - Timesheets: Track time entries
 */

import { useState, useEffect } from 'react'
import { Folder, CheckSquare, Users, Clock, Plus, Paperclip } from 'lucide-react'
import DataTable, { Column } from '../components/DataTable'
import FormModal from '../components/FormModal'
import DeleteConfirmation from '../components/DeleteConfirmation'
import DetailModal, { DetailField } from '../components/DetailModal'
import { Upload, X, FileText, Download } from 'lucide-react'
import api from '../services/api'

type Tab = 'projects' | 'tasks' | 'resources' | 'timesheets'

interface Attachment {
  id: string
  original_filename: string
  stored_filename: string
  file_path: string
  file_size: number
  file_type: string
  mime_type: string
  uploaded_by: string
  uploaded_at: string
}

interface Project {
  id: string
  project_name: string
  project_code?: string
  description?: string
  start_date: string
  end_date?: string
  status: string
  budget?: number
  customer_id?: string
  project_manager_id?: string
  invoice_id?: string
  attachments?: Attachment[]
}

interface Task {
  id: string
  task_name: string
  description?: string
  project_id: string
  assignee_id?: string
  status: string
  priority: string
  due_date?: string
  estimated_hours?: number
}

interface Resource {
  id: string
  resource_name: string
  resource_type: string
  project_id: string
  quantity: number
  unit_cost: number
  total_cost: number
}

interface Timesheet {
  id: string
  employee_id: string
  project_id: string
  task_id?: string
  date: string
  hours: number
  description?: string
  billable: boolean
}

export default function ProjectsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('projects')
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [formData, setFormData] = useState<any>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [detailItem, setDetailItem] = useState<any>(null)

  // Pagination
  const [page, setPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const pageSize = 10

  // Dropdown data for projects
  const [customers, setCustomers] = useState<any[]>([])
  const [employees, setEmployees] = useState<any[]>([])
  const [invoices, setInvoices] = useState<any[]>([])
  const [loadingDropdowns, setLoadingDropdowns] = useState(false)

  useEffect(() => {
    fetchData()
  }, [activeTab, page, searchQuery])

  const fetchData = async () => {
    setLoading(true)
    try {
      const skip = (page - 1) * pageSize
      // Map activeTab to correct API endpoint
      const endpoint = activeTab === 'projects' ? '/projects' : `/projects/${activeTab}`
      const response = await api.get(endpoint, {
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

  const fetchProjectDropdownData = async () => {
    if (activeTab !== 'projects') return

    setLoadingDropdowns(true)
    try {
      // Fetch customers, employees, and invoices in parallel
      const [customersRes, employeesRes, invoicesRes] = await Promise.all([
        api.get('/crm/customers', { params: { limit: 1000 } }),
        api.get('/hr/employees', { params: { limit: 1000 } }),
        api.get('/finance/invoices', { params: { limit: 1000 } })
      ])

      setCustomers(customersRes.data)
      setEmployees(employeesRes.data)
      setInvoices(invoicesRes.data)
    } catch (error) {
      console.error('Failed to fetch dropdown data:', error)
    } finally {
      setLoadingDropdowns(false)
    }
  }

  const handleCreate = async () => {
    setSelectedItem(null)
    setFormData(getEmptyFormData())

    // Fetch dropdown data for projects
    if (activeTab === 'projects') {
      await fetchProjectDropdownData()
    }

    setIsModalOpen(true)
  }

  const handleEdit = async (item: any) => {
    setSelectedItem(item)
    setFormData(item)

    // Fetch dropdown data for projects
    if (activeTab === 'projects') {
      await fetchProjectDropdownData()
    }

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
      case 'projects':
        return [
          { label: 'Status', value: item.status, type: 'status' as const },
          { label: 'Project Code', value: item.project_code || '-' },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Start Date', value: item.start_date, type: 'date' as const },
          { label: 'End Date', value: item.end_date || '-', type: 'date' as const },
          { label: 'Budget', value: item.budget ? `GHS ${item.budget.toLocaleString()}` : '-', type: 'currency' as const },
          { label: 'Customer', value: item.customer_id || 'Internal Project' },
          { label: 'Project Manager', value: item.project_manager_id || '-' },
          { label: 'Invoice', value: item.invoice_id || 'Not linked' },
          {
            label: 'Attachments',
            value: item.attachments,
            fullWidth: true,
            render: () => {
              if (!item.attachments || item.attachments.length === 0) {
                return <span className="text-gray-400 italic">No attachments</span>
              }
              return (
                <div className="space-y-2">
                  {item.attachments.map((att: any, idx: number) => (
                    <div key={att.id || idx} className="flex items-center justify-between bg-white px-3 py-2.5 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-50 rounded-lg">
                          <FileText className="w-4 h-4 text-blue-600" />
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-900">{att.original_filename}</span>
                          <span className="text-xs text-gray-500 ml-2">({(att.file_size / 1024).toFixed(1)} KB)</span>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={async () => {
                          try {
                            const response = await api.get(
                              `/projects/${item.id}/attachments/${att.id}/download`,
                              { responseType: 'blob' }
                            )
                            const url = window.URL.createObjectURL(new Blob([response.data]))
                            const link = document.createElement('a')
                            link.href = url
                            link.setAttribute('download', att.original_filename)
                            document.body.appendChild(link)
                            link.click()
                            link.remove()
                          } catch (err) {
                            console.error('Download failed:', err)
                          }
                        }}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="Download"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )
            }
          },
          { label: 'Created', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-', type: 'date' as const },
          { label: 'Last Updated', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-', type: 'date' as const }
        ]
      case 'tasks':
        return [
          { label: 'Task Name', value: item.task_name },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Project ID', value: item.project_id },
          { label: 'Assignee ID', value: item.assignee_id || '-' },
          { label: 'Status', value: item.status },
          { label: 'Priority', value: item.priority },
          { label: 'Due Date', value: item.due_date || '-' },
          { label: 'Estimated Hours', value: item.estimated_hours ? `${item.estimated_hours} hrs` : '-' },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
          { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
        ]
      case 'resources':
        return [
          { label: 'Resource Name', value: item.resource_name },
          { label: 'Resource Type', value: item.resource_type },
          { label: 'Project ID', value: item.project_id },
          { label: 'Quantity', value: item.quantity.toString() },
          { label: 'Unit Cost', value: `GHS ${item.unit_cost}` },
          { label: 'Total Cost', value: `GHS ${item.total_cost}` },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
          { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
        ]
      case 'timesheets':
        return [
          { label: 'Employee ID', value: item.employee_id },
          { label: 'Project ID', value: item.project_id },
          { label: 'Task ID', value: item.task_id || '-' },
          { label: 'Date', value: item.date },
          { label: 'Hours', value: `${item.hours} hrs` },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Billable', value: item.billable ? 'Yes' : 'No' },
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
      // Map activeTab to correct API endpoint
      const endpoint = activeTab === 'projects' ? '/projects' : `/projects/${activeTab}`

      // Separate attachment_files from form data
      const { attachment_files, ...dataToSubmit } = formData

      // Clean up form data: remove empty strings and convert them to null
      const cleanedData = Object.entries(dataToSubmit).reduce((acc, [key, value]) => {
        // Keep value if it's not an empty string, otherwise omit it (backend will use default)
        if (value !== '' && value !== null && value !== undefined) {
          acc[key] = value
        }
        return acc
      }, {} as any)

      let projectId: string | null = null

      if (selectedItem) {
        await api.patch(`${endpoint}/${selectedItem.id}`, cleanedData)
        projectId = selectedItem.id
      } else {
        const response = await api.post(endpoint, cleanedData)
        projectId = response.data.id
      }

      // Upload attachment files for projects
      if (activeTab === 'projects' && projectId && attachment_files && attachment_files.length > 0) {
        for (const file of attachment_files) {
          const uploadFormData = new FormData()
          uploadFormData.append('file', file)
          try {
            await api.post(
              `/projects/${projectId}/attachments`,
              uploadFormData,
              { headers: { 'Content-Type': 'multipart/form-data' } }
            )
          } catch (uploadError) {
            console.error('Failed to upload file:', file.name, uploadError)
          }
        }
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
      // Map activeTab to correct API endpoint
      const endpoint = activeTab === 'projects' ? '/projects' : `/projects/${activeTab}`
      await api.delete(`${endpoint}/${selectedItem.id}`)
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
      case 'projects':
        return {
          project_name: '',
          description: '',
          start_date: new Date().toISOString().split('T')[0],
          end_date: '',
          status: 'planning',
          budget: 0,
          customer_id: '',
          project_manager_id: '',
          invoice_id: ''
        }
      case 'tasks':
        return {
          task_name: '',
          description: '',
          project_id: '',
          assignee_id: '',
          status: 'todo',
          priority: 'medium',
          due_date: new Date().toISOString().split('T')[0],
          estimated_hours: 0
        }
      case 'resources':
        return {
          resource_name: '',
          resource_type: 'labor',
          project_id: '',
          quantity: 1,
          unit_cost: 0,
          total_cost: 0
        }
      case 'timesheets':
        return {
          employee_id: '',
          project_id: '',
          task_id: '',
          date: new Date().toISOString().split('T')[0],
          hours: 0,
          description: '',
          billable: true
        }
      default:
        return {}
    }
  }

  const getColumns = (): Column<any>[] => {
    switch (activeTab) {
      case 'projects':
        return [
          { key: 'project_name', label: 'Project Name', width: '60%' },
          {
            key: 'attachments',
            label: 'Files',
            render: (item: Project) => {
              const count = item.attachments?.length || 0
              return count > 0 ? (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-800">
                  <Paperclip className="w-3 h-3 mr-1" />
                  {count}
                </span>
              ) : (
                <span className="text-gray-400 text-xs">-</span>
              )
            }
          },
          {
            key: 'status',
            label: 'Status',
            render: (item: Project) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.status === 'completed' ? 'bg-green-100 text-green-800' :
                item.status === 'active' ? 'bg-blue-100 text-blue-800' :
                item.status === 'on_hold' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {item.status}
              </span>
            )
          }
        ]
      case 'tasks':
        return [
          { key: 'task_name', label: 'Task Name' },
          { key: 'project_id', label: 'Project ID' },
          { key: 'assignee_id', label: 'Assignee' },
          { key: 'due_date', label: 'Due Date' },
          {
            key: 'priority',
            label: 'Priority',
            render: (item: Task) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.priority === 'high' ? 'bg-red-100 text-red-800' :
                item.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                'bg-green-100 text-green-800'
              }`}>
                {item.priority}
              </span>
            )
          },
          {
            key: 'status',
            label: 'Status',
            render: (item: Task) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.status === 'done' ? 'bg-green-100 text-green-800' :
                item.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {item.status}
              </span>
            )
          }
        ]
      case 'resources':
        return [
          { key: 'resource_name', label: 'Resource Name' },
          { key: 'resource_type', label: 'Type' },
          { key: 'project_id', label: 'Project ID' },
          { key: 'quantity', label: 'Quantity' },
          {
            key: 'unit_cost',
            label: 'Unit Cost',
            render: (item: Resource) => `$${item.unit_cost.toFixed(2)}`
          },
          {
            key: 'total_cost',
            label: 'Total Cost',
            render: (item: Resource) => `$${item.total_cost.toFixed(2)}`
          }
        ]
      case 'timesheets':
        return [
          { key: 'employee_id', label: 'Employee ID' },
          { key: 'project_id', label: 'Project ID' },
          { key: 'date', label: 'Date' },
          { key: 'hours', label: 'Hours' },
          {
            key: 'billable',
            label: 'Billable',
            render: (item: Timesheet) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.billable ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {item.billable ? 'Yes' : 'No'}
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
      case 'projects':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Project Name *
              </label>
              <input
                type="text"
                value={formData.project_name || ''}
                onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Project code will be auto-generated based on the project name
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Customer (Optional)</label>
              {loadingDropdowns ? (
                <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500">
                  Loading customers...
                </div>
              ) : (
                <select
                  value={formData.customer_id || ''}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No customer (Internal project)</option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.company_name || customer.contact_name} - {customer.email}
                    </option>
                  ))}
                </select>
              )}
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date *
                </label>
                <input
                  type="date"
                  value={formData.start_date || ''}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={formData.end_date || ''}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status *</label>
                <select
                  value={formData.status || 'planning'}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="planning">Planning</option>
                  <option value="active">Active</option>
                  <option value="on_hold">On Hold</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Budget</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.budget || ''}
                  onChange={(e) => {
                    const value = e.target.value === '' ? 0 : parseFloat(e.target.value)
                    setFormData({ ...formData, budget: isNaN(value) ? 0 : value })
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Project Manager *</label>
              {loadingDropdowns ? (
                <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500">
                  Loading employees...
                </div>
              ) : (
                <select
                  value={formData.project_manager_id || ''}
                  onChange={(e) => setFormData({ ...formData, project_manager_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select a project manager</option>
                  {employees.map((employee) => (
                    <option key={employee.id} value={employee.id}>
                      {employee.full_name} - {employee.email}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Related Invoice (Optional)</label>
              {loadingDropdowns ? (
                <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500">
                  Loading invoices...
                </div>
              ) : (
                <select
                  value={formData.invoice_id || ''}
                  onChange={(e) => setFormData({ ...formData, invoice_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No linked invoice</option>
                  {invoices.map((invoice) => (
                    <option key={invoice.id} value={invoice.id}>
                      {invoice.invoice_number} - ${invoice.total_amount?.toFixed(2)} ({invoice.status})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Attachments Section - same pattern as expenses receipts */}
            <div className="border-t pt-4 mt-4">
              <div className="flex items-center mb-3">
                <Paperclip className="w-5 h-5 text-gray-500 mr-2" />
                <label className="block text-sm font-medium text-gray-700">
                  Project Attachments
                </label>
              </div>

              {/* File Upload */}
              <div className="mb-3">
                <label className="block cursor-pointer">
                  <div className="relative border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 bg-gray-50 transition-colors">
                    <input
                      type="file"
                      multiple
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.jpg,.jpeg,.png,.gif,.mp3,.wav,.mp4,.mov,.zip,.rar"
                      onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          const newFiles = Array.from(e.target.files)
                          const attachmentFiles = formData.attachment_files || []
                          setFormData({ ...formData, attachment_files: [...attachmentFiles, ...newFiles] })
                        }
                      }}
                    />
                    <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                    <p className="text-sm font-medium text-gray-700">
                      Drop files here or click to browse
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      PDF, Documents, Images, Audio, Video (max 100MB)
                    </p>
                  </div>
                </label>
              </div>

              {/* Preview files to upload */}
              {formData.attachment_files && formData.attachment_files.length > 0 && (
                <div className="mb-3 space-y-2">
                  <p className="text-xs text-amber-600 font-medium">Files to upload:</p>
                  {formData.attachment_files.map((file: File, index: number) => (
                    <div
                      key={index}
                      className="flex items-center justify-between bg-amber-50 px-3 py-2 rounded-md border border-amber-200"
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-amber-600" />
                        <span className="text-sm text-gray-700">{file.name}</span>
                        <span className="text-xs text-gray-500">
                          ({(file.size / 1024).toFixed(1)} KB)
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          const files = [...formData.attachment_files]
                          files.splice(index, 1)
                          setFormData({ ...formData, attachment_files: files })
                        }}
                        className="p-1 text-red-600 hover:bg-red-50 rounded"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Display existing attachments when editing */}
              {selectedItem && formData.attachments && formData.attachments.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs text-gray-600 font-medium">Existing attachments:</p>
                  {formData.attachments.map((att: any, index: number) => (
                    <div
                      key={att.id || index}
                      className="flex items-center justify-between bg-blue-50 px-3 py-2 rounded-md border border-blue-200"
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-blue-600" />
                        <span className="text-sm text-blue-700">{att.original_filename}</span>
                        <span className="text-xs text-gray-500">
                          ({(att.file_size / 1024).toFixed(1)} KB)
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={async () => {
                            try {
                              const response = await api.get(
                                `/projects/${selectedItem.id}/attachments/${att.id}/download`,
                                { responseType: 'blob' }
                              )
                              const url = window.URL.createObjectURL(new Blob([response.data]))
                              const link = document.createElement('a')
                              link.href = url
                              link.setAttribute('download', att.original_filename)
                              document.body.appendChild(link)
                              link.click()
                              link.remove()
                            } catch (err) {
                              console.error('Download failed:', err)
                            }
                          }}
                          className="p-1 text-blue-600 hover:bg-blue-100 rounded"
                          title="Download"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={async () => {
                            if (!confirm(`Delete "${att.original_filename}"?`)) return
                            try {
                              await api.delete(`/projects/${selectedItem.id}/attachments/${att.id}`)
                              const updatedAttachments = formData.attachments.filter((a: any) => a.id !== att.id)
                              setFormData({ ...formData, attachments: updatedAttachments })
                            } catch (err) {
                              console.error('Delete failed:', err)
                              alert('Failed to delete attachment')
                            }
                          }}
                          className="p-1 text-red-600 hover:bg-red-100 rounded"
                          title="Delete"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )

      case 'tasks':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Task Name *</label>
              <input
                type="text"
                value={formData.task_name || ''}
                onChange={(e) => setFormData({ ...formData, task_name: e.target.value })}
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Project ID *
                </label>
                <input
                  type="text"
                  value={formData.project_id || ''}
                  onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Assignee ID</label>
                <input
                  type="text"
                  value={formData.assignee_id || ''}
                  onChange={(e) => setFormData({ ...formData, assignee_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status *</label>
                <select
                  value={formData.status || 'todo'}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="todo">To Do</option>
                  <option value="in_progress">In Progress</option>
                  <option value="done">Done</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority *</label>
                <select
                  value={formData.priority || 'medium'}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                <input
                  type="date"
                  value={formData.due_date || ''}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Estimated Hours
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={formData.estimated_hours || ''}
                  onChange={(e) => setFormData({ ...formData, estimated_hours: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </>
        )

      case 'resources':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Resource Name *
              </label>
              <input
                type="text"
                value={formData.resource_name || ''}
                onChange={(e) => setFormData({ ...formData, resource_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
                <select
                  value={formData.resource_type || 'labor'}
                  onChange={(e) => setFormData({ ...formData, resource_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="labor">Labor</option>
                  <option value="equipment">Equipment</option>
                  <option value="materials">Materials</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Project ID *
                </label>
                <input
                  type="text"
                  value={formData.project_id || ''}
                  onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity *</label>
                <input
                  type="number"
                  value={formData.quantity || ''}
                  onChange={(e) => {
                    const quantity = parseFloat(e.target.value)
                    setFormData({
                      ...formData,
                      quantity,
                      total_cost: quantity * (formData.unit_cost || 0)
                    })
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Unit Cost *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.unit_cost || ''}
                  onChange={(e) => {
                    const unit_cost = parseFloat(e.target.value)
                    setFormData({
                      ...formData,
                      unit_cost,
                      total_cost: (formData.quantity || 0) * unit_cost
                    })
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Total Cost
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.total_cost || ''}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100"
                  disabled
                />
              </div>
            </div>
          </>
        )

      case 'timesheets':
        return (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Employee ID *
                </label>
                <input
                  type="text"
                  value={formData.employee_id || ''}
                  onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Project ID *
                </label>
                <input
                  type="text"
                  value={formData.project_id || ''}
                  onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Task ID</label>
              <input
                type="text"
                value={formData.task_id || ''}
                onChange={(e) => setFormData({ ...formData, task_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date *</label>
                <input
                  type="date"
                  value={formData.date || ''}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Hours *</label>
                <input
                  type="number"
                  step="0.25"
                  value={formData.hours || ''}
                  onChange={(e) => setFormData({ ...formData, hours: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
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
                  checked={formData.billable ?? true}
                  onChange={(e) => setFormData({ ...formData, billable: e.target.checked })}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Billable</span>
              </label>
            </div>
          </>
        )

      default:
        return null
    }
  }

  const tabs = [
    { id: 'projects' as Tab, label: 'Projects', icon: Folder },
    { id: 'tasks' as Tab, label: 'Tasks', icon: CheckSquare },
    { id: 'resources' as Tab, label: 'Resources', icon: Users },
    { id: 'timesheets' as Tab, label: 'Timesheets', icon: Clock }
  ]

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Project Management</h1>
        <p className="text-gray-600 mt-2">Manage projects, tasks, resources, and timesheets</p>
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
            ? activeTab === 'projects'
              ? selectedItem.project_name
              : activeTab === 'tasks'
              ? selectedItem.task_name
              : activeTab === 'resources'
              ? selectedItem.resource_name
              : selectedItem.id
            : ''
        }
        isDeleting={isDeleting}
      />

      {/* Detail Modal */}
      <DetailModal
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        title={
          activeTab === 'projects' ? detailItem?.project_name :
          activeTab === 'tasks' ? detailItem?.task_name :
          activeTab === 'resources' ? detailItem?.resource_name :
          `${activeTab.slice(0, -1).charAt(0).toUpperCase() + activeTab.slice(1, -1)} Details`
        }
        subtitle={
          activeTab === 'projects' ? detailItem?.project_code :
          activeTab === 'tasks' ? `Project: ${detailItem?.project_id}` :
          undefined
        }
        fields={getDetailFields(detailItem)}
        onEdit={() => detailItem && handleEdit(detailItem)}
      />
    </div>
  )
}
