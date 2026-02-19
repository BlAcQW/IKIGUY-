import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TwoFactorAuth from '@/components/TwoFactorAuth';
import { AuthProvider } from '@/contexts/AuthContext';

// Mock Supabase
const mockSupabase = {
  auth: {
    getUser: vi.fn(),
    updateUser: vi.fn(),
  },
  functions: {
    invoke: jest.fn(),
  },
};

jest.mock('@/integrations/supabase/client', () => ({
  supabase: mockSupabase,
}));

// Mock toast
const mockToast = jest.fn();
jest.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          {component}
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('TwoFactorAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSupabase.auth.getUser.mockResolvedValue({
      data: { user: { id: 'test-user-id', user_metadata: { two_factor_enabled: false } } },
    });
  });

  it('renders 2FA component with disabled status', async () => {
    renderWithProviders(<TwoFactorAuth />);

    await waitFor(() => {
      expect(screen.getByText('Two-Factor Authentication')).toBeInTheDocument();
      expect(screen.getByText('Add an extra layer of security to your account')).toBeInTheDocument();
      expect(screen.getByText('Disabled')).toBeInTheDocument();
    });
  });

  it('shows enabled status when 2FA is enabled', async () => {
    mockSupabase.auth.getUser.mockResolvedValue({
      data: { user: { id: 'test-user-id', user_metadata: { two_factor_enabled: true } } },
    });

    renderWithProviders(<TwoFactorAuth />);

    await waitFor(() => {
      expect(screen.getByText('Enabled')).toBeInTheDocument();
    });
  });

  it('shows enable 2FA button when disabled', async () => {
    renderWithProviders(<TwoFactorAuth />);

    await waitFor(() => {
      expect(screen.getByText('Enable 2FA')).toBeInTheDocument();
    });
  });

  it('shows disable 2FA button when enabled', async () => {
    mockSupabase.auth.getUser.mockResolvedValue({
      data: { user: { id: 'test-user-id', user_metadata: { two_factor_enabled: true } } },
    });

    renderWithProviders(<TwoFactorAuth />);

    await waitFor(() => {
      expect(screen.getByText('Disable 2FA')).toBeInTheDocument();
    });
  });

  it('handles enable 2FA button click', async () => {
    const mockSetupData = {
      secret: 'test-secret',
      qrCode: 'data:image/png;base64,test-qr-code',
      backupCodes: ['CODE1', 'CODE2', 'CODE3', 'CODE4', 'CODE5', 'CODE6', 'CODE7', 'CODE8'],
    };

    mockSupabase.functions.invoke.mockResolvedValue({
      data: mockSetupData,
      error: null,
    });

    renderWithProviders(<TwoFactorAuth />);

    await waitFor(() => {
      expect(screen.getByText('Enable 2FA')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Enable 2FA'));

    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('setup-two-factor', {
        body: { userId: 'test-user-id' },
      });
    });
  });

  it('shows QR code setup when enable is clicked', async () => {
    const mockSetupData = {
      secret: 'test-secret',
      qrCode: 'data:image/png;base64,test-qr-code',
      backupCodes: ['CODE1', 'CODE2', 'CODE3', 'CODE4', 'CODE5', 'CODE6', 'CODE7', 'CODE8'],
    };

    mockSupabase.functions.invoke.mockResolvedValue({
      data: mockSetupData,
      error: null,
    });

    renderWithProviders(<TwoFactorAuth />);

    await waitFor(() => {
      expect(screen.getByText('Enable 2FA')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Enable 2FA'));

    await waitFor(() => {
      expect(screen.getByText('Scan QR Code')).toBeInTheDocument();
      expect(screen.getByText('Verification Code')).toBeInTheDocument();
      expect(screen.getByText('Verify & Enable')).toBeInTheDocument();
    });
  });

  it('handles verification code input', async () => {
    const mockSetupData = {
      secret: 'test-secret',
      qrCode: 'data:image/png;base64,test-qr-code',
      backupCodes: ['CODE1', 'CODE2', 'CODE3', 'CODE4', 'CODE5', 'CODE6', 'CODE7', 'CODE8'],
    };

    mockSupabase.functions.invoke.mockResolvedValue({
      data: mockSetupData,
      error: null,
    });

    renderWithProviders(<TwoFactorAuth />);

    await waitFor(() => {
      expect(screen.getByText('Enable 2FA')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Enable 2FA'));

    await waitFor(() => {
      const verificationInput = screen.getByPlaceholderText('Enter 6-digit code');
      fireEvent.change(verificationInput, { target: { value: '123456' } });
      expect(verificationInput).toHaveValue('123456');
    });
  });

  it('handles verification and enable 2FA', async () => {
    const mockSetupData = {
      secret: 'test-secret',
      qrCode: 'data:image/png;base64,test-qr-code',
      backupCodes: ['CODE1', 'CODE2', 'CODE3', 'CODE4', 'CODE5', 'CODE6', 'CODE7', 'CODE8'],
    };

    mockSupabase.functions.invoke
      .mockResolvedValueOnce({
        data: mockSetupData,
        error: null,
      })
      .mockResolvedValueOnce({
        data: { success: true },
        error: null,
      });

    mockSupabase.auth.updateUser.mockResolvedValue({
      data: { user: { id: 'test-user-id' } },
      error: null,
    });

    renderWithProviders(<TwoFactorAuth />);

    await waitFor(() => {
      expect(screen.getByText('Enable 2FA')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Enable 2FA'));

    await waitFor(() => {
      const verificationInput = screen.getByPlaceholderText('Enter 6-digit code');
      fireEvent.change(verificationInput, { target: { value: '123456' } });
    });

    fireEvent.click(screen.getByText('Verify & Enable'));

    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('verify-two-factor', {
        body: {
          userId: 'test-user-id',
          code: '123456',
          secret: 'test-secret',
        },
      });
    });
  });

  it('handles disable 2FA', async () => {
    mockSupabase.auth.getUser.mockResolvedValue({
      data: { user: { id: 'test-user-id', user_metadata: { two_factor_enabled: true } } },
    });

    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true },
      error: null,
    });

    mockSupabase.auth.updateUser.mockResolvedValue({
      data: { user: { id: 'test-user-id' } },
      error: null,
    });

    renderWithProviders(<TwoFactorAuth />);

    await waitFor(() => {
      expect(screen.getByText('Disable 2FA')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Disable 2FA'));

    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('disable-two-factor', {
        body: { userId: 'test-user-id' },
      });
    });
  });

  it('handles error when setting up 2FA', async () => {
    mockSupabase.functions.invoke.mockRejectedValue(new Error('Setup failed'));

    renderWithProviders(<TwoFactorAuth />);

    await waitFor(() => {
      expect(screen.getByText('Enable 2FA')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Enable 2FA'));

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Setup failed',
        variant: 'destructive',
      });
    });
  });

  it('shows backup codes when available', async () => {
    const mockSetupData = {
      secret: 'test-secret',
      qrCode: 'data:image/png;base64,test-qr-code',
      backupCodes: ['CODE1', 'CODE2', 'CODE3', 'CODE4', 'CODE5', 'CODE6', 'CODE7', 'CODE8'],
    };

    mockSupabase.functions.invoke.mockResolvedValue({
      data: mockSetupData,
      error: null,
    });

    renderWithProviders(<TwoFactorAuth />);

    await waitFor(() => {
      expect(screen.getByText('Enable 2FA')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Enable 2FA'));

    await waitFor(() => {
      expect(screen.getByText('Backup Codes')).toBeInTheDocument();
      expect(screen.getByText('CODE1')).toBeInTheDocument();
      expect(screen.getByText('CODE2')).toBeInTheDocument();
    });
  });

  it('handles generate new backup codes', async () => {
    const mockSetupData = {
      secret: 'test-secret',
      qrCode: 'data:image/png;base64,test-qr-code',
      backupCodes: ['CODE1', 'CODE2', 'CODE3', 'CODE4', 'CODE5', 'CODE6', 'CODE7', 'CODE8'],
    };

    mockSupabase.functions.invoke
      .mockResolvedValueOnce({
        data: mockSetupData,
        error: null,
      })
      .mockResolvedValueOnce({
        data: { backupCodes: ['NEW1', 'NEW2', 'NEW3', 'NEW4', 'NEW5', 'NEW6', 'NEW7', 'NEW8'] },
        error: null,
      });

    renderWithProviders(<TwoFactorAuth />);

    await waitFor(() => {
      expect(screen.getByText('Enable 2FA')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Enable 2FA'));

    await waitFor(() => {
      expect(screen.getByText('Generate New')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Generate New'));

    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('generate-backup-codes', {
        body: { userId: 'test-user-id' },
      });
    });
  });
});
