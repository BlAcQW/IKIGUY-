/**
 * Session Schedule Component
 *
 * Public-facing display of conference sessions organized by day.
 * Shows session name, description, location in a read-only format.
 */

import { useState, useEffect } from 'react'
import { Calendar, MapPin, Clock } from 'lucide-react'

interface Session {
  id: string
  conference_id: string
  name: string
  description: string | null
  location: string | null
  day_number: number
  day_label: string
  session_date: string
  order: number
}

interface ConferenceDay {
  day_number: number
  day_label: string
  date: string
  date_display: string
}

interface SessionScheduleProps {
  conferenceId: string
}

export default function SessionSchedule({ conferenceId }: SessionScheduleProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [days, setDays] = useState<ConferenceDay[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDaysAndSessions()
  }, [conferenceId])

  const fetchDaysAndSessions = async () => {
    try {
      // Fetch days and sessions in parallel
      const [daysResponse, sessionsResponse] = await Promise.all([
        fetch(`/api/v1/conferences/${conferenceId}/days`),
        fetch(`/api/v1/conferences/${conferenceId}/sessions`)
      ])

      if (daysResponse.ok) {
        const daysData = await daysResponse.json()
        setDays(daysData.days)
      }

      if (sessionsResponse.ok) {
        const sessionsData = await sessionsResponse.json()
        setSessions(sessionsData.sessions)
      }
    } catch (err) {
      console.error('Failed to fetch sessions:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (isoDate: string): string => {
    const date = new Date(isoDate)
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  const sessionsByDay = sessions.reduce((acc, session) => {
    if (!acc[session.day_number]) acc[session.day_number] = []
    acc[session.day_number].push(session)
    return acc
  }, {} as Record<number, Session[]>)

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading schedule...</p>
      </div>
    )
  }

  // Don't show section if no sessions
  if (sessions.length === 0) {
    return null
  }

  return (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-3xl shadow-2xl p-8 md:p-12 mb-12 border-2 border-indigo-200">
      <div className="text-center mb-10">
        <div className="inline-block bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-2 rounded-full text-sm font-bold mb-4">
          📅 CONFERENCE SCHEDULE
        </div>
        <h2 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-2">
          Session Timeline
        </h2>
        <p className="text-gray-600 text-lg">Plan your conference experience</p>
      </div>

      <div className="space-y-8">
        {days.map(day => {
          const daySessions = sessionsByDay[day.day_number] || []

          if (daySessions.length === 0) return null

          return (
            <div key={day.day_number} className="bg-white rounded-2xl shadow-xl overflow-hidden border-2 border-indigo-100">
              {/* Day Header */}
              <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6">
                <div className="flex items-center gap-3 text-white">
                  <Calendar className="w-8 h-8" />
                  <div>
                    <h3 className="text-2xl font-bold">{day.day_label}</h3>
                    <p className="text-indigo-100">{day.date_display}</p>
                  </div>
                </div>
              </div>

              {/* Sessions List */}
              <div className="p-6 space-y-4">
                {daySessions.map((session, index) => (
                  <div
                    key={session.id}
                    className="group relative bg-gradient-to-br from-gray-50 to-indigo-50 rounded-xl p-6 border-2 border-indigo-100 hover:border-indigo-300 hover:shadow-lg transition-all duration-300"
                  >
                    {/* Session Number Badge */}
                    <div className="absolute -top-3 -left-3 w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 text-white rounded-full flex items-center justify-center font-bold shadow-lg">
                      {index + 1}
                    </div>

                    <div className="pl-6">
                      {/* Session Time */}
                      <div className="flex items-center gap-2 text-indigo-600 text-sm font-medium mb-2">
                        <Clock className="w-4 h-4" />
                        {formatTime(session.session_date)}
                      </div>

                      {/* Session Name */}
                      <h4 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-indigo-600 transition-colors">
                        {session.name}
                      </h4>

                      {/* Session Description */}
                      {session.description && (
                        <p className="text-gray-700 leading-relaxed mb-3">
                          {session.description}
                        </p>
                      )}

                      {/* Session Location */}
                      {session.location && (
                        <div className="flex items-center gap-2 text-gray-600 text-sm">
                          <MapPin className="w-4 h-4 text-indigo-500" />
                          <span className="font-medium">{session.location}</span>
                        </div>
                      )}
                    </div>

                    {/* Decorative gradient line */}
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 to-purple-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300"></div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
