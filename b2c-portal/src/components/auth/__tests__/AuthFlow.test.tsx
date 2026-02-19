/**
 * Unit tests for authentication flow (login/logout)
 * Tests MongoDB authentication integration
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';

// Mock react-router-dom navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate
  };
});

// Mock toast
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mockToast })
}));

// Mock MongoDB auth
vi.mock('@/lib/mongo-auth', () => ({
  mongoAuth: {
    signin: vi.fn(),
    signout: vi.fn(),
    signup: vi.fn(),
    getUser: vi.fn(),
    getAccessToken: vi.fn(),
    isAuthenticated: vi.fn(),
    validateSession: vi.fn(),
    getTenantId: vi.fn()
  }
}));

// Import components after mocks
import { LoginForm } from '../LoginForm';
import { LogoutButton } from '../LogoutButton';
import { MongoAuthProvider, useMongoAuth } from '../MongoAuthContext';
import { mongoAuth } from '@/lib/mongo-auth';

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <MongoAuthProvider>
      {children}
    </MongoAuthProvider>
  </BrowserRouter>
);

describe('MongoDB Authentication Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();

    // Setup default MongoDB auth mock responses
    vi.mocked(mongoAuth.isAuthenticated).mockReturnValue(false);
    vi.mocked(mongoAuth.getUser).mockReturnValue(null);
    vi.mocked(mongoAuth.getAccessToken).mockReturnValue(null);
    vi.mocked(mongoAuth.validateSession).mockResolvedValue(false);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('LoginForm Component', () => {
    it('should render login form', () => {
      render(
        <TestWrapper>
          <LoginForm onSuccess={() => {}} />
        </TestWrapper>
      );

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    it('should validate required fields', async () => {
      render(
        <TestWrapper>
          <LoginForm onSuccess={() => {}} />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });
    });

    it('should prevent submission with invalid email', async () => {
      const mockOnSuccess = vi.fn();

      render(
        <TestWrapper>
          <LoginForm onSuccess={mockOnSuccess} />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      // Fill in invalid email and valid password
      fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
      fireEvent.change(passwordInput, { target: { value: 'validpassword' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        // signIn should not be called due to validation failure
        expect(vi.mocked(mongoAuth.signin)).not.toHaveBeenCalled();
        expect(mockOnSuccess).not.toHaveBeenCalled();
      });
    });
  });

  describe('LogoutButton Component', () => {
    it('should render logout button', () => {
      render(
        <TestWrapper>
          <LogoutButton />
        </TestWrapper>
      );

      expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
    });

    it('should call signOut when button is clicked', async () => {
      vi.mocked(mongoAuth.signout).mockResolvedValue();

      render(
        <TestWrapper>
          <LogoutButton />
        </TestWrapper>
      );

      const logoutButton = screen.getByRole('button', { name: /logout/i });

      fireEvent.click(logoutButton);

      // Wait for signout to be called
      await waitFor(() => {
        expect(vi.mocked(mongoAuth.signout)).toHaveBeenCalled();
      });
    });

    it('should show confirmation dialog when confirmLogout is true', () => {
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);

      render(
        <TestWrapper>
          <LogoutButton confirmLogout={true} />
        </TestWrapper>
      );

      const logoutButton = screen.getByRole('button', { name: /logout/i });
      fireEvent.click(logoutButton);

      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to sign out?');
      expect(vi.mocked(mongoAuth.signout)).not.toHaveBeenCalled();

      confirmSpy.mockRestore();
    });
  });
});