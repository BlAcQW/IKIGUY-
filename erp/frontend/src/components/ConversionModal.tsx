/**
 * ConversionModal Component
 *
 * Handles Lead→Opportunity, Lead→Customer, and Opportunity→Customer conversions
 */

import { X } from 'lucide-react'
import { useState, useEffect } from 'react'
import api from '@/lib/api'

type ConversionType = 'lead-to-opportunity' | 'lead-to-customer' | 'opportunity-to-customer' | 'mark-won'

interface ConversionModalProps {
  isOpen: boolean
  onClose: () => void
  type: ConversionType
  item: any
  onSuccess: () => void
}

export default function ConversionModal({
  isOpen,
  onClose,
  type,
  item,
  onSuccess
}: ConversionModalProps) {
  const [formData, setFormData] = useState<any>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [customers, setCustomers] = useState<any[]>([])

  useEffect(() => {
    if (isOpen) {
      // Reset form
      setError('')
      initializeForm()

      // Fetch customers for dropdown if needed
      if (type === 'opportunity-to-customer' || type === 'mark-won') {
        fetchCustomers()
      }
    }
  }, [isOpen, type])

  const fetchCustomers = async () => {
    try {
      const response = await api.get('/crm/customers?limit=1000')
      setCustomers(response.data)
    } catch (error) {
      console.error('Failed to fetch customers:', error)
    }
  }

  const initializeForm = () => {
    switch (type) {
      case 'lead-to-opportunity':
        setFormData({
          opportunity_name: `${item?.company || item?.first_name} Deal`,
          amount: 10000,
          probability: 25,
          stage: 'prospecting',
          description: '',
          keep_lead_active: false
        })
        break
      case 'lead-to-customer':
        setFormData({
          customer_type: 'business',
          company_name: item?.company,
          create_contact: true,
          account_manager: '',
          tags: []
        })
        break
      case 'opportunity-to-customer':
      case 'mark-won':
        setFormData({
          create_new_customer: true,
          existing_customer_id: '',
          customer_type: 'business',
          account_manager: '',
          create_invoice: true,
          invoice_due_days: 30,
          invoice_notes: '',
          create_project: false,
          project_name: ''
        })
        break
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError('')

    try {
      let endpoint = ''
      let payload = formData

      switch (type) {
        case 'lead-to-opportunity':
          endpoint = `/crm/leads/${item.id}/convert-to-opportunity`
          break
        case 'lead-to-customer':
          endpoint = `/crm/leads/${item.id}/convert-to-customer`
          break
        case 'opportunity-to-customer':
          endpoint = `/crm/opportunities/${item.id}/convert-to-customer`
          break
        case 'mark-won':
          endpoint = `/crm/opportunities/${item.id}/mark-won`
          payload = {
            ...formData,
            create_customer: formData.create_new_customer
          }
          break
      }

      const response = await api.post(endpoint, payload)

      if (response.data.success) {
        onSuccess()
        onClose()
      } else {
        setError(response.data.message || 'Conversion failed')
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to perform conversion')
    } finally {
      setIsSubmitting(false)
    }
  }

  const getTitle = () => {
    switch (type) {
      case 'lead-to-opportunity':
        return 'Convert Lead to Opportunity'
      case 'lead-to-customer':
        return 'Convert Lead to Customer'
      case 'opportunity-to-customer':
        return 'Convert Opportunity to Customer'
      case 'mark-won':
        return 'Mark Opportunity as Won'
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>

      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
          {/* Header */}
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium leading-6 text-gray-900">
                {getTitle()}
              </h3>
              <button
                onClick={onClose}
                className="rounded-md text-gray-400 hover:text-gray-500"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {error && (
              <div className="mb-4 rounded-md bg-red-50 p-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Lead to Opportunity Fields */}
              {type === 'lead-to-opportunity' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Opportunity Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.opportunity_name || ''}
                      onChange={(e) => setFormData({ ...formData, opportunity_name: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Amount ($) *
                      </label>
                      <input
                        type="number"
                        required
                        min="0"
                        step="0.01"
                        value={formData.amount || ''}
                        onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Probability (%) *
                      </label>
                      <input
                        type="number"
                        required
                        min="0"
                        max="100"
                        value={formData.probability || ''}
                        onChange={(e) => setFormData({ ...formData, probability: parseInt(e.target.value) })}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Stage
                    </label>
                    <select
                      value={formData.stage || 'prospecting'}
                      onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    >
                      <option value="prospecting">Prospecting</option>
                      <option value="qualification">Qualification</option>
                      <option value="proposal">Proposal</option>
                      <option value="negotiation">Negotiation</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Description
                    </label>
                    <textarea
                      value={formData.description || ''}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={3}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    />
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.keep_lead_active || false}
                      onChange={(e) => setFormData({ ...formData, keep_lead_active: e.target.checked })}
                      className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <label className="ml-2 block text-sm text-gray-700">
                      Keep lead active after conversion
                    </label>
                  </div>
                </>
              )}

              {/* Lead to Customer Fields */}
              {type === 'lead-to-customer' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Customer Type
                    </label>
                    <select
                      value={formData.customer_type || 'business'}
                      onChange={(e) => setFormData({ ...formData, customer_type: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    >
                      <option value="individual">Individual</option>
                      <option value="business">Business</option>
                      <option value="government">Government</option>
                    </select>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.create_contact || false}
                      onChange={(e) => setFormData({ ...formData, create_contact: e.target.checked })}
                      className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <label className="ml-2 block text-sm text-gray-700">
                      Create contact record from lead data
                    </label>
                  </div>
                </>
              )}

              {/* Opportunity to Customer / Mark Won Fields */}
              {(type === 'opportunity-to-customer' || type === 'mark-won') && (
                <>
                  <div className="border-b pb-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Customer Options</h4>

                    <div className="space-y-3">
                      <div className="flex items-center">
                        <input
                          type="radio"
                          checked={formData.create_new_customer || false}
                          onChange={() => setFormData({ ...formData, create_new_customer: true })}
                          className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <label className="ml-2 block text-sm text-gray-700">
                          Create new customer
                        </label>
                      </div>

                      <div className="flex items-center">
                        <input
                          type="radio"
                          checked={!formData.create_new_customer}
                          onChange={() => setFormData({ ...formData, create_new_customer: false })}
                          className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <label className="ml-2 block text-sm text-gray-700">
                          Link to existing customer
                        </label>
                      </div>

                      {!formData.create_new_customer && (
                        <div className="ml-6">
                          <select
                            value={formData.existing_customer_id || ''}
                            onChange={(e) => setFormData({ ...formData, existing_customer_id: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                          >
                            <option value="">Select customer...</option>
                            {customers.map((customer) => (
                              <option key={customer.id} value={customer.id}>
                                {customer.company_name || `${customer.first_name} ${customer.last_name}`}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}

                      {formData.create_new_customer && (
                        <div className="ml-6">
                          <label className="block text-sm font-medium text-gray-700">
                            Customer Type
                          </label>
                          <select
                            value={formData.customer_type || 'business'}
                            onChange={(e) => setFormData({ ...formData, customer_type: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                          >
                            <option value="individual">Individual</option>
                            <option value="business">Business</option>
                            <option value="government">Government</option>
                          </select>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="border-b pb-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Invoice Options</h4>

                    <div className="space-y-3">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.create_invoice || false}
                          onChange={(e) => setFormData({ ...formData, create_invoice: e.target.checked })}
                          className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <label className="ml-2 block text-sm text-gray-700">
                          Create invoice automatically
                        </label>
                      </div>

                      {formData.create_invoice && (
                        <div className="ml-6 space-y-3">
                          <div>
                            <label className="block text-sm font-medium text-gray-700">
                              Invoice Due (days)
                            </label>
                            <input
                              type="number"
                              min="1"
                              value={formData.invoice_due_days || 30}
                              onChange={(e) => setFormData({ ...formData, invoice_due_days: parseInt(e.target.value) })}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700">
                              Invoice Notes
                            </label>
                            <textarea
                              value={formData.invoice_notes || ''}
                              onChange={(e) => setFormData({ ...formData, invoice_notes: e.target.value })}
                              rows={2}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                              placeholder="Payment terms: Net 30"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Project Options</h4>

                    <div className="space-y-3">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.create_project || false}
                          onChange={(e) => setFormData({ ...formData, create_project: e.target.checked })}
                          className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <label className="ml-2 block text-sm text-gray-700">
                          Create project for this customer
                        </label>
                      </div>

                      {formData.create_project && (
                        <div className="ml-6">
                          <label className="block text-sm font-medium text-gray-700">
                            Project Name
                          </label>
                          <input
                            type="text"
                            value={formData.project_name || ''}
                            onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            placeholder="Enter project name"
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </>
              )}

              {/* Footer */}
              <div className="mt-5 sm:mt-6 sm:flex sm:flex-row-reverse gap-3">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex w-full justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-base font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Converting...' : (type === 'mark-won' ? 'Mark as Won' : 'Convert')}
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isSubmitting}
                  className="mt-3 inline-flex w-full justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-base font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:mt-0 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
