/**
 * ReceiptUploadModal Component
 * Modal for uploading expense receipts with drag & drop and camera support
 */

import { useState } from 'react'
import { X, Upload, Camera, FileText } from 'lucide-react'

interface ReceiptUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onUpload: (files: File[]) => void
}

export default function ReceiptUploadModal({
  isOpen,
  onClose,
  onUpload
}: ReceiptUploadModalProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)

  if (!isOpen) return null

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
    handleFiles(files)
  }

  const handleFiles = (files: File[]) => {
    const validFiles = files.filter((file) => {
      const isImage = file.type.startsWith('image/')
      const isPDF = file.type === 'application/pdf'
      return isImage || isPDF
    })

    if (validFiles.length > 0) {
      setSelectedFiles((prev) => [...prev, ...validFiles])
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files)
      handleFiles(files)
    }
  }

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = () => {
    if (selectedFiles.length > 0) {
      onUpload(selectedFiles)
      setSelectedFiles([])
      onClose()
    }
  }

  const handleCancel = () => {
    setSelectedFiles([])
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={handleCancel}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <h2 className="text-xl font-semibold text-gray-900">Upload Receipts</h2>
            <button
              onClick={handleCancel}
              className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 space-y-4">
            {/* Drag and Drop Zone */}
            <div
              className={`p-8 border-2 border-dashed rounded-lg transition-all ${
                isDragging
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-300 hover:border-indigo-400'
              }`}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              <div className="text-center">
                <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-sm text-gray-600 mb-2">
                  Drag and drop receipt files here, or click to select
                </p>
                <p className="text-xs text-gray-500">
                  Supports PDF and image files (JPG, PNG, etc.)
                </p>
              </div>
            </div>

            {/* Upload Options */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label className="cursor-pointer">
                <div className="px-4 py-3 border-2 border-dashed border-gray-300 rounded-md hover:border-indigo-500 transition-colors text-center">
                  <Upload className="w-5 h-5 mx-auto mb-1 text-gray-400" />
                  <span className="text-sm text-gray-600">Choose Files</span>
                  <p className="text-xs text-gray-500 mt-1">Select multiple</p>
                </div>
                <input
                  type="file"
                  className="hidden"
                  accept="image/*,.pdf"
                  multiple
                  onChange={handleFileSelect}
                />
              </label>

              <label className="cursor-pointer">
                <div className="px-4 py-3 border-2 border-dashed border-gray-300 rounded-md hover:border-indigo-500 transition-colors text-center">
                  <Camera className="w-5 h-5 mx-auto mb-1 text-gray-400" />
                  <span className="text-sm text-gray-600">Take Photo</span>
                  <p className="text-xs text-gray-500 mt-1">Use camera</p>
                </div>
                <input
                  type="file"
                  className="hidden"
                  accept="image/*"
                  capture="environment"
                  onChange={handleFileSelect}
                />
              </label>
            </div>

            {/* Selected Files */}
            {selectedFiles.length > 0 && (
              <div className="mt-4 space-y-2">
                <h3 className="text-sm font-medium text-gray-700">
                  Selected Files ({selectedFiles.length})
                </h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {selectedFiles.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded-md"
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
                        <span className="text-sm text-gray-700 truncate">{file.name}</span>
                        <span className="text-xs text-gray-500 flex-shrink-0">
                          ({(file.size / 1024).toFixed(1)} KB)
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-red-600 hover:bg-red-50 rounded-md transition-colors"
                        aria-label="Remove file"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Info */}
            <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-md">
              <p className="text-xs text-indigo-800">
                <strong>Tip:</strong> You can upload multiple receipts at once. Supported formats: PDF, JPG, PNG, and other image types.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
            <button
              onClick={handleCancel}
              className="px-4 py-2 text-gray-700 hover:text-gray-900 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={selectedFiles.length === 0}
              className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Upload {selectedFiles.length > 0 && `(${selectedFiles.length})`}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
