import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import Navigation from '@/components/Navigation';
import { AuthProvider } from '@/contexts/AuthContext';

// Mock the ImageOptimizer component
vi.mock('@/components/ImageOptimizer', () => ({
  ImageOptimizer: ({ alt, ...props }: any) => <img alt={alt} {...props} />
}));

// Mock react-router-dom hooks
const mockNavigate = vi.fn();
const mockLocation = { pathname: '/' };

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockLocation,
  };
});

const renderNavigation = (user: any = null) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Navigation />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.pathname = '/';
  });

  describe('Logo and Brand', () => {
    it('renders the AI Labs Africa logo and brand name', () => {
      renderNavigation();
      
      expect(screen.getByAltText('AI Labs Africa logo')).toBeInTheDocument();
      expect(screen.getByText('AI Labs Africa')).toBeInTheDocument();
    });

    it('logo links to home page', () => {
      renderNavigation();
      
      const logoLink = screen.getByAltText('AI Labs Africa logo').closest('a');
      expect(logoLink).toHaveAttribute('href', '/');
    });
  });

  describe('Navigation Links', () => {
    it('renders all navigation links', () => {
      renderNavigation();
      
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Demos')).toBeInTheDocument();
      expect(screen.getByText('Contact')).toBeInTheDocument();
      expect(screen.getByText('Schedule Demo')).toBeInTheDocument();
      expect(screen.getByText('Create Assistant')).toBeInTheDocument();
    });

    it('all navigation links have correct href attributes', () => {
      renderNavigation();
      
      expect(screen.getByText('Home').closest('a')).toHaveAttribute('href', '/');
      expect(screen.getByText('Demos').closest('a')).toHaveAttribute('href', '/demos');
      expect(screen.getByText('Contact').closest('a')).toHaveAttribute('href', '/contact');
      expect(screen.getByText('Schedule Demo').closest('a')).toHaveAttribute('href', '/schedule-demo');
      expect(screen.getByText('Create Assistant').closest('a')).toHaveAttribute('href', '/create-assistant');
    });

    it('highlights active link when on home page', () => {
      mockLocation.pathname = '/';
      renderNavigation();
      
      const homeLink = screen.getByText('Home').closest('a');
      expect(homeLink).toHaveClass('text-primary');
    });

    it('highlights active link when on demos page', () => {
      mockLocation.pathname = '/demos';
      renderNavigation();
      
      const demosLink = screen.getByText('Demos').closest('a');
      expect(demosLink).toHaveClass('text-primary');
    });

    it('highlights active link when on contact page', () => {
      mockLocation.pathname = '/contact';
      renderNavigation();
      
      const contactLink = screen.getByText('Contact').closest('a');
      expect(contactLink).toHaveClass('text-primary');
    });

    it('highlights active link when on schedule demo page', () => {
      mockLocation.pathname = '/schedule-demo';
      renderNavigation();
      
      const scheduleDemoLink = screen.getByText('Schedule Demo').closest('a');
      expect(scheduleDemoLink).toHaveClass('text-primary');
    });

    it('highlights active link when on create assistant page', () => {
      mockLocation.pathname = '/create-assistant';
      renderNavigation();
      
      const createAssistantLink = screen.getByText('Create Assistant').closest('a');
      expect(createAssistantLink).toHaveClass('text-primary');
    });

    it('applies correct styling to inactive links', () => {
      mockLocation.pathname = '/';
      renderNavigation();
      
      const demosLink = screen.getByText('Demos').closest('a');
      expect(demosLink).toHaveClass('text-muted-foreground');
    });
  });

  describe('Authentication States', () => {
    it('shows sign in button when user is not authenticated', () => {
      renderNavigation();
      
      expect(screen.getByText('Sign In')).toBeInTheDocument();
      expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    });

    it('sign in button links to auth page', () => {
      renderNavigation();
      
      const signInButton = screen.getByText('Sign In').closest('a');
      expect(signInButton).toHaveAttribute('href', '/auth');
    });

    it('shows user dropdown when user is authenticated', () => {
      // Mock authenticated user
      const mockUser = { email: 'test@example.com' };
      
      // Mock the useAuth hook
      vi.mock('@/contexts/AuthContext', () => ({
        useAuth: () => ({
          user: mockUser,
          signOut: vi.fn(),
        }),
      }));

      renderNavigation();
      
      expect(screen.getByText('test')).toBeInTheDocument(); // Username from email
    });

    it('displays username from email address', () => {
      // Mock authenticated user
      const mockUser = { email: 'john.doe@example.com' };
      
      // Mock the useAuth hook
      vi.mock('@/contexts/AuthContext', () => ({
        useAuth: () => ({
          user: mockUser,
          signOut: vi.fn(),
        }),
      }));

      renderNavigation();
      
      expect(screen.getByText('john.doe')).toBeInTheDocument();
    });

    it('handles user without email gracefully', () => {
      // Mock authenticated user without email
      const mockUser = { email: null };
      
      // Mock the useAuth hook
      vi.mock('@/contexts/AuthContext', () => ({
        useAuth: () => ({
          user: mockUser,
          signOut: vi.fn(),
        }),
      }));

      renderNavigation();
      
      // Should not crash and should show empty username
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  });

  describe('User Dropdown Menu', () => {
    it('opens dropdown menu when user button is clicked', async () => {
      // Mock authenticated user
      const mockUser = { email: 'test@example.com' };
      const mockSignOut = vi.fn();
      
      // Mock the useAuth hook
      vi.mock('@/contexts/AuthContext', () => ({
        useAuth: () => ({
          user: mockUser,
          signOut: mockSignOut,
        }),
      }));

      renderNavigation();
      
      const userButton = screen.getByRole('button');
      fireEvent.click(userButton);
      
      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Sign Out')).toBeInTheDocument();
      });
    });

    it('navigates to dashboard when dashboard option is clicked', async () => {
      // Mock authenticated user
      const mockUser = { email: 'test@example.com' };
      const mockSignOut = vi.fn();
      
      // Mock the useAuth hook
      vi.mock('@/contexts/AuthContext', () => ({
        useAuth: () => ({
          user: mockUser,
          signOut: mockSignOut,
        }),
      }));

      renderNavigation();
      
      const userButton = screen.getByRole('button');
      fireEvent.click(userButton);
      
      await waitFor(() => {
        const dashboardOption = screen.getByText('Dashboard');
        fireEvent.click(dashboardOption);
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('calls signOut and navigates to home when sign out is clicked', async () => {
      // Mock authenticated user
      const mockUser = { email: 'test@example.com' };
      const mockSignOut = vi.fn().mockResolvedValue(undefined);
      
      // Mock the useAuth hook
      vi.mock('@/contexts/AuthContext', () => ({
        useAuth: () => ({
          user: mockUser,
          signOut: mockSignOut,
        }),
      }));

      renderNavigation();
      
      const userButton = screen.getByRole('button');
      fireEvent.click(userButton);
      
      await waitFor(() => {
        const signOutOption = screen.getByText('Sign Out');
        fireEvent.click(signOutOption);
      });
      
      await waitFor(() => {
        expect(mockSignOut).toHaveBeenCalled();
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });
  });

  describe('Responsive Design', () => {
    it('has proper navigation container styling', () => {
      renderNavigation();
      
      const nav = screen.getByRole('navigation');
      expect(nav).toHaveClass('bg-background/95', 'backdrop-blur', 'sticky', 'top-0', 'z-50');
    });

    it('has proper logo container styling', () => {
      renderNavigation();
      
      const logoLink = screen.getByAltText('AI Labs Africa logo').closest('a');
      expect(logoLink).toHaveClass('flex', 'items-center', 'space-x-2');
    });

    it('has proper navigation links container styling', () => {
      renderNavigation();
      
      const linksContainer = screen.getByText('Home').closest('div');
      expect(linksContainer).toHaveClass('flex', 'items-center', 'space-x-6');
    });
  });

  describe('Error Handling', () => {
    it('handles signOut error gracefully', async () => {
      // Mock authenticated user
      const mockUser = { email: 'test@example.com' };
      const mockSignOut = vi.fn().mockRejectedValue(new Error('Sign out failed'));
      
      // Mock the useAuth hook
      vi.mock('@/contexts/AuthContext', () => ({
        useAuth: () => ({
          user: mockUser,
          signOut: mockSignOut,
        }),
      }));

      renderNavigation();
      
      const userButton = screen.getByRole('button');
      fireEvent.click(userButton);
      
      await waitFor(() => {
        const signOutOption = screen.getByText('Sign Out');
        fireEvent.click(signOutOption);
      });
      
      await waitFor(() => {
        expect(mockSignOut).toHaveBeenCalled();
        // Should still navigate even if signOut fails
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper navigation role', () => {
      renderNavigation();
      
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('has proper button roles for interactive elements', () => {
      renderNavigation();
      
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('has proper alt text for logo image', () => {
      renderNavigation();
      
      expect(screen.getByAltText('AI Labs Africa logo')).toBeInTheDocument();
    });

    it('has proper link text for screen readers', () => {
      renderNavigation();
      
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Demos')).toBeInTheDocument();
      expect(screen.getByText('Contact')).toBeInTheDocument();
    });
  });
});
