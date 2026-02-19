/**
 * Mobile Receipt Upload Component
 *
 * A reusable component for uploading receipt photos from mobile devices or PDFs from desktop.
 * Supports:
 * - Mobile camera capture (JPEG, PNG, HEIC)
 * - Photo library selection
 * - Desktop drag-and-drop and file picker
 * - PDF uploads
 * - Image preview before upload
 * - Client-side compression
 *
 * Usage:
 * ```tsx
 * import { MobileReceiptUpload } from '@shared/frontend/components/MobileReceiptUpload'
 *
 * <MobileReceiptUpload
 *   onUploadSuccess={(result) => {
 *     console.log('Receipt uploaded:', result)
 *     // Show confirmation modal with extracted data
 *   }}
 *   onError={(error) => {
 *     console.error('Upload failed:', error)
 *   }}
 *   useAI={false}  // Default to pattern matching
 * />
 * ```
 *
 * Author: AI Labs Africa Platform Team
 * Date: 2025-11-03
 * Version: 1.0.0
 */

import React, { useState, useRef, ChangeEvent } from 'react'
import Compressor from 'compressorjs'

// Types
export interface UploadResult {
  receipt_url: string
  receipt_path: string
  file_id: string
  file_type: string
  uploaded_at: string
  extracted_data?: ExtractedData
  requires_confirmation: boolean
  extraction_method?: 'pattern' | 'ai'
}

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
  extraction_method?: 'pattern' | 'ai'
  extraction_source?: string
  requires_review?: boolean
  error?: string
  message?: string
}

export interface MobileReceiptUploadProps {
  onUploadSuccess: (result: UploadResult) => void
  onError: (error: string) => void
  apiEndpoint?: string  // Default: '/finance/expenses/upload-receipt'
  useAI?: boolean  // Default: false (pattern matching)
  maxSizeMB?: number  // Default: 10MB for images, 25MB for PDFs
  showPreview?: boolean  // Default: true
  allowedTypes?: string[]  // Default: ['pdf', 'jpg', 'jpeg', 'png', 'heic']
  className?: string
}

/**
 * Mobile Receipt Upload Component
 *
 * Features:
 * - Auto-detects mobile vs desktop
 * - Camera capture on mobile
 * - Drag-and-drop on desktop
 * - Image compression
 * - File validation
 * - Loading states
 * - Preview before upload
 */
export const MobileReceiptUpload: React.FC<MobileReceiptUploadProps> = ({
  onUploadSuccess,
  onError,
  apiEndpoint = '/finance/expenses/upload-receipt',
  useAI = false,
  maxSizeMB = 10,
  showPreview = true,
  allowedTypes = ['pdf', 'jpg', 'jpeg', 'png', 'heic', 'heif'],
  className = ''
}) => {
  const [uploading, setUploading] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)

  // Detect if mobile device
  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)

  /**
   * Validate file type and size
   */
  const validateFile = (file: File): { valid: boolean; error?: string } => {
    const fileExt = file.name.toLowerCase().split('.').pop() || ''

    // Check file type
    if (!allowedTypes.includes(fileExt)) {
      return {
        valid: false,
        error: `Unsupported file type: ${fileExt}. Supported types: ${allowedTypes.join(', ')}`
      }
    }

    // Check file size
    const isPDF = fileExt === 'pdf'
    const maxSize = isPDF ? 25 * 1024 * 1024 : maxSizeMB * 1024 * 1024
    if (file.size > maxSize) {
      const maxMB = maxSize / (1024 * 1024)
      return {
        valid: false,
        error: `File too large (${(file.size / (1024 * 1024)).toFixed(1)}MB). Max: ${maxMB}MB`
      }
    }

    return { valid: true }
  }

  /**
   * Compress image before upload
   */
  const compressImage = (file: File): Promise<File | Blob> => {
    return new Promise((resolve, reject) => {
      // Don't compress PDFs
      if (file.type === 'application/pdf') {
        resolve(file)
        return
      }

      // Don't compress HE IC files (they're already efficient)
      if (file.type === 'image/heic' || file.type === 'image/heif') {
        resolve(file)
        return
      }

      new Compressor(file, {
        quality: 0.8,
        maxWidth: 2048,
        maxHeight: 2048,
        mimeType: 'image/jpeg',
        success: (result) => {
          resolve(result)
        },
        error: (err) => {
          console.warn('Image compression failed, using original:', err)
          resolve(file)  // Use original if compression fails
        }
      })
    })
  }

  /**
   * Generate preview for image files
   */
  const generatePreview = (file: File) => {
    if (file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreviewUrl(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    } else if (file.type === 'application/pdf') {
      setPreviewUrl('pdf')  // Special indicator for PDF
    }
  }

  /**
   * Upload file to server
   */
  const uploadFile = async (file: File | Blob) => {
    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file, selectedFile?.name || 'receipt.jpg')

      const url = `${apiEndpoint}?extract_data=true&use_ai=${useAI}`

      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        credentials: 'include',  // Include cookies for authentication
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Upload failed')
      }

      const result: UploadResult = await response.json()
      onUploadSuccess(result)

      // Clear preview and selected file
      setPreviewUrl(null)
      setSelectedFile(null)
    } catch (error: any) {
      onError(error.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  /**
   * Handle file selection
   */
  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file
    const validation = validateFile(file)
    if (!validation.valid) {
      onError(validation.error!)
      return
    }

    setSelectedFile(file)

    // Show preview
    if (showPreview) {
      generatePreview(file)
    } else {
      // Upload immediately if no preview
      const compressed = await compressImage(file)
      await uploadFile(compressed)
    }
  }

  /**
   * Handle drag and drop
   */
  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragOver(false)

    const file = event.dataTransfer.files[0]
    if (file) {
      const validation = validateFile(file)
      if (!validation.valid) {
        onError(validation.error!)
        return
      }

      setSelectedFile(file)
      if (showPreview) {
        generatePreview(file)
      }
    }
  }

  /**
   * Handle confirm upload (when preview is shown)
   */
  const handleConfirmUpload = async () => {
    if (!selectedFile) return

    const compressed = await compressImage(selectedFile)
    await uploadFile(compressed)
  }

  /**
   * Handle cancel
   */
  const handleCancel = () => {
    setSelectedFile(null)
    setPreviewUrl(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
    if (cameraInputRef.current) cameraInputRef.current.value = ''
  }

  return (
    <div className={`mobile-receipt-upload ${className}`}>
      {!previewUrl ? (
        // Upload UI
        <div
          className={`upload-area ${dragOver ? 'drag-over' : ''}`}
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          {/* Mobile: Camera + Photo Library */}
          {isMobile && (
            <div className="mobile-buttons">
              <button
                type="button"
                className="camera-button"
                onClick={() => cameraInputRef.current?.click()}
                disabled={uploading}
              >
                <span className="icon">📷</span>
                <span>Take Photo</span>
              </button>

              <button
                type="button"
                className="library-button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                <span className="icon">🖼️</span>
                <span>Photo Library</span>
              </button>

              {/* Camera input (opens camera) */}
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"  // Use back camera
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />

              {/* File input (opens photo library) */}
              <input
                ref={fileInputRef}
                type="file"
                accept={allowedTypes.map(t => `.${t}`).join(',')}
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
            </div>
          )}

          {/* Desktop: Drag-and-drop + File Picker */}
          {!isMobile && (
            <div className="desktop-upload">
              <div className="upload-icon">📄</div>
              <p className="upload-text">
                Drag and drop receipt here, or click to browse
              </p>
              <button
                type="button"
                className="browse-button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                Browse Files
              </button>

              <input
                ref={fileInputRef}
                type="file"
                accept={allowedTypes.map(t => `.${t}`).join(',')}
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />

              <p className="file-types">
                Supported: PDF, JPEG, PNG{isMobile ? ', HEIC' : ''}
              </p>
            </div>
          )}

          {/* Extraction Method Info */}
          <div className="extraction-info">
            <span className="extraction-badge">
              {useAI ? '🤖 AI Extraction (~$0.01)' : '⚡ Pattern Matching (Free)'}
            </span>
          </div>
        </div>
      ) : (
        // Preview UI
        <div className="preview-container">
          <h3>Preview</h3>

          {previewUrl === 'pdf' ? (
            <div className="pdf-preview">
              <div className="pdf-icon">📄</div>
              <p>{selectedFile?.name}</p>
              <p className="file-size">
                {((selectedFile?.size || 0) / 1024).toFixed(1)} KB
              </p>
            </div>
          ) : (
            <img
              src={previewUrl || ''}
              alt="Receipt preview"
              className="image-preview"
            />
          )}

          <div className="preview-actions">
            <button
              type="button"
              className="cancel-button"
              onClick={handleCancel}
              disabled={uploading}
            >
              Cancel
            </button>
            <button
              type="button"
              className="upload-button"
              onClick={handleConfirmUpload}
              disabled={uploading}
            >
              {uploading ? 'Uploading...' : 'Upload & Extract'}
            </button>
          </div>

          {uploading && (
            <div className="upload-progress">
              <div className="spinner" />
              <p>
                {useAI
                  ? 'Uploading and extracting with AI...'
                  : 'Uploading and extracting data...'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Default Styles (can be overridden) */}
      <style jsx>{`
        .mobile-receipt-upload {
          width: 100%;
          max-width: 500px;
          margin: 0 auto;
        }

        .upload-area {
          border: 2px dashed #ccc;
          border-radius: 8px;
          padding: 24px;
          text-align: center;
          transition: all 0.3s;
        }

        .upload-area.drag-over {
          border-color: #4CAF50;
          background-color: #f0f8f0;
        }

        .mobile-buttons {
          display: flex;
          gap: 12px;
          justify-content: center;
        }

        .camera-button,
        .library-button {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 16px 24px;
          border: 2px solid #2196F3;
          border-radius: 8px;
          background: white;
          cursor: pointer;
          transition: all 0.2s;
        }

        .camera-button:hover,
        .library-button:hover {
          background: #2196F3;
          color: white;
        }

        .camera-button:disabled,
        .library-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .icon {
          font-size: 32px;
        }

        .desktop-upload {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
        }

        .upload-icon {
          font-size: 48px;
        }

        .upload-text {
          color: #666;
          margin: 0;
        }

        .browse-button {
          padding: 12px 24px;
          background: #2196F3;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 16px;
        }

        .browse-button:hover {
          background: #1976D2;
        }

        .browse-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .file-types {
          font-size: 12px;
          color: #999;
          margin: 8px 0 0 0;
        }

        .extraction-info {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid #eee;
        }

        .extraction-badge {
          display: inline-block;
          padding: 6px 12px;
          background: #f5f5f5;
          border-radius: 4px;
          font-size: 13px;
          color: #666;
        }

        .preview-container {
          text-align: center;
        }

        .preview-container h3 {
          margin: 0 0 16px 0;
        }

        .pdf-preview {
          padding: 32px;
          background: #f5f5f5;
          border-radius: 8px;
          margin-bottom: 16px;
        }

        .pdf-icon {
          font-size: 64px;
        }

        .file-size {
          color: #666;
          font-size: 14px;
        }

        .image-preview {
          max-width: 100%;
          max-height: 400px;
          border-radius: 8px;
          margin-bottom: 16px;
        }

        .preview-actions {
          display: flex;
          gap: 12px;
          justify-content: center;
        }

        .cancel-button,
        .upload-button {
          padding: 12px 24px;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 16px;
        }

        .cancel-button {
          background: #f5f5f5;
          color: #333;
        }

        .upload-button {
          background: #4CAF50;
          color: white;
        }

        .cancel-button:hover {
          background: #e0e0e0;
        }

        .upload-button:hover {
          background: #45a049;
        }

        .cancel-button:disabled,
        .upload-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .upload-progress {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid #eee;
        }

        .spinner {
          width: 32px;
          height: 32px;
          border: 3px solid #f3f3f3;
          border-top: 3px solid #2196F3;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 12px auto;
        }

        @keyframes spin {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }

        .upload-progress p {
          color: #666;
          font-size: 14px;
        }
      `}</style>
    </div>
  )
}

export default MobileReceiptUpload
