import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useOrganization } from '@/contexts/OrganizationContext'
import {
  Building2,
  Users,
  DollarSign,
  FolderKanban,
  BarChart3,
  Settings,
  LogOut,
  Home,
  Briefcase,
  UserPlus,
  Users2,
  Menu,
  X,
} from 'lucide-react'

export default function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { signOut } = useAuth()
  const { currentOrganization, organizations, setCurrentOrganization } = useOrganization()
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'CRM', href: '/crm', icon: Users },
    { name: 'HR', href: '/hr', icon: Briefcase },
    { name: 'Onboarding', href: '/onboarding', icon: UserPlus },
    { name: 'Finance', href: '/finance', icon: DollarSign },
    { name: 'Projects', href: '/projects', icon: FolderKanban },
    { name: 'Partnerships', href: '/partnerships', icon: Users2 },
    { name: 'Analytics', href: '/bi', icon: BarChart3 },
    { name: 'Integrations', href: '/integrations', icon: Settings },
    { name: 'Admin', href: '/admin', icon: Building2 },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center gap-3">
              {/* Mobile menu button */}
              <button
                onClick={() => setSidebarOpen(true)}
                className="md:hidden p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-600 hover:text-gray-900"
                aria-label="Open navigation menu"
              >
                <Menu className="w-6 h-6" />
              </button>
              <h1 className="text-xl font-bold text-gray-900">KasaAI ERP</h1>
            </div>
            <div className="flex items-center space-x-4">
              {/* Organization Selector */}
              {organizations.length > 0 && (
                <select
                  value={currentOrganization?.id || ''}
                  onChange={(e) => setCurrentOrganization(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {organizations.map((membership) => (
                    <option key={membership.organization.id} value={membership.organization.id}>
                      {membership.organization.display_name} ({membership.role})
                    </option>
                  ))}
                </select>
              )}
              <button
                onClick={() => signOut()}
                className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-700 hover:text-gray-900"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex">
        {/* Backdrop (mobile only) */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-40 md:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
        )}

        {/* Sidebar */}
        <aside className={`
          fixed md:static inset-y-0 left-0 z-50
          w-64 bg-white border-r min-h-[calc(100vh-4rem)]
          transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          md:translate-x-0
        `}>
          {/* Close button (mobile only) */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="md:hidden absolute top-4 right-4 p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-600 hover:text-gray-900"
            aria-label="Close navigation menu"
          >
            <X className="w-6 h-6" />
          </button>

          <nav className="p-4 space-y-1 pt-12 md:pt-4">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 md:p-8 min-w-0 overflow-x-auto">{children}</main>
      </div>
    </div>
  )
}
