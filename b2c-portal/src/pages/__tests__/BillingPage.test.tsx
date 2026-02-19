import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import Billing from '../Billing';
import { vi } from 'vitest';
import { useAuth } from '@/hooks/useAuth';
import { usageApi, paymentApi } from '@/lib/core-api';

const mockToast = vi.fn();

vi.mock('@/components/dashboard/DashboardSidebar', () => ({ DashboardSidebar: () => <div>Sidebar</div> }));
vi.mock('@/components/billing/EnhancedBilling', () => ({ default: () => <div>EnhancedBilling</div> }));
vi.mock('@/hooks/use-toast', () => ({ useToast: () => ({ toast: mockToast }) }));

vi.mock('@/hooks/useAuth', () => ({ useAuth: vi.fn() }));

vi.mock('@/lib/core-api', () => ({
  usageApi: { getUsageData: vi.fn() },
  paymentApi: { getWalletBalance: vi.fn(), createStripeCheckout: vi.fn() }
}));

const mockUseAuth = useAuth as unknown as any;

describe('BillingPage', () => {
  beforeEach(() => {
    mockToast.mockReset();
    (usageApi.getUsageData as any).mockReset();
    (paymentApi.getWalletBalance as any).mockReset();
  });

  it('loads billing data on success', async () => {
    mockUseAuth.mockReturnValue({ user: { id: 'u1' } });
    (usageApi.getUsageData as any).mockResolvedValue({ minutes: 100 });
    (paymentApi.getWalletBalance as any).mockResolvedValue({ balance: 50 });

    render(<Billing />);

    await waitFor(() => expect(screen.getByText('Billing & Usage')).toBeInTheDocument());
    await waitFor(() => expect(usageApi.getUsageData).toHaveBeenCalled());
  });

  it('shows toast when user not authenticated', async () => {
    mockUseAuth.mockReturnValue({ user: null });

    render(<Billing />);

    await waitFor(() => expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({ description: 'User not authenticated' })));
  });

  it('shows toast on load error', async () => {
    mockUseAuth.mockReturnValue({ user: { id: 'u1' } });
    (usageApi.getUsageData as any).mockRejectedValue(new Error('fail'));
    (paymentApi.getWalletBalance as any).mockResolvedValue({ balance: 0 });

    render(<Billing />);

    await waitFor(() => expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({ title: 'Error loading billing data' })));
  });
});
