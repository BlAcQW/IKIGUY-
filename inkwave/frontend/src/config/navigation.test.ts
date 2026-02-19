/**
 * Navigation Configuration Tests
 *
 * Tests for navigation item configuration and active state logic.
 * Ensures consistent navigation behavior across all routes.
 */

import { describe, it, expect } from 'vitest';
import {
  MAIN_NAV_ITEMS,
  ADMIN_NAV_ITEMS,
  MOBILE_NAV_ITEMS,
  HIDDEN_NAV_PATHS,
  isNavItemActive,
  shouldHideNavigation,
  type NavItem,
} from './navigation';

describe('Navigation Configuration', () => {
  describe('Nav Item Arrays', () => {
    it('should have defined main nav items', () => {
      expect(MAIN_NAV_ITEMS).toBeDefined();
      expect(MAIN_NAV_ITEMS.length).toBeGreaterThan(0);
    });

    it('should have defined admin nav items', () => {
      expect(ADMIN_NAV_ITEMS).toBeDefined();
      expect(ADMIN_NAV_ITEMS.length).toBeGreaterThan(0);
    });

    it('should have defined mobile nav items', () => {
      expect(MOBILE_NAV_ITEMS).toBeDefined();
      expect(MOBILE_NAV_ITEMS.length).toBeGreaterThan(0);
    });

    it('should have admin nav items include all main nav items paths', () => {
      const mainPaths = MAIN_NAV_ITEMS.map((item) => item.path);
      const adminPaths = ADMIN_NAV_ITEMS.map((item) => item.path);

      mainPaths.forEach((path) => {
        expect(adminPaths).toContain(path);
      });
    });

    it('should have valid nav item structure', () => {
      const allItems = [...MAIN_NAV_ITEMS, ...ADMIN_NAV_ITEMS, ...MOBILE_NAV_ITEMS];

      allItems.forEach((item) => {
        expect(item.path).toBeDefined();
        expect(item.path.startsWith('/')).toBe(true);
        expect(item.label).toBeDefined();
        expect(item.label.length).toBeGreaterThan(0);
        expect(item.icon).toBeDefined();
      });
    });
  });

  describe('isNavItemActive', () => {
    describe('Exact Path Matching', () => {
      it('should return true for exact path match', () => {
        const navItem: NavItem = { path: '/library', label: 'Library', icon: {} as any };
        expect(isNavItemActive(navItem, '/library')).toBe(true);
      });

      it('should return false for non-matching path', () => {
        const navItem: NavItem = { path: '/library', label: 'Library', icon: {} as any };
        expect(isNavItemActive(navItem, '/discover')).toBe(false);
      });
    });

    describe('Root Path Matching', () => {
      it('should return true for root path when on root', () => {
        const navItem: NavItem = { path: '/', label: 'Home', icon: {} as any };
        expect(isNavItemActive(navItem, '/')).toBe(true);
      });

      it('should return false for root path when on nested route', () => {
        const navItem: NavItem = { path: '/', label: 'Home', icon: {} as any };
        expect(isNavItemActive(navItem, '/library')).toBe(false);
      });

      it('should return false for root path when on deep nested route', () => {
        const navItem: NavItem = { path: '/', label: 'Home', icon: {} as any };
        expect(isNavItemActive(navItem, '/book/123')).toBe(false);
      });
    });

    describe('Prefix Matching for Nested Routes', () => {
      it('should return true for nested route under nav path', () => {
        const navItem: NavItem = { path: '/discover', label: 'Discover', icon: {} as any };
        expect(isNavItemActive(navItem, '/discover/recommended')).toBe(true);
      });

      it('should return true for deeply nested route under nav path', () => {
        const navItem: NavItem = { path: '/library', label: 'Library', icon: {} as any };
        expect(isNavItemActive(navItem, '/library/books/123')).toBe(true);
      });

      it('should return false when path is a partial match but not nested', () => {
        const navItem: NavItem = { path: '/lib', label: 'Lib', icon: {} as any };
        expect(isNavItemActive(navItem, '/library')).toBe(false);
      });
    });

    describe('Custom Match Paths', () => {
      it('should return true for exact custom match path', () => {
        const navItem: NavItem = {
          path: '/discover',
          label: 'Discover',
          icon: {} as any,
          matchPaths: ['/user'],
        };
        expect(isNavItemActive(navItem, '/user')).toBe(true);
      });

      it('should return true for nested custom match path', () => {
        const navItem: NavItem = {
          path: '/discover',
          label: 'Discover',
          icon: {} as any,
          matchPaths: ['/user'],
        };
        expect(isNavItemActive(navItem, '/user/123')).toBe(true);
      });

      it('should return true for multiple custom match paths', () => {
        const navItem: NavItem = {
          path: '/discover',
          label: 'Discover',
          icon: {} as any,
          matchPaths: ['/user', '/followers', '/following'],
        };
        expect(isNavItemActive(navItem, '/user/456')).toBe(true);
        expect(isNavItemActive(navItem, '/followers')).toBe(true);
        expect(isNavItemActive(navItem, '/following/789')).toBe(true);
      });
    });

    describe('Real Navigation Scenarios', () => {
      it('should correctly identify Home as active', () => {
        const homeItem = MAIN_NAV_ITEMS.find((item) => item.path === '/');
        expect(homeItem).toBeDefined();
        expect(isNavItemActive(homeItem!, '/')).toBe(true);
        expect(isNavItemActive(homeItem!, '/library')).toBe(false);
      });

      it('should correctly identify Library as active', () => {
        const libraryItem = MAIN_NAV_ITEMS.find((item) => item.path === '/library');
        expect(libraryItem).toBeDefined();
        expect(isNavItemActive(libraryItem!, '/library')).toBe(true);
        expect(isNavItemActive(libraryItem!, '/')).toBe(false);
      });

      it('should correctly identify Discover as active on user profiles', () => {
        const discoverItem = MAIN_NAV_ITEMS.find((item) => item.path === '/discover');
        expect(discoverItem).toBeDefined();
        expect(isNavItemActive(discoverItem!, '/discover')).toBe(true);
        expect(isNavItemActive(discoverItem!, '/user/123')).toBe(true);
      });

      it('should correctly identify Leaderboard as active', () => {
        const leaderboardItem = MAIN_NAV_ITEMS.find((item) => item.path === '/leaderboard');
        expect(leaderboardItem).toBeDefined();
        expect(isNavItemActive(leaderboardItem!, '/leaderboard')).toBe(true);
        expect(isNavItemActive(leaderboardItem!, '/')).toBe(false);
      });

      it('should highlight Library on player page (reading library content)', () => {
        const libraryItem = MAIN_NAV_ITEMS.find((item) => item.path === '/library');
        expect(libraryItem).toBeDefined();
        expect(isNavItemActive(libraryItem!, '/player/book-123')).toBe(true);

        // Other nav items should NOT be active
        const otherItems = MAIN_NAV_ITEMS.filter((item) => item.path !== '/library');
        otherItems.forEach((item) => {
          expect(isNavItemActive(item, '/player/book-123')).toBe(false);
        });
      });

      it('should highlight Library on book detail page (engaging with library content)', () => {
        const libraryItem = MAIN_NAV_ITEMS.find((item) => item.path === '/library');
        expect(libraryItem).toBeDefined();
        expect(isNavItemActive(libraryItem!, '/book/abc-123')).toBe(true);

        // Other nav items should NOT be active
        const otherItems = MAIN_NAV_ITEMS.filter((item) => item.path !== '/library');
        otherItems.forEach((item) => {
          expect(isNavItemActive(item, '/book/abc-123')).toBe(false);
        });
      });

      it('should highlight Library on audiobook page', () => {
        const libraryItem = MAIN_NAV_ITEMS.find((item) => item.path === '/library');
        expect(libraryItem).toBeDefined();
        expect(isNavItemActive(libraryItem!, '/audiobook/book-456')).toBe(true);
      });
    });
  });

  describe('shouldHideNavigation', () => {
    it('should hide navigation on login page', () => {
      expect(shouldHideNavigation('/login')).toBe(true);
    });

    it('should hide navigation on signup page', () => {
      expect(shouldHideNavigation('/signup')).toBe(true);
    });

    it('should hide navigation on player page', () => {
      expect(shouldHideNavigation('/player/book-123')).toBe(true);
    });

    it('should hide navigation on audiobook page', () => {
      expect(shouldHideNavigation('/audiobook/book-456')).toBe(true);
    });

    it('should hide navigation on auth callback', () => {
      expect(shouldHideNavigation('/auth/callback')).toBe(true);
    });

    it('should show navigation on home page', () => {
      expect(shouldHideNavigation('/')).toBe(false);
    });

    it('should show navigation on library page', () => {
      expect(shouldHideNavigation('/library')).toBe(false);
    });

    it('should show navigation on discover page', () => {
      expect(shouldHideNavigation('/discover')).toBe(false);
    });

    it('should show navigation on leaderboard page', () => {
      expect(shouldHideNavigation('/leaderboard')).toBe(false);
    });

    it('should show navigation on profile page', () => {
      expect(shouldHideNavigation('/profile')).toBe(false);
    });

    it('should show navigation on book detail page', () => {
      expect(shouldHideNavigation('/book/123')).toBe(false);
    });
  });

  describe('Hidden Nav Paths', () => {
    it('should have defined hidden paths', () => {
      expect(HIDDEN_NAV_PATHS).toBeDefined();
      expect(HIDDEN_NAV_PATHS.length).toBeGreaterThan(0);
    });

    it('should include player path', () => {
      expect(HIDDEN_NAV_PATHS).toContain('/player');
    });

    it('should include auth paths', () => {
      expect(HIDDEN_NAV_PATHS).toContain('/login');
      expect(HIDDEN_NAV_PATHS).toContain('/signup');
      expect(HIDDEN_NAV_PATHS).toContain('/auth');
    });
  });
});

describe('Edge Cases', () => {
  it('should handle empty path gracefully', () => {
    const navItem: NavItem = { path: '/library', label: 'Library', icon: {} as any };
    expect(isNavItemActive(navItem, '')).toBe(false);
  });

  it('should handle paths with trailing slashes', () => {
    const navItem: NavItem = { path: '/library', label: 'Library', icon: {} as any };
    // Note: React Router typically normalizes these, but we test the raw behavior
    expect(isNavItemActive(navItem, '/library/')).toBe(true);
  });

  it('should handle paths - query params are NOT in pathname', () => {
    const navItem: NavItem = { path: '/library', label: 'Library', icon: {} as any };
    // Note: In React Router, location.pathname doesn't include query params.
    // Query params are in location.search. So this test verifies the real behavior:
    // "/library" (pathname) should match, not "/library?tab=recent"
    expect(isNavItemActive(navItem, '/library')).toBe(true);
    // If somehow query params were included, it would fail (as expected)
    expect(isNavItemActive(navItem, '/library?tab=recent')).toBe(false);
  });
});
