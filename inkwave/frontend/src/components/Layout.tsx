/**
 * Main Layout Component
 * Header + Content + Bottom Nav (mobile) + PWA Install Prompt
 */

import { Outlet } from 'react-router-dom';
import Header from './Header';
import MobileBottomNav from './MobileBottomNav';
import PWAInstallPrompt from './PWAInstallPrompt';

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <Header />

      {/* Main content with bottom padding for mobile nav */}
      <main className="min-h-[calc(100vh-64px)] pb-20 md:pb-0">
        <Outlet />
      </main>

      {/* Global footer */}
      <footer className="hidden md:block border-t border-gray-800 bg-gray-950/80 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-4 py-3 text-right text-xs text-gray-500">
          Powered by{' '}
          <a
            href="https://ailabsafrica.com"
            target="_blank"
            rel="noreferrer"
            className="text-purple-400 hover:text-purple-300 underline underline-offset-2"
          >
            AI Labs
          </a>
        </div>
      </footer>

      {/* Mobile bottom navigation */}
      <MobileBottomNav />

      {/* PWA install prompt */}
      <PWAInstallPrompt />
    </div>
  );
}
