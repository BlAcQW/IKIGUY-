/**
 * OnboardingPage Component
 *
 * Full interface for Employee Onboarding Management:
 * - Create onboarding records for new employees
 * - Track onboarding progress by department
 * - Manage department-specific onboarding templates
 * - Update task completion status
 * - View onboarding statistics
 */

import { useState, useEffect } from 'react'
import {
  Users,
  CheckCircle,
  Clock,
  Plus,
  Settings,
  TrendingUp,
  FileText,
  AlertCircle,
  Calendar
} from 'lucide-react'
import DataTable, { Column } from '../components/DataTable'
import FormModal from '../components/FormModal'
import DeleteConfirmation from '../components/DeleteConfirmation'
import Toast from '../components/Toast'
import DetailModal, { DetailField } from '../components/DetailModal'
import GenerateNDAModal from '../components/GenerateNDAModal'
import api from '../services/api'

type Tab = 'onboardings' | 'templates' | 'stats'

interface OnboardingTask {
  task_id: string
  title: string
  description: string
  category: string
  status: 'pending' | 'in_progress' | 'completed' | 'skipped'
  due_date?: string
  completed_date?: string
  completed_by?: string
  assigned_to?: string
  order: number
  notes?: string
  attachments?: string[]
}

interface Onboarding {
  id: string
  employee_id: string
  first_name: string
  last_name: string
  email: string
  department: string
  position: string
  start_date: string
  onboarding_status: 'not_started' | 'in_progress' | 'completed' | 'on_hold'
  expected_completion_date?: string
  actual_completion_date?: string
  manager_id?: string
  buddy_id?: string
  hr_coordinator_id?: string
  tasks: OnboardingTask[]
  total_tasks: number
  completed_tasks: number
  progress_percentage: number
  welcome_kit_sent: boolean
  equipment_issued: boolean
  email_account_created: boolean
  system_access_granted: boolean
}

interface OnboardingTemplate {
  id: string
  template_name: string
  department: string
  position_type?: string
  description?: string
  tasks: OnboardingTask[]
  estimated_days: number
  welcome_kit_items: string[]
  standard_equipment: string[]
  required_systems: string[]
  required_training: Array<{ name: string; duration: string }>
  is_active: boolean
}

interface Department {
  id: string
  name: string
  code: string
}

interface Stats {
  total: number
  not_started: number
  in_progress: number
  completed: number
  on_hold: number
  upcoming: number
}

export default function OnboardingPage() {
  const [activeTab, setActiveTab] = useState<Tab>('onboardings')
  const [onboardings, setOnboardings] = useState<Onboarding[]>([])
  const [templates, setTemplates] = useState<OnboardingTemplate[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [employees, setEmployees] = useState<any[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [isNDAModalOpen, setIsNDAModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [formData, setFormData] = useState<any>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  // Toast notification
  const [toastMessage, setToastMessage] = useState('')
  const [toastType, setToastType] = useState<'success' | 'error'>('success')
  const [showToast, setShowToast] = useState(false)

  // Pagination
  const [page, setPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const pageSize = 10

  useEffect(() => {
    fetchDepartments()
    fetchStats()
  }, [])

  useEffect(() => {
    if (activeTab === 'onboardings') {
      fetchOnboardings()
    } else if (activeTab === 'templates') {
      fetchTemplates()
    }
  }, [activeTab, page, searchQuery])

  const fetchDepartments = async () => {
    try {
      const response = await api.get('/system/departments', {
        params: { limit: 1000 }
      })
      setDepartments(response.data)
    } catch (error) {
      console.error('Failed to fetch departments:', error)
    }
  }

  const fetchEmployees = async () => {
    try {
      const response = await api.get('/hr/employees', {
        params: { skip: 0, limit: 1000 }
      })
      setEmployees(response.data)
    } catch (error) {
      console.error('Failed to fetch employees:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await api.get('/onboarding/stats/overview')
      setStats(response.data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  const fetchOnboardings = async () => {
    setLoading(true)
    try {
      const skip = (page - 1) * pageSize
      const response = await api.get('/onboarding', {
        params: { skip, limit: pageSize, search: searchQuery || undefined }
      })
      setOnboardings(response.data)
      setTotalItems(response.data.length)
    } catch (error) {
      console.error('Failed to fetch onboardings:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchTemplates = async () => {
    setLoading(true)
    try {
      const skip = (page - 1) * pageSize
      const response = await api.get('/onboarding/templates', {
        params: { skip, limit: pageSize }
      })
      setTemplates(response.data)
      setTotalItems(response.data.length)
    } catch (error) {
      console.error('Failed to fetch templates:', error)
    } finally {
      setLoading(false)
    }
  }

  const initializeDefaultTemplates = async () => {
    try {
      setIsSubmitting(true)
      await api.post('/onboarding/init-default-templates')
      setToastMessage('Default templates initialized successfully!')
      setToastType('success')
      setShowToast(true)
      fetchTemplates()
    } catch (error) {
      console.error('Failed to initialize templates:', error)
      setToastMessage('Failed to initialize templates')
      setToastType('error')
      setShowToast(true)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEmployeeSelect = (employeeId: string) => {
    const employee = employees.find(emp => emp.id === employeeId)
    if (employee) {
      setFormData({
        ...formData,
        selected_employee_id: employeeId,
        employee_id: employee.id,
        first_name: employee.first_name,
        last_name: employee.last_name,
        email: employee.email,
        department: employee.department || '',
        position: employee.position || ''
      })
    }
  }

  const handleCreate = async () => {
    setSelectedItem(null)
    if (activeTab === 'onboardings') {
      // Fetch employees for the employee selector
      await fetchEmployees()
      setFormData({
        selected_employee_id: '',
        first_name: '',
        last_name: '',
        email: '',
        department: '',
        position: '',
        start_date: new Date().toISOString().split('T')[0],
        employee_id: '',
        manager_id: '',
        buddy_id: '',
        hr_coordinator_id: ''
      })
    } else if (activeTab === 'templates') {
      setFormData({
        template_name: '',
        department: '',
        description: '',
        estimated_days: 30,
        tasks: []
      })
    }
    setIsModalOpen(true)
  }

  const handleViewDetails = async (item: Onboarding) => {
    setSelectedItem(item)
    setIsDetailModalOpen(true)
  }

  const handleRowClick = (item: any) => {
    if (activeTab === 'onboardings') {
      handleViewDetails(item)
    } else if (activeTab === 'templates') {
      setSelectedItem(item)
      setIsDetailModalOpen(true)
    }
    // stats tab doesn't have clickable rows
  }

  const getDetailFields = (item: any): DetailField[] => {
    if (!item) return []

    if (activeTab === 'templates') {
      return [
        { label: 'Template Name', value: item.template_name },
        { label: 'Department', value: item.department },
        { label: 'Position Type', value: item.position_type || '-' },
        { label: 'Description', value: item.description || '-', fullWidth: true },
        { label: 'Estimated Days', value: `${item.estimated_days} days` },
        { label: 'Is Active', value: item.is_active ? 'Yes' : 'No' },
        { label: 'Welcome Kit Items', value: item.welcome_kit_items?.join(', ') || '-', fullWidth: true },
        { label: 'Standard Equipment', value: item.standard_equipment?.join(', ') || '-', fullWidth: true },
        { label: 'Required Systems', value: item.required_systems?.join(', ') || '-', fullWidth: true },
        { label: 'Required Training', value: item.required_training?.map((t: any) => `${t.name} (${t.duration})`).join(', ') || '-', fullWidth: true },
        { label: 'Total Tasks', value: item.tasks?.length.toString() || '0' },
        { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
        { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
      ]
    }
    return []
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const endpoint = activeTab === 'templates' ? '/onboarding/templates' : '/onboarding'

      if (selectedItem) {
        await api.patch(`${endpoint}/${selectedItem.id}`, formData)
        setToastMessage(`${activeTab === 'templates' ? 'Template' : 'Onboarding'} updated successfully!`)
      } else {
        await api.post(endpoint, formData)
        setToastMessage(`${activeTab === 'templates' ? 'Template' : 'Onboarding'} created successfully!`)
      }

      setToastType('success')
      setShowToast(true)
      setIsModalOpen(false)
      setFormData({})

      if (activeTab === 'onboardings') {
        fetchOnboardings()
        fetchStats()
      } else {
        fetchTemplates()
      }
    } catch (error) {
      console.error('Failed to save:', error)
      setToastMessage('Failed to save. Please try again.')
      setToastType('error')
      setShowToast(true)
    } finally {
      setIsSubmitting(false)
    }
  }

  const confirmDelete = async () => {
    if (!selectedItem) return

    setIsDeleting(true)
    try {
      const endpoint = activeTab === 'templates' ? '/onboarding/templates' : '/onboarding'
      await api.delete(`${endpoint}/${selectedItem.id}`)
      setIsDeleteModalOpen(false)
      setSelectedItem(null)

      if (activeTab === 'onboardings') {
        fetchOnboardings()
        fetchStats()
      } else {
        fetchTemplates()
      }

      setToastMessage('Deleted successfully!')
      setToastType('success')
      setShowToast(true)
    } catch (error) {
      console.error('Failed to delete:', error)
      setToastMessage('Failed to delete. Please try again.')
      setToastType('error')
      setShowToast(true)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleTaskUpdate = async (onboardingId: string, taskId: string, status: string) => {
    try {
      await api.patch(`/onboarding/${onboardingId}/tasks/${taskId}`, { status })
      setToastMessage('Task updated successfully!')
      setToastType('success')
      setShowToast(true)

      // Refresh the detail view
      const response = await api.get(`/onboarding/${onboardingId}`)
      setSelectedItem(response.data)

      // Refresh list and stats
      fetchOnboardings()
      fetchStats()
    } catch (error) {
      console.error('Failed to update task:', error)
      setToastMessage('Failed to update task')
      setToastType('error')
      setShowToast(true)
    }
  }

  const getOnboardingColumns = (): Column<Onboarding>[] => [
    {
      key: 'first_name',
      label: 'Employee',
      render: (item: Onboarding) => (
        <div>
          <div className="font-medium">{item.first_name} {item.last_name}</div>
          <div className="text-xs text-gray-500">{item.email}</div>
        </div>
      )
    },
    { key: 'department', label: 'Department' },
    { key: 'position', label: 'Position' },
    {
      key: 'start_date',
      label: 'Start Date',
      render: (item: Onboarding) => new Date(item.start_date).toLocaleDateString()
    },
    {
      key: 'progress_percentage',
      label: 'Progress',
      render: (item: Onboarding) => (
        <div className="w-full">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium">{Math.round(item.progress_percentage)}%</span>
            <span className="text-xs text-gray-500">{item.completed_tasks}/{item.total_tasks}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${item.progress_percentage}%` }}
            />
          </div>
        </div>
      )
    },
    {
      key: 'onboarding_status',
      label: 'Status',
      render: (item: Onboarding) => (
        <span className={`px-2 py-1 rounded-full text-xs ${
          item.onboarding_status === 'completed' ? 'bg-green-100 text-green-800' :
          item.onboarding_status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
          item.onboarding_status === 'on_hold' ? 'bg-yellow-100 text-yellow-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {item.onboarding_status.replace('_', ' ')}
        </span>
      )
    }
  ]

  const getTemplateColumns = (): Column<OnboardingTemplate>[] => [
    { key: 'template_name', label: 'Template Name' },
    { key: 'department', label: 'Department' },
    {
      key: 'estimated_days',
      label: 'Duration',
      render: (item: OnboardingTemplate) => `${item.estimated_days} days`
    },
    {
      key: 'tasks',
      label: 'Tasks',
      render: (item: OnboardingTemplate) => `${item.tasks.length} tasks`
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (item: OnboardingTemplate) => (
        <span className={`px-2 py-1 rounded-full text-xs ${
          item.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
        }`}>
          {item.is_active ? 'Active' : 'Inactive'}
        </span>
      )
    }
  ]

  const renderForm = () => {
    if (activeTab === 'onboardings') {
      // Show only employee selector for new onboarding
      if (!selectedItem) {
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select Employee *
              </label>
              <select
                value={formData.selected_employee_id || ''}
                onChange={(e) => handleEmployeeSelect(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Choose an employee...</option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.first_name} {emp.last_name} - {emp.email} ({emp.department || 'No Dept'})
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Employee details will be automatically populated
              </p>
            </div>

            {/* Show employee details once selected */}
            {formData.selected_employee_id && (
              <div className="bg-gray-50 p-4 rounded-md space-y-2">
                <h3 className="font-medium text-gray-900 mb-2">Employee Details</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Name:</span>
                    <span className="ml-2 font-medium">{formData.first_name} {formData.last_name}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Email:</span>
                    <span className="ml-2 font-medium">{formData.email}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Department:</span>
                    <span className="ml-2 font-medium">{formData.department || '-'}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Position:</span>
                    <span className="ml-2 font-medium">{formData.position || '-'}</span>
                  </div>
                </div>
              </div>
            )}

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
                disabled={!formData.selected_employee_id}
              />
            </div>

            <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded-md">
              <p><strong>Note:</strong> Onboarding tasks will be automatically populated based on the department template.</p>
            </div>
          </>
        )
      }

      // Show full form for editing existing onboarding
      return (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                First Name *
              </label>
              <input
                type="text"
                value={formData.first_name || ''}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Last Name *
              </label>
              <input
                type="text"
                value={formData.last_name || ''}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
            <input
              type="email"
              value={formData.email || ''}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Department *
              </label>
              <input
                type="text"
                value={formData.department || ''}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Position *
              </label>
              <input
                type="text"
                value={formData.position || ''}
                onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

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
        </>
      )
    } else if (activeTab === 'templates') {
      return (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Template Name *
            </label>
            <input
              type="text"
              value={formData.template_name || ''}
              onChange={(e) => setFormData({ ...formData, template_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Department *
            </label>
            <select
              value={formData.department || ''}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select Department</option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.name}>
                  {dept.name}
                </option>
              ))}
            </select>
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
              Estimated Duration (days) *
            </label>
            <input
              type="number"
              value={formData.estimated_days || 30}
              onChange={(e) => setFormData({ ...formData, estimated_days: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
        </>
      )
    }
  }

  const renderDetailView = () => {
    if (!selectedItem) return null

    const onboarding = selectedItem as Onboarding

    return (
      <div className="space-y-6">
        {/* Employee Info */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold">Employee Information</h3>
            <button
              onClick={() => setIsNDAModalOpen(true)}
              className="flex items-center px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
            >
              <FileText className="w-4 h-4 mr-1" />
              Generate NDA
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Name</p>
              <p className="font-medium">{onboarding.first_name} {onboarding.last_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Email</p>
              <p className="font-medium">{onboarding.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Department</p>
              <p className="font-medium">{onboarding.department}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Position</p>
              <p className="font-medium">{onboarding.position}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Start Date</p>
              <p className="font-medium">{new Date(onboarding.start_date).toLocaleDateString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <span className={`inline-block px-2 py-1 rounded-full text-xs ${
                onboarding.onboarding_status === 'completed' ? 'bg-green-100 text-green-800' :
                onboarding.onboarding_status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                onboarding.onboarding_status === 'on_hold' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {onboarding.onboarding_status.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>

        {/* Progress */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold mb-3">Progress</h3>
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl font-bold">{Math.round(onboarding.progress_percentage)}%</span>
            <span className="text-gray-600">{onboarding.completed_tasks} of {onboarding.total_tasks} tasks completed</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-blue-600 h-4 rounded-full transition-all"
              style={{ width: `${onboarding.progress_percentage}%` }}
            />
          </div>
        </div>

        {/* Tasks Checklist */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Onboarding Tasks</h3>
          <div className="space-y-2">
            {onboarding.tasks.map((task) => (
              <div
                key={task.task_id}
                className={`p-4 border rounded-lg ${
                  task.status === 'completed' ? 'bg-green-50 border-green-200' :
                  task.status === 'in_progress' ? 'bg-blue-50 border-blue-200' :
                  'bg-white border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={task.status === 'completed'}
                        onChange={() => handleTaskUpdate(
                          onboarding.id,
                          task.task_id,
                          task.status === 'completed' ? 'pending' : 'completed'
                        )}
                        className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                      />
                      <div>
                        <h4 className={`font-medium ${task.status === 'completed' ? 'line-through text-gray-500' : ''}`}>
                          {task.title}
                        </h4>
                        <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                          <span className="px-2 py-1 bg-gray-100 rounded">{task.category}</span>
                          {task.due_date && (
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              Due: {new Date(task.due_date).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${
                    task.status === 'completed' ? 'bg-green-100 text-green-800' :
                    task.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                    task.status === 'skipped' ? 'bg-gray-100 text-gray-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {task.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Additional Info */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium mb-2">Welcome Kit</h4>
            <p className={`text-sm ${onboarding.welcome_kit_sent ? 'text-green-600' : 'text-gray-600'}`}>
              {onboarding.welcome_kit_sent ? '✓ Sent' : '✗ Not Sent'}
            </p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium mb-2">Equipment</h4>
            <p className={`text-sm ${onboarding.equipment_issued ? 'text-green-600' : 'text-gray-600'}`}>
              {onboarding.equipment_issued ? '✓ Issued' : '✗ Not Issued'}
            </p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium mb-2">Email Account</h4>
            <p className={`text-sm ${onboarding.email_account_created ? 'text-green-600' : 'text-gray-600'}`}>
              {onboarding.email_account_created ? '✓ Created' : '✗ Not Created'}
            </p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium mb-2">System Access</h4>
            <p className={`text-sm ${onboarding.system_access_granted ? 'text-green-600' : 'text-gray-600'}`}>
              {onboarding.system_access_granted ? '✓ Granted' : '✗ Not Granted'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  const renderStatsView = () => {
    if (!stats) return <div>Loading stats...</div>

    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-600">Total Onboardings</h3>
            <Users className="w-8 h-8 text-blue-600" />
          </div>
          <p className="text-3xl font-bold">{stats.total}</p>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-600">In Progress</h3>
            <Clock className="w-8 h-8 text-blue-600" />
          </div>
          <p className="text-3xl font-bold">{stats.in_progress}</p>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-600">Completed</h3>
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <p className="text-3xl font-bold">{stats.completed}</p>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-600">Not Started</h3>
            <AlertCircle className="w-8 h-8 text-gray-600" />
          </div>
          <p className="text-3xl font-bold">{stats.not_started}</p>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-600">On Hold</h3>
            <AlertCircle className="w-8 h-8 text-yellow-600" />
          </div>
          <p className="text-3xl font-bold">{stats.on_hold}</p>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-600">Upcoming (30 days)</h3>
            <TrendingUp className="w-8 h-8 text-blue-600" />
          </div>
          <p className="text-3xl font-bold">{stats.upcoming}</p>
        </div>
      </div>
    )
  }

  const tabs = [
    { id: 'onboardings' as Tab, label: 'Onboardings', icon: Users },
    { id: 'templates' as Tab, label: 'Templates', icon: FileText },
    { id: 'stats' as Tab, label: 'Statistics', icon: TrendingUp }
  ]

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Employee Onboarding</h1>
        <p className="text-gray-600 mt-2">Manage employee onboarding by department</p>
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

      {/* Content based on active tab */}
      {activeTab === 'stats' ? (
        renderStatsView()
      ) : (
        <>
          {/* Action Buttons */}
          <div className="mb-4 flex justify-between items-center">
            <div>
              {activeTab === 'templates' && (
                <button
                  onClick={initializeDefaultTemplates}
                  disabled={isSubmitting}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  <Settings className="w-4 h-4 mr-2" />
                  Initialize Default Templates
                </button>
              )}
            </div>
            <button
              onClick={handleCreate}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add {activeTab === 'templates' ? 'Template' : 'Onboarding'}
            </button>
          </div>

          {/* Data Table */}
          <DataTable
            data={activeTab === 'onboardings' ? onboardings : templates as any}
            columns={activeTab === 'onboardings' ? getOnboardingColumns() : getTemplateColumns() as any}
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
        </>
      )}

      {/* Create/Edit Modal */}
      <FormModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setFormData({})
        }}
        title={`${selectedItem ? 'Edit' : 'Create'} ${activeTab === 'templates' ? 'Template' : 'Onboarding'}`}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
      >
        <div className="space-y-4">{renderForm()}</div>
      </FormModal>

      {/* Detail View Modal - For Onboardings (interactive) */}
      {activeTab === 'onboardings' && (
        <FormModal
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false)
            setSelectedItem(null)
          }}
          title="Onboarding Details"
        >
          {renderDetailView()}
        </FormModal>
      )}

      {/* Detail Modal - For Templates (read-only) */}
      {activeTab === 'templates' && (
        <DetailModal
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false)
            setSelectedItem(null)
          }}
          title="Template Details"
          fields={getDetailFields(selectedItem)}
          onEdit={() => selectedItem && handleEdit(selectedItem)}
        />
      )}

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
            ? activeTab === 'onboardings'
              ? `${selectedItem.first_name} ${selectedItem.last_name}'s onboarding`
              : selectedItem.template_name
            : ''
        }
        isDeleting={isDeleting}
      />

      {/* Generate NDA Modal */}
      <GenerateNDAModal
        isOpen={isNDAModalOpen}
        onClose={() => setIsNDAModalOpen(false)}
        employee={selectedItem ? {
          employee_id: selectedItem.employee_id,
          first_name: selectedItem.first_name,
          last_name: selectedItem.last_name,
          email: selectedItem.email,
          position: selectedItem.position,
          start_date: selectedItem.start_date
        } : null}
        onSuccess={() => {
          // Refresh the onboarding data after NDA is generated
          if (selectedItem) {
            fetchOnboardings()
            setToastMessage('NDA generated successfully!')
            setToastType('success')
            setShowToast(true)
          }
        }}
      />

      {/* Toast Notification */}
      <Toast
        message={toastMessage}
        type={toastType}
        isOpen={showToast}
        onClose={() => setShowToast(false)}
      />
    </div>
  )
}
