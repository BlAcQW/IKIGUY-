/**
 * DetailModal Component
 *
 * Reusable modal for displaying detailed information about an entity.
 */

import { X, Edit2, Calendar } from 'lucide-react'

export interface DetailField {
  label: string
  value: any
  render?: () => React.ReactNode
  fullWidth?: boolean
  type?: 'default' | 'status' | 'date' | 'currency'
}

export interface DetailModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  subtitle?: string
  fields: DetailField[]
  onEdit?: () => void
  accentColor?: string
}

export default function DetailModal({
  isOpen,
  onClose,
  title,
  subtitle,
  fields,
  onEdit
}: DetailModalProps) {
  if (!isOpen) return null

  const formatValue = (value: any): string => {
    if (value === null || value === undefined || value === '') {
      return '-'
    }
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No'
    }
    if (typeof value === 'object') {
      if (Array.isArray(value)) {
        return value.length > 0 ? value.join(', ') : '-'
      }
      return JSON.stringify(value, null, 2)
    }
    return String(value)
  }

  const getStatusColor = (status: string) => {
    const s = status?.toLowerCase()
    if (['completed', 'paid', 'active', 'approved', 'done'].includes(s)) return 'bg-green-100 text-green-800 border-green-200'
    if (['pending', 'planning', 'in_progress', 'in_review'].includes(s)) return 'bg-amber-100 text-amber-800 border-amber-200'
    if (['cancelled', 'rejected', 'failed'].includes(s)) return 'bg-red-100 text-red-800 border-red-200'
    if (['on_hold', 'draft'].includes(s)) return 'bg-gray-100 text-gray-800 border-gray-200'
    return 'bg-blue-100 text-blue-800 border-blue-200'
  }

  const renderFieldValue = (field: DetailField) => {
    if (field.render) return field.render()

    const value = formatValue(field.value)

    if (field.type === 'status' && value !== '-') {
      return (
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(value)}`}>
          {value.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
        </span>
      )
    }

    if (field.type === 'date' && value !== '-') {
      return (
        <span className="inline-flex items-center gap-2 text-gray-700">
          <Calendar className="w-4 h-4 text-gray-400" />
          {value}
        </span>
      )
    }

    if (field.type === 'currency' && value !== '-') {
      return <span className="font-semibold text-gray-900">{value}</span>
    }

    return value
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-5">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h2 className="text-xl font-bold text-white">{title}</h2>
              {subtitle && (
                <p className="text-white/80 text-sm mt-1">{subtitle}</p>
              )}
            </div>
            <div className="flex items-center gap-2">
              {onEdit && (
                <button
                  onClick={() => {
                    onEdit()
                    onClose()
                  }}
                  className="p-2 text-white/80 hover:text-white hover:bg-white/20 rounded-lg transition-all"
                  title="Edit"
                >
                  <Edit2 className="w-5 h-5" />
                </button>
              )}
              <button
                onClick={onClose}
                className="p-2 text-white/80 hover:text-white hover:bg-white/20 rounded-lg transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {fields.map((field, index) => (
              <div
                key={index}
                className={`${field.fullWidth ? 'md:col-span-2' : ''} group`}
              >
                <div className="bg-gray-50 rounded-xl p-4 border border-gray-100 hover:border-gray-200 hover:shadow-sm transition-all">
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    {field.label}
                  </label>
                  <div className="text-gray-900 min-h-[1.5rem]">
                    {renderFieldValue(field)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-5 py-2.5 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
