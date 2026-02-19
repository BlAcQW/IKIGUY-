/**
 * FileUpload Component
 *
 * Handles PDF receipt uploads with optional AI extraction.
 * - Accepts PDF files only
 * - Optional AI extraction (costs $0.01 per receipt)
 * - Shows loading state during upload and extraction
 * - Calls onUploadComplete with extracted data
 */

import { useState } from 'react'
import { Upload } from 'lucide-react'
import api from '../services/api'

export interface ExtractedData {
  merchant?: string
  expense_date?: string
  amount?: number
  tax_amount?: number
  currency?: string
  category?: string
  payment_method?: string
  receipt_number?: string
  confidence?: number
  extraction_method?: string
  requires_review?: boolean
  error?: string
  message?: string
}

export interface UploadResult {
  receipt_url: string
  file_id: string
  uploaded_at: string
  extracted_data: ExtractedData
  requires_confirmation: boolean
  extraction_method: 'pattern' | 'ai'
}

interface FileUploadProps {
  onUploadComplete: (result: UploadResult) => void
}

export default function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [useAI, setUseAI] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  const handleFileChange = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Only PDF files are supported')
      return
    }

    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post(
        `/finance/expenses/upload-receipt?extract_data=true&use_ai=${useAI}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )

      onUploadComplete(response.data)
    } catch (error: any) {
      console.error('Upload failed:', error)
      const errorMsg = error?.response?.data?.detail || 'Upload failed. Please try again.'
      alert(errorMsg)
    } finally {
      setUploading(false)
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0])
    }
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-lg font-semibold mb-4">Upload Receipt (PDF)</h3>

      {/* AI Extraction Checkbox */}
      <label className="flex items-center space-x-2 mb-4">
        <input
          type="checkbox"
          checked={useAI}
          onChange={(e) => setUseAI(e.target.checked)}
          disabled={uploading}
          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
        />
        <span className="text-sm text-gray-700">
          Use AI extraction (more accurate, costs $0.01 per receipt)
        </span>
      </label>

      {/* Drag & Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-gray-50'
        } ${uploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-blue-400'}`}
      >
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
          disabled={uploading}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />

        {uploading ? (
          <div className="space-y-2">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="text-sm text-gray-600">
              Uploading and extracting data...
            </p>
            <p className="text-xs text-gray-500">
              Using {useAI ? 'AI (Gemini)' : 'Pattern Matching'}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">
              Drop your PDF receipt here or click to browse
            </p>
            <p className="text-xs text-gray-500">
              PDF files only. Max file size: 10MB
            </p>
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
        <p className="text-xs text-blue-800">
          <strong>How it works:</strong>
        </p>
        <ol className="text-xs text-blue-700 mt-1 ml-4 list-decimal space-y-1">
          <li>Upload your PDF receipt</li>
          <li>We'll extract merchant, date, amount, and other details</li>
          <li>Review and confirm the extracted data</li>
          <li>Save to your expense records</li>
        </ol>
      </div>
    </div>
  )
}
