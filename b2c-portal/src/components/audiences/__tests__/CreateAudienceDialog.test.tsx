import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import CreateAudienceDialog from '../CreateAudienceDialog';

const mockOnOpenChange = vi.fn();
const mockOnAudienceCreated = vi.fn();

const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mockToast })
}));

global.fetch = vi.fn();

describe('CreateAudienceDialog', () => {
  beforeEach(() => {
    mockOnOpenChange.mockClear();
    mockOnAudienceCreated.mockClear();
    mockToast.mockClear();
    vi.mocked(fetch).mockClear();
  });

  test('renders creation method selection step', () => {
    render(
      <CreateAudienceDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onAudienceCreated={mockOnAudienceCreated}
      />
    );

    expect(screen.getByText('How do you want to create your audience?')).toBeInTheDocument();
    expect(screen.getByText('Upload CSV File')).toBeInTheDocument();
    expect(screen.getByText('Add Manually')).toBeInTheDocument();
    expect(screen.getByText('CRM Integration')).toBeInTheDocument();
  });

  test('can proceed to step 2 after selecting creation method', () => {
    render(
      <CreateAudienceDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onAudienceCreated={mockOnAudienceCreated}
      />
    );

    // Select CSV method
    const csvOption = screen.getByLabelText(/upload csv file/i);
    fireEvent.click(csvOption);

    // Click Next
    const nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).not.toBeDisabled();
    fireEvent.click(nextButton);

    expect(screen.getByText('Audience Details')).toBeInTheDocument();
    expect(screen.getByLabelText(/audience name/i)).toBeInTheDocument();
  });

  test('validates manual contact input', async () => {
    render(
      <CreateAudienceDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onAudienceCreated={mockOnAudienceCreated}
      />
    );

    // Select manual method
    const manualOption = screen.getByLabelText(/add manually/i);
    fireEvent.click(manualOption);

    // Go to step 2
    fireEvent.click(screen.getByRole('button', { name: /next/i }));

    // Fill in audience name
    const nameInput = screen.getByLabelText(/audience name/i);
    fireEvent.change(nameInput, { target: { value: 'Test Audience' } });

    // Add phone number
    const phoneInput = screen.getByPlaceholderText(/phone number/i);
    fireEvent.change(phoneInput, { target: { value: '+1234567890' } });

    // Create button should be enabled
    const createButton = screen.getByRole('button', { name: /create audience/i });
    expect(createButton).not.toBeDisabled();
  });

  test('handles CSV file validation', async () => {
    const mockFile = new File(['phone,name\n+1234567890,John Doe'], 'test.csv', {
      type: 'text/csv'
    });

    render(
      <CreateAudienceDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onAudienceCreated={mockOnAudienceCreated}
      />
    );

    // Select CSV method and go to step 2
    fireEvent.click(screen.getByLabelText(/upload csv file/i));
    fireEvent.click(screen.getByRole('button', { name: /next/i }));

    // Upload file
    const fileInput = screen.getByRole('button', { name: /choose file/i });
    const hiddenInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    Object.defineProperty(hiddenInput, 'files', {
      value: [mockFile],
      writable: false,
    });

    fireEvent.change(hiddenInput);

    await waitFor(() => {
      expect(screen.getByText('test.csv')).toBeInTheDocument();
    });
  });

  test('creates manual audience successfully', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: '123', name: 'Test Audience' })
    } as Response);

    render(
      <CreateAudienceDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onAudienceCreated={mockOnAudienceCreated}
      />
    );

    // Select manual method and go to step 2
    fireEvent.click(screen.getByLabelText(/add manually/i));
    fireEvent.click(screen.getByRole('button', { name: /next/i }));

    // Fill form
    fireEvent.change(screen.getByLabelText(/audience name/i), {
      target: { value: 'Test Audience' }
    });
    fireEvent.change(screen.getByPlaceholderText(/phone number/i), {
      target: { value: '+1234567890' }
    });

    // Create audience
    fireEvent.click(screen.getByRole('button', { name: /create audience/i }));

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Audience created successfully',
        description: 'Your audience "Test Audience" has been created.'
      });
    });

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    expect(mockOnAudienceCreated).toHaveBeenCalled();
  });

  test('handles creation errors gracefully', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 400,
      text: async () => 'Bad request'
    } as Response);

    render(
      <CreateAudienceDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onAudienceCreated={mockOnAudienceCreated}
      />
    );

    // Setup and try to create
    fireEvent.click(screen.getByLabelText(/add manually/i));
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    fireEvent.change(screen.getByLabelText(/audience name/i), {
      target: { value: 'Test Audience' }
    });
    fireEvent.change(screen.getByPlaceholderText(/phone number/i), {
      target: { value: '+1234567890' }
    });
    fireEvent.click(screen.getByRole('button', { name: /create audience/i }));

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Failed to create audience',
        description: 'Please try again.',
        variant: 'destructive'
      });
    });
  });
});