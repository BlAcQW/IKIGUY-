/**
 * ProjectAttachments Component
 *
 * Manages file attachments for projects with support for:
 * - Documents (PDF, DOC, XLS, etc.)
 * - Images (JPG, PNG, GIF, etc.)
 * - Audio (MP3, WAV, M4A, etc.)
 * - Video (MP4, MOV, AVI, etc.)
 * - Archives (ZIP, RAR, etc.)
 * - Design files (PSD, AI, Sketch, Figma, etc.)
 */

import { useState, useRef } from 'react'
import {
  FileText,
  Image,
  Music,
  Video,
  Archive,
  File,
  Upload,
  X,
  Download,
  Play,
  Pause,
  Eye,
  Loader2
} from 'lucide-react'
import api from '../services/api'

interface Attachment {
  id: string
  original_filename: string
  stored_filename: string
  file_path: string
  file_size: number
  file_type: string
  mime_type: string
  uploaded_by: string
  uploaded_at: string
}

interface PendingFile {
  id: string
  file: File
  original_filename: string
  file_size: number
  file_type: string
}

interface ProjectAttachmentsProps {
  projectId?: string
  attachments: Attachment[]
  onAttachmentsChange: (attachments: Attachment[]) => void
  pendingFiles?: PendingFile[]
  onPendingFilesChange?: (files: PendingFile[]) => void
}

type FileCategory = 'document' | 'image' | 'audio' | 'video' | 'archive' | 'design' | 'other'

const FILE_CATEGORIES: Record<string, FileCategory> = {
  // Documents
  '.pdf': 'document',
  '.doc': 'document',
  '.docx': 'document',
  '.xls': 'document',
  '.xlsx': 'document',
  '.ppt': 'document',
  '.pptx': 'document',
  '.txt': 'document',
  '.rtf': 'document',
  '.csv': 'document',
  // Images
  '.jpg': 'image',
  '.jpeg': 'image',
  '.png': 'image',
  '.gif': 'image',
  '.bmp': 'image',
  '.webp': 'image',
  '.svg': 'image',
  '.ico': 'image',
  // Audio
  '.mp3': 'audio',
  '.wav': 'audio',
  '.m4a': 'audio',
  '.ogg': 'audio',
  '.flac': 'audio',
  '.aac': 'audio',
  '.wma': 'audio',
  // Video
  '.mp4': 'video',
  '.mov': 'video',
  '.avi': 'video',
  '.mkv': 'video',
  '.webm': 'video',
  '.wmv': 'video',
  '.flv': 'video',
  '.m4v': 'video',
  // Archives
  '.zip': 'archive',
  '.rar': 'archive',
  '.7z': 'archive',
  '.tar': 'archive',
  '.gz': 'archive',
  // Design
  '.psd': 'design',
  '.ai': 'design',
  '.sketch': 'design',
  '.fig': 'design',
  '.xd': 'design'
}

const CATEGORY_COLORS: Record<FileCategory, string> = {
  document: 'bg-blue-100 text-blue-600',
  image: 'bg-green-100 text-green-600',
  audio: 'bg-purple-100 text-purple-600',
  video: 'bg-red-100 text-red-600',
  archive: 'bg-yellow-100 text-yellow-600',
  design: 'bg-pink-100 text-pink-600',
  other: 'bg-gray-100 text-gray-600'
}

const CATEGORY_ICONS: Record<FileCategory, React.ComponentType<{ className?: string }>> = {
  document: FileText,
  image: Image,
  audio: Music,
  video: Video,
  archive: Archive,
  design: File,
  other: File
}

export default function ProjectAttachments({
  projectId,
  attachments,
  onAttachmentsChange,
  pendingFiles = [],
  onPendingFilesChange
}: ProjectAttachmentsProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [previewType, setPreviewType] = useState<FileCategory | null>(null)
  const [playingAudio, setPlayingAudio] = useState<string | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const getFileCategory = (fileType: string): FileCategory => {
    return FILE_CATEGORIES[fileType.toLowerCase()] || 'other'
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    // If no projectId, stage files locally for later upload
    if (!projectId) {
      const newPendingFiles: PendingFile[] = []
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const ext = '.' + file.name.split('.').pop()?.toLowerCase()
        newPendingFiles.push({
          id: `pending-${Date.now()}-${i}`,
          file,
          original_filename: file.name,
          file_size: file.size,
          file_type: ext
        })
      }
      if (onPendingFilesChange) {
        onPendingFilesChange([...pendingFiles, ...newPendingFiles])
      }
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      return
    }

    setIsUploading(true)
    setUploadProgress(0)

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const formData = new FormData()
        formData.append('file', file)

        const response = await api.post(
          `/projects/${projectId}/attachments`,
          formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (progressEvent) => {
              const total = progressEvent.total || file.size
              const progress = Math.round((progressEvent.loaded * 100) / total)
              setUploadProgress(progress)
            }
          }
        )

        // Add new attachment to list
        if (response.data.attachment) {
          onAttachmentsChange([...attachments, response.data.attachment])
        }
      }

      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      console.error('Failed to upload file:', error)
      alert('Failed to upload file. Please try again.')
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    const files = e.dataTransfer.files
    if (!files || files.length === 0) return

    // If no projectId, stage files locally for later upload
    if (!projectId) {
      const newPendingFiles: PendingFile[] = []
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const ext = '.' + file.name.split('.').pop()?.toLowerCase()
        newPendingFiles.push({
          id: `pending-${Date.now()}-${i}`,
          file,
          original_filename: file.name,
          file_size: file.size,
          file_type: ext
        })
      }
      if (onPendingFilesChange) {
        onPendingFilesChange([...pendingFiles, ...newPendingFiles])
      }
      return
    }

    setIsUploading(true)
    setUploadProgress(0)

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const formData = new FormData()
        formData.append('file', file)

        const response = await api.post(
          `/projects/${projectId}/attachments`,
          formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (progressEvent) => {
              const total = progressEvent.total || file.size
              const progress = Math.round((progressEvent.loaded * 100) / total)
              setUploadProgress(progress)
            }
          }
        )

        if (response.data.attachment) {
          onAttachmentsChange([...attachments, response.data.attachment])
        }
      }
    } catch (error) {
      console.error('Failed to upload file:', error)
      alert('Failed to upload file. Please try again.')
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const handleDownload = async (attachment: Attachment) => {
    try {
      const response = await api.get(
        `/projects/${projectId}/attachments/${attachment.id}/download`,
        { responseType: 'blob' }
      )

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', attachment.original_filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download file:', error)
      alert('Failed to download file. Please try again.')
    }
  }

  const handleDelete = async (attachmentId: string) => {
    if (!confirm('Are you sure you want to delete this attachment?')) return

    try {
      await api.delete(`/projects/${projectId}/attachments/${attachmentId}`)
      onAttachmentsChange(attachments.filter((att) => att.id !== attachmentId))
    } catch (error) {
      console.error('Failed to delete attachment:', error)
      alert('Failed to delete attachment. Please try again.')
    }
  }

  const handlePreview = async (attachment: Attachment) => {
    const category = getFileCategory(attachment.file_type)

    if (category === 'image' || category === 'video' || category === 'audio') {
      try {
        const response = await api.get(
          `/projects/${projectId}/attachments/${attachment.id}/download`,
          { responseType: 'blob' }
        )

        const url = window.URL.createObjectURL(new Blob([response.data]))
        setPreviewUrl(url)
        setPreviewType(category)
      } catch (error) {
        console.error('Failed to preview file:', error)
        alert('Failed to preview file.')
      }
    }
  }

  const closePreview = () => {
    if (previewUrl) {
      window.URL.revokeObjectURL(previewUrl)
    }
    setPreviewUrl(null)
    setPreviewType(null)
  }

  const toggleAudioPlayback = async (attachment: Attachment) => {
    if (playingAudio === attachment.id) {
      // Stop playing
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
      setPlayingAudio(null)
    } else {
      // Start playing
      try {
        const response = await api.get(
          `/projects/${projectId}/attachments/${attachment.id}/download`,
          { responseType: 'blob' }
        )

        const url = window.URL.createObjectURL(new Blob([response.data]))
        const audio = new Audio(url)
        audio.onended = () => {
          setPlayingAudio(null)
          window.URL.revokeObjectURL(url)
        }
        audio.play()
        audioRef.current = audio
        setPlayingAudio(attachment.id)
      } catch (error) {
        console.error('Failed to play audio:', error)
      }
    }
  }

  // Group attachments by category
  const groupedAttachments = attachments.reduce(
    (acc, attachment) => {
      const category = getFileCategory(attachment.file_type)
      if (!acc[category]) {
        acc[category] = []
      }
      acc[category].push(attachment)
      return acc
    },
    {} as Record<FileCategory, Attachment[]>
  )

  const categoryOrder: FileCategory[] = ['image', 'video', 'audio', 'document', 'design', 'archive', 'other']

  const handleRemovePendingFile = (fileId: string) => {
    if (onPendingFilesChange) {
      onPendingFilesChange(pendingFiles.filter((f) => f.id !== fileId))
    }
  }

  // Group pending files by category
  const groupedPendingFiles = pendingFiles.reduce(
    (acc, file) => {
      const category = getFileCategory(file.file_type)
      if (!acc[category]) {
        acc[category] = []
      }
      acc[category].push(file)
      return acc
    },
    {} as Record<FileCategory, PendingFile[]>
  )

  return (
    <div className="space-y-4">
      {/* Upload Section - using same pattern as FileUpload component */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          isDragOver
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-gray-50'
        } ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-blue-400'}`}
        onDragOver={handleDragOver}
        onDragEnter={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          multiple
          disabled={isUploading}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.rtf,.csv,.jpg,.jpeg,.png,.gif,.bmp,.webp,.svg,.ico,.mp3,.wav,.m4a,.ogg,.flac,.aac,.wma,.mp4,.mov,.avi,.mkv,.webm,.wmv,.flv,.m4v,.zip,.rar,.7z,.tar,.gz,.psd,.ai,.sketch,.fig,.xd"
        />

        {isUploading ? (
          <div className="space-y-2">
            <Loader2 className="w-8 h-8 mx-auto animate-spin text-blue-500" />
            <p className="text-sm text-gray-600">Uploading... {uploadProgress}%</p>
            <div className="w-full bg-gray-200 rounded-full h-2 max-w-xs mx-auto">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        ) : isDragOver ? (
          <div>
            <Upload className="w-10 h-10 mx-auto text-blue-500 mb-2" />
            <p className="text-sm text-blue-600 font-medium">
              Drop files here to upload
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload className="w-8 h-8 mx-auto text-gray-400" />
            <p className="text-sm font-medium text-gray-700">
              Drop files here or click to browse
            </p>
            <p className="text-xs text-gray-500">
              Supports documents, images, audio, video, and design files (max 100MB)
            </p>
          </div>
        )}
      </div>

      {/* Attachments List */}
      {attachments.length > 0 && (
        <div className="space-y-4">
          {categoryOrder.map((category) => {
            const categoryAttachments = groupedAttachments[category]
            if (!categoryAttachments || categoryAttachments.length === 0) return null

            const Icon = CATEGORY_ICONS[category]
            const colorClass = CATEGORY_COLORS[category]

            return (
              <div key={category}>
                <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                  <span className={`p-1 rounded mr-2 ${colorClass}`}>
                    <Icon className="w-4 h-4" />
                  </span>
                  {category.charAt(0).toUpperCase() + category.slice(1)}s ({categoryAttachments.length})
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {categoryAttachments.map((attachment) => (
                    <AttachmentCard
                      key={attachment.id}
                      attachment={attachment}
                      category={category}
                      onDownload={() => handleDownload(attachment)}
                      onDelete={() => handleDelete(attachment.id)}
                      onPreview={() => handlePreview(attachment)}
                      onToggleAudio={() => toggleAudioPlayback(attachment)}
                      isPlaying={playingAudio === attachment.id}
                      formatFileSize={formatFileSize}
                    />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Pending Files List (for new projects before save) */}
      {pendingFiles.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center">
            <span className="text-sm font-medium text-amber-600 bg-amber-50 px-2 py-1 rounded">
              Files staged for upload (will be uploaded when project is saved)
            </span>
          </div>
          {categoryOrder.map((category) => {
            const categoryFiles = groupedPendingFiles[category]
            if (!categoryFiles || categoryFiles.length === 0) return null

            const Icon = CATEGORY_ICONS[category]
            const colorClass = CATEGORY_COLORS[category]

            return (
              <div key={`pending-${category}`}>
                <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                  <span className={`p-1 rounded mr-2 ${colorClass}`}>
                    <Icon className="w-4 h-4" />
                  </span>
                  {category.charAt(0).toUpperCase() + category.slice(1)}s ({categoryFiles.length})
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {categoryFiles.map((file) => (
                    <PendingFileCard
                      key={file.id}
                      file={file}
                      category={category}
                      onRemove={() => handleRemovePendingFile(file.id)}
                      formatFileSize={formatFileSize}
                    />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {attachments.length === 0 && pendingFiles.length === 0 && (
        <p className="text-center text-gray-500 py-4">
          No attachments yet. Upload files to get started.
        </p>
      )}

      {/* Preview Modal */}
      {previewUrl && previewType && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50"
          onClick={closePreview}
        >
          <div
            className="max-w-4xl max-h-[90vh] bg-white rounded-lg overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-end p-2 bg-gray-100">
              <button
                onClick={closePreview}
                className="p-1 hover:bg-gray-200 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4">
              {previewType === 'image' && (
                <img
                  src={previewUrl}
                  alt="Preview"
                  className="max-w-full max-h-[70vh] object-contain mx-auto"
                />
              )}
              {previewType === 'video' && (
                <video
                  src={previewUrl}
                  controls
                  className="max-w-full max-h-[70vh] mx-auto"
                />
              )}
              {previewType === 'audio' && (
                <audio src={previewUrl} controls className="w-full" />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

interface AttachmentCardProps {
  attachment: Attachment
  category: FileCategory
  onDownload: () => void
  onDelete: () => void
  onPreview: () => void
  onToggleAudio: () => void
  isPlaying: boolean
  formatFileSize: (bytes: number) => string
}

function AttachmentCard({
  attachment,
  category,
  onDownload,
  onDelete,
  onPreview,
  onToggleAudio,
  isPlaying,
  formatFileSize
}: AttachmentCardProps) {
  const Icon = CATEGORY_ICONS[category]
  const colorClass = CATEGORY_COLORS[category]

  const canPreview = ['image', 'video', 'audio'].includes(category)

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
      <div className="flex items-center space-x-3 flex-1 min-w-0">
        <div className={`p-2 rounded-lg ${colorClass}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {attachment.original_filename}
          </p>
          <p className="text-xs text-gray-500">
            {formatFileSize(attachment.file_size)} •{' '}
            {new Date(attachment.uploaded_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-1 ml-2">
        {category === 'audio' && (
          <button
            type="button"
            onClick={onToggleAudio}
            className="p-1.5 text-purple-600 hover:bg-purple-100 rounded transition-colors"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
        )}

        {canPreview && category !== 'audio' && (
          <button
            type="button"
            onClick={onPreview}
            className="p-1.5 text-gray-600 hover:bg-gray-200 rounded transition-colors"
            title="Preview"
          >
            <Eye className="w-4 h-4" />
          </button>
        )}

        <button
          type="button"
          onClick={onDownload}
          className="p-1.5 text-blue-600 hover:bg-blue-100 rounded transition-colors"
          title="Download"
        >
          <Download className="w-4 h-4" />
        </button>

        <button
          type="button"
          onClick={onDelete}
          className="p-1.5 text-red-600 hover:bg-red-100 rounded transition-colors"
          title="Delete"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

interface PendingFileCardProps {
  file: PendingFile
  category: FileCategory
  onRemove: () => void
  formatFileSize: (bytes: number) => string
}

function PendingFileCard({
  file,
  category,
  onRemove,
  formatFileSize
}: PendingFileCardProps) {
  const Icon = CATEGORY_ICONS[category]
  const colorClass = CATEGORY_COLORS[category]

  return (
    <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg border border-amber-200 hover:border-amber-300 transition-colors">
      <div className="flex items-center space-x-3 flex-1 min-w-0">
        <div className={`p-2 rounded-lg ${colorClass}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {file.original_filename}
          </p>
          <p className="text-xs text-gray-500">
            {formatFileSize(file.file_size)} • Pending upload
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-1 ml-2">
        <button
          type="button"
          onClick={onRemove}
          className="p-1.5 text-red-600 hover:bg-red-100 rounded transition-colors"
          title="Remove"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

export type { PendingFile }
