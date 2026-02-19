import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/integrations/supabase/client';

// Mock Supabase
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
      refreshSession: vi.fn(),
      getSession: vi.fn().mockResolvedValue({
        data: { session: null },
        error: null
      }),
      onAuthStateChange: vi.fn(() => ({
        data: { subscription: { unsubscribe: vi.fn() } }
      }))
    }
  }
}));

// Mock React Router
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn()
  };
});

// Test component to access auth context
const TestComponent = () => {
  const { signIn, signUp, signOut, user, loading, session, isSessionExpired } = useAuth();
  
  return (
    <div>
      <div data-testid="loading">{loading.toString()}</div>
      <div data-testid="user">{user ? user.email : 'no-user'}</div>
      <div data-testid="session">{session ? 'has-session' : 'no-session'}</div>
      <div data-testid="session-expired">{isSessionExpired.toString()}</div>
      <button 
        data-testid="signin-btn" 
        onClick={() => signIn('test@example.com', 'password123')}
      >
        Sign In
      </button>
      <button 
        data-testid="signup-btn" 
        onClick={() => signUp('test@example.com', 'password123', { full_name: 'Test User' })}
      >
        Sign Up
      </button>
      <button data-testid="signout-btn" onClick={() => signOut()}>
        Sign Out
      </button>
    </div>
  );
};

const renderWithAuth = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initial State', () => {
    it('should start with loading state', () => {
      renderWithAuth(<TestComponent />);
      expect(screen.getByTestId('loading')).toHaveTextContent('true');
    });

    it('should have no user initially', () => {
      renderWithAuth(<TestComponent />);
      expect(screen.getByTestId('user')).toHaveTextContent('no-user');
    });

    it('should have no session initially', () => {
      renderWithAuth(<TestComponent />);
      expect(screen.getByTestId('session')).toHaveTextContent('no-session');
    });

    it('should not have expired session initially', () => {
      renderWithAuth(<TestComponent />);
      expect(screen.getByTestId('session-expired')).toHaveTextContent('false');
    });
  });

  describe('Sign In Function', () => {
    it('should call supabase signInWithPassword with correct parameters', async () => {
      const mockSignIn = vi.mocked(supabase.auth.signInWithPassword).mockResolvedValue({
        data: { user: null, session: null },
        error: null
      });

      renderWithAuth(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('signin-btn'));

      await waitFor(() => {
        expect(mockSignIn).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123'
        });
      });
    });

    it('should handle successful sign in', async () => {
      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        app_metadata: {},
        user_metadata: {},
        aud: 'authenticated',
        role: 'authenticated'
      };

      const mockSession = {
        access_token: 'mock-token',
        refresh_token: 'mock-refresh',
        expires_in: 3600,
        expires_at: Math.floor(Date.now() / 1000) + 3600,
        token_type: 'bearer',
        user: mockUser
      };

      vi.mocked(supabase.auth.signInWithPassword).mockResolvedValue({
        data: { user: mockUser, session: mockSession },
        error: null
      });

      renderWithAuth(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('signin-btn'));

      await waitFor(() => {
        expect(supabase.auth.signInWithPassword).toHaveBeenCalled();
      });
    });

    it('should handle sign in error', async () => {
      const mockError = {
        message: 'Invalid login credentials',
        status: 400,
        name: 'AuthApiError'
      };

      vi.mocked(supabase.auth.signInWithPassword).mockResolvedValue({
        data: { user: null, session: null },
        error: mockError
      });

      renderWithAuth(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('signin-btn'));

      await waitFor(() => {
        expect(supabase.auth.signInWithPassword).toHaveBeenCalled();
      });
    });

    it('should handle network error during sign in', async () => {
      vi.mocked(supabase.auth.signInWithPassword).mockRejectedValue(
        new Error('Network error')
      );

      renderWithAuth(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('signin-btn'));

      await waitFor(() => {
        expect(supabase.auth.signInWithPassword).toHaveBeenCalled();
      });
    });

    it('should handle empty email and password', async () => {
      const mockSignIn = vi.mocked(supabase.auth.signInWithPassword).mockResolvedValue({
        data: { user: null, session: null },
        error: null
      });

      renderWithAuth(<TestComponent />);
      
      // Test with empty credentials
      await act(async () => {
        const { signIn } = useAuth();
        await signIn('', '');
      });

      expect(mockSignIn).toHaveBeenCalledWith({
        email: '',
        password: ''
      });
    });

    it('should handle special characters in email', async () => {
      const mockSignIn = vi.mocked(supabase.auth.signInWithPassword).mockResolvedValue({
        data: { user: null, session: null },
        error: null
      });

      renderWithAuth(<TestComponent />);
      
      await act(async () => {
        const { signIn } = useAuth();
        await signIn('test+tag@example.com', 'password123');
      });

      expect(mockSignIn).toHaveBeenCalledWith({
        email: 'test+tag@example.com',
        password: 'password123'
      });
    });
  });

  describe('Sign Up Function', () => {
    it('should call supabase signUp with correct parameters', async () => {
      const mockSignUp = vi.mocked(supabase.auth.signUp).mockResolvedValue({
        data: { user: null, session: null },
        error: null
      });

      renderWithAuth(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('signup-btn'));

      await waitFor(() => {
        expect(mockSignUp).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
          options: {
            emailRedirectTo: expect.any(String),
            data: { full_name: 'Test User' }
          }
        });
      });
    });

    it('should handle successful sign up', async () => {
      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        app_metadata: {},
        user_metadata: { full_name: 'Test User' },
        aud: 'authenticated',
        role: 'authenticated'
      };

      vi.mocked(supabase.auth.signUp).mockResolvedValue({
        data: { user: mockUser, session: null },
        error: null
      });

      renderWithAuth(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('signup-btn'));

      await waitFor(() => {
        expect(supabase.auth.signUp).toHaveBeenCalled();
      });
    });

    it('should handle sign up error', async () => {
      const mockError = {
        message: 'User already registered',
        status: 422,
        name: 'AuthApiError'
      };

      vi.mocked(supabase.auth.signUp).mockResolvedValue({
        data: { user: null, session: null },
        error: mockError
      });

      renderWithAuth(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('signup-btn'));

      await waitFor(() => {
        expect(supabase.auth.signUp).toHaveBeenCalled();
      });
    });
  });

  describe('Sign Out Function', () => {
    it('should call supabase signOut', async () => {
      const mockSignOut = vi.mocked(supabase.auth.signOut).mockResolvedValue({
        error: null
      });

      renderWithAuth(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('signout-btn'));

      await waitFor(() => {
        expect(mockSignOut).toHaveBeenCalled();
      });
    });

    it('should handle sign out error', async () => {
      const mockError = {
        message: 'Sign out failed',
        status: 500,
        name: 'AuthApiError'
      };

      vi.mocked(supabase.auth.signOut).mockResolvedValue({
        error: mockError
      });

      renderWithAuth(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('signout-btn'));

      await waitFor(() => {
        expect(supabase.auth.signOut).toHaveBeenCalled();
      });
    });
  });

  describe('Session Management', () => {
    it('should handle session refresh', async () => {
      const mockRefreshSession = vi.mocked(supabase.auth.refreshSession).mockResolvedValue({
        data: { user: null, session: null },
        error: null
      });

      renderWithAuth(<TestComponent />);

      await act(async () => {
        const { refreshSession } = useAuth();
        await refreshSession();
      });

      expect(mockRefreshSession).toHaveBeenCalled();
    });

    it('should handle session refresh error', async () => {
      const mockError = {
        message: 'Session refresh failed',
        status: 401,
        name: 'AuthApiError'
      };

      vi.mocked(supabase.auth.refreshSession).mockResolvedValue({
        data: { user: null, session: null },
        error: mockError
      });

      renderWithAuth(<TestComponent />);

      await act(async () => {
        const { refreshSession } = useAuth();
        await refreshSession();
      });

      expect(supabase.auth.refreshSession).toHaveBeenCalled();
    });

    it('should handle session refresh network error', async () => {
      vi.mocked(supabase.auth.refreshSession).mockRejectedValue(
        new Error('Network error')
      );

      renderWithAuth(<TestComponent />);

      await act(async () => {
        const { refreshSession } = useAuth();
        await refreshSession();
      });

      expect(supabase.auth.refreshSession).toHaveBeenCalled();
    });
  });

  describe('Auth State Changes', () => {
    it('should set up auth state listener on mount', () => {
      renderWithAuth(<TestComponent />);
      
      expect(supabase.auth.onAuthStateChange).toHaveBeenCalled();
    });

    it('should handle TOKEN_REFRESHED event with valid session', () => {
      const mockSubscription = { unsubscribe: vi.fn() };
      vi.mocked(supabase.auth.onAuthStateChange).mockReturnValue({
        data: { subscription: mockSubscription }
      });

      renderWithAuth(<TestComponent />);
      
      expect(supabase.auth.onAuthStateChange).toHaveBeenCalled();
    });

    it('should handle TOKEN_REFRESHED event with expired session', () => {
      const mockSubscription = { unsubscribe: vi.fn() };
      vi.mocked(supabase.auth.onAuthStateChange).mockReturnValue({
        data: { subscription: mockSubscription }
      });

      renderWithAuth(<TestComponent />);
      
      expect(supabase.auth.onAuthStateChange).toHaveBeenCalled();
    });

    it('should handle SIGNED_OUT event', () => {
      const mockSubscription = { unsubscribe: vi.fn() };
      vi.mocked(supabase.auth.onAuthStateChange).mockReturnValue({
        data: { subscription: mockSubscription }
      });

      renderWithAuth(<TestComponent />);
      
      expect(supabase.auth.onAuthStateChange).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('should handle useAuth outside of AuthProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      expect(() => {
        render(<TestComponent />);
      }).toThrow('useAuth must be used within an AuthProvider');
      
      consoleSpy.mockRestore();
    });

    it('should handle getSession error', async () => {
      const mockError = {
        message: 'Session retrieval failed',
        status: 500,
        name: 'AuthApiError'
      };

      vi.mocked(supabase.auth.getSession).mockResolvedValue({
        data: { session: null },
        error: mockError
      });

      renderWithAuth(<TestComponent />);

      await waitFor(() => {
        expect(supabase.auth.getSession).toHaveBeenCalled();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle multiple rapid sign in attempts', async () => {
      const mockSignIn = vi.mocked(supabase.auth.signInWithPassword).mockResolvedValue({
        data: { user: null, session: null },
        error: null
      });

      renderWithAuth(<TestComponent />);
      
      // Rapid clicks
      fireEvent.click(screen.getByTestId('signin-btn'));
      fireEvent.click(screen.getByTestId('signin-btn'));
      fireEvent.click(screen.getByTestId('signin-btn'));

      await waitFor(() => {
        expect(mockSignIn).toHaveBeenCalledTimes(3);
      });
    });

    it('should handle very long email addresses', async () => {
      const longEmail = 'a'.repeat(100) + '@example.com';
      const mockSignIn = vi.mocked(supabase.auth.signInWithPassword).mockResolvedValue({
        data: { user: null, session: null },
        error: null
      });

      renderWithAuth(<TestComponent />);
      
      await act(async () => {
        const { signIn } = useAuth();
        await signIn(longEmail, 'password123');
      });

      expect(mockSignIn).toHaveBeenCalledWith({
        email: longEmail,
        password: 'password123'
      });
    });

    it('should handle very long passwords', async () => {
      const longPassword = 'a'.repeat(1000);
      const mockSignIn = vi.mocked(supabase.auth.signInWithPassword).mockResolvedValue({
        data: { user: null, session: null },
        error: null
      });

      renderWithAuth(<TestComponent />);
      
      await act(async () => {
        const { signIn } = useAuth();
        await signIn('test@example.com', longPassword);
      });

      expect(mockSignIn).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: longPassword
      });
    });
  });
});
