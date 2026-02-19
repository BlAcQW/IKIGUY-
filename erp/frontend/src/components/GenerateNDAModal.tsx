/**
 * GenerateNDAModal Component
 *
 * Modal for HR to generate and send NDAs to new employees.
 * - Shows employee details
 * - Generates NDA from template with organization letterhead
 * - Provides signing link to send to employee
 * - Option to copy link or send via email
 */

import { useState } from 'react'
import { X, FileText, Copy, Check, Loader, AlertCircle } from 'lucide-react'
import api from '../services/api'

interface Employee {
  employee_id: string
  first_name: string
  last_name: string
  email: string
  position: string
  start_date: string
}

interface GenerateNDAModalProps {
  isOpen: boolean
  onClose: () => void
  employee: Employee | null
  onSuccess?: () => void
}

interface GeneratedNDA {
  document_id: string
  signing_token: string
  signing_link: string
  full_signing_url: string
  expires_at: string
  message: string
}

export default function GenerateNDAModal({
  isOpen,
  onClose,
  employee,
  onSuccess
}: GenerateNDAModalProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedNDA, setGeneratedNDA] = useState<GeneratedNDA | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [emailTemplate, setEmailTemplate] = useState(true)

  if (!isOpen || !employee) return null

  const handleGenerateNDA = async () => {
    setIsGenerating(true)
    setError(null)

    try {
      const response = await api.post('/legal/generate-nda', null, {
        params: {
          employee_name: `${employee.first_name} ${employee.last_name}`,
          employee_email: employee.email,
          employee_id: employee.employee_id,
          position: employee.position,
          start_date: employee.start_date
        }
      })

      setGeneratedNDA(response.data)
    } catch (err: any) {
      console.error('Failed to generate NDA:', err)
      setError(err.response?.data?.detail || 'Failed to generate NDA. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCopyLink = () => {
    if (generatedNDA) {
      navigator.clipboard.writeText(generatedNDA.full_signing_url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleClose = () => {
    setGeneratedNDA(null)
    setError(null)
    setCopied(false)
    onClose()
    if (onSuccess) onSuccess()
  }

  const getEmailTemplate = () => {
    if (!generatedNDA) return ''

    return `Subject: AI Labs Africa - NDA Signature Required

Hi ${employee.first_name},

Welcome to AI Labs Africa!

Before your start date on ${new Date(employee.start_date).toLocaleDateString()}, please review and electronically sign your Non-Disclosure Agreement (NDA).

Click here to review and sign:
${generatedNDA.full_signing_url}

This link will expire on ${new Date(generatedNDA.expires_at).toLocaleDateString()}.

If you have any questions, please contact HR at hr@ailabsafrica.com

Best regards,
AI Labs Africa HR Team`
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center">
            <FileText className="w-6 h-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">Generate NDA</h2>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Employee Info */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Employee Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Name:</span>
                <p className="font-medium">{employee.first_name} {employee.last_name}</p>
              </div>
              <div>
                <span className="text-gray-600">Email:</span>
                <p className="font-medium">{employee.email}</p>
              </div>
              <div>
                <span className="text-gray-600">Position:</span>
                <p className="font-medium">{employee.position}</p>
              </div>
              <div>
                <span className="text-gray-600">Start Date:</span>
                <p className="font-medium">{new Date(employee.start_date).toLocaleDateString()}</p>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-2 flex-shrink-0" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Generated NDA Success */}
          {generatedNDA && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start">
                  <Check className="w-5 h-5 text-green-600 mt-0.5 mr-2 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-green-800 mb-1">
                      NDA Generated Successfully!
                    </p>
                    <p className="text-xs text-green-700">
                      Document ID: {generatedNDA.document_id}
                    </p>
                    <p className="text-xs text-green-700">
                      Expires: {new Date(generatedNDA.expires_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Signing Link */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Signing Link
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={generatedNDA.full_signing_url}
                    readOnly
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm"
                  />
                  <button
                    onClick={handleCopyLink}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check className="w-4 h-4 mr-1" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4 mr-1" />
                        Copy Link
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Send this link to the employee to review and sign the NDA
                </p>
              </div>

              {/* Email Template */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Email Template
                  </label>
                  <button
                    onClick={() => setEmailTemplate(!emailTemplate)}
                    className="text-xs text-blue-600 hover:text-blue-700"
                  >
                    {emailTemplate ? 'Hide' : 'Show'} Template
                  </button>
                </div>
                {emailTemplate && (
                  <div>
                    <textarea
                      value={getEmailTemplate()}
                      readOnly
                      rows={15}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm font-mono"
                    />
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(getEmailTemplate())
                        setCopied(true)
                        setTimeout(() => setCopied(false), 2000)
                      }}
                      className="mt-2 text-sm text-blue-600 hover:text-blue-700 flex items-center"
                    >
                      <Copy className="w-3 h-3 mr-1" />
                      Copy Email Template
                    </button>
                  </div>
                )}
              </div>

              {/* Next Steps */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-blue-900 mb-2">Next Steps:</h4>
                <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                  <li>Copy the signing link or email template above</li>
                  <li>Send the link to {employee.email}</li>
                  <li>Employee will receive and sign the NDA</li>
                  <li>System will automatically update their onboarding record</li>
                  <li>You'll see the NDA marked as "Signed" in their profile</li>
                </ol>
              </div>
            </div>
          )}

          {/* Generate Button (shown if not yet generated) */}
          {!generatedNDA && (
            <div>
              <button
                onClick={handleGenerateNDA}
                disabled={isGenerating}
                className="w-full flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGenerating ? (
                  <>
                    <Loader className="w-5 h-5 mr-2 animate-spin" />
                    Generating NDA...
                  </>
                ) : (
                  <>
                    <FileText className="w-5 h-5 mr-2" />
                    Generate NDA with Organization Letterhead
                  </>
                )}
              </button>
              <p className="text-xs text-gray-500 mt-2 text-center">
                This will create a personalized NDA with company logo and address
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end px-6 py-4 border-t border-gray-200 space-x-3">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            {generatedNDA ? 'Done' : 'Cancel'}
          </button>
        </div>
      </div>
    </div>
  )
}
