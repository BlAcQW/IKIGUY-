/**
 * HRPage Component
 *
 * Full CRUD interface for HR Management:
 * - Employees: Manage employee records
 * - Payroll: Track payroll records
 * - Benefits: Manage employee benefits
 * - Recruitment: Manage job openings and candidates
 */

import { useState, useEffect } from 'react'
import { Users, DollarSign, Heart, Briefcase, Plus, Building2, Upload, X } from 'lucide-react'
import DataTable, { Column } from '../components/DataTable'
import FormModal from '../components/FormModal'
import DeleteConfirmation from '../components/DeleteConfirmation'
import Toast from '../components/Toast'
import DetailModal, { DetailField } from '../components/DetailModal'
import api from '../services/api'

type Tab = 'employees' | 'payroll' | 'benefits' | 'recruitment' | 'settings'

interface Employee {
  id: string
  employee_id: string
  first_name: string
  last_name: string
  email: string
  phone?: string
  position: string
  department: string
  hire_date: string
  employment_status: string
  salary?: number
  currency?: string
  manager_id?: string
  cv_url?: string
  certificates?: Array<{
    name: string
    url: string
    uploaded_at: string
  }>
}

interface Payroll {
  id: string
  employee_id: string
  period_start: string
  period_end: string
  gross_pay: number
  deductions: number
  net_pay: number
  status: string
  payment_date?: string
}

interface Benefit {
  id: string
  name: string
  description?: string
  benefit_type: string
  provider?: string
  cost_per_employee: number
  employer_contribution: number
  employee_contribution: number
  is_active: boolean
}

interface Recruitment {
  id: string
  job_title: string
  department: string
  description?: string
  requirements?: string[]
  status: string
  hiring_manager_id?: string
  posted_date: string
  application_deadline?: string
  salary_range?: string
}

interface Department {
  id: string
  name: string
  code: string
  description?: string
}

export default function HRPage() {
  const [activeTab, setActiveTab] = useState<Tab>('employees')
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [formData, setFormData] = useState<any>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [departments, setDepartments] = useState<Department[]>([])
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [detailItem, setDetailItem] = useState<any>(null)

  // File upload state
  const [cvFile, setCvFile] = useState<File | null>(null)
  const [certificateFiles, setCertificateFiles] = useState<Array<{ name: string; file: File }>>([])
  const [certificateName, setCertificateName] = useState('')

  // Toast notification
  const [toastMessage, setToastMessage] = useState('')
  const [toastType, setToastType] = useState<'success' | 'error'>('success')
  const [showToast, setShowToast] = useState(false)

  // Pagination
  const [page, setPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const pageSize = 10

  // Fetch departments on mount
  useEffect(() => {
    fetchDepartments()
  }, [])

  useEffect(() => {
    fetchData()
  }, [activeTab, page, searchQuery])

  const fetchData = async () => {
    setLoading(true)
    try {
      const skip = (page - 1) * pageSize
      const endpoint = activeTab === 'settings' ? '/system/departments' : `/hr/${activeTab}`
      const response = await api.get(endpoint, {
        params: { skip, limit: pageSize, search: searchQuery || undefined }
      })
      setData(response.data)
      // For simplicity, assuming total is data.length (in real app, backend should return total count)
      setTotalItems(response.data.length)

      // Update departments list if we're on settings tab
      if (activeTab === 'settings') {
        setDepartments(response.data)
      }
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

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
      case 'employees':
        return [
          { label: 'Employee ID', value: item.employee_id },
          { label: 'First Name', value: item.first_name },
          { label: 'Last Name', value: item.last_name },
          { label: 'Email', value: item.email },
          { label: 'Phone', value: item.phone || '-' },
          { label: 'Position', value: item.position },
          { label: 'Department', value: item.department },
          { label: 'Hire Date', value: item.hire_date },
          { label: 'Employment Status', value: item.employment_status },
          { label: 'Salary', value: item.salary ? `${item.currency || 'GHS'} ${item.salary}` : '-' },
          { label: 'Manager ID', value: item.manager_id || '-' },
          { label: 'CV URL', value: item.cv_url || '-', fullWidth: true },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
          { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
        ]
      case 'payroll':
        return [
          { label: 'Employee ID', value: item.employee_id },
          { label: 'Period Start', value: item.period_start },
          { label: 'Period End', value: item.period_end },
          { label: 'Gross Pay', value: `GHS ${item.gross_pay}` },
          { label: 'Deductions', value: `GHS ${item.deductions}` },
          { label: 'Net Pay', value: `GHS ${item.net_pay}` },
          { label: 'Status', value: item.status },
          { label: 'Payment Date', value: item.payment_date || '-' },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' }
        ]
      case 'benefits':
        return [
          { label: 'Benefit Name', value: item.name },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Benefit Type', value: item.benefit_type },
          { label: 'Provider', value: item.provider || '-' },
          { label: 'Cost Per Employee', value: `GHS ${item.cost_per_employee}` },
          { label: 'Employer Contribution', value: `GHS ${item.employer_contribution}` },
          { label: 'Employee Contribution', value: `GHS ${item.employee_contribution}` },
          { label: 'Is Active', value: item.is_active ? 'Yes' : 'No' },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' }
        ]
      case 'recruitment':
        return [
          { label: 'Job Title', value: item.job_title },
          { label: 'Department', value: item.department },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Requirements', value: item.requirements ? item.requirements.join(', ') : '-', fullWidth: true },
          { label: 'Status', value: item.status },
          { label: 'Hiring Manager ID', value: item.hiring_manager_id || '-' },
          { label: 'Posted Date', value: item.posted_date },
          { label: 'Application Deadline', value: item.application_deadline || '-' },
          { label: 'Salary Range', value: item.salary_range || '-' },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' }
        ]
      case 'settings':
        return [
          { label: 'Department Name', value: item.name },
          { label: 'Code', value: item.code },
          { label: 'Description', value: item.description || '-', fullWidth: true },
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
      const endpoint = activeTab === 'settings' ? '/system/departments' : `/hr/${activeTab}`
      let response

      if (selectedItem) {
        response = await api.patch(`${endpoint}/${selectedItem.id}`, formData)
      } else {
        response = await api.post(endpoint, formData)
      }

      // Handle employee-specific file uploads and toast notifications
      if (activeTab === 'employees') {
        const employeeData = response.data
        const employeeId = employeeData.employee?.id || employeeData.id

        // Show toast for email creation status
        if (employeeData.email_account) {
          if (employeeData.email_account.email_created) {
            setToastMessage(`Employee created successfully! Email account created: ${employeeData.email_account.temporary_password}`)
            setToastType('success')
            setShowToast(true)
          } else if (employeeData.email_account.email_error) {
            setToastMessage(`Employee created, but email creation failed: ${employeeData.email_account.email_error}`)
            setToastType('error')
            setShowToast(true)
          }
        }

        // Upload CV if selected
        if (cvFile && employeeId) {
          try {
            const cvFormData = new FormData()
            cvFormData.append('file', cvFile)
            await api.post(`/hr/employees/${employeeId}/upload-cv`, cvFormData, {
              headers: { 'Content-Type': 'multipart/form-data' }
            })
            setToastMessage('CV uploaded successfully!')
            setToastType('success')
            setShowToast(true)
          } catch (error) {
            console.error('Failed to upload CV:', error)
            setToastMessage('Failed to upload CV')
            setToastType('error')
            setShowToast(true)
          }
        }

        // Upload certificates if selected
        for (const cert of certificateFiles) {
          try {
            const certFormData = new FormData()
            certFormData.append('file', cert.file)
            await api.post(
              `/hr/employees/${employeeId}/upload-certificate?certificate_name=${encodeURIComponent(cert.name)}`,
              certFormData,
              { headers: { 'Content-Type': 'multipart/form-data' } }
            )
          } catch (error) {
            console.error(`Failed to upload certificate ${cert.name}:`, error)
          }
        }

        // Reset file upload state
        setCvFile(null)
        setCertificateFiles([])
        setCertificateName('')
      }

      setIsModalOpen(false)
      setFormData({})
      fetchData()

      // Refresh departments list if we modified one
      if (activeTab === 'settings') {
        fetchDepartments()
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
      const endpoint = activeTab === 'settings' ? '/system/departments' : `/hr/${activeTab}`
      await api.delete(`${endpoint}/${selectedItem.id}`)
      setIsDeleteModalOpen(false)
      setSelectedItem(null)
      fetchData()

      // Refresh departments list if we deleted one
      if (activeTab === 'settings') {
        fetchDepartments()
      }
    } catch (error) {
      console.error('Failed to delete:', error)
      alert('Failed to delete. Please try again.')
    } finally {
      setIsDeleting(false)
    }
  }

  const getEmptyFormData = () => {
    switch (activeTab) {
      case 'employees':
        return {
          first_name: '',
          last_name: '',
          email: '',
          phone: '',
          position: '',
          department: '',
          hire_date: new Date().toISOString().split('T')[0],
          employment_status: 'active',
          salary: 0,
          currency: 'GHS'
        }
      case 'payroll':
        return {
          employee_id: '',
          period_start: new Date().toISOString().split('T')[0],
          period_end: new Date().toISOString().split('T')[0],
          gross_pay: 0,
          deductions: 0,
          net_pay: 0,
          status: 'pending'
        }
      case 'benefits':
        return {
          name: '',
          description: '',
          benefit_type: 'health',
          provider: '',
          cost_per_employee: 0,
          employer_contribution: 0,
          employee_contribution: 0,
          is_active: true
        }
      case 'recruitment':
        return {
          job_title: '',
          department: '',
          description: '',
          requirements: [],
          status: 'open',
          posted_date: new Date().toISOString().split('T')[0],
          salary_range: ''
        }
      case 'settings':
        return {
          name: '',
          description: '',
          currency: 'GHS',
          budget_amount: 0
        }
      default:
        return {}
    }
  }

  const getColumns = (): Column<any>[] => {
    switch (activeTab) {
      case 'employees':
        return [
          { key: 'employee_id', label: 'Employee ID' },
          { key: 'first_name', label: 'First Name' },
          { key: 'last_name', label: 'Last Name' },
          { key: 'email', label: 'Email' },
          { key: 'position', label: 'Position' },
          { key: 'department', label: 'Department' },
          {
            key: 'employment_status',
            label: 'Status',
            render: (item: Employee) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.employment_status === 'active' ? 'bg-green-100 text-green-800' :
                item.employment_status === 'on_leave' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {item.employment_status?.replace('_', ' ')}
              </span>
            )
          }
        ]
      case 'payroll':
        return [
          { key: 'employee_id', label: 'Employee ID' },
          { key: 'period_start', label: 'Period Start' },
          { key: 'period_end', label: 'Period End' },
          {
            key: 'gross_pay',
            label: 'Gross Pay',
            render: (item: Payroll) => item.gross_pay != null ? `$${item.gross_pay.toFixed(2)}` : '$0.00'
          },
          {
            key: 'net_pay',
            label: 'Net Pay',
            render: (item: Payroll) => item.net_pay != null ? `$${item.net_pay.toFixed(2)}` : '$0.00'
          },
          {
            key: 'status',
            label: 'Status',
            render: (item: Payroll) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.status === 'paid' ? 'bg-green-100 text-green-800' :
                item.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {item.status}
              </span>
            )
          }
        ]
      case 'benefits':
        return [
          { key: 'name', label: 'Benefit Name' },
          { key: 'benefit_type', label: 'Type' },
          { key: 'provider', label: 'Provider' },
          {
            key: 'cost_per_employee',
            label: 'Cost/Employee',
            render: (item: Benefit) => item.cost_per_employee != null ? `$${item.cost_per_employee.toFixed(2)}` : '$0.00'
          },
          {
            key: 'is_active',
            label: 'Status',
            render: (item: Benefit) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {item.is_active ? 'Active' : 'Inactive'}
              </span>
            )
          }
        ]
      case 'recruitment':
        return [
          { key: 'job_title', label: 'Job Title' },
          { key: 'department', label: 'Department' },
          { key: 'posted_date', label: 'Posted Date' },
          { key: 'salary_range', label: 'Salary Range' },
          {
            key: 'status',
            label: 'Status',
            render: (item: Recruitment) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.status === 'open' ? 'bg-green-100 text-green-800' :
                item.status === 'closed' ? 'bg-gray-100 text-gray-800' :
                'bg-blue-100 text-blue-800'
              }`}>
                {item.status}
              </span>
            )
          }
        ]
      case 'settings':
        return [
          { key: 'name', label: 'Department Name' },
          { key: 'code', label: 'Code' },
          { key: 'description', label: 'Description' },
          {
            key: 'budget_amount',
            label: 'Budget',
            render: (item: Department & { budget_amount?: number }) =>
              item.budget_amount != null ? `$${item.budget_amount.toFixed(2)}` : 'N/A'
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
      case 'employees':
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input
                type="tel"
                value={formData.phone || ''}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Hire Date *
                </label>
                <input
                  type="date"
                  value={formData.hire_date || ''}
                  onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status *</label>
                <select
                  value={formData.employment_status || 'active'}
                  onChange={(e) => setFormData({ ...formData, employment_status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="active">Active</option>
                  <option value="on_leave">On Leave</option>
                  <option value="terminated">Terminated</option>
                  <option value="retired">Retired</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Salary *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.salary || ''}
                  onChange={(e) => setFormData({ ...formData, salary: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Currency *</label>
                <select
                  value={formData.currency || 'GHS'}
                  onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="GHS">GHS</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                  <option value="JPY">JPY</option>
                </select>
              </div>
            </div>

            {/* File Upload Section */}
            <div className="border-t pt-4 mt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Documents</h3>

              {/* CV Upload */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Upload CV (PDF, DOC, DOCX)
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setCvFile(e.target.files[0])
                      }
                    }}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                  {cvFile && (
                    <button
                      type="button"
                      onClick={() => setCvFile(null)}
                      className="px-2 py-2 text-red-600 hover:bg-red-50 rounded-md"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
                {cvFile && (
                  <p className="text-xs text-gray-500 mt-1">Selected: {cvFile.name}</p>
                )}
              </div>

              {/* Certificate Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Upload Certificates (PDF, JPG, PNG)
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    placeholder="Certificate name (e.g., Bachelor's Degree)"
                    value={certificateName}
                    onChange={(e) => setCertificateName(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                  <label className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer flex items-center gap-2">
                    <Upload className="w-4 h-4" />
                    <span className="text-sm">Add</span>
                    <input
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0] && certificateName) {
                          setCertificateFiles([
                            ...certificateFiles,
                            { name: certificateName, file: e.target.files[0] }
                          ])
                          setCertificateName('')
                        } else if (!certificateName) {
                          alert('Please enter a certificate name first')
                        }
                      }}
                    />
                  </label>
                </div>

                {/* List of selected certificates */}
                {certificateFiles.length > 0 && (
                  <div className="space-y-1">
                    {certificateFiles.map((cert, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded-md"
                      >
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-700">{cert.name}</p>
                          <p className="text-xs text-gray-500">{cert.file.name}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            setCertificateFiles(certificateFiles.filter((_, i) => i !== index))
                          }}
                          className="px-2 py-1 text-red-600 hover:bg-red-50 rounded-md"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </>
        )

      case 'payroll':
        return (
          <>
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Period Start *
                </label>
                <input
                  type="date"
                  value={formData.period_start || ''}
                  onChange={(e) => setFormData({ ...formData, period_start: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Period End *
                </label>
                <input
                  type="date"
                  value={formData.period_end || ''}
                  onChange={(e) => setFormData({ ...formData, period_end: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gross Pay *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.gross_pay || ''}
                  onChange={(e) => setFormData({ ...formData, gross_pay: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Deductions *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.deductions || ''}
                  onChange={(e) => setFormData({ ...formData, deductions: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Net Pay *</label>
              <input
                type="number"
                step="0.01"
                value={formData.net_pay || ''}
                onChange={(e) => setFormData({ ...formData, net_pay: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status *</label>
              <select
                value={formData.status || 'pending'}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="pending">Pending</option>
                <option value="processing">Processing</option>
                <option value="paid">Paid</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Payment Date
              </label>
              <input
                type="date"
                value={formData.payment_date || ''}
                onChange={(e) => setFormData({ ...formData, payment_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </>
        )

      case 'benefits':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Benefit Name *
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
                <select
                  value={formData.benefit_type || 'health'}
                  onChange={(e) => setFormData({ ...formData, benefit_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="health">Health</option>
                  <option value="dental">Dental</option>
                  <option value="vision">Vision</option>
                  <option value="retirement">Retirement</option>
                  <option value="life_insurance">Life Insurance</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                <input
                  type="text"
                  value={formData.provider || ''}
                  onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cost/Employee *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.cost_per_employee || ''}
                  onChange={(e) => setFormData({ ...formData, cost_per_employee: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Employer Share *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.employer_contribution || ''}
                  onChange={(e) => setFormData({ ...formData, employer_contribution: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Employee Share *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.employee_contribution || ''}
                  onChange={(e) => setFormData({ ...formData, employee_contribution: parseFloat(e.target.value) })}
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

      case 'recruitment':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Job Title *
              </label>
              <input
                type="text"
                value={formData.job_title || ''}
                onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Posted Date *
                </label>
                <input
                  type="date"
                  value={formData.posted_date || ''}
                  onChange={(e) => setFormData({ ...formData, posted_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Application Deadline
                </label>
                <input
                  type="date"
                  value={formData.application_deadline || ''}
                  onChange={(e) => setFormData({ ...formData, application_deadline: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Salary Range
                </label>
                <input
                  type="text"
                  placeholder="e.g., $60,000 - $80,000"
                  value={formData.salary_range || ''}
                  onChange={(e) => setFormData({ ...formData, salary_range: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status *</label>
                <select
                  value={formData.status || 'open'}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="open">Open</option>
                  <option value="in_progress">In Progress</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
            </div>
          </>
        )

      case 'settings':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Department Name *
              </label>
              <input
                type="text"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Department code will be auto-generated based on the name
              </p>
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
                  Budget Amount
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.budget_amount || ''}
                  onChange={(e) => setFormData({ ...formData, budget_amount: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
                <select
                  value={formData.currency || 'GHS'}
                  onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="GHS">GHS</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                  <option value="JPY">JPY</option>
                </select>
              </div>
            </div>
          </>
        )

      default:
        return null
    }
  }

  const tabs = [
    { id: 'employees' as Tab, label: 'Employees', icon: Users },
    { id: 'payroll' as Tab, label: 'Payroll', icon: DollarSign },
    { id: 'benefits' as Tab, label: 'Benefits', icon: Heart },
    { id: 'recruitment' as Tab, label: 'Recruitment', icon: Briefcase },
    { id: 'settings' as Tab, label: 'Departments', icon: Building2 }
  ]

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Human Resources</h1>
        <p className="text-gray-600 mt-2">Manage employees, payroll, benefits, and recruitment</p>
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
            ? activeTab === 'employees'
              ? `${selectedItem.first_name} ${selectedItem.last_name}`
              : activeTab === 'benefits'
              ? selectedItem.name
              : activeTab === 'recruitment'
              ? selectedItem.job_title
              : selectedItem.id
            : ''
        }
        isDeleting={isDeleting}
      />

      {/* Toast Notification */}
      <Toast
        message={toastMessage}
        type={toastType}
        isOpen={showToast}
        onClose={() => setShowToast(false)}
      />

      {/* Detail Modal */}
      <DetailModal
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        title={`${activeTab.slice(0, -1).charAt(0).toUpperCase() + activeTab.slice(1, -1)} Details`}
        fields={getDetailFields(detailItem)}
        onEdit={() => detailItem && handleEdit(detailItem)}
      />
    </div>
  )
}
