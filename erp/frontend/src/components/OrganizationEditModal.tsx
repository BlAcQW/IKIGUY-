import { useState, useEffect } from 'react'
import { X, Building2, Palette, FileText, Landmark } from 'lucide-react'
import api from '@/lib/api'

interface Organization {
  id: string
  name: string
  display_name: string
  description?: string
  industry?: string
  company_size?: string
  website?: string
  phone?: string
  email?: string
  address?: string
  billing_address?: {
    street?: string
    street2?: string
    city?: string
    state?: string
    postal_code?: string
    country?: string
  }
  logo_url?: string
  primary_color?: string
  secondary_color?: string
  accent_color?: string
  invoice_settings?: {
    invoice_prefix?: string
    invoice_number_start?: number
    next_invoice_number?: number
    default_payment_terms?: string
    late_fee_percentage?: number
    tax_id?: string
    tax_label?: string
    default_tax_rate?: number
    header_text?: string
    footer_text?: string
    default_notes?: string
    terms_and_conditions?: string
    date_format?: string
    currency_symbol?: string
    currency_position?: string
    show_logo?: boolean
    show_payment_instructions?: boolean
  }
  bank_name?: string
  bank_account_number?: string
  bank_routing_number?: string
  bank_iban?: string
  bank_swift?: string
}

interface OrganizationEditModalProps {
  organization: Organization
  isOpen: boolean
  onClose: () => void
  onSave: () => void
}

export default function OrganizationEditModal({
  organization,
  isOpen,
  onClose,
  onSave
}: OrganizationEditModalProps) {
  const [activeTab, setActiveTab] = useState<'basic' | 'branding' | 'invoice' | 'bank'>('basic')
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState<Partial<Organization>>({})

  useEffect(() => {
    if (isOpen) {
      // Initialize form data with organization values
      setFormData({
        display_name: organization.display_name,
        description: organization.description || '',
        industry: organization.industry || '',
        company_size: organization.company_size || '',
        website: organization.website || '',
        phone: organization.phone || '',
        email: organization.email || '',
        address: organization.address || '',
        billing_address: organization.billing_address || {},
        logo_url: organization.logo_url || '',
        primary_color: organization.primary_color || '#0066CC',
        secondary_color: organization.secondary_color || '#666666',
        accent_color: organization.accent_color || '#00CC66',
        invoice_settings: {
          invoice_prefix: organization.invoice_settings?.invoice_prefix || 'INV',
          invoice_number_start: organization.invoice_settings?.invoice_number_start || 1000,
          next_invoice_number: organization.invoice_settings?.next_invoice_number || 1000,
          default_payment_terms: organization.invoice_settings?.default_payment_terms || 'Net 30',
          late_fee_percentage: organization.invoice_settings?.late_fee_percentage || 0,
          tax_id: organization.invoice_settings?.tax_id || '',
          tax_label: organization.invoice_settings?.tax_label || 'Tax',
          default_tax_rate: organization.invoice_settings?.default_tax_rate || 0,
          header_text: organization.invoice_settings?.header_text || '',
          footer_text: organization.invoice_settings?.footer_text || 'Thank you for your business!',
          default_notes: organization.invoice_settings?.default_notes || '',
          terms_and_conditions: organization.invoice_settings?.terms_and_conditions || '',
          date_format: organization.invoice_settings?.date_format || 'YYYY-MM-DD',
          currency_symbol: organization.invoice_settings?.currency_symbol || '$',
          currency_position: organization.invoice_settings?.currency_position || 'before',
          show_logo: organization.invoice_settings?.show_logo !== false,
          show_payment_instructions: organization.invoice_settings?.show_payment_instructions !== false,
        },
        bank_name: organization.bank_name || '',
        bank_account_number: organization.bank_account_number || '',
        bank_routing_number: organization.bank_routing_number || '',
        bank_iban: organization.bank_iban || '',
        bank_swift: organization.bank_swift || '',
      })
    }
  }, [isOpen, organization])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.patch(`/organizations/${organization.id}`, formData)
      onSave()
      onClose()
    } catch (error) {
      console.error('Failed to update organization:', error)
      alert('Failed to update organization. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={onClose} />

        {/* Modal panel */}
        <div className="inline-block w-full max-w-4xl my-8 overflow-hidden text-left align-middle transition-all transform bg-white rounded-lg shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">
              Edit Organization: {organization.display_name}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500 focus:outline-none"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px px-6">
              <button
                onClick={() => setActiveTab('basic')}
                className={`flex items-center space-x-2 py-4 px-4 border-b-2 font-medium text-sm ${
                  activeTab === 'basic'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Building2 className="w-4 h-4" />
                <span>Basic Info</span>
              </button>
              <button
                onClick={() => setActiveTab('branding')}
                className={`flex items-center space-x-2 py-4 px-4 border-b-2 font-medium text-sm ${
                  activeTab === 'branding'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Palette className="w-4 h-4" />
                <span>Branding</span>
              </button>
              <button
                onClick={() => setActiveTab('invoice')}
                className={`flex items-center space-x-2 py-4 px-4 border-b-2 font-medium text-sm ${
                  activeTab === 'invoice'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <FileText className="w-4 h-4" />
                <span>Invoice Settings</span>
              </button>
              <button
                onClick={() => setActiveTab('bank')}
                className={`flex items-center space-x-2 py-4 px-4 border-b-2 font-medium text-sm ${
                  activeTab === 'bank'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Landmark className="w-4 h-4" />
                <span>Bank Details</span>
              </button>
            </nav>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit}>
            <div className="px-6 py-6 max-h-[600px] overflow-y-auto">
              {/* Basic Info Tab */}
              {activeTab === 'basic' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Display Name *</label>
                    <input
                      type="text"
                      required
                      value={formData.display_name || ''}
                      onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Description</label>
                    <textarea
                      value={formData.description || ''}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      rows={3}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Industry</label>
                      <input
                        type="text"
                        value={formData.industry || ''}
                        onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Company Size</label>
                      <select
                        value={formData.company_size || ''}
                        onChange={(e) => setFormData({ ...formData, company_size: e.target.value })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">Select size</option>
                        <option value="1-10">1-10</option>
                        <option value="11-50">11-50</option>
                        <option value="51-200">51-200</option>
                        <option value="201-500">201-500</option>
                        <option value="501-1000">501-1000</option>
                        <option value="1000+">1000+</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Website</label>
                      <input
                        type="url"
                        value={formData.website || ''}
                        onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Phone</label>
                      <input
                        type="tel"
                        value={formData.phone || ''}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <input
                      type="email"
                      value={formData.email || ''}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Billing Address</label>
                    <div className="space-y-3">
                      <input
                        type="text"
                        placeholder="Street Address"
                        value={formData.billing_address?.street || ''}
                        onChange={(e) => setFormData({
                          ...formData,
                          billing_address: { ...formData.billing_address, street: e.target.value }
                        })}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                      <input
                        type="text"
                        placeholder="Street Address Line 2"
                        value={formData.billing_address?.street2 || ''}
                        onChange={(e) => setFormData({
                          ...formData,
                          billing_address: { ...formData.billing_address, street2: e.target.value }
                        })}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                      <div className="grid grid-cols-2 gap-3">
                        <input
                          type="text"
                          placeholder="City"
                          value={formData.billing_address?.city || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            billing_address: { ...formData.billing_address, city: e.target.value }
                          })}
                          className="px-3 py-2 border border-gray-300 rounded-md"
                        />
                        <input
                          type="text"
                          placeholder="State/Province"
                          value={formData.billing_address?.state || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            billing_address: { ...formData.billing_address, state: e.target.value }
                          })}
                          className="px-3 py-2 border border-gray-300 rounded-md"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <input
                          type="text"
                          placeholder="Postal Code"
                          value={formData.billing_address?.postal_code || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            billing_address: { ...formData.billing_address, postal_code: e.target.value }
                          })}
                          className="px-3 py-2 border border-gray-300 rounded-md"
                        />
                        <input
                          type="text"
                          placeholder="Country"
                          value={formData.billing_address?.country || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            billing_address: { ...formData.billing_address, country: e.target.value }
                          })}
                          className="px-3 py-2 border border-gray-300 rounded-md"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Branding Tab */}
              {activeTab === 'branding' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Logo URL</label>
                    <input
                      type="url"
                      value={formData.logo_url || ''}
                      onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                      placeholder="https://example.com/logo.png"
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                    <p className="mt-1 text-sm text-gray-500">
                      URL to your company logo (PNG, JPG, or SVG)
                    </p>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Primary Color</label>
                      <div className="flex items-center mt-1 space-x-2">
                        <input
                          type="color"
                          value={formData.primary_color || '#0066CC'}
                          onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                          className="h-10 w-16 border border-gray-300 rounded cursor-pointer"
                        />
                        <input
                          type="text"
                          value={formData.primary_color || '#0066CC'}
                          onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Secondary Color</label>
                      <div className="flex items-center mt-1 space-x-2">
                        <input
                          type="color"
                          value={formData.secondary_color || '#666666'}
                          onChange={(e) => setFormData({ ...formData, secondary_color: e.target.value })}
                          className="h-10 w-16 border border-gray-300 rounded cursor-pointer"
                        />
                        <input
                          type="text"
                          value={formData.secondary_color || '#666666'}
                          onChange={(e) => setFormData({ ...formData, secondary_color: e.target.value })}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Accent Color</label>
                      <div className="flex items-center mt-1 space-x-2">
                        <input
                          type="color"
                          value={formData.accent_color || '#00CC66'}
                          onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                          className="h-10 w-16 border border-gray-300 rounded cursor-pointer"
                        />
                        <input
                          type="text"
                          value={formData.accent_color || '#00CC66'}
                          onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-gray-50 rounded-md">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Color Preview</h4>
                    <div className="flex space-x-4">
                      <div
                        className="w-24 h-24 rounded-md shadow-sm"
                        style={{ backgroundColor: formData.primary_color || '#0066CC' }}
                      />
                      <div
                        className="w-24 h-24 rounded-md shadow-sm"
                        style={{ backgroundColor: formData.secondary_color || '#666666' }}
                      />
                      <div
                        className="w-24 h-24 rounded-md shadow-sm"
                        style={{ backgroundColor: formData.accent_color || '#00CC66' }}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Invoice Settings Tab */}
              {activeTab === 'invoice' && (
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold text-gray-900">Invoice Numbering</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Prefix</label>
                      <input
                        type="text"
                        value={formData.invoice_settings?.invoice_prefix || 'INV'}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, invoice_prefix: e.target.value }
                        })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Start Number</label>
                      <input
                        type="number"
                        value={formData.invoice_settings?.invoice_number_start || 1000}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, invoice_number_start: parseInt(e.target.value) }
                        })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Next Number</label>
                      <input
                        type="number"
                        value={formData.invoice_settings?.next_invoice_number || 1000}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, next_invoice_number: parseInt(e.target.value) }
                        })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>
                  </div>

                  <h4 className="text-sm font-semibold text-gray-900 pt-4">Payment Terms</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Default Payment Terms</label>
                      <input
                        type="text"
                        value={formData.invoice_settings?.default_payment_terms || 'Net 30'}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, default_payment_terms: e.target.value }
                        })}
                        placeholder="e.g., Net 30"
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Late Fee (%)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.invoice_settings?.late_fee_percentage || 0}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, late_fee_percentage: parseFloat(e.target.value) }
                        })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>
                  </div>

                  <h4 className="text-sm font-semibold text-gray-900 pt-4">Tax Settings</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Tax ID / VAT</label>
                      <input
                        type="text"
                        value={formData.invoice_settings?.tax_id || ''}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, tax_id: e.target.value }
                        })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Tax Label</label>
                      <input
                        type="text"
                        value={formData.invoice_settings?.tax_label || 'Tax'}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, tax_label: e.target.value }
                        })}
                        placeholder="Tax, VAT, GST, etc."
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Default Tax Rate (%)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.invoice_settings?.default_tax_rate || 0}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, default_tax_rate: parseFloat(e.target.value) }
                        })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>
                  </div>

                  <h4 className="text-sm font-semibold text-gray-900 pt-4">Invoice Text</h4>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Header Text</label>
                    <input
                      type="text"
                      value={formData.invoice_settings?.header_text || ''}
                      onChange={(e) => setFormData({
                        ...formData,
                        invoice_settings: { ...formData.invoice_settings, header_text: e.target.value }
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Footer Text</label>
                    <input
                      type="text"
                      value={formData.invoice_settings?.footer_text || ''}
                      onChange={(e) => setFormData({
                        ...formData,
                        invoice_settings: { ...formData.invoice_settings, footer_text: e.target.value }
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Default Notes</label>
                    <textarea
                      value={formData.invoice_settings?.default_notes || ''}
                      onChange={(e) => setFormData({
                        ...formData,
                        invoice_settings: { ...formData.invoice_settings, default_notes: e.target.value }
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      rows={2}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Terms & Conditions</label>
                    <textarea
                      value={formData.invoice_settings?.terms_and_conditions || ''}
                      onChange={(e) => setFormData({
                        ...formData,
                        invoice_settings: { ...formData.invoice_settings, terms_and_conditions: e.target.value }
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      rows={3}
                    />
                  </div>

                  <h4 className="text-sm font-semibold text-gray-900 pt-4">Currency & Format</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Currency Symbol</label>
                      <input
                        type="text"
                        value={formData.invoice_settings?.currency_symbol || '$'}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, currency_symbol: e.target.value }
                        })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Currency Position</label>
                      <select
                        value={formData.invoice_settings?.currency_position || 'before'}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, currency_position: e.target.value }
                        })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      >
                        <option value="before">Before ($100)</option>
                        <option value="after">After (100$)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Date Format</label>
                      <select
                        value={formData.invoice_settings?.date_format || 'YYYY-MM-DD'}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, date_format: e.target.value }
                        })}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      >
                        <option value="YYYY-MM-DD">2025-01-15</option>
                        <option value="DD/MM/YYYY">15/01/2025</option>
                        <option value="MM/DD/YYYY">01/15/2025</option>
                      </select>
                    </div>
                  </div>

                  <h4 className="text-sm font-semibold text-gray-900 pt-4">Display Options</h4>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.invoice_settings?.show_logo !== false}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, show_logo: e.target.checked }
                        })}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Show logo on invoices</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.invoice_settings?.show_payment_instructions !== false}
                        onChange={(e) => setFormData({
                          ...formData,
                          invoice_settings: { ...formData.invoice_settings, show_payment_instructions: e.target.checked }
                        })}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Show payment instructions</span>
                    </label>
                  </div>
                </div>
              )}

              {/* Bank Details Tab */}
              {activeTab === 'bank' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Bank Name</label>
                    <input
                      type="text"
                      value={formData.bank_name || ''}
                      onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
                      placeholder="e.g., Chase Bank"
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Account Number</label>
                    <input
                      type="text"
                      value={formData.bank_account_number || ''}
                      onChange={(e) => setFormData({ ...formData, bank_account_number: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Routing Number / Sort Code</label>
                    <input
                      type="text"
                      value={formData.bank_routing_number || ''}
                      onChange={(e) => setFormData({ ...formData, bank_routing_number: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">IBAN</label>
                    <input
                      type="text"
                      value={formData.bank_iban || ''}
                      onChange={(e) => setFormData({ ...formData, bank_iban: e.target.value })}
                      placeholder="International Bank Account Number"
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">SWIFT / BIC Code</label>
                    <input
                      type="text"
                      value={formData.bank_swift || ''}
                      onChange={(e) => setFormData({ ...formData, bank_swift: e.target.value })}
                      placeholder="Bank Identifier Code"
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div className="mt-4 p-4 bg-blue-50 rounded-md">
                    <p className="text-sm text-blue-800">
                      <strong>Note:</strong> Bank details will be displayed on invoices for customer payments.
                      Ensure accuracy before sharing invoices with customers.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex justify-end space-x-3 px-6 py-4 bg-gray-50 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
