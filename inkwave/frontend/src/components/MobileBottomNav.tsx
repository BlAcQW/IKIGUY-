/**
 * Mobile Bottom Navigation
 *
 * Fixed bottom navigation bar for mobile devices.
 * Uses centralized navigation config for consistent active state.
 */

import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { MOBILE_NAV_ITEMS, isNavItemActive, shouldHideNavigation } from '../config/navigation';

export default function MobileBottomNav() {
  const location = useLocation();

  // Hide navigation on certain pages (player, login, signup, etc.)
  if (shouldHideNavigation(location.pathname)) {
    return null;
  }

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 md:hidden bg-gray-900/95 backdrop-blur-lg border-t border-gray-800 pb-safe">
      <div className="flex items-center justify-around h-16">
        {MOBILE_NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = isNavItemActive(item, location.pathname);

          return (
            <Link
              key={item.path}
              to={item.path}
              className="flex flex-col items-center justify-center flex-1 h-full touch-feedback no-zoom relative"
            >
              {isActive && (
                <motion.div
                  layoutId="bottomNavIndicator"
                  className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-b-full"
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              )}
              <Icon
                className={`w-5 h-5 transition-colors ${
                  isActive ? 'text-purple-400' : 'text-gray-500'
                }`}
              />
              <span
                className={`text-[10px] mt-1 transition-colors ${
                  isActive ? 'text-purple-400 font-medium' : 'text-gray-500'
                }`}
              >
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
