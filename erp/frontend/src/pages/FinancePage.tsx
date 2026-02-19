/**
 * FinancePage Component
 *
 * Full CRUD interface for Finance & Accounting:
 * - Accounts: Manage chart of accounts
 * - Transactions: Track financial transactions
 * - Invoices: Manage customer invoices
 * - Expenses: Track business expenses
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { Wallet, ArrowRightLeft, FileText, Receipt, Plus, PieChart, BarChart3, Upload, Camera, X, Repeat, ChevronDown } from 'lucide-react'
import DataTable, { Column } from '../components/DataTable'
import FormModal from '../components/FormModal'
import DeleteConfirmation from '../components/DeleteConfirmation'
import Toast from '../components/Toast'
import DetailModal, { DetailField } from '../components/DetailModal'
import FileUpload, { UploadResult } from '../components/FileUpload'
import ConfirmExtractedData, { ExpenseFormData } from '../components/ConfirmExtractedData'
import ReceiptUploadModal from '../components/ReceiptUploadModal'
import api from '../services/api'

type Tab = 'accounts' | 'transactions' | 'invoices' | 'expenses' | 'recurring' | 'budgets' | 'reports'

interface Account {
  id: string
  account_number: string
  account_name: string
  account_type: string
  balance: number
  currency: string
  is_active: boolean
}

interface Transaction {
  id: string
  transaction_date: string
  transaction_type: string
  amount: number
  account_id: string
  category?: string
  description?: string
  reference_number?: string
}

interface Invoice {
  id: string
  invoice_number: string
  customer_id: string
  issue_date: string
  due_date: string
  total_amount: number
  status: string
  payment_terms?: string
}

interface Expense {
  id: string
  expense_date: string
  category: string
  amount: number
  merchant?: string
  vendor?: string
  description?: string
  payment_method?: string
  status: string
  receipt_urls?: string[]
  tax_amount?: number
  currency?: string
  receipt_number?: string
  notes?: string
  created_by?: string
  approved_by?: string
  approver_name?: string
  approved_date?: string
  rejection_reason?: string
  payable_to?: string
  is_reimbursable?: boolean
  reimbursed?: boolean
  reimbursement_date?: string
  // Recurring expense fields
  is_recurring?: boolean
  recurrence_frequency?: 'daily' | 'weekly' | 'biweekly' | 'monthly' | 'quarterly' | 'yearly'
  recurrence_start_date?: string
  recurrence_end_date?: string
  recurrence_day_of_month?: number
  recurrence_day_of_week?: number
  parent_recurring_id?: string
  next_occurrence_date?: string
  auto_approve?: boolean
  include_in_budget?: boolean
  budget_id?: string
}

interface BudgetLineItem {
  account_id: string
  account_name: string
  account_type: string
  budgeted_amount: number
  notes?: string
}

interface Budget {
  id: string
  name: string
  fiscal_year: number
  period: string
  period_start: string
  period_end: string
  status: string
  line_items: BudgetLineItem[]
  total_revenue_budget: number
  total_expense_budget: number
  total_profit_budget: number
  currency: string
}

interface UserPermissions {
  user_id: string
  email: string
  organization_id: string
  is_admin: boolean
  is_approver: boolean
  can_approve: boolean
}

export default function FinancePage() {
  const [activeTab, setActiveTab] = useState<Tab>('accounts')
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [formData, setFormData] = useState<any>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [userPermissions, setUserPermissions] = useState<UserPermissions | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [detailItem, setDetailItem] = useState<any>(null)

  // Pagination (for non-expenses tabs)
  const [page, setPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const pageSize = 10

  // Infinite scroll for expenses
  const [expensesPage, setExpensesPage] = useState(1)
  const [hasMoreExpenses, setHasMoreExpenses] = useState(true)
  const [loadingMoreExpenses, setLoadingMoreExpenses] = useState(false)
  const observerTarget = useRef<HTMLDivElement>(null)

  // Drag and drop state
  const [isDragging, setIsDragging] = useState(false)

  // Reports state
  const [reportType, setReportType] = useState<'profit-loss' | 'balance-sheet' | 'budget-vs-actual'>('profit-loss')
  const [reportData, setReportData] = useState<any>(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportParams, setReportParams] = useState({
    period_start: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    period_end: new Date().toISOString().split('T')[0],
    as_of_date: new Date().toISOString().split('T')[0],
    budget_id: ''
  })

  // Toast state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  // PDF Upload state
  const [showConfirmation, setShowConfirmation] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)

  // Receipt upload modal and dropdown states
  const [isReceiptModalOpen, setIsReceiptModalOpen] = useState(false)
  const [showAddDropdown, setShowAddDropdown] = useState(false)

  // Customers dropdown state
  const [customers, setCustomers] = useState<any[]>([])
  const [loadingCustomers, setLoadingCustomers] = useState(false)

  // Accounts dropdown state (for budget line items)
  const [accountsList, setAccountsList] = useState<Account[]>([])
  const [loadingAccounts, setLoadingAccounts] = useState(false)

  useEffect(() => {
    // Reset expenses state when switching tabs or changing search
    if (activeTab === 'expenses') {
      setExpensesPage(1)
      setHasMoreExpenses(true)
      setData([])
    }
    fetchData()
  }, [activeTab, page, searchQuery])

  // Reset expenses when search changes
  useEffect(() => {
    if (activeTab === 'expenses') {
      setExpensesPage(1)
      setHasMoreExpenses(true)
      setData([])
    }
  }, [searchQuery, activeTab])

  useEffect(() => {
    fetchUserPermissions()
  }, [])

  const fetchUserPermissions = async () => {
    try {
      const response = await api.get('/finance/user/permissions')
      setUserPermissions(response.data)
    } catch (error) {
      console.error('Failed to fetch user permissions:', error)
    }
  }

  const fetchData = async (isLoadingMore = false) => {
    // Skip fetching for reports tab
    if (activeTab === 'reports') {
      setData([])
      return
    }

    // For expenses and recurring with infinite scroll/pagination
    if (activeTab === 'expenses' || activeTab === 'recurring') {
      if (isLoadingMore) {
        setLoadingMoreExpenses(true)
      } else {
        setLoading(true)
      }

      try {
        const currentPage = isLoadingMore ? expensesPage : 1
        const skip = (currentPage - 1) * pageSize
        const fetchEndpoint = activeTab === 'recurring' ? '/finance/recurring-expenses' : `/finance/${activeTab}`
        const response = await api.get(fetchEndpoint, {
          params: { skip, limit: pageSize, search: searchQuery || undefined }
        })
        
        if (response.data && response.data.items) {
          if (isLoadingMore) {
            // Append new items for infinite scroll
            setData(prev => {
              const newData = [...prev, ...response.data.items]
              // Check if there are more items to load
              setHasMoreExpenses(newData.length < response.data.total)
              return newData
            })
          } else {
            // Replace items for initial load or search
            setData(response.data.items)
            // Check if there are more items to load
            setHasMoreExpenses(response.data.items.length < response.data.total)
          }
          
          setTotalItems(response.data.total)
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        if (isLoadingMore) {
          setLoadingMoreExpenses(false)
        } else {
          setLoading(false)
        }
      }
    } else {
      // Regular pagination for other tabs (accounts, transactions, invoices, budgets)
      setLoading(true)
      try {
        const skip = (page - 1) * pageSize
        const response = await api.get(`/finance/${activeTab}`, {
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
  }

  // Load more expenses when scrolling to bottom
  const loadMoreExpenses = useCallback(async () => {
    if (activeTab === 'expenses' && hasMoreExpenses && !loadingMoreExpenses && !loading) {
      const nextPage = expensesPage + 1
      setExpensesPage(nextPage)
      setLoadingMoreExpenses(true)
      
      try {
        const skip = (nextPage - 1) * pageSize
        const response = await api.get(`/finance/expenses`, {
          params: { skip, limit: pageSize, search: searchQuery || undefined }
        })
        
        if (response.data && response.data.items) {
          setData(prevData => {
            const newData = [...prevData, ...response.data.items]
            setHasMoreExpenses(newData.length < response.data.total)
            return newData
          })
          setTotalItems(response.data.total)
        }
      } catch (error) {
        console.error('Failed to load more expenses:', error)
      } finally {
        setLoadingMoreExpenses(false)
      }
    }
  }, [activeTab, hasMoreExpenses, loadingMoreExpenses, loading, expensesPage, pageSize, searchQuery])

  // Intersection Observer for infinite scroll
  useEffect(() => {
    if (activeTab !== 'expenses') return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMoreExpenses && !loadingMoreExpenses) {
          loadMoreExpenses()
        }
      },
      { threshold: 0.1 }
    )

    const currentTarget = observerTarget.current
    if (currentTarget) {
      observer.observe(currentTarget)
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget)
      }
    }
  }, [activeTab, hasMoreExpenses, loadingMoreExpenses, loadMoreExpenses])

  const fetchCustomers = async () => {
    if (activeTab !== 'invoices') return

    setLoadingCustomers(true)
    try {
      const response = await api.get('/crm/customers', {
        params: { limit: 1000 } // Get all customers
      })
      setCustomers(response.data)
    } catch (error) {
      console.error('Failed to fetch customers:', error)
      setToast({ message: 'Failed to load customers', type: 'error' })
    } finally {
      setLoadingCustomers(false)
    }
  }

  const fetchAccountsForBudget = async () => {
    if (accountsList.length > 0) return // Already loaded

    setLoadingAccounts(true)
    try {
      const response = await api.get('/finance/accounts', {
        params: { limit: 1000 } // Get all accounts
      })
      setAccountsList(response.data)
    } catch (error) {
      console.error('Failed to fetch accounts:', error)
      setToast({ message: 'Failed to load accounts', type: 'error' })
    } finally {
      setLoadingAccounts(false)
    }
  }

  const handleCreate = async () => {
    setSelectedItem(null)
    setFormData(getEmptyFormData())

    // Fetch customers if creating an invoice
    if (activeTab === 'invoices') {
      await fetchCustomers()
    }

    // Fetch accounts if creating a budget
    if (activeTab === 'budgets') {
      await fetchAccountsForBudget()
    }

    setIsModalOpen(true)
  }

  const handleRowClick = (item: any) => {
    if (activeTab === 'expenses') {
      setSelectedItem(item)
      setIsDetailsModalOpen(true)
    } else if (activeTab !== 'reports') {
      setDetailItem(item)
      setIsDetailOpen(true)
    }
  }

  const getDetailFields = (item: any): DetailField[] => {
    if (!item) return []

    switch (activeTab) {
      case 'accounts':
        return [
          { label: 'Account Number', value: item.account_number },
          { label: 'Account Name', value: item.account_name },
          { label: 'Account Type', value: item.account_type },
          { label: 'Balance', value: `${item.currency || 'GHS'} ${item.balance?.toFixed(2) || '0.00'}` },
          { label: 'Currency', value: item.currency || 'GHS' },
          { label: 'Is Active', value: item.is_active ? 'Yes' : 'No' },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Parent Account', value: item.parent_account_id || '-' },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' },
          { label: 'Updated At', value: item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }
        ]
      case 'transactions':
        return [
          { label: 'Transaction Date', value: new Date(item.transaction_date).toLocaleDateString() },
          { label: 'Transaction Type', value: item.transaction_type },
          { label: 'Amount', value: `GHS ${item.amount?.toFixed(2) || '0.00'}` },
          { label: 'Account ID', value: item.account_id },
          { label: 'Category', value: item.category || '-' },
          { label: 'Reference Number', value: item.reference_number || '-' },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' }
        ]
      case 'invoices':
        return [
          { label: 'Invoice Number', value: item.invoice_number },
          { label: 'Customer ID', value: item.customer_id },
          { label: 'Issue Date', value: item.issue_date },
          { label: 'Due Date', value: item.due_date },
          { label: 'Total Amount', value: `GHS ${item.total_amount?.toFixed(2) || '0.00'}` },
          { label: 'Status', value: item.status },
          { label: 'Payment Terms', value: item.payment_terms || '-', fullWidth: true },
          { label: 'Paid Date', value: item.paid_date || '-' },
          { label: 'Notes', value: item.notes || '-', fullWidth: true },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' }
        ]
      case 'budgets':
        const lineItemsDisplay = item.line_items && item.line_items.length > 0
          ? item.line_items.map((li: BudgetLineItem) =>
              `${li.account_name} (${li.account_type}): ${item.currency || 'GHS'} ${li.budgeted_amount?.toFixed(2) || '0.00'}${li.notes ? ` - ${li.notes}` : ''}`
            ).join('\n')
          : 'No line items'
        return [
          { label: 'Budget Name', value: item.name },
          { label: 'Fiscal Year', value: item.fiscal_year },
          { label: 'Period', value: item.period },
          { label: 'Period Start', value: item.period_start ? new Date(item.period_start).toLocaleDateString() : '-' },
          { label: 'Period End', value: item.period_end ? new Date(item.period_end).toLocaleDateString() : '-' },
          { label: 'Status', value: item.status },
          { label: 'Total Revenue Budget', value: `${item.currency || 'GHS'} ${item.total_revenue_budget?.toFixed(2) || '0.00'}` },
          { label: 'Total Expense Budget', value: `${item.currency || 'GHS'} ${item.total_expense_budget?.toFixed(2) || '0.00'}` },
          { label: 'Net Profit Budget', value: `${item.currency || 'GHS'} ${item.total_profit_budget?.toFixed(2) || '0.00'}` },
          { label: 'Line Items', value: lineItemsDisplay, fullWidth: true },
          { label: 'Description', value: item.description || '-', fullWidth: true },
          { label: 'Created At', value: item.created_at ? new Date(item.created_at).toLocaleString() : '-' }
        ]
      default:
        return []
    }
  }

  const handleEdit = async (item: any) => {
    setSelectedItem(item)

    // Normalize date fields for form inputs
    const normalizedData = { ...item }

    // Helper function to convert date to YYYY-MM-DD format
    const formatDate = (dateStr: string | undefined) => {
      if (!dateStr) return ''
      try {
        const date = new Date(dateStr)
        if (isNaN(date.getTime())) return ''
        return date.toISOString().split('T')[0]
      } catch {
        return ''
      }
    }

    // Normalize dates based on active tab
    switch (activeTab) {
      case 'expenses':
        if (normalizedData.expense_date) {
          normalizedData.expense_date = formatDate(normalizedData.expense_date)
        }
        break
      case 'transactions':
        if (normalizedData.transaction_date) {
          normalizedData.transaction_date = formatDate(normalizedData.transaction_date)
        }
        break
      case 'invoices':
        if (normalizedData.issue_date) {
          normalizedData.issue_date = formatDate(normalizedData.issue_date)
        }
        if (normalizedData.due_date) {
          normalizedData.due_date = formatDate(normalizedData.due_date)
        }
        // Fetch customers for editing invoices
        await fetchCustomers()
        break
      case 'budgets':
        if (normalizedData.period_start) {
          normalizedData.period_start = formatDate(normalizedData.period_start)
        }
        if (normalizedData.period_end) {
          normalizedData.period_end = formatDate(normalizedData.period_end)
        }
        // Fetch accounts for editing budgets
        await fetchAccountsForBudget()
        break
    }

    setFormData(normalizedData)
    setIsModalOpen(true)
  }

  const handleDelete = (item: any) => {
    setSelectedItem(item)
    setIsDeleteModalOpen(true)
  }

  const handleSendForApproval = async (expense: Expense) => {
    try {
      await api.post(`/finance/expenses/${expense.id}/send-for-approval`)
      setToast({ message: 'Expense sent for approval', type: 'success' })
      fetchData() // Refresh the list
    } catch (error: any) {
      setToast({
        message: error.response?.data?.detail || 'Failed to send expense for approval',
        type: 'error'
      })
    }
  }

  const handleApprove = async (expense: Expense) => {
    if (!window.confirm('Are you sure you want to approve this expense?')) {
      return
    }

    try {
      await api.post(`/finance/expenses/${expense.id}/approve`)
      setToast({ message: 'Expense approved successfully', type: 'success' })
      fetchData() // Refresh the list
    } catch (error: any) {
      setToast({
        message: error.response?.data?.detail || 'Failed to approve expense',
        type: 'error'
      })
    }
  }

  const handleReject = async (expense: Expense) => {
    const reason = window.prompt('Please provide a reason for rejection:')
    if (!reason) {
      return
    }

    try {
      await api.post(`/finance/expenses/${expense.id}/reject?rejection_reason=${encodeURIComponent(reason)}`)
      setToast({ message: 'Expense rejected successfully', type: 'success' })
      fetchData() // Refresh the list
    } catch (error: any) {
      setToast({
        message: error.response?.data?.detail || 'Failed to reject expense',
        type: 'error'
      })
    }
  }

  const handleReceiptUpload = async (files: File[]) => {
    if (files.length === 0) {
      return
    }

    try {
      // Create a basic expense entry for each receipt
      // User can edit details later
      for (const file of files) {
        const expenseData = {
          expense_description: `Receipt uploaded: ${file.name}`,
          expense_amount: 0,
          expense_category: 'Uncategorized',
          expense_date: new Date().toISOString().split('T')[0],
          status: 'draft'
        }

        // Create the expense
        const response = await api.post('/finance/expenses', expenseData)
        const expenseId = response.data.id

        // Upload the receipt
        const uploadFormData = new FormData()
        uploadFormData.append('files', file)

        await api.post(
          `/finance/expenses/${expenseId}/attach-receipts-bulk`,
          uploadFormData,
          {
            headers: { 'Content-Type': 'multipart/form-data' }
          }
        )
      }

      setToast({
        message: `${files.length} receipt${files.length > 1 ? 's' : ''} uploaded successfully`,
        type: 'success'
      })
      fetchData() // Refresh the list
    } catch (error: any) {
      setToast({
        message: error.response?.data?.detail || 'Failed to upload receipts',
        type: 'error'
      })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Map tab names to API endpoints
      const endpointMap: Record<Tab, string> = {
        accounts: '/finance/accounts',
        transactions: '/finance/transactions',
        invoices: '/finance/invoices',
        expenses: '/finance/expenses',
        recurring: '/finance/recurring-expenses',
        budgets: '/finance/budgets',
        reports: '/finance/reports',
      }
      const endpoint = endpointMap[activeTab]

      // Create a copy of formData without receipt_files for the API call
      const { receipt_files, ...dataToSubmit } = formData

      let response
      if (selectedItem) {
        response = await api.patch(`${endpoint}/${selectedItem.id}`, dataToSubmit)
      } else {
        response = await api.post(endpoint, dataToSubmit)
      }

      // Upload receipt files for expenses
      if (activeTab === 'expenses' && receipt_files && receipt_files.length > 0) {
        const expenseId = response.data.id || selectedItem?.id

        try {
          // Use bulk upload endpoint for better performance
          const uploadFormData = new FormData()
          receipt_files.forEach((file: File) => {
            uploadFormData.append('files', file)
          })

          const uploadResponse = await api.post(
            `/finance/expenses/${expenseId}/attach-receipts-bulk`,
            uploadFormData,
            {
              headers: { 'Content-Type': 'multipart/form-data' }
            }
          )

          // Show detailed results
          const { successful_uploads, failed_uploads, receipts } = uploadResponse.data

          if (failed_uploads > 0) {
            const failedFiles = receipts
              .filter((r: any) => !r.success)
              .map((r: any) => r.filename)
              .join(', ')
            setToast({
              message: `${successful_uploads} receipt(s) uploaded. Failed: ${failedFiles}`,
              type: 'error'
            })
          } else {
            setToast({
              message: `Expense saved with ${successful_uploads} receipt(s)!`,
              type: 'success'
            })
          }
        } catch (error) {
          console.error('Failed to upload receipts:', error)
          setToast({
            message: 'Expense saved, but failed to upload receipts',
            type: 'error'
          })
        }
      } else {
        setToast({ message: `${selectedItem ? 'Updated' : 'Created'} successfully!`, type: 'success' })
      }

      setIsModalOpen(false)
      setFormData({})
      fetchData()
    } catch (error: any) {
      console.error('Failed to save:', error)
      const errorMsg = error?.response?.data?.detail || 'Failed to save. Please try again.'
      setToast({ message: errorMsg, type: 'error' })
    } finally {
      setIsSubmitting(false)
    }
  }

  const confirmDelete = async () => {
    if (!selectedItem) return

    setIsDeleting(true)
    try {
      const deleteEndpoint = activeTab === 'recurring'
        ? `/finance/recurring-expenses/${selectedItem.id}`
        : `/finance/${activeTab}/${selectedItem.id}`
      await api.delete(deleteEndpoint)
      setIsDeleteModalOpen(false)
      setSelectedItem(null)
      setToast({ message: 'Deleted successfully!', type: 'success' })
      fetchData()
    } catch (error: any) {
      console.error('Failed to delete:', error)
      const errorMsg = error?.response?.data?.detail || 'Failed to delete. Please try again.'
      setToast({ message: errorMsg, type: 'error' })
    } finally {
      setIsDeleting(false)
    }
  }

  // PDF Upload handlers
  const handleFileUpload = (result: UploadResult) => {
    setUploadResult(result)

    // Always show confirmation modal
    if (result.requires_confirmation) {
      setShowConfirmation(true)
    }
  }

  const handleConfirmData = async (confirmedData: Partial<ExpenseFormData>) => {
    try {
      // Save expense with confirmed data
      await api.post('/finance/expenses', confirmedData)

      setToast({ message: 'Expense saved successfully!', type: 'success' })
      setShowConfirmation(false)
      setUploadResult(null)
      fetchData() // Refresh expense list
    } catch (error: any) {
      console.error('Failed to save expense:', error)
      const errorMsg = error?.response?.data?.detail || 'Failed to save expense. Please try again.'
      setToast({ message: errorMsg, type: 'error' })
    }
  }

  const handleCancelConfirmation = () => {
    setShowConfirmation(false)
    setUploadResult(null)
    // Receipt is already uploaded, user can try again later
  }

  // Drag and drop handlers for receipts
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      // Filter for valid file types
      const validFiles = files.filter((file) => {
        const ext = file.name.toLowerCase().split('.').pop()
        return ['pdf', 'jpg', 'jpeg', 'png', 'heic', 'heif'].includes(ext || '')
      })

      if (validFiles.length > 0) {
        const receiptFiles = formData.receipt_files || []
        setFormData({ ...formData, receipt_files: [...receiptFiles, ...validFiles] })
      }

      if (validFiles.length < files.length) {
        setToast({
          message: `${files.length - validFiles.length} file(s) skipped (unsupported format)`,
          type: 'error'
        })
      }
    }
  }

  const getEmptyFormData = () => {
    switch (activeTab) {
      case 'accounts':
        return {
          account_number: '',
          account_name: '',
          account_type: 'asset',
          balance: 0,
          currency: 'GHS',
          is_active: true
        }
      case 'transactions':
        return {
          transaction_date: new Date().toISOString().split('T')[0],
          transaction_type: 'debit',
          amount: 0,
          account_id: '',
          category: '',
          description: '',
          reference_number: ''
        }
      case 'invoices':
        return {
          invoice_number: '',
          customer_id: '',
          issue_date: new Date().toISOString().split('T')[0],
          due_date: new Date().toISOString().split('T')[0],
          total_amount: 0,
          status: 'draft',
          payment_terms: 'net_30'
        }
      case 'expenses':
        return {
          expense_date: new Date().toISOString().split('T')[0],
          category: 'office_supplies',
          amount: 0,
          merchant: '',
          vendor: '',
          description: '',
          payment_method: 'credit_card',
          status: 'pending',
          currency: 'GHS',
          tax_amount: 0,
          receipt_urls: [],
          payable_to: ''
        }
      case 'recurring':
        return {
          expense_date: new Date().toISOString().split('T')[0],
          category: 'office_supplies',
          amount: 0,
          merchant: '',
          description: '',
          currency: 'GHC',
          tax_amount: 0,
          is_recurring: true,
          recurrence_frequency: 'monthly',
          recurrence_start_date: new Date().toISOString().split('T')[0],
          recurrence_end_date: '',
          recurrence_day_of_month: new Date().getDate(),
          auto_approve: false,
          include_in_budget: true,
          budget_id: ''
        }
      case 'budgets':
        return {
          name: '',
          fiscal_year: new Date().getFullYear(),
          period: 'monthly',
          period_start: new Date().toISOString().split('T')[0],
          period_end: new Date().toISOString().split('T')[0],
          status: 'draft',
          line_items: [],
          currency: 'GHS'
        }
      default:
        return {}
    }
  }

  const getColumns = (): Column<any>[] => {
    switch (activeTab) {
      case 'accounts':
        return [
          { key: 'account_number', label: 'Account #' },
          { key: 'account_name', label: 'Account Name' },
          { key: 'account_type', label: 'Type' },
          {
            key: 'balance',
            label: 'Balance',
            render: (item: Account) => item.balance != null ? `${item.currency} ${item.balance.toFixed(2)}` : `${item.currency} 0.00`
          },
          {
            key: 'is_active',
            label: 'Status',
            render: (item: Account) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {item.is_active ? 'Active' : 'Inactive'}
              </span>
            )
          }
        ]
      case 'transactions':
        return [
          { key: 'transaction_date', label: 'Date' },
          { key: 'reference_number', label: 'Reference' },
          {
            key: 'transaction_type',
            label: 'Type',
            render: (item: Transaction) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.transaction_type === 'credit' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
              }`}>
                {item.transaction_type}
              </span>
            )
          },
          {
            key: 'amount',
            label: 'Amount',
            render: (item: Transaction) => item.amount != null ? `GHC ${item.amount.toFixed(2)}` : 'GHC 0.00'
          },
          { key: 'category', label: 'Category' },
          { key: 'description', label: 'Description' }
        ]
      case 'invoices':
        return [
          { key: 'invoice_number', label: 'Invoice #' },
          { key: 'customer_id', label: 'Customer ID' },
          { key: 'issue_date', label: 'Issue Date' },
          { key: 'due_date', label: 'Due Date' },
          {
            key: 'total_amount',
            label: 'Amount',
            render: (item: Invoice) => item.total_amount != null ? `GHC ${item.total_amount.toFixed(2)}` : 'GHC 0.00'
          },
          {
            key: 'status',
            label: 'Status',
            render: (item: Invoice) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.status === 'paid' ? 'bg-green-100 text-green-800' :
                item.status === 'overdue' ? 'bg-red-100 text-red-800' :
                item.status === 'sent' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {item.status}
              </span>
            )
          }
        ]
      case 'expenses':
        return [
          { key: 'expense_date', label: 'Date' },
          {
            key: 'merchant',
            label: 'Merchant',
            render: (item: Expense) => item.merchant || item.vendor || '-'
          },
          { key: 'category', label: 'Category' },
          {
            key: 'amount',
            label: 'Amount',
            render: (item: Expense) => item.amount != null ? `${item.currency || 'GHC'} ${item.amount.toFixed(2)}` : `${item.currency || 'GHC'} 0.00`
          },
          {
            key: 'payable_to',
            label: 'Payable To',
            render: (item: Expense) => item.payable_to || '-'
          },
          { key: 'payment_method', label: 'Payment Method' },
          {
            key: 'status',
            label: 'Status',
            render: (item: Expense) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.status === 'approved' ? 'bg-green-100 text-green-800' :
                item.status === 'rejected' ? 'bg-red-100 text-red-800' :
                item.status === 'paid' ? 'bg-blue-100 text-blue-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {item.status}
              </span>
            )
          },
          {
            key: 'actions',
            label: 'Actions',
            render: (item: Expense) => {
              if (!userPermissions) return null

              const isOwner = item.created_by === userPermissions.user_id
              const isPending = item.status === 'pending'
              const canApproveExpenses = userPermissions.can_approve

              return (
                <div className="flex gap-2">
                  {/* Show "Send for Approval" button for owners of non-pending expenses */}
                  {isOwner && !isPending && item.status !== 'approved' && item.status !== 'rejected' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleSendForApproval(item)
                      }}
                      className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Send for Approval
                    </button>
                  )}

                  {/* Show Approve/Reject buttons for approvers on non-owned expenses */}
                  {canApproveExpenses && !isOwner && isPending && (
                    <>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleApprove(item)
                        }}
                        className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        Approve
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleReject(item)
                        }}
                        className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        Reject
                      </button>
                    </>
                  )}
                </div>
              )
            }
          }
        ]
      case 'recurring':
        return [
          { key: 'merchant', label: 'Merchant' },
          { key: 'category', label: 'Category' },
          { key: 'description', label: 'Description' },
          {
            key: 'amount',
            label: 'Amount',
            render: (item: Expense) => item.amount != null ? `${item.currency || 'GHC'} ${item.amount.toFixed(2)}` : `GHC 0.00`
          },
          {
            key: 'recurrence_frequency',
            label: 'Frequency',
            render: (item: Expense) => item.recurrence_frequency ?
              item.recurrence_frequency.charAt(0).toUpperCase() + item.recurrence_frequency.slice(1) : '-'
          },
          {
            key: 'next_occurrence_date',
            label: 'Next Due',
            render: (item: Expense) => item.next_occurrence_date || '-'
          },
          {
            key: 'is_active',
            label: 'Status',
            render: (item: Expense & { is_active?: boolean }) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.is_active !== false ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {item.is_active !== false ? 'Active' : 'Paused'}
              </span>
            )
          },
          {
            key: 'include_in_budget',
            label: 'In Budget',
            render: (item: Expense) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.include_in_budget ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {item.include_in_budget ? 'Yes' : 'No'}
              </span>
            )
          }
        ]
      case 'budgets':
        return [
          { key: 'name', label: 'Budget Name' },
          { key: 'fiscal_year', label: 'Fiscal Year' },
          {
            key: 'period',
            label: 'Period',
            render: (item: Budget) => item.period ? item.period.charAt(0).toUpperCase() + item.period.slice(1) : '-'
          },
          { key: 'period_start', label: 'Start Date' },
          { key: 'period_end', label: 'End Date' },
          {
            key: 'total_profit_budget',
            label: 'Projected Profit',
            render: (item: Budget) => item.total_profit_budget != null ? `${item.currency} ${item.total_profit_budget.toFixed(2)}` : `${item.currency} 0.00`
          },
          {
            key: 'status',
            label: 'Status',
            render: (item: Budget) => (
              <span className={`px-2 py-1 rounded-full text-xs ${
                item.status === 'active' ? 'bg-green-100 text-green-800' :
                item.status === 'closed' ? 'bg-gray-100 text-gray-800' :
                item.status === 'archived' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {item.status}
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
      case 'accounts':
        return (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Account Number *
                </label>
                <input
                  type="text"
                  value={formData.account_number || ''}
                  onChange={(e) => setFormData({ ...formData, account_number: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Account Name *
                </label>
                <input
                  type="text"
                  value={formData.account_name || ''}
                  onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
                <select
                  value={formData.account_type || 'asset'}
                  onChange={(e) => setFormData({ ...formData, account_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="asset">Asset</option>
                  <option value="liability">Liability</option>
                  <option value="equity">Equity</option>
                  <option value="revenue">Revenue</option>
                  <option value="expense">Expense</option>
                </select>
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Balance *</label>
              <input
                type="number"
                step="0.01"
                value={formData.balance || ''}
                onChange={(e) => setFormData({ ...formData, balance: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
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

      case 'transactions':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Transaction Date *
              </label>
              <input
                type="date"
                value={formData.transaction_date || ''}
                onChange={(e) => setFormData({ ...formData, transaction_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
                <select
                  value={formData.transaction_type || 'debit'}
                  onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="debit">Debit</option>
                  <option value="credit">Credit</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.amount || ''}
                  onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Account ID *</label>
              <input
                type="text"
                value={formData.account_id || ''}
                onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <input
                  type="text"
                  value={formData.category || ''}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reference Number
                </label>
                <input
                  type="text"
                  value={formData.reference_number || ''}
                  onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
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
          </>
        )

      case 'invoices':
        return (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Invoice Number *
                </label>
                <input
                  type="text"
                  value={formData.invoice_number || ''}
                  onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Customer *
                </label>
                {loadingCustomers ? (
                  <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500">
                    Loading customers...
                  </div>
                ) : (
                  <select
                    value={formData.customer_id || ''}
                    onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Select a customer</option>
                    {customers.map((customer) => (
                      <option key={customer.id} value={customer.id}>
                        {customer.company_name || customer.contact_name} - {customer.email}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Issue Date *
                </label>
                <input
                  type="date"
                  value={formData.issue_date || ''}
                  onChange={(e) => setFormData({ ...formData, issue_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date *</label>
                <input
                  type="date"
                  value={formData.due_date || ''}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Total Amount *
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.total_amount || ''}
                onChange={(e) => setFormData({ ...formData, total_amount: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status *</label>
                <select
                  value={formData.status || 'draft'}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="draft">Draft</option>
                  <option value="sent">Sent</option>
                  <option value="paid">Paid</option>
                  <option value="overdue">Overdue</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Terms
                </label>
                <select
                  value={formData.payment_terms || 'net_30'}
                  onChange={(e) => setFormData({ ...formData, payment_terms: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="due_on_receipt">Due on Receipt</option>
                  <option value="net_15">Net 15</option>
                  <option value="net_30">Net 30</option>
                  <option value="net_60">Net 60</option>
                </select>
              </div>
            </div>
          </>
        )

      case 'expenses':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expense Date *
              </label>
              <input
                type="date"
                value={formData.expense_date ?? ''}
                onChange={(e) => setFormData({ ...formData, expense_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Merchant *</label>
              <input
                type="text"
                value={formData.merchant ?? ''}
                onChange={(e) => setFormData({ ...formData, merchant: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                placeholder="Business or vendor name"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                <select
                  value={formData.category ?? 'office_supplies'}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="restaurant">Restaurant</option>
                  <option value="travel">Travel</option>
                  <option value="office_supplies">Office Supplies</option>
                  <option value="utilities">Utilities</option>
                  <option value="software">Software</option>
                  <option value="rent">Rent</option>
                  <option value="marketing">Marketing</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.amount ?? ''}
                  onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tax Amount</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.tax_amount ?? ''}
                  onChange={(e) => setFormData({ ...formData, tax_amount: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
                <select
                  value={formData.currency ?? 'GHS'}
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={formData.description ?? ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Payable To (for expenses paid from personal accounts)
              </label>
              <input
                type="text"
                value={formData.payable_to ?? ''}
                onChange={(e) => setFormData({ ...formData, payable_to: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                placeholder="Name of person/entity to reimburse"
              />
              <p className="text-xs text-gray-500 mt-1">
                Leave blank if expense was paid directly by the company
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Method
                </label>
                <select
                  value={formData.payment_method ?? 'credit_card'}
                  onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="cash">Cash</option>
                  <option value="credit_card">Credit Card</option>
                  <option value="debit_card">Debit Card</option>
                  <option value="mobile_money">Mobile Money</option>
                  <option value="bank_transfer">Bank Transfer</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status *</label>
                <select
                  value={formData.status ?? 'pending'}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="pending">Pending</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="paid">Paid</option>
                </select>
              </div>
            </div>

            {/* Receipt Upload Section */}
            <div className="border-t pt-4 mt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Receipts</h3>

              {/* File/Camera Upload with Drag & Drop */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Attach Receipts (Multiple files supported - PDF, Images, or Take Photo)
                </label>

                {/* Drag and Drop Zone */}
                <div
                  className={`mb-3 p-6 border-2 border-dashed rounded-md transition-all ${
                    isDragging
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300 hover:border-blue-400'
                  }`}
                  onDragEnter={handleDragEnter}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <div className="text-center">
                    <Upload className={`w-8 h-8 mx-auto mb-2 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`} />
                    <p className={`text-sm font-medium ${isDragging ? 'text-blue-600' : 'text-gray-700'}`}>
                      {isDragging ? 'Drop files here' : 'Drag and drop files here'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Or use the buttons below
                    </p>
                  </div>
                </div>

                {/* Upload Buttons */}
                <div className="flex gap-2">
                  <label className="flex-1 cursor-pointer">
                    <div className="px-4 py-3 border-2 border-dashed border-gray-300 rounded-md hover:border-blue-500 transition-colors text-center">
                      <Upload className="w-5 h-5 mx-auto mb-1 text-gray-400" />
                      <span className="text-sm text-gray-600">Upload Files</span>
                      <p className="text-xs text-gray-500 mt-1">Select multiple files</p>
                    </div>
                    <input
                      type="file"
                      accept="image/*,.pdf"
                      multiple
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          const newFiles = Array.from(e.target.files)
                          const receiptFiles = formData.receipt_files || []
                          setFormData({ ...formData, receipt_files: [...receiptFiles, ...newFiles] })
                        }
                      }}
                    />
                  </label>

                  <label className="flex-1 cursor-pointer">
                    <div className="px-4 py-3 border-2 border-dashed border-gray-300 rounded-md hover:border-blue-500 transition-colors text-center">
                      <Camera className="w-5 h-5 mx-auto mb-1 text-gray-400" />
                      <span className="text-sm text-gray-600">Take Photo</span>
                      <p className="text-xs text-gray-500 mt-1">One at a time</p>
                    </div>
                    <input
                      type="file"
                      accept="image/*"
                      capture="environment"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          const file = e.target.files[0]
                          const receiptFiles = formData.receipt_files || []
                          setFormData({ ...formData, receipt_files: [...receiptFiles, file] })
                        }
                      }}
                    />
                  </label>
                </div>

                {/* Preview uploaded receipts */}
                {formData.receipt_files && formData.receipt_files.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {formData.receipt_files.map((file: File, index: number) => (
                      <div
                        key={index}
                        className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded-md"
                      >
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-gray-500" />
                          <span className="text-sm text-gray-700">{file.name}</span>
                          <span className="text-xs text-gray-500">
                            ({(file.size / 1024).toFixed(1)} KB)
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            const receiptFiles = [...formData.receipt_files]
                            receiptFiles.splice(index, 1)
                            setFormData({ ...formData, receipt_files: receiptFiles })
                          }}
                          className="px-2 py-1 text-red-600 hover:bg-red-50 rounded-md"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Display existing receipts for editing */}
                {selectedItem && selectedItem.receipt_urls && selectedItem.receipt_urls.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs text-gray-600 mb-2">Existing receipts:</p>
                    <div className="space-y-2">
                      {selectedItem.receipt_urls.map((url: string, index: number) => (
                        <div
                          key={index}
                          className="flex items-center justify-between bg-blue-50 px-3 py-2 rounded-md"
                        >
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-blue-600" />
                            <span className="text-sm text-blue-700">Receipt {index + 1}</span>
                          </div>
                          <a
                            href={`/api/v1/finance/files/${encodeURIComponent(url)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline"
                          >
                            View
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-xs text-blue-800">
                  <strong>Tip:</strong> You can take photos of receipts directly from your mobile device or upload PDF/image files.
                </p>
              </div>
            </div>
          </>
        )

      case 'recurring':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Merchant *</label>
              <input
                type="text"
                value={formData.merchant ?? ''}
                onChange={(e) => setFormData({ ...formData, merchant: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., AWS, Google Cloud, Office Rent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
              <input
                type="text"
                value={formData.description ?? ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Monthly server hosting"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                <select
                  value={formData.category ?? 'office_supplies'}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="rent">Rent</option>
                  <option value="utilities">Utilities</option>
                  <option value="software">Software/Subscriptions</option>
                  <option value="insurance">Insurance</option>
                  <option value="internet">Internet/Telecom</option>
                  <option value="marketing">Marketing</option>
                  <option value="office_supplies">Office Supplies</option>
                  <option value="payroll">Payroll</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.amount ?? ''}
                  onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
                <select
                  value={formData.currency ?? 'GHC'}
                  onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="GHC">GHC</option>
                  <option value="GHS">GHS</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tax Amount</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.tax_amount ?? 0}
                  onChange={(e) => setFormData({ ...formData, tax_amount: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="border-t pt-4 mt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Recurrence Settings</h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Frequency *</label>
                  <select
                    value={formData.recurrence_frequency ?? 'monthly'}
                    onChange={(e) => setFormData({ ...formData, recurrence_frequency: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="biweekly">Bi-weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Day of Month</label>
                  <input
                    type="number"
                    min="1"
                    max="31"
                    value={formData.recurrence_day_of_month ?? ''}
                    onChange={(e) => setFormData({ ...formData, recurrence_day_of_month: parseInt(e.target.value) || undefined })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    placeholder="1-31 (for monthly)"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Date *</label>
                  <input
                    type="date"
                    value={formData.recurrence_start_date ?? ''}
                    onChange={(e) => setFormData({ ...formData, recurrence_start_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">End Date (optional)</label>
                  <input
                    type="date"
                    value={formData.recurrence_end_date ?? ''}
                    onChange={(e) => setFormData({ ...formData, recurrence_end_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Leave blank for indefinite</p>
                </div>
              </div>
            </div>

            <div className="border-t pt-4 mt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Budget Options</h3>

              <div className="space-y-3">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="include_in_budget"
                    checked={formData.include_in_budget ?? true}
                    onChange={(e) => setFormData({ ...formData, include_in_budget: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="include_in_budget" className="ml-2 text-sm text-gray-700">
                    Include in budget forecasting
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="auto_approve"
                    checked={formData.auto_approve ?? false}
                    onChange={(e) => setFormData({ ...formData, auto_approve: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="auto_approve" className="ml-2 text-sm text-gray-700">
                    Auto-approve generated expenses
                  </label>
                </div>
              </div>
            </div>

            <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-xs text-blue-800">
                <strong>Note:</strong> Recurring expenses will automatically generate expense entries based on your schedule.
                You can pause or resume them at any time.
              </p>
            </div>
          </>
        )

      case 'budgets':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Budget Name *
              </label>
              <input
                type="text"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fiscal Year *
                </label>
                <input
                  type="number"
                  value={formData.fiscal_year || new Date().getFullYear()}
                  onChange={(e) => setFormData({ ...formData, fiscal_year: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Period *</label>
                <select
                  value={formData.period || 'monthly'}
                  onChange={(e) => setFormData({ ...formData, period: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Status *</label>
                <select
                  value={formData.status || 'draft'}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="closed">Closed</option>
                  <option value="archived">Archived</option>
                </select>
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

            {/* Budget Line Items Section */}
            <div className="border-t pt-4 mt-4">
              <div className="flex justify-between items-center mb-3">
                <label className="block text-sm font-medium text-gray-700">
                  Budget Line Items
                </label>
                <button
                  type="button"
                  onClick={() => {
                    const lineItems = formData.line_items || []
                    setFormData({
                      ...formData,
                      line_items: [...lineItems, { account_id: '', account_name: '', account_type: '', budgeted_amount: 0, notes: '' }]
                    })
                  }}
                  className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4" />
                  Add Line Item
                </button>
              </div>

              {loadingAccounts ? (
                <div className="text-center py-4 text-gray-500">Loading accounts...</div>
              ) : (formData.line_items || []).length === 0 ? (
                <div className="text-center py-4 text-gray-500 bg-gray-50 rounded-md">
                  No line items added. Click "Add Line Item" to allocate budget to accounts.
                </div>
              ) : (
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {(formData.line_items || []).map((item: BudgetLineItem, index: number) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-md border border-gray-200">
                      <div className="flex gap-3 items-start">
                        <div className="flex-1">
                          <label className="block text-xs text-gray-500 mb-1">Account</label>
                          <select
                            value={item.account_id || ''}
                            onChange={(e) => {
                              const selectedAccount = accountsList.find(a => a.id === e.target.value)
                              const lineItems = [...(formData.line_items || [])]
                              lineItems[index] = {
                                ...lineItems[index],
                                account_id: e.target.value,
                                account_name: selectedAccount?.account_name || '',
                                account_type: selectedAccount?.account_type || ''
                              }
                              setFormData({ ...formData, line_items: lineItems })
                            }}
                            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="">Select Account</option>
                            {accountsList.filter(a => a.is_active).map(account => (
                              <option key={account.id} value={account.id}>
                                {account.account_number} - {account.account_name} ({account.account_type})
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="w-32">
                          <label className="block text-xs text-gray-500 mb-1">Amount</label>
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={item.budgeted_amount || 0}
                            onChange={(e) => {
                              const lineItems = [...(formData.line_items || [])]
                              lineItems[index] = { ...lineItems[index], budgeted_amount: parseFloat(e.target.value) || 0 }
                              setFormData({ ...formData, line_items: lineItems })
                            }}
                            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div className="flex-1">
                          <label className="block text-xs text-gray-500 mb-1">Notes</label>
                          <input
                            type="text"
                            value={item.notes || ''}
                            onChange={(e) => {
                              const lineItems = [...(formData.line_items || [])]
                              lineItems[index] = { ...lineItems[index], notes: e.target.value }
                              setFormData({ ...formData, line_items: lineItems })
                            }}
                            placeholder="Optional notes"
                            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            const lineItems = (formData.line_items || []).filter((_: BudgetLineItem, i: number) => i !== index)
                            setFormData({ ...formData, line_items: lineItems })
                          }}
                          className="mt-5 p-1.5 text-red-600 hover:bg-red-50 rounded"
                          title="Remove line item"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                      {item.account_type && (
                        <div className="mt-1 text-xs text-gray-500">
                          Type: <span className={`font-medium ${item.account_type === 'revenue' ? 'text-green-600' : item.account_type === 'expense' ? 'text-red-600' : 'text-gray-600'}`}>
                            {item.account_type.charAt(0).toUpperCase() + item.account_type.slice(1)}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Budget Totals Summary */}
              {(formData.line_items || []).length > 0 && (
                <div className="mt-4 p-3 bg-gray-100 rounded-md">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Revenue Budget:</span>
                      <span className="ml-2 font-medium text-green-600">
                        {formData.currency || 'GHS'} {(formData.line_items || [])
                          .filter((item: BudgetLineItem) => item.account_type === 'revenue')
                          .reduce((sum: number, item: BudgetLineItem) => sum + (item.budgeted_amount || 0), 0)
                          .toFixed(2)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Expense Budget:</span>
                      <span className="ml-2 font-medium text-red-600">
                        {formData.currency || 'GHS'} {(formData.line_items || [])
                          .filter((item: BudgetLineItem) => item.account_type === 'expense')
                          .reduce((sum: number, item: BudgetLineItem) => sum + (item.budgeted_amount || 0), 0)
                          .toFixed(2)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Net Budget:</span>
                      <span className="ml-2 font-medium">
                        {formData.currency || 'GHS'} {(
                          (formData.line_items || [])
                            .filter((item: BudgetLineItem) => item.account_type === 'revenue')
                            .reduce((sum: number, item: BudgetLineItem) => sum + (item.budgeted_amount || 0), 0) -
                          (formData.line_items || [])
                            .filter((item: BudgetLineItem) => item.account_type === 'expense')
                            .reduce((sum: number, item: BudgetLineItem) => sum + (item.budgeted_amount || 0), 0)
                        ).toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        )

      default:
        return null
    }
  }

  const generateReport = async () => {
    setReportLoading(true)
    setReportData(null)

    try {
      let response
      switch (reportType) {
        case 'profit-loss':
          response = await api.get('/finance/reports/profit-loss', {
            params: {
              period_start: reportParams.period_start,
              period_end: reportParams.period_end
            }
          })
          break
        case 'balance-sheet':
          response = await api.get('/finance/reports/balance-sheet', {
            params: {
              as_of_date: reportParams.as_of_date
            }
          })
          break
        case 'budget-vs-actual':
          if (!reportParams.budget_id) {
            setToast({ message: 'Please select a budget', type: 'error' })
            setReportLoading(false)
            return
          }
          response = await api.get(`/finance/reports/budget-vs-actual/${reportParams.budget_id}`)
          break
      }
      setReportData(response.data)
      setToast({ message: 'Report generated successfully!', type: 'success' })
    } catch (error: any) {
      console.error('Failed to generate report:', error)
      const errorMsg = error?.response?.data?.detail || 'Failed to generate report. Please try again.'
      setToast({ message: errorMsg, type: 'error' })
    } finally {
      setReportLoading(false)
    }
  }

  const renderReportView = () => {
    return (
      <div className="space-y-6">
        {/* Report Type Selector */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Report Configuration</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Report Type</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="profit-loss">Profit & Loss Statement</option>
                <option value="balance-sheet">Balance Sheet</option>
                <option value="budget-vs-actual">Budget vs Actual</option>
              </select>
            </div>

            {reportType === 'profit-loss' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Period Start</label>
                  <input
                    type="date"
                    value={reportParams.period_start}
                    onChange={(e) => setReportParams({ ...reportParams, period_start: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Period End</label>
                  <input
                    type="date"
                    value={reportParams.period_end}
                    onChange={(e) => setReportParams({ ...reportParams, period_end: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </>
            )}

            {reportType === 'balance-sheet' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">As of Date</label>
                <input
                  type="date"
                  value={reportParams.as_of_date}
                  onChange={(e) => setReportParams({ ...reportParams, as_of_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}

            {reportType === 'budget-vs-actual' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Budget ID</label>
                <input
                  type="text"
                  value={reportParams.budget_id}
                  onChange={(e) => setReportParams({ ...reportParams, budget_id: e.target.value })}
                  placeholder="Enter budget ID"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}
          </div>

          <button
            onClick={generateReport}
            disabled={reportLoading}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          >
            {reportLoading ? 'Generating...' : 'Generate Report'}
          </button>
        </div>

        {/* Report Display */}
        {reportData && (
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">{reportData.report_name || 'Financial Report'}</h3>
              <div className="text-sm text-gray-600">
                {reportData.period_start && reportData.period_end ? (
                  `${reportData.period_start} to ${reportData.period_end}`
                ) : reportData.as_of_date ? (
                  `As of ${reportData.as_of_date}`
                ) : null}
              </div>
            </div>

            <div className="overflow-x-auto">
              <pre className="bg-gray-50 p-4 rounded-md text-sm overflow-auto max-h-96">
                {JSON.stringify(reportData, null, 2)}
              </pre>
            </div>

            <div className="mt-4 text-xs text-gray-500">
              <p>Generated at: {new Date().toLocaleString()}</p>
              <p className="mt-2">
                <strong>Note:</strong> Enhanced report formatting with charts and export functionality coming soon.
              </p>
            </div>
          </div>
        )}
      </div>
    )
  }

  const tabs = [
    { id: 'accounts' as Tab, label: 'Accounts', icon: Wallet },
    { id: 'transactions' as Tab, label: 'Transactions', icon: ArrowRightLeft },
    { id: 'invoices' as Tab, label: 'Invoices', icon: FileText },
    { id: 'expenses' as Tab, label: 'Expenses', icon: Receipt },
    { id: 'recurring' as Tab, label: 'Recurring', icon: Repeat },
    { id: 'budgets' as Tab, label: 'Budgets', icon: PieChart },
    { id: 'reports' as Tab, label: 'Reports', icon: BarChart3 }
  ]

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Finance & Accounting</h1>
        <p className="text-gray-600 mt-2">Manage accounts, transactions, invoices, expenses, budgets, and financial reports</p>
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

      {/* Action Button - Hide for reports tab */}
      {activeTab !== 'reports' && (
        <div className="mb-4 flex justify-end">
          {activeTab === 'expenses' ? (
            <div className="relative">
              <button
                onClick={() => setShowAddDropdown(!showAddDropdown)}
                className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Expense
                <ChevronDown className="w-4 h-4 ml-2" />
              </button>

              {showAddDropdown && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowAddDropdown(false)}
                  />
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-20">
                    <button
                      onClick={() => {
                        handleCreate()
                        setShowAddDropdown(false)
                      }}
                      className="w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Expense
                    </button>
                    <button
                      onClick={() => {
                        setIsReceiptModalOpen(true)
                        setShowAddDropdown(false)
                      }}
                      className="w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center border-t border-gray-100"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Receipts
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <button
              onClick={handleCreate}
              className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add {activeTab.slice(0, -1).charAt(0).toUpperCase() + activeTab.slice(1, -1)}
            </button>
          )}
        </div>
      )}

      {/* PDF Upload Component - Only show for expenses tab */}
      {activeTab === 'expenses' && (
        <div className="mb-6">
          <FileUpload onUploadComplete={handleFileUpload} />
        </div>
      )}

      {/* Conditional Content: DataTable or Reports View */}
      {activeTab === 'reports' ? (
        renderReportView()
      ) : (
        <DataTable
          data={data}
          columns={getColumns()}
          loading={loading}
          searchPlaceholder={`Search ${activeTab}...`}
          onSearch={setSearchQuery}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onRowClick={activeTab === 'expenses' ? handleRowClick : undefined}
          pagination={activeTab === 'expenses' ? undefined : {
            page,
            pageSize,
            total: totalItems,
            onPageChange: setPage
          }}
          infiniteScroll={activeTab === 'expenses' ? {
            hasMore: hasMoreExpenses,
            loadingMore: loadingMoreExpenses,
            observerTarget: observerTarget
          } : undefined}
          emptyMessage={`No ${activeTab} found`}
        />
      )}

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
            ? activeTab === 'accounts'
              ? selectedItem.account_name
              : activeTab === 'invoices'
              ? selectedItem.invoice_number
              : selectedItem.id
            : ''
        }
        isDeleting={isDeleting}
      />

      {/* Confirmation Modal for PDF Upload */}
      {showConfirmation && uploadResult && (
        <ConfirmExtractedData
          extractedData={uploadResult.extracted_data}
          receiptUrl={uploadResult.receipt_url}
          onConfirm={handleConfirmData}
          onCancel={handleCancelConfirmation}
        />
      )}

      {/* Expense Details Modal */}
      {isDetailsModalOpen && selectedItem && activeTab === 'expenses' && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setIsDetailsModalOpen(false)}></div>
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-3xl">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Expense Details</h3>
                  <button
                    onClick={() => setIsDetailsModalOpen(false)}
                    className="rounded-md text-gray-400 hover:text-gray-500"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>

                <div className="space-y-6">
                  {/* Basic Information */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Expense Date</p>
                      <p className="font-medium">{new Date(selectedItem.expense_date).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Amount</p>
                      <p className="font-medium">{selectedItem.currency || 'GHC'} {selectedItem.amount?.toFixed(2) || '0.00'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Merchant</p>
                      <p className="font-medium">{selectedItem.merchant || selectedItem.vendor || '-'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Category</p>
                      <p className="font-medium capitalize">{selectedItem.category || '-'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Payment Method</p>
                      <p className="font-medium capitalize">{selectedItem.payment_method?.replace('_', ' ') || '-'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Status</p>
                      <span className={`inline-block px-2 py-1 rounded-full text-xs ${
                        selectedItem.status === 'approved' ? 'bg-green-100 text-green-800' :
                        selectedItem.status === 'rejected' ? 'bg-red-100 text-red-800' :
                        selectedItem.status === 'paid' ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {selectedItem.status}
                      </span>
                    </div>
                    {selectedItem.payable_to && (
                      <div>
                        <p className="text-sm text-gray-600">Payable To</p>
                        <p className="font-medium">{selectedItem.payable_to}</p>
                      </div>
                    )}
                    {selectedItem.tax_amount && (
                      <div>
                        <p className="text-sm text-gray-600">Tax Amount</p>
                        <p className="font-medium">{selectedItem.currency || 'GHC'} {selectedItem.tax_amount.toFixed(2)}</p>
                      </div>
                    )}
                  </div>

                  {/* Description */}
                  {selectedItem.description && (
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Description</p>
                      <p className="text-gray-900">{selectedItem.description}</p>
                    </div>
                  )}

                  {/* Notes */}
                  {selectedItem.notes && (
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Notes</p>
                      <p className="text-gray-900">{selectedItem.notes}</p>
                    </div>
                  )}

                  {/* Receipts */}
                  {selectedItem.receipt_urls && selectedItem.receipt_urls.length > 0 && (
                    <div>
                      <p className="text-sm text-gray-600 mb-2">Receipts</p>
                      <div className="space-y-2">
                        {selectedItem.receipt_urls.map((url: string, index: number) => {
                          // If URL is a relative path, construct full API URL
                          // If it's already a full URL, use it as-is
                          const fileUrl = url.startsWith('http://') || url.startsWith('https://')
                            ? url
                            : `/api/v1/finance/files/${encodeURIComponent(url)}`
                          return (
                            <a
                              key={index}
                              href={fileUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block text-blue-600 hover:text-blue-800 underline"
                            >
                              Receipt {index + 1}
                            </a>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  {/* Approval Information */}
                  {(selectedItem.approved_by || selectedItem.approver_name) && (
                    <div className="border-t pt-4">
                      <p className="text-sm text-gray-600 mb-2">Approval Information</p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-gray-500">Approver</p>
                          <p className="text-sm font-medium">{selectedItem.approver_name || selectedItem.approved_by}</p>
                        </div>
                        {selectedItem.approved_date && (
                          <div>
                            <p className="text-xs text-gray-500">Approved Date</p>
                            <p className="text-sm font-medium">{new Date(selectedItem.approved_date).toLocaleDateString()}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Rejection Reason */}
                  {selectedItem.rejection_reason && (
                    <div className="border-t pt-4">
                      <p className="text-sm text-gray-600 mb-1">Rejection Reason</p>
                      <p className="text-red-600">{selectedItem.rejection_reason}</p>
                    </div>
                  )}

                  {/* Reimbursement Information */}
                  {(selectedItem.is_reimbursable || selectedItem.reimbursed) && (
                    <div className="border-t pt-4">
                      <p className="text-sm text-gray-600 mb-2">Reimbursement Information</p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-gray-500">Reimbursable</p>
                          <p className="text-sm font-medium">{selectedItem.is_reimbursable ? 'Yes' : 'No'}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Reimbursed</p>
                          <p className="text-sm font-medium">{selectedItem.reimbursed ? 'Yes' : 'No'}</p>
                        </div>
                        {selectedItem.reimbursement_date && (
                          <div>
                            <p className="text-xs text-gray-500">Reimbursement Date</p>
                            <p className="text-sm font-medium">{new Date(selectedItem.reimbursement_date).toLocaleDateString()}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    onClick={() => {
                      setIsDetailsModalOpen(false)
                      handleEdit(selectedItem)
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => setIsDetailsModalOpen(false)}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      <Toast
        message={toast?.message || ''}
        type={toast?.type || 'success'}
        isOpen={toast !== null}
        onClose={() => setToast(null)}
      />

      {/* Detail Modal (for non-expense tabs) */}
      <DetailModal
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        title={`${activeTab.slice(0, -1).charAt(0).toUpperCase() + activeTab.slice(1, -1)} Details`}
        fields={getDetailFields(detailItem)}
        onEdit={() => detailItem && handleEdit(detailItem)}
      />

      {/* Receipt Upload Modal */}
      <ReceiptUploadModal
        isOpen={isReceiptModalOpen}
        onClose={() => setIsReceiptModalOpen(false)}
        onUpload={handleReceiptUpload}
      />
    </div>
  )
}
