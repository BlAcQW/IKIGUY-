/**
 * Navigation Configuration
 *
 * Single source of truth for all navigation items and active state logic.
 * This ensures consistent navigation behavior across all components.
 */

import { Home, Library, Users, Trophy, Search, Grid, Activity, User, Wallet } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

/**
 * Navigation item definition
 */
export interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
  /** Optional: paths that should also trigger this nav item as active */
  matchPaths?: string[];
}

/**
 * Main navigation items for regular users (bottom nav + header)
 * These are the primary navigation destinations
 */
export const MAIN_NAV_ITEMS: NavItem[] = [
  { path: '/', label: 'Home', icon: Home },
  {
    path: '/library',
    label: 'My Library',
    icon: Library,
    // Book-related routes should highlight Library since user is engaging with library content
    matchPaths: ['/book', '/player', '/audiobook']
  },
  { path: '/discover', label: 'Discover', icon: Users, matchPaths: ['/user'] },
  { path: '/wallet', label: 'Plans & Pricing', icon: Wallet },
  { path: '/leaderboard', label: 'Leaderboard', icon: Trophy },
];

/**
 * Extended navigation items for admin users (header only)
 * Includes all main nav items plus admin-specific items
 */
export const ADMIN_NAV_ITEMS: NavItem[] = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/browse', label: 'Browse', icon: Search },
  {
    path: '/library',
    label: 'My Library',
    icon: Library,
    matchPaths: ['/book', '/player', '/audiobook']
  },
  { path: '/all-books', label: 'All Books', icon: Grid },
  { path: '/discover', label: 'Discover', icon: Users, matchPaths: ['/user'] },
  { path: '/wallet', label: 'Plans & Pricing', icon: Wallet },
  { path: '/leaderboard', label: 'Leaderboard', icon: Trophy },
  { path: '/feed', label: 'Feed', icon: Activity },
];

/**
 * Mobile bottom navigation items
 * Subset of main navigation optimized for mobile experience
 */
export const MOBILE_NAV_ITEMS: NavItem[] = [
  { path: '/', label: 'Home', icon: Home },
  {
    path: '/library',
    label: 'Library',
    icon: Library,
    matchPaths: ['/book', '/player', '/audiobook']
  },
  { path: '/discover', label: 'Discover', icon: Users, matchPaths: ['/user'] },
  { path: '/leaderboard', label: 'Leaders', icon: Trophy },
  { path: '/profile', label: 'Profile', icon: User },
];

/**
 * Paths where bottom navigation should be hidden
 */
export const HIDDEN_NAV_PATHS = ['/login', '/signup', '/player', '/audiobook', '/auth'];

/**
 * Determines if a navigation item should be marked as active
 * based on the current pathname.
 *
 * Supports:
 * - Exact path matching (e.g., "/" matches only "/")
 * - Prefix matching for nested routes (e.g., "/discover" matches "/discover/something")
 * - Custom match paths for related routes (e.g., "/user/*" activates "Discover")
 *
 * @param navItem - The navigation item to check
 * @param currentPath - The current location pathname
 * @returns boolean - Whether the nav item should be active
 */
export function isNavItemActive(navItem: NavItem, currentPath: string): boolean {
  // Exact match for root path
  if (navItem.path === '/') {
    return currentPath === '/';
  }

  // Exact match
  if (currentPath === navItem.path) {
    return true;
  }

  // Prefix match for nested routes (e.g., /discover/123)
  if (currentPath.startsWith(navItem.path + '/')) {
    return true;
  }

  // Check custom match paths
  if (navItem.matchPaths) {
    for (const matchPath of navItem.matchPaths) {
      if (currentPath === matchPath || currentPath.startsWith(matchPath + '/')) {
        return true;
      }
    }
  }

  return false;
}

/**
 * Checks if bottom navigation should be hidden for the current path
 *
 * @param currentPath - The current location pathname
 * @returns boolean - Whether navigation should be hidden
 */
export function shouldHideNavigation(currentPath: string): boolean {
  return HIDDEN_NAV_PATHS.some(path => currentPath.startsWith(path));
}
