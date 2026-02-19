import { useState, useEffect } from 'react'
import {
  FileText,
  Upload,
  Download,
  Edit3,
  Trash2,
  X,
  Eye,
  EyeOff,
  Save,
  Copy,
  Check
} from 'lucide-react'
import axios from '../lib/axios-config'

interface Material {
  id: string
  title: string
  description?: string
  file_name: string
  file_size: number
  file_type: string
  material_type: string
  is_public: boolean
  display_on_landing: boolean
  display_order: number
  created_at: string
  download_url: string
}

interface ConferenceMaterialsProps {
  conferenceId: string
}

export default function ConferenceMaterials({ conferenceId }: ConferenceMaterialsProps) {
  const [materials, setMaterials] = useState<Material[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  // Upload form state
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadDescription, setUploadDescription] = useState('')
  const [uploadType, setUploadType] = useState('other')
  const [uploadPublic, setUploadPublic] = useState(true)
  const [uploadLanding, setUploadLanding] = useState(false)
  const [uploadOrder, setUploadOrder] = useState(0)

  // Edit form state
  const [editTitle, setEditTitle] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editType, setEditType] = useState('')
  const [editPublic, setEditPublic] = useState(true)
  const [editLanding, setEditLanding] = useState(false)
  const [editOrder, setEditOrder] = useState(0)

  useEffect(() => {
    loadMaterials()
  }, [conferenceId])

  const loadMaterials = async () => {
    setLoading(true)
    try {
      const response = await axios.get(
        `/api/v1/conferences/${conferenceId}/materials?public_only=false`
      )
      setMaterials(response.data.materials || [])
    } catch (error) {
      console.error('Failed to load materials:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!uploadFile) return

    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      formData.append('title', uploadTitle)
      formData.append('description', uploadDescription)
      formData.append('material_type', uploadType)
      formData.append('is_public', uploadPublic.toString())
      formData.append('display_on_landing', uploadLanding.toString())
      formData.append('display_order', uploadOrder.toString())

      await axios.post(
        `/api/v1/conferences/${conferenceId}/materials`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      // Reset form
      setUploadFile(null)
      setUploadTitle('')
      setUploadDescription('')
      setUploadType('other')
      setUploadPublic(true)
      setUploadLanding(false)
      setUploadOrder(0)
      setShowUploadForm(false)

      // Reload materials
      await loadMaterials()
      alert('Material uploaded successfully!')
    } catch (error: any) {
      console.error('Upload failed:', error)
      alert(error.response?.data?.detail || 'Failed to upload material')
    } finally {
      setUploading(false)
    }
  }

  const handleEdit = (material: Material) => {
    setEditingId(material.id)
    setEditTitle(material.title)
    setEditDescription(material.description || '')
    setEditType(material.material_type)
    setEditPublic(material.is_public)
    setEditLanding(material.display_on_landing)
    setEditOrder(material.display_order)
  }

  const handleSaveEdit = async (materialId: string) => {
    try {
      await axios.put(
        `/api/v1/conference-materials/${materialId}`,
        {
          title: editTitle,
          description: editDescription,
          material_type: editType,
          is_public: editPublic,
          display_on_landing: editLanding,
          display_order: editOrder
        }
      )

      setEditingId(null)
      await loadMaterials()
      alert('Material updated successfully!')
    } catch (error: any) {
      console.error('Update failed:', error)
      alert(error.response?.data?.detail || 'Failed to update material')
    }
  }

  const handleDelete = async (materialId: string, title: string) => {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) return

    try {
      await axios.delete(`/api/v1/conference-materials/${materialId}`)

      await loadMaterials()
      alert('Material deleted successfully!')
    } catch (error: any) {
      console.error('Delete failed:', error)
      alert(error.response?.data?.detail || 'Failed to delete material')
    }
  }

  const handleCopyURL = async (materialId: string) => {
    const baseUrl = window.location.origin
    const fullUrl = `${baseUrl}/api/v1/conference-materials/${materialId}/download`

    try {
      // Generate short URL for cleaner sharing
      let urlToCopy = fullUrl
      try {
        const response = await axios.post('/api/v1/short-urls/create', {
          target_url: fullUrl
        })
        urlToCopy = response.data.short_url
      } catch (shortUrlError) {
        console.warn('Failed to generate short URL, using full URL:', shortUrlError)
        // Fallback to full URL if shortening fails
      }

      await navigator.clipboard.writeText(urlToCopy)
      setCopiedId(materialId)
      setTimeout(() => setCopiedId(null), 2000) // Reset after 2 seconds
    } catch (error) {
      console.error('Failed to copy URL:', error)
      alert('Failed to copy URL to clipboard')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / 1024 / 1024).toFixed(1) + ' MB'
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="w-10 h-10 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-sm text-gray-500">Loading materials...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Conference Materials</h2>
          <p className="text-sm text-gray-600 mt-1">
            Manage brochures, schedules, maps, and other conference documents
          </p>
        </div>
        <button
          onClick={() => setShowUploadForm(!showUploadForm)}
          className="btn-primary flex items-center gap-2"
        >
          {showUploadForm ? (
            <>
              <X className="w-4 h-4" />
              Cancel
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              Upload Material
            </>
          )}
        </button>
      </div>

      {/* Upload Form */}
      {showUploadForm && (
        <form onSubmit={handleUpload} className="bg-gray-50 rounded-lg p-6 space-y-4">
          <h3 className="font-semibold text-gray-900">Upload New Material</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              File *
            </label>
            <input
              type="file"
              required
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.txt"
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
            />
            <p className="text-xs text-gray-500 mt-1">
              Max 50MB. Allowed: PDF, DOC, XLS, images, TXT
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title *
              </label>
              <input
                type="text"
                required
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                className="input-field"
                placeholder="e.g., Conference Schedule 2025"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Type
              </label>
              <select
                value={uploadType}
                onChange={(e) => setUploadType(e.target.value)}
                className="input-field"
              >
                <option value="brochure">Brochure</option>
                <option value="schedule">Schedule</option>
                <option value="map">Map</option>
                <option value="form">Form</option>
                <option value="flyer">Flyer</option>
                <option value="guide">Guide</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={uploadDescription}
              onChange={(e) => setUploadDescription(e.target.value)}
              className="input-field"
              rows={3}
              placeholder="Optional description..."
            />
          </div>

          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={uploadPublic}
                onChange={(e) => setUploadPublic(e.target.checked)}
                className="rounded text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm text-gray-700">Public (no login required)</span>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={uploadLanding}
                onChange={(e) => setUploadLanding(e.target.checked)}
                className="rounded text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm text-gray-700">Display on landing page</span>
            </label>

            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-700">Display order:</label>
              <input
                type="number"
                value={uploadOrder}
                onChange={(e) => setUploadOrder(parseInt(e.target.value) || 0)}
                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                min="0"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={!uploadFile || uploading}
              className="btn-primary disabled:opacity-50"
            >
              {uploading ? 'Uploading...' : 'Upload Material'}
            </button>
            <button
              type="button"
              onClick={() => setShowUploadForm(false)}
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Materials List */}
      <div className="space-y-3">
        {materials.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-600 font-medium">No materials uploaded yet</p>
            <p className="text-sm text-gray-500 mt-1">
              Click "Upload Material" to add conference documents
            </p>
          </div>
        ) : (
          materials.map((material) => (
            <div
              key={material.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              {editingId === material.id ? (
                // Edit Mode
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      className="input-field text-sm"
                      placeholder="Title"
                    />
                    <select
                      value={editType}
                      onChange={(e) => setEditType(e.target.value)}
                      className="input-field text-sm"
                    >
                      <option value="brochure">Brochure</option>
                      <option value="schedule">Schedule</option>
                      <option value="map">Map</option>
                      <option value="form">Form</option>
                      <option value="flyer">Flyer</option>
                      <option value="guide">Guide</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <textarea
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    className="input-field text-sm"
                    rows={2}
                    placeholder="Description"
                  />

                  <div className="flex flex-wrap gap-3 items-center">
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={editPublic}
                        onChange={(e) => setEditPublic(e.target.checked)}
                        className="rounded text-purple-600"
                      />
                      Public
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={editLanding}
                        onChange={(e) => setEditLanding(e.target.checked)}
                        className="rounded text-purple-600"
                      />
                      Landing page
                    </label>
                    <div className="flex items-center gap-1 text-sm">
                      <span>Order:</span>
                      <input
                        type="number"
                        value={editOrder}
                        onChange={(e) => setEditOrder(parseInt(e.target.value) || 0)}
                        className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
                        min="0"
                      />
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSaveEdit(material.id)}
                      className="btn-primary text-sm py-1.5 px-3"
                    >
                      <Save className="w-3 h-3 inline mr-1" />
                      Save
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="btn-secondary text-sm py-1.5 px-3"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                // View Mode
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-purple-50 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FileText className="w-6 h-6 text-purple-600" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                          {material.title}
                          {material.is_public ? (
                            <Eye className="w-3.5 h-3.5 text-green-600" title="Public" />
                          ) : (
                            <EyeOff className="w-3.5 h-3.5 text-gray-400" title="Private" />
                          )}
                          {material.display_on_landing && (
                            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                              Landing
                            </span>
                          )}
                        </h3>
                        {material.description && (
                          <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                            {material.description}
                          </p>
                        )}
                        <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-gray-500">
                          <span className="capitalize">{material.material_type}</span>
                          <span>•</span>
                          <span>{material.file_name}</span>
                          <span>•</span>
                          <span>{formatFileSize(material.file_size)}</span>
                          <span>•</span>
                          <span>Order: {material.display_order}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <a
                          href={material.download_url}
                          download
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Download"
                        >
                          <Download className="w-4 h-4" />
                        </a>
                        <button
                          onClick={() => handleCopyURL(material.id)}
                          className={`p-2 rounded-lg transition-colors ${
                            copiedId === material.id
                              ? 'text-green-600 bg-green-50'
                              : 'text-gray-600 hover:bg-gray-100'
                          }`}
                          title={copiedId === material.id ? 'Copied!' : 'Copy URL'}
                        >
                          {copiedId === material.id ? (
                            <Check className="w-4 h-4" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleEdit(material)}
                          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                          title="Edit"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(material.id, material.title)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
