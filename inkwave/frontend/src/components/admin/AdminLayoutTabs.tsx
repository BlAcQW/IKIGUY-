/**
 * Admin Layout with Tabs - Dark Theme
 *
 * Provides admin interface with horizontal tab navigation
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Building2,
  Users,
  Settings,
  CreditCard,
  ArrowLeft,
  User as UserIcon,
  LogOut,
  ChevronDown,
  Sparkles,
  Wallet,
  Volume2,
  Upload,
  Shield
} from 'lucide-react';

interface AdminLayoutTabsProps {
  children: React.ReactNode;
  currentPage: string;
  user?: {
    name: string;
    email: string;
  };
  appName?: string;
  onBack?: () => void;
}

export default function AdminLayoutTabs({
  children,
  currentPage,
  user,
  appName = 'KasaAI',
  onBack
}: AdminLayoutTabsProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const tabs = [
    { icon: Building2, label: 'Organizations', path: '/admin/organizations' },
    { icon: Users, label: 'Users', path: '/admin/users' },
    { icon: Shield, label: 'Moderation', path: '/admin/books/moderation' },
    { icon: Settings, label: 'Settings', path: '/admin/settings' },
    { icon: CreditCard, label: 'Billing', path: '/admin/billing' },
  ];

  const isActive = (path: string) => currentPage === path || currentPage.startsWith(path);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    // Clear local storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('sb-supabase-auth-token');
    localStorage.removeItem('current_organization_id');

    // Redirect to login
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left: Back button and title */}
            <div className="flex items-center gap-4">
              {onBack && (
                <button
                  onClick={onBack}
                  className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
              )}
              <div>
                <h1 className="text-xl font-bold text-white">{appName} Admin</h1>
              </div>
            </div>

            {/* Right: User info with dropdown */}
            {user && (
              <div className="relative" ref={userMenuRef}>
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-3 hover:bg-gray-700 rounded-lg px-3 py-2 transition-colors"
                >
                  <div className="text-right hidden sm:block">
                    <p className="text-sm font-medium text-white">{user.name}</p>
                    <p className="text-xs text-gray-400">{user.email}</p>
                  </div>
                  <div className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center">
                    <UserIcon className="w-5 h-5 text-gray-300" />
                  </div>
                  <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
                </button>

                {/* Dropdown Menu - Matches Header component */}
                {showUserMenu && (
                  <>
                    {/* Backdrop to close menu */}
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setShowUserMenu(false)}
                    />
                    <div className="absolute right-0 mt-2 w-56 sm:w-64 bg-gray-800 rounded-xl shadow-2xl border border-purple-500/30 z-50">
                      {/* User Info Header */}
                      <div className="px-4 py-3 border-b border-gray-700 bg-gradient-to-r from-purple-500/5 to-pink-500/5 rounded-t-xl">
                        <p className="text-sm font-semibold text-white truncate">{user.name}</p>
                        <p className="text-xs text-gray-400 truncate">{user.email}</p>
                      </div>

                      {/* Profile Link */}
                      <a
                        href="/profile"
                        onClick={() => setShowUserMenu(false)}
                        className="block px-4 py-3 hover:bg-purple-500/10 transition"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center">
                            <Sparkles className="h-4 w-4 text-purple-400" />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-white">My Profile</p>
                            <p className="text-xs text-gray-400">Personalized for you</p>
                          </div>
                        </div>
                      </a>

                      {/* Wallet Link */}
                      <a
                        href="/wallet"
                        onClick={() => setShowUserMenu(false)}
                        className="block px-4 py-3 hover:bg-gray-700 transition flex items-center space-x-3"
                      >
                        <Wallet className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-300">Wallet</span>
                      </a>

                      {/* Voice Settings Link */}
                      <a
                        href="/voice-settings"
                        onClick={() => setShowUserMenu(false)}
                        className="block px-4 py-3 hover:bg-gray-700 transition flex items-center space-x-3"
                      >
                        <Volume2 className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-300">Voice Settings</span>
                      </a>

                      {/* My Books Link */}
                      <a
                        href="/my-books"
                        onClick={() => setShowUserMenu(false)}
                        className="block px-4 py-3 hover:bg-gray-700 transition flex items-center space-x-3"
                      >
                        <Upload className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-300">My Books</span>
                      </a>

                      {/* Admin Links */}
                      <div className="border-t border-gray-700 my-1"></div>
                      <a
                        href="/admin"
                        onClick={() => setShowUserMenu(false)}
                        className="block px-4 py-3 hover:bg-gray-700 transition flex items-center space-x-3"
                      >
                        <Settings className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-300">Admin</span>
                      </a>
                      <a
                        href="/admin/organizations"
                        onClick={() => setShowUserMenu(false)}
                        className="block px-4 py-3 hover:bg-gray-700 transition flex items-center space-x-3"
                      >
                        <Building2 className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-300">Organizations</span>
                      </a>

                      {/* Sign Out */}
                      <div className="border-t border-gray-700 my-1"></div>
                      <button
                        onClick={() => {
                          setShowUserMenu(false);
                          handleLogout();
                        }}
                        className="w-full text-left px-4 py-3 hover:bg-red-500/10 transition flex items-center space-x-3 text-red-400 rounded-b-xl"
                      >
                        <LogOut className="h-4 w-4" />
                        <span className="text-sm">Sign Out</span>
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Tabs Navigation */}
          <div className="flex gap-1 -mb-px">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const active = isActive(tab.path);
              return (
                <a
                  key={tab.path}
                  href={tab.path}
                  className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                    active
                      ? 'border-gray-400 text-white bg-gray-900'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:bg-gray-700/50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-medium text-sm">{tab.label}</span>
                </a>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
