/**
 * Toast Component
 *
 * Simple toast notification for success/error messages.
 */

import { useEffect } from 'react'
import { CheckCircle, XCircle, X } from 'lucide-react'

export interface ToastProps {
  message: string
  type: 'success' | 'error'
  isOpen: boolean
  onClose: () => void
  duration?: number
}

export default function Toast({
  message,
  type,
  isOpen,
  onClose,
  duration = 5000
}: ToastProps) {
  useEffect(() => {
    if (isOpen && duration > 0) {
      const timer = setTimeout(() => {
        onClose()
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [isOpen, duration, onClose])

  if (!isOpen) return null

  const bgColor = type === 'success' ? 'bg-green-50' : 'bg-red-50'
  const borderColor = type === 'success' ? 'border-green-200' : 'border-red-200'
  const textColor = type === 'success' ? 'text-green-800' : 'text-red-800'
  const iconColor = type === 'success' ? 'text-green-600' : 'text-red-600'

  return (
    <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-top-5">
      <div
        className={`${bgColor} ${borderColor} ${textColor} px-4 py-3 rounded-lg border shadow-lg max-w-md flex items-center gap-3`}
      >
        {type === 'success' ? (
          <CheckCircle className={`w-5 h-5 ${iconColor} flex-shrink-0`} />
        ) : (
          <XCircle className={`w-5 h-5 ${iconColor} flex-shrink-0`} />
        )}
        <p className="text-sm font-medium flex-1">{message}</p>
        <button
          onClick={onClose}
          className={`${textColor} hover:opacity-70 focus:outline-none flex-shrink-0`}
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
