import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import SessionTimeout from '../SessionTimeout';
import { useAuth } from '@/contexts/AuthContext';

// Mock the useAuth hook
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}));

// Mock the useToast hook
jest.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn()
  })
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('SessionTimeout', () => {
  const defaultProps = {
    children: <div data-testid="child-content">Test Content</div>
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when session is valid', () => {
    mockUseAuth.mockReturnValue({
      session: {
        expires_at: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
        access_token: 'test-token',
        refresh_token: 'test-refresh-token',
        token_type: 'bearer',
        user: {
          id: 'test-user-id',
          email: 'test@example.com',
          user_metadata: {}
        }
      },
      isSessionExpired: false,
      refreshSession: jest.fn(),
      signOut: jest.fn(),
      user: null,
      loading: false,
      signUp: jest.fn(),
      signIn: jest.fn()
    });

    render(
      <BrowserRouter>
        <SessionTimeout {...defaultProps} />
      </BrowserRouter>
    );

    expect(screen.getByTestId('child-content')).toBeInTheDocument();
  });

  it('shows timeout dialog when session is expiring soon', async () => {
    const mockRefreshSession = jest.fn();
    const mockSignOut = jest.fn();

    mockUseAuth.mockReturnValue({
      session: {
        expires_at: Math.floor(Date.now() / 1000) + 240, // 4 minutes from now
        access_token: 'test-token',
        refresh_token: 'test-refresh-token',
        token_type: 'bearer',
        user: {
          id: 'test-user-id',
          email: 'test@example.com',
          user_metadata: {}
        }
      },
      isSessionExpired: false,
      refreshSession: mockRefreshSession,
      signOut: mockSignOut,
      user: null,
      loading: false,
      signUp: jest.fn(),
      signIn: jest.fn()
    });

    render(
      <BrowserRouter>
        <SessionTimeout {...defaultProps} />
      </BrowserRouter>
    );

    // Wait for the timeout dialog to appear
    await waitFor(() => {
      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument();
    });

    expect(screen.getByText(/Your session will expire in/)).toBeInTheDocument();
  });

  it('handles session refresh when refresh button is clicked', async () => {
    const mockRefreshSession = jest.fn();
    const mockSignOut = jest.fn();

    mockUseAuth.mockReturnValue({
      session: {
        expires_at: Math.floor(Date.now() / 1000) + 240, // 4 minutes from now
        access_token: 'test-token',
        refresh_token: 'test-refresh-token',
        token_type: 'bearer',
        user: {
          id: 'test-user-id',
          email: 'test@example.com',
          user_metadata: {}
        }
      },
      isSessionExpired: false,
      refreshSession: mockRefreshSession,
      signOut: mockSignOut,
      user: null,
      loading: false,
      signUp: jest.fn(),
      signIn: jest.fn()
    });

    render(
      <BrowserRouter>
        <SessionTimeout {...defaultProps} />
      </BrowserRouter>
    );

    // Wait for the timeout dialog to appear
    await waitFor(() => {
      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument();
    });

    // Click refresh button
    const refreshButton = screen.getByText('Refresh Session');
    fireEvent.click(refreshButton);

    expect(mockRefreshSession).toHaveBeenCalled();
  });

  it('handles sign out when sign out button is clicked', async () => {
    const mockRefreshSession = jest.fn();
    const mockSignOut = jest.fn();

    mockUseAuth.mockReturnValue({
      session: {
        expires_at: Math.floor(Date.now() / 1000) + 240, // 4 minutes from now
        access_token: 'test-token',
        refresh_token: 'test-refresh-token',
        token_type: 'bearer',
        user: {
          id: 'test-user-id',
          email: 'test@example.com',
          user_metadata: {}
        }
      },
      isSessionExpired: false,
      refreshSession: mockRefreshSession,
      signOut: mockSignOut,
      user: null,
      loading: false,
      signUp: jest.fn(),
      signIn: jest.fn()
    });

    render(
      <BrowserRouter>
        <SessionTimeout {...defaultProps} />
      </BrowserRouter>
    );

    // Wait for the timeout dialog to appear
    await waitFor(() => {
      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument();
    });

    // Click sign out button
    const signOutButton = screen.getByText('Sign Out');
    fireEvent.click(signOutButton);

    expect(mockSignOut).toHaveBeenCalled();
  });

  it('handles expired session', () => {
    const mockRefreshSession = jest.fn();
    const mockSignOut = jest.fn();

    mockUseAuth.mockReturnValue({
      session: null,
      isSessionExpired: true,
      refreshSession: mockRefreshSession,
      signOut: mockSignOut,
      user: null,
      loading: false,
      signUp: jest.fn(),
      signIn: jest.fn()
    });

    render(
      <BrowserRouter>
        <SessionTimeout {...defaultProps} />
      </BrowserRouter>
    );

    expect(mockSignOut).toHaveBeenCalled();
  });

  it('formats time correctly', async () => {
    const mockRefreshSession = jest.fn();
    const mockSignOut = jest.fn();

    mockUseAuth.mockReturnValue({
      session: {
        expires_at: Math.floor(Date.now() / 1000) + 125, // 2 minutes 5 seconds from now
        access_token: 'test-token',
        refresh_token: 'test-refresh-token',
        token_type: 'bearer',
        user: {
          id: 'test-user-id',
          email: 'test@example.com',
          user_metadata: {}
        }
      },
      isSessionExpired: false,
      refreshSession: mockRefreshSession,
      signOut: mockSignOut,
      user: null,
      loading: false,
      signUp: jest.fn(),
      signIn: jest.fn()
    });

    render(
      <BrowserRouter>
        <SessionTimeout {...defaultProps} />
      </BrowserRouter>
    );

    // Wait for the timeout dialog to appear
    await waitFor(() => {
      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument();
    });

    // Check that time is formatted correctly (should show 2:05)
    expect(screen.getByText(/2:05/)).toBeInTheDocument();
  });
});
