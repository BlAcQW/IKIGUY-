/**
 * Contact Bulk Import Modal
 *
 * Allows importing contacts from Excel/CSV files with minimal data requirements.
 * Supports gradual data enrichment.
 */

import { useState } from 'react'
import { X, Upload, Download, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import api from '@/lib/api'

interface BulkImportResult {
  total_rows: number
  successful: number
  failed: number
  skipped: number
  customer_id: string
  errors: { row: number; error: string }[]
  created_contact_ids: string[]
}

interface ContactBulkImportModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export default function ContactBulkImportModal({
  isOpen,
  onClose,
  onSuccess
}: ContactBulkImportModalProps) {
  const [file, setFile] = useState<File | null>(null)
  const [customerName, setCustomerName] = useState('Imported Contacts')
  const [skipDuplicates, setSkipDuplicates] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [result, setResult] = useState<BulkImportResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      // Validate file type
      const validTypes = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      ]
      if (validTypes.includes(selectedFile.type) || selectedFile.name.endsWith('.csv') || selectedFile.name.endsWith('.xlsx')) {
        setFile(selectedFile)
        setError(null)
        setResult(null)
      } else {
        setError('Please select a CSV or Excel file (.csv, .xlsx, .xls)')
        setFile(null)
      }
    }
  }

  const handleDownloadTemplate = async () => {
    try {
      const response = await api.get('/crm/contacts/bulk-import/template', {
        responseType: 'blob'
      })

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'contact_import_template.xlsx')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download template:', err)
      setError('Failed to download template. Please try again.')
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload')
      return
    }

    setIsUploading(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post(
        `/crm/contacts/bulk-import/file?customer_name=${encodeURIComponent(customerName)}&skip_duplicates=${skipDuplicates}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      setResult(response.data)

      // If successful, notify parent to refresh data
      if (response.data.successful > 0) {
        setTimeout(() => {
          onSuccess()
        }, 2000)
      }
    } catch (err: any) {
      console.error('Upload failed:', err)
      setError(err.response?.data?.detail || 'Failed to import contacts. Please check the file format and try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleClose = () => {
    setFile(null)
    setResult(null)
    setError(null)
    setCustomerName('Imported Contacts')
    setSkipDuplicates(true)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold">Bulk Import Contacts</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="font-semibold text-blue-900 mb-2">How to use:</h3>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>Download the template or use your own Excel/CSV file</li>
              <li>Minimum required: phone numbers (other fields optional)</li>
              <li>Supported columns: phone, email, first_name, last_name, company, job_title, notes</li>
              <li>You can enrich data later by editing individual contacts</li>
            </ul>
          </div>

          {/* Template Download */}
          <div>
            <button
              onClick={handleDownloadTemplate}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              <Download className="w-4 h-4" />
              <span>Download Template</span>
            </button>
          </div>

          {/* Customer Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Customer Name
            </label>
            <input
              type="text"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              placeholder="Imported Contacts"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              All imported contacts will be associated with this customer
            </p>
          </div>

          {/* Skip Duplicates */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="skip_duplicates"
              checked={skipDuplicates}
              onChange={(e) => setSkipDuplicates(e.target.checked)}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
            <label htmlFor="skip_duplicates" className="ml-2 text-sm text-gray-700">
              Skip duplicate phone numbers
            </label>
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload File
            </label>
            <div className="flex items-center space-x-4">
              <label className="flex-1 flex items-center justify-center px-4 py-6 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50">
                <div className="text-center">
                  <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <span className="text-sm text-gray-600">
                    {file ? file.name : 'Click to select CSV or Excel file'}
                  </span>
                </div>
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4 flex items-start space-x-2">
              <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-red-900">Error</h4>
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          )}

          {/* Result Summary */}
          {result && (
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <div className="flex items-start space-x-2 mb-4">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-green-900">Import Complete</h4>
                  <p className="text-sm text-green-800">
                    Successfully imported {result.successful} of {result.total_rows} contacts
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-white rounded-md p-3">
                  <div className="text-2xl font-bold text-green-600">{result.successful}</div>
                  <div className="text-xs text-gray-600">Successful</div>
                </div>
                <div className="bg-white rounded-md p-3">
                  <div className="text-2xl font-bold text-red-600">{result.failed}</div>
                  <div className="text-xs text-gray-600">Failed</div>
                </div>
                <div className="bg-white rounded-md p-3">
                  <div className="text-2xl font-bold text-yellow-600">{result.skipped}</div>
                  <div className="text-xs text-gray-600">Skipped</div>
                </div>
              </div>

              {/* Error Details */}
              {result.errors.length > 0 && (
                <div className="mt-4">
                  <h5 className="font-semibold text-red-900 mb-2 flex items-center">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    Error Details
                  </h5>
                  <div className="bg-white rounded-md p-3 max-h-40 overflow-y-auto">
                    <ul className="text-xs text-red-800 space-y-1">
                      {result.errors.map((err, idx) => (
                        <li key={idx}>Row {err.row}: {err.error}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 px-6 py-4 border-t bg-gray-50">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            {result ? 'Close' : 'Cancel'}
          </button>
          {!result && (
            <button
              onClick={handleUpload}
              disabled={!file || isUploading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {isUploading ? 'Uploading...' : 'Upload & Import'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
