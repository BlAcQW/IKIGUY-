/**
 * Shared Admin Layout Component
 *
 * Provides a consistent admin interface across all KasaAI applications.
 * Features:
 * - Responsive sidebar navigation
 * - Organization selector
 * - User menu
 * - Breadcrumbs
 */

import React, { useState } from 'react';
import {
  Building2,
  Users,
  Settings,
  CreditCard,
  LayoutDashboard,
  ChevronDown,
  Menu,
  X,
  LogOut,
  User,
  Bell,
  Search,
  Wallet,
  BarChart3
} from 'lucide-react';

interface Organization {
  id: string;
  name: string;
  display_name: string;
  role: 'owner' | 'admin' | 'user';
}

interface AdminLayoutProps {
  children: React.ReactNode;
  currentPage: string;
  user?: {
    name: string;
    email: string;
    avatar?: string;
  };
  organizations?: Organization[];
  currentOrganization?: Organization;
  onOrganizationChange?: (orgId: string) => void;
  appName?: string;
  customNavItems?: Array<{
    icon: any;
    label: string;
    path: string;
  }>;
}

export default function AdminLayout({
  children,
  currentPage,
  user,
  organizations = [],
  currentOrganization,
  onOrganizationChange,
  appName = 'KasaAI',
  customNavItems = []
}: AdminLayoutProps) {
  // Default sidebar closed on mobile (screen width < 768px)
  const [sidebarOpen, setSidebarOpen] = useState(typeof window !== 'undefined' ? window.innerWidth >= 768 : true);
  const [orgMenuOpen, setOrgMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Handle responsive sidebar on window resize
  React.useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Core admin navigation items
  const coreNavItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/admin' },
    { icon: Building2, label: 'Organizations', path: '/admin/organizations' },
    { icon: Users, label: 'Users', path: '/admin/users' },
    { icon: Settings, label: 'Settings', path: '/admin/settings' },
    { icon: CreditCard, label: 'Billing', path: '/admin/billing' },
    { icon: Wallet, label: 'Wallet', path: '/admin/wallet' },
    { icon: BarChart3, label: 'Analytics', path: '/admin/analytics' },
  ];

  // Combine core and custom navigation items
  const navItems = [...coreNavItems, ...customNavItems];

  const NavItem = ({ icon: Icon, label, path, active }: any) => (
    <a
      href={path}
      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
        active
          ? 'bg-blue-600 text-white'
          : 'text-gray-700 hover:bg-gray-100'
      }`}
    >
      <Icon className="w-5 h-5" />
      {sidebarOpen && <span className="font-medium">{label}</span>}
    </a>
  );

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:static h-screen bg-white border-r border-gray-200 transition-all duration-300 z-40
          ${sidebarOpen ? 'translate-x-0 w-64' : '-translate-x-full md:translate-x-0 md:w-20 w-64'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
            {sidebarOpen && (
              <h1 className="text-xl font-bold text-gray-900">{appName}</h1>
            )}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>

          {/* Organization Selector */}
          {sidebarOpen && organizations.length > 0 && (
            <div className="p-4 border-b border-gray-200">
              <div className="relative">
                <button
                  onClick={() => setOrgMenuOpen(!orgMenuOpen)}
                  className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                      <Building2 className="w-4 h-4 text-white" />
                    </div>
                    <div className="text-left">
                      <p className="text-sm font-semibold text-gray-900">
                        {currentOrganization?.display_name || 'Select Organization'}
                      </p>
                      <p className="text-xs text-gray-500">
                        {currentOrganization?.role || 'No role'}
                      </p>
                    </div>
                  </div>
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                </button>

                {/* Organization Dropdown */}
                {orgMenuOpen && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
                    {organizations.map((org) => (
                      <button
                        key={org.id}
                        onClick={() => {
                          onOrganizationChange?.(org.id);
                          setOrgMenuOpen(false);
                        }}
                        className={`w-full flex items-center gap-3 p-3 hover:bg-gray-50 transition-colors ${
                          org.id === currentOrganization?.id ? 'bg-blue-50' : ''
                        }`}
                      >
                        <div className="w-8 h-8 bg-gray-200 rounded-lg flex items-center justify-center">
                          <Building2 className="w-4 h-4 text-gray-600" />
                        </div>
                        <div className="text-left flex-1">
                          <p className="text-sm font-medium text-gray-900">{org.display_name}</p>
                          <p className="text-xs text-gray-500 capitalize">{org.role}</p>
                        </div>
                      </button>
                    ))}
                    <div className="border-t border-gray-200 p-2">
                      <a
                        href="/admin/organizations/new"
                        className="block w-full text-center p-2 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                      >
                        + Create Organization
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <NavItem
                key={item.path}
                icon={item.icon}
                label={item.label}
                path={item.path}
                active={currentPage === item.path}
              />
            ))}
          </nav>

          {/* User Menu */}
          {sidebarOpen && user && (
            <div className="p-4 border-t border-gray-200">
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <span className="text-white font-semibold">
                      {user.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 text-left">
                    <p className="text-sm font-semibold text-gray-900">{user.name}</p>
                    <p className="text-xs text-gray-500">{user.email}</p>
                  </div>
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                </button>

                {/* User Dropdown */}
                {userMenuOpen && (
                  <div className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                    <a
                      href="/profile"
                      className="flex items-center gap-3 p-3 hover:bg-gray-50 transition-colors"
                    >
                      <User className="w-4 h-4 text-gray-600" />
                      <span className="text-sm text-gray-700">Profile</span>
                    </a>
                    <a
                      href="/settings"
                      className="flex items-center gap-3 p-3 hover:bg-gray-50 transition-colors"
                    >
                      <Settings className="w-4 h-4 text-gray-600" />
                      <span className="text-sm text-gray-700">Settings</span>
                    </a>
                    <div className="border-t border-gray-200">
                      <button
                        onClick={async () => {
                          try {
                            // Sign out from Supabase to clear the session
                            const { supabase } = await import('../../lib/supabase');
                            await supabase.auth.signOut();
                          } catch (error) {
                            console.error('Error signing out from Supabase:', error);
                          }

                          // Clear all auth-related data from localStorage
                          localStorage.removeItem('access_token');
                          localStorage.removeItem('user_id');
                          localStorage.removeItem('user_role');
                          localStorage.removeItem('user_email');

                          // Clear any session storage
                          sessionStorage.clear();

                          // Redirect to login page
                          window.location.href = '/login';
                        }}
                        className="flex items-center gap-3 p-3 w-full hover:bg-gray-50 transition-colors text-red-600"
                      >
                        <LogOut className="w-4 h-4" />
                        <span className="text-sm">Logout</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden w-full md:w-auto">
        {/* Header */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4 md:px-6">
          <div className="flex items-center gap-4 flex-1">
            {/* Mobile menu button */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search..."
                className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button className="relative p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <Bell className="w-5 h-5 text-gray-600" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
