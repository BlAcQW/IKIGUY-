import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Calendar, CheckSquare, Wallet, User, Menu, X, Bell, LogOut, Building2, Volume2 } from 'lucide-react';
import { useStore } from '../lib/store';
import { formatCurrency } from '../lib/utils';

const navItems = [
  { name: 'Home', path: '/', icon: Home },
  { name: 'Events', path: '/events', icon: Calendar },
  { name: 'Tasks', path: '/tasks', icon: CheckSquare },
  { name: 'Wallet', path: '/wallet', icon: Wallet },
  { name: 'Voice Settings', path: '/voice-settings', icon: Volume2 },
  { name: 'Profile', path: '/profile', icon: User },
];

export const Layout: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const { user, wallet, sidebarOpen, toggleSidebar, clearUser } = useStore();

  const handleLogout = () => {
    clearUser();
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-40 flex items-center justify-between px-4">
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-lg hover:bg-gray-100"
        >
          {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
        <h1 className="text-xl font-bold text-emerald-600">EventFlow</h1>
        <button className="p-2 rounded-lg hover:bg-gray-100 relative">
          <Bell size={20} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>
      </header>

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-white border-r border-gray-200 z-50 transform transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Sidebar Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-emerald-600">EventFlow</h1>
          <button onClick={toggleSidebar} className="lg:hidden p-2 rounded-lg hover:bg-gray-100">
            <X size={20} />
          </button>
        </div>

        {/* User Info */}
        {user && (
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
                <span className="text-emerald-600 font-semibold">
                  {user.name?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user.name}</p>
                <p className="text-xs text-gray-600 truncate">{user.phone}</p>
              </div>
            </div>
            {wallet && (
              <div className="flex items-center justify-between p-2 bg-emerald-50 rounded-lg">
                <span className="text-xs text-gray-600">Balance</span>
                <span className="text-sm font-semibold text-emerald-600">
                  {formatCurrency(wallet.balance, wallet.currency)}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => window.innerWidth < 1024 && toggleSidebar()}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-emerald-50 text-emerald-600 font-medium'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Icon size={20} />
                <span>{item.name}</span>
              </Link>
            );
          })}

          {/* Admin Link */}
          <div className="border-t border-gray-200 my-4 pt-4">
            <Link
              to="/admin/organizations"
              onClick={() => window.innerWidth < 1024 && toggleSidebar()}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <Building2 size={20} />
              <span>Admin</span>
            </Link>
          </div>
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut size={20} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={toggleSidebar}
        ></div>
      )}

      {/* Main Content */}
      <main className="lg:ml-64 pt-16 lg:pt-0 min-h-screen flex flex-col">
        <div className="max-w-7xl mx-auto p-4 lg:p-6 flex-1">
          {children}
        </div>

        {/* Global footer */}
        <footer className="border-t border-gray-200 bg-white">
          <div className="max-w-7xl mx-auto px-4 py-3 text-right text-xs text-gray-500">
            Powered by{' '}
            <a
              href="https://ailabsafrica.com"
              target="_blank"
              rel="noreferrer"
              className="text-emerald-600 hover:text-emerald-500 underline underline-offset-2"
            >
              AI Labs
            </a>
          </div>
        </footer>
      </main>
    </div>
  );
};
