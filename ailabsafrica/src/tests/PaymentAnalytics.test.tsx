import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import PaymentAnalytics from '@/components/dashboard/PaymentAnalytics';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';

// Mock dependencies
vi.mock('@/contexts/AuthContext');
vi.mock('@/components/ui/use-toast');
vi.mock('@/integrations/supabase/client');
vi.mock('recharts', () => ({
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  PieChart: ({ children }: { children: React.ReactNode }) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  Legend: () => <div data-testid="legend" />,
}));

const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com',
};

const mockTransactions = [
  {
    id: '1',
    transaction_id: 'TXN123456789',
    amount: 100.00,
    currency: 'USD',
    payment_method: 'card',
    status: 'completed',
    created_at: '2024-01-15T10:00:00Z',
  },
  {
    id: '2',
    transaction_id: 'TXN987654321',
    amount: 50.00,
    currency: 'USD',
    payment_method: 'momo',
    status: 'completed',
    created_at: '2024-01-20T14:30:00Z',
  },
  {
    id: '3',
    transaction_id: 'TXN555666777',
    amount: 75.00,
    currency: 'USD',
    payment_method: 'card',
    status: 'failed',
    created_at: '2024-01-25T09:15:00Z',
  },
];

const mockAnalyticsData = {
  totalAmount: 225.00,
  totalTransactions: 3,
  successfulTransactions: 2,
  failedTransactions: 1,
  averageAmount: 75.00,
  monthlyTrends: [
    { month: 'Jan 2024', amount: 225.00, count: 3 },
  ],
  paymentMethodDistribution: [
    { method: 'Card', count: 2, amount: 175.00 },
    { method: 'Momo', count: 1, amount: 50.00 },
  ],
  statusDistribution: [
    { status: 'Completed', count: 2, amount: 150.00 },
    { status: 'Failed', count: 1, amount: 75.00 },
  ],
  recentActivity: mockTransactions,
};

describe('PaymentAnalytics', () => {
  const mockToast = vi.fn();
  const mockSupabase = {
    from: vi.fn().mockReturnThis(),
    select: vi.fn().mockReturnThis(),
    eq: vi.fn().mockReturnThis(),
    gte: vi.fn().mockReturnThis(),
    order: vi.fn().mockReturnThis(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    (useAuth as any).mockReturnValue({
      user: mockUser,
    });
    
    (useToast as any).mockReturnValue({
      toast: mockToast,
    });
    
    (supabase as any) = mockSupabase;
  });

  it('renders loading state initially', () => {
    mockSupabase.order.mockResolvedValue({ data: null, error: null });
    
    render(<PaymentAnalytics />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders analytics data when loaded successfully', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Payment Analytics')).toBeInTheDocument();
      expect(screen.getByText('$225.00')).toBeInTheDocument();
      expect(screen.getByText('67%')).toBeInTheDocument(); // Success rate
      expect(screen.getByText('$75.00')).toBeInTheDocument(); // Average amount
      expect(screen.getByText('1')).toBeInTheDocument(); // Failed transactions
    });
  });

  it('displays time range selector buttons', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('7d')).toBeInTheDocument();
      expect(screen.getByText('30d')).toBeInTheDocument();
      expect(screen.getByText('90d')).toBeInTheDocument();
      expect(screen.getByText('1y')).toBeInTheDocument();
    });
  });

  it('changes time range when button is clicked', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      const sevenDayButton = screen.getByText('7d');
      fireEvent.click(sevenDayButton);
      
      // Should trigger a new data load with 7d range
      expect(mockSupabase.gte).toHaveBeenCalled();
    });
  });

  it('displays chart type selector buttons', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Bar')).toBeInTheDocument();
      expect(screen.getByText('Line')).toBeInTheDocument();
    });
  });

  it('switches between chart types', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      const lineButton = screen.getByText('Line');
      fireEvent.click(lineButton);
      
      // Should show line chart
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  it('displays summary cards with correct data', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      // Total Amount card
      expect(screen.getByText('Total Amount')).toBeInTheDocument();
      expect(screen.getByText('$225.00')).toBeInTheDocument();
      expect(screen.getByText('3 transactions')).toBeInTheDocument();
      
      // Success Rate card
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
      expect(screen.getByText('67%')).toBeInTheDocument();
      expect(screen.getByText('2 successful')).toBeInTheDocument();
      
      // Average Amount card
      expect(screen.getByText('Average Amount')).toBeInTheDocument();
      expect(screen.getByText('$75.00')).toBeInTheDocument();
      expect(screen.getByText('per transaction')).toBeInTheDocument();
      
      // Failed Transactions card
      expect(screen.getByText('Failed Transactions')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('33% of total')).toBeInTheDocument();
    });
  });

  it('displays monthly trends chart', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Monthly Trends')).toBeInTheDocument();
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    });
  });

  it('displays payment method distribution chart', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Payment Methods')).toBeInTheDocument();
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });
  });

  it('displays status distribution section', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Transaction Status Distribution')).toBeInTheDocument();
      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.getByText('Failed')).toBeInTheDocument();
    });
  });

  it('displays recent activity section', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      expect(screen.getByText('Transaction 123456789')).toBeInTheDocument();
      expect(screen.getByText('Transaction 987654321')).toBeInTheDocument();
      expect(screen.getByText('Transaction 555666777')).toBeInTheDocument();
    });
  });

  it('handles refresh button click', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);
      
      // Should trigger data reload
      expect(mockSupabase.from).toHaveBeenCalledWith('payment_transactions');
    });
  });

  it('handles export functionality', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    // Mock URL.createObjectURL and document.createElement
    const mockCreateObjectURL = vi.fn().mockReturnValue('blob:mock-url');
    const mockRevokeObjectURL = vi.fn();
    const mockClick = vi.fn();
    
    Object.defineProperty(window, 'URL', {
      value: {
        createObjectURL: mockCreateObjectURL,
        revokeObjectURL: mockRevokeObjectURL,
      },
      writable: true,
    });
    
    Object.defineProperty(document, 'createElement', {
      value: vi.fn().mockReturnValue({
        href: '',
        download: '',
        click: mockClick,
      }),
      writable: true,
    });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      const exportButton = screen.getByText('Export');
      fireEvent.click(exportButton);
      
      expect(mockCreateObjectURL).toHaveBeenCalled();
      expect(mockClick).toHaveBeenCalled();
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Analytics exported',
        description: 'Payment analytics data has been downloaded as CSV',
      });
    });
  });

  it('handles error when loading data', async () => {
    const mockError = new Error('Database error');
    mockSupabase.order.mockResolvedValue({ data: null, error: mockError });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error loading analytics',
        description: 'Database error',
        variant: 'destructive',
      });
    });
  });

  it('displays no data message when no transactions exist', async () => {
    mockSupabase.order.mockResolvedValue({ data: [], error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('No analytics data available')).toBeInTheDocument();
    });
  });

  it('formats currency correctly', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('$225.00')).toBeInTheDocument();
      expect(screen.getByText('$75.00')).toBeInTheDocument();
    });
  });

  it('calculates percentages correctly', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockTransactions, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      // 2 successful out of 3 total = 67%
      expect(screen.getByText('67%')).toBeInTheDocument();
      // 1 failed out of 3 total = 33%
      expect(screen.getByText('33% of total')).toBeInTheDocument();
    });
  });

  it('handles different payment statuses correctly', async () => {
    const transactionsWithDifferentStatuses = [
      ...mockTransactions,
      {
        id: '4',
        transaction_id: 'TXN111222333',
        amount: 25.00,
        currency: 'USD',
        payment_method: 'bank_transfer',
        status: 'pending',
        created_at: '2024-01-30T16:45:00Z',
      },
      {
        id: '5',
        transaction_id: 'TXN444555666',
        amount: 100.00,
        currency: 'USD',
        payment_method: 'paypal',
        status: 'refunded',
        created_at: '2024-02-01T11:20:00Z',
      },
    ];
    
    mockSupabase.order.mockResolvedValue({ data: transactionsWithDifferentStatuses, error: null });
    
    render(<PaymentAnalytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('Refunded')).toBeInTheDocument();
    });
  });
});
