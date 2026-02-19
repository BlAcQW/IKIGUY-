/**
 * ConfirmExtractedData Component
 *
 * Modal for reviewing and confirming extracted receipt data.
 * - Shows PDF preview side-by-side with editable form
 * - Displays confidence warnings for low-quality extractions
 * - Validates required fields before allowing save
 * - Shows extraction method (pattern vs AI)
 */

import { useState } from 'react'
import { AlertTriangle, X } from 'lucide-react'
import { ExtractedData } from './FileUpload'

export interface ExpenseFormData {
  expense_date: string
  merchant: string
  category: string
  amount: number
  tax_amount?: number
  currency?: string
  payment_method?: string
  receipt_urls?: string[]
  receipt_number?: string
  notes?: string
}

interface ConfirmExtractedDataProps {
  extractedData: ExtractedData
  receiptUrl: string
  onConfirm: (confirmedData: Partial<ExpenseFormData>) => void
  onCancel: () => void
}

export default function ConfirmExtractedData({
  extractedData,
  receiptUrl,
  onConfirm,
  onCancel
}: ConfirmExtractedDataProps) {
  const [formData, setFormData] = useState({
    merchant: extractedData.merchant || '',
    expense_date: extractedData.expense_date || '',
    amount: extractedData.amount || 0,
    tax_amount: extractedData.tax_amount || 0,
    currency: extractedData.currency || 'USD',
    category: extractedData.category || '',
    payment_method: extractedData.payment_method || '',
    receipt_number: extractedData.receipt_number || '',
    notes: ''
  })

  const confidence = extractedData.confidence || 0
  const requiresReview = extractedData.requires_review || confidence < 0.7
  const hasError = extractedData.error

  const handleConfirm = () => {
    if (!formData.merchant || !formData.expense_date || !formData.amount) {
      alert('Please fill in all required fields (Merchant, Date, Amount)')
      return
    }

    onConfirm({
      ...formData,
      receipt_urls: [receiptUrl]
    })
  }

  // Handle extraction error
  if (hasError) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-xl font-bold text-red-800">Extraction Failed</h2>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="bg-red-50 border border-red-200 p-4 rounded-md mb-4">
            <div className="flex items-start">
              <AlertTriangle className="w-5 h-5 text-red-600 mr-3 mt-0.5" />
              <div>
                <p className="font-semibold text-red-800">
                  Failed to extract data from receipt
                </p>
                <p className="text-sm text-red-700 mt-1">{extractedData.message}</p>
              </div>
            </div>
          </div>

          <p className="text-sm text-gray-600 mb-4">
            The receipt has been uploaded successfully, but we couldn't automatically extract the data.
            You can still manually enter the expense information using the form.
          </p>

          <div className="flex justify-end space-x-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                // Reset to empty form and continue
                setFormData({
                  merchant: '',
                  expense_date: new Date().toISOString().split('T')[0],
                  amount: 0,
                  tax_amount: 0,
                  currency: 'USD',
                  category: '',
                  payment_method: '',
                  receipt_number: '',
                  notes: ''
                })
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Enter Manually
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full my-8">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-xl font-bold">Confirm Extracted Data</h2>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Confidence Warning */}
          {requiresReview && (
            <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-md mb-4">
              <div className="flex items-start">
                <AlertTriangle className="w-5 h-5 text-yellow-600 mr-3 mt-0.5" />
                <div>
                  <p className="font-semibold text-yellow-800">
                    Low Confidence - Please Review Carefully
                  </p>
                  <p className="text-sm text-yellow-700 mt-1">
                    Confidence: {(confidence * 100).toFixed(0)}%
                    {confidence < 0.5 && ' - Many fields may be incorrect'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Extraction Method Info */}
          <div className="text-sm text-gray-600 mb-4 flex items-center">
            <span className="font-medium mr-2">Extracted using:</span>
            {extractedData.extraction_method === 'ai' ? (
              <span className="inline-flex items-center px-2 py-1 bg-purple-100 text-purple-800 rounded-md text-xs font-medium">
                🤖 AI (Gemini)
              </span>
            ) : (
              <span className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-xs font-medium">
                📝 Pattern Matching
              </span>
            )}
          </div>

          {/* Side-by-side layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: PDF Preview */}
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 border-b">
                <h3 className="font-semibold text-sm">Receipt Preview</h3>
              </div>
              <div className="p-4 bg-gray-100">
                <iframe
                  src={receiptUrl}
                  className="w-full h-96 border border-gray-300 rounded bg-white"
                  title="Receipt Preview"
                />
              </div>
            </div>

            {/* Right: Editable Form */}
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 border-b">
                <h3 className="font-semibold text-sm">Extracted Data (Editable)</h3>
              </div>
              <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
                {/* Merchant */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Merchant *
                    {!formData.merchant && (
                      <span className="text-red-500 ml-1">⚠️ Missing</span>
                    )}
                  </label>
                  <input
                    type="text"
                    value={formData.merchant}
                    onChange={(e) => setFormData({ ...formData, merchant: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    placeholder="Merchant name"
                  />
                </div>

                {/* Date */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Date *
                    {!formData.expense_date && (
                      <span className="text-red-500 ml-1">⚠️ Missing</span>
                    )}
                  </label>
                  <input
                    type="date"
                    value={formData.expense_date}
                    onChange={(e) => setFormData({ ...formData, expense_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Amount */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Amount *
                    {!formData.amount && (
                      <span className="text-red-500 ml-1">⚠️ Missing</span>
                    )}
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Tax Amount */}
                <div>
                  <label className="block text-sm font-medium mb-1">Tax Amount</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.tax_amount}
                    onChange={(e) => setFormData({ ...formData, tax_amount: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Currency */}
                <div>
                  <label className="block text-sm font-medium mb-1">Currency</label>
                  <select
                    value={formData.currency}
                    onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                    <option value="GHC">GHC</option>
                    <option value="JPY">JPY</option>
                  </select>
                </div>

                {/* Category */}
                <div>
                  <label className="block text-sm font-medium mb-1">Category</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select category</option>
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

                {/* Payment Method */}
                <div>
                  <label className="block text-sm font-medium mb-1">Payment Method</label>
                  <select
                    value={formData.payment_method}
                    onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select payment method</option>
                    <option value="cash">Cash</option>
                    <option value="credit_card">Credit Card</option>
                    <option value="debit_card">Debit Card</option>
                    <option value="mobile_money">Mobile Money</option>
                    <option value="bank_transfer">Bank Transfer</option>
                  </select>
                </div>

                {/* Receipt Number */}
                <div>
                  <label className="block text-sm font-medium mb-1">Receipt Number</label>
                  <input
                    type="text"
                    value={formData.receipt_number}
                    onChange={(e) => setFormData({ ...formData, receipt_number: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    placeholder="Optional"
                  />
                </div>

                {/* Notes */}
                <div>
                  <label className="block text-sm font-medium mb-1">Notes</label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    rows={2}
                    placeholder="Additional notes (optional)"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
            <button
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={!formData.merchant || !formData.expense_date || !formData.amount}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              Confirm & Save Expense
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
