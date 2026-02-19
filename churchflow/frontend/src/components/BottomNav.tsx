import { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Home, Calendar, QrCode, Bus, Menu, X, Settings, Users, MessageSquare, Building2, LogOut, Download, DollarSign, UserCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { usePWA } from '../hooks/usePWA'

interface NavItem {
  id: string
  label: string
  icon: React.ElementType
  path: string
  requiresAuth?: boolean
}

const mainNavItems: NavItem[] = [
  { id: 'home', label: 'Home', icon: Home, path: '/dashboard' },
  { id: 'events', label: 'Events', icon: Calendar, path: '/events' },
  { id: 'checkin', label: 'Check-in', icon: QrCode, path: '/check-in' },
  { id: 'buses', label: 'Buses', icon: Bus, path: '/buses' },
  { id: 'menu', label: 'Menu', icon: Menu, path: '' },
]

const menuItems: NavItem[] = [
  { id: 'portal', label: 'Member Portal', icon: UserCircle, path: '/portal' },
  { id: 'giving', label: 'Give', icon: DollarSign, path: '/giving' },
  { id: 'conferences', label: 'Manage Events', icon: Calendar, path: '/admin/conferences' },
  { id: 'organizations', label: 'Organizations', icon: Building2, path: '/admin/organizations' },
  { id: 'users', label: 'Users', icon: Users, path: '/admin/users' },
  { id: 'sms', label: 'SMS Campaigns', icon: MessageSquare, path: '/admin/sms-campaigns' },
  { id: 'settings', label: 'Settings', icon: Settings, path: '/admin/settings' },
]

export default function BottomNav() {
  const navigate = useNavigate()
  const location = useLocation()
  const [isVisible, setIsVisible] = useState(true)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const lastScrollY = useRef(0)
  const { isInstallable, promptInstall } = usePWA()

  // Hide bottom nav on scroll down, show on scroll up
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY

      if (currentScrollY > lastScrollY.current && currentScrollY > 100) {
        setIsVisible(false)
        setIsMenuOpen(false)
      } else {
        setIsVisible(true)
      }

      lastScrollY.current = currentScrollY
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Close menu when route changes
  useEffect(() => {
    setIsMenuOpen(false)
  }, [location.pathname])

  const isActive = (path: string) => {
    if (path === '/dashboard' && (location.pathname === '/' || location.pathname === '/dashboard')) {
      return true
    }
    if (path === '/events' && (location.pathname === '/events' || location.pathname.startsWith('/conference'))) {
      return true
    }
    return location.pathname === path
  }

  const handleNavClick = (item: NavItem) => {
    if (item.id === 'menu') {
      setIsMenuOpen(!isMenuOpen)
    } else {
      navigate(item.path)
      setIsMenuOpen(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('user_email')
    navigate('/login')
  }

  const handleInstall = async () => {
    await promptInstall()
    setIsMenuOpen(false)
  }

  // Don't show on login page or public registration
  const hiddenPaths = ['/login', '/register', '/self-checkin']
  if (hiddenPaths.some(path => location.pathname.startsWith(path))) {
    return null
  }

  return (
    <>
      {/* Menu overlay */}
      <AnimatePresence>
        {isMenuOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/50 z-40 md:hidden"
              onClick={() => setIsMenuOpen(false)}
            />

            {/* Menu panel */}
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed bottom-[calc(4rem+env(safe-area-inset-bottom))] left-0 right-0 bg-white rounded-t-2xl shadow-2xl z-50 md:hidden max-h-[70vh] overflow-y-auto"
            >
              <div className="p-4">
                {/* Drag handle */}
                <div className="w-12 h-1 bg-gray-300 rounded-full mx-auto mb-4" />

                {/* Menu header */}
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Menu</h3>
                  <button
                    onClick={() => setIsMenuOpen(false)}
                    className="p-2 rounded-full hover:bg-gray-100 transition-colors"
                  >
                    <X className="w-5 h-5 text-gray-500" />
                  </button>
                </div>

                {/* Menu items */}
                <div className="space-y-1">
                  {menuItems.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleNavClick(item)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
                        isActive(item.path)
                          ? 'bg-purple-100 text-purple-700'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <item.icon className="w-5 h-5" />
                      <span className="font-medium">{item.label}</span>
                    </button>
                  ))}
                </div>

                {/* Divider */}
                <div className="h-px bg-gray-200 my-4" />

                {/* Install app button (only if installable) */}
                {isInstallable && (
                  <button
                    onClick={handleInstall}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-purple-700 hover:bg-purple-50 transition-colors mb-2"
                  >
                    <Download className="w-5 h-5" />
                    <span className="font-medium">Install App</span>
                  </button>
                )}

                {/* Logout button */}
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                  <span className="font-medium">Sign Out</span>
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Bottom navigation bar */}
      <motion.nav
        initial={{ y: 0 }}
        animate={{ y: isVisible ? 0 : 100 }}
        transition={{ duration: 0.2 }}
        className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-40 md:hidden"
        style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        <div className="flex items-center justify-around h-16">
          {mainNavItems.map((item) => {
            const active = item.id === 'menu' ? isMenuOpen : isActive(item.path)

            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item)}
                className="relative flex flex-col items-center justify-center flex-1 h-full transition-colors"
              >
                {/* Active indicator */}
                <AnimatePresence>
                  {active && (
                    <motion.div
                      layoutId="activeTab"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      className="absolute -top-0.5 w-12 h-1 bg-purple-600 rounded-full"
                    />
                  )}
                </AnimatePresence>

                {/* Icon */}
                <motion.div
                  whileTap={{ scale: 0.9 }}
                  className={`p-1.5 rounded-xl transition-colors ${
                    active ? 'text-purple-600' : 'text-gray-500'
                  }`}
                >
                  <item.icon className="w-5 h-5" strokeWidth={active ? 2.5 : 2} />
                </motion.div>

                {/* Label */}
                <span
                  className={`text-[10px] mt-0.5 font-medium transition-colors ${
                    active ? 'text-purple-600' : 'text-gray-500'
                  }`}
                >
                  {item.label}
                </span>
              </button>
            )
          })}
        </div>
      </motion.nav>
    </>
  )
}
