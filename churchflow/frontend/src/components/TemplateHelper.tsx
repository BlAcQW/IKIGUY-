/**
 * TemplateHelper Component
 *
 * Shows available template variables with descriptions and click-to-insert functionality.
 * Helps users understand and use personalization variables in greeting templates.
 */

import { User, Building2, Briefcase, Calendar, MapPin, Users } from 'lucide-react'

interface TemplateHelperProps {
  greetingType: 'simple' | 'personalized'
  onInsertVariable: (variable: string) => void
}

interface TemplateVariable {
  variable: string
  description: string
  example: string
  icon: React.ReactNode
  available: boolean
}

export default function TemplateHelper({ greetingType, onInsertVariable }: TemplateHelperProps) {
  const variables: TemplateVariable[] = [
    {
      variable: '{user_name}',
      description: "Attendee's full name",
      example: 'John Mensah',
      icon: <User className="w-4 h-4" />,
      available: greetingType === 'personalized'
    },
    {
      variable: '{first_name}',
      description: "Attendee's first name only",
      example: 'John',
      icon: <User className="w-4 h-4" />,
      available: greetingType === 'personalized'
    },
    {
      variable: '{branch}',
      description: "Attendee's branch name",
      example: 'Legon Branch',
      icon: <Building2 className="w-4 h-4" />,
      available: greetingType === 'personalized'
    },
    {
      variable: '{volunteer_role}',
      description: "Attendee's volunteer role",
      example: 'Usher',
      icon: <Briefcase className="w-4 h-4" />,
      available: greetingType === 'personalized'
    },
    {
      variable: '{event_name}',
      description: 'Conference/event name',
      example: 'IMPACT 2025',
      icon: <Calendar className="w-4 h-4" />,
      available: true
    },
    {
      variable: '{venue}',
      description: 'Conference venue location',
      example: 'National Theatre',
      icon: <MapPin className="w-4 h-4" />,
      available: true
    }
  ]

  const availableVariables = variables.filter(v => v.available)

  return (
    <div className="mt-3 p-4 bg-purple-50 border border-purple-200 rounded-lg">
      <div className="flex items-center gap-2 mb-3">
        <Users className="w-4 h-4 text-purple-600" />
        <h4 className="font-medium text-gray-900 text-sm">Available Template Variables</h4>
      </div>

      {greetingType === 'simple' && (
        <p className="text-sm text-gray-600 mb-3">
          Simple greetings use fixed text. Switch to <strong>Personalized</strong> mode to use user-specific variables.
        </p>
      )}

      <div className="space-y-2">
        {availableVariables.map(({ variable, description, example, icon }) => (
          <button
            key={variable}
            type="button"
            onClick={() => onInsertVariable(variable)}
            className="w-full flex items-start gap-3 p-3 bg-white border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-all text-left group"
          >
            <div className="mt-0.5 text-purple-600 group-hover:text-purple-700">
              {icon}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <code className="text-sm font-mono text-purple-600 group-hover:text-purple-700">
                  {variable}
                </code>
                <span className="text-xs text-gray-500">← Click to insert</span>
              </div>
              <p className="text-xs text-gray-600 mt-1">{description}</p>
              <p className="text-xs text-gray-400 mt-1">
                Example: <span className="italic">{example}</span>
              </p>
            </div>
          </button>
        ))}
      </div>

      {greetingType === 'personalized' && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs text-blue-800">
            <strong>Tip:</strong> Variables are automatically replaced with actual data during check-in.
            Mix them with regular text for natural-sounding greetings.
          </p>
        </div>
      )}

      {/* Example Templates */}
      <div className="mt-4 pt-4 border-t border-purple-200">
        <h5 className="text-xs font-medium text-gray-700 mb-2">Example Templates:</h5>
        <div className="space-y-2">
          {greetingType === 'personalized' ? (
            <>
              <div className="text-xs p-2 bg-white rounded border border-gray-200">
                <code className="text-purple-600">
                  "Hello {'{user_name}'}, welcome to {'{event_name}'}!"
                </code>
              </div>
              <div className="text-xs p-2 bg-white rounded border border-gray-200">
                <code className="text-purple-600">
                  "{'{first_name}'}, thank you for checking in from {'{branch}'}."
                </code>
              </div>
              <div className="text-xs p-2 bg-white rounded border border-gray-200">
                <code className="text-purple-600">
                  "Welcome {'{user_name}'}! Thank you for serving as {'{volunteer_role}'} at {'{event_name}'}."
                </code>
              </div>
            </>
          ) : (
            <>
              <div className="text-xs p-2 bg-white rounded border border-gray-200">
                <code className="text-purple-600">
                  "Welcome to {'{event_name}'}! Thank you for joining us."
                </code>
              </div>
              <div className="text-xs p-2 bg-white rounded border border-gray-200">
                <code className="text-purple-600">
                  "Thank you for checking in at {'{venue}'} today!"
                </code>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
