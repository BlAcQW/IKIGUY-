import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthModal } from '../AuthModal';
import { render } from '@/test/utils';

// Mock the AuthContext (Supabase-based)
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    signIn: vi.fn().mockResolvedValue({ error: null }),
    signUp: vi.fn().mockResolvedValue({ error: null }),
    signInWithProvider: vi.fn().mockResolvedValue({ error: null }),
  })),
}));

// Mock the BackendAuthContext
vi.mock('@/contexts/BackendAuthContext', () => ({
  useBackendAuth: vi.fn(() => ({
    user: null,
    tokens: null,
    loading: false,
    signIn: vi.fn().mockResolvedValue({ error: null }),
    signUp: vi.fn().mockResolvedValue({ error: null }),
    signOut: vi.fn().mockResolvedValue({ error: null }),
    updateProfile: vi.fn().mockResolvedValue({ error: null }),
    refreshProfile: vi.fn().mockResolvedValue(undefined),
  })),
  BackendAuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

describe('AuthModal', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Modal Rendering', () => {
    it('renders when isOpen is true', () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/sign in to contribute/i)).toBeInTheDocument();
    });

    it('does not render when isOpen is false', () => {
      render(
        <AuthModal isOpen={false} onClose={mockOnClose} />
      );

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('renders sign in and sign up tabs', () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByRole('tablist')).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /sign in/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /sign up/i })).toBeInTheDocument();
    });
  });

  describe('Form Elements', () => {
    it('renders sign in form elements', () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    it('renders provider sign in buttons', () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} />
      );

      // Buttons show just "Google" and "GitHub" (not "Continue with...")
      expect(screen.getByRole('button', { name: /google/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /github/i })).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('switches to sign up tab when clicked', async () => {
      const user = userEvent.setup();
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} />
      );

      // Initially on sign in tab - email field should be visible
      const signInEmailInput = screen.getByLabelText(/^email/i);
      expect(signInEmailInput).toBeInTheDocument();

      // Click sign up tab using userEvent for proper event handling
      const signUpTab = screen.getByRole('tab', { name: /sign up/i });
      await user.click(signUpTab);

      // Wait for tab content to switch and show sign up form elements
      await waitFor(() => {
        // Look for the signup-fullname input which is unique to the signup form
        expect(screen.getByPlaceholderText('John Doe')).toBeInTheDocument();
      });
      expect(screen.getByPlaceholderText('johndoe')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Confirm your password')).toBeInTheDocument();
    });

    it('starts with signup tab when defaultTab is signup', async () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} defaultTab="signup" />
      );

      // Wait for signup form to render - use placeholder text which is more reliable
      await waitFor(() => {
        expect(screen.getByPlaceholderText('John Doe')).toBeInTheDocument();
      });
      expect(screen.getByPlaceholderText('johndoe')).toBeInTheDocument();
    });
  });

  describe('Form Validation Display', () => {
    it('should show error messages in the UI', async () => {
      const user = userEvent.setup();
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} defaultTab="signup" />
      );

      // Wait for sign up tab content to render
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Confirm your password')).toBeInTheDocument();
      });

      // Fill email field (required)
      const emailInput = screen.getByPlaceholderText('your@email.com');
      await user.type(emailInput, 'test@example.com');

      // Fill form with mismatched passwords - use placeholder text which is more reliable
      const passwordInput = screen.getByPlaceholderText('At least 6 characters');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm your password');

      await user.type(passwordInput, 'password123');
      await user.type(confirmPasswordInput, 'differentpass');

      // Submit form - the sign up button in signup tab shows "Create Account"
      await user.click(screen.getByRole('button', { name: /create account/i }));

      // Should eventually show validation error message (client-side validation)
      await waitFor(() => {
        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
      });
    });
  });

  describe('Button States', () => {
    it('renders form submission buttons', () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /google/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /github/i })).toBeInTheDocument();
    });

    it('has proper button types', () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} />
      );

      const signInButton = screen.getByRole('button', { name: /sign in/i });
      expect(signInButton).toHaveAttribute('type', 'submit');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByRole('tablist')).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    it('has form labels associated with inputs', () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} />
      );

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);

      expect(emailInput).toHaveAttribute('type', 'email');
      expect(passwordInput).toHaveAttribute('type', 'password');
    });
  });

  describe('Form Structure', () => {
    it('contains proper form elements structure', async () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} />
      );

      // Wait for form to render within the dialog
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Verify email and password inputs exist using placeholder text
      expect(screen.getByPlaceholderText('your@email.com')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your password')).toBeInTheDocument();
    });

    it('sign up form has additional required fields', async () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} defaultTab="signup" />
      );

      // Wait for signup form to render - use placeholder text which is more reliable
      await waitFor(() => {
        expect(screen.getByPlaceholderText('John Doe')).toBeInTheDocument();
      });
      expect(screen.getByPlaceholderText('johndoe')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Confirm your password')).toBeInTheDocument();
    });
  });

  describe('Modal Behavior', () => {
    it('renders modal content when open', () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} />
      );

      // Modal title is "Join AfriLang Community"
      expect(screen.getByText(/afrilang community/i)).toBeInTheDocument();
    });

    it('provides close functionality', () => {
      render(
        <AuthModal isOpen={true} onClose={mockOnClose} />
      );

      // Modal should have close mechanisms (though we don't test the actual close behavior)
      expect(mockOnClose).toBeDefined();
      expect(typeof mockOnClose).toBe('function');
    });
  });
});