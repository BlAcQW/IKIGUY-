import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import MarketingFeatures from '../components/MarketingFeatures';

// Mock the toast hook
const mockToast = vi.fn();
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock Supabase client
const mockSupabase = {
  auth: {
    getSession: vi.fn(() => Promise.resolve({
      data: {
        session: {
          access_token: 'mock-token'
        }
      }
    }))
  }
};

vi.mock('@/integrations/supabase/client', () => ({
  supabase: mockSupabase,
}));

// Mock fetch
global.fetch = vi.fn();

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(),
  },
});

describe('MarketingFeatures', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: [] })
    });
  });

  describe('Initial Rendering', () => {
    it('renders the main marketing features page', () => {
      render(<MarketingFeatures />);
      
      expect(screen.getByText('Marketing Features')).toBeInTheDocument();
      expect(screen.getByText('Manage referrals, leads, and campaigns')).toBeInTheDocument();
    });

    it('renders all tab triggers', () => {
      render(<MarketingFeatures />);
      
      expect(screen.getByText('Referrals')).toBeInTheDocument();
      expect(screen.getByText('Lead Management')).toBeInTheDocument();
      expect(screen.getByText('Campaigns')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
    });

    it('shows loading state initially', () => {
      render(<MarketingFeatures />);
      
      expect(screen.getByText('Loading marketing data...')).toBeInTheDocument();
    });
  });

  describe('Referrals Tab', () => {
    beforeEach(() => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          data: {
            total_referrals: 5,
            converted_referrals: 3,
            total_rewards: 150,
            pending_rewards: 50
          }
        })
      });
    });

    it('displays referral statistics', async () => {
      render(<MarketingFeatures />);
      
      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument(); // Total referrals
        expect(screen.getByText('3')).toBeInTheDocument(); // Converted referrals
        expect(screen.getByText('$150')).toBeInTheDocument(); // Total rewards
        expect(screen.getByText('$50')).toBeInTheDocument(); // Pending rewards
      });
    });

    it('shows create referral link button', async () => {
      render(<MarketingFeatures />);
      
      await waitFor(() => {
        expect(screen.getByText('Create New Referral Link')).toBeInTheDocument();
      });
    });

    it('opens create referral dialog when button is clicked', async () => {
      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Create New Referral Link'));
      });

      expect(screen.getByText('Create Referral Link')).toBeInTheDocument();
      expect(screen.getByText('Generate a new referral link to share with potential users')).toBeInTheDocument();
    });

    it('creates referral link successfully', async () => {
      const mockReferralData = {
        id: 'ref-123',
        referral_code: 'ABC123',
        referral_link: 'http://localhost:3000/signup?ref=ABC123',
        status: 'pending'
      };

      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ data: mockReferralData })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ data: mockReferralData })
        });

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Create New Referral Link'));
      });

      fireEvent.click(screen.getByText('Create Referral Link'));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Success",
          description: "Referral link created successfully"
        });
      });
    });

    it('handles referral link creation error', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: false,
        status: 500
      });

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Create New Referral Link'));
      });

      fireEvent.click(screen.getByText('Create Referral Link'));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Error",
          description: "Failed to create referral link",
          variant: "destructive"
        });
      });
    });

    it('displays referral links list', async () => {
      const mockReferrals = [
        {
          id: 'ref-1',
          referral_code: 'ABC123',
          referral_link: 'http://localhost:3000/signup?ref=ABC123',
          status: 'pending',
          created_at: '2025-01-21T10:00:00Z'
        }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: mockReferrals })
      });

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        expect(screen.getByText('ABC123')).toBeInTheDocument();
        expect(screen.getByText('Copy')).toBeInTheDocument();
        expect(screen.getByText('Open')).toBeInTheDocument();
      });
    });

    it('copies referral link to clipboard', async () => {
      const mockReferrals = [
        {
          id: 'ref-1',
          referral_code: 'ABC123',
          referral_link: 'http://localhost:3000/signup?ref=ABC123',
          status: 'pending',
          created_at: '2025-01-21T10:00:00Z'
        }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: mockReferrals })
      });

      (navigator.clipboard.writeText as any).mockResolvedValue(undefined);

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Copy'));
      });

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith('http://localhost:3000/signup?ref=ABC123');
        expect(mockToast).toHaveBeenCalledWith({
          title: "Copied!",
          description: "Link copied to clipboard"
        });
      });
    });
  });

  describe('Lead Management Tab', () => {
    beforeEach(() => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: [] })
      });
    });

    it('switches to leads tab', async () => {
      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Lead Management'));
      });

      expect(screen.getByText('Add New Lead')).toBeInTheDocument();
      expect(screen.getByText('Lead Contacts')).toBeInTheDocument();
    });

    it('opens create contact dialog', async () => {
      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Lead Management'));
        fireEvent.click(screen.getByText('Add New Lead'));
      });

      expect(screen.getByText('Add New Lead Contact')).toBeInTheDocument();
      expect(screen.getByLabelText('First Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Last Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Email *')).toBeInTheDocument();
    });

    it('creates lead contact successfully', async () => {
      const mockContact = {
        id: 'contact-1',
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe'
      };

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: mockContact })
      });

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Lead Management'));
        fireEvent.click(screen.getByText('Add New Lead'));
      });

      fireEvent.change(screen.getByLabelText('First Name'), { target: { value: 'John' } });
      fireEvent.change(screen.getByLabelText('Last Name'), { target: { value: 'Doe' } });
      fireEvent.change(screen.getByLabelText('Email *'), { target: { value: 'test@example.com' } });

      fireEvent.click(screen.getByText('Add Lead Contact'));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Success",
          description: "Lead contact created successfully"
        });
      });
    });

    it('displays lead contacts list', async () => {
      const mockContacts = [
        {
          id: 'contact-1',
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          company: 'Test Corp',
          status: 'new',
          lead_score: 75,
          created_at: '2025-01-21T10:00:00Z'
        }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: mockContacts })
      });

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Lead Management'));
      });

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('test@example.com')).toBeInTheDocument();
        expect(screen.getByText('Test Corp')).toBeInTheDocument();
        expect(screen.getByText('Score: 75')).toBeInTheDocument();
        expect(screen.getByText('Log Activity')).toBeInTheDocument();
      });
    });

    it('opens activity dialog for lead contact', async () => {
      const mockContacts = [
        {
          id: 'contact-1',
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          status: 'new',
          lead_score: 75,
          created_at: '2025-01-21T10:00:00Z'
        }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: mockContacts })
      });

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Lead Management'));
      });

      await waitFor(() => {
        fireEvent.click(screen.getByText('Log Activity'));
      });

      expect(screen.getByText('Log Activity')).toBeInTheDocument();
      expect(screen.getByText('Log an activity for John Doe')).toBeInTheDocument();
    });
  });

  describe('Campaigns Tab', () => {
    beforeEach(() => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: [] })
      });
    });

    it('switches to campaigns tab', async () => {
      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Campaigns'));
      });

      expect(screen.getByText('Create Campaign')).toBeInTheDocument();
      expect(screen.getByText('Marketing Campaigns')).toBeInTheDocument();
    });

    it('opens create campaign dialog', async () => {
      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Campaigns'));
        fireEvent.click(screen.getByText('Create New Campaign'));
      });

      expect(screen.getByText('Create Marketing Campaign')).toBeInTheDocument();
      expect(screen.getByLabelText('Campaign Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Description')).toBeInTheDocument();
      expect(screen.getByLabelText('Campaign Type')).toBeInTheDocument();
      expect(screen.getByLabelText('Budget (USD)')).toBeInTheDocument();
    });

    it('creates campaign successfully', async () => {
      const mockCampaign = {
        id: 'campaign-1',
        name: 'Test Campaign',
        description: 'Test description',
        campaign_type: 'email',
        budget: 1000
      };

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: mockCampaign })
      });

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Campaigns'));
        fireEvent.click(screen.getByText('Create New Campaign'));
      });

      fireEvent.change(screen.getByLabelText('Campaign Name'), { target: { value: 'Test Campaign' } });
      fireEvent.change(screen.getByLabelText('Description'), { target: { value: 'Test description' } });
      fireEvent.change(screen.getByLabelText('Budget (USD)'), { target: { value: '1000' } });

      // Select campaign type
      fireEvent.click(screen.getByText('Select campaign type'));
      fireEvent.click(screen.getByText('Email'));

      fireEvent.click(screen.getByText('Create Campaign'));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Success",
          description: "Campaign created successfully"
        });
      });
    });

    it('displays campaigns list', async () => {
      const mockCampaigns = [
        {
          id: 'campaign-1',
          name: 'Test Campaign',
          description: 'Test description',
          campaign_type: 'email',
          status: 'active',
          budget: 1000,
          start_date: '2025-01-21T10:00:00Z',
          created_at: '2025-01-21T10:00:00Z'
        }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: mockCampaigns })
      });

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Campaigns'));
      });

      await waitFor(() => {
        expect(screen.getByText('Test Campaign')).toBeInTheDocument();
        expect(screen.getByText('Test description')).toBeInTheDocument();
        expect(screen.getByText('email')).toBeInTheDocument();
        expect(screen.getByText('Budget: $1000')).toBeInTheDocument();
        expect(screen.getByText('View Analytics')).toBeInTheDocument();
      });
    });
  });

  describe('Analytics Tab', () => {
    it('switches to analytics tab', async () => {
      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Analytics'));
      });

      expect(screen.getByText('Marketing Analytics')).toBeInTheDocument();
      expect(screen.getByText('Analytics Coming Soon')).toBeInTheDocument();
      expect(screen.getByText('Detailed analytics and reporting features will be available soon.')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles data loading error', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Error",
          description: "Failed to load marketing data",
          variant: "destructive"
        });
      });
    });

    it('handles clipboard error', async () => {
      const mockReferrals = [
        {
          id: 'ref-1',
          referral_code: 'ABC123',
          referral_link: 'http://localhost:3000/signup?ref=ABC123',
          status: 'pending',
          created_at: '2025-01-21T10:00:00Z'
        }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: mockReferrals })
      });

      (navigator.clipboard.writeText as any).mockRejectedValue(new Error('Clipboard error'));

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Copy'));
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Error",
          description: "Failed to copy to clipboard",
          variant: "destructive"
        });
      });
    });
  });

  describe('Status Badges', () => {
    it('displays correct status badges', async () => {
      const mockReferrals = [
        {
          id: 'ref-1',
          referral_code: 'ABC123',
          referral_link: 'http://localhost:3000/signup?ref=ABC123',
          status: 'converted',
          created_at: '2025-01-21T10:00:00Z'
        }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: mockReferrals })
      });

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        expect(screen.getByText('Converted')).toBeInTheDocument();
      });
    });
  });

  describe('Empty States', () => {
    it('shows empty state for referrals', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: [] })
      });

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        expect(screen.getByText('No referral links created yet. Create your first one above!')).toBeInTheDocument();
      });
    });

    it('shows empty state for lead contacts', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: [] })
      });

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Lead Management'));
      });

      await waitFor(() => {
        expect(screen.getByText('No lead contacts yet. Add your first lead above!')).toBeInTheDocument();
      });
    });

    it('shows empty state for campaigns', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: [] })
      });

      render(<MarketingFeatures />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Campaigns'));
      });

      await waitFor(() => {
        expect(screen.getByText('No campaigns created yet. Create your first campaign above!')).toBeInTheDocument();
      });
    });
  });
});
