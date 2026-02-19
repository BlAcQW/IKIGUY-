import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import SubscriptionManagement from '../components/SubscriptionManagement';

// Mock the toast hook
const mockToast = vi.fn();
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock Supabase client
const mockSupabase = {
  from: vi.fn(() => ({
    select: vi.fn(() => ({
      eq: vi.fn(() => ({
        order: vi.fn(() => ({
          limit: vi.fn(() => ({
            single: vi.fn(() => Promise.resolve({ data: null, error: null })),
          })),
        })),
        gte: vi.fn(() => ({
          order: vi.fn(() => ({
            limit: vi.fn(() => Promise.resolve({ data: [], error: null })),
          })),
        })),
        in: vi.fn(() => ({
          order: vi.fn(() => ({
            limit: vi.fn(() => ({
              single: vi.fn(() => Promise.resolve({ data: null, error: null })),
            })),
          })),
        })),
      })),
    })),
    insert: vi.fn(() => ({
      select: vi.fn(() => ({
        single: vi.fn(() => Promise.resolve({ data: null, error: null })),
      })),
    })),
    update: vi.fn(() => ({
      eq: vi.fn(() => ({
        select: vi.fn(() => ({
          single: vi.fn(() => Promise.resolve({ data: null, error: null })),
        })),
      })),
    })),
  })),
};

vi.mock('@/integrations/supabase/client', () => ({
  supabase: mockSupabase,
}));

describe('SubscriptionManagement', () => {
  const mockPlans = [
    {
      id: 'plan-1',
      name: 'Free',
      description: 'Basic plan for getting started',
      price: 0,
      currency: 'USD',
      billing_cycle: 'monthly' as const,
      features: {
        assistants: 1,
        templates: 5,
        api_calls: 100,
        storage: '100MB',
        support: 'community',
      },
      limits: {
        assistants: 1,
        templates: 5,
        api_calls: 100,
        storage_mb: 100,
      },
      is_active: true,
      is_popular: false,
      is_custom: false,
      sort_order: 1,
    },
    {
      id: 'plan-2',
      name: 'Professional',
      description: 'Most popular choice for growing businesses',
      price: 29.99,
      currency: 'USD',
      billing_cycle: 'monthly' as const,
      features: {
        assistants: 20,
        templates: 100,
        api_calls: 5000,
        storage: '10GB',
        support: 'priority',
        analytics: true,
        integrations: true,
        team_collaboration: true,
        advanced_features: true,
      },
      limits: {
        assistants: 20,
        templates: 100,
        api_calls: 5000,
        storage_mb: 10240,
      },
      is_active: true,
      is_popular: true,
      is_custom: false,
      sort_order: 3,
    },
  ];

  const mockSubscription = {
    id: 'sub-1',
    plan_id: 'plan-2',
    status: 'active' as const,
    current_period_start: '2025-01-01T00:00:00Z',
    current_period_end: '2025-02-01T00:00:00Z',
    cancel_at_period_end: false,
  };

  const mockUsage = [
    {
      id: 'usage-1',
      user_id: 'user-1',
      subscription_id: 'sub-1',
      feature_name: 'assistants',
      usage_count: 5,
      limit_count: 20,
      reset_date: '2025-01-01',
    },
    {
      id: 'usage-2',
      user_id: 'user-1',
      subscription_id: 'sub-1',
      feature_name: 'api_calls',
      usage_count: 1500,
      limit_count: 5000,
      reset_date: '2025-01-01',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mock responses
    mockSupabase.from.mockImplementation((table) => {
      const mockTable = {
        select: vi.fn(() => ({
          eq: vi.fn(() => ({
            order: vi.fn(() => ({
              limit: vi.fn(() => ({
                single: vi.fn(() => Promise.resolve({ data: null, error: null })),
              })),
            })),
            gte: vi.fn(() => ({
              order: vi.fn(() => ({
                limit: vi.fn(() => Promise.resolve({ data: [], error: null })),
              })),
            })),
            in: vi.fn(() => ({
              order: vi.fn(() => ({
                limit: vi.fn(() => ({
                  single: vi.fn(() => Promise.resolve({ data: null, error: null })),
                })),
              })),
            })),
          })),
        })),
        insert: vi.fn(() => ({
          select: vi.fn(() => ({
            single: vi.fn(() => Promise.resolve({ data: null, error: null })),
          })),
        })),
        update: vi.fn(() => ({
          eq: vi.fn(() => ({
            select: vi.fn(() => ({
              single: vi.fn(() => Promise.resolve({ data: null, error: null })),
            })),
          })),
        })),
      };

      // Return different data based on table
      if (table === 'subscription_plans') {
        mockTable.select.mockReturnValue({
          eq: vi.fn(() => ({
            order: vi.fn(() => Promise.resolve({ data: mockPlans, error: null })),
          })),
        });
      } else if (table === 'user_subscriptions') {
        mockTable.select.mockReturnValue({
          eq: vi.fn(() => ({
            in: vi.fn(() => ({
              order: vi.fn(() => ({
                limit: vi.fn(() => ({
                  single: vi.fn(() => Promise.resolve({ data: mockSubscription, error: null })),
                })),
              })),
            })),
          })),
        });
      } else if (table === 'subscription_usage') {
        mockTable.select.mockReturnValue({
          eq: vi.fn(() => ({
            gte: vi.fn(() => ({
              order: vi.fn(() => Promise.resolve({ data: mockUsage, error: null })),
            })),
          })),
        });
      } else if (table === 'billing_invoices') {
        mockTable.select.mockReturnValue({
          eq: vi.fn(() => ({
            order: vi.fn(() => ({
              limit: vi.fn(() => Promise.resolve({ data: [], error: null })),
            })),
          })),
        });
      } else if (table === 'payment_methods') {
        mockTable.select.mockReturnValue({
          eq: vi.fn(() => ({
            order: vi.fn(() => Promise.resolve({ data: [], error: null })),
          })),
        });
      }

      return mockTable;
    });
  });

  it('renders subscription management component', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Subscription Management')).toBeInTheDocument();
    });
  });

  it('displays current subscription when user has one', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Current Subscription')).toBeInTheDocument();
      expect(screen.getByText('Professional')).toBeInTheDocument();
      expect(screen.getByText('active')).toBeInTheDocument();
    });
  });

  it('displays subscription plans', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Free')).toBeInTheDocument();
      expect(screen.getByText('Professional')).toBeInTheDocument();
      expect(screen.getByText('$0')).toBeInTheDocument();
      expect(screen.getByText('$29.99')).toBeInTheDocument();
    });
  });

  it('shows popular badge on popular plans', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Most Popular')).toBeInTheDocument();
    });
  });

  it('displays plan features correctly', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      expect(screen.getByText(/Assistants: 1/)).toBeInTheDocument();
      expect(screen.getByText(/Templates: 5/)).toBeInTheDocument();
      expect(screen.getByText(/Api Calls: 100/)).toBeInTheDocument();
      expect(screen.getByText(/Storage: 100MB/)).toBeInTheDocument();
    });
  });

  it('shows current plan as disabled button', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      const currentPlanButton = screen.getByText('Current Plan');
      expect(currentPlanButton).toBeDisabled();
    });
  });

  it('opens subscribe dialog when subscribe button is clicked', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      const subscribeButtons = screen.getAllByText('Subscribe');
      fireEvent.click(subscribeButtons[0]);
    });

    await waitFor(() => {
      expect(screen.getByText('Subscribe to Free')).toBeInTheDocument();
    });
  });

  it('displays billing tab content', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      const billingTab = screen.getByText('Billing');
      fireEvent.click(billingTab);
    });

    await waitFor(() => {
      expect(screen.getByText('Payment Methods')).toBeInTheDocument();
      expect(screen.getByText('Recent Invoices')).toBeInTheDocument();
    });
  });

  it('displays usage tab content', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      const usageTab = screen.getByText('Usage');
      fireEvent.click(usageTab);
    });

    await waitFor(() => {
      expect(screen.getByText('Usage Overview')).toBeInTheDocument();
      expect(screen.getByText(/Assistants/)).toBeInTheDocument();
      expect(screen.getByText(/Api Calls/)).toBeInTheDocument();
    });
  });

  it('shows usage progress bars', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      const usageTab = screen.getByText('Usage');
      fireEvent.click(usageTab);
    });

    await waitFor(() => {
      // Check for progress bars (they should be rendered as div elements)
      const progressBars = document.querySelectorAll('.bg-primary.h-2');
      expect(progressBars.length).toBeGreaterThan(0);
    });
  });

  it('opens billing dialog when billing button is clicked', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      const billingButton = screen.getByText('Billing');
      fireEvent.click(billingButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Billing & Payment')).toBeInTheDocument();
    });
  });

  it('opens usage dialog when usage button is clicked', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      const usageButton = screen.getByText('Usage');
      fireEvent.click(usageButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Usage Analytics')).toBeInTheDocument();
    });
  });

  it('handles subscription cancellation', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      const cancelButton = screen.getByText('Cancel Subscription');
      fireEvent.click(cancelButton);
    });

    await waitFor(() => {
      expect(mockSupabase.from).toHaveBeenCalledWith('user_subscriptions');
    });
  });

  it('handles refresh button click', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);
    });

    await waitFor(() => {
      expect(mockSupabase.from).toHaveBeenCalledWith('subscription_plans');
    });
  });

  it('displays loading state initially', () => {
    // Mock loading state by not resolving the promises immediately
    mockSupabase.from.mockImplementation(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          order: vi.fn(() => new Promise(() => {})), // Never resolves
        })),
      })),
    }));

    render(<SubscriptionManagement />);
    
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('handles error when loading subscription data', async () => {
    // Mock error response
    mockSupabase.from.mockImplementation(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          order: vi.fn(() => Promise.resolve({ data: null, error: { message: 'Database error' } })),
        })),
      })),
    }));

    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Failed to load subscription data',
        variant: 'destructive',
      });
    });
  });

  it('handles subscription creation', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      const subscribeButtons = screen.getAllByText('Subscribe');
      fireEvent.click(subscribeButtons[0]);
    });

    await waitFor(() => {
      const confirmButton = screen.getByText('Confirm Subscription');
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(mockSupabase.from).toHaveBeenCalledWith('user_subscriptions');
    });
  });

  it('formats feature values correctly', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      // Check for unlimited features
      expect(screen.getByText(/Advanced Features: Included/)).toBeInTheDocument();
      expect(screen.getByText(/Analytics: Included/)).toBeInTheDocument();
    });
  });

  it('displays billing cycle information', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('/monthly')).toBeInTheDocument();
    });
  });

  it('shows next billing date for current subscription', async () => {
    render(<SubscriptionManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Next Billing')).toBeInTheDocument();
      // The date should be formatted and displayed
      expect(screen.getByText(/1\/1\/2025/)).toBeInTheDocument();
    });
  });
});
