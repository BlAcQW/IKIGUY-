/**
 * VoiceUploadDialog Component
 *
 * Dialog for uploading custom voice reference audio files.
 * Handles file validation, transcript input, and upload progress.
 */

import { useState, useRef } from 'react'
import { X, Upload, FileAudio, AlertCircle, CheckCircle, Info } from 'lucide-react'

interface VoiceUploadDialogProps {
  onClose: () => void
  onUploadSuccess: (voiceId: string, voiceName: string) => void
}

export default function VoiceUploadDialog({ onClose, onUploadSuccess }: VoiceUploadDialogProps) {
  const [file, setFile] = useState<File | null>(null)
  const [voiceName, setVoiceName] = useState('')
  const [refText, setRefText] = useState('')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // File validation
  const validateFile = (file: File): string | null => {
    // Check file type
    if (!file.type.match(/audio\/(wav|mpeg|mp3)/)) {
      return 'Only WAV and MP3 files are supported'
    }

    // Check file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      return 'File size must be less than 50MB'
    }

    return null
  }

  const handleFileSelect = (selectedFile: File) => {
    const error = validateFile(selectedFile)
    if (error) {
      setError(error)
      return
    }

    setFile(selectedFile)
    setError(null)

    // Auto-fill voice name from filename
    if (!voiceName) {
      const name = selectedFile.name.replace(/\.(wav|mp3)$/i, '').replace(/_/g, ' ')
      setVoiceName(name)
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
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file || !voiceName) {
      setError('Please provide both file and voice name')
      return
    }

    setUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('voice_name', voiceName)
      formData.append('ref_text', refText || '')

      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('Please login to upload custom voices')
      }

      const response = await fetch('/api/v1/voice-greetings/voices/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }))
        throw new Error(errorData.detail || 'Failed to upload voice')
      }

      const data = await response.json()
      onUploadSuccess(data.voice_id, data.voice_name)
    } catch (err: any) {
      console.error('Voice upload error:', err)
      setError(err.message || 'Failed to upload voice')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Upload className="w-6 h-6 text-purple-600" />
            <h3 className="text-xl font-bold text-gray-900">Upload Custom Voice</h3>
          </div>
          <button
            onClick={onClose}
            disabled={uploading}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Info Message */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">Voice Upload Guidelines:</p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>Upload a <strong>5-60 second</strong> audio clip of the person speaking</li>
                  <li>Use <strong>WAV or MP3</strong> format</li>
                  <li>Ensure <strong>clear audio</strong> without background noise</li>
                  <li>The voice will be cloned for your custom greetings</li>
                </ul>
              </div>
            </div>
          </div>

          {/* File Upload Area */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? 'border-purple-500 bg-purple-50'
                : file
                ? 'border-green-500 bg-green-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/wav,audio/mpeg,audio/mp3"
              onChange={handleFileInputChange}
              className="hidden"
            />

            {file ? (
              <div className="space-y-3">
                <CheckCircle className="w-12 h-12 text-green-600 mx-auto" />
                <div>
                  <p className="font-medium text-gray-900">{file.name}</p>
                  <p className="text-sm text-gray-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setFile(null)
                    if (fileInputRef.current) {
                      fileInputRef.current.value = ''
                    }
                  }}
                  className="text-sm text-purple-600 hover:text-purple-700"
                >
                  Change File
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <FileAudio className="w-12 h-12 text-gray-400 mx-auto" />
                <div>
                  <p className="text-gray-700 font-medium">Drop audio file here</p>
                  <p className="text-sm text-gray-500">or click to browse</p>
                </div>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="mt-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
                >
                  Select File
                </button>
              </div>
            )}
          </div>

          {/* Voice Name Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Voice Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={voiceName}
              onChange={(e) => setVoiceName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="e.g., Pastor Smith, Senior Leader"
              disabled={uploading}
            />
          </div>

          {/* Reference Text Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reference Text (Optional)
            </label>
            <textarea
              value={refText}
              onChange={(e) => setRefText(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Transcript of what's being said in the audio file..."
              rows={3}
              disabled={uploading}
            />
            <p className="text-xs text-gray-500 mt-1">
              If you know what's being said in the audio, enter it here for better results.
              Leave empty if unknown.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t">
          <button
            type="button"
            onClick={onClose}
            disabled={uploading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleUpload}
            disabled={!file || !voiceName || uploading}
            className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload Voice
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
