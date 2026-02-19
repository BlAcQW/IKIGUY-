import { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Bus, Calendar, Users, QrCode, Bell, LogOut, Menu, X, Building2, UserCheck, Mic, Settings, ChevronDown, Phone, BarChart3, MessageSquare } from 'lucide-react'

interface User {
  id: string
  name: string
  phone: string
  roles: string[]
}

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

export default function Dashboard() {
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState<User | null>(null)
  // Default sidebar closed on mobile (screen width < 768px)
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768)
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30030'
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
  const [showUserMenu, setShowUserMenu] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const [topBusRoutes, setTopBusRoutes] = useState<BusRoute[]>([])

  useEffect(() => {
    fetchUser()
    fetchStats()

    // Handle responsive sidebar on window resize
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarOpen(false)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
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
    }
  }

  const fetchUser = async (retryWithTokenExchange = true) => {
    const token = localStorage.getItem('access_token')

    if (!token) {
      // No token, but allow access anyway for demo
      setUser({
        id: 'demo',
        name: 'Demo User',
        phone: '+233200000000',
        roles: ['admin']
      })
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      // If we get 401, try to exchange token and retry
      if (response.status === 401 && retryWithTokenExchange) {
        try {
          // Import supabase dynamically
          const { supabase } = await import('../lib/supabase')
          const { data: { session } } = await supabase.auth.getSession()

          if (session?.access_token) {
            // Exchange the fresh Supabase token for a backend JWT
            const exchangeResponse = await fetch(`${apiBaseUrl}/api/v1/auth/exchange-token`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${session.access_token}`,
                'Content-Type': 'application/json'
              }
            })

            if (exchangeResponse.ok) {
              const exchangeData = await exchangeResponse.json()
              localStorage.setItem('access_token', exchangeData.access_token)
              // Retry the request with the new token (but don't retry again to avoid loops)
              return fetchUser(false)
            }
          }
        } catch (exchangeError) {
          // Token exchange failed - fall through to error handling
        }
      }

      if (!response.ok) {
        // Only log error if we've already tried token exchange
        if (!retryWithTokenExchange) {
          console.error('Failed to fetch user:', response.statusText)
        }
        throw new Error('Unauthorized')
      }

      const data = await response.json()
      setUser({
        id: data.id,
        name: data.name || 'User',
        phone: data.phone || '',
        roles: data.roles || []
      })
    } catch (err: any) {
      // Only log error if we've already tried token exchange
      if (!retryWithTokenExchange) {
        console.error('Error fetching user:', err)
      }
      // If API fails, use demo user
      setUser({
        id: 'demo',
        name: 'Demo User',
        phone: '+233200000000',
        roles: ['admin']
      })
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      // Sign out from Supabase to clear the session
      const { supabase } = await import('../lib/supabase')
      await supabase.auth.signOut()
    } catch (error) {
      console.error('Error signing out from Supabase:', error)
    }

    // Clear all auth-related data from localStorage
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('user_role')
    localStorage.removeItem('user_email')

    // Clear any session storage
    sessionStorage.clear()

    // Redirect to login page
    window.location.href = '/login'
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  const menuItems = [
    { id: 'overview', label: 'Overview', icon: Users, path: '/dashboard' },
    { id: 'buses', label: 'Bus Management', icon: Bus, path: '/buses' },
    { id: 'conferences', label: 'Conferences', icon: Calendar, path: '/conferences' },
    { id: 'registered-users', label: 'Registered Users', icon: UserCheck, path: '/registered-users' },
    { id: 'bus-checkin', label: 'Bus Check-in', icon: Bus, path: '/bus-checkin' },
    { id: 'session-checkin', label: 'Session Check-in', icon: QrCode, path: '/check-in' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, path: '/analytics' },
    { id: 'sms-campaigns', label: 'SMS Campaigns', icon: MessageSquare, path: '/sms-campaigns' },
    { id: 'voice-library', label: 'Voice Library', icon: Mic, path: '/admin/voice-library' },
    { id: 'notifications', label: 'Notifications', icon: Bell, path: '/notifications' },
  ]

  // Get current active path
  const currentPath = location.pathname
  const activeItem = menuItems.find(item => item.path === currentPath) || menuItems[0]

  const closeSidebarOnMobile = () => {
    if (window.innerWidth < 768) {
      setSidebarOpen(false)
    }
  }

  return (
    <div className="relative min-h-screen bg-gray-50 overflow-x-hidden">
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-gray-900/50 z-10 md:hidden animate-fade-in"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar - z-30 to stay below modals (z-50+) */}
      <div className={`fixed left-0 top-0 h-full bg-white shadow-sm transition-all duration-300 z-30
        ${sidebarOpen ? 'translate-x-0 w-64' : '-translate-x-full md:translate-x-0 md:w-20'}`}>
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center justify-between">
            {sidebarOpen && <h1 className="text-lg font-semibold text-gray-900">ChurchFlow</h1>}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        <nav className="p-3 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = currentPath === item.path
            return (
              <button
                key={item.id}
                onClick={() => {
                  navigate(item.path)
                  closeSidebarOnMobile()
                }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors touch-manipulation text-sm ${
                  isActive
                    ? 'bg-purple-50 text-purple-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && <span>{item.label}</span>}
              </button>
            )
          })}
        </nav>

        {/* Talk To Papa Link */}
        <div className="px-3 mt-2 pt-2 border-t border-gray-100">
          <a href="/talk-to-papa" className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-teal-600 hover:bg-teal-50 transition-colors text-sm">
            <Phone className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span className="font-medium">Talk To Papa</span>}
          </a>
        </div>

        {/* Admin Link */}
        <div className="px-3 mt-1">
          <a href="/admin/organizations" className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors text-sm">
            <Building2 className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span className="font-medium">Admin</span>}
          </a>
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-gray-100 bg-white">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-red-600 hover:bg-red-50 transition-colors text-sm"
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span className="font-medium">Logout</span>}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className={`min-h-screen transition-all duration-300 ${sidebarOpen ? 'md:ml-64' : 'md:ml-20'}`}>
        {/* Header */}
        <header className="bg-white border-b border-gray-100 px-4 md:px-6 py-4 sticky top-0 z-10 w-full">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Mobile menu button */}
              <button
                onClick={() => setSidebarOpen(true)}
                className="md:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500"
              >
                <Menu className="w-5 h-5" />
              </button>
              <div>
                <h2 className="text-lg md:text-xl font-semibold text-gray-900">
                  {activeItem.label}
                </h2>
              </div>
            </div>
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 hover:bg-gray-50 rounded-lg px-2 py-1.5 transition-colors"
              >
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-medium text-gray-900">{user?.name || 'Admin User'}</p>
                  <p className="text-xs text-gray-400">{user?.phone}</p>
                </div>
                <div className="w-9 h-9 bg-purple-100 rounded-full flex items-center justify-center">
                  <span className="text-purple-600 font-medium text-sm">
                    {user?.name?.[0] || 'A'}
                  </span>
                </div>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
              </button>

              {/* Dropdown Menu */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-52 bg-white border border-gray-100 rounded-xl shadow-lg py-1.5 z-50 animate-fade-in">
                  {/* User Info (mobile) */}
                  <div className="px-4 py-2.5 border-b border-gray-100 sm:hidden">
                    <p className="text-sm font-medium text-gray-900">{user?.name || 'Admin User'}</p>
                    <p className="text-xs text-gray-400">{user?.phone}</p>
                  </div>

                  {/* Admin Panel Link */}
                  <a
                    href="/admin/organizations"
                    className="flex items-center gap-2.5 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
                  >
                    <Building2 className="w-4 h-4" />
                    <span>Admin Panel</span>
                  </a>

                  {/* Settings Option */}
                  <a
                    href="/admin/settings"
                    className="flex items-center gap-2.5 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
                  >
                    <Settings className="w-4 h-4" />
                    <span>Settings</span>
                  </a>

                  {/* Logout Option */}
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Logout</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <main className="p-4 md:p-6 bg-gray-50 min-h-screen w-full">
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
                <button onClick={() => setActiveTab('bus-checkin')} className="card card-hover p-4 text-center min-h-[100px] touch-manipulation flex flex-col items-center justify-center">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <Bus className="w-5 h-5 text-purple-600" />
                  </div>
                  <p className="font-medium text-gray-900 text-sm">Bus Check-in</p>
                  <p className="text-xs text-gray-400 mt-0.5">Board passengers</p>
                </button>

                <button onClick={() => setActiveTab('session-checkin')} className="card card-hover p-4 text-center min-h-[100px] touch-manipulation flex flex-col items-center justify-center">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <QrCode className="w-5 h-5 text-purple-600" />
                  </div>
                  <p className="font-medium text-gray-900 text-sm">Session Check-in</p>
                  <p className="text-xs text-gray-400 mt-0.5">Scan attendees</p>
                </button>

                <button onClick={() => setActiveTab('notifications')} className="card card-hover p-4 text-center min-h-[100px] touch-manipulation flex flex-col items-center justify-center">
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
        </main>
      </div>
    </div>
  )
}
