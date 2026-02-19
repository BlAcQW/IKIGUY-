import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import EnhancedBilling from '../EnhancedBilling';
import { vi } from 'vitest';

const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({ useToast: () => ({ toast: mockToast }) }));

describe('EnhancedBilling', () => {
  beforeEach(() => {
    mockToast.mockReset();
  });

  const renderComponent = () =>
    render(<EnhancedBilling currentBalance={0} usageData={{ minutes_used: 0, minutes_included: 0 }} />);

  it('successfully tops up with custom amount', async () => {
    renderComponent();
    fireEvent.click(screen.getByText('Top Up'));
    fireEvent.change(screen.getByPlaceholderText('Enter amount'), { target: { value: '75' } });
    fireEvent.click(screen.getAllByText('Add Credits')[1]);
    await waitFor(
      () =>
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({ title: 'Top-up successful', description: expect.stringContaining('$75') }),
        ),
      { timeout: 3000 },
    );
  });

  it('handles default top up when no custom amount', async () => {
    renderComponent();
    fireEvent.click(screen.getByText('Top Up'));
    fireEvent.click(screen.getAllByText('Add Credits')[1]);
    await waitFor(
      () =>
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({ description: expect.stringContaining('$50') }),
        ),
      { timeout: 3000 },
    );
  });

  it('shows toast on top up failure', async () => {
    mockToast.mockImplementationOnce(() => {
      throw new Error('fail');
    });
    renderComponent();
    fireEvent.click(screen.getByText('Top Up'));
    fireEvent.click(screen.getAllByText('Add Credits')[1]);
    await waitFor(
      () =>
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({ title: 'Top-up failed' }),
        ),
      { timeout: 3000 },
    );
  });
});
