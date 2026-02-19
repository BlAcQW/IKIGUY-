import { useEffect, useState } from 'react'
import { MessageSquare, Users, Send, Play, Pause, Trash2, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react'
import { API_BASE_URL } from '../config'

interface ConferenceSMSCampaignsProps {
  conferenceId: string
  conferenceName: string
}

interface SMSCampaign {
  id: string
  name: string
  template_content: string
  status: 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  progress: {
    total_recipients: number
    sent: number
    delivered: number
    failed: number
    pending: number
  }
  total_cost: number
  sms_provider: string
  created_at: string
  started_at: string | null
  completed_at: string | null
}

interface Session {
  id: string
  name: string
  day_label: string
}

export default function ConferenceSMSCampaigns({
  conferenceId,
  conferenceName
}: ConferenceSMSCampaignsProps) {
  const token = localStorage.getItem('access_token')
  const [campaigns, setCampaigns] = useState<SMSCampaign[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    template_content: '',
    audience_type: 'conference',
    session_ids: [] as string[]
  })

  useEffect(() => {
    if (token && conferenceId) {
      fetchCampaigns()
      fetchSessions()
    }
  }, [token, conferenceId])

  const fetchCampaigns = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/sms-campaigns?conference_id=${conferenceId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setCampaigns(data.campaigns || [])
      }
    } catch (err) {
      console.error('Error fetching conference SMS campaigns:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchSessions = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/conferences/${conferenceId}/sessions`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (response.ok) {
        const data = await response.json()
        setSessions((data.sessions || data || []) as Session[])
      }
    } catch (err) {
      console.error('Error fetching sessions for SMS:', err)
    }
  }

  const handleCreate = async () => {
    if (!formData.name || !formData.template_content) {
      alert('Please provide a campaign name and message template.')
      return
    }

    try {
      const payload = {
        name: formData.name,
        template_content: formData.template_content,
        audience_type: formData.audience_type,
        conference_id: conferenceId,
        branch_id: null,
        session_ids: formData.audience_type === 'session' && formData.session_ids.length > 0
          ? formData.session_ids
          : null,
        config: {
          send_rate_per_second: 1.0
        },
        sms_provider: 'arkesel'
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/sms-campaigns/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        setShowCreate(false)
        setFormData({
          name: '',
          template_content: '',
          audience_type: 'conference',
          session_ids: []
        })
        fetchCampaigns()
      } else {
        const error = await response.json().catch(() => ({}))
        alert(error.detail || 'Failed to create SMS campaign')
      }
    } catch (err) {
      console.error('Error creating conference SMS campaign:', err)
      alert('Failed to create campaign')
    }
  }

  const handlePrepare = async (campaignId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/sms-campaigns/${campaignId}/prepare`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` } }
      )
      const data = await response.json()
      if (response.ok) {
        alert(`Prepared ${data.message_count} messages`)
        fetchCampaigns()
      } else {
        alert(data.detail || 'Failed to prepare campaign')
      }
    } catch (err) {
      console.error('Error preparing conference SMS campaign:', err)
    }
  }

  const handleStart = async (campaignId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/sms-campaigns/${campaignId}/start`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` } }
      )
      if (response.ok) {
        fetchCampaigns()
      } else {
        const error = await response.json().catch(() => ({}))
        alert(error.detail || 'Failed to start campaign')
      }
    } catch (err) {
      console.error('Error starting conference SMS campaign:', err)
    }
  }

  const handlePause = async (campaignId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/sms-campaigns/${campaignId}/pause`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` } }
      )
      if (response.ok) {
        fetchCampaigns()
      }
    } catch (err) {
      console.error('Error pausing conference SMS campaign:', err)
    }
  }

  const handleDelete = async (campaignId: string) => {
    if (!window.confirm('Delete this SMS campaign?')) return
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/sms-campaigns/${campaignId}`,
        { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } }
      )
      if (response.ok) {
        fetchCampaigns()
      }
    } catch (err) {
      console.error('Error deleting conference SMS campaign:', err)
    }
  }

  const handleRetryFailed = async (campaignId: string) => {
    if (!window.confirm('Retry all failed messages? This will reset them to pending status.')) return
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/sms-campaigns/${campaignId}/retry-failed`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` } }
      )
      const data = await response.json()
      if (response.ok) {
        alert(`Retried ${data.retried_count} failed messages`)
        fetchCampaigns()
      } else {
        alert(data.detail || 'Failed to retry messages')
      }
    } catch (err) {
      console.error('Error retrying failed messages:', err)
      alert('Failed to retry messages')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-6">
        <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-purple-600" />
            SMS Campaigns for {conferenceName}
          </h2>
          <p className="text-sm text-gray-500">
            Targeted SMS to attendees of this specific conference.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2 text-sm"
        >
          <Send className="w-4 h-4" />
          New Campaign
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500 uppercase">
              Campaigns
            </span>
            <MessageSquare className="w-4 h-4 text-gray-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-gray-900">
            {campaigns.length}
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500 uppercase">
              Messages Sent
            </span>
            <Send className="w-4 h-4 text-blue-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-gray-900">
            {campaigns.reduce((sum, c) => sum + c.progress.sent, 0).toLocaleString()}
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500 uppercase">
              Total Cost
            </span>
            <Users className="w-4 h-4 text-purple-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-gray-900">
            ${campaigns.reduce((sum, c) => sum + c.total_cost, 0).toFixed(2)}
          </div>
        </div>
      </div>

      {/* List */}
      {campaigns.length === 0 ? (
        <div className="bg-white rounded-lg border p-6 text-center text-gray-500">
          No SMS campaigns created for this conference yet.
        </div>
      ) : (
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Campaign
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Progress
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Provider
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {campaigns.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{c.name}</div>
                    <div className="text-xs text-gray-500 truncate max-w-xs">
                      {c.template_content}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        c.status === 'completed'
                          ? 'bg-emerald-50 text-emerald-700'
                          : c.status === 'running'
                          ? 'bg-green-50 text-green-700'
                          : c.status === 'paused'
                          ? 'bg-yellow-50 text-yellow-700'
                          : c.status === 'failed'
                          ? 'bg-red-50 text-red-700'
                          : 'bg-gray-50 text-gray-700'
                      }`}
                    >
                      {c.status === 'completed' && (
                        <CheckCircle className="w-3 h-3 mr-1" />
                      )}
                      {c.status === 'failed' && (
                        <AlertCircle className="w-3 h-3 mr-1" />
                      )}
                      {c.status.charAt(0).toUpperCase() + c.status.slice(1)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="w-32">
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-purple-600 rounded-full"
                          style={{
                            width: `${
                              c.progress.total_recipients > 0
                                ? ((c.progress.sent + c.progress.failed) /
                                    c.progress.total_recipients) *
                                  100
                                : 0
                            }%`
                          }}
                        />
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {c.progress.sent}/{c.progress.total_recipients} sent
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 capitalize">
                    {c.sms_provider.replace('_', ' ')}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="inline-flex items-center gap-1">
                      {c.status === 'draft' && c.progress.total_recipients === 0 && (
                        <button
                          onClick={() => handlePrepare(c.id)}
                          className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                          title="Prepare recipients"
                        >
                          <Users className="w-4 h-4" />
                        </button>
                      )}
                      {['draft', 'paused'].includes(c.status) &&
                        c.progress.total_recipients > 0 && (
                          <button
                            onClick={() => handleStart(c.id)}
                            className="p-1.5 text-green-600 hover:bg-green-50 rounded"
                            title="Start"
                          >
                            <Play className="w-4 h-4" />
                          </button>
                        )}
                      {c.status === 'running' && (
                        <button
                          onClick={() => handlePause(c.id)}
                          className="p-1.5 text-yellow-600 hover:bg-yellow-50 rounded"
                          title="Pause"
                        >
                          <Pause className="w-4 h-4" />
                        </button>
                      )}
                      {c.progress.failed > 0 && ['draft', 'paused', 'completed', 'failed'].includes(c.status) && (
                        <button
                          onClick={() => handleRetryFailed(c.id)}
                          className="p-1.5 text-orange-600 hover:bg-orange-50 rounded"
                          title={`Retry ${c.progress.failed} failed message(s)`}
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      )}
                      {['draft', 'paused'].includes(c.status) && (
                        <button
                          onClick={() => handleDelete(c.id)}
                          className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Campaign */}
      {showCreate && (
        <div className="bg-white rounded-lg border p-6 space-y-4">
          <h3 className="text-md font-semibold text-gray-900 mb-2">New SMS Campaign</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Campaign Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="e.g., Day 2 Reminder"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Audience
            </label>
            <select
              value={formData.audience_type}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  audience_type: e.target.value,
                  session_ids: []
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="conference">All Registrants (This Conference)</option>
              <option value="checked_in">Checked-In Attendees Only</option>
              <option value="session">Attendees of Selected Sessions</option>
            </select>
          </div>
          {formData.audience_type === 'session' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sessions
              </label>
              <div className="border border-gray-200 rounded-lg p-3 max-h-40 overflow-y-auto">
                {sessions.length === 0 ? (
                  <p className="text-xs text-gray-500">
                    No sessions found for this conference.
                  </p>
                ) : (
                  sessions.map((s) => (
                    <label
                      key={s.id}
                      className="flex items-center gap-2 text-sm text-gray-700 py-1 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={formData.session_ids.includes(s.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({
                              ...formData,
                              session_ids: [...formData.session_ids, s.id]
                            })
                          } else {
                            setFormData({
                              ...formData,
                              session_ids: formData.session_ids.filter((id) => id !== s.id)
                            })
                          }
                        }}
                        className="w-4 h-4 text-purple-600 rounded"
                      />
                      <span>
                        {s.day_label} – {s.name}
                      </span>
                    </label>
                  ))
                )}
              </div>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Message Template
            </label>
            <textarea
              value={formData.template_content}
              onChange={(e) =>
                setFormData({ ...formData, template_content: e.target.value })
              }
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Dear {{name}}, thank you for joining {{conference}}..."
            />
            <p className="text-xs text-gray-500 mt-1">
              You can use variables like <code className="font-mono">{"{{name}}"}</code> and{' '}
              <code className="font-mono">{"{{conference}}"}</code>.
            </p>
          </div>
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleCreate}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700"
            >
              Create Campaign
            </button>
          </div>
        </div>
      )}
    </div>
  )
}


