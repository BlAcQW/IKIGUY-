import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ProtectedRoute from '@/components/ProtectedRoute';
import { AuthProvider } from '@/contexts/AuthContext';
import { UserRole } from '@/lib/roles';

// Mock react-router-dom hooks
const mockLocation = { pathname: '/protected' };

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useLocation: () => mockLocation,
  };
});

// Mock the roles module
vi.mock('@/lib/roles', () => ({
  UserRole: {
    ADMIN: 'admin',
    USER: 'user',
    DEMO: 'demo',
    GUEST: 'guest',
  },
  canAccessRoute: vi.fn(),
}));

const TestComponent = () => <div>Protected Content</div>;

const renderProtectedRoute = (
  props: any = {},
  user: any = null,
  loading: boolean = false
) => {
  // Mock the useAuth hook
  vi.mock('@/contexts/AuthContext', () => ({
    useAuth: () => ({
      user,
      loading,
    }),
  }));

  return render(
    <BrowserRouter>
      <AuthProvider>
        <ProtectedRoute {...props}>
          <TestComponent />
        </ProtectedRoute>
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.pathname = '/protected';
  });

  describe('Loading State', () => {
    it('shows loading spinner when authentication is loading', () => {
      renderProtectedRoute({}, null, true);
      
      expect(screen.getByRole('status')).toBeInTheDocument();
      expect(screen.getByRole('status')).toHaveClass('animate-spin');
    });

    it('does not render protected content while loading', () => {
      renderProtectedRoute({}, null, true);
      
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Authentication Check', () => {
    it('redirects to auth page when user is not authenticated', () => {
      renderProtectedRoute({}, null, false);
      
      // Should redirect to /auth with location state
      expect(window.location.pathname).toBe('/auth');
    });

    it('renders protected content when user is authenticated', () => {
      const mockUser = { id: '1', email: 'test@example.com' };
      renderProtectedRoute({}, mockUser, false);
      
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  describe('Route Access Control', () => {
    it('shows access denied when user cannot access route', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      // Mock canAccessRoute to return false
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(false);
      
      renderProtectedRoute({}, mockUser, false);
      
      expect(screen.getByText('Access Denied')).toBeInTheDocument();
      expect(screen.getByText("You don't have permission to access this page")).toBeInTheDocument();
    });

    it('renders protected content when user can access route', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      // Mock canAccessRoute to return true
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(true);
      
      renderProtectedRoute({}, mockUser, false);
      
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('handles user without role metadata gracefully', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com'
        // No user_metadata.role
      };
      
      // Mock canAccessRoute to return true
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(true);
      
      renderProtectedRoute({}, mockUser, false);
      
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  describe('Role-Based Access Control', () => {
    it('shows role required message when user lacks required role', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      // Mock canAccessRoute to return true for route access
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(true);
      
      renderProtectedRoute({ requiredRole: UserRole.ADMIN }, mockUser, false);
      
      expect(screen.getByText('Role Required')).toBeInTheDocument();
      expect(screen.getByText('This page requires the admin role')).toBeInTheDocument();
      expect(screen.getByText('Your current role: user')).toBeInTheDocument();
      expect(screen.getByText('Required role: admin')).toBeInTheDocument();
    });

    it('renders protected content when user has required role', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.ADMIN }
      };
      
      // Mock canAccessRoute to return true
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(true);
      
      renderProtectedRoute({ requiredRole: UserRole.ADMIN }, mockUser, false);
      
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('renders fallback when user lacks required role and fallback is provided', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      const fallback = <div>Fallback Content</div>;
      
      // Mock canAccessRoute to return true for route access
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(true);
      
      renderProtectedRoute({ 
        requiredRole: UserRole.ADMIN, 
        fallback 
      }, mockUser, false);
      
      expect(screen.getByText('Fallback Content')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Permission-Based Access Control', () => {
    it('shows permission required message when user lacks required permission', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      // Mock canAccessRoute to return false for permission check
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(false);
      
      renderProtectedRoute({ 
        requiredPermission: { resource: 'users', action: 'delete' }
      }, mockUser, false);
      
      expect(screen.getByText('Permission Required')).toBeInTheDocument();
      expect(screen.getByText('You need permission to delete users')).toBeInTheDocument();
    });

    it('renders protected content when user has required permission', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.ADMIN }
      };
      
      // Mock canAccessRoute to return true
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(true);
      
      renderProtectedRoute({ 
        requiredPermission: { resource: 'users', action: 'delete' }
      }, mockUser, false);
      
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('renders fallback when user lacks required permission and fallback is provided', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      const fallback = <div>Permission Fallback</div>;
      
      // Mock canAccessRoute to return false for permission check
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(false);
      
      renderProtectedRoute({ 
        requiredPermission: { resource: 'users', action: 'delete' },
        fallback
      }, mockUser, false);
      
      expect(screen.getByText('Permission Fallback')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Navigation Buttons', () => {
    it('shows dashboard and home buttons in access denied page', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      // Mock canAccessRoute to return false
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(false);
      
      renderProtectedRoute({}, mockUser, false);
      
      expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Go Home')).toBeInTheDocument();
    });

    it('shows dashboard button in role required page', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      // Mock canAccessRoute to return true for route access
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(true);
      
      renderProtectedRoute({ requiredRole: UserRole.ADMIN }, mockUser, false);
      
      expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();
    });

    it('shows dashboard button in permission required page', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      // Mock canAccessRoute to return false for permission check
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(false);
      
      renderProtectedRoute({ 
        requiredPermission: { resource: 'users', action: 'delete' }
      }, mockUser, false);
      
      expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles missing user metadata gracefully', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com'
        // No user_metadata
      };
      
      // Mock canAccessRoute to return true
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(true);
      
      renderProtectedRoute({}, mockUser, false);
      
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('handles null user metadata gracefully', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: null
      };
      
      // Mock canAccessRoute to return true
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(true);
      
      renderProtectedRoute({}, mockUser, false);
      
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper loading spinner accessibility', () => {
      renderProtectedRoute({}, null, true);
      
      const spinner = screen.getByRole('status');
      expect(spinner).toBeInTheDocument();
    });

    it('has proper heading structure in error pages', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      // Mock canAccessRoute to return false
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(false);
      
      renderProtectedRoute({}, mockUser, false);
      
      expect(screen.getByRole('heading', { name: 'Access Denied' })).toBeInTheDocument();
    });

    it('has proper button roles and labels', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      // Mock canAccessRoute to return false
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(false);
      
      renderProtectedRoute({}, mockUser, false);
      
      expect(screen.getByRole('button', { name: 'Go to Dashboard' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Go Home' })).toBeInTheDocument();
    });
  });

  describe('Styling and Layout', () => {
    it('has proper loading container styling', () => {
      renderProtectedRoute({}, null, true);
      
      const container = screen.getByRole('status').parentElement;
      expect(container).toHaveClass('min-h-screen', 'flex', 'items-center', 'justify-center');
    });

    it('has proper error page container styling', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      // Mock canAccessRoute to return false
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(false);
      
      renderProtectedRoute({}, mockUser, false);
      
      const container = screen.getByText('Access Denied').closest('div');
      expect(container).toHaveClass('min-h-screen', 'flex', 'items-center', 'justify-center');
    });

    it('has proper card styling in error pages', () => {
      const mockUser = { 
        id: '1', 
        email: 'test@example.com',
        user_metadata: { role: UserRole.USER }
      };
      
      // Mock canAccessRoute to return false
      const { canAccessRoute } = require('@/lib/roles');
      canAccessRoute.mockReturnValue(false);
      
      renderProtectedRoute({}, mockUser, false);
      
      const card = screen.getByText('Access Denied').closest('[class*="card"]');
      expect(card).toHaveClass('w-full', 'max-w-md');
    });
  });
});
