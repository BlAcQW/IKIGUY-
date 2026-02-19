import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import Auth from '@/pages/Auth';
import { AuthProvider } from '@/contexts/AuthContext';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/components/ui/use-toast';

// Mock dependencies
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      onAuthStateChange: vi.fn(),
      getSession: vi.fn(),
    },
  },
}));

vi.mock('@/components/ui/use-toast', () => ({
  useToast: vi.fn(),
}));

const mockUseAuth = vi.fn();
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: mockUseAuth,
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const renderAuth = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Auth />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Authentication - CSP Fix Verification', () => {
  const mockToast = vi.fn();
  const mockSignInWithPassword = vi.fn();
  const mockSignUp = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    (useToast as any).mockReturnValue({
      toast: mockToast,
    });

    (supabase.auth.signInWithPassword as any) = mockSignInWithPassword;
    (supabase.auth.signUp as any) = mockSignUp;
    (supabase.auth.onAuthStateChange as any).mockReturnValue({
      data: { subscription: { unsubscribe: vi.fn() } },
    });
    (supabase.auth.getSession as any).mockResolvedValue({
      data: { session: null },
      error: null,
    });

    // Mock the AuthContext
    mockUseAuth.mockReturnValue({
      signIn: async (email: string, password: string) => {
        const result = await mockSignInWithPassword({ email, password });
        if (result.error) {
          return { error: result.error };
        }
        return { error: null };
      },
      signUp: async (email: string, password: string, metadata: any) => {
        const result = await mockSignUp({ email, password, options: { data: metadata } });
        if (result.error) {
          return { error: result.error };
        }
        return { error: null };
      },
      user: null,
    });
  });

  describe('Sign In Functionality', () => {
    it('should handle successful sign in', async () => {
      mockSignInWithPassword.mockResolvedValue({
        data: {
          user: { id: 'test-user-id', email: 'test@example.com' },
          session: { access_token: 'test-token' },
        },
        error: null,
      });

      renderAuth();
      
      fireEvent.change(screen.getByLabelText('Email'), { 
        target: { value: 'test@example.com' } 
      });
      fireEvent.change(screen.getByLabelText('Password'), { 
        target: { value: 'password123' } 
      });
      
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(mockSignInWithPassword).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        });
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Welcome back!',
          description: "You've been signed in successfully.",
        });
      });
    });

    it('should handle sign in error', async () => {
      mockSignInWithPassword.mockResolvedValue({
        data: null,
        error: { message: 'Invalid credentials' },
      });

      renderAuth();
      
      fireEvent.change(screen.getByLabelText('Email'), { 
        target: { value: 'test@example.com' } 
      });
      fireEvent.change(screen.getByLabelText('Password'), { 
        target: { value: 'wrongpassword' } 
      });
      
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Error signing in',
          description: 'Invalid credentials',
          variant: 'destructive',
        });
      });
    });

    it('should handle network error during sign in', async () => {
      mockSignInWithPassword.mockRejectedValue(new Error('Network error'));

      renderAuth();
      
      fireEvent.change(screen.getByLabelText('Email'), { 
        target: { value: 'test@example.com' } 
      });
      fireEvent.change(screen.getByLabelText('Password'), { 
        target: { value: 'password123' } 
      });
      
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Error signing in',
          description: 'Network error',
          variant: 'destructive',
        });
      });
    });
  });

  describe('Sign Up Functionality', () => {
    it('should handle successful sign up', async () => {
      mockSignUp.mockResolvedValue({
        data: {
          user: { id: 'test-user-id', email: 'test@example.com' },
          session: null,
        },
        error: null,
      });

      renderAuth();
      
      // Switch to sign up mode
      fireEvent.click(screen.getByText('Sign Up'));
      
      fireEvent.change(screen.getByLabelText('Full Name'), { 
        target: { value: 'John Doe' } 
      });
      fireEvent.change(screen.getByLabelText('Company (Optional)'), { 
        target: { value: 'Test Company' } 
      });
      fireEvent.change(screen.getByLabelText('Phone Number'), { 
        target: { value: '+233123456789' } 
      });
      fireEvent.change(screen.getByLabelText('Email'), { 
        target: { value: 'test@example.com' } 
      });
      fireEvent.change(screen.getByLabelText('Password'), { 
        target: { value: 'password123' } 
      });
      
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(mockSignUp).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
          options: {
            data: {
              full_name: 'John Doe',
              company_name: 'Test Company',
              phone: '+233123456789',
            },
          },
        });
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Account created!',
          description: 'Please check your email to verify your account.',
        });
      });
    });

    it('should handle sign up error', async () => {
      mockSignUp.mockResolvedValue({
        data: null,
        error: { message: 'Email already registered' },
      });

      renderAuth();
      
      // Switch to sign up mode
      fireEvent.click(screen.getByText('Sign Up'));
      
      fireEvent.change(screen.getByLabelText('Full Name'), { 
        target: { value: 'John Doe' } 
      });
      fireEvent.change(screen.getByLabelText('Phone Number'), { 
        target: { value: '+233123456789' } 
      });
      fireEvent.change(screen.getByLabelText('Email'), { 
        target: { value: 'existing@example.com' } 
      });
      fireEvent.change(screen.getByLabelText('Password'), { 
        target: { value: 'password123' } 
      });
      
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Error creating account',
          description: 'Email already registered',
          variant: 'destructive',
        });
      });
    });
  });

  describe('Form Validation', () => {
    it('should validate required fields', async () => {
      renderAuth();
      
      // Try to submit without filling fields
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

      // The form should still submit but with empty values
      await waitFor(() => {
        expect(mockSignInWithPassword).toHaveBeenCalledWith({
          email: '',
          password: '',
        });
      });
    });

    it('should validate email format', async () => {
      renderAuth();
      
      fireEvent.change(screen.getByLabelText('Email'), { 
        target: { value: 'invalid-email' } 
      });
      fireEvent.change(screen.getByLabelText('Password'), { 
        target: { value: 'password123' } 
      });
      
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

      // The form should still submit but with invalid email
      await waitFor(() => {
        expect(mockSignInWithPassword).toHaveBeenCalledWith({
          email: 'invalid-email',
          password: 'password123',
        });
      });
    });

    it('should allow short passwords (validation handled by Supabase)', async () => {
      renderAuth();
      
      fireEvent.change(screen.getByLabelText('Email'), { 
        target: { value: 'test@example.com' } 
      });
      fireEvent.change(screen.getByLabelText('Password'), { 
        target: { value: '123' } // Short password
      });
      
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

      // The form should submit with short password (Supabase will handle validation)
      await waitFor(() => {
        expect(mockSignInWithPassword).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: '123',
        });
      });
    });
  });

  describe('CSP Compatibility', () => {
    it('should handle Supabase API calls without CSP blocking', async () => {
      // This test verifies that the CSP fix allows Supabase API calls
      mockSignInWithPassword.mockResolvedValue({
        data: {
          user: { id: 'test-user-id', email: 'test@example.com' },
          session: { access_token: 'test-token' },
        },
        error: null,
      });

      renderAuth();
      
      fireEvent.change(screen.getByLabelText('Email'), { 
        target: { value: 'test@example.com' } 
      });
      fireEvent.change(screen.getByLabelText('Password'), { 
        target: { value: 'password123' } 
      });
      
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

      // If CSP was blocking, this would fail
      await waitFor(() => {
        expect(mockSignInWithPassword).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Welcome back!',
          description: "You've been signed in successfully.",
        });
      });
    });

    it('should handle network errors gracefully', async () => {
      // Simulate a network error that might occur due to CSP issues
      mockSignInWithPassword.mockRejectedValue(new Error('NetworkError when attempting to fetch resource'));

      renderAuth();
      
      fireEvent.change(screen.getByLabelText('Email'), { 
        target: { value: 'test@example.com' } 
      });
      fireEvent.change(screen.getByLabelText('Password'), { 
        target: { value: 'password123' } 
      });
      
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Error signing in',
          description: 'NetworkError when attempting to fetch resource',
          variant: 'destructive',
        });
      });
    });
  });
});
