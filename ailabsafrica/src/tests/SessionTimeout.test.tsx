import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import SessionTimeout from '@/components/SessionTimeout';
import { AuthProvider } from '@/contexts/AuthContext';

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock the AuthContext
const mockSignOut = vi.fn();
const mockRefreshSession = vi.fn();
const mockIsSessionExpired = false;

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    session: null,
    isSessionExpired: mockIsSessionExpired,
    refreshSession: mockRefreshSession,
    signOut: mockSignOut,
  }),
}));

// Mock toast
const mockToast = vi.fn();
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: mockToast }),
}));

// Mock Date.now and setInterval
const mockDateNow = vi.fn();
const mockSetInterval = vi.fn();
const mockClearInterval = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  mockDateNow.mockReturnValue(1000000000000); // Mock timestamp
  global.Date.now = mockDateNow;
  global.setInterval = mockSetInterval;
  global.clearInterval = mockClearInterval;
});

afterEach(() => {
  vi.restoreAllMocks();
});

const TestComponent = () => <div>Test Content</div>;

const renderSessionTimeout = (session: any = null, isSessionExpired: boolean = false) => {
  // Mock the AuthContext with the provided session
  vi.mocked(require('@/contexts/AuthContext').useAuth).mockReturnValue({
    session,
    isSessionExpired,
    refreshSession: mockRefreshSession,
    signOut: mockSignOut,
  });

  return render(
    <BrowserRouter>
      <AuthProvider>
        <SessionTimeout>
          <TestComponent />
        </SessionTimeout>
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('SessionTimeout', () => {
  describe('Basic Rendering', () => {
    it('renders children when no session exists', () => {
      renderSessionTimeout(null);
      
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('renders children when session exists', () => {
      const session = { expires_at: 1000000000300 }; // 5 minutes from now
      renderSessionTimeout(session);
      
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('does not show timeout dialog initially', () => {
      const session = { expires_at: 1000000000300 };
      renderSessionTimeout(session);
      
      expect(screen.queryByText('Session Expiring Soon')).not.toBeInTheDocument();
    });
  });

  describe('Session Expiry Checking', () => {
    it('sets up interval to check session expiry', () => {
      const session = { expires_at: 1000000000300 };
      renderSessionTimeout(session);
      
      expect(mockSetInterval).toHaveBeenCalledWith(expect.any(Function), 60000);
    });

    it('clears interval on unmount', () => {
      const session = { expires_at: 1000000000300 };
      const { unmount } = renderSessionTimeout(session);
      
      unmount();
      
      expect(mockClearInterval).toHaveBeenCalled();
    });

    it('does not set up interval when no session exists', () => {
      renderSessionTimeout(null);
      
      expect(mockSetInterval).not.toHaveBeenCalled();
    });

    it('does not set up interval when session has no expires_at', () => {
      const session = { expires_at: null };
      renderSessionTimeout(session);
      
      expect(mockSetInterval).not.toHaveBeenCalled();
    });
  });

  describe('Session Warning Dialog', () => {
    it('shows warning dialog 5 minutes before expiry', () => {
      const session = { expires_at: 1000000000300 }; // 5 minutes from now
      renderSessionTimeout(session);
      
      // Simulate the interval callback
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument();
      expect(screen.getByText(/Your session will expire in/)).toBeInTheDocument();
    });

    it('shows correct time remaining in dialog', () => {
      const session = { expires_at: 1000000000300 }; // 5 minutes from now
      renderSessionTimeout(session);
      
      // Simulate the interval callback
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.getByText(/5:00/)).toBeInTheDocument();
    });

    it('does not show warning dialog when more than 5 minutes remaining', () => {
      const session = { expires_at: 1000000000600 }; // 10 minutes from now
      renderSessionTimeout(session);
      
      // Simulate the interval callback
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.queryByText('Session Expiring Soon')).not.toBeInTheDocument();
    });

    it('does not show warning dialog when session has expired', () => {
      const session = { expires_at: 1000000000000 }; // Expired
      renderSessionTimeout(session);
      
      // Simulate the interval callback
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.queryByText('Session Expiring Soon')).not.toBeInTheDocument();
    });
  });

  describe('Session Refresh', () => {
    it('refreshes session when refresh button is clicked', async () => {
      const session = { expires_at: 1000000000300 };
      mockRefreshSession.mockResolvedValue(undefined);
      
      renderSessionTimeout(session);
      
      // Show the dialog
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      const refreshButton = screen.getByText('Refresh Session');
      fireEvent.click(refreshButton);
      
      await waitFor(() => {
        expect(mockRefreshSession).toHaveBeenCalled();
      });
      
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Session Refreshed',
        description: 'Your session has been refreshed successfully.',
      });
    });

    it('closes dialog after successful refresh', async () => {
      const session = { expires_at: 1000000000300 };
      mockRefreshSession.mockResolvedValue(undefined);
      
      renderSessionTimeout(session);
      
      // Show the dialog
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument();
      
      const refreshButton = screen.getByText('Refresh Session');
      fireEvent.click(refreshButton);
      
      await waitFor(() => {
        expect(screen.queryByText('Session Expiring Soon')).not.toBeInTheDocument();
      });
    });

    it('handles refresh failure gracefully', async () => {
      const session = { expires_at: 1000000000300 };
      mockRefreshSession.mockRejectedValue(new Error('Refresh failed'));
      
      renderSessionTimeout(session);
      
      // Show the dialog
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      const refreshButton = screen.getByText('Refresh Session');
      fireEvent.click(refreshButton);
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Refresh Failed',
          description: 'Failed to refresh session. Please sign in again.',
          variant: 'destructive',
        });
      });
      
      expect(mockSignOut).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/auth');
    });
  });

  describe('Sign Out', () => {
    it('signs out when sign out button is clicked', () => {
      const session = { expires_at: 1000000000300 };
      
      renderSessionTimeout(session);
      
      // Show the dialog
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      const signOutButton = screen.getByText('Sign Out');
      fireEvent.click(signOutButton);
      
      expect(mockSignOut).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/auth');
    });

    it('closes dialog when sign out button is clicked', () => {
      const session = { expires_at: 1000000000300 };
      
      renderSessionTimeout(session);
      
      // Show the dialog
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument();
      
      const signOutButton = screen.getByText('Sign Out');
      fireEvent.click(signOutButton);
      
      expect(screen.queryByText('Session Expiring Soon')).not.toBeInTheDocument();
    });
  });

  describe('Automatic Session Expiry', () => {
    it('automatically logs out when session expires', () => {
      const session = { expires_at: 1000000000000 }; // Expired
      
      renderSessionTimeout(session);
      
      // Simulate the interval callback
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(mockSignOut).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/auth');
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Session Expired',
        description: 'Your session has expired. Please sign in again.',
        variant: 'destructive',
      });
    });

    it('handles session expired from context', () => {
      renderSessionTimeout(null, true);
      
      expect(mockSignOut).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/auth');
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Session Expired',
        description: 'Your session has expired. Please sign in again.',
        variant: 'destructive',
      });
    });
  });

  describe('Time Formatting', () => {
    it('formats time correctly for minutes and seconds', () => {
      const session = { expires_at: 1000000000300 }; // 5 minutes from now
      
      renderSessionTimeout(session);
      
      // Simulate the interval callback
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.getByText(/5:00/)).toBeInTheDocument();
    });

    it('formats time correctly for less than a minute', () => {
      const session = { expires_at: 1000000000050 }; // 50 seconds from now
      
      renderSessionTimeout(session);
      
      // Simulate the interval callback
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.getByText(/0:50/)).toBeInTheDocument();
    });

    it('formats time correctly for single digit seconds', () => {
      const session = { expires_at: 1000000000009 }; // 9 seconds from now
      
      renderSessionTimeout(session);
      
      // Simulate the interval callback
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.getByText(/0:09/)).toBeInTheDocument();
    });
  });

  describe('Dialog Interaction', () => {
    it('closes dialog when clicking outside', () => {
      const session = { expires_at: 1000000000300 };
      
      renderSessionTimeout(session);
      
      // Show the dialog
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument();
      
      // Simulate clicking outside (onOpenChange with false)
      const dialog = screen.getByRole('dialog');
      fireEvent.click(dialog);
      
      // Dialog should still be open as clicking inside doesn't close it
      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument();
    });

    it('shows correct dialog content', () => {
      const session = { expires_at: 1000000000300 };
      
      renderSessionTimeout(session);
      
      // Show the dialog
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument();
      expect(screen.getByText(/Would you like to refresh your session/)).toBeInTheDocument();
      expect(screen.getByText('Refresh Session')).toBeInTheDocument();
      expect(screen.getByText('Sign Out')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles missing session gracefully', () => {
      renderSessionTimeout(null);
      
      expect(screen.getByText('Test Content')).toBeInTheDocument();
      expect(mockSetInterval).not.toHaveBeenCalled();
    });

    it('handles session without expires_at gracefully', () => {
      const session = { expires_at: null };
      renderSessionTimeout(session);
      
      expect(screen.getByText('Test Content')).toBeInTheDocument();
      expect(mockSetInterval).not.toHaveBeenCalled();
    });

    it('handles refresh session errors gracefully', async () => {
      const session = { expires_at: 1000000000300 };
      mockRefreshSession.mockRejectedValue(new Error('Network error'));
      
      renderSessionTimeout(session);
      
      // Show the dialog
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      const refreshButton = screen.getByText('Refresh Session');
      fireEvent.click(refreshButton);
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Refresh Failed',
          description: 'Failed to refresh session. Please sign in again.',
          variant: 'destructive',
        });
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper dialog role', () => {
      const session = { expires_at: 1000000000300 };
      
      renderSessionTimeout(session);
      
      // Show the dialog
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('has proper button roles', () => {
      const session = { expires_at: 1000000000300 };
      
      renderSessionTimeout(session);
      
      // Show the dialog
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.getByRole('button', { name: 'Refresh Session' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Sign Out' })).toBeInTheDocument();
    });

    it('has proper heading structure', () => {
      const session = { expires_at: 1000000000300 };
      
      renderSessionTimeout(session);
      
      // Show the dialog
      const intervalCallback = mockSetInterval.mock.calls[0][0];
      act(() => {
        intervalCallback();
      });
      
      expect(screen.getByRole('heading', { name: 'Session Expiring Soon' })).toBeInTheDocument();
    });
  });
});
