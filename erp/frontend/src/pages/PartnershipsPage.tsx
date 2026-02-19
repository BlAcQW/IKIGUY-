/**
 * Partnerships Page - Partnership Management
 *
 * Manages partnerships, proposals, and interactions with full CRUD operations.
 */

/* eslint-disable @typescript-eslint/no-unused-vars */
import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { Plus, FileText, Users, TrendingUp } from 'lucide-react'
import DataTable, { Column } from '@/components/DataTable'
import FormModal from '@/components/FormModal'
import DeleteConfirmation from '@/components/DeleteConfirmation'
import Toast from '@/components/Toast'
import DetailModal, { DetailField } from '@/components/DetailModal'
import { useAuth } from '@/contexts/AuthContext'

type TabType = 'partnerships' | 'interactions' | 'stats'

export default function PartnershipsPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<TabType>('partnerships')
  const [partnerships, setPartnerships] = useState<any[]>([])
  const [interactions, setInteractions] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isInteractionModalOpen, setIsInteractionModalOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [selectedPartnership, setSelectedPartnership] = useState<any>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState<any>({})
  const [searchQuery, setSearchQuery] = useState('')
  const [stageFilter, setStageFilter] = useState<string>('')
  const [typeFilter, setTypeFilter] = useState<string>('')

  // File upload states
  const [proposalFiles, setProposalFiles] = useState<File[]>([])
  const [contractFiles, setContractFiles] = useState<File[]>([])
  const [documentFiles, setDocumentFiles] = useState<File[]>([])

  // Toast notification
  const [toastMessage, setToastMessage] = useState('')
  const [toastType, setToastType] = useState<'success' | 'error'>('success')
  const [showToast, setShowToast] = useState(false)

  // Detail modal
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [detailItem, setDetailItem] = useState<any>(null)

  useEffect(() => {
    if (activeTab === 'partnerships') {
      fetchPartnerships()
    } else if (activeTab === 'interactions') {
      fetchInteractions()
    } else if (activeTab === 'stats') {
      fetchStats()
    }
  }, [activeTab, searchQuery, stageFilter, typeFilter])

  const fetchPartnerships = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (searchQuery) params.append('search', searchQuery)
      if (stageFilter) params.append('stage', stageFilter)
      if (typeFilter) params.append('partnership_type', typeFilter)

      const response = await api.get(`/partnerships/partnerships?${params}`)
      setPartnerships(response.data)
    } catch (error) {
      console.error('Failed to fetch partnerships:', error)
      setToastMessage('Failed to fetch partnerships')
      setToastType('error')
      setShowToast(true)
    } finally {
      setLoading(false)
    }
  }

  const fetchInteractions = async () => {
    setLoading(true)
    try {
      // Get all partnerships first, then get interactions for all
      const partnershipsResponse = await api.get('/partnerships/partnerships?limit=1000')
      const allPartnerships = partnershipsResponse.data

      // For simplicity, we'll show interactions for a selected partnership
      // In a real app, you might want to show all interactions or have a filter
      setInteractions([])
      setPartnerships(allPartnerships)
    } catch (error) {
      console.error('Failed to fetch interactions:', error)
      setToastMessage('Failed to fetch interactions')
      setToastType('error')
      setShowToast(true)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    setLoading(true)
    try {
      const response = await api.get('/partnerships/partnerships/stats/summary')
      setStats(response.data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
      setToastMessage('Failed to fetch statistics')
      setToastType('error')
      setShowToast(true)
    } finally {
      setLoading(false)
    }
  }

  const fetchPartnershipInteractions = async (partnershipId: string) => {
    try {
      const response = await api.get(`/partnerships/partnerships/${partnershipId}/interactions`)
      setInteractions(response.data)
    } catch (error) {
      console.error('Failed to fetch partnership interactions:', error)
      setToastMessage('Failed to fetch interactions')
      setToastType('error')
      setShowToast(true)
    }
  }

  const handleCreate = () => {
    setSelectedItem(null)
    setFormData({
      partnership_type: 'strategic',
      stage: 'prospect',
      assigned_to: user?.id || user?.email || '',
    })
    setProposalFiles([])
    setContractFiles([])
    setDocumentFiles([])
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
    if (activeTab !== 'stats') {
      setDetailItem(item)
      setIsDetailOpen(true)
    }
  }

  const getDetailFields = (item: any): DetailField[] => {
    if (!item) return []

    switch (activeTab) {
      case 'partnerships':
        return [
          { label: 'Partner Name', value: item.partner_name },
          { label: 'Partnership Type', value: item.partnership_type },
          { label: 'Contact Person', value: item.contact_person || '-' },
          { label: 'Email', value: item.email || '-' },
          { label: 'Phone', value: item.phone || '-' },
          { label: 'Stage', value: item.stage },
          { label: 'Status', value: item.status },
          { label: 'Start Date', value: item.start_date || '-' },
          { label: 'End Date', value: item.end_date || '-' },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Terms', value: item.terms || '-', fullWidth: true },
          { label: 'Revenue Share %', value: item.revenue_share ? `${item.revenue_share}%` : '-' },
          { label: 'Contract Value', value: item.contract_value ? `GHS ${item.contract_value}` : '-' },
          { label: 'Proposal Files', value: item.proposal_files?.length > 0 ? item.proposal_files.join(', ') : '-', fullWidth: true },
          { label: 'Contract Files', value: item.contract_files?.length > 0 ? item.contract_files.join(', ') : '-', fullWidth: true },
          { label: 'Documents', value: item.documents?.length > 0 ? item.documents.join(', ') : '-', fullWidth: true },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
          { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
        ]
      case 'interactions':
        return [
          { label: 'Partnership ID', value: item.partnership_id },
          { label: 'Interaction Type', value: item.interaction_type },
          { label: 'Interaction Date', value: item.interaction_date },
          { label: 'Attendees', value: item.attendees || '-' },
          { label: 'Notes', value: item.notes || '-', fullWidth: true },
          { label: 'Follow Up Date', value: item.follow_up_date || '-' },
          { label: 'Follow Up Notes', value: item.follow_up_notes || '-', fullWidth: true },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' }
        ]
      default:
        return []
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      if (selectedItem) {
        // Update existing partnership
        await api.patch(`/partnerships/partnerships/${selectedItem.id}`, formData)
        setToastMessage('Partnership updated successfully')
        setToastType('success')
        setShowToast(true)
      } else {
        // Create new partnership
        const response = await api.post('/partnerships/partnerships', formData)
        const newPartnership = response.data

        // Upload files if any
        if (proposalFiles.length > 0) {
          for (const file of proposalFiles) {
            const formData = new FormData()
            formData.append('file', file)
            await api.post(`/partnerships/partnerships/${newPartnership.id}/upload-proposal`, formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
            })
          }
        }

        if (contractFiles.length > 0) {
          for (const file of contractFiles) {
            const formData = new FormData()
            formData.append('file', file)
            await api.post(`/partnerships/partnerships/${newPartnership.id}/upload-contract`, formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
            })
          }
        }

        if (documentFiles.length > 0) {
          for (const file of documentFiles) {
            const formData = new FormData()
            formData.append('file', file)
            await api.post(`/partnerships/partnerships/${newPartnership.id}/upload-document`, formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
            })
          }
        }

        setToastMessage('Partnership created successfully')
        setToastType('success')
        setShowToast(true)
      }

      setIsModalOpen(false)
      fetchPartnerships()
    } catch (error: any) {
      console.error('Failed to save partnership:', error)
      setToastMessage(error.response?.data?.detail || 'Failed to save partnership')
      setToastType('error')
      setShowToast(true)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteConfirm = async () => {
    try {
      await api.delete(`/partnerships/partnerships/${selectedItem.id}`)
      setToastMessage('Partnership deleted successfully')
      setToastType('success')
      setShowToast(true)
      setIsDeleteOpen(false)
      fetchPartnerships()
    } catch (error: any) {
      console.error('Failed to delete partnership:', error)
      setToastMessage(error.response?.data?.detail || 'Failed to delete partnership')
      setToastType('error')
      setShowToast(true)
    }
  }

  // Interaction handlers
  const handleCreateInteraction = (partnership: any) => {
    setSelectedPartnership(partnership)
    setFormData({
      partnership_id: partnership.id,
      interaction_type: 'email',
      interaction_date: new Date().toISOString().slice(0, 16),
      follow_up_required: false,
    })
    setIsInteractionModalOpen(true)
  }

  const handleSubmitInteraction = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await api.post('/partnerships/partnerships/interactions', formData)
      setToastMessage('Interaction recorded successfully')
      setToastType('success')
      setShowToast(true)
      setIsInteractionModalOpen(false)
      if (selectedPartnership) {
        fetchPartnershipInteractions(selectedPartnership.id)
      }
    } catch (error: any) {
      console.error('Failed to save interaction:', error)
      setToastMessage(error.response?.data?.detail || 'Failed to save interaction')
      setToastType('error')
      setShowToast(true)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Define columns for partnerships table
  const partnershipColumns: Column<any>[] = [
    {
      key: 'partner_name',
      label: 'Partner Name',
      sortable: true,
    },
    {
      key: 'partnership_type',
      label: 'Type',
      sortable: true,
      render: (value: any) => (
        <span className="capitalize">{value ? String(value).replace('_', ' ') : '-'}</span>
      ),
    },
    {
      key: 'stage',
      label: 'Stage',
      sortable: true,
      render: (value: any) => {
        const stageColors: Record<string, string> = {
          prospect: 'bg-gray-100 text-gray-800',
          initial_contact: 'bg-blue-100 text-blue-800',
          discussion: 'bg-indigo-100 text-indigo-800',
          proposal_sent: 'bg-purple-100 text-purple-800',
          negotiation: 'bg-yellow-100 text-yellow-800',
          agreement_signed: 'bg-green-100 text-green-800',
          active: 'bg-green-100 text-green-800',
          on_hold: 'bg-orange-100 text-orange-800',
          inactive: 'bg-gray-100 text-gray-800',
          terminated: 'bg-red-100 text-red-800',
        }
        return (
          <span className={`px-2 py-1 rounded text-xs font-medium ${stageColors[value] || 'bg-gray-100 text-gray-800'}`}>
            {value ? String(value).replace('_', ' ') : '-'}
          </span>
        )
      },
    },
    {
      key: 'primary_contact_name',
      label: 'Contact',
      sortable: true,
    },
    {
      key: 'expected_revenue',
      label: 'Expected Revenue',
      sortable: true,
      render: (value: any) => value ? `$${value.toLocaleString()}` : '-',
    },
    {
      key: 'interaction_count',
      label: 'Interactions',
      sortable: true,
    },
  ]

  // Define columns for interactions table
  const interactionColumns: Column<any>[] = [
    {
      key: 'interaction_date',
      label: 'Date',
      sortable: true,
      render: (value: any) => new Date(value).toLocaleDateString(),
    },
    {
      key: 'interaction_type',
      label: 'Type',
      sortable: true,
      render: (value: any) => (
        <span className="capitalize">{value ? String(value).replace('_', ' ') : '-'}</span>
      ),
    },
    {
      key: 'subject',
      label: 'Subject',
      sortable: true,
    },
    {
      key: 'description',
      label: 'Description',
      render: (value: any) => (
        <div className="truncate max-w-xs">{value || '-'}</div>
      ),
    },
    {
      key: 'follow_up_required',
      label: 'Follow-up',
      render: (value: any) => (
        <span className={`px-2 py-1 rounded text-xs font-medium ${value ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'}`}>
          {value ? 'Required' : 'No'}
        </span>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Partnership Management</h1>
          <p className="text-gray-600 mt-1">Track partnerships, proposals, and interactions</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'partnerships', label: 'Partnerships', icon: Users },
            { id: 'interactions', label: 'Interactions', icon: FileText },
            { id: 'stats', label: 'Statistics', icon: TrendingUp },
          ].map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Partnerships Tab */}
      {activeTab === 'partnerships' && (
        <div className="space-y-4">
          {/* Filters and Actions */}
          <div className="flex gap-4 items-center">
            <input
              type="text"
              placeholder="Search partnerships..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 px-4 py-2 border rounded-lg"
            />
            <select
              value={stageFilter}
              onChange={(e) => setStageFilter(e.target.value)}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Stages</option>
              <option value="prospect">Prospect</option>
              <option value="initial_contact">Initial Contact</option>
              <option value="discussion">Discussion</option>
              <option value="proposal_sent">Proposal Sent</option>
              <option value="negotiation">Negotiation</option>
              <option value="agreement_signed">Agreement Signed</option>
              <option value="active">Active</option>
              <option value="on_hold">On Hold</option>
              <option value="inactive">Inactive</option>
            </select>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Types</option>
              <option value="vendor">Vendor</option>
              <option value="technology">Technology</option>
              <option value="strategic">Strategic</option>
              <option value="reseller">Reseller</option>
              <option value="distributor">Distributor</option>
              <option value="affiliate">Affiliate</option>
              <option value="consulting">Consulting</option>
            </select>
            <button
              onClick={handleCreate}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center gap-2"
            >
              <Plus size={20} />
              New Partnership
            </button>
          </div>

          {/* Partnerships Table */}
          <DataTable
            columns={partnershipColumns}
            data={partnerships}
            loading={loading}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onRowClick={handleRowClick}
          />
        </div>
      )}

      {/* Interactions Tab */}
      {activeTab === 'interactions' && (
        <div className="space-y-4">
          {/* Partnership Selector */}
          <div className="flex gap-4 items-center">
            <select
              value={selectedPartnership?.id || ''}
              onChange={(e) => {
                const partnership = partnerships.find(p => p.id === e.target.value)
                setSelectedPartnership(partnership)
                if (partnership) {
                  fetchPartnershipInteractions(partnership.id)
                }
              }}
              className="flex-1 px-4 py-2 border rounded-lg"
            >
              <option value="">Select a partnership...</option>
              {partnerships.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.partner_name} ({p.partnership_type})
                </option>
              ))}
            </select>
            {selectedPartnership && (
              <button
                onClick={() => handleCreateInteraction(selectedPartnership)}
                className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center gap-2"
              >
                <Plus size={20} />
                Record Interaction
              </button>
            )}
          </div>

          {/* Interactions Table */}
          {selectedPartnership ? (
            <DataTable
              columns={interactionColumns}
              data={interactions}
              loading={loading}
              onRowClick={handleRowClick}
            />
          ) : (
            <div className="text-center py-12 text-gray-500">
              Select a partnership to view interactions
            </div>
          )}
        </div>
      )}

      {/* Statistics Tab */}
      {activeTab === 'stats' && stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Total Partnerships</h3>
            <p className="text-3xl font-bold text-blue-600">{stats.total_partnerships}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Expected Revenue</h3>
            <p className="text-3xl font-bold text-green-600">
              ${stats.total_expected_revenue?.toLocaleString() || 0}
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Actual Revenue</h3>
            <p className="text-3xl font-bold text-green-600">
              ${stats.total_actual_revenue?.toLocaleString() || 0}
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow col-span-full">
            <h3 className="text-lg font-semibold mb-4">By Stage</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(stats.by_stage || {}).map(([stage, count]) => (
                <div key={stage} className="text-center">
                  <p className="text-2xl font-bold">{count as number}</p>
                  <p className="text-sm text-gray-600 capitalize">{stage ? String(stage).replace('_', ' ') : '-'}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow col-span-full">
            <h3 className="text-lg font-semibold mb-4">By Type</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(stats.by_type || {}).map(([type, count]) => (
                <div key={type} className="text-center">
                  <p className="text-2xl font-bold">{count as number}</p>
                  <p className="text-sm text-gray-600 capitalize">{type ? String(type).replace('_', ' ') : '-'}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Recent Interactions (30 days)</h3>
            <p className="text-3xl font-bold text-purple-600">{stats.recent_interactions_30_days}</p>
          </div>
        </div>
      )}

      {/* Partnership Form Modal */}
      <FormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={selectedItem ? 'Edit Partnership' : 'Create Partnership'}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Basic Information */}
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Partner Name *
            </label>
            <input
              type="text"
              required
              value={formData.partner_name || ''}
              onChange={(e) => setFormData({ ...formData, partner_name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Partnership Type *
            </label>
            <select
              required
              value={formData.partnership_type || 'strategic'}
              onChange={(e) => setFormData({ ...formData, partnership_type: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="vendor">Vendor</option>
              <option value="technology">Technology</option>
              <option value="strategic">Strategic</option>
              <option value="reseller">Reseller</option>
              <option value="distributor">Distributor</option>
              <option value="affiliate">Affiliate</option>
              <option value="consulting">Consulting</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Stage *
            </label>
            <select
              required
              value={formData.stage || 'prospect'}
              onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="prospect">Prospect</option>
              <option value="initial_contact">Initial Contact</option>
              <option value="discussion">Discussion</option>
              <option value="proposal_sent">Proposal Sent</option>
              <option value="negotiation">Negotiation</option>
              <option value="agreement_signed">Agreement Signed</option>
              <option value="active">Active</option>
              <option value="on_hold">On Hold</option>
              <option value="inactive">Inactive</option>
              <option value="terminated">Terminated</option>
            </select>
          </div>

          {/* Primary Contact */}
          <div className="col-span-2 border-t pt-4 mt-4">
            <h3 className="font-semibold mb-3">Primary Contact</h3>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contact Name
            </label>
            <input
              type="text"
              value={formData.primary_contact_name || ''}
              onChange={(e) => setFormData({ ...formData, primary_contact_name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contact Email
            </label>
            <input
              type="email"
              value={formData.primary_contact_email || ''}
              onChange={(e) => setFormData({ ...formData, primary_contact_email: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contact Phone
            </label>
            <input
              type="tel"
              value={formData.primary_contact_phone || ''}
              onChange={(e) => setFormData({ ...formData, primary_contact_phone: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contact Title
            </label>
            <input
              type="text"
              value={formData.primary_contact_title || ''}
              onChange={(e) => setFormData({ ...formData, primary_contact_title: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          {/* Partnership Details */}
          <div className="col-span-2 border-t pt-4 mt-4">
            <h3 className="font-semibold mb-3">Partnership Details</h3>
          </div>

          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Value Proposition
            </label>
            <textarea
              value={formData.value_proposition || ''}
              onChange={(e) => setFormData({ ...formData, value_proposition: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Expected Revenue ($)
            </label>
            <input
              type="number"
              value={formData.expected_revenue || ''}
              onChange={(e) => setFormData({ ...formData, expected_revenue: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Industry
            </label>
            <input
              type="text"
              value={formData.industry || ''}
              onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          {/* Proposal */}
          <div className="col-span-2 border-t pt-4 mt-4">
            <h3 className="font-semibold mb-3">Proposal</h3>
          </div>

          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Proposal Title
            </label>
            <input
              type="text"
              value={formData.proposal_title || ''}
              onChange={(e) => setFormData({ ...formData, proposal_title: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Proposal Content
            </label>
            <textarea
              value={formData.proposal_content || ''}
              onChange={(e) => setFormData({ ...formData, proposal_content: e.target.value })}
              rows={5}
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="Type your proposal content here..."
            />
          </div>

          {!selectedItem && (
            <>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Upload Proposal Files
                </label>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.ppt,.pptx"
                  onChange={(e) => setProposalFiles(Array.from(e.target.files || []))}
                  className="w-full px-3 py-2 border rounded-lg"
                />
                {proposalFiles.length > 0 && (
                  <div className="mt-2 text-sm text-gray-600">
                    {proposalFiles.length} file(s) selected
                  </div>
                )}
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Upload Contract Files
                </label>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => setContractFiles(Array.from(e.target.files || []))}
                  className="w-full px-3 py-2 border rounded-lg"
                />
                {contractFiles.length > 0 && (
                  <div className="mt-2 text-sm text-gray-600">
                    {contractFiles.length} file(s) selected
                  </div>
                )}
              </div>
            </>
          )}

          {/* Dates */}
          <div className="col-span-2 border-t pt-4 mt-4">
            <h3 className="font-semibold mb-3">Important Dates</h3>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              First Contact Date
            </label>
            <input
              type="date"
              value={formData.first_contact_date?.split('T')[0] || ''}
              onChange={(e) => setFormData({ ...formData, first_contact_date: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Agreement Start Date
            </label>
            <input
              type="date"
              value={formData.agreement_start_date?.split('T')[0] || ''}
              onChange={(e) => setFormData({ ...formData, agreement_start_date: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Agreement End Date
            </label>
            <input
              type="date"
              value={formData.agreement_end_date?.split('T')[0] || ''}
              onChange={(e) => setFormData({ ...formData, agreement_end_date: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          {/* Management */}
          <div className="col-span-2 border-t pt-4 mt-4">
            <h3 className="font-semibold mb-3">Management</h3>
          </div>

          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status Notes
            </label>
            <textarea
              value={formData.status_notes || ''}
              onChange={(e) => setFormData({ ...formData, status_notes: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Next Action
            </label>
            <input
              type="text"
              value={formData.next_action || ''}
              onChange={(e) => setFormData({ ...formData, next_action: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="e.g., Follow up with proposal, Schedule demo call"
            />
          </div>
        </div>
      </FormModal>

      {/* Interaction Form Modal */}
      <FormModal
        isOpen={isInteractionModalOpen}
        onClose={() => setIsInteractionModalOpen(false)}
        title="Record Interaction"
        onSubmit={handleSubmitInteraction}
        isSubmitting={isSubmitting}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Interaction Type *
            </label>
            <select
              required
              value={formData.interaction_type || 'email'}
              onChange={(e) => setFormData({ ...formData, interaction_type: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="email">Email</option>
              <option value="phone_call">Phone Call</option>
              <option value="meeting">Meeting</option>
              <option value="video_call">Video Call</option>
              <option value="proposal_sent">Proposal Sent</option>
              <option value="proposal_received">Proposal Received</option>
              <option value="contract_review">Contract Review</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subject *
            </label>
            <input
              type="text"
              required
              value={formData.subject || ''}
              onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Interaction Date *
            </label>
            <input
              type="datetime-local"
              required
              value={formData.interaction_date || ''}
              onChange={(e) => setFormData({ ...formData, interaction_date: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.follow_up_required || false}
                onChange={(e) => setFormData({ ...formData, follow_up_required: e.target.checked })}
                className="rounded"
              />
              <span className="text-sm font-medium text-gray-700">Follow-up Required</span>
            </label>
          </div>

          {formData.follow_up_required && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Follow-up Date
              </label>
              <input
                type="datetime-local"
                value={formData.follow_up_date || ''}
                onChange={(e) => setFormData({ ...formData, follow_up_date: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              value={formData.notes || ''}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
        </div>
      </FormModal>

      {/* Delete Confirmation */}
      <DeleteConfirmation
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        onConfirm={handleDeleteConfirm}
        itemName={selectedItem?.partner_name || 'partnership'}
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
        title={`${activeTab === 'partnerships' ? 'Partnership' : 'Interaction'} Details`}
        fields={getDetailFields(detailItem)}
        onEdit={() => detailItem && handleEdit(detailItem)}
      />
    </div>
  )
}
