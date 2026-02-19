import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import RefundRequest from '@/components/RefundRequest';
import { AuthProvider } from '@/contexts/AuthContext';

// Mock Supabase
const mockSupabase = {
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

const mockTransaction = {
  transaction_id: 'test-transaction-123',
  amount: 100.00,
  currency: 'USD',
  status: 'successful',
  created_at: '2024-01-15T10:00:00Z',
};

describe('RefundRequest', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders refund request form', () => {
    renderWithProviders(<RefundRequest transaction={mockTransaction} />);

    expect(screen.getByText('Request Refund')).toBeInTheDocument();
    expect(screen.getByText('Submit a refund request for this transaction')).toBeInTheDocument();
    expect(screen.getByText('Transaction Details')).toBeInTheDocument();
    expect(screen.getByText('Refund Type')).toBeInTheDocument();
    expect(screen.getByText('Reason for Refund *')).toBeInTheDocument();
  });

  it('displays transaction details correctly', () => {
    renderWithProviders(<RefundRequest transaction={mockTransaction} />);

    expect(screen.getByText('$100.00')).toBeInTheDocument();
    expect(screen.getByText('successful')).toBeInTheDocument();
  });

  it('shows full refund by default', () => {
    renderWithProviders(<RefundRequest transaction={mockTransaction} />);

    const refundTypeSelect = screen.getByRole('combobox');
    expect(refundTypeSelect).toHaveValue('full');
  });

  it('allows switching to partial refund', () => {
    renderWithProviders(<RefundRequest transaction={mockTransaction} />);

    const refundTypeSelect = screen.getByRole('combobox');
    fireEvent.click(refundTypeSelect);
    
    const partialOption = screen.getByText('Partial Refund');
    fireEvent.click(partialOption);

    expect(screen.getByText('Refund Amount (USD)')).toBeInTheDocument();
  });

  it('validates refund amount for partial refund', async () => {
    renderWithProviders(<RefundRequest transaction={mockTransaction} />);

    // Switch to partial refund
    const refundTypeSelect = screen.getByRole('combobox');
    fireEvent.click(refundTypeSelect);
    fireEvent.click(screen.getByText('Partial Refund'));

    // Try to submit without amount
    const reasonInput = screen.getByPlaceholderText('Please explain why you\'re requesting a refund...');
    fireEvent.change(reasonInput, { target: { value: 'Test reason' } });

    const submitButton = screen.getByText('Submit Refund Request');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Invalid Amount',
        description: 'Please enter a valid refund amount',
        variant: 'destructive',
      });
    });
  });

  it('prevents refund amount exceeding original amount', async () => {
    renderWithProviders(<RefundRequest transaction={mockTransaction} />);

    // Switch to partial refund
    const refundTypeSelect = screen.getByRole('combobox');
    fireEvent.click(refundTypeSelect);
    fireEvent.click(screen.getByText('Partial Refund'));

    // Enter amount exceeding original
    const amountInput = screen.getByRole('spinbutton');
    fireEvent.change(amountInput, { target: { value: '150.00' } });

    const reasonInput = screen.getByPlaceholderText('Please explain why you\'re requesting a refund...');
    fireEvent.change(reasonInput, { target: { value: 'Test reason' } });

    const submitButton = screen.getByText('Submit Refund Request');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Invalid Amount',
        description: 'Refund amount cannot exceed the original transaction amount',
        variant: 'destructive',
      });
    });
  });

  it('requires reason for refund', async () => {
    renderWithProviders(<RefundRequest transaction={mockTransaction} />);

    const submitButton = screen.getByText('Submit Refund Request');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Reason Required',
        description: 'Please provide a reason for the refund request',
        variant: 'destructive',
      });
    });
  });

  it('submits full refund request successfully', async () => {
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true },
      error: null,
    });

    renderWithProviders(<RefundRequest transaction={mockTransaction} />);

    const reasonInput = screen.getByPlaceholderText('Please explain why you\'re requesting a refund...');
    fireEvent.change(reasonInput, { target: { value: 'Test refund reason' } });

    const submitButton = screen.getByText('Submit Refund Request');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('process-refund', {
        body: {
          transaction_id: 'test-transaction-123',
          amount: undefined,
          reason: 'Test refund reason',
          user_id: undefined,
        },
      });
    });

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Refund Request Submitted',
        description: 'Your refund request has been processed successfully',
      });
    });
  });

  it('submits partial refund request successfully', async () => {
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true },
      error: null,
    });

    renderWithProviders(<RefundRequest transaction={mockTransaction} />);

    // Switch to partial refund
    const refundTypeSelect = screen.getByRole('combobox');
    fireEvent.click(refundTypeSelect);
    fireEvent.click(screen.getByText('Partial Refund'));

    // Enter amount and reason
    const amountInput = screen.getByRole('spinbutton');
    fireEvent.change(amountInput, { target: { value: '50.00' } });

    const reasonInput = screen.getByPlaceholderText('Please explain why you\'re requesting a refund...');
    fireEvent.change(reasonInput, { target: { value: 'Partial refund test' } });

    const submitButton = screen.getByText('Submit Refund Request');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('process-refund', {
        body: {
          transaction_id: 'test-transaction-123',
          amount: 50.00,
          reason: 'Partial refund test',
          user_id: undefined,
        },
      });
    });
  });

  it('handles refund request failure', async () => {
    mockSupabase.functions.invoke.mockRejectedValue(new Error('Refund failed'));

    renderWithProviders(<RefundRequest transaction={mockTransaction} />);

    const reasonInput = screen.getByPlaceholderText('Please explain why you\'re requesting a refund...');
    fireEvent.change(reasonInput, { target: { value: 'Test reason' } });

    const submitButton = screen.getByText('Submit Refund Request');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Refund Request Failed',
        description: 'Refund failed',
        variant: 'destructive',
      });
    });
  });

  it('shows refund summary for partial refund', () => {
    renderWithProviders(<RefundRequest transaction={mockTransaction} />);

    // Switch to partial refund
    const refundTypeSelect = screen.getByRole('combobox');
    fireEvent.click(refundTypeSelect);
    fireEvent.click(screen.getByText('Partial Refund'));

    // Enter amount
    const amountInput = screen.getByRole('spinbutton');
    fireEvent.change(amountInput, { target: { value: '30.00' } });

    expect(screen.getByText('Refund Summary')).toBeInTheDocument();
    expect(screen.getByText('$100.00')).toBeInTheDocument(); // Original amount
    expect(screen.getByText('$30.00')).toBeInTheDocument(); // Refund amount
    expect(screen.getByText('$70.00')).toBeInTheDocument(); // Remaining balance
  });

  it('calls onClose when cancel button is clicked', () => {
    const mockOnClose = jest.fn();
    renderWithProviders(<RefundRequest transaction={mockTransaction} onClose={mockOnClose} />);

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onRefundSuccess when refund is successful', async () => {
    const mockOnRefundSuccess = jest.fn();
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true },
      error: null,
    });

    renderWithProviders(
      <RefundRequest 
        transaction={mockTransaction} 
        onRefundSuccess={mockOnRefundSuccess}
      />
    );

    const reasonInput = screen.getByPlaceholderText('Please explain why you\'re requesting a refund...');
    fireEvent.change(reasonInput, { target: { value: 'Test reason' } });

    const submitButton = screen.getByText('Submit Refund Request');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnRefundSuccess).toHaveBeenCalled();
    });
  });
});
