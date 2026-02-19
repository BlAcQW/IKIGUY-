/**
 * CRM Page - Customer Relationship Management
 *
 * Manages Customers, Leads, Opportunities, and Contacts with full CRUD operations.
 */

/* eslint-disable @typescript-eslint/no-unused-vars */
import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { Plus, Upload, UserCheck, DollarSign, TrendingUp, MessageSquare } from 'lucide-react'
import DataTable, { Column } from '@/components/DataTable'
import FormModal from '@/components/FormModal'
import DeleteConfirmation from '@/components/DeleteConfirmation'
import ContactBulkImportModal from '@/components/ContactBulkImportModal'
import ConversionModal from '@/components/ConversionModal'
import ActivityLogForm from '@/components/ActivityLogForm'
import ActivityTimeline from '@/components/ActivityTimeline'
import DetailModal, { DetailField } from '@/components/DetailModal'
import UserSelectDropdown from '@/components/UserSelectDropdown'
import { useAuth } from '@/contexts/AuthContext'
import { useOrganization } from '@/contexts/OrganizationContext'

type TabType = 'customers' | 'leads' | 'opportunities' | 'contacts'
type ConversionType = 'lead-to-opportunity' | 'lead-to-customer' | 'opportunity-to-customer' | 'mark-won'

export default function CRMPage() {
  const { user } = useAuth()
  const { currentOrganization } = useOrganization()
  const [activeTab, setActiveTab] = useState<TabType>('customers')
  const [data, setData] = useState<any[]>([])
  const [customers, setCustomers] = useState<any[]>([])
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [isImportOpen, setIsImportOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState<any>({})
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 10

  // Conversion and Activity state
  const [isConversionOpen, setIsConversionOpen] = useState(false)
  const [conversionType, setConversionType] = useState<ConversionType>('lead-to-opportunity')
  const [conversionItem, setConversionItem] = useState<any>(null)
  const [isActivityLogOpen, setIsActivityLogOpen] = useState(false)
  const [activityEntity, setActivityEntity] = useState<{ type: string; id: string } | null>(null)
  const [isTimelineOpen, setIsTimelineOpen] = useState(false)
  const [timelineEntity, _setTimelineEntity] = useState<{ type: string; id: string } | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [detailItem, setDetailItem] = useState<any>(null)

  useEffect(() => {
    fetchData()
  }, [activeTab, searchQuery, page])

  useEffect(() => {
    // Fetch customers for the contact form dropdown
    const fetchCustomers = async () => {
      try {
        const response = await api.get('/crm/customers?limit=1000')
        setCustomers(response.data)
      } catch (error) {
        console.error('Failed to fetch customers:', error)
      }
    }
    fetchCustomers()
  }, [])

  useEffect(() => {
    // Fetch organization users for lead/opportunity assignment
    const fetchUsers = async () => {
      try {
        if (currentOrganization?.id) {
          const response = await api.get(`/organizations/${currentOrganization.id}/users`)
          setUsers(response.data)
        }
      } catch (error) {
        console.error('Failed to fetch organization users:', error)
      }
    }
    fetchUsers()
  }, [currentOrganization])

  const fetchData = async () => {
    setLoading(true)
    try {
      const skip = (page - 1) * pageSize
      const endpoint = `/crm/${activeTab}`
      const params = new URLSearchParams({
        skip: skip.toString(),
        limit: pageSize.toString(),
        ...(searchQuery && { search: searchQuery })
      })

      const response = await api.get(`${endpoint}?${params}`)
      setData(response.data)
      setTotal(response.data.length) // In real app, backend should return total count
    } catch (error) {
      console.error(`Failed to fetch ${activeTab}:`, error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setSelectedItem(null)
    // Set default values based on tab
    const defaults: Record<TabType, any> = {
      customers: { customer_type: 'individual' },
      leads: { source: '', status: 'new' },
      opportunities: {
        stage: 'prospecting',
        probability: 10,
        assigned_to: user?.id || user?.email || ''
      },
      contacts: { is_primary: false }
    }
    setFormData(defaults[activeTab] || {})
    setIsModalOpen(true)
  }

  const handleEdit = (item: any) => {
    setSelectedItem(item)
    setFormData(item)
    setIsModalOpen(true)
  }

  const handleDelete = (item: any) => {
    setSelectedItem(item)
    setIsDeleteOpen(true)
  }

  const handleRowClick = (item: any) => {
    setDetailItem(item)
    setIsDetailOpen(true)
  }

  // Helper to get user display name from user ID
  const getUserDisplayName = (userId: string): string => {
    if (!userId) return '-'
    const user = users.find(u => u.user_id === userId)
    if (user) {
      if (user.display_name) return user.display_name
      if (user.first_name || user.last_name) {
        return `${user.first_name || ''} ${user.last_name || ''}`.trim()
      }
      return user.email
    }
    return userId // Fallback to ID if user not found
  }

  const getDetailFields = (item: any): DetailField[] => {
    if (!item) return []

    switch (activeTab) {
      case 'customers':
        return [
          { label: 'Company Name', value: item.company_name },
          { label: 'Contact Name', value: item.contact_name },
          { label: 'Email', value: item.email },
          { label: 'Phone', value: item.phone },
          { label: 'Address', value: item.address, fullWidth: true },
          { label: 'City', value: item.city },
          { label: 'Country', value: item.country },
          { label: 'Customer Type', value: item.customer_type },
          { label: 'Industry', value: item.industry },
          { label: 'Website', value: item.website, fullWidth: true },
          { label: 'Tags', value: item.tags },
          { label: 'Notes', value: item.notes, fullWidth: true },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
          { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
        ]
      case 'leads':
        return [
          { label: 'Name', value: item.name },
          { label: 'Email', value: item.email },
          { label: 'Phone', value: item.phone },
          { label: 'Company', value: item.company },
          { label: 'Source', value: item.source },
          { label: 'Status', value: item.status },
          { label: 'Score', value: item.score },
          { label: 'Assigned To', value: getUserDisplayName(item.assigned_to) },
          { label: 'Expected Revenue', value: item.expected_revenue },
          { label: 'Tags', value: item.tags },
          { label: 'Notes', value: item.notes, fullWidth: true },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
          { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
        ]
      case 'opportunities':
        return [
          { label: 'Name', value: item.name },
          { label: 'Customer ID', value: item.customer_id },
          { label: 'Amount', value: item.amount },
          { label: 'Stage', value: item.stage },
          { label: 'Probability', value: item.probability ? `${item.probability}%` : '-' },
          { label: 'Expected Close Date', value: item.expected_close_date },
          { label: 'Assigned To', value: getUserDisplayName(item.assigned_to) },
          { label: 'Lead Source', value: item.lead_source },
          { label: 'Description', value: item.description, fullWidth: true },
          { label: 'Tags', value: item.tags },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
          { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
        ]
      case 'contacts':
        return [
          { label: 'Name', value: item.name },
          { label: 'Email', value: item.email },
          { label: 'Phone', value: item.phone },
          { label: 'Position', value: item.position },
          { label: 'Customer ID', value: item.customer_id },
          { label: 'Is Primary', value: item.is_primary ? 'Yes' : 'No' },
          { label: 'LinkedIn', value: item.linkedin_url, fullWidth: true },
          { label: 'Notes', value: item.notes, fullWidth: true },
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
      const endpoint = `/crm/${activeTab}`
      if (selectedItem) {
        // Update
        await api.patch(`${endpoint}/${selectedItem.id}`, formData)
      } else {
        // Create
        await api.post(endpoint, formData)
      }
      setIsModalOpen(false)
      fetchData()
    } catch (error) {
      console.error('Failed to save:', error)
      alert('Failed to save. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleConfirmDelete = async () => {
    if (!selectedItem) return

    setIsSubmitting(true)
    try {
      await api.delete(`/crm/${activeTab}/${selectedItem.id}`)
      setIsDeleteOpen(false)
      fetchData()
    } catch (error) {
      console.error('Failed to delete:', error)
      alert('Failed to delete. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Conversion handlers
  const handleConvert = (item: any, type: ConversionType) => {
    setConversionItem(item)
    setConversionType(type)
    setIsConversionOpen(true)
  }

  const handleConversionSuccess = () => {
    setIsConversionOpen(false)
    fetchData()
  }

  // Activity handlers
  const handleLogActivity = (item: any, entityType: 'lead' | 'customer' | 'opportunity' | 'contact') => {
    setActivityEntity({ type: entityType, id: item.id })
    setIsActivityLogOpen(true)
  }

  const handleActivitySuccess = () => {
    setIsActivityLogOpen(false)
    fetchData() // Refresh to show updated activity counts
  }

  // Column definitions for each tab
  const columns: Record<TabType, Column<any>[]> = {
    customers: [
      {
        key: 'id',
        label: 'ID',
        render: (item) => (
          <span className="text-xs text-gray-600 font-mono" title={item.id}>
            {item.id?.substring(0, 8)}...
          </span>
        )
      },
      { key: 'company_name', label: 'Company', render: (item) => item.company_name || `${item.first_name} ${item.last_name}` },
      { key: 'email', label: 'Email' },
      { key: 'phone', label: 'Phone' },
      {
        key: 'customer_type',
        label: 'Type',
        render: (item) => (
          <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
            {item.customer_type}
          </span>
        )
      },
      {
        key: 'actions',
        label: 'Actions',
        render: (item) => (
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleLogActivity(item, 'customer')
            }}
            className="p-1 text-purple-600 hover:bg-purple-50 rounded"
            title="Log Activity"
          >
            <MessageSquare className="h-4 w-4" />
          </button>
        )
      }
    ],
    leads: [
      { key: 'name', label: 'Name', render: (item) => `${item.first_name} ${item.last_name}` },
      { key: 'email', label: 'Email' },
      { key: 'company', label: 'Company' },
      {
        key: 'status',
        label: 'Status',
        render: (item) => (
          <span className={`px-2 py-1 text-xs rounded-full ${
            item.status === 'qualified' ? 'bg-green-100 text-green-800' :
            item.status === 'new' ? 'bg-blue-100 text-blue-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {item.status}
          </span>
        )
      },
      { key: 'assigned_to', label: 'Assigned To', render: (item) => getUserDisplayName(item.assigned_to) },
      {
        key: 'actions',
        label: 'Quick Actions',
        render: (item) => (
          <div className="flex gap-1">
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleConvert(item, 'lead-to-opportunity')
              }}
              className="p-1 text-blue-600 hover:bg-blue-50 rounded"
              title="Convert to Opportunity"
            >
              <TrendingUp className="h-4 w-4" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleConvert(item, 'lead-to-customer')
              }}
              className="p-1 text-green-600 hover:bg-green-50 rounded"
              title="Convert to Customer"
            >
              <UserCheck className="h-4 w-4" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleLogActivity(item, 'lead')
              }}
              className="p-1 text-purple-600 hover:bg-purple-50 rounded"
              title="Log Activity"
            >
              <MessageSquare className="h-4 w-4" />
            </button>
          </div>
        )
      }
    ],
    opportunities: [
      { key: 'name', label: 'Name' },
      { key: 'amount', label: 'Amount', render: (item) => `$${item.amount?.toLocaleString()}` },
      {
        key: 'stage',
        label: 'Stage',
        render: (item) => (
          <span className={`px-2 py-1 text-xs rounded-full ${
            item.stage === 'closed_won' ? 'bg-green-100 text-green-800' :
            item.stage === 'closed_lost' ? 'bg-red-100 text-red-800' :
            'bg-blue-100 text-blue-800'
          }`}>
            {item.stage}
          </span>
        )
      },
      { key: 'probability', label: 'Probability', render: (item) => `${item.probability}%` },
      { key: 'assigned_to', label: 'Assigned To', render: (item) => getUserDisplayName(item.assigned_to) },
      {
        key: 'actions',
        label: 'Quick Actions',
        render: (item) => (
          <div className="flex gap-1">
            {item.stage !== 'closed_won' && item.stage !== 'closed_lost' && (
              <>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleConvert(item, 'mark-won')
                  }}
                  className="p-1 text-green-600 hover:bg-green-50 rounded"
                  title="Mark as Won"
                >
                  <DollarSign className="h-4 w-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleConvert(item, 'opportunity-to-customer')
                  }}
                  className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                  title="Convert to Customer"
                >
                  <UserCheck className="h-4 w-4" />
                </button>
              </>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleLogActivity(item, 'opportunity')
              }}
              className="p-1 text-purple-600 hover:bg-purple-50 rounded"
              title="Log Activity"
            >
              <MessageSquare className="h-4 w-4" />
            </button>
          </div>
        )
      }
    ],
    contacts: [
      { key: 'name', label: 'Name', render: (item) => `${item.first_name} ${item.last_name}` },
      { key: 'email', label: 'Email' },
      { key: 'phone', label: 'Phone' },
      {
        key: 'is_primary',
        label: 'Primary',
        render: (item) => item.is_primary ? (
          <span className="text-green-600">✓</span>
        ) : (
          <span className="text-gray-300">-</span>
        )
      },
      {
        key: 'actions',
        label: 'Actions',
        render: (item) => (
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleLogActivity(item, 'contact')
            }}
            className="p-1 text-purple-600 hover:bg-purple-50 rounded"
            title="Log Activity"
          >
            <MessageSquare className="h-4 w-4" />
          </button>
        )
      }
    ]
  }

  const renderForm = () => {
    switch (activeTab) {
      case 'customers':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                <input
                  type="text"
                  required
                  value={formData.first_name || ''}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                <input
                  type="text"
                  required
                  value={formData.last_name || ''}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
              <input
                type="email"
                required
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
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
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
              <input
                type="text"
                value={formData.company_name || ''}
                onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Customer Type *</label>
              <select
                required
                value={formData.customer_type || 'individual'}
                onChange={(e) => setFormData({ ...formData, customer_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="individual">Individual</option>
                <option value="business">Business</option>
              </select>
            </div>
          </div>
        )

      case 'leads':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                <input
                  type="text"
                  required
                  value={formData.first_name || ''}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                <input
                  type="text"
                  required
                  value={formData.last_name || ''}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
              <input
                type="email"
                required
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
              <input
                type="text"
                value={formData.company || ''}
                onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input
                type="tel"
                value={formData.phone || ''}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Lead Source *</label>
                <input
                  type="text"
                  required
                  value={formData.source || ''}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="e.g., Website, Referral, LinkedIn, Trade Show"
                />
                <p className="text-xs text-gray-500 mt-1">Enter where this lead came from</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={formData.status || 'new'}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="new">New</option>
                  <option value="contacted">Contacted</option>
                  <option value="qualified">Qualified</option>
                  <option value="unqualified">Unqualified</option>
                  <option value="converted">Converted</option>
                </select>
              </div>
            </div>
            <UserSelectDropdown
              users={users}
              value={formData.assigned_to || ''}
              onChange={(userId) => setFormData({ ...formData, assigned_to: userId })}
              label="Assigned To"
              placeholder="-- Unassigned --"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Score (0-100)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.score || ''}
                onChange={(e) => setFormData({ ...formData, score: parseInt(e.target.value) || undefined })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                rows={3}
                value={formData.notes || ''}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>
        )

      case 'opportunities':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input
                type="text"
                required
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                rows={3}
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount *</label>
                <input
                  type="number"
                  required
                  min="0"
                  step="0.01"
                  value={formData.amount || ''}
                  onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Probability %</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.probability || ''}
                  onChange={(e) => setFormData({ ...formData, probability: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stage</label>
              <select
                value={formData.stage || 'prospecting'}
                onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="prospecting">Prospecting</option>
                <option value="qualification">Qualification</option>
                <option value="proposal">Proposal</option>
                <option value="negotiation">Negotiation</option>
                <option value="closed_won">Closed Won</option>
                <option value="closed_lost">Closed Lost</option>
              </select>
            </div>
            <UserSelectDropdown
              users={users}
              value={formData.assigned_to || ''}
              onChange={(userId) => setFormData({ ...formData, assigned_to: userId })}
              label="Assigned To"
              placeholder="-- Select User --"
              required
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Expected Close Date</label>
              <input
                type="date"
                value={formData.expected_close_date ? new Date(formData.expected_close_date).toISOString().split('T')[0] : ''}
                onChange={(e) => setFormData({ ...formData, expected_close_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Next Step</label>
              <input
                type="text"
                value={formData.next_step || ''}
                onChange={(e) => setFormData({ ...formData, next_step: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="What's the next action?"
              />
            </div>
          </div>
        )

      case 'contacts':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Customer *</label>
              <select
                required
                value={formData.customer_id || ''}
                onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">Select a customer...</option>
                {customers.map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.company_name || `${customer.first_name} ${customer.last_name}`} ({customer.email})
                  </option>
                ))}
              </select>
              {customers.length === 0 && (
                <p className="mt-1 text-sm text-amber-600">
                  No customers found. Create a customer first before adding contacts.
                </p>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                <input
                  type="text"
                  required
                  value={formData.first_name || ''}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                <input
                  type="text"
                  required
                  value={formData.last_name || ''}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
              <input
                type="email"
                required
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="tel"
                  value={formData.phone || ''}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mobile</label>
                <input
                  type="tel"
                  value={formData.mobile || ''}
                  onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
                <input
                  type="text"
                  value={formData.job_title || ''}
                  onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
                <input
                  type="text"
                  value={formData.department || ''}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                rows={3}
                value={formData.notes || ''}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_primary"
                checked={formData.is_primary || false}
                onChange={(e) => setFormData({ ...formData, is_primary: e.target.checked })}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded"
              />
              <label htmlFor="is_primary" className="ml-2 block text-sm text-gray-700">
                Primary Contact
              </label>
            </div>
          </div>
        )
    }
  }

  const getItemName = (item: any) => {
    if (!item) return ''
    if (item.name) return item.name
    if (item.company_name) return item.company_name
    return `${item.first_name} ${item.last_name}`
  }

  return (
    <div className="w-full overflow-x-hidden">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Customer Relationship Management</h1>
        <div className="flex items-center space-x-3">
          {activeTab === 'contacts' && (
            <button
              onClick={() => setIsImportOpen(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              <Upload className="w-4 h-4" />
              <span>Import Contacts</span>
            </button>
          )}
          <button
            onClick={handleCreate}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            <span>New {activeTab.slice(0, -1)}</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {(['customers', 'leads', 'opportunities', 'contacts'] as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab)
                setPage(1)
                setSearchQuery('')
              }}
              className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Data Table */}
      <DataTable
        data={data}
        columns={columns[activeTab]}
        loading={loading}
        searchPlaceholder={`Search ${activeTab}...`}
        onSearch={setSearchQuery}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onRowClick={handleRowClick}
        pagination={{
          page,
          pageSize,
          total,
          onPageChange: setPage
        }}
        emptyMessage={`No ${activeTab} yet. Click "New ${activeTab.slice(0, -1)}" to add your first one.`}
      />

      {/* Form Modal */}
      <FormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={selectedItem ? `Edit ${activeTab.slice(0, -1)}` : `New ${activeTab.slice(0, -1)}`}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
      >
        {renderForm()}
      </FormModal>

      {/* Delete Confirmation */}
      <DeleteConfirmation
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        onConfirm={handleConfirmDelete}
        itemName={getItemName(selectedItem)}
        isDeleting={isSubmitting}
      />

      {/* Bulk Import Modal */}
      <ContactBulkImportModal
        isOpen={isImportOpen}
        onClose={() => setIsImportOpen(false)}
        onSuccess={() => {
          fetchData()
          setIsImportOpen(false)
        }}
      />

      {/* Conversion Modal */}
      {conversionItem && (
        <ConversionModal
          isOpen={isConversionOpen}
          onClose={() => setIsConversionOpen(false)}
          type={conversionType}
          item={conversionItem}
          onSuccess={handleConversionSuccess}
        />
      )}

      {/* Activity Log Form */}
      {activityEntity && (
        <ActivityLogForm
          isOpen={isActivityLogOpen}
          onClose={() => setIsActivityLogOpen(false)}
          entityType={activityEntity.type as 'lead' | 'customer' | 'opportunity' | 'contact'}
          entityId={activityEntity.id}
          onSuccess={handleActivitySuccess}
        />
      )}

      {/* Activity Timeline Modal */}
      {isTimelineOpen && timelineEntity && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setIsTimelineOpen(false)}></div>
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium leading-6 text-gray-900">
                    Activity Timeline
                  </h3>
                  <button
                    onClick={() => setIsTimelineOpen(false)}
                    className="rounded-md text-gray-400 hover:text-gray-500"
                  >
                    <span className="text-2xl">×</span>
                  </button>
                </div>
                <ActivityTimeline
                  entityType={timelineEntity.type as 'lead' | 'customer' | 'opportunity' | 'contact'}
                  entityId={timelineEntity.id}
                />
              </div>
            </div>
          </div>
        </div>
      )}

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
