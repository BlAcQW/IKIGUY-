import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import Dashboard from '@/pages/Dashboard';
import { supabase } from '@/integrations/supabase/client';

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
const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
};

const mockSignOut = vi.fn();
const mockRefreshSession = vi.fn();

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    loading: false,
    signOut: mockSignOut,
    refreshSession: mockRefreshSession,
  }),
}));

// Mock Supabase client
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(),
  },
}));

// Mock toast
const mockToast = vi.fn();
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: mockToast }),
}));

// Mock dashboard components
vi.mock('@/components/dashboard/WalletSection', () => ({
  default: ({ wallet, onWalletUpdate }: any) => (
    <div data-testid="wallet-section">
      Wallet Section {wallet ? 'with data' : 'without data'}
    </div>
  ),
}));

vi.mock('@/components/dashboard/RecentDemos', () => ({
  default: () => <div data-testid="recent-demos">Recent Demos</div>,
}));

vi.mock('@/components/dashboard/DemoBookings', () => ({
  default: () => <div data-testid="demo-bookings">Demo Bookings</div>,
}));

vi.mock('@/components/dashboard/TransactionHistory', () => ({
  default: () => <div data-testid="transaction-history">Transaction History</div>,
}));

vi.mock('@/components/dashboard/PaymentHistory', () => ({
  default: () => <div data-testid="payment-history">Payment History</div>,
}));

vi.mock('@/components/dashboard/RefundHistory', () => ({
  default: () => <div data-testid="refund-history">Refund History</div>,
}));

vi.mock('@/components/dashboard/PaymentAnalytics', () => ({
  default: () => <div data-testid="payment-analytics">Payment Analytics</div>,
}));

vi.mock('@/components/dashboard/DemoAnalytics', () => ({
  default: () => <div data-testid="demo-analytics">Demo Analytics</div>,
}));

vi.mock('@/components/dashboard/AdvancedAnalytics', () => ({
  default: () => <div data-testid="advanced-analytics">Advanced Analytics</div>,
}));

vi.mock('@/components/dashboard/VoiceAgentManagement', () => ({
  default: () => <div data-testid="voice-agent-management">Voice Agent Management</div>,
}));

vi.mock('@/components/dashboard/AssistantAnalytics', () => ({
  default: () => <div data-testid="assistant-analytics">Assistant Analytics</div>,
}));

vi.mock('@/components/TwoFactorAuth', () => ({
  default: () => <div data-testid="two-factor-auth">Two Factor Auth</div>,
}));

const renderDashboard = (user: any = mockUser, loading: boolean = false) => {
  // Mock the AuthContext with the provided user
  vi.mocked(require('@/contexts/AuthContext').useAuth).mockReturnValue({
    user,
    loading,
    signOut: mockSignOut,
    refreshSession: mockRefreshSession,
  });

  return render(
    <BrowserRouter>
      <Dashboard />
    </BrowserRouter>
  );
};

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Authentication', () => {
    it('redirects to auth page when user is not authenticated', () => {
      renderDashboard(null);
      
      expect(mockNavigate).toHaveBeenCalledWith('/auth');
    });

    it('redirects to auth page when loading is true', () => {
      renderDashboard(mockUser, true);
      
      expect(mockNavigate).toHaveBeenCalledWith('/auth');
    });

    it('renders dashboard when user is authenticated', () => {
      renderDashboard(mockUser);
      
      expect(screen.getByText(/Welcome back/)).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading spinner when loading', () => {
      renderDashboard(mockUser, true);
      
      expect(screen.getByRole('status')).toBeInTheDocument();
      expect(screen.getByRole('status')).toHaveClass('animate-spin');
    });

    it('does not render dashboard content when loading', () => {
      renderDashboard(mockUser, true);
      
      expect(screen.queryByText(/Welcome back/)).not.toBeInTheDocument();
    });
  });

  describe('User Data Loading', () => {
    it('fetches user data when component mounts', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ data: null, error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);

      await waitFor(() => {
        expect(supabase.from).toHaveBeenCalledWith('wallets');
        expect(supabase.from).toHaveBeenCalledWith('profiles');
      });
    });

    it('handles wallet data loading error gracefully', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ 
            data: null, 
            error: { code: 'PGRST116', message: 'Not found' } 
          }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);

      await waitFor(() => {
        expect(screen.getByTestId('wallet-section')).toHaveTextContent('without data');
      });
    });

    it('handles profile data loading error gracefully', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ 
            data: null, 
            error: { code: 'PGRST116', message: 'Not found' } 
          }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);

      await waitFor(() => {
        expect(screen.getByText(/Welcome back, test@example.com/)).toBeInTheDocument();
      });
    });

    it('shows error toast when data loading fails', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockRejectedValue(new Error('Network error')),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Error loading data',
          description: 'Failed to load your account information.',
          variant: 'destructive',
        });
      });
    });
  });

  describe('Welcome Message', () => {
    it('shows user email when no display name is available', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ data: null, error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);

      await waitFor(() => {
        expect(screen.getByText(/Welcome back, test@example.com/)).toBeInTheDocument();
      });
    });

    it('shows display name when available', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ 
            data: { display_name: 'John Doe' }, 
            error: null 
          }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);

      await waitFor(() => {
        expect(screen.getByText(/Welcome back, John Doe/)).toBeInTheDocument();
      });
    });
  });

  describe('Tab Navigation', () => {
    beforeEach(async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ data: null, error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);
      
      await waitFor(() => {
        expect(screen.getByText(/Welcome back/)).toBeInTheDocument();
      });
    });

    it('shows wallet tab by default', () => {
      expect(screen.getByTestId('wallet-section')).toBeInTheDocument();
      expect(screen.getByTestId('recent-demos')).toBeInTheDocument();
    });

    it('navigates to demo bookings tab', () => {
      const bookingsTab = screen.getByText('Demo Bookings');
      fireEvent.click(bookingsTab);

      expect(screen.getByTestId('demo-bookings')).toBeInTheDocument();
    });

    it('navigates to transactions tab', () => {
      const transactionsTab = screen.getByText('Transactions');
      fireEvent.click(transactionsTab);

      expect(screen.getByTestId('transaction-history')).toBeInTheDocument();
    });

    it('navigates to payment history tab', () => {
      const paymentsTab = screen.getByText('Payment History');
      fireEvent.click(paymentsTab);

      expect(screen.getByTestId('payment-history')).toBeInTheDocument();
      expect(screen.getByTestId('refund-history')).toBeInTheDocument();
    });

    it('navigates to analytics tab', () => {
      const analyticsTab = screen.getByText('Analytics');
      fireEvent.click(analyticsTab);

      expect(screen.getByTestId('payment-analytics')).toBeInTheDocument();
    });

    it('navigates to demo analytics tab', () => {
      const demoAnalyticsTab = screen.getByText('Demo Analytics');
      fireEvent.click(demoAnalyticsTab);

      expect(screen.getByTestId('demo-analytics')).toBeInTheDocument();
    });

    it('navigates to advanced analytics tab', () => {
      const advancedAnalyticsTab = screen.getByText('Advanced Analytics');
      fireEvent.click(advancedAnalyticsTab);

      expect(screen.getByTestId('advanced-analytics')).toBeInTheDocument();
    });

    it('navigates to voice agents tab', () => {
      const agentsTab = screen.getByText('Voice Agents');
      fireEvent.click(agentsTab);

      expect(screen.getByTestId('voice-agent-management')).toBeInTheDocument();
    });

    it('navigates to security tab', () => {
      const securityTab = screen.getByText('Security');
      fireEvent.click(securityTab);

      expect(screen.getByTestId('two-factor-auth')).toBeInTheDocument();
    });
  });

  describe('Voice Agents Tab', () => {
    beforeEach(async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ data: null, error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);
      
      await waitFor(() => {
        expect(screen.getByText(/Welcome back/)).toBeInTheDocument();
      });

      const agentsTab = screen.getByText('Voice Agents');
      fireEvent.click(agentsTab);
    });

    it('shows management tab by default', () => {
      expect(screen.getByTestId('voice-agent-management')).toBeInTheDocument();
    });

    it('navigates to analytics sub-tab', () => {
      const analyticsSubTab = screen.getByText('Analytics');
      fireEvent.click(analyticsSubTab);

      expect(screen.getByTestId('assistant-analytics')).toBeInTheDocument();
    });

    it('navigates back to management sub-tab', () => {
      const analyticsSubTab = screen.getByText('Analytics');
      fireEvent.click(analyticsSubTab);

      const managementSubTab = screen.getByText('Management');
      fireEvent.click(managementSubTab);

      expect(screen.getByTestId('voice-agent-management')).toBeInTheDocument();
    });
  });

  describe('Tab Icons', () => {
    beforeEach(async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ data: null, error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);
      
      await waitFor(() => {
        expect(screen.getByText(/Welcome back/)).toBeInTheDocument();
      });
    });

    it('has wallet icon', () => {
      const walletTab = screen.getByText('Wallet');
      expect(walletTab.closest('button')).toHaveClass('flex', 'items-center', 'gap-2');
    });

    it('has calendar icon for bookings', () => {
      const bookingsTab = screen.getByText('Demo Bookings');
      expect(bookingsTab.closest('button')).toHaveClass('flex', 'items-center', 'gap-2');
    });

    it('has history icon for transactions', () => {
      const transactionsTab = screen.getByText('Transactions');
      expect(transactionsTab.closest('button')).toHaveClass('flex', 'items-center', 'gap-2');
    });

    it('has credit card icon for payments', () => {
      const paymentsTab = screen.getByText('Payment History');
      expect(paymentsTab.closest('button')).toHaveClass('flex', 'items-center', 'gap-2');
    });

    it('has bar chart icon for analytics', () => {
      const analyticsTab = screen.getByText('Analytics');
      expect(analyticsTab.closest('button')).toHaveClass('flex', 'items-center', 'gap-2');
    });

    it('has trending up icon for advanced analytics', () => {
      const advancedAnalyticsTab = screen.getByText('Advanced Analytics');
      expect(advancedAnalyticsTab.closest('button')).toHaveClass('flex', 'items-center', 'gap-2');
    });

    it('has bot icon for voice agents', () => {
      const agentsTab = screen.getByText('Voice Agents');
      expect(agentsTab.closest('button')).toHaveClass('flex', 'items-center', 'gap-2');
    });

    it('has shield icon for security', () => {
      const securityTab = screen.getByText('Security');
      expect(securityTab.closest('button')).toHaveClass('flex', 'items-center', 'gap-2');
    });
  });

  describe('Layout and Styling', () => {
    beforeEach(async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ data: null, error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);
      
      await waitFor(() => {
        expect(screen.getByText(/Welcome back/)).toBeInTheDocument();
      });
    });

    it('has proper container styling', () => {
      const container = screen.getByText(/Welcome back/).closest('div');
      expect(container).toHaveClass('container', 'mx-auto', 'px-4', 'py-8');
    });

    it('has proper background styling', () => {
      const background = screen.getByText(/Welcome back/).closest('[class*="min-h-screen"]');
      expect(background).toHaveClass('bg-gradient-to-br', 'from-background', 'to-muted');
    });

    it('has proper tab list styling', () => {
      const tabList = screen.getByRole('tablist');
      expect(tabList).toHaveClass('grid', 'w-full', 'grid-cols-9');
    });

    it('has proper grid layout for wallet section', () => {
      const walletContent = screen.getByTestId('wallet-section').closest('div');
      expect(walletContent).toHaveClass('grid', 'gap-6', 'md:grid-cols-2');
    });

    it('has proper grid layout for payments section', () => {
      const paymentsTab = screen.getByText('Payment History');
      fireEvent.click(paymentsTab);

      const paymentsContent = screen.getByTestId('payment-history').closest('div');
      expect(paymentsContent).toHaveClass('grid', 'gap-6', 'md:grid-cols-2');
    });
  });

  describe('Accessibility', () => {
    beforeEach(async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ data: null, error: null }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);
      
      await waitFor(() => {
        expect(screen.getByText(/Welcome back/)).toBeInTheDocument();
      });
    });

    it('has proper heading structure', () => {
      expect(screen.getByRole('heading', { name: /Welcome back/ })).toBeInTheDocument();
    });

    it('has proper tab roles', () => {
      const tabs = screen.getAllByRole('tab');
      expect(tabs.length).toBeGreaterThan(0);
    });

    it('has proper tab panel roles', () => {
      const tabPanels = screen.getAllByRole('tabpanel');
      expect(tabPanels.length).toBeGreaterThan(0);
    });

    it('has proper tab list role', () => {
      expect(screen.getByRole('tablist')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles network errors gracefully', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockRejectedValue(new Error('Network error')),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Error loading data',
          description: 'Failed to load your account information.',
          variant: 'destructive',
        });
      });
    });

    it('handles database errors gracefully', async () => {
      const mockSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ 
            data: null, 
            error: { code: 'PGRST116', message: 'Not found' } 
          }),
        }),
      });
      (supabase.from as any).mockReturnValue({ select: mockSelect });

      renderDashboard(mockUser);

      await waitFor(() => {
        expect(screen.getByText(/Welcome back/)).toBeInTheDocument();
      });
    });
  });
});
