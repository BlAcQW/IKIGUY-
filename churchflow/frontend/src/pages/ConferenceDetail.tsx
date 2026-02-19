import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Calendar,
  MapPin,
  Users,
  Edit3,
  Mic,
  BarChart3,
  MessageSquare,
  UserCheck,
  FileText
} from 'lucide-react'
import ConferenceManagement from './ConferenceManagement'
import RegisteredMembers from './RegisteredMembers'
import ConferenceAnalytics from './ConferenceAnalytics'
import VoiceSettingsModal from '../components/VoiceSettingsModal'
import SessionManager from '../components/SessionManager'
import QRScanner from './QRScanner'
import ConferenceSMSCampaigns from './ConferenceSMSCampaigns'
import ConferenceMaterials from '../components/ConferenceMaterials'

interface ConferenceSummary {
  id: string
  name: string
  description?: string | null
  venue: string
  start_date: string
  end_date: string
  current_attendees: number
  max_attendees?: number | null
  status: string
}

type TabId =
  | 'overview'
  | 'registrations'
  | 'sessions'
  | 'checkin'
  | 'materials'
  | 'edit'
  | 'voice'
  | 'analytics'
  | 'sms'

export default function ConferenceDetail() {
  const { conferenceId } = useParams<{ conferenceId: string }>()
  const [conference, setConference] = useState<ConferenceSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const [showVoiceModal, setShowVoiceModal] = useState(false)
  const [showEditInline, setShowEditInline] = useState(false)

  useEffect(() => {
    if (conferenceId) {
      fetchConference(conferenceId)
    }
  }, [conferenceId])

  const fetchConference = async (id: string) => {
    setLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      const headers: any = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`/api/v1/conferences/${id}`, { headers })
      if (response.ok) {
        const data = await response.json()
        setConference({
          id: data.id,
          name: data.name,
          description: data.description,
          venue: data.venue,
          start_date: data.start_date,
          end_date: data.end_date,
          current_attendees: data.current_attendees ?? 0,
          max_attendees: data.max_attendees,
          status: data.status
        })
      }
    } catch (err) {
      console.error('Failed to load conference:', err)
    } finally {
      setLoading(false)
    }
  }

  if (!conferenceId) {
    return (
      <div className="p-6">
        <p className="text-gray-600">No conference selected.</p>
      </div>
    )
  }

  if (loading || !conference) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm text-gray-500">Loading conference...</p>
        </div>
      </div>
    )
  }

  const tabs: { id: TabId; label: string; icon: any }[] = [
    { id: 'overview', label: 'Overview', icon: Calendar },
    { id: 'registrations', label: 'Registrations', icon: Users },
    { id: 'sessions', label: 'Sessions', icon: Calendar },
    { id: 'checkin', label: 'Admin Check-in', icon: UserCheck },
    { id: 'materials', label: 'Materials', icon: FileText },
    { id: 'edit', label: 'Edit Details', icon: Edit3 },
    { id: 'voice', label: 'Voice Greeting', icon: Mic },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'sms', label: 'SMS Campaigns', icon: MessageSquare }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => (window.location.href = '/conferences')}
            className="text-xs text-gray-500 hover:text-gray-700 mb-2"
          >
            ← Back to Conferences
          </button>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 flex items-center gap-2">
            {conference.name}
          </h1>
          <p className="text-gray-600 mt-1 flex items-center gap-3 text-sm">
            <span className="inline-flex items-center gap-1">
              <Calendar className="w-4 h-4 text-gray-400" />
              {new Date(conference.start_date).toLocaleDateString()} -{' '}
              {new Date(conference.end_date).toLocaleDateString()}
            </span>
            <span className="inline-flex items-center gap-1">
              <MapPin className="w-4 h-4 text-gray-400" />
              {conference.venue}
            </span>
            <span className="inline-flex items-center gap-1">
              <Users className="w-4 h-4 text-gray-400" />
              {conference.current_attendees}{' '}
              {conference.max_attendees
                ? `/ ${conference.max_attendees} registered`
                : 'registered'}
            </span>
          </p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="border-b border-gray-200 px-4 pt-4">
            <div className="flex flex-wrap gap-2">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-purple-50 text-purple-700 border border-purple-200'
                        : 'text-gray-600 hover:bg-gray-50 border border-transparent'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="p-4 md:p-6">
            {activeTab === 'overview' && (
              <div className="space-y-4">
                {conference.description && (
                  <p className="text-gray-700 text-sm">{conference.description}</p>
                )}
                <p className="text-sm text-gray-500">
                  Use the tabs above to manage everything related to this conference in one
                  place: registrations, sessions, admin check-in, voice greetings, analytics,
                  and SMS campaigns.
                </p>
              </div>
            )}

            {activeTab === 'registrations' && (
              <RegisteredMembers
                initialCheckedInFilter="all"
                conferenceId={conference.id}
              />
            )}

            {activeTab === 'sessions' && (
              <SessionManager
                conference={{
                  id: conference.id,
                  name: conference.name,
                  description: conference.description,
                  venue: conference.venue,
                  start_date: conference.start_date,
                  end_date: conference.end_date,
                  venue_latitude: null,
                  venue_longitude: null,
                  venue_checkin_radius: 1000,
                  registration_open: true,
                  self_checkin_enabled: true,
                  allow_repeat_checkin: true,
                  location_checkin_required: true,
                  max_attendees: conference.max_attendees ?? 0,
                  current_attendees: conference.current_attendees,
                  status: conference.status
                }}
                onClose={() => undefined}
              />
            )}

            {activeTab === 'checkin' && <QRScanner />}

            {activeTab === 'edit' && (
              <div className="space-y-4">
                {!showEditInline && (
                  <button
                    onClick={() => setShowEditInline(true)}
                    className="btn-primary"
                  >
                    Edit Conference Details
                  </button>
                )}
                {showEditInline && (
                  <ConferenceManagement />
                )}
              </div>
            )}

            {activeTab === 'materials' && (
              <ConferenceMaterials conferenceId={conference.id} />
            )}

            {activeTab === 'voice' && (
              <>
                <button
                  onClick={() => setShowVoiceModal(true)}
                  className="btn-primary mb-4"
                >
                  Configure Voice Greeting
                </button>
                {showVoiceModal && (
                  <VoiceSettingsModal
                    conferenceId={conference.id}
                    conferenceName={conference.name}
                    onClose={() => setShowVoiceModal(false)}
                    onSave={() => setShowVoiceModal(false)}
                  />
                )}
              </>
            )}

            {activeTab === 'analytics' && (
              <ConferenceAnalytics conferenceId={conference.id} />
            )}

            {activeTab === 'sms' && (
              <ConferenceSMSCampaigns conferenceId={conference.id} conferenceName={conference.name} />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}


