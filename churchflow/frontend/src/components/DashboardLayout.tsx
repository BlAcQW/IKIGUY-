import { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { Bus, Calendar, Users, QrCode, Bell, LogOut, Menu, X, UserCheck, Mic, BarChart3, MessageSquare, Phone, DollarSign, UserCircle, Building2, ChevronDown, Church, UserPlus, Megaphone } from 'lucide-react'
import { useOrganization } from '../contexts/OrganizationContext'

interface User {
  id: string
  name: string
  phone: string
  roles: string[]
}

interface DashboardLayoutProps {
  children: React.ReactNode
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState<User | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showOrgMenu, setShowOrgMenu] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const orgMenuRef = useRef<HTMLDivElement>(null)
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:30030'
  const { organizations, currentOrganization, setCurrentOrganization } = useOrganization()

  const menuItems = [
    { id: 'overview', label: 'Overview', icon: Users, path: '/dashboard' },
    { id: 'portal', label: 'Member Portal', icon: UserCircle, path: '/portal' },
    // Members dashboard moved to Member Portal Admin tab - sidebar item removed to avoid duplication
    { id: 'giving', label: 'Giving', icon: DollarSign, path: '/giving' },
    { id: 'visitors', label: 'Visitors', icon: UserCheck, path: '/visitors' },
    { id: 'first-timers', label: 'First Timers', icon: UserPlus, path: '/admin/first-timers' },
    { id: 'cell-groups', label: 'Cell Groups', icon: Users, path: '/cell-groups' },
    { id: 'groups', label: 'Group Management', icon: Users, path: '/admin/groups' },
    { id: 'buses', label: 'Bus Management', icon: Bus, path: '/buses' },
    { id: 'conferences', label: 'Conferences', icon: Calendar, path: '/conferences' },
    { id: 'services', label: 'Services', icon: Church, path: '/admin/services' },
    { id: 'registered-users', label: 'Registered Users', icon: UserCheck, path: '/registered-users' },
    { id: 'bus-checkin', label: 'Bus Check-in', icon: Bus, path: '/bus-checkin' },
    { id: 'session-checkin', label: 'Session Check-in', icon: QrCode, path: '/check-in' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, path: '/analytics' },
    { id: 'sms-campaigns', label: 'SMS Campaigns', icon: MessageSquare, path: '/sms-campaigns' },
    { id: 'voice-library', label: 'Voice Library', icon: Mic, path: '/admin/voice-library' },
    { id: 'announcements', label: 'Announcements', icon: Megaphone, path: '/admin/announcements' },
    { id: 'notifications', label: 'Notifications', icon: Bell, path: '/notifications' },
  ]

  const currentPath = location.pathname
  const activeItem = menuItems.find(item => item.path === currentPath) || menuItems[0]

  useEffect(() => {
    fetchUser()

    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarOpen(false)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false)
      }
      if (orgMenuRef.current && !orgMenuRef.current.contains(event.target as Node)) {
        setShowOrgMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const fetchUser = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) return

      const response = await fetch(`${apiBaseUrl}/api/v1/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setUser(data)
      }
    } catch (err) {
      console.error('Failed to fetch user:', err)
    }
  }

  const handleLogout = async () => {
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  const closeSidebarOnMobile = () => {
    if (window.innerWidth < 768) {
      setSidebarOpen(false)
    }
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar Overlay */}
      {sidebarOpen && window.innerWidth < 768 && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:static inset-y-0 left-0 transform ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0 transition-transform duration-200 ease-in-out z-30 bg-white border-r border-gray-200 flex flex-col w-64`}
      >
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <Link 
            to="/" 
            className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer"
            onClick={closeSidebarOnMobile}
          >
            <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">CF</span>
            </div>
            <span className="font-semibold text-gray-900">ChurchFlow</span>
          </Link>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="md:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Organization Switcher */}
        {organizations.length > 1 && (
          <div className="px-3 pt-3 pb-2 border-b border-gray-100" ref={orgMenuRef}>
            <div className="relative">
              <button
                onClick={() => setShowOrgMenu(!showOrgMenu)}
                className="w-full flex items-center justify-between gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors text-sm"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Building2 className="w-4 h-4 flex-shrink-0 text-purple-600" />
                  <span className="truncate text-gray-900 font-medium">
                    {currentOrganization?.display_name || currentOrganization?.name || 'Select Organization'}
                  </span>
                </div>
                <ChevronDown className={`w-4 h-4 flex-shrink-0 text-gray-500 transition-transform ${showOrgMenu ? 'rotate-180' : ''}`} />
              </button>

              {showOrgMenu && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
                  {organizations.map((membership) => (
                    <button
                      key={membership.organization.id}
                      onClick={() => {
                        setCurrentOrganization(membership.organization.id)
                        setShowOrgMenu(false)
                      }}
                      className={`w-full text-left px-3 py-2 hover:bg-gray-50 transition-colors text-sm ${
                        currentOrganization?.id === membership.organization.id
                          ? 'bg-purple-50 text-purple-700 font-medium'
                          : 'text-gray-700'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 flex-shrink-0" />
                        <div className="min-w-0">
                          <div className="truncate">{membership.organization.display_name || membership.organization.name}</div>
                          <div className="text-xs text-gray-500 truncate">{membership.role}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        <nav className="p-3 space-y-1 flex-1 overflow-y-auto">
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
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>

        {/* Talk To Papa Link */}
        <div className="px-3 mt-2 pt-2 border-t border-gray-100">
          <button
            onClick={() => {
              navigate('/talk-to-papa')
              closeSidebarOnMobile()
            }}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm bg-gradient-to-r from-purple-600 to-purple-700 text-white hover:from-purple-700 hover:to-purple-800"
          >
            <Phone className="w-5 h-5 flex-shrink-0" />
            <span>Talk to Papa</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-4 md:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
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
                <p className="text-xs text-gray-500">{user?.roles?.[0] || 'Admin'}</p>
              </div>
              <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
                {(user?.name || 'A').charAt(0).toUpperCase()}
              </div>
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 bg-gray-50">
          {children}
        </main>
      </div>
    </div>
  )
}
