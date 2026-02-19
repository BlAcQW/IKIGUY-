import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bus, Calendar, Users, QrCode, Bell, UserCheck, BarChart3 } from 'lucide-react'

interface Conference {
  id: string
  name: string
  theme?: string
  start_date: string
  end_date: string
  current_attendees: number
  expected_attendance?: number
  banner_url?: string
}

interface BusRoute {
  id: string
  name: string
  departure_time: string
  registered_count: number
  capacity: number
  status: string
}

interface DashboardStats {
  total_registered: number
  checked_in_today: number
  total_conferences: number
  active_bus_routes: number
  registrations_today: number
  sessions_today: number
}

export default function DashboardOverview() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<DashboardStats>({
    total_registered: 0,
    checked_in_today: 0,
    total_conferences: 0,
    active_bus_routes: 0,
    registrations_today: 0,
    sessions_today: 0
  })
  const [upcomingConference, setUpcomingConference] = useState<Conference | null>(null)
  const [topBusRoutes, setTopBusRoutes] = useState<BusRoute[]>([])

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      // Fetch dashboard stats from the dedicated endpoint
      const statsResponse = await fetch('/api/v1/dashboard/stats')
      if (statsResponse.ok) {
        const statsData = await statsResponse.json()
        setStats(statsData)
      }

      // Fetch buses for top routes display
      const busesResponse = await fetch('/api/v1/buses/routes')
      if (busesResponse.ok) {
        const busesData = await busesResponse.json()
        // Get top 5 routes by capacity
        setTopBusRoutes(busesData.slice(0, 5))
      }

      // Fetch conferences for upcoming conference display
      const conferencesResponse = await fetch('/api/v1/conferences')
      if (conferencesResponse.ok) {
        const conferencesData = await conferencesResponse.json()
        if (conferencesData.length > 0) {
          setUpcomingConference(conferencesData[0])
        }
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-700 rounded-xl p-6 md:p-8 text-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl sm:text-2xl md:text-3xl font-bold mb-1">Dashboard Overview</h1>
            <p className="text-sm sm:text-base text-purple-100">Managing {stats.total_conferences} conference{stats.total_conferences !== 1 ? 's' : ''} • {stats.active_bus_routes} bus routes</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => navigate('/conferences')} className="px-4 py-2 min-h-[44px] bg-white text-purple-600 font-medium text-sm rounded-lg hover:bg-purple-50 transition-colors touch-manipulation">
              View Conferences
            </button>
            <button onClick={() => navigate('/buses')} className="px-4 py-2 min-h-[44px] bg-purple-800/50 text-white font-medium text-sm rounded-lg hover:bg-purple-800 transition-colors touch-manipulation">
              Manage Buses
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card card-hover cursor-pointer" onClick={() => navigate('/registered-users')}>
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Registered</p>
              <h3 className="text-2xl font-bold text-gray-900">{stats.total_registered}</h3>
            </div>
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Users className="w-5 h-5 text-purple-600" />
            </div>
          </div>
          <p className="text-xs text-gray-500">Total members</p>
        </div>

        <div className="card card-hover cursor-pointer" onClick={() => navigate('/registered-users')}>
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Checked In</p>
              <h3 className="text-2xl font-bold text-green-600">{stats.checked_in_today}</h3>
            </div>
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <UserCheck className="w-5 h-5 text-green-600" />
            </div>
          </div>
          <p className="text-xs text-gray-500">Today</p>
        </div>

        <div className="card card-hover cursor-pointer" onClick={() => navigate('/conferences')}>
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Conferences</p>
              <h3 className="text-2xl font-bold text-gray-900">{stats.total_conferences}</h3>
            </div>
            <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
              <Calendar className="w-5 h-5 text-indigo-600" />
            </div>
          </div>
          <p className="text-xs text-gray-500">Active events</p>
        </div>

        <div className="card card-hover cursor-pointer" onClick={() => navigate('/buses')}>
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Bus Routes</p>
              <h3 className="text-2xl font-bold text-gray-900">{stats.active_bus_routes}</h3>
            </div>
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
              <Bus className="w-5 h-5 text-orange-600" />
            </div>
          </div>
          <p className="text-xs text-gray-500">Available</p>
        </div>
      </div>

      {/* Upcoming Conference Highlight */}
      {upcomingConference && (
        <div className="card overflow-hidden">
          <div className="relative h-36 bg-gradient-to-r from-purple-600 to-purple-700 -m-6 mb-4">
            {upcomingConference.banner_url && (
              <img src={upcomingConference.banner_url} alt={upcomingConference.name} className="absolute inset-0 w-full h-full object-cover opacity-40" />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
            <div className="absolute bottom-4 left-6 right-6">
              <span className="badge-purple mb-2 inline-block">UPCOMING</span>
              <h2 className="text-xl font-bold text-white mb-0.5">{upcomingConference.name}</h2>
              {upcomingConference.theme && (
                <p className="text-white/70 text-sm italic">"{upcomingConference.theme}"</p>
              )}
            </div>
          </div>
          <div className="pt-2">
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Start Date</p>
                <p className="text-gray-900 font-semibold text-sm">{new Date(upcomingConference.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Expected</p>
                <p className="text-gray-900 font-semibold text-sm">{upcomingConference.expected_attendance?.toLocaleString() || 'TBA'}</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Registered</p>
                <p className="text-gray-900 font-semibold text-sm">{upcomingConference.current_attendees}</p>
              </div>
            </div>
            <button
              onClick={() => window.location.href = `/conference/${upcomingConference.id}`}
              className="btn-primary w-full"
            >
              View Conference Details
            </button>
          </div>
        </div>
      )}

      {/* Bus Routes Preview & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Top Bus Routes */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-gray-900">Top Bus Routes</h3>
              <p className="text-sm text-gray-500">Most popular routes</p>
            </div>
            <button onClick={() => navigate('/buses')} className="text-purple-600 hover:text-purple-700 font-medium text-sm min-h-[44px] px-3 touch-manipulation">View All</button>
          </div>
          <div className="space-y-2">
            {topBusRoutes.map((route, index) => (
              <div key={route.id} className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100">
                <div className="bg-purple-600 text-white w-7 h-7 rounded-lg flex items-center justify-center font-medium text-xs">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 text-sm truncate">{route.name}</p>
                  <p className="text-xs text-gray-400">{route.departure_time}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{route.registered_count}/{route.capacity}</p>
                  <p className="text-xs text-gray-400">{Math.round((route.registered_count / route.capacity) * 100)}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-gray-900">Recent Activity</h3>
              <p className="text-sm text-gray-500">Latest updates</p>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex gap-3 pb-3 border-b border-gray-100">
              <div className="bg-green-500 w-1 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">Conference Registration</p>
                <p className="text-xs text-gray-500">New registration for IMPACT 2025</p>
                <p className="text-xs text-gray-400 mt-0.5">Just now</p>
              </div>
            </div>
            <div className="flex gap-3 pb-3 border-b border-gray-100">
              <div className="bg-blue-500 w-1 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">Bus Route Updated</p>
                <p className="text-xs text-gray-500">Legon route departure time changed</p>
                <p className="text-xs text-gray-400 mt-0.5">5 mins ago</p>
              </div>
            </div>
            <div className="flex gap-3 pb-3 border-b border-gray-100">
              <div className="bg-purple-500 w-1 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">Check-in Complete</p>
                <p className="text-xs text-gray-500">45 attendees checked in</p>
                <p className="text-xs text-gray-400 mt-0.5">1 hour ago</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="bg-orange-500 w-1 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">Notification Sent</p>
                <p className="text-xs text-gray-500">Bus delay alert to 150 users</p>
                <p className="text-xs text-gray-400 mt-0.5">2 hours ago</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 sm:gap-4">
        <button onClick={() => navigate('/bus-checkin')} className="card card-hover p-4 text-center min-h-[100px] touch-manipulation flex flex-col items-center justify-center">
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
            <Bus className="w-5 h-5 text-purple-600" />
          </div>
          <p className="font-medium text-gray-900 text-sm">Bus Check-in</p>
          <p className="text-xs text-gray-400 mt-0.5">Board passengers</p>
        </button>

        <button onClick={() => navigate('/check-in')} className="card card-hover p-4 text-center min-h-[100px] touch-manipulation flex flex-col items-center justify-center">
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
            <QrCode className="w-5 h-5 text-purple-600" />
          </div>
          <p className="font-medium text-gray-900 text-sm">Session Check-in</p>
          <p className="text-xs text-gray-400 mt-0.5">Scan attendees</p>
        </button>

        <button onClick={() => navigate('/notifications')} className="card card-hover p-4 text-center min-h-[100px] touch-manipulation flex flex-col items-center justify-center">
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
            <Bell className="w-5 h-5 text-purple-600" />
          </div>
          <p className="font-medium text-gray-900 text-sm">Notifications</p>
          <p className="text-xs text-gray-400 mt-0.5">Alert members</p>
        </button>

        <button onClick={() => navigate('/conferences')} className="card card-hover p-4 text-center min-h-[100px] touch-manipulation flex flex-col items-center justify-center">
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
            <Calendar className="w-5 h-5 text-purple-600" />
          </div>
          <p className="font-medium text-gray-900 text-sm">New Event</p>
          <p className="text-xs text-gray-400 mt-0.5">Create event</p>
        </button>

        <button onClick={() => navigate('/analytics')} className="card card-hover p-4 text-center min-h-[100px] touch-manipulation flex flex-col items-center justify-center">
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
            <BarChart3 className="w-5 h-5 text-purple-600" />
          </div>
          <p className="font-medium text-gray-900 text-sm">Analytics</p>
          <p className="text-xs text-gray-400 mt-0.5">View insights</p>
        </button>
      </div>
    </div>
  )
}
