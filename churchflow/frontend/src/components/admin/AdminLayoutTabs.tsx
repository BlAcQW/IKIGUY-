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
  MessageSquare
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
    { icon: MessageSquare, label: 'SMS Campaigns', path: '/admin/sms-campaigns' },
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

  const handleLogout = async () => {
    try {
      // Sign out from Supabase to clear the session
      const { supabase } = await import('../../lib/supabase');
      await supabase.auth.signOut();
    } catch (error) {
      console.error('Error signing out from Supabase:', error);
    }

    // Clear local storage
    localStorage.removeItem('access_token');
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

                {/* Dropdown Menu */}
                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-56 bg-gray-800 border border-gray-700 rounded-lg shadow-xl py-2 z-50">
                    {/* User Info (mobile) */}
                    <div className="px-4 py-3 border-b border-gray-700 sm:hidden">
                      <p className="text-sm font-medium text-white">{user.name}</p>
                      <p className="text-xs text-gray-400">{user.email}</p>
                    </div>

                    {/* Settings Option */}
                    <a
                      href="/admin/settings"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
                    >
                      <Settings className="w-4 h-4" />
                      <span>User Settings</span>
                    </a>

                    {/* Logout Option */}
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Logout</span>
                    </button>
                  </div>
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
