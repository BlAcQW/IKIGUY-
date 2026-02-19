/**
 * ActivityTimeline Component
 *
 * Displays a visual timeline of all activities for a CRM entity
 */

import { useState, useEffect } from 'react'
import { Phone, Mail, Calendar, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import api from '@/lib/api'

interface ActivityTimelineProps {
  entityType: 'lead' | 'customer' | 'opportunity' | 'contact'
  entityId: string
}

export default function ActivityTimeline({ entityType, entityId }: ActivityTimelineProps) {
  const [activities, setActivities] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchActivities()
  }, [entityType, entityId])

  const fetchActivities = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/crm/activities/timeline/${entityType}/${entityId}`)
      setActivities(response.data)
    } catch (error) {
      console.error('Failed to fetch activities:', error)
    } finally {
      setLoading(false)
    }
  }

  const getActivityIcon = (activityType: string) => {
    switch (activityType) {
      case 'call':
        return <Phone className="h-5 w-5 text-blue-600" />
      case 'email':
        return <Mail className="h-5 w-5 text-green-600" />
      case 'meeting':
        return <Calendar className="h-5 w-5 text-purple-600" />
      case 'note':
        return <FileText className="h-5 w-5 text-gray-600" />
      case 'task':
        return <CheckCircle className="h-5 w-5 text-indigo-600" />
      default:
        return <AlertCircle className="h-5 w-5 text-orange-600" />
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (activities.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <FileText className="h-12 w-12 mx-auto mb-2 text-gray-400" />
        <p>No activities yet</p>
        <p className="text-sm">Start logging activities to see the timeline</p>
      </div>
    )
  }

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {activities.map((activity, activityIdx) => (
          <li key={activity.id}>
            <div className="relative pb-8">
              {activityIdx !== activities.length - 1 ? (
                <span
                  className="absolute top-5 left-5 -ml-px h-full w-0.5 bg-gray-200"
                  aria-hidden="true"
                />
              ) : null}
              <div className="relative flex items-start space-x-3">
                <div>
                  <div className="relative px-1">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-100 ring-8 ring-white">
                      {getActivityIcon(activity.activity_type)}
                    </div>
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <div>
                    <div className="text-sm">
                      <span className="font-medium text-gray-900">{activity.subject}</span>
                    </div>
                    <p className="mt-0.5 text-sm text-gray-500">
                      {formatDate(activity.activity_date)}
                      {activity.duration_minutes && (
                        <span className="ml-2">• {activity.duration_minutes} min</span>
                      )}
                    </p>
                  </div>
                  <div className="mt-2 text-sm text-gray-700">
                    {activity.description && <p>{activity.description}</p>}

                    {/* Call specifics */}
                    {activity.activity_type === 'call' && activity.call_outcome && (
                      <p className="mt-1 text-xs text-gray-500">
                        Outcome: <span className="capitalize">{activity.call_outcome}</span>
                      </p>
                    )}

                    {/* Email specifics */}
                    {activity.activity_type === 'email' && activity.email_subject && (
                      <p className="mt-1 text-xs text-gray-500">
                        {activity.email_sent ? '📤 Sent' : '📥 Received'}: {activity.email_subject}
                      </p>
                    )}

                    {/* Meeting specifics */}
                    {activity.activity_type === 'meeting' && activity.meeting_location && (
                      <p className="mt-1 text-xs text-gray-500">
                        📍 {activity.meeting_location}
                      </p>
                    )}

                    {/* Follow-up indicator */}
                    {activity.requires_follow_up && !activity.follow_up_completed && (
                      <div className="mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        <AlertCircle className="h-3 w-3 mr-1" />
                        Follow-up needed
                        {activity.follow_up_date && (
                          <span className="ml-1">
                            by {new Date(activity.follow_up_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    )}

                    {activity.follow_up_completed && (
                      <div className="mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Follow-up completed
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
